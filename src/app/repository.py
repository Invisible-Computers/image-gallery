import datetime
import secrets
from uuid import UUID

from django.utils.timezone import now

from .models import OneTimeToken


def generate_one_time_token_for_user_id(user_id: UUID) -> str:
    secret_token = secrets.token_urlsafe(50)[:50]
    OneTimeToken.objects.filter(owner_id=user_id).delete()
    one_time_token = OneTimeToken.objects.create(
        owner_id=user_id,
        token=secret_token,
        expiration_time=now() + datetime.timedelta(minutes=10),
    )

    return one_time_token.token
