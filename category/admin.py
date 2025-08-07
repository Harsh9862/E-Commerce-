from django.contrib import admin
from . models import Category

# Register your models here. Whatever u want to shown in the admin
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('category_name',)}
    list_display = ('category_name','slug')
    #ordering = ('category_name',)

admin.site.register(Category,CategoryAdmin)