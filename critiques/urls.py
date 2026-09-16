from django.urls import path
from . import views

urlpatterns = [
    path('artwork/<int:artwork_pk>/new/', views.create_critique, name='create_critique'),
]