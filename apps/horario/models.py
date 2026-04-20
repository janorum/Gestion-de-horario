from django.db import models
from typing import Any

class AjusteGlobal(models.Model):
    clave: models.CharField = models.CharField(max_length=100, primary_key=True)
    valor: models.TextField = models.TextField()

    class Meta:
        verbose_name_plural = "Ajustes Globales"

class HorarioDefecto(models.Model):
    dia: models.CharField = models.CharField(max_length=15, primary_key=True)
    m_in: models.TimeField = models.TimeField(null=True, blank=True)
    m_out: models.TimeField = models.TimeField(null=True, blank=True)
    t_in: models.TimeField = models.TimeField(null=True, blank=True)
    t_out: models.TimeField = models.TimeField(null=True, blank=True)

class RegistroDiario(models.Model):
    fecha: models.DateField = models.DateField(primary_key=True)
    m_in: models.TimeField = models.TimeField(null=True, blank=True)
    m_out: models.TimeField = models.TimeField(null=True, blank=True)
    t_in: models.TimeField = models.TimeField(null=True, blank=True)
    t_out: models.TimeField = models.TimeField(null=True, blank=True)
    categoria: models.CharField = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']

class PeriodoEspecial(models.Model):
    nombre: models.CharField = models.CharField(max_length=100, primary_key=True)
    inicio: models.CharField = models.CharField(max_length=5) 
    fin: models.CharField = models.CharField(max_length=5)
    h_sem: models.FloatField = models.FloatField(default=37.5)
    h_tarde: models.FloatField = models.FloatField(default=0.0)
    es_estricto: models.BooleanField = models.BooleanField(default=True)
    m_in: models.TimeField = models.TimeField(null=True, blank=True)
    m_out: models.TimeField = models.TimeField(null=True, blank=True)
    t_in: models.TimeField = models.TimeField(null=True, blank=True)
    t_out: models.TimeField = models.TimeField(null=True, blank=True)
    usa_tarde: models.BooleanField = models.BooleanField(default=False)

class ReduccionHijos(models.Model):
    # Añadimos la anotación de tipo explícita para calmar a Pyright
    porcentaje: models.IntegerField = models.IntegerField(default=0) 
    m_in: models.TimeField = models.TimeField(default="08:00")
    m_out: models.TimeField = models.TimeField(default="14:00")
    t_in: models.TimeField = models.TimeField(null=True, blank=True)
    t_out: models.TimeField = models.TimeField(null=True, blank=True)
    activa: models.BooleanField = models.BooleanField(default=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.activa = self.porcentaje > 0
        super().save(*args, **kwargs)