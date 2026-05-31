from django.contrib import admin
from .models import Product, Variation, Review
# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display        = ('product_name','price','stock','category','modified_date','is_available')
    prepopulated_fields = {'slug' : ('product_name',)}

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product','variation_category','variation_value','is_active')
    list_editable = ('is_active',)
    list_filter = ('product','variation_category','variation_value')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('product__product_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(Review, ReviewAdmin)