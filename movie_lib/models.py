from django.db import models


# Create your models here.


class Film(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    poster = models.ImageField(upload_to='posters')
    poster_url = models.URLField()
    description = models.TextField()
    trailer_link = models.URLField(
        blank=True,
        default=''
    )
    release_year = models.CharField(max_length=4)
    countries = models.ManyToManyField(
        'Country',
        related_name='films'
    )
    genres = models.ManyToManyField(
        'Genre',
        related_name='films'
    )
    director = models.ManyToManyField(
        'Director',
        related_name='films'
    )
    actors = models.ManyToManyField(
        'Actor',
        related_name='films'
    )
    duration = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )
    rating = models.FloatField(
        null=True,
        blank=True
    )
    imdb_reviews = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )


class Country(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Director(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, max_length=100)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Actor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, max_length=100)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Snap(models.Model):
    url = models.URLField()
    image = models.ImageField(upload_to='snaps', null=True, blank=True)
    film = models.ForeignKey('Film',
                             on_delete=models.CASCADE,
                             related_name='snaps'
                             )

    def __str__(self):
        return self.url

