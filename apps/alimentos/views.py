from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages

from .forms import AlimentoForm
from .models import Alimento


@login_required(login_url="funcionarios:iniciarSesion")
def crearalimentos(request):
    offline_snapshot = request.GET.get("offline_snapshot") == "1"
    if request.method == "POST":
        form = AlimentoForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Alimento registrado correctamente.")
            return redirect("alimentos:crearalimentos")
    else:
        form = None if offline_snapshot else AlimentoForm()

    alimentos = Alimento.objects.order_by("nombre")
    return render(
        request,
        "alimentos/agregar_alimentos.html",
        {
            "alimentos": alimentos,
            "form": form,
            "offline_snapshot": offline_snapshot,
        },
    )


@login_required(login_url="funcionarios:iniciarSesion")
def Editaralimentos(request):
    alimentos = Alimento.objects.order_by("nombre")
    return render(request, "alimentos/editar_alimentos.html", {"alimentos": alimentos})


@login_required(login_url="funcionarios:iniciarSesion")
@require_POST
def desabilitar_alimentos(request, alimento_id):
    alimento = get_object_or_404(Alimento, pk=alimento_id)
    if alimento.estado:
        alimento.estado = False
        alimento.save(update_fields=["estado"])
    return redirect("alimentos:editar_alimentos")


@login_required(login_url="funcionarios:iniciarSesion")
def modificar_alimentos(request, alimento_id):
    alimento = get_object_or_404(Alimento, pk=alimento_id)
    form = AlimentoForm(
        data=request.POST if request.method == "POST" else None,
        instance=alimento,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("alimentos:editar_alimentos")

    return render(
        request,
        "alimentos/modificar_alimentos.html",
        {"alimento": alimento, "form": form},
    )


@login_required(login_url="funcionarios:iniciarSesion")
def quedastock(request):
    alimentos = Alimento.objects.filter(estado=True).order_by("nombre")
    return render(request, "alimentos/lista_alimentos.html", {
        "alimentos": alimentos,
        "offline_snapshot": request.GET.get("offline_snapshot") == "1",
    })
