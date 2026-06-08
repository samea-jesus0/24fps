from datetime import datetime

from flask import url_for
from sqlalchemy.orm import selectinload

from extensions import db
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie
from service.filme_service import buscar_filme_por_id, buscar_filme_por_nome


WISHLIST_TITLE_MAX_LENGTH = 120
WISHLIST_DESCRIPTION_MAX_LENGTH = 500
WISHLIST_MOVIE_TITLE_MAX_LENGTH = 255


def _isoformat(value):
    return value.isoformat() if value else None


def _date_label(value):
    if not value:
        return "Data nao informada"
    return value.strftime("%d/%m/%Y")


def _normalize_movie_title(title):
    return " ".join((title or "").strip().lower().split())


def _build_movie_key(movie_id, title):
    if movie_id:
        return f"imdb:{movie_id.strip().lower()}"
    return f"title:{_normalize_movie_title(title)}"


def _wishlist_movie_payload(movie):
    return {
        "id": movie.id,
        "movieId": movie.filme_id,
        "title": movie.filme_titulo,
        "posterUrl": movie.poster_url,
        "addedAt": _isoformat(movie.added_at),
        "addedAtLabel": _date_label(movie.added_at),
    }


def _sorted_wishlist_movies(wishlist):
    return sorted(
        wishlist.movies or [],
        key=lambda movie: (movie.added_at or datetime.min, movie.id or 0),
        reverse=True,
    )


def _wishlist_payload(wishlist, public_profile=False):
    movies = _sorted_wishlist_movies(wishlist)
    payload = {
        "id": wishlist.id,
        "title": wishlist.titulo,
        "description": wishlist.descricao or "",
        "isPublic": bool(wishlist.is_public),
        "visibilityLabel": "Publica" if wishlist.is_public else "Privada",
        "movieCount": len(movies),
        "movies": [_wishlist_movie_payload(movie) for movie in movies],
        "createdAt": _isoformat(wishlist.created_at),
        "createdAtLabel": _date_label(wishlist.created_at),
        "updatedAt": _isoformat(wishlist.updated_at),
        "updatedAtLabel": _date_label(wishlist.updated_at),
    }

    if public_profile:
        payload["url"] = url_for("users.public_profile", user_id=wishlist.user_id) + "#publicLists"

    return payload


def _wishlist_query():
    return Wishlist.query.options(selectinload(Wishlist.movies))


def _get_user_wishlist(user_id, wishlist_id):
    return _wishlist_query().filter_by(id=wishlist_id, user_id=user_id).first()


def _resolve_movie_details(movie_id=None, title=None, poster_url=None):
    resolved_title = (title or "").strip()
    resolved_movie_id = (movie_id or "").strip() or None
    resolved_poster_url = (poster_url or "").strip() or None

    try:
        movie_data = buscar_filme_por_id(resolved_movie_id) if resolved_movie_id else buscar_filme_por_nome(resolved_title)
    except Exception:
        movie_data = None

    if movie_data:
        resolved_title = (movie_data.get("titulo") or resolved_title or "").strip()
        resolved_movie_id = (movie_data.get("id") or resolved_movie_id or "").strip() or None
        resolved_poster_url = (movie_data.get("poster") or resolved_poster_url or "").strip() or None

    return resolved_title, resolved_movie_id, resolved_poster_url


def _find_existing_movie(wishlist, movie_id, normalized_title):
    for movie in wishlist.movies or []:
        if movie_id and movie.filme_id and movie.filme_id == movie_id:
            return movie
        if normalized_title and _normalize_movie_title(movie.filme_titulo) == normalized_title:
            return movie
    return None


def list_user_wishlists(user_id, public_only=False):
    query = _wishlist_query().filter_by(user_id=user_id)

    if public_only:
        query = query.filter_by(is_public=True)

    wishlists = query.order_by(Wishlist.updated_at.desc(), Wishlist.created_at.desc()).all()
    return [_wishlist_payload(wishlist) for wishlist in wishlists]


def list_public_wishlists(user_id):
    wishlists = (
        _wishlist_query()
        .filter_by(user_id=user_id, is_public=True)
        .order_by(Wishlist.updated_at.desc(), Wishlist.created_at.desc())
        .all()
    )
    return [_wishlist_payload(wishlist, public_profile=True) for wishlist in wishlists]


def create_wishlist(user_id, title, description="", is_public=True):
    title = (title or "").strip()
    description = (description or "").strip()

    if len(title) < 2:
        return None, "Informe um titulo com pelo menos 2 caracteres."

    if len(title) > WISHLIST_TITLE_MAX_LENGTH:
        return None, f"O titulo deve ter no maximo {WISHLIST_TITLE_MAX_LENGTH} caracteres."

    if len(description) > WISHLIST_DESCRIPTION_MAX_LENGTH:
        return None, f"A descricao deve ter no maximo {WISHLIST_DESCRIPTION_MAX_LENGTH} caracteres."

    wishlist = Wishlist(
        user_id=user_id,
        titulo=title,
        descricao=description or None,
        is_public=bool(is_public),
    )

    db.session.add(wishlist)
    db.session.commit()

    return _wishlist_payload(wishlist), None


def update_wishlist(user_id, wishlist_id, title, description="", is_public=True):
    wishlist = _get_user_wishlist(user_id, wishlist_id)
    if not wishlist:
        return None, "Wishlist nao encontrada."

    title = (title or "").strip()
    description = (description or "").strip()

    if len(title) < 2:
        return None, "Informe um titulo com pelo menos 2 caracteres."

    if len(title) > WISHLIST_TITLE_MAX_LENGTH:
        return None, f"O titulo deve ter no maximo {WISHLIST_TITLE_MAX_LENGTH} caracteres."

    if len(description) > WISHLIST_DESCRIPTION_MAX_LENGTH:
        return None, f"A descricao deve ter no maximo {WISHLIST_DESCRIPTION_MAX_LENGTH} caracteres."

    wishlist.titulo = title
    wishlist.descricao = description or None
    wishlist.is_public = bool(is_public)
    wishlist.updated_at = datetime.utcnow()
    db.session.commit()

    refreshed_wishlist = _get_user_wishlist(user_id, wishlist.id)
    return _wishlist_payload(refreshed_wishlist), None


def delete_wishlist(user_id, wishlist_id):
    wishlist = _get_user_wishlist(user_id, wishlist_id)
    if not wishlist:
        return "Wishlist nao encontrada."

    db.session.delete(wishlist)
    db.session.commit()
    return None


def add_movie_to_wishlist(user_id, wishlist_id, title, movie_id=None, poster_url=None):
    wishlist = _get_user_wishlist(user_id, wishlist_id)
    if not wishlist:
        return None, "Wishlist nao encontrada."

    raw_title = (title or "").strip()
    raw_movie_id = (movie_id or "").strip() or None
    raw_poster_url = (poster_url or "").strip() or None

    if len(raw_title) < 2 and not raw_movie_id:
        return None, "Informe o nome do filme ou selecione uma sugestao valida."

    resolved_title, resolved_movie_id, resolved_poster_url = _resolve_movie_details(
        movie_id=raw_movie_id,
        title=raw_title,
        poster_url=raw_poster_url,
    )

    if not resolved_title:
        resolved_title = raw_title

    if len(resolved_title) < 2:
        return None, "Nao foi possivel identificar o filme selecionado."

    if len(resolved_title) > WISHLIST_MOVIE_TITLE_MAX_LENGTH:
        return None, f"O titulo do filme deve ter no maximo {WISHLIST_MOVIE_TITLE_MAX_LENGTH} caracteres."

    normalized_title = _normalize_movie_title(resolved_title)
    existing_movie = _find_existing_movie(wishlist, resolved_movie_id, normalized_title)

    if existing_movie:
        return None, "Este filme ja esta nesta wishlist."

    wishlist_movie = WishlistMovie(
        wishlist_id=wishlist.id,
        movie_key=_build_movie_key(resolved_movie_id, resolved_title),
        filme_id=resolved_movie_id,
        filme_titulo=resolved_title,
        poster_url=resolved_poster_url,
    )

    wishlist.updated_at = datetime.utcnow()
    db.session.add(wishlist_movie)
    db.session.commit()

    refreshed_wishlist = _get_user_wishlist(user_id, wishlist.id)
    return _wishlist_payload(refreshed_wishlist), None


def remove_movie_from_wishlist(user_id, wishlist_id, wishlist_movie_id):
    wishlist = _get_user_wishlist(user_id, wishlist_id)
    if not wishlist:
        return None, "Wishlist nao encontrada."

    movie = next((item for item in wishlist.movies or [] if item.id == wishlist_movie_id), None)
    if not movie:
        return None, "Filme nao encontrado nesta wishlist."

    db.session.delete(movie)
    wishlist.updated_at = datetime.utcnow()
    db.session.commit()

    refreshed_wishlist = _get_user_wishlist(user_id, wishlist.id)
    return _wishlist_payload(refreshed_wishlist), None
