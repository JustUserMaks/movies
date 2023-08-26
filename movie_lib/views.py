from django.shortcuts import render
from django.views.defaults import page_not_found


def index(request):
    return render(request, 'index.html')


def error_page(request, exception=None):  # Pass the exception parameter
    return page_not_found(request, exception, template_name='404.html')


def upcoming_movie(request):
    return render(request, 'upcoming_movie.html')
