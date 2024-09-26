"""
URL configuration for back project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from api.views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",vista_home , name=""),
    path('start-monitoring/<int:data_source_id>', start_monitoring_view, name='start-monitoring'),
    path('stop-monitoring/<int:data_source_id>', stop_monitoring_view, name='stop-monitoring'),
    path('visualize', visualize_data, name=' visualize_harvest_data'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup', SignUpView.as_view(), name='signup'),
    path('edit/<int:fuente_id>', edit_fuente, name='edit_fuente'),
    path('delete/<int:fuente_id>', delete_fuente, name='delete_fuente'),
    # path('api/crsf', )

    path('login',login_user),
    path('patentes', get_patents, name="patentes"),
    path('ejes',get_ejes, name="get_ejes" ),
    path("fuentes",get_fuentes),
    path("registros",get_registros),
    path('insert', insert_fuente, name='insert'),
    path('users',get_all_users),


    # JWT paths
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/get-user-from-token/', get_user_from_token, name='get_user_from_token'),
]
