from time import perf_counter

from django.core.management import BaseCommand, CommandError
from movie_lib.services.one_scrape import main


class Command(BaseCommand):
    help = 'Scraping ua.kino website and write ot db'

    def handle(self, *args, **options):
        try:
            t1 = perf_counter()
            main()
            print(f'Time for scrapper {perf_counter() - t1:.2f} seconds')
        except Exception as error:
            raise CommandError('Scraping error %s', error)
        self.stdout.write(self.style.SUCCESS('Scrape finished'))
