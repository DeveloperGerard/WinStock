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
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "turno": forms.Select(choices=[("Mañana", "Mañana"), ("Tarde", "Tarde"), ("Noche", "Noche")]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lote_id"].queryset = Lote.objects.filter(activo=True).order_by("nombre")
        self.fields["lote_id"].empty_label = "Selecciona un lote"

class AlimentoSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            instance = getattr(value, "instance", None)
            if instance is not None:
                option["attrs"]["data-stock"] = str(instance.stock)
        return option


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
    alimento = forms.ModelChoiceField(
    queryset=Alimento.objects.filter(estado=True).order_by("nombre"),
    label="Alimento",
    empty_label="Selecciona un alimento",
    widget=AlimentoSelect,
)

DetalleRacionFormSet = formset_factory(DetalleRacionForm, extra=1)


class HistorialFiltroForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False, label="Desde",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
    )
    fecha_hasta = forms.DateField(
        required=False, label="Hasta",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
    )
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.order_by("nombre"), required=False,
        label="Lote", empty_label="Todos los lotes",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    turno = forms.ChoiceField(
        required=False, label="Turno",
        choices=[("", "Todos los turnos"), ("Mañana", "Mañana"), ("Tarde", "Tarde"), ("Noche", "Noche")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        data = super().clean()
        d, h = data.get("fecha_desde"), data.get("fecha_hasta")
        if d and h and d > h:
            raise forms.ValidationError("La fecha «Desde» no puede ser posterior a «Hasta».")
        return data