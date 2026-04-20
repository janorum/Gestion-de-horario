from django.urls import path
from .views import HorarioSemanalView, GuardarRegistroAjaxView

app_name = 'horario' # Este es el prefijo 'horario:'

urlpatterns = [
    # El nombre 'ver_horario' es el que busca el template
    path('', HorarioSemanalView.as_view(), name='ver_horario'), 
    path('ajax/guardar/', GuardarRegistroAjaxView.as_view(), name='guardar_registro_ajax'),
]