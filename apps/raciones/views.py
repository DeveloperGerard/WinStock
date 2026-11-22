
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

    if request.method == "POST":

        form = RacionForm(request.POST)
        formset = DetalleRacionFormSet(request.POST, prefix="detalles")

        if form.is_valid() and formset.is_valid():

            detalles = [
                f.cleaned_data
                for f in formset
                if f.cleaned_data and not f.cleaned_data.get("DELETE")
            ]

            if not detalles:

                messages.error(
                    request,
                    "Agrega al menos un alimento a la ración."
                )

            else:

                try:

                    alertas_stock = []

                    with transaction.atomic():

                        # Obtener los alimentos seleccionados
                        ids = sorted({
                            d["alimento"].pk
                            for d in detalles
                        })

                        alimentos = {
                            a.pk: a
                            for a in Alimento.objects.select_for_update().filter(
                                pk__in=ids,
                                estado=True
                            )
                        }

                        # Agrupar consumos del mismo alimento
                        consumos = {}

                        for detalle in detalles:

                            alimento_id = detalle["alimento"].pk

                            consumos[alimento_id] = (
                                consumos.get(alimento_id, Decimal("0"))
                                + detalle["kg"]
                            )

                        # Comprobar disponibilidad antes de guardar
                        for alimento_id, cantidad in consumos.items():

                            alimento = alimentos.get(alimento_id)

                            if alimento is None:
                                raise ValueError(
                                    "Uno de los alimentos seleccionados "
                                    "ya no está disponible."
                                )

                            if alimento.stock_actual < cantidad:

                                raise ValueError(
                                    f"Stock insuficiente de {alimento.nombre}. "
                                    f"Disponible: {alimento.stock_actual} "
                                    f"{alimento.stock_registrado}; "
                                    f"solicitado: {cantidad}."
                                )

                        # Guardar la ración
                        racion = form.save(commit=False)
                        racion.usuario_id = request.user
                        racion.save()

                        # Registrar detalles y descontar inventario
                        for detalle in detalles:

                            alimento = alimentos[detalle["alimento"].pk]
                            cantidad = detalle["kg"]

                            detalle_racion.objects.create(
                                racion_id=racion,
                                alimento_id=alimento,
                                kg=cantidad,
                                stock_insuficiente=False,
                            )

                            alimento.stock_actual -= cantidad

                            alimento.save(
                                update_fields=["stock_actual"]
                            )

                            # Registrar movimiento de salida
                            Movimientos_alimentos.objects.create(
                                alimento=alimento,
                                cantidad=-float(cantidad),
                                usuario=request.user,
                                motivo=(
                                    f"Consumo por ración #{racion.pk} "
                                    f"({racion.turno})"
                                ),
                            )

                        # Revisar el stock después de descontar
                        for alimento in alimentos.values():

                            if alimento.stock_actual <= 0:

                                alertas_stock.append(
                                    f"{alimento.nombre}: SIN EXISTENCIAS."
                                )

                            elif alimento.stock_actual <= alimento.stock_minimo:

                                alertas_stock.append(
                                    f"{alimento.nombre}: STOCK BAJO. "
                                    f"Quedan {alimento.stock_actual} "
                                    f"{alimento.stock_registrado}."
                                )

                    # Los mensajes se muestran después de confirmar
                    # correctamente la transacción.
                    messages.success(
                        request,
                        "Ración registrada y stock actualizado correctamente."
                    )

                    if alertas_stock:

                        messages.warning(
                            request,
                            "ALERTA DE INVENTARIO: "
                            + " ".join(alertas_stock)
                        )

                    return redirect("raciones:raciones")

                except ValueError as error:

                    messages.error(request, str(error))

        else:

            messages.error(
                request,
                "Revisa los datos del formulario."
            )

    else:

        form = RacionForm(
            initial={"fecha": timezone.localdate()}
        )

        formset = DetalleRacionFormSet(prefix="detalles")

    # Obtener las últimas raciones
    ultimas_raciones = (
        racion_diaria.objects
        .select_related("lote_id", "usuario_id")
        .order_by("-fecha", "-id")[:8]
    )

    return render(
        request,
        "raciones/raciones.html",
        {
            "form": form,
            "formset": formset,
            "ultimas_raciones": ultimas_raciones,
        }
    )
