from django.urls import path

from .views import *

urlpatterns = [

    path(
        "create/",
        PropertyCreateView.as_view()
    ),

    path(
        "my-properties/",
        MyPropertiesView.as_view()
    ),

    path(
        "<int:pk>/",
        PropertyDetailView.as_view()
    ),

    path(
        "<int:pk>/update/",
        PropertyUpdateView.as_view()
    ),

    path(
        "<int:pk>/delete/",
        PropertyDeleteView.as_view()
    ),

    path(
        "media/upload/",
        PropertyMediaUploadView.as_view()
    ),

    path(
        "<int:property_id>/media/",
        PropertyMediaListView.as_view()
    ),

    path(
        "media/<int:pk>/delete/",
        PropertyMediaDeleteView.as_view()
    ),

    path(
        "rules/create/",
        PropertyRuleCreateView.as_view()
    ),

    path(
        "<int:property_id>/rules/",
        PropertyRuleListView.as_view()
    ),

    path("create/", UnitCreateView.as_view()),
    path("", UnitListView.as_view()),
    path("<int:pk>/", UnitDetailView.as_view()),
    path("<int:pk>/update/", UnitUpdateView.as_view()),
    path("<int:pk>/delete/", UnitDeleteView.as_view()),
]