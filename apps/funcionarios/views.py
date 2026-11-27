from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistroForm, CrearFuncionarioForm, EditarFuncionarioForm, LoginForm
from django.http import HttpResponse
from .models import Funcionario
from .decorators import rol_requerido
from django.contrib import messages

from apps.alimentos.models import Alimento
from apps.raciones.models import Racion_diaria
from apps.inventarios.acceso import inventario_requerido, claves_permitidas

@login_required
def inicio(request):
    claves = claves_permitidas(request.user)
    puede_raciones = {"alimentos", "lotes"} <= claves

    ultimas_raciones = (
        Racion_diaria.objects
        .select_related("lote_id", "usuario_id")
        .order_by("-fecha", "-id")[:5]
        if puede_raciones else []
    )

    return render(request, "inicio.html", {
        "ultimas_raciones": ultimas_raciones,
        "puede_raciones": puede_raciones,
        "offline_snapshot": request.GET.get("offline_snapshot") == "1",
    })


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
        funcionario = form.save()
        form.guardar_inventarios(funcionario)
        return redirect("funcionarios:cuentas")
    return render(request, "registrarFunc.html", {"form": form, "modo": "crear"})


@rol_requerido("adm")
def editarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)

    if funcionario.is_superuser and funcionario.rut != request.user.rut:
        messages.error(request, "No se puede editar este usuario.")
        return redirect("funcionarios:cuentas")

    form = EditarFuncionarioForm(
        request.POST if request.method == "POST" else None,
        instance=funcionario,
    )
    if form.is_valid():
        funcionario = form.save()
        form.guardar_inventarios(funcionario)
        messages.success(request, "Usuario editado con exito.")
        return redirect("funcionarios:cuentas")
    return render(request, "registrarFunc.html", {"form": form, "modo": "editar"})


@rol_requerido("adm")
@require_POST
def desabilitarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)
    if funcionario.is_superuser == True:
        messages.error(request, "No se puede deshabilitar este usuario.")
    elif funcionario.is_superuser == False:
        funcionario.is_active = False
        funcionario.save(update_fields=["is_active"])
        messages.success(request, "Usuario deshabilitado con exito.")
    return redirect("funcionarios:cuentas")


@rol_requerido("adm")
@require_POST
def habilitarFuncionario(request, uuid):
    funcionario = get_object_or_404(Funcionario, uuid=uuid)
    funcionario.is_active = True
    funcionario.save(update_fields=["is_active"])
    messages.success(request, "Usuario habilitado con exito.")
    return redirect("funcionarios:cuentas")
