import calendar
import holidays
from datetime import date
from typing import Dict, Any, List
from apps.calendario.models import EventoCalendario

class CalendarioService:
    """Servicio maestro de fechas y eventos con mapeo de colores corregido."""

    @staticmethod
    def obtener_mapeo_colores():
        """Define la identidad visual. Aseguramos que 'OTRO' tenga su color."""
        return {
            'FESTIVO':        'bg-danger text-white',      
            'VACACIONES':     'bg-success text-white',     
            'ASUNTOS_PROPIOS':'bg-primary text-white',     
            'BAJA':           'bg-warning text-dark',      
            'ENFERMEDAD':     'bg-info text-dark',         
            'SIN_SUELDO':     'bg-secondary text-white',
            'OTRO':           'bg-secondary text-white', # Color para el tipo OTRO
        }

    @staticmethod
    def traducir_festivo(nombre_en: str) -> str:
        traducciones = {
            "New Year's Day": "Año Nuevo", "Epiphany": "Reyes Magos",
            "Saint Joseph's Day": "San José", "Maundy Thursday": "Jueves Santo",
            "Good Friday": "Viernes Santo", "Labor Day": "Fiesta del Trabajo",
            "Labour Day": "Fiesta del Trabajo", "Saint John the Baptist": "San Juan", 
            "Galician National Day": "Día de Galicia", "Assumption of Mary": "Asunción", 
            "National Day": "Fiesta Nacional", "All Saints' Day": "Todos los Santos", 
            "Constitution Day": "Constitución", "Inmaculada Conception": "Inmaculada", 
            "Christmas Day": "Navidad"
        }
        return traducciones.get(nombre_en, nombre_en)

    @classmethod
    def obtener_mes(cls, año: int, mes: int) -> Dict[str, Any]:
        from apps.horario.services.horario_service import HorarioService
        from apps.horario.models import RegistroDiario
        
        cal = calendar.Calendar(firstweekday=0)
        mes_it = cal.monthdatescalendar(año, mes)
        colores = cls.obtener_mapeo_colores()
        
        festivos_raw = holidays.CountryHoliday('ES', prov='GA', years=año)
        eventos_db = EventoCalendario.objects.filter(fecha__year=año)
        
        mapa_eventos = {}
        for fecha, nombre in festivos_raw.items():
            mapa_eventos[fecha] = {'tipo': 'FESTIVO', 'label': 'FESTIVO', 'desc': cls.traducir_festivo(nombre)}
        
        for e in eventos_db:
            mapa_eventos[e.fecha] = {'tipo': e.tipo, 'label': e.get_tipo_display(), 'desc': e.descripcion}

        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        organizado = {nombre: [] for nombre in meses_nombres}
        
        for fecha, info in sorted(mapa_eventos.items()):
            organizado[meses_nombres[fecha.month-1]].append({
                'id': EventoCalendario.objects.filter(fecha=fecha).first().id if info['tipo'] != 'FESTIVO' else None,
                'fecha': fecha,
                'nombre': info['desc'] or info['label'],
                'tipo_label': info['label'],
                'clase': colores.get(info['tipo'], 'bg-dark text-white'),
                'borrable': info['tipo'] != 'FESTIVO'
            })

        registros = {r.fecha: r for r in RegistroDiario.objects.filter(fecha__year=año, fecha__month=mes)}
        semanas = []
        for semana in mes_it:
            dias_semana = []
            for dia in semana:
                reg = registros.get(dia)
                ev = mapa_eventos.get(dia)
                total_dia = HorarioService.calcular_total_dia(reg) if reg else 0.0
                
                dias_semana.append({
                    'dia': dia.day,
                    'fecha': dia.strftime('%Y-%m-%d'),
                    'es_mes_actual': dia.month == mes,
                    'total_str': HorarioService.decimal_a_hhmm(total_dia) if total_dia > 0 else "",
                    'clase_evento': colores.get(ev['tipo'], 'bg-white') if ev else 'bg-white',
                    'tipo_dia': ev['label'] if ev else "",
                    'descripcion': ev['desc'] if ev else "",
                })
            semanas.append(dias_semana)
            
        return {
            'semanas': semanas, 
            'eventos_organizados': organizado, 
            'tipos_opciones': EventoCalendario.TIPO_CHOICES
        }