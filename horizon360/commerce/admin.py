from django.contrib import admin
from .models import Product, Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'company', 'created_at')
    list_filter = ('company', 'created_at')
    search_fields = ('name', 'sku')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'company', 'created_at')
    list_filter = ('status', 'company', 'created_at')
    inlines = [OrderItemInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_amount', 'company', 'created_at')
    list_filter = ('company', 'created_at')
    inlines = [CartItemInline]

