from decimal import Decimal

from django import forms
from django.db import transaction

from .models import Alimento, Movimientos_alimentos


class AlimentoForm(forms.ModelForm):
    motivo = forms.CharField(
        max_length=200,
        required=False,
        label="Motivo del cambio de stock",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej: Reajuste, compra, merma",
        }),
    )

    class Meta:
        model = Alimento
        fields = ("nombre", "stock")
        labels = {
            "nombre": "Nombre",
            "stock": "Stock actual en Kg",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Heno"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0", "placeholder": "Ej: 500"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.es_edicion = self.instance.pk is not None
        self.stock_original = self.instance.stock if self.es_edicion else None

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock

    def clean(self):
        data = super().clean()
        stock = data.get("stock")
        motivo = (data.get("motivo") or "").strip()
        if (
            self.es_edicion
            and stock is not None
            and stock != self.stock_original
            and not motivo
        ):
            self.add_error("motivo", "Indica el motivo del cambio de stock.")
        data["motivo"] = motivo
        return data

    def guardar(self, usuario):
        """Guarda el alimento y registra el movimiento, todo o nada."""
        with transaction.atomic():
            if self.es_edicion:
                # Bloquea la fila y toma el stock real de este instante
                anterior = (
                    Alimento.objects.select_for_update()
                    .get(pk=self.instance.pk).stock
                )
                motivo = self.cleaned_data["motivo"]
            else:
                anterior = Decimal("0")
                motivo = self.cleaned_data["motivo"] or "Stock inicial"

            alimento = self.save()
            diferencia = alimento.stock - anterior

            if diferencia != 0:
                Movimientos_alimentos.objects.create(
                    alimento=alimento,
                    cantidad=diferencia,
                    usuario=usuario,
                    motivo=motivo,
                )
        return alimento