from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Password tidak sama")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah terpakai")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)

        # Autentikasi ulang sebelum login (aman untuk multiple backend)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Terjadi kesalahan saat login otomatis.")
            return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Successfully signed in as {user.username}")
            return redirect("index")
        else:
            messages.error(request, "Username atau password salah")
            return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")
