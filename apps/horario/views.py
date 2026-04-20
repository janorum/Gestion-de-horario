import json
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from apps.horario.models import RegistroDiario
from apps.horario.services.horario_service import HorarioService

def vista_semanal(request):
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_ref = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_ref = date.today()
    else:
        fecha_ref = date.today()
        
    datos_semana = HorarioService.obtener_datos_semana(fecha_ref)
    return render(request, 'horario/horario.html', datos_semana)

@csrf_exempt
@require_POST
def guardar_registro_ajax(request):
    try:
        data = json.loads(request.body)
        fecha_str = data.get('fecha')
        campo = data.get('campo')
        valor = data.get('valor')

        registro, _ = RegistroDiario.objects.get_or_create(fecha=fecha_str)
        
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