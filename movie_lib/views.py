from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views.defaults import page_not_found
from django.views.generic import TemplateView, ListView, DetailView

from .models import Genre, Film


class IndexView(TemplateView):
    template_name = 'index.html'


def error_page(request, exception=None):  # Pass the exception parameter
    return page_not_found(request, exception, template_name='404.html')


def upcoming_movie(request):
    context = {}
    return render(request, 'upcoming_movie.html', context=context)


def movie(request):
    context = {}
    return render(request, 'movie.html', context=context)


class CatalogueView(ListView):
    template_name = 'movies.html'
    model = Film
    context_object_name = 'films'
    slug_url_kwarg = 'slug'
    paginate_by = 24

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        genre = get_object_or_404(Genre, slug=slug)
        queryset = Film.objects.filter(
            ~Q(poster=''),
            genres=genre,
            poster__isnull=False
        )[:24]
        return queryset
