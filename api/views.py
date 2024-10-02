from django.shortcuts import redirect, render, get_object_or_404
from .utils import start_monitoring, stop_monitoring
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import *
from .serializers import ApiFuenteCreateSerializer, ApiFuenteSerializer, RegistrosSerializer,PatentSerializer, SignUpSerializer,UserSerializer,FuenteSerializer, EjeSerializer, UserProfile
import json
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['GET'])
def get_all_users(request):
    data = User.objects.all()
    users = UserSerializer(data, many=True)
    return Response(users.data)

# Create your views here.
@api_view(['GET'])
def get_registros(request):
   if request.method == 'GET':
    data_sources = ApiRegistros.objects.all()
    serializer = RegistrosSerializer(data_sources, many=True)
    return Response(serializer.data)
    

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        # Autenticar usuario
        user = authenticate(password=password, username=username)

        if user is not None:
            # Si el usuario es válido, generamos los tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Datos que retornamos junto con el token
            user_data = {
               'username': user.username,
               'lastName': user.last_name,
               'is_superuser': user.is_superuser,
               'refresh': str(refresh),
               'access': str(refresh.access_token),  # Token de acceso
            }
            return JsonResponse(user_data, safe=False)
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    else:
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    



@api_view(['GET'])
@permission_classes([IsAuthenticated])  # El token JWT debe ser válido para acceder
def get_user_from_token(request):
    user = request.user  # El usuario ya es identificado por el token JWT
    user_data = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_superuser': user.is_superuser
    }
    return JsonResponse(user_data, safe=False)





@api_view(['GET'])
def get_fuentes(request):
   if request.method == 'GET':
      fuentes = ApiFuente.objects.all()
      serializer = FuenteSerializer(fuentes,many=True)
      return Response(serializer.data)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_patents(request):
   if request.method == 'GET':
      patents = ApiPatente.objects.all()
      serializer = PatentSerializer(patents, many=True)
      return Response(serializer.data)   

   
def vista_home(request):
    fuentes = ApiFuente.objects.all().order_by('id')      
    return render(request,'home.html',{'fuentes':fuentes})
    

def visualize_data(request):
    datos=ApiRegistros.objects.all()        
    parsed_data=[]
    for data in datos:
        header_dict = json.loads(data.header) 
        metadata_dict=json.loads(data.metadata)       
        parsed_data.append({'header':header_dict.get('_datestamp'),
        'metadata':metadata_dict.get('_map'),
        })
    return render(request,'visualize.html',{'datos':parsed_data})


def start_monitoring_view(request, data_source_id):
    data_source = ApiFuente.objects.get(id=data_source_id)    
    start_monitoring(data_source)
    return redirect(vista_home)


def stop_monitoring_view(request, data_source_id):
    data_source = ApiFuente.objects.get(id=data_source_id)
    stop_monitoring(data_source)
    return redirect(vista_home)



class InsertFuenteView(APIView):
    def post(self, request):
        serializer = ApiFuenteCreateSerializer(data = request.data)
        print("AQUIIIIIIIII")
        if serializer.is_valid():
     

            try:
                eje = EjeTematico.objects.get(id_eje=serializer.validated_data['id_eje'])
            except EjeTematico.DoesNotExist:
                return Response({'error': 'Eje temático no encontrado'}, status=status.HTTP_404_NOT_FOUND)

            nuevo_id = ApiFuente.objects.count() + 1 

            
            nueva_fuente = ApiFuente(
                id = nuevo_id,
                title=serializer.validated_data['title'],
                organization=serializer.validated_data['organization'],
                frequency=serializer.validated_data['frequency'],
                is_monitoring=serializer.validated_data['is_monitoring'],
                editores=serializer.validated_data['editores'],
                materia=serializer.validated_data['materia'],
                url=serializer.validated_data['url'],
                id_eje=serializer.validated_data['id_eje']  
            )
            nueva_fuente.save()

            return Response(ApiFuenteCreateSerializer(nueva_fuente).data, status=status.HTTP_201_CREATED)
            

        return Response(serializer.data, status=status.HTTP_201_CREATED)

def edit_fuente(request, fuente_id):
    fuente = get_object_or_404(ApiFuente, id=fuente_id)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        organizacion = request.POST.get('organizacion')
        editores = request.POST.get('editores')
        url = request.POST.get('url')
        materia = request.POST.get('materia')
        eje_tematico = request.POST.get('eje_tematico')
        frecuencia = request.POST.get('frecuencia')

        eje = EjeTematico.objects.get(id_eje=eje_tematico)

        fuente.title = titulo
        fuente.organization = organizacion
        fuente.editores = editores
        fuente.url = url
        fuente.materia = materia
        fuente.id_eje = eje
        fuente.frequency = frecuencia

        fuente.save()

        return redirect('visualize_harvest_data')  # Puedes cambiar la redirección según tu preferencia.

    return render(request, 'edit.html', {'fuente': fuente})

def delete_fuente(request, fuente_id):
    fuente = get_object_or_404(ApiFuente, id=fuente_id)

    if request.method == 'POST':
        fuente.delete()
        return redirect('visualize_harvest_data')  # Cambia la redirección según tu preferencia.

    return render(request, 'delete_confirmation.html', {'fuente': fuente})

class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            print('aquiiii')
            user = serializer.save()
            print(f"Usuario creado con ID: {user.id}")
            # Crear el UserProfile usando los datos de request
            user_profile = UserProfile.objects.get(user=user)
            user_profile.role = request.data.get('role', '')
            user_profile.organization = request.data.get('organization', '')
            user_profile.save()


            return Response({
                'user': SignUpSerializer(user).data,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_ejes(request):
   if request.method == 'GET':
      ejes = EjeTematico.objects.all()
      serializer = EjeSerializer(ejes, many=True)
      return Response(serializer.data)   


# def get_crsf_token(request):
#     if request.method == 'GET':
#         crsf_token = get_token(request)
#         print(crsf_token)
#         return JsonResponse({'csrfToken': crsf_token})
