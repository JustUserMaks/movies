from http import HTTPStatus
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from queue import Queue
from threading import Lock
from time import sleep

import httpx
from selectolax.parser import HTMLParser

url_movies = 'https://uakino.club/filmy/'
demo_page = 'https://uakino.club/filmy/genre-action/17795-kolektiv.html'


def request_to_url(url):
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


def get_pagination_links(url: str) -> list[str]:
    pages_html = []
    while True:
        print('Working with url:', url)
        response = request_to_url(url)
        print(type(response))
        pages_html.append(response)  # Append the html_string from page to the list
        print('HTML string added to list')
        try:
            response = HTMLParser(response)
            parse_next_url = response.css_first('.pnext a')
            if parse_next_url:
                url = parse_next_url.attributes.get('href')
                print('Next URL:', url)
            else:
                break  # Exit the loop if there's no next URL
        except AttributeError:
            break
    return pages_html


def parse_movies_pages(html_string: str):
    tree = HTMLParser(html_string)
    movie_pages = tree.css('.movie-item.short-item a.movie-title')
    for movie in movie_pages:
        title = movie.text(strip=True)
        link = movie.attributes.get('href')
        print(title, link)


def parse_page(html_string: str) -> dict:
    tree = HTMLParser(html_string)

    # Extract original title
    original_title = tree.css_first('.origintitle').text()

    # Extract poster link
    poster_link_node = tree.css_first('.film-poster a')
    poster_link = poster_link_node.attributes.get('href')

    # Extract movie description
    movie_description = tree.css_first('.full-text.clearfix').text(strip=True)

    # Extract trailer link
    trailer_node = tree.css('.box.full-text iframe[data-src]')
    trailer_link = None
    for node in trailer_node:
        trailer_link = node.attributes.get('data-src')

    # Extraction of movie additional info
    labels = tree.css('div.film-info div.fi-item .fi-label')
    values = tree.css('div.film-info div.fi-item .fi-desc')
    labels = [label.text(strip=True) for label in labels]
    values = [value.text(strip=True) for value in values]
    data = dict(zip(labels, values))  # Dict of data collected through cycles

    release_date = data.get('Рік виходу:', '')
    country = data.get('Країна:', '')
    genre = data.get('Жанр:', '')
    director = data.get('Режисер:', '')
    actors = data.get('Актори:', '')
    duration = data.get('Тривалість:', '')
    imdb_rate = data.get('', '')  # Replace with the actual label for IMDb rating

    # Collecting snapshots from movie
    snap_shots = tree.css('div.screens-section a')
    snap_links = [snap_link.attributes.get('href') for snap_link in snap_shots]

    # Create and return the dictionary with movie details
    movie_details = {
        original_title: {
            'poster_link': poster_link,
            'movie_description': movie_description,
            'trailer_link': trailer_link,
            'release_date': release_date,
            'country': country,
            'genre': genre,
            'director': director,
            'actors': actors,
            'duration': duration,
            'imdb_rate': imdb_rate,
            'snap_links': snap_links
        }
    }

    return movie_details


def demo_parse_page(url: str):
    html_string = request_to_url(url)
    tree = HTMLParser(html_string)

    # extract original title
    original_title = tree.css_first('.origintitle').text()

    # extract poster link
    poster_link_node = tree.css_first('.film-poster a')
    poster_link = poster_link_node.attributes.get('href')

    # extract movie description
    movie_description = tree.css_first('.full-text.clearfix').text(strip=True)

    # extract trailer link
    trailer_node = tree.css('.box.full-text iframe[data-src]')
    trailer_link = None
    for node in trailer_node:
        trailer_link = node.attributes.get('data-src')

    # extraction of movie additional info
    labels = tree.css('div.film-info div.fi-item .fi-label')
    values = tree.css('div.film-info div.fi-item .fi-desc')
    labels = [label.text(strip=True) for label in labels]
    values = [value.text(strip=True) for value in values]
    data = dict(zip(labels, values))  # dict of data collected through cycle

    release_date = data['Рік виходу:']
    country = data['Країна:']
    genre = data['Жанр:']
    director = data['Режисер:']
    actors = data['Актори:']
    duration = data['Тривалість:']
    imdb_rate = data['']

    #  collecting snapshots from movie
    snap_shots = tree.css('div.screens-section a')
    snap_links = [snap_link.attributes.get('href') for snap_link in snap_shots]

    print(original_title,
          poster_link,
          movie_description,
          trailer_link,
          release_date,
          country,
          genre,
          director,
          actors,
          duration,
          imdb_rate,
          snap_links,

          sep='\n')


def main():
    # get_pagination_links(url_movies)
    # parse_movies_pages()
    # parse_page()
    demo_parse_page(demo_page)
    sleep(10)


if __name__ == '__main__':
    main()
