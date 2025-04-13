from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import random, string
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
# Create your models here.
# class CustomUser(AbstractUser):
#     telefon = models.CharField(max_length=15)
#     adresa = models.CharField(max_length=255)
#     data_nasterii = models.DateField()
#     gen = models.CharField(max_length=10)
#     ocupatie = models.CharField(max_length=100)
import uuid

class CustomUser(AbstractUser):
    telefon = models.CharField(max_length=15, blank=True)
    nationalitate = models.CharField(max_length=50, blank=True)
    gen = models.CharField(max_length=10, blank=True)
    ocupatie = models.CharField(max_length=100, blank=True)
    adresa = models.CharField(max_length=255, blank=True)
    data_nasterii = models.DateField(null=True, blank=True)
    
    # Câmpuri pentru confirmarea emailului
    cod = models.CharField(max_length=36, unique=True)  # UUID-ul va fi stocat ca șir de caractere
    email_confirmat = models.BooleanField(default=False)
    blocat = models.BooleanField(default=False)  # câmpul pentru a marca utilizatorii blocați

    def __str__(self):
        return self.username

    




class CustomCat(models.Model):
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username
    
class CustomCatt(models.Model):
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username

# 1. Produs
class Produs(models.Model):
    nume = models.CharField(max_length=100)
    imagine = models.ImageField(upload_to='produse/', null=True, blank=True)  # Adăugat câmpul imagine
    pret = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.ForeignKey('Categorie', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    dimensiuni = models.ManyToManyField('Dimensiune', related_name='produse')
    materiale = models.ManyToManyField('Material', related_name='produse')
    recenzii = models.ManyToManyField('Recenzie', related_name='produse', blank=True)
    data_adaugare = models.DateTimeField(auto_now_add=True)
    stoc = models.PositiveIntegerField(default=10)  # Adaugă un câmp pentru a stoca numărul de item-uri disponibile


    class Meta:
        permissions = [
            ("vizualizeaza_oferta", "Poate vizualiza oferta speciala"),
        ]

    def __str__(self):
        return self.nume

# 2. Recenzie
class Recenzie(models.Model):
    rating = models.IntegerField()
    comentariu = models.TextField()

    def __str__(self):
        return f"Recenzie {self.rating} - {self.comentariu[:30]}"

# 3. Categorie
class Categorie(models.Model):
    nume = models.CharField(max_length=100)

    def __str__(self):
        return self.nume

# 4. Brand
class Brand(models.Model):
    nume = models.CharField(max_length=100)

    def __str__(self):
        return self.nume

# 5. Dimensiune
class Dimensiune(models.Model):
    dimensiune = models.CharField(max_length=50)

    def __str__(self):
        return self.dimensiune

# 6. Material
class Material(models.Model):
    nume = models.CharField(max_length=100)

    def __str__(self):
        return self.nume

class Vizualizare(models.Model):
    utilizator = models.ForeignKey('CustomUser', on_delete=models.CASCADE)  # Legătura cu utilizatorul
    produs = models.ForeignKey('Produs', on_delete=models.CASCADE)  # Legătura cu produsul
    data_vizualizare = models.DateTimeField(auto_now_add=True)  # Data vizualizării produsului

    def __str__(self):
        return f"{self.utilizator.username} - {self.produs.nume} - {self.data_vizualizare}"
    
    class Meta:
        ordering = ['-data_vizualizare']  # Ordonăm vizualizările după data vizualizării, cele mai recente primele

class Promotie(models.Model):
    nume = models.CharField(max_length=255)
    data_creare = models.DateTimeField(auto_now_add=True)
    data_expirare = models.DateTimeField()
    discount = models.DecimalField(max_digits=5, decimal_places=2)  
    descriere = models.TextField(blank=True)  

    def __str__(self):
        return self.nume


# Crearea permisiunii (o poți pune într-o migrație sau într-un script de inițializare)
# content_type = ContentType.objects.get_for_model(CustomUser)  # sau User, dacă nu ai custom user

# permission = Permission.objects.create(
#     codename='vizualizeaza_oferta',
#     name='Poate vizualiza oferta',
#     content_type=content_type,
# )