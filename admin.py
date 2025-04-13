from django.contrib import admin

# Register your models here.
from .models import Produs, Recenzie, Categorie, Brand, Dimensiune, Material, CustomUser
from .forms import ProdusForm, CustomUserCreationForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import CustomUser
from .forms import CustomUserCreationForm
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'telefon', 'nationalitate', 'gen', 'ocupatie', 'adresa', 'data_nasterii', 'email_confirmat', 'blocat')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefon', 'nationalitate', 'gen', 'ocupatie', 'adresa', 'data_nasterii', 'cod', 'email_confirmat', 'blocat')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('telefon', 'nationalitate', 'gen', 'ocupatie', 'adresa', 'data_nasterii', 'cod', 'blocat')}),
    )
    list_filter = ('blocat',)  # permite filtrarea utilizatorilor  blocati

    search_fields = ('username', 'email', 'telefon')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
def create_product_admin_group():
    group, created = Group.objects.get_or_create(name='Administratori_produse')
    
    product_content_type = ContentType.objects.get_for_model(Produs)
    
    permissions = Permission.objects.filter(content_type=product_content_type)
    
    group.permissions.set(permissions)
    group.save()

create_product_admin_group()





class ProdusAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informații Generale', {
            'fields': ('nume', 'pret', 'imagine')
        }),
        ('Detalii Produs', {
            'fields': ('categoria', 'brand', 'dimensiuni', 'materiale', 'recenzii'),
            'classes': ('collapse',),
        })
    )
    search_fields = ['nume', 'pret']
    list_filter = ('categoria', 'brand')
    list_display = ('nume', 'pret', 'categoria')
    filter_horizontal = ('dimensiuni', 'materiale', 'recenzii')  # Adăugat dimensiuni


admin.site.register(Produs, ProdusAdmin)

class RecenzieAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informații Recenzie', {
            'fields': ('comentariu', 'rating')  # Inversez ordinea
        }),
    )
    
    search_fields = ['comentariu']

class BrandAdmin(admin.ModelAdmin):
    search_fields = ['nume']

class DimensiuneAdmin(admin.ModelAdmin):
    search_fields= ['dimensiune']

class MaterialAdmin(admin.ModelAdmin):
    search_fields = ['nume']

class CategorieAdmin(admin.ModelAdmin):
    search_fields = ['nume']


admin.site.register(Recenzie, RecenzieAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Dimensiune, DimensiuneAdmin)
admin.site.register(Material, MaterialAdmin)

admin.site.site_header = "Panou de Administrare Produse"
admin.site.site_title = "Admin Produse"
admin.site.index_title = "Bine ai venit în adminul produselor"

# admin.site.register(CustomUser)
