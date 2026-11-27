from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView

from .forms import FiltroCategoriaForm, InsumoForm
from .models import Insumo
from apps.inventarios.acceso import inventario_requerido

@inventario_requerido("insumos")
def lista_insumos(request):
    if request.user.is_authenticated:
        insumos = Insumo.objects.select_related("categoria").order_by("nombre")
        offline_snapshot = request.GET.get("offline_snapshot") == "1"
        categoria = None
        if offline_snapshot:
            filtro_form = None
        else:
            filtro_form = FiltroCategoriaForm(request.GET)
            if filtro_form.is_valid():
                categoria = filtro_form.cleaned_data["categoria"]
                if categoria:
                    insumos = insumos.filter(categoria=categoria)

        return render(
            request,
            "insumos/lista_insumos.html",
            {
                "insumos": insumos,
                "filtro_form": filtro_form,
                "categoria_seleccionada": categoria is not None,
                "offline_snapshot": offline_snapshot,
            },
        )
    return redirect("funcionarios:iniciarSesion")

@login_required(login_url="funcionarios:iniciarSesion")
@inventario_requerido("insumos")
def crear_insumo(request):
    if request.method == "POST":
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("insumos:lista")
    else:
        form = InsumoForm()

    return render(request, "insumos/crear_insumo.html", {"form": form})

class InsumoUpdateView(LoginRequiredMixin, UpdateView):
    model = Insumo
    form_class = InsumoForm
    template_name = "insumos/editar_insumo.html"
    success_url = reverse_lazy("insumos:lista")
    login_url = "funcionarios:iniciarSesion"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class InsumoDeleteView(LoginRequiredMixin, DeleteView):
    model = Insumo
    template_name = "insumos/insumo_confirm_delete.html"
    success_url = reverse_lazy("insumos:lista")
    login_url = "funcionarios:iniciarSesion"
    
    #Toma el valor de parametro  uuid
    slug_field = "uuid"
    #Y este busca el valor uuid dentro del modelo
    slug_url_kwarg = "uuid"
