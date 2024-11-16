from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class FuenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiFuente
        fields = '__all__'    
class RegistrosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiRegistros
        fields = '__all__'

class PatentSerializer(serializers.ModelSerializer):
    sourceData = FuenteSerializer(source = 'fuente',read_only = True)
    class Meta:
        model = ApiPatente
        fields = '__all__'


class EjeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjeTematico
        fields = '__all__'    



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'organization']

class UserSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = '__all__' 


class SignUpSerializer(serializers.ModelSerializer):
 
    role = serializers.CharField(required=False, allow_blank=True)
    organization = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'role', 'organization']

    # def validate(self, data):
    #     if data['password1'] != data['password2']:
    #         raise serializers.ValidationError({"password2": "Passwords must match."})
    #     return data

    def create(self, validated_data):
         
        print(validated_data)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            last_name=validated_data.get('last_name'),  # Utiliza .get() para evitar el KeyError
        first_name=validated_data.get('first_name')

        )

        return user
    

    from rest_framework import serializers
from .models import ApiFuente

class ApiFuenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiFuente
        fields = '__all__'

class ApiFuenteCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    organization = serializers.CharField(max_length=100)
    frequency = serializers.IntegerField()
    is_monitoring = serializers.BooleanField(default=False)
    editores = serializers.CharField(max_length=100)
    materia = serializers.CharField(max_length=100)
    url = serializers.CharField()
    id_eje = serializers.IntegerField()



class BoletinSerializer(serializers.ModelSerializer):
    theme = EjeSerializer(read_only=True)  # Serializa el tema como un objeto
    theme_id = serializers.PrimaryKeyRelatedField(
        queryset=EjeTematico.objects.all(), source='theme', write_only=True
    )  # Para aceptar solo el ID al crear o actualizar
    published_by = UserSerializer(read_only=True)  # Serializa el usuario como un objeto completo
    published_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='published_by', write_only=True
    )  # Para aceptar solo el ID del usuario
    labels = serializers.JSONField(required=False)  # Campo opcional para etiquetas

    class Meta:
        model = Boletin
        fields = [
            'id',
            'title',
            'image',
            'theme',
            'theme_id',
            'published_by',
            'published_by_id',
            'labels',
            'attached_document',
            'content',
            'publication_date',
        ]

    def create(self, validated_data):
        # Crear un boletín con los datos validados
        return Boletin.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Actualizar los campos de un boletín
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
