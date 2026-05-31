import os
from django.contrib import messages,auth
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.db.models import Sum

from accounts.models import Account, Profile
from carts.models import CartItem
from orders.models import Order
# use django forms for registration and login -> forms.py
from .forms import RegistrationForm
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
import requests

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']  #cleaned data -> to fetch the value from request
            last_name = form.cleaned_data['last_name'] 
            phone_number = form.cleaned_data['phone_number'] 
            email = form.cleaned_data['email'] 
            password = form.cleaned_data['password'] 
            username = email.split('@')[0]

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password) #create_user func we created before in the models.py 
            user.phone_number = phone_number #we are not using phone number to create account therefore we are adding it latter
            user.save()
            # create an empty profile for the user
            try:
                Profile.objects.create(user=user, phone_number=phone_number)
            except Exception:
                pass

            # USER ACTIVATION for account verification.
            current_site = get_current_site(request) #get the current site domain
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/accounts_verification.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encode the user id to base64 format, user.pk -> primary key of the user
                'token':default_token_generator.make_token(user), #generate a token for the user
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            # messages.success(request, 'Your account has been registered successfully!')
            return redirect('/accounts/login/?command=verification&email='+email) #redirect to login page with a query parameter to show the verification message, +email -> concatenate the email to the url to show the email in the verification message
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(request, user)

            cart_items = CartItem.objects.filter(user__isnull=True)
            for item in cart_items:
                item.user = user
                item.save()

            messages.success(request, 'You are now logged in.')

            url = request.META.get('HTTP_REFERER') #get the url of the page from which the user is coming to the login page 
            try:
                query = requests.utils.urlparse(url).query #parse the url to get the query parameters-> -> it will from the url ?/next=/cart/checkout/ or ?/cart/ or ?/dashboard/ etc.
                # ?/next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&')) #split the query parameters to get the key and value -> {'next': '/cart/checkout/'}
                # {'next': '/cart/checkout/'} -> now redirect the user to the value of the params value.
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
             
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url='login') #this decorator will restrict the access to the logout view to only logged in users. if a user is not logged in and tries to access the logout view then it will redirect to the login page.
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #decode the user id from base64 format
        user = Account._default_manager.get(pk=uid) #get the user from the database using the decoded user id
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token): #check if the token is valid for the user
        user.is_active = True #activate the user
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')
    

def get_avatar_urls():
    avatars_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'avatars')
    avatar_urls = []
    if os.path.isdir(avatars_dir):
        for filename in sorted(os.listdir(avatars_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                avatar_urls.append(settings.STATIC_URL + 'images/avatars/' + filename)
    return avatar_urls


def dashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    total_spent = orders.aggregate(total_spent=Sum('order_total'))['total_spent'] or 0
    profile = None
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    context = {
        'orders': orders,
        'order_count': orders.count(),
        'total_spent': total_spent,
        'profile': profile,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def profile_view(request):
    profile = None
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    avatar_urls = get_avatar_urls()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'avatar_urls': avatar_urls,
    })


@login_required(login_url='login')
def edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})


def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():# will return True if the email exists in the database, otherwise False
            user = Account.objects.get(email__exact=email) #get the user from the database using the email

            # USER ACTIVATION for account verification.
            current_site = get_current_site(request) #get the current site domain
            mail_subject = 'Reset your password'
            message = render_to_string('accounts/reset_password.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encode the user id to base64 format, user.pk -> primary key of the user
                'token':default_token_generator.make_token(user), #generate a token for the user
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotpassword')
    return render(request, 'accounts/forgotpassword.html')

def resetpassword(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #decode the user id from base64 format
        user = Account._default_manager.get(pk=uid) #get the user from the database using the decoded user id
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token): #check if the token is valid for the user
        request.session['uid'] = uid #store the user id in the session
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword') #redirect to the reset password page where the user can enter the new password 
    else:
        messages.error(request, 'The reset password link is invalid! or expired.')
        return redirect('login')
    
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid') #get the user id from the session
            user = Account.objects.get(pk=uid) #get the user from the database using the
            user.set_password(password) #set the new password for the user
            user.save()
            messages.success(request, 'Password reset successful! You can now login with your new password.')  
            return redirect('login')

        else:
            messages.error(request, 'Passwords do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetpassword.html')