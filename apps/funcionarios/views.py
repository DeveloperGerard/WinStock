from django.shortcuts import render,redirect
from django.contrib.auth import login,logout
from .forms import RegistroForm,LoginForm
from .models import Funcionario
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
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("funcionarios:inicio")
    else:
        form = LoginForm(request)
    return render(request,"forms/inifunc.html",{"form":form})

def cerrarSesion(request):
    logout(request)
    return redirect("funcionarios:iniciarSesion")


def cuentas(request):
    funcionarios = Funcionario.objects.all()
    return render(request,"cuentas.html",{"funcionarios":funcionarios})


def crearFuncionario(request):
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("funcionarios:inicio")
    return render(request, "registrarFunc.html", {"form": form})