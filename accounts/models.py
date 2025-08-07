from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.

class MyAccountManager(BaseUserManager):                             # this is a Custom User Model for the Super Admin
    def create_user(self, first_name, last_name, username, email, password=None): # This is for creating a normal user
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise ValueError('User must have an username')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name
        )
        # normalize will convert the capital into small 

        user.set_password(password)      # for setting up the pass
        user.save(using = self._db)
        return user
    
    def create_superuser(self, first_name, last_name, email, username, password):  # And this is for creating superuser
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name=last_name,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using = self._db)
        return user


class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50,unique = True)
    email = models.EmailField(max_length=50,unique=True)
    phone_number = models.CharField(max_length=15,null=True)

    # required fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)  # or we can remove it django handles it
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'              # now we will be able to login with the 'email' field
    REQUIRED_FIELDS = ['username','first_name','last_name']

    objects = MyAccountManager()     # for telling the Account that we are using MyAccountManager for all the operations i.e. creating user and superuser

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):   # means if the user is admin then he has the permission to do changes
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True
    
    
    
'''Django models are organized inside apps (like accounts, blog, store, etc.).

So, when Django checks for permissions or module access, it passes the app_label (i.e., the app name as a string) to your custom user model.

✅ Example
Suppose you have an app called accounts, and you register a model called Account.

Then the app_label for that model is 'accounts'.

When Django calls:

user.has_module_perms('accounts')
It's asking:

“Does this user have permission to access the models/views inside the accounts app?”

✅ Purpose in Your Model
In your custom user model, you added:

def has_module_perms(self, app_label):
    return True
This tells Django:

“Yes, this user has permission to access any part of any app.”

You could also make it conditional, like:

def has_module_perms(self, app_label):
    return self.is_admin or app_label == 'accounts'
✅ Related: has_perm()
has_perm() checks permission for a specific action like accounts.add_user

has_module_perms() checks permission for the whole app/module

✅ Summary
Term	Meaning
app_label	The name of the Django app (accounts, blog, etc.)
Used in	Permissions, admin site, access control
You return	True to allow access, False to deny'''