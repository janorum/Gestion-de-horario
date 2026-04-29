from django.urls import path
from .views import HorarioSemanalView, GuardarRegistroAjaxView

app_name = 'horario'

urlpatterns = [
    # Vista principal del horario semanal
    path('', HorarioSemanalView.as_view(), name='ver_horario'), 
    
    # Ruta crítica para el guardado automático vía AJAX
    # Esta URL debe coincidir con la llamada fetch en tu JS: '/horario/guardar-ajax/'
    path('guardar-ajax/', GuardarRegistroAjaxView.as_view(), name='guardar_registro_ajax'),
]