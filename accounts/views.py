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
