import dataclasses
import datetime
import io
import os
import secrets
from typing import Any
from uuid import UUID

import jwt
import pytz
import requests
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now
from django.views import View
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppInstallation, OneTimeToken


class GetLoginToken(APIView):
    # Why do this login step and not pass the JWT directly to the settings page?
    # Because the mobile app will open the settings url in the browser, it can only pass a URL to the browser.
    # And passing a JWT in the URL is considered a security risk because it may leak,
    # for example via the browser history.
    # So we pass a one-time token instead, which is immediately expired after use.
    # If you are not worried about the JWT leaking, you can simply return it as the login_token and then re-validate it
    # in the settings page.

    permission_classes = []
    # For transparency, we handle permissions in the view itself.

    def get(self, request):
        decoded_jwt: DecodedJWT = authenticate_jwt(request)
        installation_id = decoded_jwt.installation_id
        one_time_token = generate_login_token(
            installation_id=installation_id,
        )
        # Optionally, you may also create-if-not-exists a user account here
        # and link it to the installation_id and/or the device_id.
        return Response({"login_token": one_time_token})


class Login(View):
    def get(self, request):
        login_token = request.GET.get("login-token")
        installation_id = authenticate_login_token(login_token=login_token)

        request.GET["device-type"]

        AppInstallation.objects.get_or_create(
            installation_id=installation_id,
        )

        # For a more complex app, for example, the installation entity may be linked to a device entity, which in turn
        # could be linked to a user entity.

        # You can also use user-linked sessions.
        request.session["installation-id"] = str(installation_id)

        # If you are using user-linked sessions, you could for example include the installation_id in the url of the settings page.
        return HttpResponseRedirect(reverse("settings"))


class Settings(View):  # NOT a DRF view!!
    def get(self, request):
        installation_id = authenticate_session(request)
        installation = AppInstallation.objects.get(installation_id=installation_id)

        return render(
            request=request,
            template_name="settings.html",
            context={
                "is_vertically_oriented": installation.is_vertically_oriented,
            },
        )

    def post(self, request):
        installation_id = authenticate_session(request)
        installation = AppInstallation.objects.get(installation_id=installation_id)

        is_vertically_oriented = request.POST["orientation"] == "vertical"
        installation.is_vertically_oriented = is_vertically_oriented
        installation.save()
        return HttpResponseRedirect(reverse("settings"))


class GetRender(APIView):

    permission_classes = []  # We handle authentication inside the view

    def get(self, request):
        decoded_jwt = authenticate_jwt(request)

        # This endpoint may be called before the settings page is first called.
        # If you are working with  user and device entities, you should create them here if they do not exist yet.
        # The decoded_jwt contains the user_id as well as the device_id. You can use these to create the entities.

        device_type = request.GET["device-type"]
        installation_id = decoded_jwt.installation_id
        installation, _ = AppInstallation.objects.get_or_create(
            installation_id=installation_id
        )

        if device_type == "BLACK_AND_WHITE_SCREEN_880X528":
            if installation.is_vertically_oriented:
                width = 528
                height = 880
            else:
                width = 880
                height = 528
        elif device_type == "BLACK_AND_WHITE_SCREEN_800X480":
            if installation.is_vertically_oriented:
                width = 480
                height = 800
            else:
                width = 800
                height = 480
        else:
            raise ValueError(f"Invalid device type{device_type}")
        cache_key = f"image_gallery_cache_key_{installation_id}_{width}_{height}"
        cache_value = cache.get(key=cache_key)
        image = io.BytesIO(cache_value) if cache_value else None

        if not image:
            image = requests.get(
                url=f"https://picsum.photos/{width}/{height}/",
                stream=True,
            ).raw
            cache.set(
                key=cache_key,
                value=image.read(),
                timeout=30 * 60,
            )
        return HttpResponse(image, content_type="application/octet-stream")


## Authentication and authorization methods


@dataclasses.dataclass
class DecodedJWT:
    user_id: UUID
    device_id: UUID
    installation_id: UUID

    def from_raw_jwt(jwt: dict[str, Any]) -> "DecodedJWT":
        return DecodedJWT(
            user_id=UUID(jwt["user_id"]),
            device_id=UUID(jwt["device_id"]),
            installation_id=UUID(jwt["installation_id"]),
        )


def authenticate_jwt(request) -> DecodedJWT:
    try:
        signed_token = request.META["HTTP_AUTHORIZATION"]
    except KeyError:
        raise AuthenticationFailed("No http auth header")
    try:
        decoded_token = jwt.decode(
            signed_token,
            os.environ["JWT_PUBLIC_KEY"].replace("\\n", "\n"),
            algorithms=["RS256"],
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")

    try:
        if decoded_token["developer_id"] != os.environ["MY_DEVELOPER_ID"]:
            raise AuthenticationFailed("Invalid developer id")
    except (KeyError, TypeError):
        raise AuthenticationFailed("Missing developer id")

    # At this point, we trust that the user is who they claim to be
    return DecodedJWT.from_raw_jwt(decoded_token)


def authenticate_login_token(login_token) -> UUID:
    if not login_token:
        raise AuthenticationFailed("No login token")
    one_time_token_object = OneTimeToken.objects.filter(token=login_token).first()
    if not one_time_token_object:
        raise AuthenticationFailed("Token does not exist")
    if one_time_token_object.expiration_time < datetime.datetime.now(tz=pytz.UTC):
        raise AuthenticationFailed("Token expired")

    installation_id = one_time_token_object.installation_id

    OneTimeToken.objects.filter(installation_id=installation_id).delete()
    return installation_id


def generate_login_token(
    installation_id: UUID,
) -> str:

    secret_token = secrets.token_urlsafe(50)[:50]
    OneTimeToken.objects.filter(installation_id=installation_id).delete()
    one_time_token = OneTimeToken.objects.create(
        installation_id=installation_id,
        token=secret_token,
        expiration_time=now() + datetime.timedelta(minutes=10),
    )

    return one_time_token.token


def authenticate_session(request) -> UUID:
    installation_id = UUID(request.session.get("installation-id"))
    if installation_id:
        return installation_id
    raise AuthenticationFailed("Session authentication failed")
