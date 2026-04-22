import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.horario.models import RegistroDiario
from apps.horario.services.horario_service import HorarioService
from apps.opciones.models import ConfiguracionHorario, HorarioEspecial, HorarioDefecto, DiaHorarioEspecial

class HorarioSemanalView(LoginRequiredMixin, View):
    """Vista principal para la gestión de horarios filtrada por usuario."""
    template_name = 'horario/horario.html'

    def get(self, request, *args, **kwargs):
        fecha_str = request.GET.get('fecha')
        fecha_ref = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()

        # 1. Obtener datos de la semana del service
        datos_semana = HorarioService.obtener_datos_semana(fecha_ref, usuario=request.user)
        
        # Variables para recalcular el total semanal si inyectamos defaults
        total_semanal_decimal = 0.0

        # 2. Procesar cada día para inyectar Opciones si el registro está vacío
        for dia in datos_semana.get('dias', []):
            fecha_dia = dia['fecha']
            reg = dia['reg'] # El registro recuperado/creado por el service
            
            config = self._obtener_config_por_fecha(request.user, fecha_dia)
            
            # Comprobamos si el registro está vacío (no tiene ninguna hora puesta)
            es_registro_vacio = not (reg.m_in or reg.m_out or reg.t_in or reg.t_out)
            
            if es_registro_vacio:
                defaults = self._obtener_defaults(request.user, config, fecha_dia.isoweekday())
                if defaults:
                    # Inyectamos los valores de Opciones en el objeto 'reg' para que el template los vea
                    reg.m_in = defaults.m_in
                    reg.m_out = defaults.m_out
                    reg.t_in = defaults.t_in
                    reg.t_out = defaults.t_out
                    
                    # Recalculamos los strings de total que usa tu template basándonos en los nuevos datos
                    h_m = max(0, HorarioService.hhmm_a_decimal(reg.m_out) - HorarioService.hhmm_a_decimal(reg.m_in))
                    h_t = max(0, HorarioService.hhmm_a_decimal(reg.t_out) - HorarioService.hhmm_a_decimal(reg.t_in))
                    
                    dia['total_m_str'] = HorarioService.decimal_a_hhmm(h_m)
                    dia['total_t_str'] = HorarioService.decimal_a_hhmm(h_t)
                    dia['total_dia_str'] = HorarioService.decimal_a_hhmm(h_m + h_t)
            
            # Sumamos al total decimal de la semana para actualizar el resumen final
            total_semanal_decimal += HorarioService.hhmm_a_decimal(dia['total_dia_str'])
            dia['config_nombre'] = config.nombre if isinstance(config, HorarioEspecial) else "Horario Base"

        # 3. Actualizar los totales globales de la semana con la nueva suma
        objetivo = HorarioService.obtener_objetivo_semanal(request.user)
        datos_semana['totales_semanales']['total'] = HorarioService.decimal_a_hhmm(total_semanal_decimal)
        datos_semana['faltan_str'] = HorarioService.decimal_a_hhmm(max(0, objetivo - total_semanal_decimal))
        datos_semana['cumple'] = total_semanal_decimal >= objetivo

        context = {
            **datos_semana,
            'fecha_actual': fecha_ref,
            'fecha_hoy': date.today(),
            'semana_anterior': (fecha_ref - timedelta(days=7)).strftime('%Y-%m-%d'),
            'semana_siguiente': (fecha_ref + timedelta(days=7)).strftime('%Y-%m-%d'),
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
    """API para guardar cambios en tiempo real vía AJAX."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            campo = data.get('campo')
            valor = data.get('valor')

            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            config = self._obtener_config_por_fecha(request.user, fecha_dt)
            
            # El service ya garantiza que el registro existe por su get_or_create
            registro = RegistroDiario.objects.get(fecha=fecha_dt, usuario=request.user)
            
            # Si el registro estaba vacío antes de esta edición, aplicamos defaults
            if not (registro.m_in or registro.m_out or registro.t_in or registro.t_out):
                defaults = self._obtener_defaults(request.user, config, fecha_dt.isoweekday())
                if defaults:
                    registro.m_in = defaults.m_in
                    registro.m_out = defaults.m_out
                    registro.t_in = defaults.t_in
                    registro.t_out = defaults.t_out

            # Aplicar el cambio del usuario
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
        config, _ = ConfiguracionHorario.objects.get_or_create(usuario=usuario)
        return config

    def _obtener_defaults(self, usuario, config, dia_sem):
        if isinstance(config, HorarioEspecial):
            return DiaHorarioEspecial.objects.filter(periodo=config, dia_semana=dia_sem).first()
        return HorarioDefecto.objects.filter(usuario=usuario, dia_semana=dia_sem).first()