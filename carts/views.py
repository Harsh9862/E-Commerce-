from urllib import request
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from store.models import Product,Variation
from .models import Cart,CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required


# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart
    

def add_cart(request,product_id):
    product = Product.objects.get(id = product_id) #gets the product
    product_variations = []  # storing diff. kind of variations selected by the user

    if request.method == 'POST':
        # color = request.POST['color']
        # size = request.POST['size']
        # making the above fields more dynamic
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:    
                # we are making sure that the variation category must be matched with the variation value i.e. color with color and size with size
                variation = Variation.objects.get(product = product, variation_category__iexact = key, variation_value__iexact = value)
                product_variations.append(variation)
            except:
                pass   


    # We are getting the Cart here
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    # for grouping the same product with same variations in the cart
    is_cart_item_exists = CartItem.objects.filter(product = product, cart = cart)
    # We are getting the Cartitem here
    # try: -> change to if else statement because we are not getting the cart item here we are checking whether the cart item exists or not and if it exists then we are adding the quantity of the cart item and if it does not exist then we are creating a new cart item
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product = product, cart = cart) #using this we will see the variations in the database

        # if the current variation is inside the exisiting vaiations then we are increasing the quantity of the cart item 
        # and if the current variation is not inside the existing variations of the cart item then we are creating a new cart item with the current variation
        ex_var_list = [] # existing variation list
        id = [] # to store the id of the cart item with the same product and same cart and same variations
        for item in cart_item:
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation)) 
            id.append(item.id)
        
        if product_variations in ex_var_list:
            # increase the quantity of the cart item
            index = ex_var_list.index(product_variations) # getting the index of the cart item with the same product and same cart and same variations
            item_id = id[index] # getting the id of the cart item with the same product and same cart and same variations
            item = CartItem.objects.get(product = product, id = item_id) # getting the cart item with the same product and same cart and same variations
            item.quantity += 1
            item.save()

        else:
            item = CartItem.objects.create(product = product, quantity = 1, cart = cart)
            # creating a new cart item
            if len(product_variations) > 0: # if there are any variations then we are adding those variations to the cart item
                item.variations.clear() # we are clearing the previous variations of the cart item and adding the new variations to the cart item
                item.variations.add(*product_variations) # we are adding the new variations to the cart item
                    
            item.save()                                                             # now it is handling the gruoping properly

    else:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )   
        if len(product_variations) > 0: 
            cart_item.variations.clear()
            cart_item.variations.add(*product_variations)
        cart_item.save()

    return redirect('cart')
    # Redirect to the 'next' URL if provided, else default to product_detail
    # next_url = request.GET.get('next')
    # if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
    #     return redirect(next_url)
    # else:
    #     return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)      # Redirect back to the product detail page



def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id = product_id)
    
    try:
        cart_item = CartItem.objects.get(product = product, cart = cart, id = cart_item_id)
        if cart_item.quantity > 1 :
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')    


def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id = product_id)
    
    try:
        cart_item = CartItem.objects.get(product = product, cart = cart, id = cart_item_id)
        cart_item.delete()
    except:
        pass
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart = cart, is_active = True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2*total)/100
        grand_total = total+tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total,
    }

    return render(request, 'store/cart.html',context) 


@login_required(login_url = 'login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart = cart, is_active = True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            tax = (2*total)/100
            grand_total = total+tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total,
    }

    return render(request, 'store/checkout.html',context)

