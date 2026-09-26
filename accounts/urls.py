from django.urls import path
from . import views

# Profiles deliberately live at /artist/<username>/ (wired in config/urls.py),
# not under this prefix: a <str:username> route here would shadow Django's own
# accounts/logout/ and accounts/password_reset/ URLs.
urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('settings/', views.edit_profile, name='edit_profile'),
]
