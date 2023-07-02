from django.contrib import admin

from .models import AuthorizedDevice, OneTimeToken

admin.site.register(OneTimeToken)
admin.site.register(AuthorizedDevice)
