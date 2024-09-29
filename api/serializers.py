from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class RegistrosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiRegistros
        fields = '__all__'

class PatentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiPatente
        fields = '__all__'

class FuenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiFuente
        fields = '__all__'    

class EjeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjeTematico
        fields = '__all__'    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'    






class SignUpSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', "first_name", 'last_name', 'password', 'rol', 'organization']

    # def validate(self, data):
    #     if data['password1'] != data['password2']:
    #         raise serializers.ValidationError({"password2": "Passwords must match."})
    #     return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            

        )
        return user