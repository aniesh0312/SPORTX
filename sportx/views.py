from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import CheckoutForm, LoginForm, ProfileForm, RegisterForm
from .models import Order, OrderItem, Product
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Review
from .forms import ReviewForm

def _get_cart_details(request):
    """Return valid cart rows and their total; remove deleted products from the session."""
    saved_cart = request.session.get("cart", {})
    cart = {}

    for product_id, quantity in saved_cart.items():
        try:
            product_id = str(int(product_id))
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity > 0:
            cart[product_id] = quantity

    product_ids = [int(product_id) for product_id in cart]
    products_by_id = Product.objects.in_bulk(product_ids)

    cart_items = []
    total = Decimal("0.00")
    valid_cart = {}

    for product_id, quantity in cart.items():
        product = products_by_id.get(int(product_id))
        if product is None:
            continue

        subtotal = product.price * quantity
        total += subtotal
        valid_cart[product_id] = quantity
        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    if valid_cart != saved_cart:
        request.session["cart"] = valid_cart
        request.session.modified = True

    return cart_items, total


def index(request):
    featured_products = Product.objects.filter(is_featured=True)
    latest_products = Product.objects.order_by("-created_at")[:8]
    return render(
        request,
        "index.html",
        {
            "featured_products": featured_products,
            "latest_products": latest_products,
        },
    )


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


def products(request):
    search = request.GET.get("search", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_brand = request.GET.get("brand", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "newest")

    products_queryset = Product.objects.select_related("category").all()

    # Dynamic category and brand choices for the sidebar
    category_model = Product._meta.get_field("category").remote_field.model
    categories = category_model.objects.all().order_by("name")

    brands = (
        Product.objects.exclude(brand__isnull=True)
        .exclude(brand__exact="")
        .order_by("brand")
        .values_list("brand", flat=True)
        .distinct()
    )

    # Navbar search + sidebar filters work together
    if search:
        products_queryset = products_queryset.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
            | Q(category__name__icontains=search)
        )

    if selected_category.isdigit():
        products_queryset = products_queryset.filter(
            category_id=selected_category
        )
    else:
        selected_category = ""

    if selected_brand:
        products_queryset = products_queryset.filter(
            brand__iexact=selected_brand
        )

    try:
        if min_price:
            products_queryset = products_queryset.filter(
                price__gte=Decimal(min_price)
            )

        if max_price:
            products_queryset = products_queryset.filter(
                price__lte=Decimal(max_price)
            )

    except (InvalidOperation, ValueError):
        min_price = ""
        max_price = ""

    sort_options = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "name_asc": "name",
    }

    if sort not in sort_options:
        sort = "newest"

    products_queryset = products_queryset.order_by(sort_options[sort])

    selected_category_name = ""

    if selected_category:
        for category in categories:
            if str(category.id) == selected_category:
                selected_category_name = category.name
                break

    context = {
        "products": products_queryset,
        "product_count": products_queryset.count(),
        "categories": categories,
        "brands": brands,
        "search": search,
        "selected_category": selected_category,
        "selected_category_name": selected_category_name,
        "selected_brand": selected_brand,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
    }

    return render(request, "products.html", context)


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(id=product.id)[:4]
    )

    reviews = (
        Review.objects.filter(product=product)
        .select_related("user")
        .order_by("-created_at")
    )

    rating_summary = reviews.aggregate(average_rating=Avg("rating"))
    average_rating = rating_summary["average_rating"] or 0

    user_review = None
    review_form = ReviewForm()

    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

        if user_review:
            review_form = ReviewForm(instance=user_review)

    return render(
        request,
        "product_detail.html",
        {
            "product": product,
            "related_products": related_products,
            "reviews": reviews,
            "average_rating": round(average_rating, 1),
            "review_count": reviews.count(),
            "review_form": review_form,
            "user_review": user_review,
        },
    )

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    existing_review = Review.objects.filter(
        product=product,
        user=request.user,
    ).first()

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            if existing_review:
                messages.success(request, "Your review has been updated.")
            else:
                messages.success(request, "Thank you for your review.")

        else:
            messages.error(request, "Please correct the review form errors.")

    return redirect("product_detail", product.id)
# ------------------------- Cart -------------------------

def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is currently out of stock.")
        return redirect("product_detail", id=product.id)

    cart = request.session.get("cart", {})
    product_id = str(product.id)
    current_quantity = int(cart.get(product_id, 0))

    if current_quantity >= product.stock:
        messages.warning(request, f"Only {product.stock} unit(s) of {product.name} are available.")
    else:
        cart[product_id] = current_quantity + 1
        request.session["cart"] = cart
        request.session.modified = True
        messages.success(request, f"{product.name} was added to your cart.")

    return redirect("cart")


def cart(request):
    cart_items, total = _get_cart_details(request)
    return render(request, "cart.html", {"cart_items": cart_items, "total": total})


def update_cart(request, id):
    product = get_object_or_404(Product, id=id)
    cart = request.session.get("cart", {})
    product_id = str(product.id)
    action = request.POST.get("action") or request.GET.get("action")

    if product_id not in cart:
        messages.warning(request, "That product is not in your cart.")
        return redirect("cart")

    quantity = int(cart[product_id])

    if action == "increase":
        if quantity < product.stock:
            cart[product_id] = quantity + 1
        else:
            messages.warning(request, f"Only {product.stock} unit(s) are available.")
    elif action == "decrease":
        if quantity > 1:
            cart[product_id] = quantity - 1
        else:
            del cart[product_id]

    request.session["cart"] = cart
    request.session.modified = True
    return redirect("cart")


def remove_from_cart(request, id):
    cart = request.session.get("cart", {})
    product_id = str(id)

    if product_id in cart:
        del cart[product_id]
        request.session["cart"] = cart
        request.session.modified = True
        messages.info(request, "Item removed from your cart.")

    return redirect("cart")


# ----------------------- Wishlist -----------------------

def wishlist(request):
    wishlist_ids = request.session.get("wishlist", [])
    products_in_wishlist = Product.objects.filter(id__in=wishlist_ids)
    return render(request, "wishlist.html", {"products": products_in_wishlist})


def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)
    wishlist_ids = request.session.get("wishlist", [])

    if product.id not in wishlist_ids:
        wishlist_ids.append(product.id)
        request.session["wishlist"] = wishlist_ids
        request.session.modified = True
        messages.success(request, f"{product.name} was added to your wishlist.")
    else:
        messages.info(request, "This product is already in your wishlist.")

    return redirect("wishlist")


def remove_from_wishlist(request, id):
    wishlist_ids = request.session.get("wishlist", [])

    if id in wishlist_ids:
        wishlist_ids.remove(id)
        request.session["wishlist"] = wishlist_ids
        request.session.modified = True
        messages.info(request, "Item removed from your wishlist.")

    return redirect("wishlist")


def move_to_cart(request, id):
    product = get_object_or_404(Product, id=id)
    wishlist_ids = request.session.get("wishlist", [])
    cart = request.session.get("cart", {})
    product_id = str(product.id)

    if product.stock > 0:
        cart[product_id] = min(int(cart.get(product_id, 0)) + 1, product.stock)
        request.session["cart"] = cart

    if product.id in wishlist_ids:
        wishlist_ids.remove(product.id)
        request.session["wishlist"] = wishlist_ids

    request.session.modified = True
    return redirect("cart")


# ------------------- Checkout and orders -------------------

@login_required
def checkout(request):
    cart_items, total = _get_cart_details(request)

    if not cart_items:
        messages.warning(
            request,
            "Your cart is empty. Add a product before checking out.",
        )
        return redirect("products")

    return render(
        request,
        "checkout.html",
        {
            "form": CheckoutForm(),
            "cart_items": cart_items,
            "total": total,
        },
    )


@login_required
@transaction.atomic
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    cart_items, total = _get_cart_details(request)

    if not cart_items:
        messages.warning(
            request,
            "Your cart is empty. Add a product before checking out.",
        )
        return redirect("products")

    form = CheckoutForm(request.POST)

    if not form.is_valid():
        return render(
            request,
            "checkout.html",
            {
                "form": form,
                "cart_items": cart_items,
                "total": total,
            },
        )

    for item in cart_items:
        if item["quantity"] > item["product"].stock:
            messages.error(
                request,
                f"Only {item['product'].stock} unit(s) of {item['product'].name} are available.",
            )
            return redirect("cart")

    order = form.save(commit=False)
    order.user = request.user
    order.total_amount = total
    order.save()

    for item in cart_items:
        product = item["product"]

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item["quantity"],
            price=product.price,
        )

        product.stock -= item["quantity"]
        product.save(update_fields=["stock"])

    request.session["cart"] = {}
    request.session.modified = True

    messages.success(request, "Your order was placed successfully.")
    return redirect("order_success", order_id=order.id)


def order_success(request, order_id):
    order_ids = request.session.get("order_ids", [])
    if order_id not in order_ids:
        messages.error(request, "That order is not available in this browser session.")
        return redirect("index")

    order = get_object_or_404(Order.objects.prefetch_related("items__product"), id=order_id)
    return render(request, "order_success.html", {"order": order})


@login_required
def my_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-order_date")
    )
    return render(request, "my_orders.html", {"orders": orders})


def _safe_next_url(request, default_url_name="home"):
    """Only redirect to a local next URL, preventing open-redirect attacks."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default_url_name


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to SPORTX, {user.first_name}!")
            return redirect(_safe_next_url(request))
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if not request.POST.get("remember_me"):
                request.session.set_expiry(0)
            messages.success(
                request,
                f"Welcome back, {request.user.first_name or request.user.username}!",
            )
            return redirect(_safe_next_url(request))
    else:
        form = LoginForm(request)
    return render(request, "login.html", {"form": form, "next": request.GET.get("next", "")})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)

    recent_orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-order_date")[:3]
    )
    return render(
        request,
        "profile.html",
        {
            "form": form,
            "recent_orders": recent_orders,
            "order_count": Order.objects.filter(user=request.user).count(),
        },
    )
