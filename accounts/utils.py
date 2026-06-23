# accounts/utils.py

from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, otp):

    send_mail(
        subject="Email Verification",
        message=f"Your verification code is {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )