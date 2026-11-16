from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView

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


class InsumoDeleteView(LoginRequiredMixin, DeleteView):
    model = Insumo
    template_name = "insumos/insumo_confirm_delete.html"
    success_url = reverse_lazy("insumos:lista")
    login_url = "funcionarios:iniciarSesion"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
