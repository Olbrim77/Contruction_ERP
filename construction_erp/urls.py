# construction_erp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # EZ A SOR HIÁNYZOTT! (Ez adja hozzá a /accounts/login/ útvonalat)
    path('accounts/', include('django.contrib.auth.urls')),

    # A te alkalmazásod
    path('', include('projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)