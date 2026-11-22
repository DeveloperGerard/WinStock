
from django import forms
from .models import Alimento


class AlimentoForm(forms.ModelForm):

    stock_registrado = forms.ChoiceField(
        label="Unidad de medida",
        choices=[
            ("kg", "Kilogramos (kg)"),
            ("g", "Gramos (g)"),
            ("ton", "Toneladas (ton)"),
            ("L", "Litros (L)"),
            ("unidad", "Unidades"),
        ],
        initial="kg",
    )

    class Meta:
        model = Alimento

        fields = (
            "nombre",
            "stock_registrado",
            "stock_actual",
            "stock_minimo",
        )

        labels = {
            "nombre": "Nombre del alimento",
            "stock_actual": "Stock actual",
            "stock_minimo": "Stock mínimo",
        }

        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej: Trigo"
            }),

            "stock_actual": forms.NumberInput(attrs={
                "min": "0",
                "step": "0.01",
                "placeholder": "Ej: 150"
            }),

            "stock_minimo": forms.NumberInput(attrs={
                "min": "0",
                "step": "0.01",
                "placeholder": "Ej: 50"
            }),
        }
