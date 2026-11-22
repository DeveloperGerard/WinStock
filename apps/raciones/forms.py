from django import forms
from django.forms import formset_factory
from apps.alimentos.models import Alimento
from apps.lotes_ganado.models import Lote
from .models import Racion_diaria


class RacionForm(forms.ModelForm):
    class Meta:
        model = Racion_diaria
        fields = ("fecha", "turno", "lote_id")
        labels = {"fecha": "Fecha", "turno": "Turno", "lote_id": "Lote"}
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "turno": forms.Select(choices=[("Mañana", "Mañana"), ("Tarde", "Tarde"), ("Noche", "Noche")]),
        }


class DetalleRacionForm(forms.Form):
    alimento = forms.ModelChoiceField(
        queryset=Alimento.objects.filter(estado=True).order_by("nombre"),
        label="Alimento",
        empty_label="Selecciona un alimento",
    )
    kg = forms.DecimalField(
        label="Cantidad a utilizar",
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "placeholder": "0,00"}),
    )


DetalleRacionFormSet = formset_factory(DetalleRacionForm, extra=1, can_delete=True)
