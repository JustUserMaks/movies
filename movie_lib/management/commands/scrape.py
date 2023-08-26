from django.core.management import BaseCommand, CommandError
from movie_lib.services.scrape import main


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            main()
        except Exception as error:
            raise CommandError('Scraping error %s', error)
        self.stdout.write(self.style.SUCCESS('Scrape finished'))
