from django.contrib import admin
from .models import *

@admin.register(LeaseRequest)
class LeaseRequestAdmin(admin.ModelAdmin):
    list_display = ("tenant", "unit", "required_amount", "amount_paid", "status", "created_at")
    list_filter = ("status",)

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ("tenant", "unit", "entry_code", "status", "move_in_date")
    list_filter = ("status",)

@admin.register(LeaseWallet)
class LeaseWalletAdmin(admin.ModelAdmin):
    list_display = ("lease", "available_credit", "updated_at")

@admin.register(RentCharge)
class RentChargeAdmin(admin.ModelAdmin):
    list_display = ("lease", "billing_month", "rent_amount", "amount_paid", "balance", "status")

@admin.register(MoveOutRequest)
class MoveOutRequestAdmin(admin.ModelAdmin):
    list_display = ("lease", "requested_date", "status")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("tenant", "amount", "phone_number", "status", "mpesa_receipt", "created_at")
    list_filter = ("status",)