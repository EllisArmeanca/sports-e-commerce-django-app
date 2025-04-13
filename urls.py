from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ProductSitemap
# , StaticViewSitemap

sitemaps = {
    'products': ProductSitemap,
    # 'static': StaticViewSitemap,  # Adaugă și paginile statice (despre, contact etc.)
}

urlpatterns = [
    # path("", views.index, name="index"),
    path('produse/', views.lista_produse, name='lista_produse'),
    # path('filtreaza-produse/', views.filtreaza_produse, name='filtreaza_produse'),
    path('contact/', views.contact_view, name='contact-form'),
    path('adauga-produs/', views.creare_produs, name='adauga'),
    # path('profil/', views.profile_view, name='profile'),
    # path('schimba-parola/', views.change_password, name='change_password'),
    # path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('login/', views.login_view, name="login-view"),
    path('logout/', views.logout_view, name="logout-view"),
    path('register/', views.register_view, name='register-view'),
    path('profile/', views.profile_view, name='profile-view'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('confirma_mail/<str:cod>/', views.confirma_mail_view, name='confirma_mail'),
    path('produse/<int:produs_id>/', views.vizualizeaza_produs, name='vizualizeaza_produs'),
    path('promotii/', views.promotii, name='promotii'),
    path('eroare403/', views.eroare_403_view, name='403'),
    path('adauga-permisune/', views.adauga_permisune, name='adauga_permisune'),
    path('oferta/', views.oferta, name='oferta'),
    path('produs/<int:id>/', views.product_detail, name='product_detail'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),



]

urlpatterns += [
    path('cos/', views.cos_virtual, name='cos_virtual'),  # Afișarea coșului virtual
    path('cos/adauga/<int:produs_id>/', views.adauga_in_cos, name='adauga_in_cos'),  # Adăugare produs în coș
    path('cos/cantitate/adauga/<int:produs_id>/', views.adauga_cantitate, name='adauga_cantitate'),  # Creștere cantitate
    path('cos/cantitate/scade/<int:produs_id>/', views.scade_cantitate, name='scade_cantitate'),  # Scădere cantitate
    path('cos/sterge/<int:produs_id>/', views.sterge_din_cos, name='sterge_din_cos'),  # Ștergere produs din coș
]
