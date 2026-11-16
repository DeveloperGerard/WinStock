from django.urls import path,include
from . import views

app_name = "insumos"

urlpatterns = [
    path('', views.lista_insumos, name='lista'),
    path('crear/', views.crear_insumo, name='crear'),
]

