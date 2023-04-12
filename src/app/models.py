from django.db import models


class OneTimeToken(models.Model):

    owner_id = models.UUIDField(unique=True)
    expiration_time = models.DateTimeField()
    token = models.CharField(max_length=100)


class Device(models.Model):
    device_id = models.UUIDField(unique=True, primary_key=True)
    owner_id = models.UUIDField()
    is_vertically_oriented = models.BooleanField(default=False)
