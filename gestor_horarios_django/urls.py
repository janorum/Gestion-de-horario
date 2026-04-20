# gestor_horarios_django/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación Global
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Apps Protegidas
    path('horario/', include('apps.horario.urls')),
    path('calendario/', include('apps.calendario.urls')),
    path('opciones/', include('apps.opciones.urls')),
    
    # Ruta raíz: si alguien entra a la web vacía, lo mandamos al calendario (pedirá login)
    path('', auth_views.LoginView.as_view(template_name='login.html')), 
]