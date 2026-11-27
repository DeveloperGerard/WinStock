from django.urls import path
from . import views

app_name = "raciones"

urlpatterns = [
    path("", views.raciones, name="raciones"),
    path("historial/", views.historial_raciones, name="historial"),
]
