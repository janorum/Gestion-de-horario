import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.horario.models import RegistroDiario
from apps.horario.services.horario_service import HorarioService

class HorarioSemanalView(LoginRequiredMixin, View):
    """Vista principal para la gestión de horarios filtrada por usuario."""
    template_name = 'horario/horario.html'

    def get(self, request, *args, **kwargs):
        fecha_str = request.GET.get('fecha')
        
        # Validación de fecha y navegación
        if fecha_str:
            try:
                fecha_ref = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_ref = date.today()
        else:
            fecha_ref = date.today()

        # Obtener datos de la semana filtrados por el usuario logueado
        # Nota: Asegúrate de pasar request.user al service para que filtre los registros
        datos_semana = HorarioService.obtener_datos_semana(fecha_ref, usuario=request.user)
        
        # Contexto profesional con navegación
        context = {
            **datos_semana,
            'fecha_actual': fecha_ref,
            'fecha_hoy': date.today(),
            'semana_anterior': (fecha_ref - timedelta(days=7)).strftime('%Y-%m-%d'),
            'semana_siguiente': (fecha_ref + timedelta(days=7)).strftime('%Y-%m-%d'),
        }
        
        return render(request, self.template_name, context)


class GuardarRegistroAjaxView(LoginRequiredMixin, View):
    """API para guardar cambios en tiempo real vía AJAX."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            campo = data.get('campo')
            valor = data.get('valor')

            if not fecha_str or not campo:
                return JsonResponse({'status': 'error', 'message': 'Datos incompletos'}, status=400)

            # Buscamos o creamos el registro para este usuario específico
            registro, _ = RegistroDiario.objects.get_or_create(
                fecha=fecha_str, 
                usuario=request.user
            )
            
            # Asignación dinámica del campo (m_in, m_out, etc.)
            if valor and valor.strip():
                setattr(registro, campo, valor)
            else:
                setattr(registro, campo, None)
            
            registro.save()

            # Cálculos automáticos para la respuesta AJAX
            h_m = max(0, HorarioService.hhmm_a_decimal(registro.m_out) - HorarioService.hhmm_a_decimal(registro.m_in))
            h_t = max(0, HorarioService.hhmm_a_decimal(registro.t_out) - HorarioService.hhmm_a_decimal(registro.t_in))
            
            return JsonResponse({
                'status': 'success',
                'subtotal_m': HorarioService.decimal_a_hhmm(h_m),
                'subtotal_t': HorarioService.decimal_a_hhmm(h_t),
                'total_dia': HorarioService.decimal_a_hhmm(h_m + h_t)
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)