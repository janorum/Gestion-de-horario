from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .models import ConfiguracionHorario, HorarioDefecto, HorarioEspecial, DiaHorarioEspecial, SaldoDias

class OpcionesMainView(LoginRequiredMixin, View):
    template_name = 'opciones/configuracion.html'

    def get(self, request):
        # 1. Configuración de Horarios
        config, _ = ConfiguracionHorario.objects.get_or_create(usuario=request.user)
        for i in range(1, 6):
            HorarioDefecto.objects.get_or_create(usuario=request.user, dia_semana=i)
            
        horarios_base = HorarioDefecto.objects.filter(usuario=request.user, dia_semana__lte=5).order_by('dia_semana')
        especiales = HorarioEspecial.objects.filter(usuario=request.user)
        
        # Asegurar días en especiales
        for e in especiales:
            for i in range(1, 6):
                DiaHorarioEspecial.objects.get_or_create(periodo=e, dia_semana=i)

        # 2. Saldo de Días (Vacaciones/Asuntos) - Año actual 2026
        saldo, _ = SaldoDias.objects.get_or_create(usuario=request.user, anio=2026)

        context = {
            'config': config,
            'horarios_base': horarios_base,
            'especiales': especiales.prefetch_related('detalles_dias'),
            'saldo': saldo,
            'user': request.user,
            'dias_obligatorios': config.get_dias_list('dias_obligatorios_tarde'),
            'dias_teletrabajo': config.get_dias_list('dias_teletrabajo'),
            'nombres_dias': [(i, n) for i, n in HorarioDefecto.DIAS if i <= 5]
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if 'update_profile' in request.POST:
            self._guardar_cuenta(request)
        elif 'update_saldo' in request.POST:
            self._guardar_saldo(request)
        elif 'crear_especial' in request.POST:
            self._guardar_periodo(request)
        elif 'actualizar_especial' in request.POST:
            especial_id = request.POST.get('especial_id')
            self._guardar_periodo(request, especial_id)
        elif 'borrar_especial' in request.POST:
            especial_id = request.POST.get('especial_id')
            HorarioEspecial.objects.filter(id=especial_id, usuario=request.user).delete()
            messages.success(request, "Periodo especial eliminado.")
        else:
            self._guardar_base(request)
            messages.success(request, "Configuración base guardada.")
            
        return redirect('opciones:main')

    def _safe_time_to_float(self, val, default=0.0):
        """Convierte inteligentemente '37:30' o '37.5' a float 37.5"""
        if not val:
            return default
        try:
            val_str = str(val).strip()
            if ':' in val_str:
                partes = val_str.split(':')
                horas = float(partes[0])
                minutos = float(partes[1]) if len(partes) > 1 else 0
                return horas + (minutos / 60)
            return float(val_str.replace(',', '.'))
        except (ValueError, TypeError, IndexError):
            return default

    def _guardar_cuenta(self, request):
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')
        
        if pass1:
            if pass1 == pass2:
                user.set_password(pass1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Perfil y contraseña actualizados.")
            else:
                user.save()
                messages.error(request, "Las contraseñas no coinciden.")
        else:
            user.save()
            messages.success(request, "Perfil actualizado correctamente.")

    def _guardar_saldo(self, request):
        saldo = SaldoDias.objects.get(usuario=request.user, anio=2026)
        saldo.vacaciones_totales = int(request.POST.get('vac_totales') or 22)
        saldo.asuntos_propios_totales = int(request.POST.get('asu_totales') or 6)
        saldo.save()
        messages.success(request, "Saldo de días actualizado para 2026.")

    def _guardar_base(self, request):
        config = ConfiguracionHorario.objects.get(usuario=request.user)
        
        config.horas_semanales_estandar = self._safe_time_to_float(request.POST.get('horas_semanales'), 37.5)
        config.max_hora_manana = request.POST.get('max_hora_manana') or "15:00"
        config.max_hora_tarde = request.POST.get('max_hora_tarde') or "20:00"
        config.hora_inicio_conteo = request.POST.get('hora_inicio_conteo') or "07:30"
        
        # Nuevos campos de horario obligatorio
        config.oblig_manana_in = request.POST.get('oblig_manana_in') or "09:00"
        config.oblig_manana_out = request.POST.get('oblig_manana_out') or "14:30"
        
        config.minutos_descanso = int(request.POST.get('minutos_descanso') or 30)
        config.max_horas_manana_presencial = self._safe_time_to_float(request.POST.get('max_presencial'), 6.0)
        config.max_horas_manana_teletrabajo = self._safe_time_to_float(request.POST.get('max_teletrabajo'), 7.0)
        config.min_horas_tarde = self._safe_time_to_float(request.POST.get('min_horas_tarde'), 1.0)
        config.max_horas_tarde = self._safe_time_to_float(request.POST.get('max_horas_tarde'), 3.0)
        
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

        if 'actualizar_especial' in request.POST:
            obj.horas_semanales = self._safe_time_to_float(request.POST.get('horas_semanales'), 35.0)
            obj.max_hora_manana = request.POST.get('max_hora_manana') or "15:00"
            obj.max_hora_tarde = request.POST.get('max_hora_tarde') or "20:00"
            obj.hora_inicio_conteo = request.POST.get('hora_inicio_conteo') or "07:30"
            
            # Nuevos campos de horario obligatorio en especial
            obj.oblig_manana_in = request.POST.get('oblig_manana_in') or "09:00"
            obj.oblig_manana_out = request.POST.get('oblig_manana_out') or "14:30"
            
            obj.minutos_descanso = int(request.POST.get('minutos_descanso') or 30)
            obj.max_presencial = self._safe_time_to_float(request.POST.get('max_presencial'), 6.0)
            obj.max_teletrabajo = self._safe_time_to_float(request.POST.get('max_teletrabajo'), 7.0)
            obj.min_horas_tarde = self._safe_time_to_float(request.POST.get('min_horas_tarde'), 1.0)
            obj.max_horas_tarde = self._safe_time_to_float(request.POST.get('max_horas_tarde'), 3.0)
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
            messages.success(request, f"Horario '{obj.nombre}' actualizado.")
        else:
            for i in range(1, 6):
                DiaHorarioEspecial.objects.get_or_create(periodo=obj, dia_semana=i)
            messages.success(request, f"Periodo '{obj.nombre}' creado correctamente.")