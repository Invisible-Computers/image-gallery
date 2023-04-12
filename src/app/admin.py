from django.contrib import admin

from .models import Device, OneTimeToken

admin.site.register(OneTimeToken)
admin.site.register(Device)
