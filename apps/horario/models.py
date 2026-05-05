from django.db import models
from django.contrib.auth.models import User

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

