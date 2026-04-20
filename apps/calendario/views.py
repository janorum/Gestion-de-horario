from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from .services.calendario_service import CalendarioService
from .models import EventoCalendario

class CalendarioView(LoginRequiredMixin, View):
    """Vista principal del calendario con lógica de navegación y filtrado por usuario."""
    template_name = 'calendario/calendario.html'

    def get(self, request, *args, **kwargs):
        hoy = datetime.now()
        
        # Capturar parámetros con validación básica
        try:
            año = int(request.GET.get('año', hoy.year))
            mes = int(request.GET.get('mes', hoy.month))
        except ValueError:
            año, mes = hoy.year, hoy.month

        # Manejar desbordamiento de meses (Navegación de flechas)
        if mes > 12:
            mes = 1
            año += 1
        elif mes < 1:
            mes = 12
            año -= 1

        # Obtener datos del servicio filtrados por el usuario actual
        datos = CalendarioService.obtener_mes(año, mes, request.user)
        
        nombres_meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        context = {
            # Datos del Calendario
            'semanas': datos['semanas'],
            'resumen_anual': datos['resumen_anual'],
            'tipos_opciones': datos['tipos_opciones'],
            
            # Estado de la Navegación
            'nombre_mes': nombres_meses[mes-1],
            'año': año,
            'mes': mes,
            
            # Datos de referencia para la UI
            'range_años': range(hoy.year - 5, hoy.year + 6),
            'año_hoy': hoy.year,
            'mes_hoy': hoy.month,
            'usuario': request.user,
        }
        
        return render(request, self.template_name, context)


class GuardarEventoView(LoginRequiredMixin, View):
    """API para crear o actualizar eventos del calendario del usuario."""
    
    def post(self, request, *args, **kwargs):
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion', '')

        if not fecha:
            return redirect('calendario:ver_calendario')

        if tipo == 'BORRAR':
            EventoCalendario.objects.filter(fecha=fecha, usuario=request.user).delete()
        elif tipo:
            EventoCalendario.objects.update_or_create(
                fecha=fecha, 
                usuario=request.user,
                defaults={'tipo': tipo, 'descripcion': descripcion}
            )
            
        return redirect('calendario:ver_calendario')


class BorrarEventoView(LoginRequiredMixin, View):
    """API para borrar un evento específico por ID asegurando propiedad del usuario."""
    
    def get(self, request, id, *args, **kwargs):
        # El filtro por usuario evita que alguien borre eventos de otros mediante la URL
        EventoCalendario.objects.filter(id=id, usuario=request.user).delete()
        return redirect('calendario:ver_calendario')