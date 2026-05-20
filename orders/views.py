import json
import hmac
import hashlib
import uuid
import datetime

import razorpay
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from carts.views import _cart_id
from .models import Order, Payment, OrderProduct
from carts.models import CartItem
from .forms import OrderForm

from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    tax = 0
    grand_total = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone_number = form.cleaned_data['phone_number']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            context = {
                'order': data,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'quantity': quantity,
                'grand_total': grand_total,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount_in_paise': int(grand_total * 100),
                'receipt': order_number,
            }
            return render(request, 'orders/payments.html', context)

    return redirect('checkout')


@require_POST
def api_create_order(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    amount = payload.get('amount')
    currency = payload.get('currency', 'INR')
    receipt = payload.get('receipt')

    if amount is None:
        return JsonResponse({'error': 'Amount is required'}, status=400)

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Amount must be an integer in paise'}, status=400)

    if amount < 100:
        return JsonResponse({'error': 'Minimum amount is 100 paise'}, status=400)

    if not receipt:
        receipt = f'order_{uuid.uuid4().hex[:12]}'

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        razorpay_order = client.order.create({
            'amount': amount,
            'currency': currency,
            'receipt': receipt,
            'payment_capture': 1,
        })
    except razorpay.errors.AuthenticationError:
        return JsonResponse({'error': 'Razorpay authentication failed'}, status=401)
    except razorpay.errors.BadRequestError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception:
        return JsonResponse({'error': 'Unable to create Razorpay order'}, status=500)

    if receipt:
        try:
            order = Order.objects.get(user=request.user, order_number=receipt, is_ordered=False)
            order.razorpay_order_id = razorpay_order['id']
            order.save()
        except Order.DoesNotExist:
            pass

    return JsonResponse({
        'order_id': razorpay_order['id'],
        'amount': razorpay_order['amount'],
        'currency': razorpay_order['currency'],
    })


@require_POST
def api_verify_payment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    razorpay_payment_id = payload.get('razorpay_payment_id')
    razorpay_order_id = payload.get('razorpay_order_id')
    razorpay_signature = payload.get('razorpay_signature')

    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        f'{razorpay_order_id}|{razorpay_payment_id}'.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, razorpay_signature):
        return JsonResponse({'error': 'Signature mismatch'}, status=400)

    try:
        order = Order.objects.get(user=request.user, is_ordered=False, razorpay_order_id=razorpay_order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    payment = Payment(
        user=request.user,
        payment_id=razorpay_payment_id,
        payment_method='Razorpay',
        amount_paid=str(order.order_total),
        status='Paid',
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.status = 'Completed'
    order.save()

    # saves data in order product table
    cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    for cart_item in cart_items:
        order_product = OrderProduct()
        order_product.order = order
        order_product.payment = payment
        order_product.user = request.user
        order_product.product = cart_item.product

        colors = []
        sizes = []
        selected_variation = None
        for variation in cart_item.variations.all():
            category = variation.variation_category.lower()
            if category == 'color':
                colors.append(variation.variation_value)
            elif category == 'size':
                sizes.append(variation.variation_value)
            elif not selected_variation:
                selected_variation = variation

        if not selected_variation and cart_item.variations.exists():
            selected_variation = cart_item.variations.first()

        order_product.variation = selected_variation
        order_product.cilor = ', '.join(colors) if colors else ''
        order_product.size = ', '.join(sizes) if sizes else ''
        order_product.quantity = cart_item.quantity
        order_product.product_price = cart_item.product.price
        order_product.ordered = True
        order_product.save()

        # reduce stock count for the sold product and update availability
        product = cart_item.product
        product.stock = max(product.stock - cart_item.quantity, 0)
        if product.stock == 0:
            product.is_available = False
        product.save()

    # Empty the active cart items after successful payment
    cart_items.update(is_active=False)
    session_cart_id = _cart_id(request)
    CartItem.objects.filter(cart__cart_id=session_cart_id, is_active=True).update(is_active=False)

    # sending mail that order recieved
    mail_subject = 'Thank you for the Order!'
    message = render_to_string('orders/order_received_email.html',{
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    return JsonResponse({
        'status': 'success',
        'redirect_url': reverse('order_success', args=[order.order_number]),
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, user=request.user, order_number=order_number, is_ordered=True)
    order_products = OrderProduct.objects.filter(order=order)
    return render(request, 'orders/order_success.html', {
        'order': order,
        'order_products': order_products,
    })


def payments(request):
    return redirect('checkout')

