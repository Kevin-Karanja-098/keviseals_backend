from notifications.services import send_push_notification
from .models import User


def notify_registration(user):
    send_push_notification(
        user=user,
        title="🎉 Welcome to KeviSeals",
        body="Your account has been created successfully.",
        notification_type="announcement",
        data={
            "type": "registration",
        },
    )


def notify_email_verified(user):
    send_push_notification(
        user=user,
        title="Email Verified",
        body="Your email has been verified successfully.",
        notification_type="announcement",
        data={
            "type": "email_verified",
        },
    )

def notify_contract_generated(user):
    send_push_notification(
        user=user,
        title="Contract Generated",
        body="Your landlord contract has been generated.",
        notification_type="announcement",
        data={
            "type": "contract_generated",
        },
    )


def notify_contract_uploaded(user):
    send_push_notification(
        user=user,
        title="Contract Uploaded",
        body="Your signed contract has been received.",
        notification_type="announcement",
        data={
            "type": "contract_uploaded",
        },
    )


def notify_contract_approved(user):
    send_push_notification(
        user=user,
        title="🎉 Account Approved",
        body="Congratulations! Your landlord account has been approved.",
        notification_type="announcement",
        data={
            "type": "contract_approved",
        },
    )


def notify_contract_rejected(user):
    send_push_notification(
        user=user,
        title="Application Rejected",
        body="Unfortunately your contract was not approved.",
        notification_type="announcement",
        data={
            "type": "contract_rejected",
        },
    )

def notify_property_managers(title, body, data=None):

    if data is None:
        data = {}

    managers = User.objects.filter(
        role="PROPERTY_MANAGER",
        is_active=True,
    )

    for manager in managers:

        send_push_notification(
            user=manager,
            title=title,
            body=body,
            notification_type="announcement",
            data=data,
        )

def notify_new_landlord_registration(user):

    notify_property_managers(
        title="New Landlord Registration",
        body=f"{user.email} has registered as a landlord.",
        data={
            "type": "new_landlord",
            "user_id": user.id,
        },
    )


def notify_new_tenant_registration(user):

    notify_property_managers(
        title="New Tenant Registration",
        body=f"{user.email} has registered as a tenant.",
        data={
            "type": "new_tenant",
            "user_id": user.id,
        },
    )


def notify_contract_uploaded_to_admin(user):

    notify_property_managers(
        title="Contract Uploaded",
        body=f"{user.email} uploaded a signed contract.",
        data={
            "type": "contract_uploaded_admin",
            "user_id": user.id,
        },
    )