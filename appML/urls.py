from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import os
from core.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', preprocessing, name='preprocessing'),
    path('checker_page/', checker_page, name='checker_page'),
    path('clustering/', clustering, name='clustering'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
