# Generated by Django 5.0.2 on 2024-03-26 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='fuente',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('organization', models.CharField(max_length=100)),
                ('frequency', models.IntegerField()),
                ('is_monitoring', models.BooleanField(default=False)),
                ('editores', models.CharField(max_length=100)),
                ('materia', models.CharField(max_length=100)),
                ('url', models.CharField()),
                ('ejesTematicos', models.CharField(max_length=100)),
            ],
        ),
    ]
