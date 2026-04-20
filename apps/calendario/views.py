from django.shortcuts import render, redirect
from datetime import datetime
from .services.calendario_service import CalendarioService
from .models import EventoCalendario

def vista_calendario(request):
    """Vista principal con el nombre de variable actualizado."""
    hoy = datetime.now()
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    
    if mes > 12: mes, año = 1, año + 1
    elif mes < 1: mes, año = 12, año - 1
    
    datos = CalendarioService.obtener_mes(año, mes)
    
    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    context = {
        'semanas': datos['semanas'],
        'resumen_anual': datos['resumen_anual'], # <--- CAMBIADO AQUÍ (antes era eventos_organizados)
        'tipos_opciones': datos['tipos_opciones'],
        'nombre_mes': nombres_meses[mes-1],
        'año': año,
        'mes': mes,
    }
    return render(request, 'calendario/calendario.html', context)

def api_guardar_evento(request):
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion', '')
        if fecha:
            if tipo == 'BORRAR':
                EventoCalendario.objects.filter(fecha=fecha).delete()
            elif tipo:
                EventoCalendario.objects.update_or_create(
                    fecha=fecha, 
                    defaults={'tipo': tipo, 'descripcion': descripcion}
                )
    return redirect('calendario:ver_calendario')

def api_borrar_evento(request, id):
    EventoCalendario.objects.filter(id=id).delete()
    return redirect('calendario:ver_calendario')