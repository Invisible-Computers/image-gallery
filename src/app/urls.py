from django.urls import path

from .views import GetRender, Login, Settings, save_settings

urlpatterns = [
    path("login/", Login.as_view(), name="login"),
    path("settings/", Settings.as_view(), name="settings"),
    path("settings/save/", save_settings, name="save_settings"),
    path("render/", GetRender.as_view(), name="render"),
]
