from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('run_gege/', views.run_gege, name='run_gege'),
    path('display_csv/', views.display_csv, name='display_csv'),
]
