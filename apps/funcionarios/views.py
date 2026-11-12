from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistroForm,LoginForm
from django.http import HttpResponse
from .models import Funcionario
from .decorators import rol_requerido
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
    funcionarios = Funcionario.objects.exclude(id=request.user.id)
    return render(request,"cuentas.html",{"funcionarios":funcionarios})


def crearFuncionario(request):
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("funcionarios:inicio")
    return render(request, "registrarFunc.html", {"form": form})


@rol_requerido("Admin")
@require_POST
def desabilitarFuncionario(request, public_id):
    funcionario = get_object_or_404(Funcionario, public_id=public_id)
    funcionario.is_active = False
    funcionario.save(update_fields=["is_active"])
    return redirect("funcionarios:cuentas")


@rol_requerido("Admin")
@require_POST
def habilitarFuncionario(request, public_id):
    funcionario = get_object_or_404(Funcionario, public_id=public_id)
    funcionario.is_active = True
    funcionario.save(update_fields=["is_active"])
    return redirect("funcionarios:cuentas")