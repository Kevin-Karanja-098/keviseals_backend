from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User,
    EmailVerificationOTP,
    LandlordProfile,
    TenantProfile,
    LandlordContract,
    LandlordTheme,
)


# =========================================================
# INLINES
# =========================================================

class EmailVerificationOTPInline(admin.TabularInline):
    model = EmailVerificationOTP
    extra = 0
    fields = ("otp", "is_used", "created_at", "expires_at")
    readonly_fields = ("otp", "is_used", "created_at", "expires_at")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class LandlordProfileInline(admin.StackedInline):
    model = LandlordProfile
    fk_name = "user"
    can_delete = False
    verbose_name_plural = "Landlord Profile Details"
    extra = 0
    show_change_link = True


class TenantProfileInline(admin.StackedInline):
    model = TenantProfile
    fk_name = "user"
    can_delete = False
    verbose_name_plural = "Tenant Profile Details"
    extra = 0
    show_change_link = True


# =========================================================
# CUSTOM USER ADMIN
# =========================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):

    ordering = ("email",)

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "role",
        "is_email_verified",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_email_verified",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
    )

    # Fields for editing existing users.
    # IMPORTANT: Do not include username.
    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
        ("Personal Information", {
            "fields": (
                "first_name",
                "last_name",
                "phone_number",
            ),
        }),
        ("Roles and Verification", {
            "fields": (
                "role",
                "is_email_verified",
            ),
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            ),
        }),
    )

    # Fields for creating new users.
    # These replace Django's default username-based form fields.
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "phone_number",
                "password1",
                "password2",
                "role",
                "is_email_verified",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    inlines = (EmailVerificationOTPInline,)

    def get_inlines(self, request, obj=None):
        if obj is None:
            # Do not create profiles automatically from the user add form.
            return ()

        if obj.role == "LANDLORD":
            return (
                LandlordProfileInline,
                EmailVerificationOTPInline,
            )

        if obj.role == "TENANT":
            return (
                TenantProfileInline,
                EmailVerificationOTPInline,
            )

        return (EmailVerificationOTPInline,)


# =========================================================
# LANDLORD PROFILE ADMIN
# =========================================================

@admin.register(LandlordProfile)
class LandlordProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "company_name",
        "national_id",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__phone_number",
        "company_name",
        "national_id",
    )

    autocomplete_fields = ("user",)


# =========================================================
# TENANT PROFILE ADMIN
# =========================================================

@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "national_id",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__phone_number",
        "national_id",
    )

    autocomplete_fields = ("user",)


# =========================================================
# LANDLORD CONTRACT ADMIN
# =========================================================

@admin.register(LandlordContract)
class LandlordContractAdmin(admin.ModelAdmin):

    list_display = (
        "landlord",
        "status",
        "view_contract",
        "reviewed_by",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "reviewed_at",
    )

    search_fields = (
        "landlord__user__email",
        "landlord__company_name",
        "landlord__national_id",
    )

    readonly_fields = (
        "view_contract",
    )

    def view_contract(self, obj):
        if obj.signed_contract:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">'
                'View Signed Contract</a>',
                obj.signed_contract.url,
            )

        if obj.generated_contract:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">'
                'View Generated Contract</a>',
                obj.generated_contract.url,
            )

        return "No Document"

    view_contract.short_description = "Contract Document"


# =========================================================
# LANDLORD BRANDING / THEMES ADMIN
# =========================================================

@admin.register(LandlordTheme)
class LandlordThemeAdmin(admin.ModelAdmin):

    list_display = (
        "landlord",
        "app_name",
        "primary_color",
        "secondary_color",
        "font_family",
    )

    search_fields = (
        "landlord__user__email",
        "landlord__company_name",
        "app_name",
    )

    list_filter = ("font_family",)


# =========================================================
# EMAIL VERIFICATION OTP ADMIN
# =========================================================

@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "otp",
        "is_used",
        "created_at",
        "expires_at",
    )

    list_filter = (
        "is_used",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__phone_number",
    )

    readonly_fields = (
        "user",
        "otp",
        "is_used",
        "created_at",
        "expires_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
