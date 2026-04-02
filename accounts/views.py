from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import User


def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


@login_required
@user_passes_test(is_admin)
def user_management(request):
    """List all users with role badges; admin can create or deactivate."""
    users = User.objects.all().order_by('username')
    return render(request, 'accounts/user_management.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Admin creates a new system user."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'CLINICIAN')
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('user_management')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('user_management')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.save()
        messages.success(request, f'User "{username}" created successfully as {role}.')
        return redirect('user_management')

    return redirect('user_management')


@login_required
@user_passes_test(is_admin)
def user_deactivate(request, user_id):
    """Toggle active status of a user (deactivate or reactivate)."""
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_management')

    if request.method == 'POST':
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = 'activated' if target_user.is_active else 'deactivated'
        messages.success(request, f'User "{target_user.username}" {status}.')

    return redirect('user_management')

@login_required
def profile_view(request):
    """View user's own profile settings."""
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def change_password(request):
    """Allow user to change their own password inside the app."""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})

def register(request):
    """Public registration for new users. Default to inactive until approved by admin."""
    if request.user.is_authenticated:
        return redirect('population_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', 'ANALYST')
        
        if not username or not password or not email:
            messages.error(request, 'All fields are required.')
            return redirect('register')
            
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
            
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role if role in ['CLINICIAN', 'ANALYST'] else 'ANALYST'
        user.is_active = False # Require admin activation
        user.save()
        
        messages.success(request, 'Registration successful! Your account is pending admin approval. You will be able to log in once an administrator activates it.')
        return redirect('login')
        
    return render(request, 'accounts/register.html')
