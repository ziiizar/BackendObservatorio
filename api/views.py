from django.shortcuts import redirect, render, get_object_or_404
from .utils import start_monitoring, stop_monitoring
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import Http404, JsonResponse
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
from math import ceil
from django.db.models import CharField
from django.db.models.functions import Cast


@api_view(['GET'])
def get_all_users(request):

    limit = request.query_params.get('limit', None)
    offset = request.query_params.get('offset', 0)

    try:
        limit = int(limit) if limit is not None else None
        offset = int(offset)
    except ValueError:
        return Response({"error": "Invalid limit or offset parameter"}, status=400)

    data = User.objects.all()[offset:offset + limit] if limit is not None else User.objects.all()[offset:]
    users = UserSerializer(data, many=True)
    return Response(users.data)



@api_view(['GET'])
def get_users_total_pages(request):
    if request.method == 'GET':
        limit = request.query_params.get('limit', None)

        try:
            limit = int(limit) if limit is not None else None
            if limit is None or limit <= 0:
                return Response({"error": "Invalid or missing limit parameter"}, status=400)
        except ValueError:
            return Response({"error": "Invalid limit parameter"}, status=400)

        # Obtener el total de registros
        total_users = User.objects.count()

        # Calcular el número de páginas
        total_pages = ceil(total_users / limit) if limit else 1

        return Response(total_pages)  
    

class SignUpView(APIView):
    def post(self, request):
        print(request.data)
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


@api_view(['PUT'])  # O 'PATCH' si solo deseas actualizar algunos campos
def edit_user(request):
    try:
        user_id = request.data.get('id')
        user = User.objects.get(id=user_id)

    # Deserializar los datos del request
        user_serializer = SignUpSerializer(user, data=request.data, partial=True)  # Partial=True permite actualizaciones parciales
        if user_serializer.is_valid():
            user_serializer.save()  # Guardar cambios en el usuario

            # Actualizar el perfil de usuario
            user_profile, created = UserProfile.objects.get_or_create(user=user)  # Obtener o crear el perfil

            # Actualizar campos del perfil
            organization = request.data.get('organization')
            role = request.data.get('role')
            if organization is not None:
                user_profile.organization = organization
            
            if role is not None:
                user_profile.role = role
            
            user_profile.save()  # Guardar cambios en el perfil

            return Response(user_serializer.data, status=status.HTTP_200_OK)  # Devolver los datos actualizados

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_user(request, id):
    try:
        user = User.objects.get(id=id)
        user.delete()  # Eliminar el usuario
        return Response(status=status.HTTP_204_NO_CONTENT)  # Respuesta sin contenido
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)  # Usuario no encontrado
    


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
        'role': user.userprofile.role
    }
    return JsonResponse(user_data, safe=False)



@api_view(['GET'])
def get_registros(request):
    if request.method == 'GET':
        # Obtener los parámetros 'limit', 'offset', 'orderBy' y 'sortOrder' de la URL
        limit = request.query_params.get('limit', None)
        offset = request.query_params.get('offset', 0)  # Valor por defecto 0 para 'offset'
        order_by = request.query_params.get('orderBy', None)  # Campo por defecto (None si no se pasa)
        sort_order = request.query_params.get('sortOrder', 'asc')  # 'asc' o 'desc'

        # Convertir los valores de limit y offset a enteros, o usar None si no se pasan correctamente
        try:
            limit = int(limit) if limit is not None else None
            offset = int(offset)
        except ValueError:
            return Response({"error": "Invalid limit or offset parameter"}, status=400)

        # Consulta base
        registros = ApiRegistros.objects.all()

        # Si se especifica order_by, procesar la ordenación
        if order_by:
            # Validar que el campo de ordenación esté dentro de 'metadata'
            allowed_fields = ['creator', 'title', 'subject', 'date', 'publisher', 'description']  # Agrega aquí otros campos permitidos

            if order_by in allowed_fields:
                # Crear el campo de orden dinámicamente usando 'metadata__'
                sort_field = f'metadata__{order_by}__0'

                # Si el orden es descendente, agregar el prefijo '-'
                if sort_order == 'desc':
                    registros = registros.order_by(f'-{sort_field}')
                else:
                    registros = registros.order_by(sort_field)
            else:
                return Response({"error": "Invalid sort field"}, status=400)

        # Aplicar el paginado con offset y limit
        if limit is not None:
            registros = registros[offset:offset + limit]
        else:
            registros = registros[offset:]

        # Serializar los resultados
        serializer = RegistrosSerializer(registros, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def get_registros_total_pages(request):
    if request.method == 'GET':
        limit = request.query_params.get('limit', None)

        try:
            limit = int(limit) if limit is not None else None
            if limit is None or limit <= 0:
                return Response({"error": "Invalid or missing limit parameter"}, status=400)
        except ValueError:
            return Response({"error": "Invalid limit parameter"}, status=400)

        # Obtener el total de registros
        total_registros = ApiRegistros.objects.count()

        # Calcular el número de páginas
        total_pages = ceil(total_registros / limit) if limit else 1

        return Response(total_pages)    





@api_view(['GET'])
def get_fuentes(request):
   if request.method == 'GET':
      fuentes = ApiFuente.objects.all()
      serializer = FuenteSerializer(fuentes,many=True)
      return Response(serializer.data)
   
class InsertFuenteView(APIView):
    def post(self, request):
        serializer = ApiFuenteCreateSerializer(data = request.data)
        if serializer.is_valid():

            try:
                eje = EjeTematico.objects.get(id_eje=serializer.validated_data['id_eje'])
                print(eje.id_eje)
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
                id_eje=eje  
            )
            nueva_fuente.save()

            return Response(ApiFuenteSerializer(nueva_fuente).data, status=status.HTTP_201_CREATED)
            

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
def edit_fuente(request):
    fuente_id = request.data.get('id')
    fuente = get_object_or_404(ApiFuente, id=fuente_id)

    if request.method == 'PUT':
        # Obtener los datos del formulario
        titulo = request.data.get('title')
        organizacion = request.data.get('organization')
        editores = request.data.get('editores')
        url = request.data.get('url')
        materia = request.data.get('materia')
        id_eje = request.data.get('id_eje')
        frecuencia = request.data.get('frequency')
        print(request.data)
        # Validar si se encuentra el eje temático, si no lanzar error
        try:
            print("id_eje")
            print(id_eje)
            
            eje = EjeTematico.objects.get(id_eje=id_eje)
            print(eje)
        except EjeTematico.DoesNotExist:
            print("AQUIIIIIIIII")
            raise Http404("Eje temático no encontrado")


        # Actualizar los campos de la fuente
        fuente.title = titulo
        fuente.organization = organizacion
        fuente.editores = editores
        fuente.url = url
        fuente.materia = materia
        fuente.id_eje = eje  # Asignar la instancia de EjeTematico
        fuente.frequency = frecuencia

        # Guardar los cambios
        fuente.save()
        serializer = ApiFuenteSerializer(fuente)


        # Redirigir a una vista, puede ser la vista de detalle de la fuente
        return Response(serializer.data, status=status.HTTP_200_OK)  # Cambia esta redirección según tu preferencia

    # Renderizar el formulario con la fuente cargada
    return render(request, 'fuente.html',{'fuente': fuente})

@api_view(['DELETE'])
def delete_fuente(request, fuente_id):

    print(fuente_id)
    fuente = get_object_or_404(ApiFuente, id=fuente_id)

    if request.method == 'DELETE':
        fuente.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  # Cambia la redirección según tu preferencia.

    return render(request, 'delete_confirmation.html', {'fuente': fuente})


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_patents(request):
    if request.method == 'GET':
        # Obtener los parámetros 'limit', 'offset' y 'orderBy' de la URL
        limit = request.query_params.get('limit', None)
        offset = request.query_params.get('offset', 0)  # Valor por defecto 0 para 'offset'
        order_by = request.query_params.get('orderBy', None)  # Nuevo parámetro para ordenar

        # Convertir los valores de limit y offset a enteros, o usar None si no se pasan correctamente
        try:
            limit = int(limit) if limit is not None else None
            offset = int(offset)
        except ValueError:
            return Response({"error": "Invalid limit or offset parameter"}, status=400)

        # Validar y aplicar el ordenamiento si se proporciona
        valid_order_fields = ['id', 'abstract', 'description', 'claims', 'patent_office', 'url', 'fuente_id']  # Campos válidos para ordenar
        if order_by and order_by not in valid_order_fields:
            return Response({"error": f"Invalid orderBy parameter. Valid options are: {', '.join(valid_order_fields)}"}, status=400)

        # Realizar la consulta con offset, limit y orden
        queryset = ApiPatente.objects.all()
        if order_by:
            queryset = queryset.order_by(order_by)  # Aplicar el orden

        patents = queryset[offset:offset + limit] if limit is not None else queryset[offset:]

        # Serializar los resultados
        serializer = PatentSerializer(patents, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def get_patents_total_pages(request):
    if request.method == 'GET':
        limit = request.query_params.get('limit', None)

        try:
            limit = int(limit) if limit is not None else None
            if limit is None or limit <= 0:
                return Response({"error": "Invalid or missing limit parameter"}, status=400)
        except ValueError:
            return Response({"error": "Invalid limit parameter"}, status=400)

        # Obtener el total de patentes
        total_patents = ApiPatente.objects.count()

        # Calcular el número de páginas
        total_pages = ceil(total_patents / limit) if limit else 1

        return Response(total_pages)   


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







@api_view(['GET'])
def get_ejes(request):
    if request.method == 'GET':
        # Obtener los parámetros 'limit', 'offset' y 'orderBy' de la URL
        limit = request.query_params.get('limit', None)

        offset = request.query_params.get('offset', 0)  # Valor por defecto 0 para 'offset'
        order_by = request.query_params.get('orderBy', None)  # Parámetro para ordenar

        # Convertir los valores de limit y offset a enteros, o usar None si no se pasan correctamente
        try:
            limit = int(limit) if limit is not None else None
            offset = int(offset)
        except ValueError:
            return Response({"error": "Invalid limit or offset parameter"}, status=400)

        # Validar y aplicar el ordenamiento si se proporciona
        valid_order_fields = ['id_eje', 'nombre_eje', 'esta_activo']  # Campos válidos para ordenar
        if order_by and order_by not in valid_order_fields:
            return Response({"error": f"Invalid orderBy parameter. Valid options are: {', '.join(valid_order_fields)}"}, status=400)

        # Realizar la consulta con offset, limit y orden
        queryset = EjeTematico.objects.all()
        if order_by:
            queryset = queryset.order_by(order_by)  # Aplicar el orden

        # Obtener el total de ejes para el cálculo de páginas
        total_ejes = queryset.count()

        # Calcular el número total de páginas basado en el límite
        if limit and limit > 0:
            total_pages = ceil(total_ejes / limit)
        else:
            total_pages = 1  # Si no hay límite, solo hay una "página"

        # Aplicar la paginación si se define el límite
        ejes = queryset[offset:offset + limit] if limit is not None else queryset[offset:]

        # Serializar los resultados
        serializer = EjeSerializer(ejes, many=True)

        # Devolver los ejes y el total de páginas
        return Response({
            'ejes': serializer.data,
            'total_pages': total_pages,
            'total_ejes': total_ejes
        })



@api_view(['POST'])
def insert_eje(request):
    if request.method == 'POST':
        # Deserializar los datos del request usando el serializer
        serializer = EjeSerializer(data=request.data)
        
        # Validar los datos
        if serializer.is_valid():
            # Si los datos son válidos, guardar el nuevo objeto EjeTematico
            serializer.save()
            return Response({"message": "Eje temático creado exitosamente", "eje": serializer.data}, status=201)
        else:
            # Si los datos no son válidos, devolver errores de validación
            return Response(serializer.errors, status=400)



@api_view(['PUT'])  # PUT para actualizar todo, PATCH para actualizar parcialmente
def edit_eje(request):
    try:
        id_eje = request.data.get('id_eje')
        eje = EjeTematico.objects.get(id_eje=id_eje)

        # Deserializar y validar los datos del request
        serializer = EjeSerializer(eje, data=request.data, partial=True)  # partial=True para actualizaciones parciales
        if serializer.is_valid():
            serializer.save()  # Guardar cambios
            return Response(serializer.data, status=status.HTTP_200_OK)  # Devolver los datos actualizados
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Errores de validación
    except EjeTematico.DoesNotExist:
        return Response({'error': 'Eje temático no encontrado'}, status=status.HTTP_404_NOT_FOUND)  # Eje no encontrado


@api_view(['DELETE'])
def delete_eje(request, id_eje):
    try:
        # Buscar el eje temático por su id
        eje = EjeTematico.objects.get(id_eje=id_eje)
        eje.delete()  # Eliminar el eje temático
        return Response(status=status.HTTP_204_NO_CONTENT)  # Respuesta sin contenido
    except EjeTematico.DoesNotExist:
        return Response({'error': 'Eje temático no encontrado'}, status=status.HTTP_404_NOT_FOUND)  # Eje no encontrado
