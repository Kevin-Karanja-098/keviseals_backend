from django.conf import settings
from django.core.mail import send_mail


def send_email(subject, message, recipient):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )

def send_new_lease_request_email(landlord, tenant, unit):
    send_email(
        subject="New Lease Request",
        recipient=landlord.email,
        message=f"""
Hello,

{tenant.user.email} has submitted a lease request.

Property:
{unit.property.name}

Unit:
{unit.unit_number}

Please review the request from your dashboard.

Regards,
KeviSeals Team
""",
    )

def send_lease_approved_email(user, unit):
    send_email(
        subject="Lease Request Approved",
        recipient=user.email,
        message=f"""
Hello,

Congratulations!

Your lease request has been approved.

Unit:
{unit.unit_number}

You may now proceed with payment if required.

Regards,
KeviSeals Team
""",
    )

def send_lease_rejected_email(user):
    send_email(
        subject="Lease Request Rejected",
        recipient=user.email,
        message=f"""
Hello,

Unfortunately your lease request was not approved.

Please contact the landlord for more information.

Regards,
KeviSeals Team
""",
    )

def send_deposit_received_email(user, amount):
    send_email(
        subject="Deposit Payment Received",
        recipient=user.email,
        message=f"""
Hello,

We have successfully received your deposit payment.

Amount:
KES {amount}

Thank you.

Regards,
KeviSeals Team
""",
    )

def send_lease_activated_email(user):
    send_email(
        subject="Lease Activated",
        recipient=user.email,
        message="""
Hello,

Congratulations!

Your lease is now active.

Welcome to your new home.

Regards,
KeviSeals Team
""",
    )

def send_rent_generated_email(user, amount, due_date):
    send_email(
        subject="Monthly Rent Due",
        recipient=user.email,
        message=f"""
Hello,

A new rent charge has been generated.

Amount:
KES {amount}

Due Date:
{due_date}

Please make payment before the due date.

Regards,
KeviSeals Team
""",
    )

def send_payment_success_email(user, amount):
    send_email(
        subject="Payment Successful",
        recipient=user.email,
        message=f"""
Hello,

Your payment of KES {amount} has been received successfully.

Thank you.

Regards,
KeviSeals Team
""",
    )

def send_payment_failed_email(user):
    send_email(
        subject="Payment Failed",
        recipient=user.email,
        message="""
Hello,

Unfortunately your payment could not be completed.

Please try again.

Regards,
KeviSeals Team
""",
    )