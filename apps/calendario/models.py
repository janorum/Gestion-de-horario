from django.db import models
from django.contrib.auth.models import User

class EventoCalendario(models.Model):
    TIPO_CHOICES = [
        ('FESTIVO', 'Festivo Extra'),
        ('VACACIONES', 'Vacaciones'),
        ('ASUNTOS_PROPIOS', 'Asuntos Propios'),
        ('BAJA', 'Baja Médica'),
        ('ENFERMEDAD', 'Enfermedad Puntual'),
        ('SIN_SUELDO', 'Día sin Sueldo'),
        ('OTRO', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos_calendario')
    fecha = models.DateField() # Quitamos unique=True para que varios usuarios puedan tener la misma fecha
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FESTIVO')
    descripcion = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Evento de Calendario"
        verbose_name_plural = "Eventos de Calendario"
        unique_together = ['usuario', 'fecha'] # Un usuario no puede repetir evento el mismo día

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha} - {self.get_tipo_display()}"