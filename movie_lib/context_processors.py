from django.db.models import Count

from .models import (Film,
                     Genre,
                     Actor,
                     Director,
                     Snap)


def header_genres(request):
    genres = Genre.objects.annotate(
        film_count=Count('films')
    ).order_by('-film_count')[:10]
    return {
        'genres': genres
    }
