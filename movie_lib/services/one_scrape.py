import logging
from queue import Queue
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


from anyascii import anyascii
from django.utils.text import slugify
from django.db import transaction
import httpx
from selectolax.parser import HTMLParser

from movie_lib.models import Film, Country, Genre, Director, Actor, Snap

lock = Lock()
logger = logging.getLogger(__name__)

site_pages = []
movie_pages_list = []
PRODUCT_FIELDS = (
    'title',
    'poster_link',
    'movie_description',
    'trailer_link',
    'release_date',
    'country',
    'genre',
    'director',
    'actors',
    'duration',
    'imdb_rating',
    'imdb_reviews',
    'snap_shots'
)


def try_except_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.exception('An exception occurred: %s', e)
            result = None
        return result
    return wrapper


def request_to_url(url):
    # global html_string
    headers = {  # google headers for hidden request
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)"
    }

    try:  # start of try/except block for debugging and evading errors
        html_string = httpx.get(
            url,
            timeout=5,
            headers=headers,
        )
        assert html_string.status_code == 200  # checking response code
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while "
            f"requesting {exc.request.url!r}.")

    return html_string.text


# Function for extracting additional content
def add_content_extract(additional_info: list) -> dict | None:
    result = {}
    for item in additional_info:
        node = item.split(':')
        if len(node) > 1:
            result[node[0]] = [item for item in node[1].split(',')]
        else:
            node = node[0].split('/')
            if len(node) > 1:
                result['IMDb_Rating'] = node[0]
                result['IMDb_Reviews'] = node[1]
            else:
                result['IMDb_Rating'] = None
                result['IMDb_Reviews'] = None
    return result


def parse_page(url: str) -> dict:
    html_string = request_to_url(url)
    tree = HTMLParser(html_string)

    # extract original title
    original_title = tree.css_first('.origintitle').text()

    # extract poster link
    poster_link_node = tree.css_first('.film-poster a')
    poster_link = poster_link_node.attributes.get('href')
    if not poster_link.startswith('https://'):
        poster_link = 'https://uakino.club' + poster_link

    # extract movie description
    movie_description = tree.css_first('.full-text.clearfix').text(strip=True)

    # extract trailer link
    trailer_node = tree.css('.box.full-text iframe[data-src]')
    trailer_link = ''
    if trailer_node:
        for node in trailer_node:
            trailer_link = node.attributes.get('data-src')

    # Preparation for check if movie has additional content in specific class
    check_movie_content = tree.css('div.film-info div.fi-item')
    check_other_content = tree.css('div.film-info-serial div.fi-item-s')

    # extraction of movie additional info
    if len(check_movie_content) != 0:
        list_of_add_info = [item.text(strip=True) for item in check_movie_content]
        add_info = add_content_extract(list_of_add_info)
    else:
        list_of_add_info = [item.text(strip=True) for item in check_other_content]
        add_info = add_content_extract(list_of_add_info)

    # Extract release year as a single value (not a list)
    release_date = add_info.get('Рік виходу')[0] if add_info.get('Рік виходу') \
        else None

    # variable country cleansing
    country = add_info['Країна'] if add_info['Країна'] else None

    # variable genres cleansing
    genres = add_info['Жанр'] if add_info['Жанр'] else None

    # variable director cleansing
    director = add_info['Режисер'] if add_info['Режисер'] else None

    # variable actors cleansing
    actors = add_info['Актори'] if add_info['Актори'] else None

    # variable duration cleansing
    if 'Тривалість' in add_info:
        duration_list = add_info['Тривалість']
        if duration_list:
            duration = duration_list[0].split(' ', 1)[0]
        else:
            duration = None
    else:
        duration = None

    # variable imdb rating cleansing
    imdb_rating = add_info.get('IMDb_Rating') if add_info.get('IMDb_Rating')\
        else None

    # variable imdb reviews cleansing
    imdb_reviews = add_info.get('IMDb_Reviews') if add_info.get('IMDb_Reviews')\
        else None
    if imdb_reviews is not None:
        imdb_reviews = imdb_reviews.replace(' ', '')

    #  collecting snapshots from movie
    snap_shots = tree.css('div.screens-section a')
    snap_links = []
    for snap_shot in snap_shots:
        snap_shot_link = snap_shot.attributes.get('href')
        if not snap_shot_link.startswith('https://'):
            snap_shot_link = 'https://uakino.club' + snap_shot_link
            snap_links.append(snap_shot_link)
        else:
            snap_links.append(snap_shot_link)

    # Create and return the dictionary with movie details
    final_data = {
        'Title': original_title,
        'Poster_link': poster_link,
        'Movie_description': movie_description,
        'Trailer_link': trailer_link,
        'Release_date': release_date,
        'Country': country,
        'Genre': genres,
        'Director': director,
        'Actors': actors,
        'Duration': duration,
        'IMDb_Rating': imdb_rating,
        'IMDb_Reviews': imdb_reviews,
        'Snap_shots': snap_links
    }
    return final_data


def save_movie_poster_locally(poster_link: str, title: str) -> str:
    try:
        with httpx.Client() as client:
            response = client.get(poster_link)
            response.raise_for_status()

            if response.status_code == 404:
                logger.warning('Poster image for %s not found (404)', title)
                return None

            # Generate file name and path
            file_name = f'posters/{slugify(anyascii(title))}.jpg'
            file_path = f'media/{file_name}'

            # Save the image locally
            with open(file_path, 'wb') as file:
                file.write(response.content)

            return file_name  # Return the saved file name
    except Exception as exc:
        logger.exception(
            'An error occurred while saving the poster for %s: %s',
            title,
            exc
        )
        return None  # Return None if there's an error saving the poster


def save_movie_snaps_locally(snap_links: list, title: str, film: Film) -> list:
    saved_file_names = []  # Initialize a list to store saved file names

    for i, snap in enumerate(snap_links, start=1):
        try:
            with httpx.Client() as client:
                response = client.get(snap)

                # Check if the response status code is 404 (Not Found)
                if response.status_code == 404:
                    logger.warning('Snap image %d for %s not found (404)', i, title)

                response.raise_for_status()

                # Generate file name and path
                file_name = f'snaps/{slugify(anyascii(title))}-{i}.jpg'
                file_path = f'media/{file_name}'

                # Save the image locally
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                Snap.objects.create(
                    image=file_name,
                    url=snap,
                    film=film
                )

                saved_file_names.append(file_name)  # Add the saved file name to the list
        except Exception as exc:
            logger.exception(
                'An error occurred while saving snap %d for %s: %s',
                i,
                title,
                exc
            )
    return saved_file_names


@try_except_decorator
@transaction.atomic
def write_to_db(data: dict) -> None:
    file_name = save_movie_poster_locally(data['Poster_link'], data['Title'])

    film, created = Film.objects.get_or_create(
        slug=f"{slugify(anyascii(data['Title']))}-{data['Poster_link'].split('/')[-1]}",
        defaults={
            'title': data['Title'],
            'poster_url': data['Poster_link'],
            'description': data['Movie_description'],
            'trailer_link': data['Trailer_link'],
            'release_year': data['Release_date'],
            'duration': data['Duration'],
            'rating': data['IMDb_Rating'],
            'imdb_reviews': data['IMDb_Reviews'],
        }
    )

    if not created:
        film.title = data['Title']
        film.poster_url = data['Poster_link']
        film.description = data['Movie_description']
        film.trailer_link = data['Trailer_link']
        film.release_year = data['Release_date']
        film.duration = data['Duration']
        film.rating = data['IMDb_Rating']
        film.imdb_reviews = data['IMDb_Reviews']
        if file_name:
            film.poster = file_name
        film.save()

    if data['Country']:
        countries = [Country.objects.get_or_create(
            slug=slugify(anyascii(country)),
            defaults={
                'name': country,
            }
        )[0] for country in data['Country']]
        film.countries.set(countries)

    if data['Genre']:
        genres = [Genre.objects.get_or_create(
            slug=slugify(anyascii(genre)),
            defaults={
                'name': genre,
            }
        )[0] for genre in data['Genre']]
        film.genres.set(genres)

    if data['Director']:
        film.director.set([
            Director.objects.get_or_create(
                slug=slugify(anyascii(director_name)),
                defaults={'first_name': director_name.split(' ')[0],
                          'last_name': director_name.split(' ')[1]}
            )[0]
            for director_name in data['Director']
        ])

    if data['Actors']:
        film.actors.set([
            Actor.objects.get_or_create(
                slug=slugify(anyascii(actor_name)),
                defaults={'first_name': actor_name.split(' ')[0],
                          'last_name': actor_name.split(' ')[1]}
            )[0]
            for actor_name in data['Actors']
        ])

    if data['Snap_shots']:
        save_movie_snaps_locally(
            data['Snap_shots'],
            data['Title'],
            film
        )
    logger.info('Object "%s" written to db', data['Title'])


def main():
    # Main enter links
    url = 'https://uakino.club/seriesss/drama_series/16783-psi-doschu-1-sezon.html'
    parsed_data = parse_page(url)
    write_to_db(parsed_data)

    logger.info('Parsing complete')


if __name__ == '__main__':
    main()
