from django import forms
from .models import (
    Consulta, Cita, Modelo, Marca, Categoria, Ajustes, FotoModelo, Entrada,
    RecordatorioRevision, Pagina,
)


class ConsultaForm(forms.ModelForm):
    consentimiento = forms.BooleanField(required=True, label="Acepto la política de privacidad")
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Consulta
        fields = ["nombre", "telefono", "email", "mensaje", "modelo", "consentimiento"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mensaje": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "modelo": forms.HiddenInput(),
        }

    def clean_honeypot(self):
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Spam detectado")
        return self.cleaned_data.get("honeypot")


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ["nombre", "telefono", "email", "fecha_hora", "motivo", "notas"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "fecha_hora": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "motivo": forms.Select(attrs={"class": "form-select"}),
            "notas": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "logo", "orden", "visible"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "orden": forms.NumberInput(attrs={"class": "form-control"}),
            "visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "orden", "visible"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "orden": forms.NumberInput(attrs={"class": "form-control"}),
            "visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ModeloForm(forms.ModelForm):
    class Meta:
        model = Modelo
        fields = [
            "marca", "categoria", "nombre", "descripcion_corta", "descripcion_larga",
            "precio", "precio_texto", "material", "forma", "ancho_lente", "puente",
            "varilla", "color", "genero", "destacado", "novedad", "visible", "orden",
        ]
        widgets = {
            "marca": forms.Select(attrs={"class": "form-select"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion_corta": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion_larga": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "precio_texto": forms.TextInput(attrs={"class": "form-control"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "forma": forms.Select(attrs={"class": "form-select"}),
            "ancho_lente": forms.TextInput(attrs={"class": "form-control"}),
            "puente": forms.TextInput(attrs={"class": "form-control"}),
            "varilla": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "destacado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "novedad": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "orden": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.organizacion = kwargs.pop("organizacion", None)
        super().__init__(*args, **kwargs)
        if self.organizacion:
            self.fields["marca"].queryset = Marca.objects.filter(organizacion=self.organizacion)
            self.fields["categoria"].queryset = Categoria.objects.filter(organizacion=self.organizacion)


class AjustesForm(forms.ModelForm):
    class Meta:
        model = Ajustes
        fields = [
            "nombre_comercial", "direccion", "telefono", "whatsapp", "email",
            "horario", "vacaciones", "google_maps_url", "google_reviews_url", "instagram", "facebook",
            "tiktok", "telegram", "texto_portada", "logo", "color_primario", "color_secundario",
        ]
        widgets = {f: forms.TextInput(attrs={"class": "form-control"}) for f in [
            "nombre_comercial", "direccion", "telefono", "whatsapp", "email",
            "google_maps_url", "instagram", "facebook", "tiktok",
            "color_primario", "color_secundario",
        ]}
        widgets.update({
            "horario": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "vacaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "texto_portada": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        })


class RecordatorioForm(forms.ModelForm):
    consentimiento = forms.BooleanField(required=True, label="Acepto recibir un recordatorio anual")

    class Meta:
        model = RecordatorioRevision
        fields = ["nombre", "email", "telefono", "fecha_ultima_revision", "consentimiento"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_ultima_revision": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class PaginaForm(forms.ModelForm):
    class Meta:
        model = Pagina
        fields = ["slug", "titulo", "contenido", "publicada"]
        widgets = {
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "contenido": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "publicada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ["titulo", "texto", "imagen", "publicada"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "texto": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "publicada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
