import secrets
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from .models import *
from .notifications import notify_monthly_billing_and_due_rent

def create_settlement(inspection):
    lease = inspection.move_out_request.lease
    deposit = lease.deposit_held
    wallet_credit = lease.wallet.available_credit
    damage = inspection.total_damage

    outstanding_total = RentCharge.objects.filter(lease=lease).exclude(status="PAID").aggregate(total=Sum("balance"))["total"] or Decimal("0.00")
    result = deposit + wallet_credit - outstanding_total - damage
    refund, oed = (result, Decimal("0.00")) if result >= 0 else (Decimal("0.00"), abs(result))

    return LeaseSettlement.objects.create(
        inspection=inspection, deposit_amount=deposit, wallet_credit=wallet_credit,
        outstanding_rent=outstanding_total, damage_cost=damage, refund_amount=refund, amount_owed=oed, status="COMPLETED"
    )

def apply_payment_to_charges(lease, amount):
    remaining = amount
    charges = RentCharge.objects.filter(lease=lease).exclude(status="PAID").order_by("billing_month", "id")

    for charge in charges:
        if remaining <= 0: break
        allocation = min(remaining, charge.balance)
        charge.amount_paid += allocation
        charge.balance -= allocation
        charge.status = "PAID" if charge.balance <= 0 else "PARTIAL"
        if charge.balance < 0: charge.balance = Decimal("0.00")
        charge.save(update_fields=["amount_paid", "balance", "status"])
        remaining -= allocation

    return remaining

def create_initial_rent_charge(lease, rent_amount):
    return RentCharge.objects.create(
        lease=lease, billing_month=timezone.now().date(), due_date=timezone.now().date(),
        rent_amount=rent_amount, amount_paid=rent_amount, balance=Decimal("0.00"), status="PAID"
    )

def apply_wallet_to_charge(charge):
    wallet = charge.lease.wallet
    if wallet.available_credit <= 0: return

    allocation = min(wallet.available_credit, charge.balance)
    charge.amount_paid += allocation
    charge.balance -= allocation
    wallet.available_credit -= allocation
    charge.status = "PAID" if charge.balance <= 0 else "PARTIAL"
    if charge.balance < 0: charge.balance = Decimal("0.00")

    charge.save(update_fields=["amount_paid", "balance", "status"])
    wallet.save(update_fields=["available_credit"])

def create_monthly_rent_charge(lease, billing_month):
    rent_amount = lease.unit.monthly_rent
    charge, created = RentCharge.objects.get_or_create(
        lease=lease, billing_month=billing_month,
        defaults={"due_date": billing_month, "rent_amount": rent_amount, "amount_paid": Decimal("0.00"), "balance": rent_amount, "status": "UNPAID"}
    )
    if created: apply_wallet_to_charge(charge)
    return charge

def create_rent_charge(lease):
    charge = RentCharge.objects.create(
        lease=lease, 
        billing_month=timezone.now().date(), 
        due_date=timezone.now().date(),
        rent_amount=lease.unit.monthly_rent, 
        amount_paid=Decimal("0.00"), 
        balance=lease.unit.monthly_rent, 
        status="UNPAID"
    )
    
    # 1. Apply wallet credits first to deduce final status and balances
    apply_wallet_to_charge(charge)
    
    # 2. Trigger the real-time notification immediately based on the final charge state
    notify_monthly_billing_and_due_rent(charge)
    
    return charge

def allocate_wallet_credit(lease):
    wallet = lease.wallet
    credit = wallet.available_credit
    if credit <= 0: return

    charges = RentCharge.objects.filter(lease=lease).exclude(status="PAID").order_by("billing_month")
    for charge in charges:
        if credit <= 0: break
        allocation = min(credit, charge.balance)
        charge.amount_paid += allocation
        charge.balance -= allocation
        charge.status = "PAID" if charge.balance <= 0 else "PARTIAL"
        if charge.balance < 0: charge.balance = Decimal("0.00")
        charge.save(update_fields=["amount_paid", "balance", "status"])
        credit -= allocation

    wallet.available_credit = credit
    wallet.save(update_fields=["available_credit"])

def generate_entry_code():
    return secrets.token_hex(4).upper()

def create_lease_wallet(lease):
    return LeaseWallet.objects.create(lease=lease)

def generate_due_rent_charges():
    now = timezone.now()
    cycle = timedelta(minutes=settings.RENT_CYCLE_MINUTES)

    for lease in Lease.objects.filter(status="ACTIVE"):
        if lease.last_billing_date is None:
            create_rent_charge(lease)
            lease.last_billing_date = now
        else:
            while now >= (lease.last_billing_date + cycle):
                create_rent_charge(lease)
                lease.last_billing_date += cycle

        lease.save(update_fields=["last_billing_date"])

def reconcile_settlement(settlement):
    transactions = SettlementTransaction.objects.filter(
        settlement=settlement,
        status="SUCCESS"
    )

    collected = (
        transactions.filter(transaction_type="COLLECTION")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    refunded = (
        transactions.filter(transaction_type="REFUND")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    update_fields = []

    # ----------------------------
    # Tenant owes landlord
    # ----------------------------
    if settlement.amount_owed > 0:

        if collected >= settlement.amount_owed:

            settlement.balance_received = True
            settlement.balance_received_at = timezone.now()
            settlement.status = "FINANCIALLY_SETTLED"

            update_fields.extend([
                "balance_received",
                "balance_received_at",
                "status",
            ])

        else:

            settlement.balance_received = False
            settlement.balance_received_at = None
            settlement.status = "WAITING_FOR_TENANT_PAYMENT"

            update_fields.extend([
                "balance_received",
                "balance_received_at",
                "status",
            ])

    # ----------------------------
    # Landlord owes tenant
    # ----------------------------
    elif settlement.refund_amount > 0:

        if refunded >= settlement.refund_amount:

            settlement.refund_paid = True
            settlement.refund_paid_at = timezone.now()
            settlement.status = "FINANCIALLY_SETTLED"

            update_fields.extend([
                "refund_paid",
                "refund_paid_at",
                "status",
            ])

        else:

            settlement.refund_paid = False
            settlement.refund_paid_at = None
            settlement.status = "WAITING_FOR_REFUND"

            update_fields.extend([
                "refund_paid",
                "refund_paid_at",
                "status",
            ])

    # ----------------------------
    # Nothing owed either way
    # ----------------------------
    else:

        settlement.status = "FINANCIALLY_SETTLED"
        update_fields.append("status")

    settlement.save(update_fields=update_fields)