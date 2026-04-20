from django.db import models


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

    fecha = models.DateField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FESTIVO')
    descripcion = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Evento de Calendario"
        verbose_name_plural = "Eventos de Calendario"

    def __str__(self):
        return f"{self.fecha} - {self.get_tipo_display()}"