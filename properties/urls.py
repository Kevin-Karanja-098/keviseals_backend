from django.urls import path
from .views import *

urlpatterns = [

    # PROPERTY

    path(
        "properties/create/",
        PropertyCreateView.as_view()
    ),

    path(
        "properties/my/",
        MyPropertiesView.as_view()
    ),

    path(
        "properties/<int:pk>/",
        PropertyDetailView.as_view()
    ),

    path(
        "properties/<int:pk>/update/",
        PropertyUpdateView.as_view()
    ),

    path(
        "properties/<int:pk>/delete/",
        PropertyDeleteView.as_view()
    ),

    # PROPERTY MEDIA

    path(
        "properties/media/upload/",
        PropertyMediaUploadView.as_view()
    ),

    path(
        "properties/<int:property_id>/media/",
        PropertyMediaListView.as_view()
    ),

    path(
        "properties/media/<int:pk>/delete/",
        PropertyMediaDeleteView.as_view()
    ),

    # PROPERTY RULES

    path(
        "properties/rules/create/",
        PropertyRuleCreateView.as_view()
    ),

    path(
        "properties/<int:property_id>/rules/",
        PropertyRuleListView.as_view()
    ),

    # UNITS

    path(
        "units/create/",
        UnitCreateView.as_view()
    ),

    path(
        "units/",
        UnitListView.as_view()
    ),

    path(
        "units/<int:pk>/",
        UnitDetailView.as_view()
    ),

    path(
        "units/<int:pk>/update/",
        UnitUpdateView.as_view()
    ),

    path(
        "units/<int:pk>/delete/",
        UnitDeleteView.as_view()
    ),
]