from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta

def get_tokens_for_user(user):
    """Generate JWT tokens untuk user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def register_view(request):
    """Halaman daftar akun baru dengan JWT"""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')  # Kalau udah login, ke dashboard

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generate JWT tokens
            tokens = get_tokens_for_user(user)

            # Login user (session)
            login(request, user)

            # Store JWT tokens in session
            request.session['access_token'] = tokens['access']
            request.session['refresh_token'] = tokens['refresh']

            messages.success(request, f'Welcome {user.first_name or user.username}! Account created successfully.')
            return redirect('authentication:dashboard')  # REDIRECT KE DASHBOARD!
    else:
        form = CustomUserCreationForm()

    return render(request, 'authentication/register.html', {'form': form})

def login_view(request):
    """Halaman login dengan JWT"""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')  # Kalau udah login, ke dashboard

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)

            # Login user (session)
            login(request, user)

            # Store JWT tokens in session
            request.session['access_token'] = tokens['access']
            request.session['refresh_token'] = tokens['refresh']

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')

            # Check if there's a 'next' parameter (for redirecting after login requirement)
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)

            return redirect('authentication:dashboard')  # REDIRECT KE DASHBOARD!
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'authentication/login.html')

def logout_view(request):
    """Logout dan hapus JWT tokens"""
    # Clear JWT tokens from session
    request.session.pop('access_token', None)
    request.session.pop('refresh_token', None)

    logout(request)
    messages.success(request, 'Logout berhasil. See you next time!')
    return redirect('index')  # Logout tetap ke homepage

@login_required
def dashboard_view(request):
    """Dashboard untuk user yang sudah login"""
    user = request.user

    # Get JWT tokens from session
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')

    # Import booking model (adjust sesuai struktur kamu)
    try:
        from booking.models import Booking
        user_bookings = Booking.objects.filter(user=user) if hasattr(Booking, 'user') else Booking.objects.all()
        recent_bookings = user_bookings.order_by('-date')[:5]
        total_bookings = user_bookings.count()
    except:
        recent_bookings = []
        total_bookings = 0

    # User statistics
    days_since_joined = (timezone.now().date() - user.date_joined.date()).days

    # Quick stats
    stats = {
        'total_bookings': total_bookings,
        'days_member': days_since_joined,
        'last_login': user.last_login.strftime('%d %B %Y, %H:%M') if user.last_login else 'Never',
        'member_since': user.date_joined.strftime('%d %B %Y'),
    }

    # JWT info (for debugging/display)
    jwt_info = {
        'has_access_token': bool(access_token),
        'has_refresh_token': bool(refresh_token),
        'access_token_preview': access_token[:30] + '...' if access_token else None,
    }

    context = {
        'user': user,
        'stats': stats,
        'recent_bookings': recent_bookings,
        'jwt_info': jwt_info,
        'current_time': timezone.now(),
    }

    return render(request, 'authentication/dashboard.html', context)

@login_required
def profile_view(request):
    """User profile page"""
    if request.method == 'POST':
        # Update profile logic
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('authentication:profile')

    return render(request, 'authentication/profile.html', {'user': request.user})

@login_required
def user_bookings_view(request):
    try:
        from booking.models import Booking
        user_bookings = Booking.objects.filter(user=request.user) if hasattr(Booking, 'user') else Booking.objects.all()
        bookings = user_bookings.order_by('-date')
    except:
        bookings = []

    return render(request, 'authentication/user_bookings.html', {
        'bookings': bookings,
        'total_bookings': len(bookings)
    })

# API endpoint untuk get user info (testing JWT)
def user_info_api(request):
    """API endpoint untuk test JWT dari session"""
    access_token = request.session.get('access_token')

    if access_token:
        return JsonResponse({
            'authenticated': True,
            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
            'access_token': access_token[:50] + '...',  # Cuma show sebagian
            'message': 'JWT token found in session'
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'message': 'No JWT token in session'
        })
