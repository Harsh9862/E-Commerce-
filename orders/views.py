from django.shortcuts import render,redirect
from .models import Order, Payment, OrderProduct
from carts.models import CartItem
from django.shortcuts import redirect
from .forms import OrderForm
import datetime


def place_order(request, total=0, quantity=0):
    current_user = request.user #we know the user is already logged in

    # if the cart count is less than or equal to 0, then redirect back to cart page
    cart_items = CartItem.objects.filter(user=current_user) #fetch the cart items for the current user
    cart_count = cart_items.count() #count the number of cart items

    print("cart_items:", cart_items)
    print("cart_count:", cart_count)
    if cart_count <= 0:
        return redirect('store')
    
    
    grand_total = 0
    tax = 0
    for item in cart_items:
        total += (item.product.price * item.quantity)
        quantity += item.quantity
    tax = (2 * total)/100
    grand_total = total + tax
        

    if request.method == 'POST':
        form = OrderForm(request.POST) #fetch the data from the order form
        if form.is_valid():
            # Store all the billing information in the Order table
            data = Order() #create an order object
            data.user = current_user #assign the current user to the order
            data.first_name = form.cleaned_data['first_name'] #fetch the first name from the form
            data.last_name = form.cleaned_data['last_name'] #fetch the last name from the form
            data.phone_number = form.cleaned_data['phone_number'] #fetch the phone number from the form
            data.email = form.cleaned_data['email'] #fetch the email from the form
            data.address_line_1 = form.cleaned_data['address_line_1'] #fetch the address line 1 from the form
            data.address_line_2 = form.cleaned_data['address_line_2'] #fetch the address line 2 from the form
            data.country = form.cleaned_data['country'] #fetch the country from the form
            data.state = form.cleaned_data['state'] #fetch the state from the form
            data.city = form.cleaned_data['city'] #fetch the city from the form
            data.order_note = form.cleaned_data['order_note'] #fetch the order note from the form
            data.order_total = grand_total #assign the grand total to the order total field
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save() #save the order to the database

            # Generate order number by combining date and order id
            yr = int(datetime.date.today().strftime('%Y')) #fetch the current year
            dt = int(datetime.date.today().strftime('%d')) #fetch the current date
            mt = int(datetime.date.today().strftime('%m')) #fetch the current month
            d = datetime.date(yr,mt,dt) #create a date object with year, month and date
            current_date = d.strftime("%Y%m%d") #format the date to YYYYMMDD format
            order_number = current_date + str(data.id) #combine date and order id to generate order number
            data.order_number = order_number #assign the generated order number to the order
            data.save() #save the order to update the order number
            return redirect('checkout')
    else:
        return redirect('checkout')
        



    
