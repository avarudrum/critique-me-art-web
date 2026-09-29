from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

# Off unless .env turns it on. Forgetting to set it on a server should give a
# plain error page, not a debug page that shows visitors your settings.
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Forms are POSTed with a CSRF token, and over HTTPS Django also checks the
# request came from a trusted origin -- so the live domain must be listed here
# or every form on the deployed site fails with 403.
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]

# Render sets this to the service's own domain (e.g. atelier.onrender.com), so
# that domain works without being typed into two settings by hand.
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Must come *after* staticfiles. It ships its own collectstatic, and the
    # first app listed wins a command name; its version reads a setting Django
    # 5.1 removed and crashes, which would fail every deploy build. It is only
    # here to configure the Cloudinary connection from CLOUDINARY_STORAGE.
    'cloudinary_storage',
    # Required by FORM_RENDERER below: it is what makes Django's own built-in
    # widget templates discoverable once form rendering goes through TEMPLATES.
    'django.forms',
    'cloudinary',
    'accounts',
    'artworks',
    'critiques',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # With DEBUG off, Django stops serving static files at all, and the site
    # goes live unstyled. WhiteNoise serves them instead. It sits right after
    # SecurityMiddleware, as its docs require, so CSS skips the rest of the stack.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# By default Django renders form widgets through a private template engine that
# only sees django/forms/templates and app-level template dirs -- it cannot see
# the project-level `templates/` directory configured above. This setting routes
# widget rendering through TEMPLATES instead, so a custom widget template can
# live at templates/artworks/widgets/ with every other template.
# It requires 'django.forms' in INSTALLED_APPS.
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# SQLite locally; on the server, DATABASE_URL points at PostgreSQL. A server's
# disk is wiped on every deploy, so a SQLite file there would lose every account
# and critique each time you pushed. conn_max_age reuses connections between
# requests instead of opening a new one each time.
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Project-level static files, mirroring how templates/ is organised.
STATICFILES_DIRS = [BASE_DIR / 'static']

# Where collectstatic will gather everything for deployment. Not used in
# development, where the staticfiles app serves from STATICFILES_DIRS directly.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise's storage gives each file a content hash in its name
# (atelier.3f9a1c.css), so browsers can cache it forever and still pick up a
# new version the moment the CSS changes. The default storage entry has to be
# restated because STORAGES replaces the whole dict, not just one key.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Only on the server: locally there is no HTTPS, so these would break login.
if not DEBUG:
    # Render terminates HTTPS and forwards plain HTTP, marking the original
    # scheme in this header. Without it Django thinks every request is
    # insecure and SECURE_SSL_REDIRECT would redirect forever.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Browsing is behind a login, so unauthenticated visitors land here.
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'browse'
LOGOUT_REDIRECT_URL = 'home'