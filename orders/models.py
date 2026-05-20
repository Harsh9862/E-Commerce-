from django.db import models
from accounts.models import Account
from store.models import Product, Variation

class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE) #foreign key to the user model, on_delete=models.CASCADE -> if the user is deleted then the payment will also be deleted
    payment_id = models.CharField(max_length=100) #payment id from the payment gateway -> razorpay_order_id -> gateway id for the order
    payment_method = models.CharField(max_length=100) #payment method used for the payment
    amount_paid = models.CharField(max_length=100) #amount paid for the order
    status = models.CharField(max_length=100) #status of the payment
    created_at = models.DateTimeField(auto_now_add=True) 
    
    def __str__(self):
        return self.payment_id
    
class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True) #foreign key to the user model, on_delete=models.SET_NULL -> if the user is deleted then the order will not be deleted but the user field will be set to null
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True) #foreign key to the payment model, on_delete=models.SET_NULL -> if the payment is deleted then the order will not be deleted but the payment field will be set to null
    order_number = models.CharField(max_length=20) #order number for the order
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=100) 
    address_line_2 = models.CharField(max_length=100, blank=True) #optional
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50) 
    order_note = models.CharField(max_length=100, blank=True) #order note for the order, field : optional
    order_total = models.FloatField()
    tax = models.FloatField() #tax amount for the order
    status = models.CharField(max_length=10, choices=STATUS, default='New') #status of the order, choices=STATUS -> this field can only have values from the STATUS tuple, default='New'
    ip = models.CharField(blank=True, max_length=20) #ip address of the customer
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) #updated at field to store the date and time when the order was updated


    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def __str__(self):
        return self.first_name
    
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE) #foreign key to the order model, on_delete=models.CASCADE -> if the order is deleted then the order product will also be deleted
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True) #foreign key to the payment model, on_delete=models.SET_NULL -> if the payment is deleted then the order product will not be deleted but the payment field will be set to null
    user = models.ForeignKey(Account, on_delete=models.CASCADE) #foreign key to the user model, on_delete=models.CASCADE -> if the user is deleted then the order product will also be deleted
    product = models.ForeignKey(Product, on_delete=models.CASCADE) #foreign key to the product model, on_delete=models.CASCADE -> if the product is deleted then the order product will also be deleted
    variation = models.ForeignKey(Variation, on_delete=models.SET_NULL, blank=True, null=True) #foreign key to the variation model, on_delete=models.SET_NULL -> if the variation is deleted then the order product will not be deleted but the variation field will be set to null
    cilor = models.CharField(max_length=50) #color of the product in the order
    size = models.CharField(max_length=50) #size of the product in the order
    quantity = models.IntegerField() #quantity of the product in the order
    product_price = models.FloatField() #price of the product in the order
    ordered = models.BooleanField(default=False) #ordered field to check if the order product is ordered or not
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) #updated at field to store the date and time when the order product was updated

    def __str__(self):
        return self.product.product_name