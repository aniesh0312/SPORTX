def cart_count(request):
    cart = request.session.get("cart", {})

    return {
        "cart_count": sum(int(quantity) for quantity in cart.values())
    }