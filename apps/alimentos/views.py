from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AlimentoForm
from .models import Alimento


def crearalimentos(request):
    form = AlimentoForm(
        data=request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("alimentos:crearalimentos")

    alimentos = Alimento.objects.order_by("nombre")
    return render(
        request,
        "alimentos/alimentos.html",
        {"alimentos": alimentos, "form": form},
    )


def Editaralimentos(request):
    alimentos = Alimento.objects.order_by("nombre")
    return render(request, "alimentos/editar_alimentos.html", {"alimentos": alimentos})


@require_POST
def desabilitar_alimentos(request, alimento_id):
    alimento = get_object_or_404(Alimento, pk=alimento_id)
    if alimento.estado:
        alimento.estado = False
        alimento.save(update_fields=["estado"])
    return redirect("alimentos:editar_alimentos")


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


def quedastock(request):
    alimentos = Alimento.objects.filter(estado=True).order_by("nombre")
    return render(request, "alimentos/quedastock.html", {"alimentos": alimentos})
