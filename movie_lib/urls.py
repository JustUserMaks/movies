from django.urls import path

from . views import IndexView, CatalogueView, movie

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('movie/', movie, name='movie'),
    path('catalogue/<slug:slug>/', CatalogueView.as_view(), name='catalogue'),
]
