from django.urls import path,include
from . import views

app_name = "insumos"

urlpatterns = [
    path('', views.lista_insumos, name='lista'),
    path('crear/', views.crear_insumo, name='crear'),
    path('<uuid:uuid>/editar/', views.InsumoUpdateView.as_view(), name='editar'),
    path('<uuid:uuid>/eliminar/', views.InsumoDeleteView.as_view(), name='eliminar'),
]

