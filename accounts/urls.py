from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'), # even if we forget to go on accounts/dashboard/ and we go on accounts/ then also it will take us to the dashboard page.
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'), #this url will be used for account activation. it will take the user id and token as parameters.
    path('forgotpassword/', views.forgotpassword, name='forgotpassword'),
    path('resetpassword/<uidb64>/<token>/', views.resetpassword, name='resetpassword'),
     path('resetPassword/', views.resetPassword, name='resetPassword'),
]