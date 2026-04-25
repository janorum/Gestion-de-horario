import json
from datetime import datetime, date, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.horario.models import RegistroDiario
from apps.horario.services.horario_service import HorarioService
from apps.opciones.models import ConfiguracionHorario, HorarioEspecial, HorarioDefecto, DiaHorarioEspecial
from apps.calendario.models import EventoCalendario

class HorarioSemanalView(LoginRequiredMixin, View):
    """Vista principal para la gestión de horarios con desbloqueo de tarde garantizado."""
    template_name = 'horario/horario.html'

    FESTIVOS_NACIONALES = [
        (1, 1), (6, 1), (1, 5), (15, 8), (12, 10), (1, 11), (6, 12), (8, 12), (25, 12),
    ]

    def get(self, request, *args, **kwargs):
        fecha_str = request.GET.get('fecha')
        fecha_ref = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()

        datos_semana = HorarioService.obtener_datos_semana(fecha_ref, usuario=request.user)
        total_semanal_decimal = 0.0

        for dia in datos_semana.get('dias', []):
            fecha_dia = dia['fecha']
            reg = dia['reg']
            dia_semana_num = str(fecha_dia.isoweekday()) # "1" a "7"
            
            es_festivo_oficial = (fecha_dia.day, fecha_dia.month) in self.FESTIVOS_NACIONALES
            evento = EventoCalendario.objects.filter(usuario=request.user, fecha=fecha_dia).first()

            if es_festivo_oficial or evento:
                dia['es_festivo'] = True
                dia['tipo_evento'] = evento.get_tipo_display() if evento else "Festivo Oficial"
                dia['total_m_str'], dia['total_t_str'], dia['total_dia_str'] = "07:30", "00:00", "07:30"
                dia['alertas'], dia['incumple'], dia['tiene_tarde'] = [], False, False
                reg.m_in = reg.m_out = reg.t_in = reg.t_out = None
            else:
                dia['es_festivo'] = False
                config = self._obtener_config_por_fecha(request.user, fecha_dia)
                
                # --- LÓGICA DE DESBLOQUEO DE TARDE (EXTRACCIÓN DIRECTA) ---
                if isinstance(config, HorarioEspecial):
                    # Asumimos que en HorarioEspecial el campo se llama dias_obligatorios_tarde o similar
                    # Si el modelo HorarioEspecial no tiene get_dias_list, lo hacemos manual:
                    raw_dias = getattr(config, 'dias_obligatorios_tarde', "")
                else:
                    raw_dias = config.dias_obligatorios_tarde
                
                # Limpiamos la cadena (quitamos espacios) y convertimos en lista
                lista_tardes = [d.strip() for d in str(raw_dias).split(',') if d.strip()]
                
                # IMPORTANTE: dia_semana_num es string ("2"), lista_tardes son strings (["2", "4"])
                dia['tiene_tarde'] = dia_semana_num in lista_tardes
                
                # Inyectar defaults si el registro está vacío
                if not (reg.m_in or reg.m_out or reg.t_in or reg.t_out):
                    defaults = self._obtener_defaults(request.user, config, int(dia_semana_num))
                    if defaults:
                        reg.m_in, reg.m_out = defaults.m_in, defaults.m_out
                        reg.t_in, reg.t_out = defaults.t_in, defaults.t_out
                
                # Cálculo y validación
                h_m, h_t = HorarioService.calcular_horas_reales(reg, config, fecha_dia)
                dia['alertas'], dia['incumple'] = self._validar_registro(reg, config, fecha_dia)
                
                dia['total_m_str'] = HorarioService.decimal_a_hhmm(h_m)
                dia['total_t_str'] = HorarioService.decimal_a_hhmm(h_t)
                dia['total_dia_str'] = HorarioService.decimal_a_hhmm(h_m + h_t)
                dia['config_nombre'] = config.nombre if isinstance(config, HorarioEspecial) else "Horario Base"

            total_semanal_decimal += HorarioService.hhmm_a_decimal(dia['total_dia_str'])

        objetivo = HorarioService.obtener_objetivo_semanal(request.user)
        datos_semana['totales_semanales']['total'] = HorarioService.decimal_a_hhmm(total_semanal_decimal)
        datos_semana['faltan_str'] = HorarioService.decimal_a_hhmm(max(0, objetivo - total_semanal_decimal))
        datos_semana['cumple'] = total_semanal_decimal >= objetivo

        context = {
            **datos_semana,
            'fecha_ref': fecha_ref,
            'fecha_hoy': date.today(),
            'config': ConfiguracionHorario.objects.get_or_create(usuario=request.user)[0],
        }
        return render(request, self.template_name, context)

    def _validar_registro(self, reg, config, fecha):
        alertas = []
        incumple = False
        if not reg.m_in or not reg.m_out: return alertas, incumple
        
        mi, mo = HorarioService.hhmm_a_decimal(reg.m_in), HorarioService.hhmm_a_decimal(reg.m_out)
        if mi > HorarioService.hhmm_a_decimal(config.oblig_manana_in):
            alertas.append(f"Entrada tardía ({config.oblig_manana_in})"); incumple = True
        if mo < HorarioService.hhmm_a_decimal(config.oblig_manana_out):
            alertas.append(f"Salida temprana ({config.oblig_manana_out})"); incumple = True
        return alertas, incumple

    def _obtener_config_por_fecha(self, usuario, fecha):
        especiales = HorarioEspecial.objects.filter(usuario=usuario)
        for esp in especiales:
            inicio, fin = date(fecha.year, esp.mes_inicio, esp.dia_inicio), date(fecha.year, esp.mes_fin, esp.dia_fin)
            if (inicio <= fin and inicio <= fecha <= fin) or (inicio > fin and (fecha >= inicio or fecha <= fin)):
                return esp
        return ConfiguracionHorario.objects.get_or_create(usuario=usuario)[0]

    def _obtener_defaults(self, usuario, config, dia_sem):
        if isinstance(config, HorarioEspecial):
            return DiaHorarioEspecial.objects.filter(periodo=config, dia_semana=dia_sem).first()
        return HorarioDefecto.objects.filter(usuario=usuario, dia_semana=dia_sem).first()

class GuardarRegistroAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            fecha_dt = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date()
            
            es_festivo = (fecha_dt.day, fecha_dt.month) in HorarioSemanalView.FESTIVOS_NACIONALES
            if es_festivo or EventoCalendario.objects.filter(usuario=request.user, fecha=fecha_dt).exists():
                return JsonResponse({'status': 'error', 'message': 'Día no editable.'}, status=403)

            config = HorarioSemanalView()._obtener_config_por_fecha(request.user, fecha_dt)
            registro, _ = RegistroDiario.objects.get_or_create(fecha=fecha_dt, usuario=request.user)
            
            setattr(registro, data.get('campo'), data.get('valor') if data.get('valor') else None)
            registro.save()

            h_m, h_t = HorarioService.calcular_horas_reales(registro, config, fecha_dt)
            alertas, incumple = HorarioSemanalView()._validar_registro(registro, config, fecha_dt)
            
            return JsonResponse({
                'status': 'success',
                'subtotal_m': HorarioService.decimal_a_hhmm(h_m),
                'subtotal_t': HorarioService.decimal_a_hhmm(h_t),
                'total_dia': HorarioService.decimal_a_hhmm(h_m + h_t),
                'alertas': alertas,
                'incumple': incumple
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)