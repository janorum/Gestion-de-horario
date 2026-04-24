import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.horario.models import RegistroDiario
from apps.horario.services.horario_service import HorarioService
from apps.opciones.models import ConfiguracionHorario, HorarioEspecial, HorarioDefecto, DiaHorarioEspecial
from apps.calendario.models import EventoCalendario

class HorarioSemanalView(LoginRequiredMixin, View):
    """Vista principal para la gestión de horarios integrada con Eventos de Calendario y Festivos Oficiales."""
    template_name = 'horario/horario.html'

    # Lista de festivos nacionales fijos (día, mes)
    FESTIVOS_NACIONALES = [
        (1, 1),   # Año Nuevo
        (6, 1),   # Reyes
        (1, 5),   # Fiesta del Trabajo
        (15, 8),  # Asunción
        (12, 10), # Fiesta Nacional
        (1, 11),  # Todos los Santos
        (6, 12),  # Constitución
        (8, 12),  # Inmaculada Concepción
        (25, 12), # Navidad
    ]

    def get(self, request, *args, **kwargs):
        fecha_str = request.GET.get('fecha')
        fecha_ref = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()

        # 1. Obtener datos de la semana del service
        datos_semana = HorarioService.obtener_datos_semana(fecha_ref, usuario=request.user)
        
        total_semanal_decimal = 0.0

        # 2. Procesar cada día para inyectar lógica de calendario y defaults
        for dia in datos_semana.get('dias', []):
            fecha_dia = dia['fecha']
            reg = dia['reg']
            
            # --- COMPROBACIÓN DE FESTIVO O EVENTO ---
            # A) Comprobar si es un festivo nacional fijo
            es_festivo_oficial = (fecha_dia.day, fecha_dia.month) in self.FESTIVOS_NACIONALES
            
            # B) Comprobar si hay evento en base de datos (Vacaciones, Asuntos, Festivo local...)
            evento = EventoCalendario.objects.filter(usuario=request.user, fecha=fecha_dia).first()

            if es_festivo_oficial or evento:
                # El día cuenta como 7h 30min (7.5 decimal)
                dia['es_festivo'] = True
                dia['tipo_evento'] = evento.get_tipo_display() if evento else "Festivo Oficial"
                
                # Inyectamos valores fijos para el cálculo
                dia['total_m_str'] = "07:30"
                dia['total_t_str'] = "00:00"
                dia['total_dia_str'] = "07:30"
                
                # Limpiamos los inputs del registro
                reg.m_in = reg.m_out = reg.t_in = reg.t_out = None
            else:
                # Día normal laboral
                dia['es_festivo'] = False
                config = self._obtener_config_por_fecha(request.user, fecha_dia)
                
                # Inyectar defaults si el registro está vacío
                if not (reg.m_in or reg.m_out or reg.t_in or reg.t_out):
                    defaults = self._obtener_defaults(request.user, config, fecha_dia.isoweekday())
                    if defaults:
                        reg.m_in = defaults.m_in
                        reg.m_out = defaults.m_out
                        reg.t_in = defaults.t_in
                        reg.t_out = defaults.t_out
                        
                        h_m = max(0, HorarioService.hhmm_a_decimal(reg.m_out) - HorarioService.hhmm_a_decimal(reg.m_in))
                        h_t = max(0, HorarioService.hhmm_a_decimal(reg.t_out) - HorarioService.hhmm_a_decimal(reg.t_in))
                        
                        dia['total_m_str'] = HorarioService.decimal_a_hhmm(h_m)
                        dia['total_t_str'] = HorarioService.decimal_a_hhmm(h_t)
                        dia['total_dia_str'] = HorarioService.decimal_a_hhmm(h_m + h_t)
                
                dia['config_nombre'] = config.nombre if isinstance(config, HorarioEspecial) else "Horario Base"

            # Sumar al total semanal
            total_semanal_decimal += HorarioService.hhmm_a_decimal(dia['total_dia_str'])

        # 3. Totales globales
        objetivo = HorarioService.obtener_objetivo_semanal(request.user)
        datos_semana['totales_semanales']['total'] = HorarioService.decimal_a_hhmm(total_semanal_decimal)
        datos_semana['faltan_str'] = HorarioService.decimal_a_hhmm(max(0, objetivo - total_semanal_decimal))
        datos_semana['cumple'] = total_semanal_decimal >= objetivo

        context = {
            **datos_semana,
            'fecha_ref': fecha_ref,
            'fecha_hoy': date.today(),
            'semana_anterior': (fecha_ref - timedelta(days=7)).strftime('%Y-%m-%d'),
            'semana_siguiente': (fecha_ref + timedelta(days=7)).strftime('%Y-%m-%d'),
            'config': ConfiguracionHorario.objects.get_or_create(usuario=request.user)[0],
        }
        
        return render(request, self.template_name, context)

    def _obtener_config_por_fecha(self, usuario, fecha):
        especiales = HorarioEspecial.objects.filter(usuario=usuario)
        for esp in especiales:
            inicio = date(fecha.year, esp.mes_inicio, esp.dia_inicio)
            fin = date(fecha.year, esp.mes_fin, esp.dia_fin)
            if (inicio <= fin and inicio <= fecha <= fin) or (inicio > fin and (fecha >= inicio or fecha <= fin)):
                return esp
        config, _ = ConfiguracionHorario.objects.get_or_create(usuario=usuario)
        return config

    def _obtener_defaults(self, usuario, config, dia_sem):
        if isinstance(config, HorarioEspecial):
            return DiaHorarioEspecial.objects.filter(periodo=config, dia_semana=dia_sem).first()
        return HorarioDefecto.objects.filter(usuario=usuario, dia_semana=dia_sem).first()


class GuardarRegistroAjaxView(LoginRequiredMixin, View):
    """API para guardar cambios vía AJAX, bloqueando días festivos o con eventos."""

    FESTIVOS_NACIONALES = HorarioSemanalView.FESTIVOS_NACIONALES

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            campo = data.get('campo')
            valor = data.get('valor')

            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Bloqueo: Festivos Oficiales o Eventos de Calendario
            es_festivo_fijo = (fecha_dt.day, fecha_dt.month) in self.FESTIVOS_NACIONALES
            es_evento = EventoCalendario.objects.filter(usuario=request.user, fecha=fecha_dt).exists()
            
            if es_festivo_fijo or es_evento:
                return JsonResponse({'status': 'error', 'message': 'Día festivo o evento. No editable.'}, status=403)

            config = self._obtener_config_por_fecha(request.user, fecha_dt)
            registro, _ = RegistroDiario.objects.get_or_create(fecha=fecha_dt, usuario=request.user)
            
            if not (registro.m_in or registro.m_out or registro.t_in or registro.t_out):
                defaults = self._obtener_defaults(request.user, config, fecha_dt.isoweekday())
                if defaults:
                    registro.m_in = defaults.m_in
                    registro.m_out = defaults.m_out
                    registro.t_in = defaults.t_in
                    registro.t_out = defaults.t_out

            if valor and valor.strip():
                setattr(registro, campo, valor)
            else:
                setattr(registro, campo, None)
            
            registro.save()

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

    def _obtener_config_por_fecha(self, usuario, fecha):
        especiales = HorarioEspecial.objects.filter(usuario=usuario)
        for esp in especiales:
            inicio = date(fecha.year, esp.mes_inicio, esp.dia_inicio)
            fin = date(fecha.year, esp.mes_fin, esp.dia_fin)
            if (inicio <= fin and inicio <= fecha <= fin) or (inicio > fin and (fecha >= inicio or fecha <= fin)):
                return esp
        return ConfiguracionHorario.objects.get_or_create(usuario=usuario)[0]

    def _obtener_defaults(self, usuario, config, dia_sem):
        if isinstance(config, HorarioEspecial):
            return DiaHorarioEspecial.objects.filter(periodo=config, dia_semana=dia_sem).first()
        return HorarioDefecto.objects.filter(usuario=usuario, dia_semana=dia_sem).first()