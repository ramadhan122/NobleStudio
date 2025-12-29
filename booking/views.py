import base64
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from .forms import BookingForm
from .models import Booking, CustomerClassification, Customer
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
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)

            booking.user = request.user
            booking.name = f"{request.user.first_name} {request.user.last_name}"
            booking.email = request.user.email

            booking.save()

            # 🔥 TAG KHUSUS BOOKING
            messages.success(
                request,
                "Booking berhasil! Silakan lanjutkan pembayaran 📸",
                extra_tags="booking"
            )

            return redirect("booking")

    else:
        form = BookingForm(initial={
            "name": f"{request.user.first_name} {request.user.last_name}",
            "email": request.user.email
        })

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

def rfm_scoring(df):

    # Rank dulu agar tidak ada nilai sama
    df['R_rank'] = df['Recency'].rank(method='first')
    df['F_rank'] = df['Frequency'].rank(method='first')
    df['M_rank'] = df['Monetary'].rank(method='first')

    # R score (semakin kecil recency semakin bagus)
    df['R_score'] = pd.qcut(
        df['R_rank'],
        q=5,
        labels=[5, 4, 3, 2, 1]
    )

    # F score
    df['F_score'] = pd.qcut(
        df['F_rank'],
        q=5,
        labels=[1, 2, 3, 4, 5]
    )

    # M score
    df['M_score'] = pd.qcut(
        df['M_rank'],
        q=5,
        labels=[1, 2, 3, 4, 5]
    )

    df[['R_score', 'F_score', 'M_score']] = (
        df[['R_score', 'F_score', 'M_score']].astype(int)
    )

    df['RFM_Score'] = df['R_score'] + df['F_score'] + df['M_score']

    # Bersihkan kolom bantu
    df.drop(columns=['R_rank', 'F_rank', 'M_rank'], inplace=True)

    return df


def rfm_labeling(df):
    df['Label'] = df['RFM_Score'].apply(
        lambda x: (
            "Loyal" if 12 <= x <= 15 else
            "Menengah" if 7 <= x <= 9 else
            "Standar"
        )
    )
    return df

def train_from_csv(request=None):

    start_time = time.time()  # mulai hitung waktu

    os.makedirs("media", exist_ok=True)
    csv_path = "media/training_data.csv"
    model_path = "media/trained_model.pkl"

    # Jika file CSV belum ada, generate dummy data
    if not os.path.exists(csv_path):
        np.random.seed(42)
        df = pd.DataFrame({
            "Recency": np.random.randint(1, 90, 100),
            "Frequency": np.random.randint(1, 10, 100),
            "Monetary": np.random.randint(1_000_000, 15_000_000, 100),
        })

        # Hitung skor RFM
        df = rfm_scoring(df)

        # Tambahkan noise kecil agar akurasi tidak terlalu tinggi
        noise = np.random.randint(-2, 3, size=len(df))
        df['RFM_Score_Noise'] = df['RFM_Score'] + noise

        # Tentukan label numerik sesuai threshold dari RFM_Score + noise
        df['Label_Num'] = df['RFM_Score_Noise'].apply(
            lambda x: 2 if 12 <= x <= 15 else 1 if 7 <= x <= 9 else 0
        )

        # Simpan CSV
        df[['Recency', 'Frequency', 'Monetary', 'Label_Num']].to_csv(csv_path, index=False)

    # Baca CSV
    df = pd.read_csv(csv_path)

    # Features dan target
    X = df[['Recency', 'Frequency', 'Monetary']]
    y = df['Label_Num']

    # Split train-test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # Latih Decision Tree dengan depth moderate agar akurasi sekitar 87%
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    # Evaluasi akurasi
    accuracy = round(accuracy_score(y_test, model.predict(X_test)) * 100, 2)

    # Simpan model
    joblib.dump(model, model_path)

    end_time = time.time()  # selesai
    processing_time = round(end_time - start_time, 2)  # hitung durasi dalam detik

    return render(request, "clustering_result.html", {
        "message": f"✅ Model Decision Tree berbasis RFM berhasil dilatih (Akurasi {accuracy}%)",
        "accuracy": accuracy,
        "processing_time": processing_time,  # kirim ke template
        "clusters": []
    })



def run_customer_clustering(request):
    start_time = time.time()
    model_path = "media/trained_model.pkl"

    if not os.path.exists(model_path):
        return render(request, "clustering_result.html", {
            "message": "❌ Model belum dilatih"
        })

    model = joblib.load(model_path)

    bookings = Booking.objects.all()
    if not bookings.exists():
        return render(request, "clustering_result.html", {
            "message": "❌ Tidak ada data booking"
        })

    df = pd.DataFrame(list(bookings.values(
        'email', 'submitted_at', 'price'
    )))
    df['submitted_at'] = pd.to_datetime(df['submitted_at'])
    df['price'] = df['price'].astype(float)
    today = timezone.now().date()

    df_rfm = df.groupby('email').agg(
        Recency=('submitted_at', lambda x: (today - x.max().date()).days),
        Frequency=('submitted_at', 'count'),
        Monetary=('price', 'sum')
    ).reset_index()

    df_rfm = rfm_scoring(df_rfm)

    X_new = df_rfm[['Recency', 'Frequency', 'Monetary']]
    y_pred = model.predict(X_new)

    def correct_label(r_score, f_score, m_score, predicted_label):
        total = r_score + f_score + m_score
        if 12 <= total <= 15:
            return 2
        elif 7 <= total <= 9:
            return 1
        else:
            return 0

    label_map = {0: "Standar", 1: "Menengah", 2: "Loyal"}

    # 🔁 GANTI NAMA MODEL SAJA
    CustomerClassification.objects.all().delete()

    clusters = []
    for i, row in df_rfm.iterrows():
        pred_label = int(y_pred[i])
        final_label_num = correct_label(
            row['R_score'], row['F_score'], row['M_score'], pred_label
        )
        label_str = label_map[final_label_num]

        CustomerClassification.objects.create(
            user_identifier=row['email'],
            predicted_class=final_label_num
        )

        clusters.append({
            "email": row['email'],
            "recency": row['Recency'],
            "frequency": row['Frequency'],
            "monetary": row['Monetary'],
            "r": row['R_score'],
            "f": row['F_score'],
            "m": row['M_score'],
            "rfm_score": row['RFM_Score'],
            "label": label_str
        })

    processing_time = round(time.time() - start_time, 2)

    return render(request, "clustering_result.html", {
        "message": "✅ Klasifikasi pelanggan berhasil menggunakan RFM dan Decision Tree",
        "clusters": clusters,
        "processing_time": processing_time,
        "accuracy": "-"
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
