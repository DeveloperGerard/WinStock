from django import forms

from .models import Insumo


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ("nombre", "categoria", "cantidad", "unidad")
        labels = {
            "nombre": "Nombre",
            "categoria": "Categoría",
            "cantidad": "Cantidad",
            "unidad": "Unidad",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej.: Filtro hidráulico"}),
            "cantidad": forms.NumberInput(attrs={"step": "1"}),
        }
