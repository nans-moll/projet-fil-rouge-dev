"""URL routing principal."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls", namespace="core")),
    path("comptes/", include("apps.accounts.urls", namespace="accounts")),
    path("biens/", include("apps.properties.urls", namespace="properties")),
    path("transactions/", include("apps.transactions.urls", namespace="transactions")),
    path("analytics/", include("apps.analytics.urls", namespace="analytics")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Ymmo — Administration"
admin.site.site_title = "Ymmo Admin"
admin.site.index_title = "Tableau de bord"
