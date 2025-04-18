"""
URL configuration for amoneyplan project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from amoneyplan.api.schema import schema

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True))),
    path("accounts/", include("allauth.urls")),
]
