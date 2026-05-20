from django.contrib import admin
from .models import Payment, Order, OrderProduct


class OrderProductInline(admin.TabularInline):
    # this will append the order product table in the order table in the admin panel
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'variation', 'size', 'quantity', 'product_price', 'ordered') # make these fields read only in the admin panel
    extra = 0 # django provides default 3 extra fields to add new order products, extra = 0 -> this will remove those extra fields and only show the existing order products for the order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'first_name', 'last_name', 'email', 'phone_number', 'order_total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'first_name', 'last_name', 'email', 'phone_number')
    list_per_page = 20
    inlines = [OrderProductInline]

# Register your models here
admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)