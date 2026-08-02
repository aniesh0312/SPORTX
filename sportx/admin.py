from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Product,
    Review,
    Order,
    OrderItem,
)


# ==========================
# Category Admin
# ==========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "product_count",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    def product_count(self, obj):
        return obj.product_set.count()

    product_count.short_description = "Products"


# ==========================
# Product Admin
# ==========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "image_preview",
        "name",
        "brand",
        "category",
        "price",
        "stock",
        "stock_status",
        "is_featured",
    )

    list_filter = (
        "category",
        "brand",
        "is_featured",
    )

    search_fields = (
        "name",
        "brand",
    )

    ordering = (
        "name",
    )

    list_per_page = 15

    list_editable = (
        "price",
        "stock",
        "is_featured",
    )

    readonly_fields = (
        "created_at",
        "image_preview_large",
    )

    fieldsets = (

        ("Product Information", {

            "fields": (
                "image_preview_large",
                "image",
                "category",
                "name",
                "brand",
                "description",
            )

        }),

        ("Pricing", {

            "fields": (
                "price",
                "stock",
                "rating",
                "is_featured",
            )

        }),

        ("System", {

            "fields": (
                "created_at",
            )

        }),

    )

    def image_preview(self, obj):

        if obj.image:

            return format_html(

                '<img src="{}" width="60" height="60" style="border-radius:8px;object-fit:cover;">',

                obj.image.url

            )

        return "-"

    image_preview.short_description = "Image"

    def image_preview_large(self, obj):

        if obj.image:

            return format_html(

                '<img src="{}" width="220" style="border-radius:12px;">',

                obj.image.url

            )

        return "-"

    image_preview_large.short_description = "Preview"

    def stock_status(self, obj):
        if obj.stock == 0:
            return "❌ Out of Stock"

        elif obj.stock <= 5:
            return "🟡 Low Stock"

        return "🟢 Available"

    stock_status.short_description = "Status"

# ==========================
# Review Admin
# ==========================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "user",
        "rating",
        "title",
        "created_at",
    )

    search_fields = (
        "product__name",
        "user__username",
        "title",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20


# ==========================
# Order Items
# ==========================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product",
        "quantity",
        "price",
    )

    can_delete = False


# ==========================
# Order Admin
# ==========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer_name",
        "email",
        "city",
        "payment_method",
        "total_amount",
        "status",
        "order_date",
    )

    search_fields = (
        "customer_name",
        "email",
        "phone",
    )

    list_filter = (
        "status",
        "payment_method",
        "order_date",
    )

    ordering = (
        "-order_date",
    )

    list_editable = (
        "status",
    )

    list_per_page = 20

    inlines = [
        OrderItemInline,
    ]