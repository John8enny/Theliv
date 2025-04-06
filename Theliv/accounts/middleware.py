from django.shortcuts import redirect
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice

class TOTPSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path not in ['/accounts/totp/', '/accounts/logout/']:
            totp_devices = [d for d in devices_for_user(request.user) if isinstance(d, TOTPDevice)]
            if not totp_devices:
                return redirect('accounts:totp_setup')
        response = self.get_response(request)
        return response