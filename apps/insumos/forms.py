from django import forms

from .models import Categoria, Insumo


class FiltroCategoriaForm(forms.Form):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.order_by("nombre"),
        required=False,
        empty_label="Todas las categorías",
        label="Categoría",
    )


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
