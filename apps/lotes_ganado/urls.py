from django.urls import path
from . import views

app_name = 'ganado'

urlpatterns = [
    path('lotes/', views.lista_lotes, name='lotes'),
    path('lotes/nuevo/', views.crear_lote, name='crear_lote'),
    path('lotes/<uuid:uuid>/editar/', views.editar_lote, name='editar_lote'),
    path('lotes/<uuid:uuid>/estado/', views.cambiar_estado_lote, name='cambiar_estado_lote'),
    path('lotes/<uuid:uuid>/eliminar/', views.eliminar_lote, name='eliminar_lote'),
]