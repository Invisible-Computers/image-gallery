import datetime
import io
import os
from uuid import UUID

import jwt
import pytz
import requests
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device, OneTimeToken
from .repository import generate_one_time_token_for_user_id


class Login(APIView):
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
        user_id, user_device_ids = authenticate_jwt(request)
        # TODO: If the mobile apps pass the device-id here as well,
        #  we can already do the get_or_create_device call here,
        #  this may be useful for some implementations.
        one_time_token = generate_one_time_token_for_user_id(
            user_id=user_id, user_device_ids=user_device_ids
        )
        return Response({"login_token": one_time_token})


class Settings(View):  # NOT a DRF view!!
    def get(self, request):
        try:
            login_token = request.GET.get("login-token")
            user_id, user_device_ids = authenticate_login_token(login_token=login_token)

            device_id = request.GET["device-id"]
            device_type = request.GET["device-type"]

            device = get_or_create_device(
                device_id=UUID(device_id),
                user_id=user_id,
                device_type=device_type,
                authorized_user_device_ids=user_device_ids,
            )

            # Put the data in the session, so it is still there when the user refreses the page. The OneTimeToken won't work anymore.
            request.session["user-id"] = str(user_id)
            request.session["device-id"] = str(device_id)
        except AuthenticationFailed:
            # This happens when the user refreshes the settings page, or when the form has posted and the page
            # is re-loaded.
            # We can trust what is in the session, because it is set by us and stored server-side.
            user_id, device_id = authenticate_session(request)
            device = Device.objects.get(device_id=device_id)
        return render(
            request=request,
            template_name="settings.html",
            context={
                "device_id": device_id,
                "device_type": device.device_type,
                "is_vertically_oriented": device.is_vertically_oriented,
            },
        )


def save_settings(request):
    user_id, device_id = authenticate_session(request)

    device = Device.objects.get(device_id=device_id)
    is_vertically_oriented = request.POST["orientation"] == "vertical"
    device.is_vertically_oriented = is_vertically_oriented
    device.save()
    return HttpResponseRedirect(reverse("settings"))


class GetRender(APIView):

    permission_classes = []  # We handle authentication inside the view

    def get(self, request):
        user_id, user_device_ids = authenticate_jwt(request)

        device_id = request.GET["device-id"]
        device_type = request.GET["device-type"]

        device = get_or_create_device(
            user_id=user_id,
            device_id=UUID(device_id),
            device_type=request.GET["device-type"],
            authorized_user_device_ids=user_device_ids,
        )

        if device_type == "BLACK_AND_WHITE_SCREEN_880X528":
            if device.is_vertically_oriented:
                width = 528
                height = 880
            else:
                width = 880
                height = 528
        elif device_type == "BLACK_AND_WHITE_SCREEN_800X480":
            if device.is_vertically_oriented:
                width = 480
                height = 800
            else:
                width = 800
                height = 480
        else:
            raise ValueError(f"Invalid device type{device_type}")
        cache_key = f"image_gallery_cache_key_{device.device_id}_{width}_{height}"
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


def get_or_create_device(
    device_id: UUID,
    user_id: UUID,
    device_type: str,
    authorized_user_device_ids: list[str],
) -> Device:
    """This function will only create the device if it is in the authorized_user_device_ids list.
    This is to prevent a user from claiming a device that does not belong to them."""

    authorized_user_device_ids = [UUID(item) for item in authorized_user_device_ids]

    if device_id not in authorized_user_device_ids:
        raise PermissionDenied("Device does not belong to user")

    device, created = Device.objects.get_or_create(
        device_id=device_id, defaults={"owner_id": user_id, "device_type": device_type}
    )
    if device.owner_id != user_id:
        raise PermissionDenied(
            "Device is already claimed by another user. "
            "This should never happen, because we verify that the device belongs to a user before creating it."
        )
    return device


def authenticate_jwt(request) -> tuple[UUID, list[str]]:
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
    user_id = UUID(decoded_token["user_id"])
    user_device_ids = decoded_token["user_device_ids"]
    return user_id, user_device_ids


def authenticate_login_token(login_token) -> tuple[UUID, list[str]]:
    if login_token:
        one_time_token_object = OneTimeToken.objects.filter(token=login_token).first()
        if not one_time_token_object:
            raise AuthenticationFailed("Token does not exist")
        if one_time_token_object.expiration_time < datetime.datetime.now(tz=pytz.UTC):
            raise AuthenticationFailed("Token expired")

        user_id = one_time_token_object.owner_id
        user_device_ids = one_time_token_object.user_device_ids
        one_time_token_object.delete()
        return user_id, user_device_ids
    raise AuthenticationFailed("No login token")


def authenticate_session(request) -> tuple[UUID, UUID]:
    user_id = UUID(request.session.get("user-id"))
    device_id = UUID(request.session.get("device-id"))
    if user_id and device_id:
        return user_id, device_id
    raise AuthenticationFailed("Session authentication failed")
