from datetime import date
from apps.opciones.models import HorarioEspecial, ConfiguracionHorario

def obtener_configuracion_aplicable(usuario, fecha):
    """
    Determina si aplica un periodo especial (Navidad/Verano) o la configuración base.
    """
    especiales = HorarioEspecial.objects.filter(usuario=usuario)
    
    for esp in especiales:
        # Validamos si la fecha cae en el rango anual (mes y día)
        inicio = date(fecha.year, esp.mes_inicio, esp.dia_inicio)
        fin = date(fecha.year, esp.mes_fin, esp.dia_fin)
        
        # Manejo de rangos que cruzan el año (ej: 15 dic a 15 ene)
        if inicio <= fin:
            if inicio <= fecha <= fin:
                return esp
        else: # Rango que cruza fin de año
            if fecha >= inicio or fecha <= fin:
                return esp
                
    return ConfiguracionHorario.objects.get(usuario=usuario)