from django import forms
from .models import Lote


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['nombre', 'cantidad', 'activo']

    def clean_cantidad(self):
        cantidad = self.cleaned_data['cantidad']
        if cantidad < 1:
            raise forms.ValidationError('La cantidad debe ser al menos 1.')
        return cantidad