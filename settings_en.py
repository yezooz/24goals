import os

# Django settings for myscore project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG
LOGGING_DIR = [os.path.join(os.path.dirname(__file__), "logs")]
LOGGING_SHOW_METRICS = True

ADMINS = (
    ('Marek Mikuliszyn', 'marek@24gole.pl'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'myscore2'  # Or path to database file if using sqlite3.
DATABASE_USER = 'root'  # Not used with sqlite3.
DATABASE_PASSWORD = ''  # Not used with sqlite3.
DATABASE_HOST = ''  # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''  # Set to empty string for default. Not used with sqlite3.
DATABASE_OPTIONS = {
    'charset': 'utf8',
}

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Warsaw'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/static/media.lawrence.com/"
MEDIA_ROOT = os.path.dirname(__file__) + "/static/"

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = 'http://192.168.1.2:8000/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/static/", "/static/".
ADMIN_MEDIA_PREFIX = 'http://192.168.1.2:8000/static/'

MAX_PHOTO_UPLOAD_SIZE = '5120'
MAX_PHOTO_WIDTH = '10240'
MAX_PHOTO_HEIGHT = '10240'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    #     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    # 'myscore.libs.middleware.ban.Ban', # banowanie userow
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'myscore.libs.middleware.flash.Middleware',  # flash msgs
    'myscore.libs.middleware.logging.ActivityAndBanning',  # logowanie requestow uzytkownikow
    'myscore.libs.middleware.logging.WhoIsOnline',  # who's online ?
    'myscore.libs.djangologging.middleware.LoggingMiddleware',  # zapisywanie i przetwarzanie logow aplikacji
    'myscore.libs.middleware.cache.CacheMiddleware',  # browser caching headers
)

ROOT_URLCONF = 'myscore.urls'

# CACHE_BACKEND = 'file:///var/tmp/django'
# CACHE_BACKEND = 'memcached://192.168.1.2:11211/'
CACHE_BACKEND = 'dummy:///'
CACHE_MIDDLEWARE_SECONDS = 1
CACHE_MIDDLEWARE_KEY_PREFIX = ''

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    [os.path.join(os.path.dirname(__file__), "templates")]
)

STATIC_DIR = [os.path.join(os.path.dirname(__file__), "static")]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'myscore.main',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "myscore.libs.context_processors.layout.process",
    "myscore.libs.context_processors.layout.flash",
)

INTERNAL_IPS = ()
CURRENT_SEASON_ID = 3

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
)

AUTH_PROFILE_MODULE = 'main.Accounts'

EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = ''

ACCOUNT_ACTIVATION_DAYS = 3
TEST_DATABASE_COLLATION = "utf8_polish_ci"
USE_ETAGS = False
APPEND_SLASH = True
PER_PAGE = 20
