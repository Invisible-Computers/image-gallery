from django.db import models


class OneTimeToken(models.Model):

    installation_id = models.UUIDField(unique=True)
    expiration_time = models.DateTimeField()
    token = models.CharField(max_length=100)


class AppInstallation(models.Model):
    installation_id = models.UUIDField(unique=True, primary_key=True)
    is_vertically_oriented = models.BooleanField(default=False)
