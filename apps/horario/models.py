from django.db import models
from django.contrib.auth.models import User
from typing import Any

class AjusteGlobal(models.Model):
    """Ajustes compartidos por todo el sistema (no dependen de usuario)."""
    clave = models.CharField(max_length=100, primary_key=True)
    valor = models.TextField()

    class Meta:
        verbose_name_plural = "Ajustes Globales"

class HorarioDefecto(models.Model):
    """Horarios base que cada usuario configura para autocompletar."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='horarios_defecto')
    dia = models.CharField(max_length=15)
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ['usuario', 'dia']

class RegistroDiario(models.Model):
    """Fichajes diarios reales de cada usuario con almacenamiento de cálculos."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_diarios')
    fecha = models.DateField()
    
    # Fichajes introducidos por el usuario
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)
    
    # Metadatos del día (Juez de las reglas)
    categoria = models.CharField(max_length=50, null=True, blank=True)
    es_teletrabajo = models.BooleanField(default=False)
    es_periodo_especial = models.BooleanField(default=False)
    
    # Cálculos persistentes (para informes y coherencia de alertas)
    horas_m = models.FloatField(default=0.0)
    horas_t = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-fecha']
        unique_together = ['usuario', 'fecha']

    def __str__(self):
        total = self.horas_m + self.horas_t
        return f"{self.usuario.username} - {self.fecha} ({total}h)"

class PeriodoEspecial(models.Model):
    """Configuraciones de jornada de verano, navidad, etc."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='periodos_especiales')
    nombre = models.CharField(max_length=100)
    inicio = models.CharField(max_length=5) # Formato "DD/MM"
    fin = models.CharField(max_length=5)
    h_sem = models.FloatField(default=37.5)
    h_tarde = models.FloatField(default=0.0)
    es_estricto = models.BooleanField(default=True)
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)
    usa_tarde = models.BooleanField(default=False)

    class Meta:
        unique_together = ['usuario', 'nombre']