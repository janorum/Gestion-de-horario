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

    horas_festivo = models.FloatField(default=7.5)

    def __str__(self):
        return f"Configuración de {self.usuario.username}"

    def get_dias_list(self, attr):
        campo = getattr(self, attr)
        if not campo: return []
        return [int(d.strip()) for d in str(campo).split(',') if d.strip().isdigit()]

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

    horas_festivo = models.FloatField(default=7.5)

    def __str__(self):
        return f"{self.nombre} - {self.usuario.username}"

    def get_dias_list_oblig(self):
        if not self.dias_obligatorios_tarde: return []
        return [int(d.strip()) for d in str(self.dias_obligatorios_tarde).split(',') if d.strip().isdigit()]

    def get_dias_list_tele(self):
        if not self.dias_teletrabajo: return []
        return [int(d.strip()) for d in str(self.dias_teletrabajo).split(',') if d.strip().isdigit()]

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
    
    vacaciones_libres_totales = models.IntegerField(default=4)
    vacaciones_bloques_totales = models.IntegerField(default=18)
    asuntos_propios_totales = models.IntegerField(default=6)
    enfermedad_sin_justificar_totales = models.IntegerField(default=3)
    
    vacaciones_libres_disfrutadas = models.IntegerField(default=0)
    vacaciones_bloques_disfrutadas = models.IntegerField(default=0)
    asuntos_disfrutados = models.IntegerField(default=0)
    enfermedad_sin_justificar_disfrutados = models.IntegerField(default=0)

    class Meta:
        unique_together = ['usuario', 'anio']
        verbose_name = "Saldo de Días"
        verbose_name_plural = "Saldos de Días"

    def __str__(self):
        return f"Saldo {self.anio} - {self.usuario.username}"

    @property
    def vacaciones_totales(self):
        return self.vacaciones_libres_totales + self.vacaciones_bloques_totales

    @property
    def vacaciones_disfrutadas(self):
        return self.vacaciones_libres_disfrutadas + self.vacaciones_bloques_disfrutadas

    @property
    def vacaciones_restantes(self):
        return max(0, self.vacaciones_totales - self.vacaciones_disfrutadas)

    @property
    def asuntos_restantes(self):
        return max(0, self.asuntos_propios_totales - self.asuntos_disfrutados)

    # ESTA ES LA PROPIEDAD QUE CAUSABA EL ERROR (Debe llamarse exactamente así)
    @property
    def enfermedad_sin_justificar_restantes(self):
        return max(0, self.enfermedad_sin_justificar_totales - self.enfermedad_sin_justificar_disfrutados)

class FestivoEspecial(models.Model):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    nombre = models.CharField(max_length=100)
    dia = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(choices=MESES)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['dia', 'mes', 'usuario']
        verbose_name = "Festivo Especial"
        verbose_name_plural = "Festivos Especiales"

    def __str__(self):
        return f"{self.nombre} ({self.dia}/{self.get_mes_display()})"