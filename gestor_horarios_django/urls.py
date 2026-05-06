# gestor_horarios_django/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .auth_views import registro_view, LoginConRegistroView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación Global
    path('login/', LoginConRegistroView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registro/', registro_view, name='registro'),

    # Apps Protegidas
    path('horario/', include('apps.horario.urls')),
    path('calendario/', include('apps.calendario.urls')),
    path('opciones/', include('apps.opciones.urls')),

    # Ruta raíz
    path('', LoginConRegistroView.as_view()),
]