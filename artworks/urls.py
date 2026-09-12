from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_artwork, name='upload_artwork'),
    path('<int:pk>/', views.artwork_detail, name='artwork_detail'),
]