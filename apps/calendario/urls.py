from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    # Cambiamos vista_calendario por CalendarioView.as_view()
    path('', views.CalendarioView.as_view(), name='ver_calendario'),
    
    # Cambiamos api_guardar_evento por GuardarEventoView.as_view()
    path('guardar/', views.GuardarEventoView.as_view(), name='guardar_evento'),
    
    # Cambiamos api_borrar_evento por BorrarEventoView.as_view()
    path('borrar/<int:id>/', views.BorrarEventoView.as_view(), name='borrar_evento'),
]