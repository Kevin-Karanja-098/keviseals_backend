from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import Property, PropertyMedia, PropertyRule, Block, Unit, UnitMedia

class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 1

class BlockInline(admin.TabularInline):
    model = Block
    extra = 1

@admin.register(Property)
class PropertyAdmin(LeafletGeoAdmin):
    list_display = ("name", "county", "town", "status", "landlord")
    search_fields = ("name", "county", "town")
    inlines = [PropertyMediaInline, BlockInline]

admin.site.register(PropertyRule)
admin.site.register(Unit)
admin.site.register(UnitMedia)