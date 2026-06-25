import secrets
from decimal import Decimal
from django.utils import timezone
from .models import RentCharge, LeaseWallet

def create_initial_rent_charge(lease, rent_amount):
    RentCharge.objects.create(
        lease=lease,
        billing_month=timezone.now().date().replace(day=1),
        rent_amount=rent_amount,
        amount_paid=rent_amount,
        balance=Decimal("0.00"),
        status="PAID"
    )

def generate_entry_code():
    return secrets.token_hex(4).upper()

def create_lease_wallet(lease):
    return LeaseWallet.objects.create(lease=lease)