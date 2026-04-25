from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from datetime import datetime
from .services.calendario_service import CalendarioService
from .models import EventoCalendario
# CORRECCIÓN: Importamos FestivoEspecial desde la app opciones
from apps.opciones.models import FestivoEspecial

class CalendarioView(LoginRequiredMixin, View):
    """Vista principal del calendario con lógica de navegación y filtrado por usuario."""
    template_name = 'calendario/calendario.html'

    def get(self, request, *args, **kwargs):
        hoy = datetime.now()
        
        try:
            año = int(request.GET.get('año', hoy.year))
            mes = int(request.GET.get('mes', hoy.month))
        except ValueError:
            año, mes = hoy.year, hoy.month

        if mes > 12:
            mes = 1
            año += 1
        elif mes < 1:
            mes = 12
            año -= 1

        # El service gestionará la lógica de los festivos especiales
        datos = CalendarioService.obtener_mes(año, mes, request.user)
        
        nombres_meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        context = {
            'semanas': datos['semanas'],
            'resumen_anual': datos['resumen_anual'],
            'tipos_opciones': datos['tipos_opciones'],
            'saldo': datos['saldo'],  # Objeto SaldoDias
            'nombre_mes': nombres_meses[mes-1],
            'año': año,
            'mes': mes,
            'range_años': range(hoy.year - 5, hoy.year + 6),
            'año_hoy': hoy.year,
            'mes_hoy': hoy.month,
            'usuario': request.user,
        }
        
        return render(request, self.template_name, context)


class GuardarEventoView(LoginRequiredMixin, View):
    """API para crear o actualizar eventos del calendario del usuario."""
    
    def post(self, request, *args, **kwargs):
        fecha_str = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion', '')

        if not fecha_str:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'No fecha'}, status=400)
            return redirect('calendario:ver_calendario')

        # Acción de guardar o borrar
        if tipo == 'BORRAR':
            EventoCalendario.objects.filter(fecha=fecha_str, usuario=request.user).delete()
        elif tipo:
            EventoCalendario.objects.update_or_create(
                fecha=fecha_str, 
                usuario=request.user,
                defaults={'tipo': tipo, 'descripcion': descripcion}
            )

        # Respuesta AJAX con saldos actualizados
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
            datos = CalendarioService.obtener_mes(fecha_dt.year, fecha_dt.month, request.user)
            
            return JsonResponse({
                'status': 'ok',
                'vacaciones_restantes': datos['saldo'].vacaciones_restantes,
                'asuntos_restantes': datos['saldo'].asuntos_restantes
            })
            
        return redirect('calendario:ver_calendario')


class BorrarEventoView(LoginRequiredMixin, View):
    """API para borrar un evento específico por ID asegurando propiedad del usuario."""
    
    def get(self, request, id, *args, **kwargs):
        evento = EventoCalendario.objects.filter(id=id, usuario=request.user).first()
        if evento:
            fecha_dt = evento.fecha
            evento.delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                datos = CalendarioService.obtener_mes(fecha_dt.year, fecha_dt.month, request.user)
                return JsonResponse({
                    'status': 'ok',
                    'vacaciones_restantes': datos['saldo'].vacaciones_restantes,
                    'asuntos_restantes': datos['saldo'].asuntos_restantes
                })

        return redirect('calendario:ver_calendario')