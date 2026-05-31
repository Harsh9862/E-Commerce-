from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
# Create your models here.

class Product(models.Model):
    product_name  = models.CharField(max_length=50,unique=True)
    slug          = models.SlugField(max_length=100,unique=True)
    description   = models.TextField(max_length=200,blank=True)
    price         = models.IntegerField()
    images        = models.ImageField(upload_to='photos/product')
    stock         = models.IntegerField()
    is_available  = models.BooleanField(default=True)
    category      = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date  = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    def get_url(self):
        return reverse('product_detail', args = [self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
    

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager,self).filter(variation_category = 'color',is_active = True)
    def sizes(self):
        return super(VariationManager,self).filter(variation_category = 'size',is_active = True)
    

variation_category_choice = (
    ('color','color'),
    ('size','size'),
)    


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    variation_category = models.CharField(max_length=100,choices=variation_category_choice)
    variation_value = models.CharField(max_length = 100)
    is_active = models.BooleanField(default = True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager() # after creating VariationManager class we have to create its object here or we have to tell that about the manager then it will start working

    def __str__(self):
        return self.variation_value


class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f'{self.product.product_name} - {self.rating} stars by {self.user.email}'