from django.urls import path
from . import views

urlpatterns = [
    # Authentication routes
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    path('get-meals/', views.getMeals, name='getMeals'),
    path('get-cals/', views.getCals, name='getCals'),
    path('get-workout/', views.getWorkout, name='getCals'),
    # path('get-workout/', views.CustomQueryView.as_view(), name='custom-query'),
    # path('get-cals/', views.CustomQueryView.as_view(), name='custom-query'),

]
