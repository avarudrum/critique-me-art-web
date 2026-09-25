from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_artwork, name='upload_artwork'),
    path('browse/', views.browse, name='browse'),
    path('<int:pk>/', views.artwork_detail, name='artwork_detail'),
    path('<int:pk>/edit/', views.edit_artwork, name='edit_artwork'),
    path('<int:pk>/delete/', views.delete_artwork, name='delete_artwork'),
]