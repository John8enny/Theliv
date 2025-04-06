from django import forms
from django.contrib.auth import authenticate
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import devices_for_user

class TOTPLoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    totp_code = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TOTP Code'}), required=False)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        totp_code = cleaned_data.get('totp_code')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid username or password.")
            else:
                # Check TOTP if a device exists
                totp_devices = [d for d in devices_for_user(self.user_cache) if isinstance(d, TOTPDevice)]
                if totp_devices:
                    if not totp_code:
                        raise forms.ValidationError("TOTP code is required.")
                    for device in totp_devices:
                        if device.verify_token(totp_code):
                            return cleaned_data
                    raise forms.ValidationError("Invalid TOTP code.")
        return cleaned_data

    def get_user(self):
        return self.user_cache