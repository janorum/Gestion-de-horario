from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('horario', '0002_registrodiario_es_periodo_especial_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AjusteGlobal',
        ),
        migrations.DeleteModel(
            name='HorarioDefecto',
        ),
        migrations.DeleteModel(
            name='PeriodoEspecial',
        ),
    ]
