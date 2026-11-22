from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistroForm, CrearFuncionarioForm, EditarFuncionarioForm, LoginForm
from django.http import HttpResponse
from .models import Funcionario
from .decorators import rol_requerido

from apps.alimentos.models import Alimento
from apps.raciones.models import Racion_diaria

@login_required
def inicio(request):
    if request.user.is_authenticated:
        offline_snapshot = request.GET.get("offline_snapshot") == "1"
        ultimas_raciones = (
            Racion_diaria.objects
            .select_related("lote_id", "usuario_id")
            .order_by("-fecha", "-id")[:5]
        )
        return render(
            request,
            "inicio.html",
            {
                "offline_snapshot": offline_snapshot,
                "ultimas_raciones": ultimas_raciones,
            },
        )
    return redirect("funcionarios:iniciarSesion")

"""
def registro(request):
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("funcionarios:inicio")
    return render(request, "forms/regfunc.html", {"form": form})
"""
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


@rol_requerido("adm")
def cuentas(request):
    funcionarios = Funcionario.objects.exclude(id=request.user.id)
    return render(request, "cuentas.html", {
        "funcionarios": funcionarios,
        "offline_snapshot": request.GET.get("offline_snapshot") == "1",
    })


@rol_requerido("adm")
def crearFuncionario(request):
    form = CrearFuncionarioForm(request.POST or None)
    if form.is_valid():
        # Solo se crea la cuenta: el admin NO debe quedar logueado como el nuevo usuario
        form.save()
        return redirect("funcionarios:cuentas")
    return render(request, "registrarFunc.html", {"form": form, "modo": "crear"})


@rol_requerido("adm")
def editarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)
    form = EditarFuncionarioForm(
        request.POST if request.method == "POST" else None,
        instance=funcionario,
    )
    if form.is_valid():
        form.save()
        return redirect("funcionarios:cuentas")
    return render(request, "registrarFunc.html", {"form": form, "modo": "editar"})


@rol_requerido("adm")
@require_POST
def desabilitarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)
    funcionario.is_active = False
    funcionario.save(update_fields=["is_active"])
    return redirect("funcionarios:cuentas")


@rol_requerido("adm")
@require_POST
def habilitarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)
    funcionario.is_active = True
    funcionario.save(update_fields=["is_active"])
    return redirect("funcionarios:cuentas")
