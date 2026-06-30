from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from koro.views import KoroDashboardView
from public.views import HomeView
from tikina.views import TikinaDashboardView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('tikina/', include('tikina.urls', namespace='tikina')),
    path('koro/', include('koro.urls', namespace='koro')),
    path('news/', include('news.urls', namespace='news')),
    path('events/', include('events.urls', namespace='events')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('', include("public.urls")),
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/koro/", KoroDashboardView.as_view(), name="koro_dashboard"),
    path("dashboard/tikina/", TikinaDashboardView.as_view(), name="tikina_dashboard"),
    path("dashboard/yavusa/", include("yavusa.urls")),
    path("dashboard/admin/", include("admin_panel.urls")),
    path("turani/", include("turani.urls")),
    path("mata-ni-tikina/", include("mata_ni_tikina.urls")),
    path("turaga-ni-yavusa/", include("turaga_ni_yavusa.urls")),
    path("roko/", include("roko.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
