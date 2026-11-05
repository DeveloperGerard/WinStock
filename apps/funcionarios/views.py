from django.shortcuts import render,redirect
from django.contrib.auth import login
from django.http import HttpResponse
from .forms import RegistroForm,LoginForm
# Create your views here.

def inicio(request):
    if request.user.is_authenticated:
        return render(request,"base.html")
    return redirect("funcionarios:iniciarSesion")


def registro(request):
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("funcionarios:inicio")
    return render(request, "forms/regfunc.html", {"form": form})

def iniciarSesion(request):
    form = LoginForm()
    return render(request,"forms/inifunc.html",{"form":form})