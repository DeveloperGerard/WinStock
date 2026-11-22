from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.alimentos.models import Alimento, Movimientos_alimentos
from .forms import RacionForm, DetalleRacionFormSet
from .models import detalle_racion, racion_diaria


@login_required
def raciones(request):
    offline_snapshot = request.GET.get("offline_snapshot") == "1"
    if request.method == "POST":
        form = RacionForm(request.POST)
        formset = DetalleRacionFormSet(request.POST, prefix="detalles")

        if form.is_valid() and formset.is_valid():
            detalles = [f.cleaned_data for f in formset if f.cleaned_data and not f.cleaned_data.get("DELETE")]
            if not detalles:
                messages.error(request, "Agrega al menos un alimento a la ración.")
            else:
                try:
                    with transaction.atomic():
                        # Bloquea los registros para evitar descuentos simultáneos sobre el mismo stock.
                        ids = sorted({d["alimento"].pk for d in detalles})
                        alimentos = {
                            a.pk: a for a in Alimento.objects.select_for_update().filter(pk__in=ids, estado=True)
                        }
                        consumos = {}
                        for detalle in detalles:
                            alimento_id = detalle["alimento"].pk
                            consumos[alimento_id] = consumos.get(alimento_id, Decimal("0")) + detalle["kg"]

                        for alimento_id, cantidad in consumos.items():
                            alimento = alimentos.get(alimento_id)
                            if alimento is None:
                                raise ValueError("Uno de los alimentos seleccionados ya no está disponible.")
                            if alimento.stock < cantidad:
                                raise ValueError(
                                    f"Stock insuficiente de {alimento.nombre}. Disponible: "
                                    f"{alimento.stock} kg; solicitado: {cantidad} kg."
                                )

                        racion = form.save(commit=False)
                        racion.usuario_id = request.user
                        racion.save()

                        for detalle in detalles:
                            alimento = alimentos[detalle["alimento"].pk]
                            cantidad = detalle["kg"]
                            detalle_racion.objects.create(
                                racion_id=racion,
                                alimento_id=alimento,
                                kg=cantidad,
                                stock_insuficiente=False,
                            )
                            alimento.stock -= cantidad
                            alimento.save(update_fields=["stock"])
                            Movimientos_alimentos.objects.create(
                                alimento=alimento,
                                cantidad=-float(cantidad),
                                usuario=request.user,
                                motivo=f"Consumo por ración #{racion.pk} ({racion.turno})",
                            )

                    messages.success(request, "Ración registrada y stock actualizado correctamente.")
                    return redirect("raciones:raciones")
                except ValueError as error:
                    messages.error(request, str(error))
        else:
            messages.error(request, "Revisa los datos del formulario.")
    elif offline_snapshot:
        form = None
        formset = None
    else:
        form = RacionForm(initial={"fecha": timezone.localdate()})
        formset = DetalleRacionFormSet(prefix="detalles")

    ultimas_raciones = racion_diaria.objects.select_related("lote_id", "usuario_id").order_by("-fecha", "-id")[:8]
    return render(request, "raciones/raciones.html", {
        "form": form,
        "formset": formset,
        "ultimas_raciones": ultimas_raciones,
        "offline_snapshot": offline_snapshot,
    })
