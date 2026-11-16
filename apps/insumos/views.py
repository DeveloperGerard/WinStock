from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import InsumoForm
from .models import Insumo
# Create your views here.



def lista_insumos(request):
    if request.user.is_authenticated:
        insumos = Insumo.objects.select_related("categoria").order_by("nombre")
        return render(request, "insumos/lista_insumos.html", {"insumos": insumos})
    return redirect("funcionarios:iniciarSesion")


@login_required(login_url="funcionarios:iniciarSesion")
def crear_insumo(request):
    if request.method == "POST":
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("insumos:lista")
    else:
        form = InsumoForm()

    return render(request, "insumos/crear_insumo.html", {"form": form})
