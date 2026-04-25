from django.urls import path
from .views import OpcionesMainView, PerfilUsuarioView

# El app_name debe coincidir con el prefijo usado en el template {% url 'opciones:main' %}
app_name = 'opciones'

urlpatterns = [
    # Ruta principal para la configuración del usuario
    path('', OpcionesMainView.as_view(), name='main'),
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil'),
]