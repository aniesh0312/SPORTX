from django.shortcuts import render
from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("", views.index, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("products/", views.products, name="products"),
    

    path("product/<int:id>/", views.product_detail, name="product_detail"),
    path(
    "product/<int:product_id>/review/",
    views.submit_review,
    name="submit_review",
),


    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:id>/", views.remove_from_cart, name="remove_from_cart"),

    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/add/<int:id>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<int:id>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/move-to-cart/<int:id>/", views.move_to_cart, name="move_to_cart"),

    path("checkout/", views.checkout, name="checkout"),
    path("place-order/", views.place_order, name="place_order"),
    path("orders/<int:order_id>/success/", views.order_success, name="order_success"),
    path("my-orders/", views.my_orders, name="my_orders"),

    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    
]

