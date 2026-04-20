from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/horario/', permanent=True)),
    path('horario/', include('apps.horario.urls')),
    path('calendario/', include('apps.calendario.urls')),
]