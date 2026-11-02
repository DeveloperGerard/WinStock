from django.urls import path,include
from . import views

app_name = "funcionarios"

urlpatterns = [
    path('', views.inicio ,name="inicio"),

]
