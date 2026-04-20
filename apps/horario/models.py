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
    """Fichajes diarios de cada usuario."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_diarios')
    fecha = models.DateField()
    m_in = models.TimeField(null=True, blank=True)
    m_out = models.TimeField(null=True, blank=True)
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)
    categoria = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        unique_together = ['usuario', 'fecha']

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha}"

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

class ReduccionHijos(models.Model):
    """Configuración de reducción de jornada por usuario."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reduccion_jornada')
    porcentaje = models.IntegerField(default=0) 
    m_in = models.TimeField(default="08:00")
    m_out = models.TimeField(default="14:00")
    t_in = models.TimeField(null=True, blank=True)
    t_out = models.TimeField(null=True, blank=True)
    activa = models.BooleanField(default=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.activa = self.porcentaje > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reducción {self.usuario.username} ({self.porcentaje}%)"