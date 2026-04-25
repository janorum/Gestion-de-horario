from datetime import time, date, timedelta
from typing import Optional, Dict, Any, Union
from apps.opciones.models import ConfiguracionHorario, HorarioEspecial, FestivoEspecial

class HorarioService:
    """Servicio centrado en cálculos de horas y jornadas semanales respetando restricciones de Opciones."""

    @staticmethod
    def hhmm_a_decimal(hora: Union[time, str, None]) -> float:
        if not hora:
            return 0.0
        if isinstance(hora, str):
            try:
                h, m = map(int, hora.split(':'))
                return h + (m / 60.0)
            except (ValueError, AttributeError, IndexError):
                return 0.0
        return hora.hour + (hora.minute / 60.0)

    @staticmethod
    def decimal_a_hhmm(horas_decimales: float) -> str:
        if horas_decimales <= 0:
            return "00:00"
        horas = int(horas_decimales)
        minutos = int(round((horas_decimales - horas) * 60))
        if minutos == 60:
            horas += 1
            minutos = 0
        return f"{horas:02d}:{minutos:02d}"

    @classmethod
    def obtener_config_por_fecha(cls, usuario, fecha: date):
        """Busca si aplica un periodo especial o la configuración base."""
        especiales = HorarioEspecial.objects.filter(usuario=usuario)
        for esp in especiales:
            inicio = date(fecha.year, esp.mes_inicio, esp.dia_inicio)
            fin = date(fecha.year, esp.mes_fin, esp.dia_fin)
            if (inicio <= fin and inicio <= fecha <= fin) or (inicio > fin and (fecha >= inicio or fecha <= fin)):
                return esp
        config, _ = ConfiguracionHorario.objects.get_or_create(usuario=usuario)
        return config

    @classmethod
    def calcular_horas_reales(cls, reg, config, fecha: date) -> tuple[float, float]:
        """Calcula horas de mañana y tarde aplicando topes, límites y horas por festivos (oficiales, manuales y recurrentes)."""
        from apps.calendario.models import EventoCalendario
        
        # 1. Comprobación de Festivo/Permiso para computar horas automáticas
        
        # A. Evento manual en el calendario (VAC, ASU, etc)
        evento = EventoCalendario.objects.filter(usuario=reg.usuario, fecha=fecha).first()
        
        # B. Festivo oficial (Holidays)
        import holidays
        festivos_oficiales = holidays.CountryHoliday('ES', prov='GA', years=fecha.year)
        es_festivo_oficial = fecha in festivos_oficiales
        
        # C. Festivo Especial/Recurrente (Configurado en Opciones)
        es_festivo_recurrente = FestivoEspecial.objects.filter(
            usuario=reg.usuario, 
            dia=fecha.day, 
            mes=fecha.month
        ).exists()

        # Si el día es festivo por cualquiera de las 3 vías, aplicamos horas configuradas
        if evento or es_festivo_oficial or es_festivo_recurrente:
            horas_computables = getattr(config, 'horas_festivo', 7.5)
            return round(horas_computables, 2), 0.0

        # 2. Cálculo para día laboral normal (Fichajes)
        h_m = 0.0
        if reg.m_in and reg.m_out:
            mi = cls.hhmm_a_decimal(reg.m_in)
            mo = cls.hhmm_a_decimal(reg.m_out)
            inicio_c = cls.hhmm_a_decimal(config.hora_inicio_conteo)
            tope_m = cls.hhmm_a_decimal(config.max_hora_manana)
            
            dia_sem = fecha.isoweekday()
            if isinstance(config, HorarioEspecial):
                dias_tele = config.get_dias_list_tele()
                limit_m = config.max_teletrabajo if dia_sem in dias_tele else config.max_presencial
            else:
                dias_tele = config.get_dias_list('dias_teletrabajo')
                limit_m = config.max_horas_manana_teletrabajo if dia_sem in dias_tele else config.max_horas_manana_presencial

            calc_m = max(0, min(mo, tope_m) - max(mi, inicio_c))
            h_m = min(calc_m, limit_m)

        h_t = 0.0
        if reg.t_in and reg.t_out:
            ti = cls.hhmm_a_decimal(reg.t_in)
            to = cls.hhmm_a_decimal(reg.t_out)
            tope_m = cls.hhmm_a_decimal(config.max_hora_manana)
            tope_t = cls.hhmm_a_decimal(config.max_hora_tarde)
            limit_t = config.max_horas_tarde

            calc_t = max(0, min(to, tope_t) - max(ti, tope_m))
            h_t = min(calc_t, limit_t)

        return round(h_m, 2), round(h_t, 2)

    @classmethod
    def calcular_total_dia(cls, registro) -> float:
        """Calcula el total diario sumando mañana y tarde."""
        if not registro:
            return 0.0
        config = cls.obtener_config_por_fecha(registro.usuario, registro.fecha)
        h_m, h_t = cls.calcular_horas_reales(registro, config, registro.fecha)
        return h_m + h_t

    @classmethod
    def obtener_objetivo_semanal(cls, usuario) -> float:
        """Calcula el objetivo de horas según el periodo actual."""
        config_opc = cls.obtener_config_por_fecha(usuario, date.today())
        if isinstance(config_opc, ConfiguracionHorario):
            return config_opc.horas_semanales_estandar
        return config_opc.horas_semanales

    @classmethod
    def obtener_datos_semana(cls, fecha_referencia: date, usuario) -> Dict[str, Any]:
        """Recupera el desglose semanal para la vista de horario."""
        from apps.horario.models import RegistroDiario

        lunes = fecha_referencia - timedelta(days=fecha_referencia.weekday())
        dias_datos = []
        totales_m, totales_t = 0.0, 0.0
        nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

        for i in range(5):
            fecha_dia = lunes + timedelta(days=i)
            reg, _ = RegistroDiario.objects.get_or_create(fecha=fecha_dia, usuario=usuario)
            config = cls.obtener_config_por_fecha(usuario, fecha_dia)
            h_m, h_t = cls.calcular_horas_reales(reg, config, fecha_dia)
            
            totales_m += h_m
            totales_t += h_t
            
            dia_sem = fecha_dia.isoweekday()
            if isinstance(config, HorarioEspecial):
                es_tele = dia_sem in config.get_dias_list_tele()
            else:
                es_tele = dia_sem in config.get_dias_list('dias_teletrabajo')

            dias_datos.append({
                'nombre': nombres[i],
                'fecha': fecha_dia,
                'reg': reg,
                'total_m_str': cls.decimal_a_hhmm(h_m),
                'total_t_str': cls.decimal_a_hhmm(h_t),
                'total_dia_str': cls.decimal_a_hhmm(h_m + h_t),
                'es_teletrabajo': es_tele
            })

        objetivo = cls.obtener_objetivo_semanal(usuario)
        total_sem = totales_m + totales_t
        
        return {
            'dias': dias_datos,
            'lunes': lunes,
            'fecha_ref': fecha_referencia,
            'obj_sem_str': cls.decimal_a_hhmm(objetivo),
            'totales_semanales': {
                'mañana': cls.decimal_a_hhmm(totales_m),
                'tarde': cls.decimal_a_hhmm(totales_t),
                'total': cls.decimal_a_hhmm(total_sem),
            },
            'faltan_str': cls.decimal_a_hhmm(max(0, objetivo - total_sem)),
            'cumple': total_sem >= objetivo,
        }