import calendar
import holidays
from datetime import date
from django.db.models import Count
from typing import Dict, Any, List
from apps.calendario.models import EventoCalendario
from apps.opciones.models import SaldoDias

class CalendarioService:
    """Servicio maestro para la gestión de eventos y cálculo de saldos disponibles."""

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
            "Constitution Day": "Constitución", "Christmas Day": "Navidad", "All Saints' Day": "Todos los Santos",
            "Immaculate Conception": "Inmaculada Concepción"
        }
        return traducciones.get(nombre_en, nombre_en)

    @classmethod
    def actualizar_y_obtener_saldos(cls, usuario):
        """
        Lógica centralizada: Cuenta los eventos en el calendario y 
        actualiza el saldo en la tabla de Opciones.
        """
        anio_actual = date.today().year
        saldo, _ = SaldoDias.objects.get_or_create(usuario=usuario, anio=anio_actual)
        
        # Contamos cuántos eventos de tipo VAC y ASU tiene el usuario este año
        eventos = EventoCalendario.objects.filter(
            usuario=usuario, 
            fecha__year=anio_actual
        ).values('tipo').annotate(total=Count('id'))
        
        vac_gastadas = 0
        asu_gastados = 0
        
        for e in eventos:
            if e['tipo'] == 'VACACIONES' or e['tipo'] == 'VAC':
                vac_gastadas = e['total']
            elif e['tipo'] == 'ASUNTOS_PROPIOS' or e['tipo'] == 'ASU':
                asu_gastados = e['total']
        
        # Sincronizamos con el modelo de Opciones
        saldo.vacaciones_disfrutadas = vac_gastadas
        saldo.asuntos_disfrutados = asu_gastados
        saldo.save()
        
        return saldo

    @classmethod
    def obtener_mes(cls, año: int, mes: int, usuario: Any) -> Dict[str, Any]:
        # Importación diferida para evitar ciclos si HorarioService usa este service
        from apps.horario.services.horario_service import HorarioService
        from apps.horario.models import RegistroDiario
        
        hoy = date.today()
        cal = calendar.Calendar(firstweekday=0)
        mes_it = cal.monthdatescalendar(año, mes)
        
        festivos_oficiales = holidays.CountryHoliday('ES', prov='GA', years=año)
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
        
        # LLAMADA AL MÉTODO DE SALDOS PROPIO
        saldo_actual = cls.actualizar_y_obtener_saldos(usuario)
            
        return {
            'semanas': semanas, 
            'resumen_anual': resumen_anual, 
            'tipos_opciones': EventoCalendario.TIPO_CHOICES,
            'saldo': saldo_actual
        }