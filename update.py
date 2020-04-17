import json
import requests
from bs4 import BeautifulSoup
import pandas
import os
import pickle
import unicodedata

path_base = r"D:\data\films\IMDb\film.tsv"
url = "https://www.imdb.com/title/"

main_data = pandas.DataFrame()

if os.path.exists("temp.pickle"):
    with open("temp.pickle", "rb") as f:
        main_data = pickle.load(f)
else:
    chunker = pandas.read_csv(path_base, sep='\t', iterator=True, chunksize=100000, low_memory=False)

    for chunk in chunker:
        main_data = pandas.concat((main_data, chunk[chunk['titleType'] == "movie"]))

    with open("temp.pickle", "wb") as f:
        pickle.dump(main_data, f)


def find_film(title: str):
    string_data = main_data[main_data['primaryTitle'] == title]
    if string_data.empty:
        string_data = main_data[main_data['originalTitle'] == title]
    return string_data


def get_html(id: str):
    html = requests.get(url + id)
    html.encoding = 'utf-8'
    return html.text


with open("movies.json", "r") as f:
    movies = json.load(f)

localed_genres = {}

structure = {}
for movie in movies:
    if int(movie['year']) > 1970:
        try:
            id_film = find_film(movie['title']).iloc[0]['tconst']
            html_code = BeautifulSoup(get_html(id_film), 'lxml')
            banner = html_code.find('div', class_="title_wrapper")
            rus_title = unicodedata.normalize("NFKD", banner.find('h1').get_text().split('(')[0]).rstrip(' ')

            poster = html_code.find('div', class_="poster").find('img').get('src')
            img = requests.get(poster)
            with open("posters\\" + rus_title + ".jpg", "wb") as f:
                f.write(img.content)

            stars = html_code.find('div', class_="plot_summary").find_all('div', class_="credit_summary_item")[-1]
            actors = []
            for actor in stars.find_all('a'):
                actors.append(actor.get_text())

            actors = actors[:len(actors) - 1]

            genres = []
            for genre in movie['genres']:
                if genre not in localed_genres:
                    rus_genre = input(genre + " - ")
                    localed_genres[genre] = rus_genre
                genres.append(localed_genres[genre])

            print(rus_title)
            structure['title'] = rus_title
            structure["directors"] = movie["directors"]
            structure["actors"] = actors
            structure["runtime"] = movie["runtime"]
            structure["year"] = movie["year"]
            structure["genres"] = genres

        except IndexError:
            continue

print(structure)
