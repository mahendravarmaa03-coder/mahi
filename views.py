from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Cart, CartItem, Order, OrderItem

# Home page - all products show aagum
def home(request):
    products = Product.objects.all()
    # Cart item count for navbar badge
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.cartitem_set.count()
        except Cart.DoesNotExist:
            cart_count = 0
    return render(request, 'index.html', {'products': products, 'cart_count': cart_count})

# Login view
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

# Register view
def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Account created! Welcome!')
            return redirect('home')
    return render(request, 'register.html')

# Logout
def user_logout(request):
    logout(request)
    return redirect('home')

# Add to Cart
@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'"{product.name}" cart-la add achu!')
    return redirect('home')

# View Cart
@login_required(login_url='/login/')
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()
        total = cart.get_total()
    except Cart.DoesNotExist:
        cart_items = []
        total = 0
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

# Update quantity
@login_required(login_url='/login/')
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
    return redirect('view_cart')

# Checkout & Place Order
@login_required(login_url='/login/')
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()
        total = cart.get_total()
    except Cart.DoesNotExist:
        messages.error(request, 'Cart empty!')
        return redirect('home')

    if request.method == 'POST':
        address = request.POST['address']
        phone = request.POST['phone']

        # Order create panrom
        order = Order.objects.create(
            user=request.user,
            total_price=total,
            address=address,
            phone=phone
        )
        # Each cart item -> OrderItem convert panrom
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity
            )
        # Cart clear panrom
        cart_items.delete()
        messages.success(request, 'Order placed successfully!')
        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})

# Order Success page
@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.orderitem_set.all()
    return render(request, 'order_success.html', {'order': order, 'order_items': order_items})

# My Orders
@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})
