from django.urls import path

from .views import (
    GetLoginToken,
    GetRender,
    Login,
    Settings,
)

urlpatterns = [
    path("get-login-token/", GetLoginToken.as_view(), name="login"),
    path(
        "login/",
        Login.as_view(),
        name="login",
    ),
    path("settings/", Settings.as_view(), name="settings"),
    path("render/", GetRender.as_view(), name="render"),
]
