from django.urls import path

from .views import (
    RegisterDeviceView,
    RemoveDeviceView,
)

urlpatterns = [

    path(
        "register-device/",
        RegisterDeviceView.as_view(),
    ),

    path(
        "remove-device/",
        RemoveDeviceView.as_view(),
    ),

]