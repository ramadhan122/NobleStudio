from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from .forms import BookingForm
from .models import Booking, CustomerCluster, Customer
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import time
import pandas as pd
from datetime import datetime
import joblib
from django.shortcuts import get_object_or_404
import requests
from django.http import JsonResponse
import midtransclient
import os


# === Booking View ===
def booking_view(request):
    """Menangani form booking pengguna."""
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.email = request.user.email
            booking.save()
            return redirect("success_page")
    else:
        form = BookingForm(initial={'email': request.user.email})

    return render(request, "booking.html", {"form": form})


# === Notifikasi Booking ===
def notif_booking(request):
    """Menampilkan notifikasi booking yang disetujui untuk user yang login."""
    approved_booking = None
    if request.user.is_authenticated:
        booking = Booking.objects.filter(
            user=request.user,
            approved=True,
            date__gte=now()
        ).first()

        if booking:
            approved_booking = booking.date

    return render(request, 'mywebsite/index.html', {
        'approved_booking': approved_booking
    })


# === 1️⃣ TRAIN MODEL DARI CSV (dengan generate noisy dataset otomatis) ===
def train_from_csv(request=None):
    start_time = time.time()
    csv_path = "media/training_data.csv"
    model_path = "media/trained_model.pkl"

    # Pastikan folder media ada
    os.makedirs("media", exist_ok=True)

    # Jika CSV tidak ada, buat dataset 100 record + noise otomatis
    if not os.path.exists(csv_path):
        np.random.seed(42)
        n = 100
        recency = np.random.randint(0, 31, size=n)
        frequency = np.random.randint(1, 6, size=n)
        monetary = np.random.randint(2_000_000, 15_000_001, size=n)
        labels = []
        for r, f, m in zip(recency, frequency, monetary):
            if m >= 10_000_000:
                label = 2  # Loyal
            elif m >= 5_000_000:
                label = 1  # Menengah
            else:
                label = 0  # Standar
            labels.append(label)
        labels = np.array(labels)

        # Tambahkan noise: 10% record label acak berbeda
        num_noise = int(0.1 * n)
        noise_indices = np.random.choice(n, num_noise, replace=False)
        for idx in noise_indices:
            possible = [0, 1, 2]
            possible.remove(labels[idx])
            labels[idx] = np.random.choice(possible)

        # Buat DataFrame dan simpan CSV
        df = pd.DataFrame({
            "Recency": recency,
            "Frequency": frequency,
            "Monetary": monetary,
            "Label": labels
        })
        df.to_csv(csv_path, index=False)

    # Baca CSV
    df = pd.read_csv(csv_path)
    required_cols = ['Recency', 'Frequency', 'Monetary', 'Label']
    if not all(col in df.columns for col in required_cols):
        return render(request, "clustering_result.html", {
            "message": "❌ CSV harus memiliki kolom: Recency, Frequency, Monetary, Label."
        })

    # Training Decision Tree
    X = df[['Recency', 'Frequency', 'Monetary']]
    y = df['Label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = DecisionTreeClassifier(random_state=42, max_depth=3)
    model.fit(X_train, y_train)

    # Evaluasi
    y_pred = model.predict(X_test)
    accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)

    # Simpan model
    joblib.dump(model, model_path)
    processing_time = round(time.time() - start_time, 2)

    return render(request, "clustering_result.html", {
        "message": f"✅ Model berhasil dilatih dari CSV dengan akurasi test {accuracy}%.",
        "accuracy": accuracy,
        "processing_time": processing_time,
        "clusters": []
    })


def run_customer_clustering(request):
    start_time = time.time()
    model_path = "media/trained_model.pkl"

    if not os.path.exists(model_path):
        return render(request, "clustering_result.html", {
            "message": "❌ Model belum dilatih. Jalankan training dulu dari CSV."
        })

    model = joblib.load(model_path)

    bookings = Booking.objects.all()
    if not bookings.exists():
        return render(request, "clustering_result.html", {"message": "Tidak ada data booking."})

    # Buat DataFrame
    df = pd.DataFrame(list(bookings.values('email', 'submitted_at', 'price')))
    df['price'] = df['price'].fillna(0).astype(float)
    df['submitted_at'] = pd.to_datetime(df['submitted_at'], errors='coerce')

    today = timezone.now().date()

    # Fungsi recency aman
    def recency_days(x):
        if x.dropna().empty:
            return 999
        last_submit = x.max().date()
        delta = (today - last_submit).days
        return max(delta, 0)

    # Hitung RFM
    df_grouped = df.groupby('email').agg(
        Recency=('submitted_at', recency_days),
        Frequency=('submitted_at', 'count'),
        Monetary=('price', 'sum')
    ).reset_index()

    # Prediksi Decision Tree
    X_new = df_grouped[['Recency', 'Frequency', 'Monetary']]
    y_pred = model.predict(X_new)
    label_map = {0: "Standar", 1: "Menengah", 2: "Loyal"}

    corrected_labels = []
    for i, row in df_grouped.iterrows():
        label = label_map[int(y_pred[i])]
        if row["Recency"] <= 7 and row["Frequency"] >= 3 and row["Monetary"] >= 10000000:
            label = "Loyal"
        elif row["Recency"] <= 15 and row["Frequency"] >= 2 and row["Monetary"] >= 5000000:
            label = "Menengah"
        elif row["Recency"] > 20 or row["Frequency"] == 1 or row["Monetary"] < 5000000:
            label = "Standar"
        corrected_labels.append(label)

    # Simpan hasil ke database
    CustomerCluster.objects.all().delete()
    for i, row in df_grouped.iterrows():
        label_str = corrected_labels[i]
        label_num = next((k for k, v in label_map.items() if v == label_str), 0)
        CustomerCluster.objects.create(user_identifier=row['email'], cluster=label_num)

    # Siapkan data untuk template
    clusters = []
    for i, row in df_grouped.iterrows():
        clusters.append({
            "email": row['email'],
            "recency": int(row['Recency']),
            "frequency": int(row['Frequency']),
            "monetary": float(row['Monetary']),
            "label": corrected_labels[i],
            "cluster_label": int(y_pred[i])
        })

    processing_time = round(time.time() - start_time, 2)

    return render(request, "clustering_result.html", {
        "message": "✅ Klasifikasi pelanggan berhasil dijalankan dengan model dan aturan berbasis RFM.",
        "clusters": clusters,
        "accuracy": "-",
        "processing_time": processing_time,
    })

def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Inisialisasi Midtrans
    snap = midtransclient.Snap(
        is_production=False,  # ubah ke True jika sudah live
        server_key='Mid-server-LWpZPL5K-D8C1zPFZbcuRxSf'  # ganti dengan server key kamu
    )

    if booking.payment_status == "paid":
        return render(request, "details.html", {
            "booking": booking,
            "snap_token": None,
            "already_paid": True,
        })

    # Data transaksi
    transaction = {
        "transaction_details": {
            "order_id": f"BOOK-{booking.id}-{int(time.time())}",
            "gross_amount": int(booking.price),
        },
        "customer_details": {
            "first_name": request.user.username,
            "email": booking.email,
            "phone": booking.phone,
        },
    }

    snap_token = snap.create_transaction(transaction)["token"]

    return render(request, "details.html", {
        "booking": booking,
        "snap_token": snap_token
    })

def mark_paid(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.payment_status = "paid"
    booking.save()

    # Tutup transaksi di Midtrans (supaya token tidak bisa dipakai ulang)
    order_id = f"BOOK-{booking.id}-{int(time.time())}"
    server_key = 'Mid-server-LWpZPL5K-D8C1zPFZbcuRxSf'
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic " + base64.b64encode(f"{server_key}:".encode()).decode()
    }

    try:
        requests.post(f"https://api.sandbox.midtrans.com/v2/{order_id}/expire", headers=headers)
    except Exception as e:
        print("❌ Gagal meng-expire transaksi di Midtrans:", e)

    return JsonResponse({"status": "success"})
