from django.shortcuts import redirect, render
from .utils import start_monitoring, stop_monitoring
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import *
from .serializers import RegistrosSerializer,PatentSerializer, SignUpSerializer,UserSerializer,FuenteSerializer, EjeSerializer
import json
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.views import APIView


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
    all_users = User.objects.all()
    print('all_users') 
    print(all_users) 
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        print("username, password")
        print(username, password)
        
        user = authenticate(password=password,username=username)
            
   
        print(user)
        if user is not None:
            login(request, user)
            user_data = {
               'username': user.username,
            #    'email': user.email,
               'lastName': user.last_name,
               'is_superuser': user.is_superuser
            }
            return JsonResponse(user_data, safe=False)
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    else:
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
@api_view(['GET'])
def get_fuentes(request):
   if request.method == 'GET':
      fuentes = ApiFuente.objects.all()
      serializer = FuenteSerializer(fuentes,many=True)
      return Response(serializer.data)

@api_view(['GET'])
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

def insert_fuente(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        organizacion = request.POST.get('organizacion')
        editores = request.POST.get('editores')
        url = request.POST.get('url')
        materia = request.POST.get('materia')
        ejes_tematicos = request.POST.get('ejes_tematicos')
        frecuencia = request.POST.get('frecuencia')
        id_html = request.POST.get('id')
        
        eje=EjeTematico.objects.get(id_eje=ejes_tematicos)
        nueva_fuente = ApiFuente(
            id=id_html,
            title=titulo,
            organization=organizacion,
            editores=editores,
            url=url,
            materia=materia,
            id_eje=eje,
            frequency=frecuencia,
            is_monitoring = False
            
    
    
        )
        nueva_fuente.save()
        return redirect(vista_home)
    return render(request, 'insert.html')



class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
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
