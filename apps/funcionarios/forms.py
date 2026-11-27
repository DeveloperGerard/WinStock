from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Funcionario
from core.validators import normalizar_rut  # ajusta la ruta a donde tengas normalizar_rut
from apps.inventarios.models import Inventario


class LoginForm(AuthenticationForm):
    """Inicio de sesión solo con RUT + contraseña (USERNAME_FIELD = 'rut')."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "RUT"
        self.fields["username"].widget.attrs.update(
            placeholder="12.345.678-9", autocomplete="username"
        )
        self.fields["password"].widget.attrs.update(placeholder="••••••••")

    def clean_username(self):
        return normalizar_rut(self.cleaned_data["username"])


class RegistroForm(UserCreationForm):
    """Registro público: el rol lo asigna el sistema (funcionario), nunca el usuario."""

    class Meta:
        model = Funcionario
        fields = ("rut", "first_name", "last_name", "email")
        labels = {
            "rut": "RUT",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Repetir contraseña"
        placeholders = {
            "rut": "12.345.678-9",
            "first_name": "Juan Andrés",
            "last_name": "Pérez Soto",
            "email": "correo@ejemplo.cl",
        }
        for nombre, texto in placeholders.items():
            self.fields[nombre].widget.attrs["placeholder"] = texto

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data["rut"])

class InventariosMixin:
    """Campo 'inventarios' para formularios que usa el administrador."""

    def _agregar_campo_inventarios(self):
        self.fields["inventarios"] = forms.ModelMultipleChoiceField(
            queryset=Inventario.objects.all(),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            label="Inventarios con acceso",
        )
        if self.instance.pk:
            self.fields["inventarios"].initial = self.instance.inventarios.all()

    def guardar_inventarios(self, funcionario):
        funcionario.inventarios.set(self.cleaned_data.get("inventarios", []))

class CrearFuncionarioForm(InventariosMixin, RegistroForm):
    """Alta de funcionarios hecha por un administrador: permite elegir el rol."""

    class Meta(RegistroForm.Meta):
        fields = RegistroForm.Meta.fields + ("rol",)
        labels = {**RegistroForm.Meta.labels, "rol": "Rol"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._agregar_campo_inventarios()


class EditarFuncionarioForm(InventariosMixin, forms.ModelForm):
    """Edición de datos del funcionario sin modificar su contraseña o permisos técnicos."""

    class Meta:
        model = Funcionario
        fields = ("rut", "first_name", "last_name", "email", "phone_number", "rol")
        labels = {
            "rut": "RUT",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "phone_number": "Teléfono",
            "rol": "Rol",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._agregar_campo_inventarios()