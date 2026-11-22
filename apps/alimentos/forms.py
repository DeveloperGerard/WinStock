from django import forms

from .models import Alimento


class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = ("nombre", "stock")
        labels = {
            "nombre": "Nombre",
            "stock": "Stock actual en Kg",
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Heno'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Ej: 500'
            }),
        }

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock