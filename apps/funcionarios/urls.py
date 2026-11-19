from django.urls import path,include
from . import views

app_name = "funcionarios"

urlpatterns = [
    path('', views.inicio ,name="inicio"),
    path('iniciarSesion/',views.iniciarSesion,name="iniciarSesion")  ,
    path('cerrarSesion/',views.cerrarSesion,name="cerrarSesion"),
    path('cuentas/',views.cuentas, name="cuentas"),
    path('crearFuncionario/',views.crearFuncionario,name="crearFuncionario"),
    path('editarFuncionario/<uuid:uuid>/', views.editarFuncionario, name="editarFuncionario"),
    path('desabilitarFuncionario/<uuid:uuid>/', views.desabilitarFuncionario, name="desabilitarFuncionario"),
    path('habilitarFuncionario/<uuid:uuid>/', views.habilitarFuncionario, name="habilitarFuncionario")
]
"""
 path('registro/',views.registro,name="registro"),
"""