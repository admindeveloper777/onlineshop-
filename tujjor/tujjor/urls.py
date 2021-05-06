from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/',include('user.urls')),
    path('',include('user.urls')),
    path('home/',include('home.urls')),
    path('',include('home.urls')),
    path('order/',include('order.urls')),
    path('',include('order.urls')),
    path('product/',include('product.urls')),
    path('',include('product.urls')),
    path('i18n/',include('django.conf.urls.i18n')),
    path('ckeditor/',include('ckeditor_uploader.urls')),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
