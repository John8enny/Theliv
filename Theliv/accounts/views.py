from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import devices_for_user
from django.urls import reverse
import qrcode
from io import BytesIO
import base64

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def totp_setup(request):
    user = request.user
    totp_devices = [d for d in devices_for_user(user) if isinstance(d, TOTPDevice)]
    
    if not totp_devices:
        if request.method == 'POST':
            device = TOTPDevice(user=user, name='default')
            device.save()
            return redirect('accounts:totp_setup')
        return render(request, 'accounts/totp.html')
    
    device = totp_devices[0]
    qr_url = device.config_url
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return render(request, 'accounts/totp.html', {'qr_image': qr_image})

def check_totp_setup(request):
    """Redirect to TOTP setup if no device exists after login."""
    if request.user.is_authenticated:
        totp_devices = [d for d in devices_for_user(request.user) if isinstance(d, TOTPDevice)]
        if not totp_devices:
            return redirect('accounts:totp_setup')
    return None