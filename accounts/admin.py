from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, EmailVerificationOTP, LandlordProfile, TenantProfile, LandlordContract, LandlordTheme

# --- Inlines ---
class EmailVerificationOTPInline(admin.TabularInline):
    model = EmailVerificationOTP
    extra = 0
    readonly_fields = ('otp', 'is_used', 'created_at', 'expires_at')
    can_delete = False

class LandlordProfileInline(admin.StackedInline):
    model = LandlordProfile
    can_delete = False
    verbose_name_plural = 'Landlord Profile Details'
    fk_name = 'user'

class TenantProfileInline(admin.StackedInline):
    model = TenantProfile
    can_delete = False
    verbose_name_plural = 'Tenant Profile Details'
    fk_name = 'user'

# --- Custom User Admin ---
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'is_email_verified', 'is_staff')
    list_filter = ('role', 'is_email_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions & Roles', {'fields': ('role', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [EmailVerificationOTPInline]

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == 'LANDLORD':
                return [LandlordProfileInline, EmailVerificationOTPInline]
            elif obj.role == 'TENANT':
                return [TenantProfileInline, EmailVerificationOTPInline]
        return self.inlines

# --- Profile Admin ---
@admin.register(LandlordProfile)
class LandlordProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'national_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'company_name', 'national_id')

@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'national_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'national_id')

# --- FIXED: Landlord Contract Admin ---
@admin.register(LandlordContract)
class LandlordContractAdmin(admin.ModelAdmin):
    # Swapped signed_at -> reviewed_at, and fixed file paths
    list_display = ('landlord', 'status', 'view_contract', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'reviewed_at')
    search_fields = ('landlord__user__email', 'landlord__company_name')

    def view_contract(self, obj):
        if obj.signed_contract:
            return format_html('<a href="{}" target="_blank">📥 View Signed</a>', obj.signed_contract.url)
        if obj.generated_contract:
            return format_html('<a href="{}" target="_blank">⏳ System Generated</a>', obj.generated_contract.url)
        return "No Document"
    view_contract.short_description = "Contract Status"

# --- NEW: Landlord Branding / Themes Admin ---
@admin.register(LandlordTheme)
class LandlordThemeAdmin(admin.ModelAdmin):
    list_display = ('landlord', 'app_name', 'primary_color', 'secondary_color', 'font_family')
    search_fields = ('landlord__company_name', 'app_name')

@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_used', 'created_at', 'expires_at')