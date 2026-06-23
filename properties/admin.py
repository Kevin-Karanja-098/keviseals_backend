# from django.contrib import admin
# from .models import *
# from leases.models import *


# # =========================
# # INLINE MODELS
# # =========================

# class PropertyMediaInline(admin.TabularInline):
#     model = PropertyMedia
#     extra = 1


# class PropertyRuleInline(admin.TabularInline):
#     model = PropertyRule
#     extra = 1


# class BlockInline(admin.TabularInline):
#     model = Block
#     extra = 1


# class UnitMediaInline(admin.TabularInline):
#     model = UnitMedia
#     extra = 1


# class RentChargeInline(admin.TabularInline):
#     model = RentCharge
#     extra = 0
#     readonly_fields = ("created_at", "balance")


# # =========================
# # PROPERTY ADMIN
# # =========================

# @admin.register(Property)
# class PropertyAdmin(admin.ModelAdmin):
#     list_display = (
#         "name",
#         "landlord",
#         "town",
#         "county",
#         "status",
#         "created_at",
#     )

#     list_filter = ("status", "county", "town")
#     search_fields = (
#         "name",
#         "address",
#         "landlord__user__username",
#     )

#     ordering = ("-created_at",)

#     inlines = [
#         PropertyMediaInline,
#         PropertyRuleInline,
#         BlockInline,
#     ]


# # =========================
# # BLOCK ADMIN
# # =========================

# @admin.register(Block)
# class BlockAdmin(admin.ModelAdmin):
#     list_display = ("name", "property", "created_at")
#     search_fields = ("name", "property__name")
#     list_filter = ("property",)


# # =========================
# # UNIT ADMIN
# # =========================

# @admin.register(Unit)
# class UnitAdmin(admin.ModelAdmin):
#     list_display = (
#         "unit_number",
#         "title",
#         "property",
#         "block",
#         "bedrooms",
#         "monthly_rent",
#         "occupancy_status",
#         "updated_at",
#     )

#     list_filter = (
#         "occupancy_status",
#         "bedrooms",
#         "property",
#         "block",
#     )

#     search_fields = (
#         "unit_number",
#         "title",
#         "property__name",
#     )

#     ordering = ("property", "unit_number")

#     inlines = [UnitMediaInline]


# # =========================
# # LEASE REQUEST ADMIN (SAFE FIX)
# # =========================

# @admin.register(LeaseRequest)
# class LeaseRequestAdmin(admin.ModelAdmin):
#     list_display = (
#         "tenant",
#         "unit",
#         "status",
#         "amount_paid",
#         "created_at",
#     )

#     list_filter = ("status",)
#     search_fields = (
#         "tenant__user__username",
#         "unit__unit_number",
#     )


# # =========================
# # LEASE ADMIN
# # =========================

# @admin.register(Lease)
# class LeaseAdmin(admin.ModelAdmin):
#     list_display = (
#         "tenant",
#         "unit",
#         "status",
#         "move_in_date",
#         "entry_code",
#     )

#     list_filter = ("status",)
#     search_fields = (
#         "tenant__user__username",
#         "unit__unit_number",
#         "entry_code",
#     )

#     inlines = [RentChargeInline]


# # =========================
# # WALLET ADMIN
# # =========================

# @admin.register(LeaseWallet)
# class LeaseWalletAdmin(admin.ModelAdmin):
#     list_display = (
#         "lease",
#         "available_credit",
#         "updated_at",
#     )

#     search_fields = ("lease__unit__unit_number",)


# # =========================
# # RENT CHARGES
# # =========================

# @admin.register(RentCharge)
# class RentChargeAdmin(admin.ModelAdmin):
#     list_display = (
#         "lease",
#         "billing_month",
#         "rent_amount",
#         "amount_paid",
#         "balance",
#         "status",
#     )

#     list_filter = ("status", "billing_month")
#     search_fields = ("lease__unit__unit_number",)

#     readonly_fields = ("balance",)


# # =========================
# # MOVE OUT REQUEST
# # =========================

# @admin.register(MoveOutRequest)
# class MoveOutRequestAdmin(admin.ModelAdmin):
#     list_display = (
#         "lease",
#         "requested_date",
#         "status",
#         "created_at",
#     )

#     list_filter = ("status",)
#     search_fields = ("lease__unit__unit_number",)


# # =========================
# # SIMPLE REGISTRATIONS
# # =========================

# admin.site.register(PropertyMedia)
# admin.site.register(PropertyRule)
# admin.site.register(UnitMedia)