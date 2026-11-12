from django.urls import path

from . import views


app_name = "alimentos"

urlpatterns = [
    path("", views.crearalimentos, name="crearalimentos"),
    path("editar/", views.Editaralimentos, name="editar_alimentos"),
    path(
        "editar/<int:alimento_id>/",
        views.modificar_alimentos,
        name="modificar_alimentos",
    ),
    path(
        "deshabilitar/<int:alimento_id>/",
        views.desabilitar_alimentos,
        name="deshabilitar_alimentos",
    ),
    path("stock/", views.quedastock, name="quedastock"),
]
