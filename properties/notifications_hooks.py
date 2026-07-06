from django.core.mail import send_mail
from django.conf import settings
from notifications.services import send_push_notification

def send_email_fallback(email, subject, body):
    """Fallback channel wrapper targeting email delivery pipelines securely."""
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Fallback communication routing pipeline error: {e}")

def notify_property_created(property_instance):
    landlord_user = property_instance.landlord.user
    title = "Property Registered Successfully"
    body = f"Your property '{property_instance.name}' located in {property_instance.town}, {property_instance.county} has been cataloged."
    
    send_push_notification(landlord_user, title, body, "property", {"property_id": property_instance.id})
    send_email_fallback(landlord_user.email, title, body)

def notify_property_updated(property_instance):
    landlord_user = property_instance.landlord.user
    title = "Property Profile Updated"
    body = f"The records for '{property_instance.name}' have been modified successfully."
    
    send_push_notification(landlord_user, title, body, "property", {"property_id": property_instance.id})

def notify_unit_created(unit_instance):
    landlord_user = unit_instance.property.landlord.user
    title = "New Unit Added"
    body = f"Unit {unit_instance.unit_number} ({unit_instance.title}) has been registered under {unit_instance.property.name}."
    
    send_push_notification(landlord_user, title, body, "unit", {"unit_id": unit_instance.id, "property_id": unit_instance.property.id})

def notify_unit_updated(unit_instance):
    landlord_user = unit_instance.property.landlord.user
    title = "Unit Details Modified"
    body = f"Unit {unit_instance.unit_number} configuration specifications were updated."
    
    send_push_notification(landlord_user, title, body, "unit", {"unit_id": unit_instance.id})

def notify_unit_status_changed(unit_instance, old_status):
    landlord_user = unit_instance.property.landlord.user
    title = f"Unit {unit_instance.unit_number} Status Alert"
    body = f"Occupancy transition detected for Unit {unit_instance.unit_number}: Changed from {old_status} to {unit_instance.occupancy_status}."
    
    send_push_notification(landlord_user, title, body, "unit", {"unit_id": unit_instance.id, "status": unit_instance.occupancy_status})
    send_email_fallback(landlord_user.email, f"Unit Occupancy Alert - {unit_instance.unit_number}", body)