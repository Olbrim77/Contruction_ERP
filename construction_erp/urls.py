# construction_erp/urls.py
from django.contrib import admin
from django.urls import path, include

# === ÚJ IMPORTOK A FÁJLKEZELÉSHEZ ===
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('projects.urls')),
]

# === EZT A SORT ADD HOZZÁ A VÉGÉHEZ ===
# Ez teszi lehetővé, hogy fejlesztés közben a Django kiszolgálja
# a feltöltött fájlokat (pl. a 'media' mappából).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)