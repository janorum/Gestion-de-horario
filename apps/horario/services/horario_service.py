from datetime import time, date, timedelta
from typing import Optional, Dict, Any, Union

class HorarioService:
    """Servicio centrado exclusivamente en cálculos de horas y jornadas semanales con soporte multiusuario."""

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
    def calcular_total_dia(cls, registro) -> float:
        if not registro:
            return 0.0
        h_m = max(0, cls.hhmm_a_decimal(registro.m_out) - cls.hhmm_a_decimal(registro.m_in))
        h_t = max(0, cls.hhmm_a_decimal(registro.t_out) - cls.hhmm_a_decimal(registro.t_in))
        return h_m + h_t

    @classmethod
    def obtener_objetivo_semanal(cls, usuario) -> float:
        """Calcula el objetivo de horas según la reducción de jornada del usuario."""
        from apps.horario.models import ReduccionHijos
        # Obtenemos o creamos la configuración específica para este usuario
        config_red, _ = ReduccionHijos.objects.get_or_create(usuario=usuario)
        
        base_semanal = 37.5 
        if config_red.activa:
            reduccion = base_semanal * (config_red.porcentaje / 100)
            return base_semanal - reduccion
        return base_semanal

    @classmethod
    def obtener_datos_semana(cls, fecha_referencia: date, usuario) -> Dict[str, Any]:
        """Recupera y calcula todos los datos de la semana para un usuario específico."""
        from apps.horario.models import RegistroDiario

        lunes = fecha_referencia - timedelta(days=fecha_referencia.weekday())
        dias_datos = []
        totales_m, totales_t = 0.0, 0.0
        nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

        for i in range(5):
            fecha_dia = lunes + timedelta(days=i)
            # Aseguramos que el registro pertenezca al usuario logueado
            reg, _ = RegistroDiario.objects.get_or_create(
                fecha=fecha_dia, 
                usuario=usuario
            )
            
            h_m = max(0, cls.hhmm_a_decimal(reg.m_out) - cls.hhmm_a_decimal(reg.m_in))
            h_t = max(0, cls.hhmm_a_decimal(reg.t_out) - cls.hhmm_a_decimal(reg.t_in))
            totales_m += h_m
            totales_t += h_t
            
            dias_datos.append({
                'nombre': nombres[i],
                'fecha': fecha_dia,
                'reg': reg,
                'total_m_str': cls.decimal_a_hhmm(h_m),
                'total_t_str': cls.decimal_a_hhmm(h_t),
                'total_dia_str': cls.decimal_a_hhmm(h_m + h_t)
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