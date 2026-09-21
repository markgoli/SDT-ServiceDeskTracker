
from pathlib import Path
import os
import dotenv
dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("APP_SECRET")

DEBUG = os.environ.get("APP_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'TickectTracker',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SDTracker.urls'

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
                'TickectTracker.context_processors.tracker_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'SDTracker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True



STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / "static",]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Service Desk Tracker: ManageEngine ServiceDesk Plus API ---

SDP_BASE_URL = os.environ.get("SDP_BASE_URL", "").strip()
SDP_AUTH_TOKEN = os.environ.get("SDP_AUTH_TOKEN", "").strip()
SDP_TEMPLATE_IDS = [
    t.strip() for t in os.environ.get("SDP_TEMPLATE_IDS", "").split(",") if t.strip()
]


def _parse_template_sla_days(raw):
    result = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        template_id, days = pair.split(":", 1)
        try:
            result[template_id.strip()] = int(days.strip())
        except ValueError:
            continue
    return result


# Fixed SLA day-window per template — see .env for the format/rationale.
SDP_TEMPLATE_SLA_DAYS = _parse_template_sla_days(os.environ.get("SDP_TEMPLATE_SLA_DAYS", ""))


def _parse_holidays(raw):
    from datetime import date

    result = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            result.add(date.fromisoformat(token))
        except ValueError:
            continue
    return result


SDP_HOLIDAYS = _parse_holidays(os.environ.get("SDP_HOLIDAYS", ""))

AUTO_REFRESH_MINUTES = int(os.environ.get("AUTO_REFRESH_MINUTES", "30"))

