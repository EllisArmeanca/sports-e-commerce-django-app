# views.py
# Standard library imports
import json
import logging
import os
import re
import time
import uuid
from datetime import date
from uuid import UUID

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins, send_mail, send_mass_mail
from django.db.models import Count
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.contrib import messages
from collections import defaultdict
# Local app imports
from .forms import (
    ContactForm,
    CustomAuthenticationForm,
    CustomUserCreationForm,
    FiltruProduseForm,
    ProdusForm,
    PromotieForm,
)
from .models import CustomUser, Dimensiune, Material, Produs, Vizualizare

logger = logging.getLogger(__name__)

def lista_produse(request):
    form = FiltruProduseForm(request.GET, queryset=Produs.objects.all())
    page_number = request.GET.get('page')
    page_obj = form.paginate_queryset(page=page_number)

    return render(request, 'lista_produse.html', {
        'form': form,
        'page_obj': page_obj,
    })


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():

            data_nastere = form.cleaned_data.get('data_nastere')
            today = date.today()
            varsta_ani = today.year - data_nastere.year
            varsta_luni = today.month - data_nastere.month

            if today.day < data_nastere.day:
                varsta_luni -= 1

            if varsta_luni < 0:
                varsta_ani -= 1
                varsta_luni += 12

            varsta = f"{varsta_ani} ani si {varsta_luni} luni"

            mesaj = form.cleaned_data.get('mesaj')
            # Inlocuieste liniile noi cu spatiile
            mesaj = mesaj.replace('\n', ' ')
            # spatiile succesive intr-un singur spatiu
            mesaj = re.sub(r'\s+', ' ', mesaj)

            folder_path = os.path.join(os.path.dirname(__file__), 'mesaje')

            timestamp = int(time.time())  # Obtinem timestamp-ul curent
            file_name = f"mesaj_{timestamp}.json"
            file_path = os.path.join(folder_path, file_name)

            data_fisier = {
                'nume': form.cleaned_data.get('nume'),
                'prenume': form.cleaned_data.get('prenume'),
                'varsta': varsta,
                'email': form.cleaned_data.get('email'),
                'tip_mesaj': form.cleaned_data.get('tip_mesaj'),
                'subiect': form.cleaned_data.get('subiect'),
                'minimum_zile': form.cleaned_data.get('minimum_zile'),
                'mesaj': mesaj,
            }

            with open(file_path, 'w') as json_file:
                json.dump(data_fisier, json_file, indent=4)

            return render(request, 'contact_succes.html')
    else:
        form = ContactForm()  # formular gol pt get

    return render(request, 'contact_form.html', {'form': form})



@login_required
def creare_produs(request):
    # Permite accesul daca utilizatorul este superuser
    if request.user.is_superuser or request.user.groups.filter(name='Administratori_produse').exists():
        if request.method == 'POST':
            form = ProdusForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()  # Salveaza instanta modelului cu prelucrarea câmpurilor aditionale
                return redirect('lista_produse')  # Redirectionare dupa salvare
        else:
            form = ProdusForm()

        return render(request, 'creare_produs.html', {'form': form})
    else:
        context = {'tip_produs': 'produse'}  # inlocuieste cu tipul de produse din site-ul tau
        return HttpResponseForbidden(render_to_string('403.html', context))

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        logger.debug(f"Utilizatorul {request.POST.get('username')} incearca sa se logheze.")
        
        if form.is_valid():
            user = form.get_user()

            # Verificam daca utilizatorul este blocat
            if user.blocat:
                logger.warning(f"Utilizatorul {user.username} incearca sa se logheze, dar contul sau este blocat.")
                messages.error(request, "Contul tau a fost blocat. Te rugam sa contactezi administratorul.")
                return redirect('/proiect/login')

            if not user.is_superuser and not user.email_confirmat:
                logger.warning(f"Utilizatorul {user.username} incearca sa se logheze fara a-si confirma emailul.")
                messages.error(request, "Te rugam sa iti confirmi adresa de email inainte de a te loga.")
                return redirect('/proiect/login')

            login(request, user)
            logger.info(f"Utilizatorul {user.username} s-a logat cu succes.")
            
            # Salveaza datele utilizatorului in sesiune
            request.session['user_data'] = {
                'username': user.username,
                'email': user.email,
                'telefon': user.telefon,
                'nationalitate': user.nationalitate,
                'gen': user.gen,
                'ocupatie': user.ocupatie,
                'adresa': user.adresa,
                'data_nasterii': user.data_nasterii.strftime('%Y-%m-%d') if user.data_nasterii else None,
            }

            # Configurarea expirarii sesiunii
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(86400)
            else:
                request.session.set_expiry(0)

            return redirect('/proiect/profile')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('/proiect/login/')



def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            if username.lower() == 'admin':
                logger.warning(f"Se incearca inregistrarea cu username-ul 'admin' de catre utilizatorul {email}.")
                subject = "Cineva incearca sa ne preia site-ul"
                plain_message = f"S-a incercat inregistrarea cu username-ul 'admin'. Adresa de e-mail folosita: {email}."
                html_message = format_html(
                    "<h1 style='color: red;'>Cineva incearca sa ne preia site-ul</h1>"
                    "<p><strong>Username:</strong> admin</p>"
                    "<p><strong>Email:</strong> {}</p>", email)
                mail_admins(subject, plain_message, html_message=html_message)
                form.add_error('username', 'Utilizarea acestui username nu este permisa.')
                return render(request, 'inregistrare.html', {'form': form})

            user = form.save()
            logger.info(f"Utilizatorul {user.username} s-a inregistrat cu succes.")

            subject = "Confirma-ti adresa de email"
            message = render_to_string('confirmare_email.html', {
                'nume': user.get_full_name(),
                'confirmare_url': f"http://{get_current_site(request).domain}/proiect/confirma_mail/{user.cod}/"
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return redirect('/proiect/login/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inregistrare.html', {'form': form})




def profile_view(request):
    user_data = request.session.get('user_data')  # Obtine datele din sesiune
    if not user_data:
        # Daca nu exista sesiune activa, redirectioneaza spre logare
        return redirect('/proiect/login')
    return render(request, 'profile.html', {'user_data': user_data})



def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                user = form.save()
                update_session_auth_hash(request, user)
                return redirect('/proiect/profile')
            except Exception as e:
                logger.error(f"Eroare la schimbarea parolei pentru utilizatorul {request.user.username}. Detalii: {e}")
                subject = "Eroare la schimbarea parolei"
                plain_message = f"A aparut o eroare la schimbarea parolei pentru utilizatorul {request.user.username}.\nDetalii: {e}"
                html_message = format_html(
                    "<h1 style='color: red;'>Eroare la schimbarea parolei</h1>"
                    "<p><strong>Utilizator:</strong> {}</p>"
                    "<p><strong>Eroare:</strong> {}</p>",
                    request.user.username, e
                )
                mail_admins(subject, plain_message, html_message=html_message)
                return render(request, 'change_password.html', {'form': form, 'error': 'A aparut o problema la schimbarea parolei.'})

    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})


def confirma_mail_view(request, cod):
    try:
        # Codul este acum sir de caractere, asa ca nu trebuie sa-l convertesti
        user = CustomUser.objects.get(cod=cod)
        user.email_confirmat = True
        user.save()
        return render(request, 'confirmare_mail_reusita.html', {'user': user})
    except CustomUser.DoesNotExist:
        return render(request, 'confirmare_mail_esuata.html')


def vizualizeaza_produs(request, produs_id):
    # Obtine produsul folosind ID-ul
    produs = get_object_or_404(Produs, id=produs_id)

    # Verifica daca utilizatorul este autentificat
    if request.user.is_authenticated:
        # Defineste limita de vizualizari N
        N = 5

        # Obtine vizualizarile utilizatorului pentru acest produs
        vizualizari = Vizualizare.objects.filter(utilizator=request.user)

        # Daca exista deja N vizualizari, sterge cea mai veche vizualizare
        if vizualizari.count() >= N:
            # sterge cea mai veche vizualizare
            vizualizari.order_by('data_vizualizare').first().delete()

        # Adauga o noua vizualizare
        Vizualizare.objects.create(
            utilizator=request.user,
            produs=produs,
        )

    # Reda pagina produsului cu detalii
    return render(request, 'pagina_produs.html', {'produs': produs})


def promotii(request):
    if request.method == 'POST':
        form = PromotieForm(request.POST)

        if form.is_valid():
            # Salvam promotia
            promotie = form.save()
            messages.success(request, "Promotia a fost creata cu succes!")

            # Alegem K, minimul de vizualizari pentru a trimite emailuri
            K = 1

            categorii_selectate = form.cleaned_data['categoriile']
            nume_categorii_selectate = [categorie.nume for categorie in categorii_selectate]
            messages.info(request, f"Categorii selectate: {', '.join(nume_categorii_selectate)}")

            # Obtine toate vizualizarile
            vizualizari = Vizualizare.objects.select_related('produs').all()
            if not vizualizari:
                messages.warning(request, "Nu exista vizualizari inregistrate pentru produsele selectate.")

            categorii_ids = [categorie.id for categorie in categorii_selectate]
            vizualizari_utilizatori = defaultdict(int)
            
            for vizualizare in vizualizari:
                if vizualizare.produs.categoria_id in categorii_ids:
                    vizualizari_utilizatori[vizualizare.utilizator_id] += 1
            
            utilizatori2 = [
                utilizator_id for utilizator_id, numar_vizualizari in vizualizari_utilizatori.items()
                if numar_vizualizari >= K
            ]
            
            utilizatori = get_user_model().objects.filter(id__in=utilizatori2)

            if not utilizatori:
                messages.warning(request, "Nu s-au gasit utilizatori eligibili pentru aceasta promotie.")
                return redirect('/proiect/promotii')

            email_messages = []
            for categorie in form.cleaned_data['categoriile']:
                if str(categorie) == 'Mingi de fotbal':
                    subject = "Promotie pentru Mingi de Fotbal!"
                    template = 'email_mingi.html'
                elif str(categorie) == 'Ghete de fotbal':
                    subject = "Promotie pentru Ghete de Fotbal!"
                    template = 'email_ghete.html'
                else:
                    messages.debug(request, f"Categoria '{categorie}' nu are un template asociat.")
                    continue

                # Pregatim continutul e-mail-ului
                for utilizator in utilizatori:
                    context = {
                        'subiect': subject,
                        'data_expirare': promotie.data_expirare,
                        'discount': promotie.discount,
                        'descriere': promotie.descriere,
                    }
                    email_message = (subject, render_to_string(
                        template, context), settings.DEFAULT_FROM_EMAIL, [utilizator.email])
                    email_messages.append(email_message)

            # Trimitem toate emailurile
            if email_messages:
                send_mass_mail(email_messages)
                messages.success(request, f"Emailurile au fost trimise cu succes catre {len(utilizatori)} utilizatori.")
            else:
                messages.error(request, "A aparut o eroare la trimiterea emailurilor.")

            # Redirect catre aceeasi pagina dupa trimiterea emailurilor
            return redirect('/proiect/promotii')
        else:
            messages.error(request, "Formularul este invalid. Te rugam sa incerci din nou.")
    else:
        form = PromotieForm()
        messages.info(request, "Completeaza formularul pentru a adauga o promotie.")

    return render(request, 'promotii.html', {'form': form})




def eroare_403_view(request):
    context = {
        'titlu': 'Acces interzis',  
        'mesaj_personalizat': 'Nu aveti permisiunea necesara pentru a accesa aceasta resursa.',
    }
    return render(request, '403.html', context)


@login_required
def adauga_permisune(request):
    if request.method == 'POST':
        permisiune = Permission.objects.get(codename='vizualizeaza_oferta')

        # Adaugam permisiunea utilizatorului
        request.user.user_permissions.add(permisiune)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def oferta(request):
    if not request.user.has_perm('proiect.vizualizeaza_oferta'):
        context = {'titlu': 'Eroare afisare oferta', 'mesaj_personalizat': 'Nu ai voie sa vizualizezi oferta'}
        return HttpResponseForbidden(render(request, '403.html', context))

    # Daca utilizatorul are permisiunea, arata oferta
    return render(request, 'oferta.html')



def product_detail(request, id):
    produs = Produs.objects.get(id=id)
    return render(request, 'pagina_produs.html', {'produs': produs})


def adauga_in_cos(request, produs_id):
    produs = get_object_or_404(Produs, id=produs_id)
    cos = request.session.get('cos', {})

    if str(produs_id) not in cos:
        if produs.stoc > 0:
            cos[str(produs_id)] = {'nume': produs.nume, 'pret': float(produs.pret), 'stoc': 1}
            produs.stoc -= 1
            produs.save()
        else:
            messages.error(request, "Stoc insuficient!")
    else:
        if cos[str(produs_id)]['stoc'] < produs.stoc:
            cos[str(produs_id)]['stoc'] += 1
            produs.stoc -= 1
            produs.save()
        else:
            messages.error(request, "Nu poți adăuga mai multe produse decât sunt disponibile în stoc!")

    request.session['cos'] = cos
    return redirect('lista_produse')


def adauga_cantitate(request, produs_id):
    produs = get_object_or_404(Produs, id=produs_id)
    cos = request.session.get('cos', {})

    if str(produs_id) in cos and cos[str(produs_id)]['stoc'] < produs.stoc:
        cos[str(produs_id)]['stoc'] += 1
        produs.stoc -= 1
        produs.save()
    else:
        messages.error(request, "Stoc insuficient!")

    request.session['cos'] = cos
    return redirect('cos_virtual')


def scade_cantitate(request, produs_id):
    produs = get_object_or_404(Produs, id=produs_id)
    cos = request.session.get('cos', {})

    if str(produs_id) in cos and cos[str(produs_id)]['stoc'] > 0:
        cos[str(produs_id)]['stoc'] -= 1
        produs.stoc += 1
        produs.save()

        if cos[str(produs_id)]['stoc'] == 0:
            del cos[str(produs_id)]

    request.session['cos'] = cos
    return redirect('cos_virtual')


def cos_virtual(request):
    cos = request.session.get('cos', {})
    total = 0
    total_items = 0

    for item in cos.values():
        item['subtotal'] = item['stoc'] * item['pret']  # Calculate subtotal
        total += item['subtotal']  # Add subtotal to total
        total_items += item['stoc']  # Add stoc to total_items

    return render(request, 'cos_virtual.html', {
        'cos': cos,
        'total': total,
        'total_items': total_items,
    })


def sterge_din_cos(request, produs_id):
    produs = get_object_or_404(Produs, id=produs_id)
    cos = request.session.get('cos', {})

    if str(produs_id) in cos:
        # Returnăm stocul produsului la valoarea inițială
        produs.stoc += cos[str(produs_id)]['stoc']
        produs.save()

        # Ștergem produsul din coș
        del cos[str(produs_id)]

    request.session['cos'] = cos
    return redirect('cos_virtual')


    # Filtru pentru Recenzii (ex: filtrare dupa rating sau comentariu)
    # recenzie = request.GET.get('recenzie')
    # if recenzie:
    #     produse = produse.filter(recenzii__comentariu__icontains=recenzie)  # Filtru dupa comentariul recenziei

    # # Filtru pentru Data Adaugare
    # data_min = request.GET.get('data_min')
    # if data_min:
    #     produse = produse.filter(data_adaugare__gte=data_min)  # Filtru pentru data minima de adaugare

    # data_max = request.GET.get('data_max')
    # if data_max:
    #     produse = produse.filter(data_adaugare__lte=data_max)  # Filtru pentru data maxima de adaugare

    # Obtine filtrele din GET
    # nume = request.GET.get('nume', '')
    # pret_min = request.GET.get('pret_min')
    # pret_max = request.GET.get('pret_max')
    # categorie = request.GET.get('categorie', '')
    # brand = request.GET.get('brand', '')
    # dimensiuni = request.GET.getlist('dimensiune')
    # materiale = request.GET.getlist('materiale')

    # # Filtrarea produselor
    # produse = Produs.objects.all()

    # if nume:
    #     produse = produse.filter(nume__icontains=nume)
    # if pret_min:
    #     produse = produse.filter(pret__gte=pret_min)
    # if pret_max:
    #     produse = produse.filter(pret__lte=pret_max)
    # if categorie:
    #     produse = produse.filter(categoria__nume__icontains=categorie)
    # if brand:
    #     produse = produse.filter(brand__nume__icontains=brand)
    # if dimensiuni:
    #     produse = produse.filter(dimensiuni__id__in=dimensiuni)
    # if materiale:
    #     produse = produse.filter(materiale__id__in=materiale)


# View pentru filtrarea produselor - va raspunde la cereri AJAX


# def filtreaza_produse(request):
#     if request.method == 'POST':
#         nume = request.POST.get('nume', '')
#         pret_min = request.POST.get('pret_min')
#         pret_max = request.POST.get('pret_max')
#         categorie = request.POST.get('categorie', '')
#         brand = request.POST.get('brand', '')
#         dimensiuni = request.POST.getlist('dimensiune')
#         materiale = request.POST.getlist('materiale')

#         produse = Produs.objects.all()

#         if nume:
#             produse = produse.filter(nume__icontains=nume)
#         if pret_min:
#             produse = produse.filter(pret__gte=pret_min)
#         if pret_max:
#             produse = produse.filter(pret__lte=pret_max)
#         if categorie:
#             produse = produse.filter(categoria__nume__icontains=categorie)
#         if brand:
#             produse = produse.filter(brand__nume__icontains=brand)
#         if dimensiuni:
#             produse = produse.filter(dimensiuni__id__in=dimensiuni)
#         if materiale:
#             produse = produse.filter(materiale__id__in=materiale)

#         # Aplicam paginarea
#         paginator = Paginator(produse, 3)  # Pagina cu 3 produse pe pagina
#         page_number = request.GET.get('page')
#         page_obj = paginator.get_page(page_number)

#         produse_serializate = [
#             {
#                 'nume': produs.nume,
#                 'pret': str(produs.pret),
#                 'imagine': produs.imagine.url if produs.imagine else '',
#             }
#             # Foloseste `page_obj` pentru produsele paginate
#             for produs in page_obj
#         ]

#         return JsonResponse({
#             'status': 'success',
#             'produse': produse_serializate,
#             'pagination': {
#                 'has_next': page_obj.has_next(),
#                 'has_previous': page_obj.has_previous(),
#                 'num_pages': page_obj.paginator.num_pages,
#                 'current_page': page_obj.number
#             }
#         })

#     return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# View pentru lista de produse cu paginare


# request session sau variabila globala
