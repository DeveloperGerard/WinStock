from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import F
from .forms import AlimentoForm
from .models import Alimento


@login_required(login_url="funcionarios:iniciarSesion")
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

    alimentos = Alimento.objects.filter(
        estado=True
    ).order_by("nombre")

    sin_stock = alimentos.filter(
        stock_actual__lte=0
    ).count()

    stock_bajo = alimentos.filter(
        stock_actual__gt=0,
        stock_actual__lte=F("stock_minimo")
    ).count()

    stock_normal = alimentos.filter(
        stock_actual__gt=F("stock_minimo")
    ).count()

    contexto = {
        "alimentos": alimentos,
        "sin_stock": sin_stock,
        "stock_bajo": stock_bajo,
        "stock_normal": stock_normal,
    }

    return render(
        request,
        "alimentos/quedastock.html",
        contexto
    )


@login_required
def alertas_stock(request):
    alimentos = Alimento.objects.filter(
        estado=True,
        stock_actual__lte=F("stock_minimo")
    ).order_by("nombre")

    sin_stock = alimentos.filter(
        stock_actual__lte=0
    ).count()

    stock_bajo = alimentos.filter(
        stock_actual__gt=0
    ).count()

    contexto = {
        "alimentos": alimentos,
        "sin_stock": sin_stock,
        "stock_bajo": stock_bajo,
    }

    return render(
        request,
        "alimentos/alertas_stock.html",
        contexto
    )
