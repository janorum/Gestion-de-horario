"""
Django settings for gestor_horarios_django project.
Optimizado para estructura de carpetas 'apps/' y localización en España.
"""

import os
import sys
from pathlib import Path

# 1. Definición de Rutas Base
BASE_DIR = Path(__file__).resolve().parent.parent

# FUNDAMENTAL: Añadimos la carpeta 'apps' al path de Python para que las importaciones funcionen
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# SECURITY WARNING: Pon aquí tu clave secreta real
SECRET_KEY = 'django-insecure-tu-clave-aqui'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# 2. Definición de Aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Tus aplicaciones (usando la ruta absoluta para evitar conflictos de labels)
    'apps.horario.apps.HorarioConfig',
    'apps.calendario',
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

ROOT_URLCONF = 'gestor_horarios_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Definimos explícitamente dónde buscar los templates globales y de apps
        'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestor_horarios_django.wsgi.application'

# 3. Base de Datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 4. Validación de Contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 5. Internacionalización (Configurado para España)
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_L10N = True
USE_I18N = True

USE_TZ = True # Manejo de cambios de hora verano/invierno

# 6. Archivos Estáticos (CSS, JS)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 7. Tipo de clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'