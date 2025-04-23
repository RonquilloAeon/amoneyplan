"""
URL configuration for amoneyplan project.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from amoneyplan.api.schema import schema


# Simple health check view
def health_check(request):
    return HttpResponse(status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True))),
    path("accounts/", include("allauth.urls")),
    path("health", health_check, name="health_check"),
]
