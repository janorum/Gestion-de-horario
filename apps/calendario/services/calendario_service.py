import calendar
import holidays
from datetime import date
from typing import Dict, Any, List
from apps.calendario.models import EventoCalendario

class CalendarioService:
    """Servicio maestro con contadores detallados por tipo de día."""

    @staticmethod
    def obtener_mapeo_colores():
        return {
            'FESTIVO':        'bg-danger text-white',      
            'FESTIVO_EXTRA':  'bg-warning text-white',     
            'VACACIONES':     'bg-success text-white',     
            'ASUNTOS_PROPIOS':'bg-primary text-white',     
            'BAJA':           'bg-warning text-dark',      
            'ENFERMEDAD':     'bg-info text-dark',         
            'SIN_SUELDO':     'bg-secondary text-white',
            'OTRO':           'bg-secondary text-white', 
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
        
        festivos_oficiales = holidays.CountryHoliday('ES', prov='GA', years=año)
        eventos_db = EventoCalendario.objects.filter(fecha__year=año)
        
        mapa_eventos = {}
        for fecha, nombre in festivos_oficiales.items():
            mapa_eventos[fecha] = {'tipo': 'FESTIVO', 'label': 'FESTIVO', 'desc': cls.traducir_festivo(nombre), 'es_oficial': True}
        
        for e in eventos_db:
            tipo_key = 'FESTIVO_EXTRA' if e.tipo == 'FESTIVO' else e.tipo
            mapa_eventos[e.fecha] = {'tipo': tipo_key, 'label': e.get_tipo_display(), 'desc': e.descripcion, 'es_oficial': False, 'id': e.id}

        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Estructura para el resumen: eventos y conteos por mes
        resumen_anual = {nombre: {'eventos': [], 'conteos': {}} for nombre in meses_nombres}
        
        for fecha, info in sorted(mapa_eventos.items()):
            nombre_mes = meses_nombres[fecha.month-1]
            tipo = info['tipo']
            id_evento = info.get('id')
            
            # Añadir evento a la lista
            resumen_anual[nombre_mes]['eventos'].append({
                'id': id_evento,
                'fecha': fecha,
                'nombre': info['desc'] or info['label'],
                'tipo_label': info['label'],
                'clase': colores.get(tipo, 'bg-dark text-white'),
                'borrable': not info.get('es_oficial', False) and id_evento is not None
            })
            
            # Incrementar contador por tipo
            conteos = resumen_anual[nombre_mes]['conteos']
            conteos[tipo] = conteos.get(tipo, 0) + 1

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
                    'tipo_raw': ev['tipo'] if ev else "",
                    'descripcion': ev['desc'] if ev else "",
                    'es_oficial': ev.get('es_oficial', False) if ev else False,
                })
            semanas.append(dias_semana)
            
        return {
            'semanas': semanas, 
            'resumen_anual': resumen_anual, 
            'tipos_opciones': EventoCalendario.TIPO_CHOICES,
            'colores': colores
        }