import calendar
import holidays
from datetime import date
from typing import Dict, Any, List
from apps.calendario.models import EventoCalendario

class CalendarioService:
    """Servicio maestro filtrado por usuario autenticado."""

    @staticmethod
    def obtener_mapeo_colores():
        return {
            'FESTIVO': 'FESTIVO', 'FESTIVO_EXTRA': 'FESTIVO_EXTRA', 'VACACIONES': 'VACACIONES',
            'ASUNTOS_PROPIOS': 'ASUNTOS_PROPIOS', 'BAJA': 'BAJA', 'ENFERMEDAD': 'ENFERMEDAD',
            'SIN_SUELDO': 'SIN_SUELDO', 'OTRO': 'OTRO',
        }

    @staticmethod
    def traducir_festivo(nombre_en: str) -> str:
        traducciones = {
            "New Year's Day": "Año Nuevo", "Epiphany": "Reyes Magos", "Saint Joseph's Day": "San José",
            "Maundy Thursday": "Jueves Santo", "Good Friday": "Viernes Santo", "Fiesta Nacional": "Fiesta Nacional",
            "Constitution Day": "Constitución", "Christmas Day": "Navidad"
        }
        return traducciones.get(nombre_en, nombre_en)

    @classmethod
    def obtener_mes(cls, año: int, mes: int, usuario: Any) -> Dict[str, Any]:
        from apps.horario.services.horario_service import HorarioService
        from apps.horario.models import RegistroDiario
        
        hoy = date.today()
        cal = calendar.Calendar(firstweekday=0)
        mes_it = cal.monthdatescalendar(año, mes)
        
        festivos_oficiales = holidays.CountryHoliday('ES', prov='GA', years=año)
        # FILTRO POR USUARIO:
        eventos_db = EventoCalendario.objects.filter(fecha__year=año, usuario=usuario)
        
        mapa_eventos = {}
        for fecha, nombre in festivos_oficiales.items():
            mapa_eventos[fecha] = {'tipo': 'FESTIVO', 'label': 'FESTIVO', 'desc': cls.traducir_festivo(nombre), 'es_oficial': True}
        
        for e in eventos_db:
            tipo_key = 'FESTIVO_EXTRA' if e.tipo == 'FESTIVO' else e.tipo
            mapa_eventos[e.fecha] = {
                'tipo': tipo_key, 'label': e.get_tipo_display(), 'desc': e.descripcion, 'es_oficial': False, 'id': e.id
            }

        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        resumen_anual = {nombre: {'eventos': [], 'conteos': {}} for nombre in meses_nombres}
        
        for fecha, info in sorted(mapa_eventos.items()):
            nombre_mes = meses_nombres[fecha.month-1]
            tipo = info['tipo']
            resumen_anual[nombre_mes]['eventos'].append({
                'id': info.get('id'), 'fecha': fecha, 'nombre': info['desc'] or info['label'],
                'tipo_label': info['label'], 'tipo_raw_clase': tipo,
                'borrable': not info.get('es_oficial', False) and info.get('id') is not None
            })
            conteos = resumen_anual[nombre_mes]['conteos']
            conteos[tipo] = conteos.get(tipo, 0) + 1

        # FILTRO POR USUARIO EN REGISTROS DIARIOS:
        registros = {r.fecha: r for r in RegistroDiario.objects.filter(fecha__year=año, fecha__month=mes, usuario=usuario)}
        
        semanas = []
        for semana in mes_it:
            dias_semana = []
            for dia in semana:
                reg = registros.get(dia)
                ev = mapa_eventos.get(dia)
                total_dia = HorarioService.calcular_total_dia(reg) if reg else 0.0
                dias_semana.append({
                    'dia': dia.day, 'fecha': dia.strftime('%Y-%m-%d'), 'es_mes_actual': dia.month == mes,
                    'es_hoy': dia == hoy, 'total_str': HorarioService.decimal_a_hhmm(total_dia) if total_dia > 0 else "",
                    'tipo_dia': ev['label'] if ev else "", 'tipo_raw': ev['tipo'] if ev else "",
                    'descripcion': ev['desc'] if ev else "", 'es_oficial': ev.get('es_oficial', False) if ev else False,
                })
            semanas.append(dias_semana)
            
        return {'semanas': semanas, 'resumen_anual': resumen_anual, 'tipos_opciones': EventoCalendario.TIPO_CHOICES}