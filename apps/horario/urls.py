from django.urls import path
from . import views

app_name = 'horario'

urlpatterns = [
    path('', views.vista_semanal, name='horario_semanal'),
    path('api/guardar/', views.guardar_registro_ajax, name='api_guardar'),
]