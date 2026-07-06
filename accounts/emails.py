from django.conf import settings
from django.core.mail import send_mail


def send_email(
    subject,
    message,
    recipient,
):
    """
    Generic email sender used across the Accounts app.
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )

def send_registration_email(user):
    send_email(
        subject="🎉 Welcome to KeviSeals",
        recipient=user.email,
        message=f"""
Hi,

Welcome to KeviSeals.

Your account has been created successfully.

Please verify your email to activate your account.

Thank you,
KeviSeals Team
""",
    )


def send_otp_email(user, otp):
    send_email(
        subject="Email Verification Code",
        recipient=user.email,
        message=f"""
Hi,

Your verification code is:

{otp}

This code expires in 10 minutes.

If you didn't request this code, simply ignore this email.

Thank you,
KeviSeals Team
""",
    )


def send_email_verified_email(user):
    send_email(
        subject="Email Verified Successfully",
        recipient=user.email,
        message=f"""
Hi,

Congratulations!

Your email has been verified successfully.

You can now continue using KeviSeals.

Thank you,
KeviSeals Team
""",
    )


def send_contract_generated_email(user):
    send_email(
        subject="Your Contract is Ready",
        recipient=user.email,
        message=f"""
Hi,

Your landlord contract has been generated.

Please download it, sign it, and upload it back for review.

Thank you,
KeviSeals Team
""",
    )


def send_contract_uploaded_email(user):
    send_email(
        subject="Contract Received",
        recipient=user.email,
        message=f"""
Hi,

We have received your signed contract.

Our team will review it shortly.

Thank you,
KeviSeals Team
""",
    )


def send_contract_approved_email(user):
    send_email(
        subject="🎉 Account Approved",
        recipient=user.email,
        message=f"""
Hi,

Congratulations!

Your landlord account has been approved.

You can now create properties and begin managing tenants.

Thank you,
KeviSeals Team
""",
    )


def send_contract_rejected_email(user):
    send_email(
        subject="Contract Review Result",
        recipient=user.email,
        message=f"""
Hi,

Unfortunately your submitted contract was not approved.

Please review the feedback, make the necessary corrections, and upload it again.

Thank you,
KeviSeals Team
""",
    )


def send_contract_generated_email(user):
    send_email(
        subject="Your Contract is Ready",
        recipient=user.email,
        message=f"""
Hello,

Your landlord contract has been generated successfully.

Please review it, sign it, and upload the signed copy.

Regards,
KeviSeals Team
""",
    )


def send_contract_uploaded_email(user):
    send_email(
        subject="Signed Contract Received",
        recipient=user.email,
        message=f"""
Hello,

We have received your signed contract.

Our team will review it shortly.

Regards,
KeviSeals Team
""",
    )


def send_contract_approved_email(user):
    send_email(
        subject="🎉 Account Approved",
        recipient=user.email,
        message=f"""
Hello,

Congratulations!

Your landlord account has been approved.

You can now begin using all landlord features.

Regards,
KeviSeals Team
""",
    )


def send_contract_rejected_email(user):
    send_email(
        subject="Contract Review Result",
        recipient=user.email,
        message=f"""
Hello,

Unfortunately your submitted contract was not approved.

Please review the requested corrections and upload it again.

Regards,
KeviSeals Team
""",
    )
    