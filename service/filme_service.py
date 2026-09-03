import math
import re
from functools import lru_cache

import requests
from flask import current_app


OMDB_BASE_URL = "http://www.omdbapi.com/"
CATALOG_PAGE_SIZE = 4
CATALOG_API_PAGES_PER_LOAD = 1
CATALOG_MAX_SEARCH_PAGES = 5
CATALOG_DURATION_BUCKETS = [
    {"value": "under-90", "label": "Ate 90 min"},
    {"value": "90-120", "label": "90 a 120 min"},
    {"value": "120-150", "label": "120 a 150 min"},
    {"value": "150-plus", "label": "150+ min"},
]
CATALOG_SORT_OPTIONS = [
    {"value": "featured", "label": "Ordem recomendada"},
    {"value": "year_desc", "label": "Ano: mais recentes"},
    {"value": "year_asc", "label": "Ano: mais antigos"},
    {"value": "rating_desc", "label": "IMDb: maior nota"},
    {"value": "runtime_desc", "label": "Duracao: mais longos"},
    {"value": "title_asc", "label": "Titulo: A-Z"},
]
CATALOG_SECTIONS = [
    {
        "slug": "action",
        "title": "Acao",
        "genre_name": "Action",
        "description": "Perseguicoes, adrenalina, reviravoltas e energia alta para quando a sessao pede movimento.",
        "note": "Acao e o genero para quando voce quer sentir o cinema correndo na frente da poltrona.",
        "featured_ids": ["tt1392190", "tt4633694", "tt1877830"],
        "search_terms": ["mad max", "john wick", "mission impossible", "the raid"],
    },
    {
        "slug": "drama",
        "title": "Drama",
        "genre_name": "Drama",
        "description": "Filmes guiados por personagens, conflitos fortes e cenas que continuam ecoando depois dos creditos.",
        "note": "Drama costuma ser onde a gente encontra as historias que ficam conversando com a nossa propria vida.",
        "featured_ids": ["tt2582802", "tt4975722", "tt7286456"],
        "search_terms": ["moonlight", "whiplash", "nomadland", "tar"],
    },
    {
        "slug": "comedy",
        "title": "Comedia",
        "genre_name": "Comedy",
        "description": "Leveza, timing e filmes perfeitos para desarmar o dia sem abrir mao de personalidade.",
        "note": "Comedia boa nao serve so para rir: ela muda o ritmo da casa inteira e deixa a noite mais leve.",
        "featured_ids": ["tt0449059", "tt1452459", "tt4925292"],
        "search_terms": ["booksmart", "superbad", "little miss sunshine", "bottoms"],
    },
    {
        "slug": "romance",
        "title": "Romance",
        "genre_name": "Romance",
        "description": "Encontros, despedidas e filmes que vivem no olhar, no tempo e no que poderia ter sido.",
        "note": "Romance funciona quando a gente quer um filme que abrace, aperte e deixe um gosto de memoria.",
        "featured_ids": ["tt13238346", "tt0338013", "tt3783958"],
        "search_terms": ["past lives", "before sunrise", "pride and prejudice", "la la land"],
    },
    {
        "slug": "animation",
        "title": "Animacao",
        "genre_name": "Animation",
        "description": "Universos autorais, cor, invencao visual e historias que atravessam qualquer idade.",
        "note": "Animacao e um genero incrivel para lembrar que forma e emocao podem dancar juntas.",
        "featured_ids": ["tt0245429", "tt0327597", "tt0129167"],
        "search_terms": ["spirited away", "coraline", "toy story", "klaus"],
    },
    {
        "slug": "sci-fi",
        "title": "Ficcao Cientifica",
        "genre_name": "Sci-Fi",
        "description": "Ideias grandes, futuros estranhos e filmes que usam o impossivel para falar do presente.",
        "note": "Ficcao cientifica brilha quando faz a gente imaginar o futuro e entender melhor o agora.",
        "featured_ids": ["tt2543164", "tt1856101", "tt1160419"],
        "search_terms": ["arrival", "ex machina", "blade runner", "dune"],
    },
]


def _parse_year(value):
    if not value or value == "N/A":
        return None

    match = re.search(r"\d{4}", str(value))
    return int(match.group()) if match else None


def _parse_runtime(value):
    if not value or value == "N/A":
        return None

    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def _parse_float(value):
    if not value or value == "N/A":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _split_list(value):
    if not value or value == "N/A":
        return []

    return [item.strip() for item in str(value).split(",") if item.strip()]


def _get_api_key():
    return current_app.config.get("OMDB_API_KEY")


@lru_cache(maxsize=512)
def _request_movie_by_title_cached(api_key, title):
    if not api_key:
        raise RuntimeError("OMDB_API_KEY nao configurada.")

    response = requests.get(
        OMDB_BASE_URL,
        params={"t": title, "apikey": api_key, "plot": "full"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=1024)
def _request_movie_by_id_cached(api_key, imdb_id):
    if not api_key:
        raise RuntimeError("OMDB_API_KEY nao configurada.")

    response = requests.get(
        OMDB_BASE_URL,
        params={"i": imdb_id, "apikey": api_key, "plot": "full"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=2048)
def _request_search_page_cached(api_key, search_term, page):
    if not api_key:
        raise RuntimeError("OMDB_API_KEY nao configurada.")

    response = requests.get(
        OMDB_BASE_URL,
        params={"s": search_term, "type": "movie", "page": page, "apikey": api_key},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _normalize_movie_data(data, source_rank=0):
    if not data or data.get("Response") == "False":
        return None

    genres = _split_list(data.get("Genre"))
    countries = _split_list(data.get("Country"))
    languages = _split_list(data.get("Language"))
    runtime_minutes = _parse_runtime(data.get("Runtime"))
    year = _parse_year(data.get("Year"))
    imdb_rating = _parse_float(data.get("imdbRating"))

    return {
        "id": data.get("imdbID"),
        "titulo": data.get("Title"),
        "ano": year,
        "ano_label": data.get("Year") if data.get("Year") and data.get("Year") != "N/A" else "Nao informado",
        "genero": data.get("Genre"),
        "generos": genres,
        "diretor": data.get("Director"),
        "roteiro": data.get("Writer"),
        "atores": data.get("Actors"),
        "sinopse": data.get("Plot"),
        "poster": None if data.get("Poster") == "N/A" else data.get("Poster"),
        "imdb": data.get("imdbRating"),
        "imdb_valor": imdb_rating,
        "duracao": data.get("Runtime"),
        "duracao_minutos": runtime_minutes,
        "classificacao": data.get("Rated") if data.get("Rated") and data.get("Rated") != "N/A" else "Nao informado",
        "pais": data.get("Country"),
        "paises": countries,
        "idioma": data.get("Language"),
        "idiomas": languages,
        "rank": source_rank,
    }


def buscar_filme_por_nome(nome_filme):
    api_key = _get_api_key()
    data = _request_movie_by_title_cached(api_key, nome_filme.strip())
    return _normalize_movie_data(data)


def buscar_filme_por_id(imdb_id):
    api_key = _get_api_key()
    data = _request_movie_by_id_cached(api_key, imdb_id.strip())
    return _normalize_movie_data(data)


def resolver_metadados_filme(movie_id=None, title=None):
    movie_id = (movie_id or "").strip()
    title = (title or "").strip()

    movie = buscar_filme_por_id(movie_id) if movie_id else None
    if not movie and title:
        movie = buscar_filme_por_nome(title)

    if not movie:
        return {}

    genres = movie.get("generos") or _split_list(movie.get("genero"))

    return {
        "filme_id": movie.get("id") or movie_id or None,
        "filme_titulo": movie.get("titulo") or title,
        "poster_url": movie.get("poster"),
        "generos": ", ".join(genres) if genres else None,
        "ano_lancamento": movie.get("ano"),
    }


def _fetch_movie_by_id(imdb_id, source_rank=0):
    api_key = _get_api_key()
    data = _request_movie_by_id_cached(api_key, imdb_id)
    return _normalize_movie_data(data, source_rank=source_rank)


def _parse_total_results(data):
    try:
        return int(data.get("totalResults", 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def _match_duration_bucket(movie, duration_bucket):
    runtime_minutes = movie.get("duracao_minutos")
    if runtime_minutes is None or not duration_bucket:
        return True

    if duration_bucket == "under-90":
        return runtime_minutes < 90
    if duration_bucket == "90-120":
        return 90 <= runtime_minutes <= 120
    if duration_bucket == "120-150":
        return 121 <= runtime_minutes <= 150
    if duration_bucket == "150-plus":
        return runtime_minutes > 150
    return True


def _movie_matches_filters(movie, filters):
    search_term = (filters.get("search") or "").strip().lower()
    if search_term:
        haystack = " ".join(
            [
                movie.get("titulo") or "",
                movie.get("diretor") or "",
                movie.get("atores") or "",
                movie.get("sinopse") or "",
            ]
        ).lower()
        if search_term not in haystack:
            return False

    year_min = filters.get("year_min")
    year_max = filters.get("year_max")
    country = filters.get("country")
    classification = filters.get("classification")
    language = filters.get("language")
    duration_bucket = filters.get("duration")

    if year_min and (movie.get("ano") is None or movie["ano"] < year_min):
        return False

    if year_max and (movie.get("ano") is None or movie["ano"] > year_max):
        return False

    if country and country not in movie.get("paises", []):
        return False

    if classification and movie.get("classificacao") != classification:
        return False

    if language and language not in movie.get("idiomas", []):
        return False

    if not _match_duration_bucket(movie, duration_bucket):
        return False

    return True


def _movie_matches_section_genre(section, movie):
    return section["genre_name"] in movie.get("generos", [])


def _sort_movies(movies, sort_key):
    if sort_key == "year_desc":
        return sorted(movies, key=lambda movie: (movie.get("ano") or 0, movie.get("titulo") or ""), reverse=True)
    if sort_key == "year_asc":
        return sorted(movies, key=lambda movie: (movie.get("ano") or 9999, movie.get("titulo") or ""))
    if sort_key == "rating_desc":
        return sorted(movies, key=lambda movie: (movie.get("imdb_valor") or 0, movie.get("titulo") or ""), reverse=True)
    if sort_key == "runtime_desc":
        return sorted(
            movies,
            key=lambda movie: (movie.get("duracao_minutos") or 0, movie.get("titulo") or ""),
            reverse=True,
        )
    if sort_key == "title_asc":
        return sorted(movies, key=lambda movie: (movie.get("titulo") or "").lower())

    return sorted(movies, key=lambda movie: (movie.get("rank") or 0, movie.get("titulo") or ""))


def _build_filter_options(movies_by_id):
    movies = list(movies_by_id.values())
    years = sorted(movie["ano"] for movie in movies if movie.get("ano") is not None)
    countries = sorted({country for movie in movies for country in movie.get("paises", [])})
    classifications = sorted(
        {movie.get("classificacao") for movie in movies if movie.get("classificacao") and movie.get("classificacao") != "Nao informado"}
    )
    languages = sorted({language for movie in movies for language in movie.get("idiomas", [])})

    return {
        "categories": [{"value": "all", "label": "Todos os generos"}]
        + [{"value": section["slug"], "label": section["title"]} for section in CATALOG_SECTIONS],
        "countries": countries,
        "classifications": classifications,
        "languages": languages,
        "duration_buckets": CATALOG_DURATION_BUCKETS,
        "sort_options": CATALOG_SORT_OPTIONS,
        "year_bounds": {
            "min": years[0] if years else None,
            "max": years[-1] if years else None,
        },
    }


def _normalize_filters(raw_filters):
    raw_filters = raw_filters or {}

    def parse_int(value):
        if value in (None, "", "None"):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return {
        "search": (raw_filters.get("search") or "").strip(),
        "category": raw_filters.get("category") or "all",
        "country": (raw_filters.get("country") or "").strip(),
        "classification": (raw_filters.get("classification") or "").strip(),
        "language": (raw_filters.get("language") or "").strip(),
        "duration": (raw_filters.get("duration") or "").strip(),
        "year_min": parse_int(raw_filters.get("year_min")),
        "year_max": parse_int(raw_filters.get("year_max")),
        "sort": raw_filters.get("sort") or "featured",
    }


def _normalize_section_pages(raw_filters):
    raw_filters = raw_filters or {}
    section_pages = {}

    for section in CATALOG_SECTIONS:
        raw_value = raw_filters.get(f"section_page_{section['slug']}")
        try:
            page = int(raw_value)
        except (TypeError, ValueError):
            page = 1

        section_pages[section["slug"]] = max(1, page)

    return section_pages


def _get_search_terms_for_section(section, filters):
    search_terms = []
    user_search = (filters.get("search") or "").strip()

    if user_search:
        search_terms.append(user_search)

    for search_term in section.get("search_terms", []):
        if search_term.lower() != user_search.lower():
            search_terms.append(search_term)

    return search_terms


def _append_movie_if_relevant(section, movie, filters, matched_movies, discovered_movies, seen_ids):
    movie_id = movie.get("id")
    if not movie_id or movie_id in seen_ids or not _movie_matches_section_genre(section, movie):
        return

    seen_ids.add(movie_id)
    discovered_movies[movie_id] = movie

    if _movie_matches_filters(movie, filters):
        matched_movies.append(movie)


def _load_featured_movies(section, filters, matched_movies, discovered_movies, seen_ids):
    for rank, imdb_id in enumerate(section.get("featured_ids", [])):
        movie = _fetch_movie_by_id(imdb_id, source_rank=rank)
        if movie:
            _append_movie_if_relevant(section, movie, filters, matched_movies, discovered_movies, seen_ids)


def _load_search_movies(section, filters, requested_page, matched_movies, discovered_movies, seen_ids, rank_offset):
    search_terms = _get_search_terms_for_section(section, filters)
    if not search_terms:
        return False

    search_page_limit = min(
        CATALOG_MAX_SEARCH_PAGES,
        max(1, requested_page * CATALOG_API_PAGES_PER_LOAD),
    )
    more_api_available = False
    rank_counter = rank_offset

    for search_term in search_terms:
        for search_page in range(1, search_page_limit + 1):
            data = _request_search_page_cached(_get_api_key(), search_term, search_page)
            if not data or data.get("Response") == "False":
                break

            total_results = _parse_total_results(data)
            total_pages = max(1, math.ceil(total_results / 10)) if total_results else 1
            if search_page < total_pages or search_page_limit < total_pages:
                more_api_available = True

            for search_item in data.get("Search") or []:
                imdb_id = search_item.get("imdbID")
                if not imdb_id or imdb_id in seen_ids:
                    continue

                movie = _fetch_movie_by_id(imdb_id, source_rank=rank_counter)
                rank_counter += 1
                if movie:
                    _append_movie_if_relevant(section, movie, filters, matched_movies, discovered_movies, seen_ids)

            if search_page >= total_pages:
                break

    return more_api_available


def _build_results_label(section, visible_movies, has_more):
    if has_more:
        return f"Mais filmes de {section['title']} podem ser buscados na API"
    if visible_movies:
        return f"{len(visible_movies)} filmes de {section['title']} carregados"
    return f"Nenhum filme de {section['title']} combinou com os filtros"


def _build_section_payload(section, filters, requested_page):
    matched_movies = []
    discovered_movies = {}
    seen_ids = set()

    _load_featured_movies(section, filters, matched_movies, discovered_movies, seen_ids)
    more_api_available = _load_search_movies(
        section,
        filters,
        requested_page,
        matched_movies,
        discovered_movies,
        seen_ids,
        rank_offset=len(section.get("featured_ids", [])),
    )

    sorted_movies = _sort_movies(matched_movies, filters.get("sort"))
    visible_limit = requested_page * CATALOG_PAGE_SIZE
    visible_movies = sorted_movies[:visible_limit]
    has_more = len(sorted_movies) > visible_limit or more_api_available

    return (
        {
            "slug": section["slug"],
            "title": section["title"],
            "description": section["description"],
            "note": section["note"],
            "movie_count": len(visible_movies),
            "total_filtered_movies": len(sorted_movies),
            "results_label": _build_results_label(section, visible_movies, has_more),
            "current_page": requested_page,
            "page_size": CATALOG_PAGE_SIZE,
            "has_more": has_more,
            "movies": visible_movies,
        },
        discovered_movies,
    )


def obter_catalogo_filmes(raw_filters=None):
    filters = _normalize_filters(raw_filters)
    section_pages = _normalize_section_pages(raw_filters)

    try:
        selected_section = filters.get("category") or "all"
        sections = []
        visible_movie_ids = set()
        discovered_movies_by_id = {}

        for section in CATALOG_SECTIONS:
            if selected_section != "all" and selected_section != section["slug"]:
                continue

            section_payload, discovered_movies = _build_section_payload(
                section,
                filters,
                section_pages.get(section["slug"], 1),
            )

            discovered_movies_by_id.update(discovered_movies)

            if not section_payload["movies"]:
                continue

            visible_movie_ids.update(movie["id"] for movie in section_payload["movies"] if movie.get("id"))
            sections.append(section_payload)

        options = _build_filter_options(discovered_movies_by_id)
    except requests.RequestException:
        current_app.logger.exception("Falha ao carregar filmes na OMDb.")
        return {
            "error": "Nao foi possivel carregar o catalogo agora. Tente novamente em instantes.",
            "sections": [],
            "stats": {"visible_movies": 0, "available_movies": 0, "visible_sections": 0},
            "options": _build_filter_options({}),
            "applied_filters": filters,
            "section_pages": section_pages,
        }
    except RuntimeError as exc:
        current_app.logger.exception("Configuracao da API ausente.")
        return {
            "error": str(exc),
            "sections": [],
            "stats": {"visible_movies": 0, "available_movies": 0, "visible_sections": 0},
            "options": _build_filter_options({}),
            "applied_filters": filters,
            "section_pages": section_pages,
        }

    return {
        "error": None,
        "sections": sections,
        "stats": {
            "visible_movies": len(visible_movie_ids),
            "available_movies": len(discovered_movies_by_id),
            "visible_sections": len(sections),
        },
        "options": options,
        "applied_filters": filters,
        "section_pages": section_pages,
    }


def buscar_sugestoes_filmes(query):
    """Busca sugestões de filmes na API do OMDb baseado em uma query."""
    api_key = current_app.config.get("OMDB_API_KEY")
    if not api_key:
        raise RuntimeError("OMDB_API_KEY não configurada.")

    url = f"http://www.omdbapi.com/?s={query}&apikey={api_key}&type=movie"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            suggestions = []
            for movie in data.get("Search", [])[:10]:  # Limita a 10 sugestões
                suggestions.append({
                    "titulo": movie.get("Title"),
                    "ano": movie.get("Year"),
                    "imdb_id": movie.get("imdbID"),
                    "poster": movie.get("Poster") if movie.get("Poster") != "N/A" else None
                })
            return suggestions
        else:
            return []
    except requests.RequestException:
        current_app.logger.exception("Falha ao buscar sugestões de filmes na OMDb.")
        return []
