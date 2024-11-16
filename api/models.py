from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class ApiFuente(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100)
    organization = models.CharField(max_length=100)
    frequency = models.IntegerField()
    is_monitoring = models.BooleanField()
    editores = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)
    url = models.CharField()
    id_eje = models.ForeignKey('EjeTematico', models.DO_NOTHING, db_column='id_eje')

    class Meta:
        managed = False
        db_table = 'api_fuente'
       


class ApiPatente(models.Model):
    id = models.CharField(primary_key=True)
    abstract = models.TextField()
    description = models.TextField()
    claims = models.TextField()
    patent_office = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    fuente = models.ForeignKey(ApiFuente, models.DO_NOTHING, blank=True, null=True)
     
    class Meta:
        managed = False
        db_table = 'api_patente'


class ApiRegistros(models.Model):
    id = models.BigAutoField(primary_key=True)
    header = models.JSONField()
    metadata = models.JSONField()
    dia = models.IntegerField()
    mes = models.IntegerField()
    anno = models.IntegerField()
    fuente = models.ForeignKey(ApiFuente, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_registros'

class EjeTematico(models.Model):
    id_eje = models.BigAutoField(primary_key=True)
    nombre_eje = models.CharField(max_length=60, blank=True, null=True)
    esta_activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'eje_tematico'


class UserProfile(models.Model):
    ADMIN = 'admin'
    USER = 'user'
    OBSERVADOR = 'observador'
    DIRECTIVO = 'directivo'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (USER, 'User'),
        (OBSERVADOR, 'Observador'),
        (DIRECTIVO, 'Directivo'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)  # Limitado a 10 caracteres por los valores posibles
    organization = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username



class Boletin(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='boletines/imagenes/', blank=True, null=True)  # Para almacenar imágenes
    theme = models.ForeignKey(
        'EjeTematico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='boletines'
    )  # Referencia a fuente.materia
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='boletines_publicados'
    )  # Usuario que publicó el boletín
    labels = models.JSONField(blank=True, null=True)  # Arreglo opcional de etiquetas
    attached_document = models.FileField(
        upload_to='boletines/documentos/',
        blank=True,
        null=True
    )  # Documento adjunto opcional
    content = models.TextField()  # Contenido del boletín
    publication_date = models.DateTimeField(default=now)  # Fecha de publicación

    class Meta:
        db_table = 'boletines'
        ordering = ['-publication_date']  # Ordenar por fecha de publicación, el más reciente primero

    def __str__(self):
        return self.title
