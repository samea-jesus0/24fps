import requests
from flask import current_app

def buscar_filme_por_nome(nome_filme):
    api_key = current_app.config["OMDB_API_KEY"]
    url = f"http://www.omdbapi.com/?t={nome_filme}&apikey={api_key}&plot=full"

    response = requests.get(url)
    data = response.json()

    if data.get("Response") == "False":
        return None

    return {
        "titulo": data.get("Title"),
        "ano": data.get("Year"),
        "genero": data.get("Genre"),
        "diretor": data.get("Director"),
        "roteiro": data.get("Writer"),
        "atores": data.get("Actors"),
        "sinopse": data.get("Plot"),
        "poster": data.get("Poster"),
        "imdb": data.get("imdbRating")
    }