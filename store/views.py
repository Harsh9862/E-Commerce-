from django.shortcuts import render, get_object_or_404, redirect
from category.models import Category
from .models import Product, Review
from .forms import ReviewForm
from carts.models import CartItem
from carts.views import _cart_id
from orders.models import OrderProduct
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Avg
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def store(request, category_slug = None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug = category_slug)
        products = Product.objects.filter(category = categories, is_available = True)

        paginator = Paginator(products, 3)  # paginator
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

        products_count = products.count()
    else:
        products = Product.objects.all().filter(is_available = True)
        
        paginator = Paginator(products, 3)  # paginator for the store page
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

        products_count = products.count()

    context = {
        'products': paged_products,
        'products_count' : products_count,
    }
    # changed this 'products': products to 'products': paged_products
    return render(request, 'store/store.html',context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug = category_slug, slug = product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id = _cart_id(request),product = single_product).exists()
    except Exception as e:
        raise e

    reviews = Review.objects.filter(product=single_product).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    user_review = None
    can_review = False

    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=single_product, user=request.user).first()
        can_review = OrderProduct.objects.filter(
            user=request.user,
            product=single_product,
            ordered=True,
            order__is_ordered=True
        ).exists()

    form = ReviewForm()

    context = {
        "single_product" : single_product,
        'in_cart' : in_cart,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': reviews.count(),
        'user_review': user_review,
        'can_review': can_review,
        'form': form,
    }
    return render(request, 'store/product_detail.html',context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword :
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains = keyword) | Q(product_name__icontains = keyword))

    context = {
        'products' : products,
    }
    return render(request, 'store/store.html', context)


@login_required(login_url='login')
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        purchased = OrderProduct.objects.filter(
            user=request.user,
            product=product,
            ordered=True,
            order__is_ordered=True
        ).exists()

        if not purchased:
            messages.error(request, 'Only customers who purchased this product can leave a review.')
            return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review, created = Review.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                }
            )
            return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

    return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)