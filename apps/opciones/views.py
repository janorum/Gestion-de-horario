from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ConfiguracionHorario, HorarioDefecto, HorarioEspecial, DiaHorarioEspecial

class OpcionesMainView(LoginRequiredMixin, View):
    template_name = 'opciones/configuracion.html'

    def get(self, request):
        config, _ = ConfiguracionHorario.objects.get_or_create(usuario=request.user)
        for i in range(1, 6):
            HorarioDefecto.objects.get_or_create(usuario=request.user, dia_semana=i)
            
        horarios_base = HorarioDefecto.objects.filter(usuario=request.user, dia_semana__lte=5).order_by('dia_semana')
        especiales = HorarioEspecial.objects.filter(usuario=request.user)
        
        # Asegurar días en especiales
        for e in especiales:
            for i in range(1, 6):
                DiaHorarioEspecial.objects.get_or_create(periodo=e, dia_semana=i)

        context = {
            'config': config,
            'horarios_base': horarios_base,
            'especiales': especiales.prefetch_related('detalles_dias'),
            'dias_obligatorios': config.get_dias_list('dias_obligatorios_tarde'),
            'dias_teletrabajo': config.get_dias_list('dias_teletrabajo'),
            'nombres_dias': [(i, n) for i, n in HorarioDefecto.DIAS if i <= 5]
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if 'crear_especial' in request.POST:
            self._guardar_periodo(request)
        elif 'actualizar_especial' in request.POST:
            especial_id = request.POST.get('especial_id')
            self._guardar_periodo(request, especial_id)
        elif 'borrar_especial' in request.POST:
            especial_id = request.POST.get('especial_id')
            HorarioEspecial.objects.filter(id=especial_id, usuario=request.user).delete()
        else:
            self._guardar_base(request)
            
        return redirect('opciones:main')

    def _guardar_base(self, request):
        config = ConfiguracionHorario.objects.get(usuario=request.user)
        
        # Función auxiliar para convertir a float de forma segura
        def safe_float(val, default=0.0):
            try:
                return float(val) if val else default
            except (ValueError, TypeError):
                return default

        config.horas_semanales_estandar = safe_float(request.POST.get('horas_semanales'), 37.5)
        config.max_hora_manana = request.POST.get('max_hora_manana') or "15:00"
        config.max_hora_tarde = request.POST.get('max_hora_tarde') or "20:00"
        config.minutos_descanso = int(request.POST.get('minutos_descanso') or 30)
        config.max_horas_manana_presencial = safe_float(request.POST.get('max_presencial'), 6.0)
        config.max_horas_manana_teletrabajo = safe_float(request.POST.get('max_teletrabajo'), 7.0)
        config.min_horas_tarde = safe_float(request.POST.get('min_horas_tarde'), 1.0)
        
        config.dias_obligatorios_tarde = ",".join(request.POST.getlist('dias_obligatorios'))
        config.dias_teletrabajo = ",".join(request.POST.getlist('dias_teletrabajo'))
        config.save()

        for i in range(1, 6):
            h = HorarioDefecto.objects.get(usuario=request.user, dia_semana=i)
            h.m_in = request.POST.get(f'm_in_{i}') or None
            h.m_out = request.POST.get(f'm_out_{i}') or None
            h.t_in = request.POST.get(f't_in_{i}') or None
            h.t_out = request.POST.get(f't_out_{i}') or None
            h.save()

    def _guardar_periodo(self, request, especial_id=None):
        def safe_float(val, default=0.0):
            try:
                return float(val) if val else default
            except (ValueError, TypeError):
                return default

        if especial_id:
            obj = get_object_or_404(HorarioEspecial, id=especial_id, usuario=request.user)
        else:
            f_inicio = request.POST.get('fecha_inicio').split('-')
            f_fin = request.POST.get('fecha_fin').split('-')
            obj = HorarioEspecial.objects.create(
                usuario=request.user, 
                nombre=request.POST.get('nombre_especial'),
                dia_inicio=int(f_inicio[2]), mes_inicio=int(f_inicio[1]),
                dia_fin=int(f_fin[2]), mes_fin=int(f_fin[1])
            )

        # Si se están mandando datos de configuración detallada
        if 'actualizar_especial' in request.POST:
            obj.horas_semanales = safe_float(request.POST.get('horas_semanales'), 35.0)
            obj.max_hora_manana = request.POST.get('max_hora_manana') or "15:00"
            obj.max_hora_tarde = request.POST.get('max_hora_tarde') or "20:00"
            obj.minutos_descanso = int(request.POST.get('minutos_descanso') or 30)
            obj.max_presencial = safe_float(request.POST.get('max_presencial'), 6.0)
            obj.max_teletrabajo = safe_float(request.POST.get('max_teletrabajo'), 7.0)
            obj.min_horas_tarde = safe_float(request.POST.get('min_horas_tarde'), 1.0)
            obj.dias_obligatorios_tarde = ",".join(request.POST.getlist('dias_obligatorios'))
            obj.dias_teletrabajo = ",".join(request.POST.getlist('dias_teletrabajo'))
            obj.save()

            for i in range(1, 6):
                d, _ = DiaHorarioEspecial.objects.get_or_create(periodo=obj, dia_semana=i)
                d.m_in = request.POST.get(f'm_in_{i}') or None
                d.m_out = request.POST.get(f'm_out_{i}') or None
                d.t_in = request.POST.get(f't_in_{i}') or None
                d.t_out = request.POST.get(f't_out_{i}') or None
                d.save()
        else:
            # Al crear por primera vez, asegurar los 5 días vacíos
            for i in range(1, 6):
                DiaHorarioEspecial.objects.get_or_create(periodo=obj, dia_semana=i)