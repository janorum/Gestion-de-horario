from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    # Cambiamos el name a 'ver_calendario' para que coincida con el template base
    path('', views.vista_calendario, name='ver_calendario'),
    path('guardar/', views.api_guardar_evento, name='guardar_evento'),
    path('borrar/<int:id>/', views.api_borrar_evento, name='borrar_evento'),
]