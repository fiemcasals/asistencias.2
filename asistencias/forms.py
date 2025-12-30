# FILE: asistencias/forms.py
from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm as AllauthSignupForm
from .models import Diplomatura, Materia, Clase, Nota

User = get_user_model()

class CrearMateriaForm(forms.ModelForm):
    diplomatura = forms.ModelChoiceField(
        label="Diplomatura",
        queryset=Diplomatura.objects.all().order_by("nombre"),
        empty_label="Seleccioná una diplomatura",
        widget=forms.Select(attrs={"class": "input"})
    )
    class Meta:
        model = Materia
        fields = ["diplomatura", "nombre", "descripcion", "codigo", "link_clase"]

class DiplomaturaForm(forms.ModelForm):
    class Meta:
        model = Diplomatura
        fields = ['nombre', 'descripcion']

class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['diplomatura', 'nombre', 'descripcion', "link_clase"]

# FILE: asistencias/forms.py

class ClaseForm(forms.ModelForm):
    # ... (mantén tus campos repetir_cada y repetir_hasta iguales)

    class Meta:
        model = Clase
        fields = ['materia', 'fecha', 'hora_inicio', 'hora_fin', 'tema', 'link_clase', 'comentarios_docente']
        # ... (mantén tus widgets iguales)

    def __init__(self, *args, **kwargs):
        super(ClaseForm, self).__init__(*args, **kwargs)
        # 1. Hacemos que nada sea obligatorio para el validador
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        # 2. Si estamos EDITANDO, ignoramos errores de formato en los campos fijos
        if self.instance and self.instance.pk:
            campos_fijos = ['materia', 'fecha', 'hora_inicio', 'hora_fin']
            for campo in campos_fijos:
                # Si el campo tiene error de formato o viene vacío, lo limpiamos
                if campo in self._errors:
                    del self._errors[campo]
                # Aseguramos que el valor final sea el que ya estaba guardado
                cleaned_data[campo] = getattr(self.instance, campo)
        return cleaned_data

class MarcarPresenteForm(forms.Form):
    dni = forms.CharField(label="DNI", max_length=20)

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','second_name','last_name','second_last_name','dni','email', 'phone_number']

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['valor', 'observaciones']
        widgets = {
            'valor': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '10', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class SignupForm(AllauthSignupForm):
    first_name = forms.CharField(label="Nombre", max_length=50)
    second_name = forms.CharField(label="Segundo nombre", max_length=50, required=False)
    last_name = forms.CharField(label="Apellido", max_length=50)
    second_last_name = forms.CharField(label="Segundo apellido", max_length=50, required=False)
    dni = forms.CharField(label="DNI", max_length=20)
    email2 = forms.EmailField(label="Confirmar email")
    token_upgrade = forms.CharField(label="Token de nivel (opcional)", max_length=64, required=False)

    def clean(self):
        cleaned = super().clean()
        e1 = (cleaned.get("email") or "").strip().lower()
        e2 = (cleaned.get("email2") or "").strip().lower()
        if e1 and e2 and e1 != e2:
            self.add_error("email2", "Los correos no coinciden.")
        return cleaned

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.second_name = self.cleaned_data.get("second_name","")
        user.second_last_name = self.cleaned_data.get("second_last_name","")
        user.dni = self.cleaned_data["dni"]
        user.save()
        return user
