from django.db import models
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice

class CustomTOTPDevice(TOTPDevice):
    class Meta:
        proxy = True

