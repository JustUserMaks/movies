from django.urls import path

from . views import index, error_page, upcoming_movie

urlpatterns = [
    path('', index, name='index'),
    path('', error_page, name='404'),
    path('', upcoming_movie, name='upcoming_movie')
]
