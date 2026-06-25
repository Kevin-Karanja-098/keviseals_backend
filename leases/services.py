import secrets
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Lease, LeaseWallet, RentCharge

def apply_payment_to_charges(lease, amount):
    remaining = amount

    charges = (
        RentCharge.objects
        .filter(lease=lease)
        .exclude(status="PAID")
        .order_by("billing_month", "id")
    )

    for charge in charges:

        if remaining <= 0:
            break

        allocation = min(remaining, charge.balance)

        charge.amount_paid += allocation
        charge.balance -= allocation

        if charge.balance <= 0:
            charge.balance = Decimal("0.00")
            charge.status = "PAID"
        else:
            charge.status = "PARTIAL"

        charge.save()

        remaining -= allocation

    return remaining


def create_initial_rent_charge(lease, rent_amount):
    return RentCharge.objects.create(
        lease=lease,
        billing_month=timezone.now().date(),
        due_date=timezone.now().date(),
        rent_amount=rent_amount,
        amount_paid=rent_amount,
        balance=Decimal("0.00"),
        status="PAID"
    )

def apply_wallet_to_charge(charge):
    wallet = charge.lease.wallet

    if wallet.available_credit <= 0:
        return

    allocation = min(
        wallet.available_credit,
        charge.balance
    )

    charge.amount_paid += allocation
    charge.balance -= allocation

    wallet.available_credit -= allocation

    if charge.balance <= 0:
        charge.status = "PAID"
        charge.balance = Decimal("0.00")
    else:
        charge.status = "PARTIAL"

    charge.save()
    wallet.save()


def create_monthly_rent_charge(lease, billing_month):
    rent_amount = lease.unit.monthly_rent

    charge, created = RentCharge.objects.get_or_create(
        lease=lease,
        billing_month=billing_month,
        defaults={
            "due_date": billing_month,
            "rent_amount": rent_amount,
            "amount_paid": Decimal("0.00"),
            "balance": rent_amount,
            "status": "UNPAID",
        },
    )

    if created:
        apply_wallet_to_charge(charge)

    return charge


def create_rent_charge(lease):
    charge = RentCharge.objects.create(
        lease=lease,
        billing_month=timezone.now().date(),
        due_date=timezone.now().date(),
        rent_amount=lease.unit.monthly_rent,
        amount_paid=Decimal("0.00"),
        balance=lease.unit.monthly_rent,
        status="UNPAID",
    )

    # Immediately try to pay from wallet
    apply_wallet_to_charge(charge)

    return charge


def allocate_wallet_credit(lease):
    wallet = lease.wallet
    credit = wallet.available_credit

    if credit <= 0:
        return

    charges = (
        RentCharge.objects.filter(lease=lease)
        .exclude(status="PAID")
        .order_by("billing_month")
    )

    for charge in charges:
        if credit <= 0:
            break

        needed = charge.balance
        allocation = min(credit, needed)

        charge.amount_paid += allocation
        charge.balance -= allocation

        if charge.balance <= 0:
            charge.status = "PAID"
            charge.balance = Decimal("0.00")
        else:
            charge.status = "PARTIAL"

        charge.save()

        credit -= allocation

    wallet.available_credit = credit
    wallet.save()


def generate_entry_code():
    return secrets.token_hex(4).upper()


def create_lease_wallet(lease):
    return LeaseWallet.objects.create(lease=lease)


def generate_due_rent_charges():
    now = timezone.now()

    leases = Lease.objects.filter(status="ACTIVE")

    for lease in leases:

        if lease.last_billing_date is None:
            create_rent_charge(lease)

            lease.last_billing_date = now
            lease.save(update_fields=["last_billing_date"])

            continue

        next_due = (
            lease.last_billing_date
            + timedelta(minutes=settings.RENT_CYCLE_MINUTES)
        )

        while now >= next_due:

            create_rent_charge(lease)

            lease.last_billing_date += timedelta(
                minutes=settings.RENT_CYCLE_MINUTES
            )

            next_due = (
                lease.last_billing_date
                + timedelta(minutes=settings.RENT_CYCLE_MINUTES)
            )

        lease.save(update_fields=["last_billing_date"])