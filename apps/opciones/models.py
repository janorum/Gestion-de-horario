from django.db import models
from django.contrib.auth.models import User

class ConfiguracionHorario(models.Model):
    TIPO_JORNADA = [('FIJO', 'Horario Fijo'), ('FLEXIBLE', 'Horario Flexible')]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_horario')
    tipo_jornada = models.CharField(max_length=10, choices=TIPO_JORNADA, default='FLEXIBLE')
    horas_semanales_estandar = models.FloatField(default=37.5)
    
    # Límites de conteo
    hora_inicio_conteo = models.TimeField(default="07:30")
    max_hora_manana = models.TimeField(default="15:00")
    max_hora_tarde = models.TimeField(default="20:00")
    
    # Horario Obligatorio Mañana
    oblig_manana_in = models.TimeField(default="09:00")
    oblig_manana_out = models.TimeField(default="14:30")
    
    minutos_descanso = models.IntegerField(default=30)
    min_horas_tarde = models.FloatField(default=1.0)
    max_horas_tarde = models.FloatField(default=3.0) 
    
    dias_obligatorios_tarde = models.CharField(max_length=20, default="", blank=True)
    dias_teletrabajo = models.CharField(max_length=20, default="", blank=True)
    
    max_horas_manana_presencial = models.FloatField(default=6.0)
    max_horas_manana_teletrabajo = models.FloatField(default=7.0)

    def get_dias_list(self, attr):
        campo = getattr(self, attr)
        if not campo: return []
        return [int(d) for d in campo.split(',') if d.isdigit()]

class HorarioDefecto(models.Model):
    DIAS = [(1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo')]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='horarios_base')
    dia_semana = models.IntegerField(choices=DIAS)
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ['usuario', 'dia_semana']
        ordering = ['dia_semana']

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.usuario.username}"

class HorarioEspecial(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='horarios_especiales')
    nombre = models.CharField(max_length=100)
    dia_inicio = models.IntegerField(default=1)
    mes_inicio = models.IntegerField(default=1)
    dia_fin = models.IntegerField(default=31)
    mes_fin = models.IntegerField(default=12)
    
    horas_semanales = models.FloatField(default=35.0)
    
    # Límites de conteo específicos
    hora_inicio_conteo = models.TimeField(default="07:30")
    max_hora_manana = models.TimeField(default="15:00")
    max_hora_tarde = models.TimeField(default="20:00")
    
    # Horario Obligatorio Mañana específico
    oblig_manana_in = models.TimeField(default="09:00")
    oblig_manana_out = models.TimeField(default="14:30")
    
    minutos_descanso = models.IntegerField(default=30)
    min_horas_tarde = models.FloatField(default=1.0)
    max_horas_tarde = models.FloatField(default=3.0)
    
    dias_teletrabajo = models.CharField(max_length=20, default="", blank=True)
    dias_obligatorios_tarde = models.CharField(max_length=20, default="", blank=True)
    
    max_presencial = models.FloatField(default=6.0)
    max_teletrabajo = models.FloatField(default=7.0)

    def get_dias_list_oblig(self):
        if not self.dias_obligatorios_tarde: return []
        return [int(d) for d in self.dias_obligatorios_tarde.split(',') if d.isdigit()]

    def get_dias_list_tele(self):
        if not self.dias_teletrabajo: return []
        return [int(d) for d in self.dias_teletrabajo.split(',') if d.isdigit()]

class DiaHorarioEspecial(models.Model):
    DIAS = HorarioDefecto.DIAS 
    periodo = models.ForeignKey(HorarioEspecial, on_delete=models.CASCADE, related_name='detalles_dias')
    dia_semana = models.IntegerField(choices=DIAS)
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ['periodo', 'dia_semana']
        ordering = ['dia_semana']

class SaldoDias(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saldos')
    anio = models.IntegerField(default=2026)
    vacaciones_totales = models.IntegerField(default=22)
    asuntos_propios_totales = models.IntegerField(default=6)
    vacaciones_disfrutadas = models.IntegerField(default=0)
    asuntos_disfrutados = models.IntegerField(default=0)

    class Meta:
        unique_together = ['usuario', 'anio']
        verbose_name = "Saldo de Días"