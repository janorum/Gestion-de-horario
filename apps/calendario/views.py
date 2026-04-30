import json
from datetime import datetime, date
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from .services.calendario_service import CalendarioService
from .models import EventoCalendario
# Importación corregida para acceder a los festivos recurrentes
from apps.opciones.models import FestivoEspecial, ConfiguracionHorario

class CalendarioView(LoginRequiredMixin, View):
    """Vista principal del calendario con lógica de navegación y filtrado por usuario."""
    template_name = 'calendario/calendario.html'

    def get(self, request, *args, **kwargs):
        hoy = date.today()
        
        try:
            año = int(request.GET.get('año', hoy.year))
            mes = int(request.GET.get('mes', hoy.month))
        except ValueError:
            año, mes = hoy.year, hoy.month

        # Lógica de desbordamiento de meses (navegación con flechas)
        if mes > 12:
            mes = 1
            año += 1
        elif mes < 1:
            mes = 12
            año -= 1

        # El service gestiona la lógica de días, festivos oficiales y recurrentes
        datos = CalendarioService.obtener_mes(año, mes, request.user)
        
        nombres_meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        context = {
            'semanas': datos['semanas'],
            'resumen_anual': datos['resumen_anual'],
            'tipos_opciones': datos['tipos_opciones'],
            'saldo': datos['saldo'],  # Objeto con vacaciones_restantes y asuntos_restantes
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
    """API para crear o actualizar eventos del calendario del usuario (Modo Pintura)."""
    
    def post(self, request, *args, **kwargs):
        fecha_str = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion', '')

        if not fecha_str:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Fecha no proporcionada'}, status=400)
            return redirect('calendario:ver_calendario')

        # Acción de guardar o borrar según el pincel seleccionado
        if tipo == 'BORRAR':
            EventoCalendario.objects.filter(fecha=fecha_str, usuario=request.user).delete()
        elif tipo:
            EventoCalendario.objects.update_or_create(
                fecha=fecha_str, 
                usuario=request.user,
                defaults={'tipo': tipo, 'descripcion': descripcion}
            )

        # Si es AJAX (Modo Pintura), devolvemos los saldos actualizados para refrescar los contadores
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            datos = CalendarioService.obtener_mes(fecha_dt.year, fecha_dt.month, request.user)
            
            return JsonResponse({
                'status': 'ok',
                'vacaciones_restantes': datos['saldo'].vacaciones_restantes,
                'asuntos_restantes': datos['saldo'].asuntos_restantes,
                'enfermedad_sin_justificar_restantes': datos['saldo'].enfermedad_sin_justificar_restantes  # Campo añadido
            })
            
        return redirect('calendario:ver_calendario')


class BorrarEventoView(LoginRequiredMixin, View):
    """API para borrar un evento específico desde la lista del resumen anual."""
    
    def get(self, request, id, *args, **kwargs):
        evento = EventoCalendario.objects.filter(id=id, usuario=request.user).first()
        if evento:
            fecha_dt = evento.fecha
            evento.delete()
            
            # Devolvemos respuesta AJAX para actualizar la UI sin recargar
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                datos = CalendarioService.obtener_mes(fecha_dt.year, fecha_dt.month, request.user)
                return JsonResponse({
                    'status': 'ok',
                    'vacaciones_restantes': datos['saldo'].vacaciones_restantes,
                    'asuntos_restantes': datos['saldo'].asuntos_restantes
                })

        return redirect('calendario:ver_calendario')