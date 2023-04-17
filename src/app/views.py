import datetime
import io
import os
from typing import Optional
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

    permission_classes = []

    def get(self, request):
        user_id, _ = authenticate_jwt(request)
        one_time_token = generate_one_time_token_for_user_id(user_id=user_id)
        return Response({"login_token": one_time_token})


class Settings(View):  # NOT a DRF view!!
    def get(self, request):
        user_id, device = authenticate_login_token_or_session(request)
        # Return a simple form where the user can configure if the
        # device is vertically or horizontally oriented.
        device_type = request.session.get("device-type") or request.GET["device-type"]

        return render(
            request=request,
            template_name="settings.html",
            context={
                "device_id": device.device_id,
                "device_type": device_type,
                "is_vertically_oriented": device.is_vertically_oriented,
            },
        )


def save_settings(request):
    user_id, device = authenticate_login_token_or_session(request)

    is_vertically_oriented = request.POST["orientation"] == "vertical"
    device.is_vertically_oriented = is_vertically_oriented
    device.save()
    return HttpResponseRedirect(reverse("settings"))


class GetRender(APIView):

    permission_classes = []  # We handle authentication inside the view

    def get(self, request):
        user_id, device = authenticate_jwt(request)
        device_type = request.GET["device-type"]

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


## Authentication methods


def authenticate_login_token_or_session(request):

    # Try to authenticate with the login token
    user_id, device = _maybe_authenticate_login_token(request)
    if user_id:
        request.session["user-id"] = str(user_id)
        request.session["device-id"] = str(device.device_id)
        return user_id, device
    # Try to authenticate with the session
    user_id, device = _maybe_authenticate_session(request)
    if user_id:
        return user_id, device

    raise PermissionDenied("Not authenticated")


def authenticate_jwt(request) -> tuple[UUID, Optional[Device]]:
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
    user_id = UUID(decoded_token["user_id"])
    device_id_str = request.GET.get("device-id", None)
    device_id = UUID(device_id_str) if device_id_str else None
    if device_id:
        device = claim_device(device_id=device_id, user_id=user_id)
    else:
        device = None
    return user_id, device


def claim_device(device_id: UUID, user_id: UUID) -> Device:

    device, created = Device.objects.get_or_create(
        device_id=device_id, owner_id=user_id
    )
    if device.owner_id != user_id:
        raise PermissionDenied("Not authenticated")
    return device


def _maybe_authenticate_login_token(request) -> tuple[Optional[UUID], Optional[Device]]:
    login_token = request.GET.get("login-token")
    device_id = request.GET.get("device-id")
    if login_token and device_id:
        one_time_token_object = OneTimeToken.objects.filter(token=login_token).first()
        if one_time_token_object:
            if one_time_token_object.expiration_time > datetime.datetime.now(
                tz=pytz.UTC
            ):
                user_id = one_time_token_object.owner_id
                one_time_token_object.delete()
                device = claim_device(device_id=device_id, user_id=user_id)
                return user_id, device
    return None, None


def _maybe_authenticate_session(request) -> tuple[Optional[UUID], Optional[Device]]:
    user_id = UUID(request.session.get("user-id", None))
    device_id = UUID(request.session.get("device-id", None))
    if user_id and device_id:
        device = claim_device(device_id=device_id, user_id=user_id)
        return user_id, device
    return None, None
