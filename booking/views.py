import base64
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

    # Fungsi untuk penentuan label berdasarkan RFM Score
    def rfm_label(recency, frequency, monetary):

        # Score Recency
        if recency <= 5: r = 5
        elif recency <= 10: r = 4
        elif recency <= 15: r = 3
        elif recency <= 20: r = 2
        else: r = 1

        # Score Frequency
        if frequency >= 5: f = 5
        elif frequency == 4: f = 4
        elif frequency == 3: f = 3
        elif frequency == 2: f = 2
        else: f = 1

        # Score Monetary
        if monetary >= 12_000_000: m = 5
        elif monetary >= 9_000_000: m = 4
        elif monetary >= 6_000_000: m = 3
        elif monetary >= 3_000_000: m = 2
        else: m = 1

        total = r + f + m

        # Labeling berdasarkan total skor
        if total >= 12:
            return 2  # Loyal
        elif total >= 8:
            return 1  # Menengah
        else:
            return 0  # Standar

    # Jika CSV tidak ada, generate dataset + noise
    if not os.path.exists(csv_path):
        np.random.seed(42)
        n = 100
        recency = np.random.randint(0, 31, size=n)
        frequency = np.random.randint(1, 6, size=n)
        monetary = np.random.randint(2_000_000, 15_000_001, size=n)

        # Penentuan label menggunakan fungsi RFM baru
        labels = np.array([rfm_label(r, f, m) for r, f, m in zip(recency, frequency, monetary)])

        # Tambahkan noise: 10% label acak
        num_noise = int(0.2 * n)
        noise_indices = np.random.choice(n, num_noise, replace=False)
        for idx in noise_indices:
            possible = [0, 1, 2]
            possible.remove(labels[idx])
            labels[idx] = np.random.choice(possible)

        # Simpan CSV
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
        "message": f"✅ Model berhasil dilatih dari CSV berdasarkan RFM dengan akurasi {accuracy}%.",
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

def check_midtrans_payment_status(order_id, server_key):
    url = f"https://api.sandbox.midtrans.com/v2/{order_id}/status"
    headers = {
        "accept": "application/json",
        "authorization": "Basic " + base64.b64encode(f"{server_key}:".encode()).decode(),
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("transaction_status", None)
    except:
        return None

    return None


# ============================
#       BOOKING DETAIL
# ============================
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    server_key = "Mid-server-LWpZPL5K-D8C1zPFZbcuRxSf"

    snap = midtransclient.Snap(
        is_production=False,
        server_key=server_key
    )

    # Jika booking sudah punya order_id, cek ke Midtrans dulu
    if booking.order_id:
        status = check_midtrans_payment_status(booking.order_id, server_key)

        if status in ["settlement", "capture", "success"]:
            booking.payment_status = "paid"
            booking.save()
            return render(request, "details.html", {
                "booking": booking,
                "snap_token": None,
                "already_paid": True,
            })

    # Jika belum punya order_id → generate sekali saja
    if not booking.order_id:
        booking.order_id = f"BOOK-{booking.id}-{int(time.time())}"
        booking.save()

    transaction = {
        "transaction_details": {
            "order_id": booking.order_id,
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


# ============================
#         MARK PAID
# ============================
def mark_paid(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    server_key = "Mid-server-LWpZPL5K-D8C1zPFZbcuRxSf"

    # ⛔ WAJIB! Jangan pakai BOOK-{id}, pakai order_id yang tersimpan
    if not booking.order_id:
        return JsonResponse({
            "status": "failed",
            "message": "Order ID tidak ditemukan."
        })

    # 🔍 cek status midtrans pakai order_id sebenarnya
    status = check_midtrans_payment_status(booking.order_id, server_key)

    if status not in ["settlement", "capture", "success"]:
        return JsonResponse({
            "status": "failed",
            "message": "Pembayaran belum diterima Midtrans."
        })

    # update status pembayaran
    booking.payment_status = "paid"
    booking.save()

    # expire transaksi supaya token tidak bisa dipakai ulang
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic " + base64.b64encode(f"{server_key}:".encode()).decode()
    }

    try:
        requests.post(
            f"https://api.sandbox.midtrans.com/v2/{booking.order_id}/expire",
            headers=headers
        )
    except Exception as e:
        print("❌ Gagal meng-expire transaksi:", e)

    return JsonResponse({"status": "success"})
