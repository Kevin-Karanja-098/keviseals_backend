from django.contrib import admin
from .models import (
    LeaseRequest, Lease, LeaseWallet, RentCharge, Payment,
    MoveOutRequest, PropertyInspection, InspectionItem,
    LeaseSettlement, SettlementTransaction
)

@admin.register(LeaseRequest)
class LeaseRequestAdmin(admin.ModelAdmin):
    list_display = ("tenant", "unit", "required_amount", "amount_paid", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tenant__user__username", "unit__unit_number")

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "unit", "entry_code", "status", "move_in_date")
    list_filter = ("status", "move_in_date")
    search_fields = ("tenant__user__username", "unit__unit_number", "entry_code")

@admin.register(LeaseWallet)
class LeaseWalletAdmin(admin.ModelAdmin):
    list_display = ("lease", "available_credit", "updated_at")
    search_fields = ("lease__tenant__user__username", "lease__unit__unit_number")

@admin.register(RentCharge)
class RentChargeAdmin(admin.ModelAdmin):
    list_display = ("lease", "billing_month", "due_date", "rent_amount", "amount_paid", "balance", "status")
    list_filter = ("status", "billing_month")
    search_fields = ("lease__tenant__user__username", "lease__unit__unit_number")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("tenant", "amount", "phone_number", "status", "mpesa_receipt", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tenant__user__username", "phone_number", "mpesa_receipt", "checkout_request_id")

@admin.register(MoveOutRequest)
class MoveOutRequestAdmin(admin.ModelAdmin):
    list_display = ("lease", "requested_date", "status", "completed_at", "created_at")
    list_filter = ("status", "requested_date")
    search_fields = ("lease__tenant__user__username", "lease__unit__unit_number")

class InspectionItemInline(admin.TabularInline):
    model = InspectionItem
    extra = 1

@admin.register(PropertyInspection)
class PropertyInspectionAdmin(admin.ModelAdmin):
    list_display = ("id", "move_out_request", "inspected_by", "status", "inspection_date")
    list_filter = ("status", "inspection_date")
    search_fields = ("move_out_request__lease__tenant__user__username", "inspected_by__user__username")
    inlines = [InspectionItemInline]

@admin.register(LeaseSettlement)
class LeaseSettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "inspection", "deposit_amount", "refund_amount", "amount_owed", "status", "refund_paid", "balance_received")
    list_filter = ("status", "refund_paid", "balance_received", "created_at")
    search_fields = ("inspection__move_out_request__lease__tenant__user__username",)

@admin.register(SettlementTransaction)
class SettlementTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "settlement", "transaction_type", "payment_method", "amount", "status", "mpesa_receipt", "created_at")
    list_filter = ("transaction_type", "payment_method", "status", "created_at")
    search_fields = ("settlement__id", "phone_number", "mpesa_receipt", "checkout_request_id")