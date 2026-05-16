from django.contrib import messages,auth
from django.http import HttpResponse
from django.shortcuts import render,redirect

from accounts.models import Account
# use django forms for registration and login -> forms.py
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

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
            messages.success(request, 'You are now logged in.')
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
    

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

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