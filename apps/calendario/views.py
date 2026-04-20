from django.shortcuts import render, redirect
from datetime import datetime
from .services.calendario_service import CalendarioService
from .models import EventoCalendario

def vista_calendario(request):
    hoy = datetime.now()
    # Capturar parámetros o usar actuales
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    
    # Manejar desbordamiento de meses (flechas)
    if mes > 12: 
        mes = 1
        año += 1
    elif mes < 1: 
        mes = 12
        año -= 1
    
    datos = CalendarioService.obtener_mes(año, mes)
    
    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    context = {
        'semanas': datos['semanas'],
        'resumen_anual': datos['resumen_anual'],
        'tipos_opciones': datos['tipos_opciones'],
        'nombre_mes': nombres_meses[mes-1],
        'año': año,
        'mes': mes,
        # Datos para alta granularidad
        'range_años': range(hoy.year - 5, hoy.year + 6), # 5 años atrás y 5 adelante
        'año_hoy': hoy.year,
        'mes_hoy': hoy.month,
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