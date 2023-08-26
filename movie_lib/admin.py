from django.contrib import admin
from movie_lib import models
# Register your models here.

admin.site.register(models.Film)
admin.site.register(models.Director)
admin.site.register(models.Actor)
admin.site.register(models.Snap)
admin.site.register(models.Genre)
admin.site.register(models.Country)
