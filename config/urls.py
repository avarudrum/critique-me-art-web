from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView

from accounts import views as account_views
from accounts.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('artwork/', include('artworks.urls')),
    # Its own prefix so a username can never collide with an auth URL.
    path('artist/<str:username>/', account_views.profile, name='profile'),
    path('accounts/', include('accounts.urls')),
    # Declared before the auth include so this one wins, purely to hand
    # LoginView a form whose labels match the rest of the site.
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(authentication_form=LoginForm),
        name='login',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('critiques/', include('critiques.urls')),
]   