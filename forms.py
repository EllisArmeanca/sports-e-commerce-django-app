from django import forms
from .models import Dimensiune, Material, Produs
from datetime import date
import re
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
import datetime
import uuid









from django import forms
from .models import Dimensiune, Material, Categorie, Promotie


class PromotieForm(forms.ModelForm):
    categoriile = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Promotie
        fields = ['nume', 'data_expirare', 'discount', 'descriere', 'categoriile']
        widgets = {
            'data_expirare': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def __init__(self, *args, **kwargs):
        super(PromotieForm, self).__init__(*args, **kwargs)
        # Setează implicit toate categoriile ca selectate
        self.fields['categoriile'].initial = [categorie.id for categorie in Categorie.objects.all()]




class FiltruProduseForm(forms.Form):
    nume = forms.CharField(required=False, label="Nume")
    pret_min = forms.DecimalField(required=False, label="Pret minim", max_digits=8, decimal_places=2)
    pret_max = forms.DecimalField(required=False, label="Pret maxim", max_digits=8, decimal_places=2)
    categorie = forms.CharField(required=False, label="Categorie")
    brand = forms.CharField(required=False, label="Brand")

    dimensiune = forms.MultipleChoiceField(
        required=False,
        label="Dimensiune",
        widget=forms.SelectMultiple,
    )
    materiale = forms.MultipleChoiceField(
        required=False,
        label="Materiale",
        widget=forms.SelectMultiple,
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dimensiune'].choices = [(dim.id, dim.dimensiune) for dim in Dimensiune.objects.all()]
        self.fields['materiale'].choices = [(mat.id, mat.nume) for mat in Material.objects.all()]
        self.queryset = queryset or Produs.objects.all() #setul de date default sau queryset, profusele filtrate, personalizate

    def filter_queryset(self):
        produse = self.queryset #primeste querysetul curent si aplica filtrele pe el
        if self.is_valid():
            if self.cleaned_data.get('nume'):
                produse = produse.filter(nume__icontains=self.cleaned_data['nume'])
            if self.cleaned_data.get('pret_min') is not None:
                produse = produse.filter(pret__gte=self.cleaned_data['pret_min'])
            if self.cleaned_data.get('pret_max') is not None:
                produse = produse.filter(pret__lte=self.cleaned_data['pret_max'])
            if self.cleaned_data.get('categorie'):
                produse = produse.filter(categoria__nume__icontains=self.cleaned_data['categorie'])
            if self.cleaned_data.get('brand'):
                produse = produse.filter(brand__nume__icontains=self.cleaned_data['brand'])
            if self.cleaned_data.get('dimensiune'):
                produse = produse.filter(dimensiuni__id__in=self.cleaned_data['dimensiune'])
            if self.cleaned_data.get('materiale'):
                produse = produse.filter(materiale__id__in=self.cleaned_data['materiale'])
        return produse

    def paginate_queryset(self, page, per_page=3):
        paginator = Paginator(self.filter_queryset(), per_page)
        return paginator.get_page(page)




MESAJ_CHOICES = [
    ('reclamatie', 'Reclamatie'),
    ('intrebare', 'Intrebare'),
    ('review', 'Review'),
    ('cerere', 'Cerere'),
    ('programare', 'Programare'),
]


class ContactForm(forms.Form):
    nume = forms.CharField(max_length=100, label='Nume', required=True)
    prenume = forms.CharField(max_length=100, label='Prenume', required=False)
    data_nastere = forms.DateField(label="Data nasteriiiii", required=True, widget=forms.SelectDateWidget(years=list(range(2000,2024))))
    email = forms.EmailField(label="Email", required=True, error_messages={
        'invalid': 'Introduceți o adresă de email validă.'
    }
    )
    confirm_email = forms.EmailField(label="Confirm Email", required=True, error_messages={
        'invalid': 'Introduceți o adresă de email validă.'
    }
    )
    tip_mesaj = forms.ChoiceField(
        label="Tip mesaj",
        choices=MESAJ_CHOICES
    )
    subiect = forms.CharField(max_length=100, label="Subiect", required=True)
    minimum_zile = forms.IntegerField(
        label="Minim zile asteptare", min_value=1)
    mesaj = forms.CharField(
        widget=forms.Textarea, label='Mesaj (te rog semneaza-te la final)', required=True)

    def validare_comuna(self, value):
        if value and not re.match(r'^[A-Z][a-zA-Z\s]*$', value):
            return False
        return True

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")

        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Adresele de email nu coincid.")

        nume = cleaned_data.get("nume")
        prenume = cleaned_data.get("prenume")
        subiect = cleaned_data.get("subiect")

        if not self.validare_comuna(nume):
            raise forms.ValidationError(
                "Numele trebuie sa inceapa cu litera mare si sa contina doar litere si spatii")
        if prenume and not self.validare_comuna(prenume):
            raise forms.ValidationError(
                "Prenumele trebuie sa inceapa cu litera mare si sa contina doar litere si spatii")
        if not self.validare_comuna(subiect):
            raise forms.ValidationError(
                "Subiectul trebuie sa inceapa cu litera mare si sa contina doar litere si spatii")

        return cleaned_data

    def clean_data_nastere(self):
        data_nastere = self.cleaned_data.get('data_nastere')

        today = date.today()
        varsta = today.year - data_nastere.year - (
            (today.month, today.day) < (data_nastere.month, data_nastere.day)
        )

        if varsta < 18:
            raise forms.ValidationError("Trebuie sa aveti cel putin 18 ani.")

        return data_nastere

    def clean_mesaj(self):
        mesaj = self.cleaned_data.get('mesaj')
        nume = self.cleaned_data.get('nume')

        if re.search(r'\bhttps?://\S+', mesaj):
            raise forms.ValidationError("Mesajul nu poate contine linkuri.")

        cuvinte = re.findall(r'\b\w+\b', mesaj)

        nr_cuvinte = len(cuvinte)

        if (cuvinte[len(cuvinte)-1].strip().lower() != nume.strip().lower()):
            raise forms.ValidationError(
                "Trebuie sa va semnati! (ultimul cuvant al measjului sa fie numele dvs.")

        if nr_cuvinte < 5:
            raise forms.ValidationError(
                "Mesajul trebuie sa contina cel putin 5 cuvinte.")
        if nr_cuvinte > 100:
            raise forms.ValidationError(
                "Mesajul trebuie sa contina cel mult 100 cuvinte.")

        return mesaj

    def clean_minimum_zile(self):
        minimum_zile = self.cleaned_data.get('minimum_zile')
        if minimum_zile <= 0:
            raise forms.ValidationError(
                "Numarul de zile asteptare trebuie sa fie mai mare decat 0.")
        return minimum_zile



class ProdusForm(forms.ModelForm):
    # campuri aditionale
    camp_aditional_1 = forms.IntegerField(label="Camp Aditional 1", required=True)
    camp_aditional_2 = forms.IntegerField(label="Camp Aditional 2", required=True)

    class Meta:
        model = Produs
        fields = ['nume', 'imagine', 'pret', 'categoria', 'brand', 'dimensiuni', 'materiale', 'recenzii']
        labels = {
            'nume': 'Numele produsului',
            'imagine': 'Imagine produs',
            'pret': 'Pret produs',
            'categoria': 'Categoria produsului',
            'brand': 'Brandul produsului',
            'dimensiuni': 'Dimensiuni',
            'materiale': 'Materiale',
            'recenzii': 'Recenzii'
        }
        help_texts = {
            'pret': 'Introduceti pretul produsului in RON.',
            'imagine': 'Alegeti o imagine pentru produs (optional).',
        }
        error_messages = {
            'nume': {
                'max_length': 'Numele produsului nu poate depasi 100 de caractere.',
                'required': 'Numele produsului este obligatoriu.'
            },
            'pret': {
                'invalid': 'Introduceti un pret valid.',
                'required': 'Pretul este obligatoriu.'
            },
            'imagine': {
                'invalid': 'Imaginea trebuie sa fie in format .jpg, .png sau .webp.'
            }
        }

    # Validari pe campuri
    def clean_pret(self):
        pret = self.cleaned_data.get('pret')
        if pret <= 0:
            raise ValidationError("Pretul trebuie sa fie mai mare decat 0.")
        return pret

    def clean_nume(self):
        nume = self.cleaned_data.get('nume')
        if len(nume) > 100:
            raise ValidationError("Numele produsului nu poate depasi 100 de caractere.")
        return nume

    def clean_imagine(self):
        imagine = self.cleaned_data.get('imagine')
        if imagine:
            if not imagine.name.endswith(('.jpg', '.png', '.webp')):
                raise ValidationError("Imaginea trebuie sa fie in format .jpg, .png sau .webp.")
        return imagine

    # Validare globala care implica doua campuri
    def clean(self):
        cleaned_data = super().clean()
        camp_aditional_1 = cleaned_data.get('camp_aditional_1')
        camp_aditional_2 = cleaned_data.get('camp_aditional_2')

        # Validare care implica cele doua campuri aditionale
        if camp_aditional_1 + camp_aditional_2 < 100:
            raise ValidationError("Suma celor doua campuri aditionale trebuie sa fie mai mare sau egala cu 100.")

        return cleaned_data

    # Salvare cu commit=False pentru a prelucra datele
    def save(self, commit=True):
        instance = super().save(commit=False)

        # Prelucrarea campurilor aditionale pentru calcularea valorilor lipsa
        camp_aditional_1 = self.cleaned_data.get('camp_aditional_1')
        camp_aditional_2 = self.cleaned_data.get('camp_aditional_2')

        instance.pret = camp_aditional_1 * 10 + camp_aditional_2  

        if commit:
            instance.save()
        return instance


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254)
    password = forms.CharField(label="Parola", strip=False, widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False, label="Ține-mă minte")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Nume de utilizator sau parola incorecte.",
                    code='invalid_login',
                )
        return self.cleaned_data



class CustomUserCreationForm(UserCreationForm):
    telefon = forms.CharField(required=True)
    nationalitate = forms.CharField(required=True)
    gen = forms.ChoiceField(choices=[('M', 'Masculin'), ('F', 'Feminin'), ('O', 'Altul')], required=True)
    ocupatie = forms.CharField(required=False)
    adresa = forms.CharField(required=False)
    data_nasterii = forms.DateField(required=True, widget=forms.SelectDateWidget(years=list(range(1900,2024))))

    class Meta:
        model = CustomUser
        fields = ("username", "email", "telefon", "nationalitate", "gen", "ocupatie", "adresa", "data_nasterii", "password1", "password2")

    def clean_data_nasterii(self):
        data_nasterii = self.cleaned_data.get('data_nasterii')
        if data_nasterii and data_nasterii > datetime.date.today():
            raise ValidationError("Data nașterii nu poate fi în viitor.")
        return data_nasterii

    def clean_nationalitate(self):
        nationalitate = self.cleaned_data.get('nationalitate')
        if not nationalitate.isalpha():
            raise ValidationError("Naționalitatea trebuie să conțină doar litere.")
        return nationalitate

    def clean_gen(self):
        gen = self.cleaned_data.get('gen')
        if gen not in ['M', 'F', 'O']:
            raise ValidationError("Genul trebuie să fie 'Masculin', 'Feminin' sau 'Altul'.")
        return gen

    def save(self, commit=True):
        user = super().save(commit=False)
        user.telefon = self.cleaned_data["telefon"]
        user.nationalitate = self.cleaned_data["nationalitate"]
        user.gen = self.cleaned_data["gen"]
        user.ocupatie = self.cleaned_data["ocupatie"]
        user.adresa = self.cleaned_data["adresa"]
        user.data_nasterii = self.cleaned_data["data_nasterii"]
        user.cod = str(uuid.uuid4())  # Generăm un cod aleatoriu pentru confirmarea emailului (ca șir de caractere)
        user.email_confirmat = False  # Setăm email_confirmat pe False
        if commit:
            user.save()
        return user

