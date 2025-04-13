from django.contrib.sitemaps import Sitemap
from .models import Produs
from django.urls import reverse

class ProductSitemap(Sitemap):
    

    def items(self):
        return Produs.objects.all()

    def lastmod(self, obj):
        return obj.data_adaugare
    def location(self, obj):
        return reverse('product_detail', args=[obj.id]) 
