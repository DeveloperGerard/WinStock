from django.urls import path,include
from . import views

app_name = "funcionarios"

urlpatterns = [
    path('', views.inicio ,name="inicio"),
    path('registro/',views.registro,name="registro"),
    path('iniciarSesion/',views.iniciarSesion,name="iniciarSesion")  ,
    path('cerrarSesion/',views.cerrarSesion,name="cerrarSesion"),
    path('cuentas/',views.cuentas, name="cuentas"),
    path('crearFuncionario/',views.crearFuncionario,name="crearFuncionario"),
    path('desabilitarFuncionario/<uuid:uuid>/', views.desabilitarFuncionario, name="desabilitarFuncionario"),
    path('habilitarFuncionario/<uuid:uuid>/', views.habilitarFuncionario, name="habilitarFuncionario")
]
