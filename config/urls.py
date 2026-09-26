from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from accounts import views as account_views
from artworks import views as artwork_views
from accounts.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', artwork_views.home, name='home'),
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
    # Same reason as the login override: declared first so it wins over the
    # stock LogoutView from the include below.
    path(
        'accounts/logout/',
        account_views.LogoutWithNoticeView.as_view(),
        name='logout',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('critiques/', include('critiques.urls')),
]   