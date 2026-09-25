from django.urls import path
from . import views

urlpatterns = [
    path('artwork/<int:artwork_pk>/new/', views.create_critique, name='create_critique'),
    path('<int:pk>/edit/', views.edit_critique, name='edit_critique'),
    path('<int:pk>/delete/', views.delete_critique, name='delete_critique'),
]