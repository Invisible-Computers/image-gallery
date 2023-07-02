from django.contrib import admin

from .models import AppInstallation, OneTimeToken

admin.site.register(OneTimeToken)
admin.site.register(AppInstallation)
