function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function formatValue(value, fallback = "Nao informado") {
    if (!value || value === "N/A") {
        return fallback;
    }

    return escapeHtml(value);
}

function splitItems(value) {
    if (!value || value === "N/A") {
        return [];
    }

    return String(value)
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
}

function renderLoadingState(container) {
    container.innerHTML = `
        <div class="result-loading">
            <span class="loading-badge">buscando filme</span>
            <h3>Montando a ficha do seu proximo filme...</h3>
            <div class="loading-line"></div>
            <div class="loading-line"></div>
            <div class="loading-line"></div>
        </div>
    `;
}

function renderErrorState(container, title, description) {
    container.innerHTML = `
        <div class="error-card">
            <span class="result-kicker">search note</span>
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(description)}</p>
        </div>
    `;
}

let runtimeToastTimeout = null;

function showRuntimeToast(message, variant = "success") {
    let toast = document.getElementById("runtimeToast");

    if (!toast) {
        toast = document.createElement("div");
        toast.id = "runtimeToast";
        toast.className = "toast toast--runtime";
        document.body.appendChild(toast);
    }

    toast.className = `toast toast--runtime toast--${variant}`;
    toast.innerHTML = `<p>${escapeHtml(message)}</p>`;
    toast.classList.add("show");

    if (runtimeToastTimeout) {
        window.clearTimeout(runtimeToastTimeout);
    }

    runtimeToastTimeout = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

function buildPosterMarkup(data) {
    const poster = data.poster;
    const titulo = formatValue(data.titulo, "Filme");

    if (poster && poster !== "N/A") {
        return `<img class="result-poster" src="${escapeHtml(poster)}" alt="Poster de ${titulo}" loading="lazy">`;
    }

    return `
        <div class="result-poster--placeholder">
            <span>Poster nao disponivel</span>
        </div>
    `;
}

function renderMovieResult(data, searchedTitle) {
    const genres = splitItems(data.genero)
        .slice(0, 4)
        .map((genre) => `<span class="genre-chip">${escapeHtml(genre)}</span>`)
        .join("");

    const metaItems = [
        { label: "Ano", value: formatValue(data.ano) },
        { label: "Duracao", value: formatValue(data.duracao) },
        { label: "Classificacao", value: formatValue(data.classificacao) },
        { label: "IMDb", value: formatValue(data.imdb, "Sem nota") },
    ]
        .map((item) => `<span class="meta-chip">${item.label}: ${item.value}</span>`)
        .join("");

    const detailItems = [
        { label: "Direcao", value: formatValue(data.diretor) },
        { label: "Elenco", value: formatValue(data.atores) },
        { label: "Roteiro", value: formatValue(data.roteiro) },
        { label: "Pais", value: formatValue(data.pais) },
        { label: "Idioma", value: formatValue(data.idioma) },
        { label: "Busca", value: escapeHtml(searchedTitle) },
    ]
        .map(
            (item) => `
                <div class="detail-item">
                    <strong>${item.label}</strong>
                    <span>${item.value}</span>
                </div>
            `
        )
        .join("");

    return `
        <article class="result-card">
            <div class="result-poster-shell">
                ${buildPosterMarkup(data)}
            </div>

            <div class="result-copy">
                <div class="result-heading">
                    <span class="result-kicker">search result</span>
                    <h2>${formatValue(data.titulo, searchedTitle)}</h2>
                    <div class="result-meta">${metaItems}</div>
                    <div class="genre-row">${genres || '<span class="genre-chip">Genero nao informado</span>'}</div>
                </div>

                <div class="detail-grid">
                    ${detailItems}
                </div>

                <div class="synopsis">
                    <strong>Sinopse</strong>
                    <p>${formatValue(data.sinopse, "Sinopse nao disponivel.")}</p>
                </div>
            </div>
        </article>
    `;
}

function buildPublicMoviePosterMarkup(data) {
    const poster = data.poster;
    const titulo = formatValue(data.titulo, "Filme");

    if (poster && poster !== "N/A") {
        return `<img src="${escapeHtml(poster)}" alt="Poster de ${titulo}" loading="lazy">`;
    }

    return `
        <div class="public-detail-poster-placeholder">
            <span>Poster nao disponivel</span>
        </div>
    `;
}

async function buscarFilme() {
    const input = document.getElementById("movieInput");
    const resultado = document.getElementById("resultado");

    if (!input || !resultado) {
        return;
    }

    const nome = input.value.trim();

    if (!nome) {
        renderErrorState(resultado, "Digite o nome do filme", "Use um titulo para abrir a ficha do filme.");
        input.focus();
        return;
    }

    renderLoadingState(resultado);

    try {
        const response = await fetch("/buscar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ nome }),
        });

        const data = await response.json();

        if (!response.ok) {
            renderErrorState(
                resultado,
                data.erro || "Nao foi possivel encontrar o filme",
                "Tente usar o titulo original ou um nome mais completo."
            );
            return;
        }

        resultado.innerHTML = renderMovieResult(data, nome);
    } catch (error) {
        renderErrorState(
            resultado,
            "Erro ao buscar o filme",
            "Verifique sua conexao ou tente novamente em instantes."
        );
    }
}

function redirecionar_login() {
    window.location.href = "/login";
}

function redirecionar_perfil() {
    window.location.href = "/perfil";
}

function redirecionar_pesquisa() {
    window.location.href = "/pesquisa";
}

function isAcceptedImageFile(file) {
    if (!file || !file.name) {
        return false;
    }

    const acceptedExtensions = [".png", ".jpg", ".jpeg", ".gif"];
    const lowerName = file.name.toLowerCase();

    return acceptedExtensions.some((extension) => lowerName.endsWith(extension));
}

function setAvatarError(input, errorElement, message) {
    if (input) {
        input.setCustomValidity(message || "");
    }

    if (!errorElement) {
        return;
    }

    errorElement.textContent = message || "";
    errorElement.hidden = !message;
}

function updateAvatarPosition(editor) {
    const xInput = editor.querySelector("[data-avatar-pos-x]");
    const yInput = editor.querySelector("[data-avatar-pos-y]");
    const xValue = editor.querySelector("[data-avatar-pos-x-value]");
    const yValue = editor.querySelector("[data-avatar-pos-y-value]");
    const previews = editor.querySelectorAll("[data-avatar-preview]");

    const posX = `${xInput ? xInput.value : 50}%`;
    const posY = `${yInput ? yInput.value : 50}%`;

    previews.forEach((preview) => {
        preview.style.setProperty("--avatar-pos-x", posX);
        preview.style.setProperty("--avatar-pos-y", posY);
    });

    if (xValue && xInput) {
        xValue.textContent = `${xInput.value}%`;
    }

    if (yValue && yInput) {
        yValue.textContent = `${yInput.value}%`;
    }
}

function initAvatarEditor(editor) {
    const input = editor.querySelector("[data-avatar-input]");
    const errorElement = editor.querySelector("[data-file-error]");
    const previews = editor.querySelectorAll("[data-avatar-preview]");
    const xInput = editor.querySelector("[data-avatar-pos-x]");
    const yInput = editor.querySelector("[data-avatar-pos-y]");

    updateAvatarPosition(editor);

    if (xInput) {
        xInput.addEventListener("input", () => updateAvatarPosition(editor));
    }

    if (yInput) {
        yInput.addEventListener("input", () => updateAvatarPosition(editor));
    }

    if (!input) {
        return;
    }

    input.addEventListener("change", () => {
        const file = input.files && input.files[0];

        if (!file) {
            setAvatarError(input, errorElement, "");
            return;
        }

        if (!isAcceptedImageFile(file)) {
            setAvatarError(input, errorElement, "Formato invalido. Use PNG, JPG, JPEG ou GIF.");
            input.value = "";
            return;
        }

        setAvatarError(input, errorElement, "");

        const reader = new FileReader();
        reader.onload = function (loadEvent) {
            previews.forEach((preview) => {
                preview.src = loadEvent.target.result;
            });
        };
        reader.readAsDataURL(file);
    });
}

function previewImage(event) {
    const editor = event.target.closest("[data-avatar-editor]");
    if (editor) {
        initAvatarEditor(editor);
    }
}

const REVIEW_API_BASE = "/perfil/reviews";
const WISHLIST_API_BASE = "/perfil/wishlists";
const PUBLIC_MOVIE_DETAILS_API = "/api/movies/details";
const WISHLIST_MOVIES_PER_PAGE = 5;

function formatReviewDate(dateString) {
    if (!dateString) {
        return "Hoje";
    }

    const parsed = new Date(dateString);
    if (Number.isNaN(parsed.getTime())) {
        return dateString;
    }

    return parsed.toLocaleDateString("pt-BR");
}

function createReviewSlideMarkup(review) {
    let posterHtml = '';
    if (review.poster_url) {
        posterHtml = '<div class="review-poster"><img src="' + escapeHtml(review.poster_url) + '" alt="Poster" loading="lazy"></div>';
    }

    const reviewDate = formatReviewDate(review.updated_at || review.created_at);

    const posterClass = review.poster_url ? 'review-slide--with-poster' : 'review-slide--no-poster';

    return '<article class="review-slide ' + posterClass + ' is-active" data-review-id="' + escapeHtml(review.id) + '" data-review-movie-id="' + escapeHtml(review.filme_id || "") + '" data-review-poster-url="' + escapeHtml(review.poster_url || "") + '" data-review-created-at="' + escapeHtml(review.created_at || "") + '" data-review-updated-at="' + escapeHtml(review.updated_at || "") + '">' +
           '<div class="review-slide-layout">' +
           posterHtml +
           '<div class="review-slide-copy">' +
           '<div class="review-slide-top">' +
           '<span class="review-film">' + escapeHtml(review.filme_titulo) + '</span>' +
           '<span class="review-rating">' + escapeHtml(review.nota || 0) + '/5</span>' +
           '</div>' +
           '<p class="review-slide-text">' + escapeHtml(review.conteudo || "") + '</p>' +
           '<div class="review-slide-footer">' +
           '<span class="review-date">Atualizado em ' + escapeHtml(reviewDate) + '</span>' +
           '<button class="review-edit-button" type="button" data-review-id="' + escapeHtml(review.id) + '">Editar</button>' +
           '</div>' +
           '</div>' +
           '</div>' +
           '</article>';
}

function getReviewSlides() {
    return Array.from(document.querySelectorAll(".review-slide"));
}

function updateCarouselButtons() {
    const slides = getReviewSlides();
    const prevButton = document.querySelector(".review-nav[data-direction='prev']");
    const nextButton = document.querySelector(".review-nav[data-direction='next']");
    const activeIndex = slides.findIndex((slide) => slide.classList.contains("is-active"));

    if (!prevButton || !nextButton) {
        return;
    }

    prevButton.disabled = activeIndex <= 0;
    nextButton.disabled = activeIndex === -1 || activeIndex >= slides.length - 1;
}

function showReviewSlide(index) {
    const slides = getReviewSlides();
    slides.forEach((slide, slideIndex) => {
        slide.classList.toggle("is-active", slideIndex === index);
    });
    updateCarouselButtons();
}

function showReviewModal(mode = "create", review = null) {
    const modal = document.getElementById("reviewModal");
    const title = document.getElementById("reviewModalTitle");
    const reviewIdInput = document.getElementById("reviewIdInput");
    const filmeTitulo = document.getElementById("filmeTitulo");
    const reviewRating = document.getElementById("reviewRating");
    const reviewContent = document.getElementById("reviewContent");
    const deleteButton = document.getElementById("deleteReviewButton");
    const errorElement = document.getElementById("reviewFormError");

    if (!modal || !title || !reviewIdInput || !filmeTitulo || !reviewRating || !reviewContent || !deleteButton || !errorElement) {
        return;
    }

    modal.hidden = false;
    title.textContent = mode === "edit" ? "Editar resenha" : "Nova resenha";
    reviewIdInput.value = review?.id || "";
    filmeTitulo.value = review?.filme_titulo || "";
    filmeTitulo.setAttribute('data-filme-id', review?.filme_id || "");
    filmeTitulo.setAttribute('data-poster-url', review?.poster_url || "");
    reviewRating.value = review?.nota || 0;
    reviewContent.value = review?.conteudo || "";
    deleteButton.hidden = mode !== "edit";
    errorElement.hidden = true;
    errorElement.textContent = "";
    document.body.style.overflow = "hidden";

    // Inicializar autocomplete se ainda não foi inicializado
    if (!filmeTitulo.hasAttribute('data-autocomplete-init')) {
        // Adiar a inicialização para garantir que o modal esteja totalmente renderizado
        setTimeout(() => {
            initMovieAutocomplete(filmeTitulo);
            filmeTitulo.setAttribute('data-autocomplete-init', 'true');
        }, 100);
    }
}

function hideReviewModal() {
    const modal = document.getElementById("reviewModal");
    if (!modal) {
        return;
    }

    modal.hidden = true;
    document.body.style.overflow = "";
}

function showReviewError(message) {
    const errorElement = document.getElementById("reviewFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = message;
    errorElement.hidden = false;
}

function clearReviewError() {
    const errorElement = document.getElementById("reviewFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = "";
    errorElement.hidden = true;
}

function getActiveSlideIndex() {
    const slides = getReviewSlides();
    return slides.findIndex((slide) => slide.classList.contains("is-active"));
}

function addOrUpdateSlide(review) {
    const carousel = document.getElementById("reviewCarousel");
    const emptyState = document.getElementById("reviewEmptyState");
    const existingSlide = document.querySelector(`.review-slide[data-review-id='${review.id}']`);

    if (emptyState) {
        emptyState.remove();
    }

    if (existingSlide) {
        existingSlide.outerHTML = createReviewSlideMarkup(review);
    } else if (carousel) {
        carousel.insertAdjacentHTML("beforeend", createReviewSlideMarkup(review));
    }

    const slides = getReviewSlides();
    const newActive = Array.from(slides).findIndex((slide) => slide.dataset.reviewId === String(review.id));
    if (newActive !== -1) {
        showReviewSlide(newActive);
    }
}

function removeReviewSlide(reviewId) {
    const slide = document.querySelector(`.review-slide[data-review-id='${reviewId}']`);
    if (slide) {
        const slides = getReviewSlides();
        const currentIndex = slides.indexOf(slide);
        slide.remove();
        const remainingSlides = getReviewSlides();

        if (remainingSlides.length === 0) {
            const carousel = document.getElementById("reviewCarousel");
            if (carousel) {
                carousel.innerHTML = `<div class="review-empty" id="reviewEmptyState"><p>Você ainda não escreveu nenhuma resenha. Clique em "Nova resenha" para começar.</p></div>`;
            }
            updateCarouselButtons();
            return;
        }

        const nextIndex = Math.min(currentIndex, remainingSlides.length - 1);
        showReviewSlide(nextIndex);
    }
}

async function requestReview(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.erro || "Ocorreu um erro ao processar sua solicitação.");
    }
    return data;
}

async function submitReviewForm(event) {
    event.preventDefault();
    clearReviewError();

    const reviewId = document.getElementById("reviewIdInput").value;
    const filmeTitulo = document.getElementById("filmeTitulo").value.trim();
    const filmeId = document.getElementById("filmeTitulo").getAttribute('data-filme-id') || "";
    const posterUrl = document.getElementById("filmeTitulo").getAttribute('data-poster-url') || "";
    const reviewRating = document.getElementById("reviewRating").value;
    const reviewContent = document.getElementById("reviewContent").value.trim();

    if (!filmeTitulo || !reviewContent) {
        showReviewError("Preencha o título do filme e a resenha.");
        return;
    }

    const payload = {
        filme_titulo: filmeTitulo,
        filme_id: filmeId,
        poster_url: posterUrl,
        conteudo: reviewContent,
        nota: Number(reviewRating || 0),
    };

    try {
        const url = reviewId ? `${REVIEW_API_BASE}/${reviewId}` : REVIEW_API_BASE;
        const method = reviewId ? "PUT" : "POST";
        const result = await requestReview(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        addOrUpdateSlide(result);
        hideReviewModal();
        refreshProfileStatistics();
    } catch (error) {
        showReviewError(error.message);
    }
}

async function deleteReview(event) {
    const reviewId = document.getElementById("reviewIdInput").value;
    if (!reviewId) {
        return;
    }

    try {
        await requestReview(`${REVIEW_API_BASE}/${reviewId}`, { method: "DELETE" });
        removeReviewSlide(reviewId);
        hideReviewModal();
        refreshProfileStatistics();
    } catch (error) {
        showReviewError(error.message);
    }
}

function openEditReview(reviewId) {
    const slide = document.querySelector(`.review-slide[data-review-id='${reviewId}']`);
    if (!slide) {
        return;
    }

    const filmeTitulo = slide.querySelector(".review-film")?.textContent || "";
    const nota = slide.querySelector(".review-rating")?.textContent?.split("/")[0]?.trim() || "0";
    const conteudo = slide.querySelector(".review-slide-text")?.textContent || "";
    const posterUrl = slide.dataset.reviewPosterUrl || "";
    const filmeId = slide.dataset.reviewMovieId || "";

    showReviewModal("edit", {
        id: reviewId,
        filme_titulo: filmeTitulo,
        nota: Number(nota),
        conteudo,
        filme_id: filmeId,
        poster_url: posterUrl,
    });
}

function bindReviewEvents() {
    const openButton = document.getElementById("openReviewModalButton");
    const modal = document.getElementById("reviewModal");
    const reviewForm = document.getElementById("reviewForm");
    const deleteButton = document.getElementById("deleteReviewButton");
    const carousel = document.getElementById("reviewCarousel");

    if (openButton) {
        openButton.addEventListener("click", () => showReviewModal("create"));
    }

    if (modal) {
        modal.addEventListener("click", (event) => {
            if (event.target.closest("[data-review-modal-close]")) {
                hideReviewModal();
            }
        });
    }

    if (reviewForm) {
        reviewForm.addEventListener("submit", submitReviewForm);
    }

    if (deleteButton) {
        deleteButton.addEventListener("click", deleteReview);
    }

    if (carousel) {
        carousel.addEventListener("click", (event) => {
            const editButton = event.target.closest(".review-edit-button");
            if (editButton) {
                openEditReview(editButton.dataset.reviewId);
                return;
            }
        });
    }

    document.querySelectorAll(".review-nav").forEach((button) => {
        button.addEventListener("click", () => {
            const slides = getReviewSlides();
            const currentIndex = getActiveSlideIndex();

            if (button.dataset.direction === "prev") {
                showReviewSlide(Math.max(0, currentIndex - 1));
            } else {
                showReviewSlide(Math.min(slides.length - 1, currentIndex + 1));
            }
        });
    });
}

function initializeReviewCarousel() {
    const slides = getReviewSlides();
    if (slides.length > 0 && getActiveSlideIndex() === -1) {
        slides[0].classList.add("is-active");
    }
    updateCarouselButtons();
}

function parseWishlistMovies(value) {
    if (!value) {
        return [];
    }

    try {
        const parsed = JSON.parse(value);
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        return [];
    }
}

function serializeWishlistMovies(movies) {
    return escapeHtml(JSON.stringify(Array.isArray(movies) ? movies : []));
}

function clampWishlistPage(page, totalMovies) {
    const maxPage = Math.max(Math.ceil(totalMovies / WISHLIST_MOVIES_PER_PAGE) - 1, 0);
    return Math.min(Math.max(Number(page) || 0, 0), maxPage);
}

function getWishlistPageCount(totalMovies) {
    return Math.max(Math.ceil(totalMovies / WISHLIST_MOVIES_PER_PAGE), 1);
}

function createWishlistMovieMarkup(movie, wishlistId) {
    const posterMarkup = movie.posterUrl
        ? `<img src="${escapeHtml(movie.posterUrl)}" alt="Poster de ${escapeHtml(movie.title || "Filme")}" loading="lazy">`
        : `<span>Poster</span>`;

    return `
        <article
            class="wishlist-movie-item"
            data-wishlist-movie-id="${escapeHtml(movie.id)}"
            data-movie-id="${escapeHtml(movie.movieId || "")}"
            data-movie-title="${escapeHtml(movie.title || "Filme")}"
            data-movie-poster-url="${escapeHtml(movie.posterUrl || "")}">
            <div class="wishlist-movie-poster" aria-hidden="true">
                ${posterMarkup}
            </div>
            <div class="wishlist-movie-copy">
                <strong>${escapeHtml(movie.title || "Filme")}</strong>
            </div>
            <button
                class="wishlist-movie-remove"
                type="button"
                data-remove-wishlist-movie
                data-wishlist-id="${escapeHtml(wishlistId)}"
                data-wishlist-movie-id="${escapeHtml(movie.id)}"
                aria-label="Remover ${escapeHtml(movie.title || "filme")} da wishlist">
                remover
            </button>
        </article>
    `;
}

function createWishlistMoviesMarkup(wishlist, requestedPage = 0) {
    const movies = Array.isArray(wishlist.movies) ? wishlist.movies : [];

    if (!movies.length) {
        return `<p class="wishlist-movies-empty">Nenhum filme adicionado ainda. Clique em "Adicionar filme" para comecar.</p>`;
    }

    const safePage = clampWishlistPage(requestedPage, movies.length);
    const pageCount = getWishlistPageCount(movies.length);
    const pageStart = safePage * WISHLIST_MOVIES_PER_PAGE;
    const visibleMovies = movies.slice(pageStart, pageStart + WISHLIST_MOVIES_PER_PAGE);
    const isPrevDisabled = safePage <= 0;
    const isNextDisabled = safePage >= pageCount - 1;
    const paginationHidden = pageCount <= 1 ? " hidden" : "";

    return `
        <div class="wishlist-movie-grid">
            ${visibleMovies.map((movie) => createWishlistMovieMarkup(movie, wishlist.id)).join("")}
        </div>
        <div class="wishlist-movie-pagination"${paginationHidden}>
            <button
                class="wishlist-page-button"
                type="button"
                data-wishlist-page-action="prev"
                data-wishlist-id="${escapeHtml(wishlist.id)}"
                ${isPrevDisabled ? "disabled" : ""}>
                Anterior
            </button>
            <span class="wishlist-page-indicator">${safePage + 1} de ${pageCount}</span>
            <button
                class="wishlist-page-button"
                type="button"
                data-wishlist-page-action="next"
                data-wishlist-id="${escapeHtml(wishlist.id)}"
                ${isNextDisabled ? "disabled" : ""}>
                Proximo
            </button>
        </div>
    `;
}

function createWishlistCardMarkup(wishlist, requestedPage = 0) {
    const description = wishlist.description
        ? escapeHtml(wishlist.description)
        : "Wishlist criada para voce comecar a organizar filmes em uma lista propria.";
    const movies = Array.isArray(wishlist.movies) ? wishlist.movies : [];
    const safePage = clampWishlistPage(requestedPage, movies.length);

    return `
        <article
            class="wishlist-card"
            data-wishlist-id="${escapeHtml(wishlist.id)}"
            data-wishlist-title="${escapeHtml(wishlist.title || "Wishlist")}"
            data-wishlist-description="${escapeHtml(wishlist.description || "")}"
            data-wishlist-is-public="${wishlist.isPublic ? "true" : "false"}"
            data-wishlist-page="${safePage}">
            <div class="wishlist-card-head">
                <span class="card-kicker">Lista</span>
                <span class="wishlist-visibility">${escapeHtml(wishlist.visibilityLabel || (wishlist.isPublic ? "Publica" : "Privada"))}</span>
            </div>
            <h3>${escapeHtml(wishlist.title || "Wishlist")}</h3>
            <p>${description}</p>
            <div class="wishlist-meta">
                <span>${escapeHtml(wishlist.movieCount || 0)} filmes</span>
                <span>Criada em ${escapeHtml(wishlist.createdAtLabel || "hoje")}</span>
            </div>
            <div class="wishlist-card-actions">
                <button
                    class="wishlist-action-button"
                    type="button"
                    data-open-wishlist-movie-modal
                    data-wishlist-id="${escapeHtml(wishlist.id)}"
                    data-wishlist-title="${escapeHtml(wishlist.title || "Wishlist")}">
                    Adicionar filme
                </button>
                <button
                    class="wishlist-action-button wishlist-action-button--ghost"
                    type="button"
                    data-edit-wishlist
                    data-wishlist-id="${escapeHtml(wishlist.id)}">
                    Editar
                </button>
                <button
                    class="wishlist-action-button wishlist-action-button--danger"
                    type="button"
                    data-delete-wishlist
                    data-wishlist-id="${escapeHtml(wishlist.id)}"
                    data-wishlist-title="${escapeHtml(wishlist.title || "Wishlist")}">
                    Excluir
                </button>
            </div>
            <div
                class="wishlist-movie-list"
                data-wishlist-movies="${serializeWishlistMovies(movies)}"
                data-wishlist-page="${safePage}">
                ${createWishlistMoviesMarkup(wishlist, safePage)}
            </div>
        </article>
    `;
}

function getWishlistCardData(card) {
    if (!card) {
        return null;
    }

    return {
        id: card.dataset.wishlistId || "",
        title: card.dataset.wishlistTitle || "Wishlist",
        description: card.dataset.wishlistDescription || "",
        isPublic: card.dataset.wishlistIsPublic === "true",
    };
}

function getWishlistMoviesContainer(card) {
    return card?.querySelector(".wishlist-movie-list") || null;
}

function getWishlistMoviesFromCard(card) {
    const moviesContainer = getWishlistMoviesContainer(card);
    return parseWishlistMovies(moviesContainer?.dataset?.wishlistMovies || "[]");
}

function getWishlistCurrentPage(card) {
    const moviesContainer = getWishlistMoviesContainer(card);
    return clampWishlistPage(
        moviesContainer?.dataset?.wishlistPage ?? card?.dataset?.wishlistPage ?? 0,
        getWishlistMoviesFromCard(card).length
    );
}

function renderWishlistCatalogPage(card, requestedPage) {
    const moviesContainer = getWishlistMoviesContainer(card);
    if (!card || !moviesContainer) {
        return;
    }

    const movies = getWishlistMoviesFromCard(card);
    const safePage = clampWishlistPage(requestedPage, movies.length);
    const wishlistId = card.dataset.wishlistId || "";

    card.dataset.wishlistPage = String(safePage);
    moviesContainer.dataset.wishlistPage = String(safePage);
    moviesContainer.innerHTML = createWishlistMoviesMarkup(
        {
            id: wishlistId,
            movies,
        },
        safePage
    );
}

function showWishlistModal(mode = "create", wishlist = null) {
    const modal = document.getElementById("wishlistModal");
    const form = document.getElementById("wishlistForm");
    const modalTitle = document.getElementById("wishlistModalTitle");
    const wishlistIdInput = document.getElementById("wishlistIdInput");
    const titleField = document.getElementById("wishlistTitle");
    const descriptionField = document.getElementById("wishlistDescription");
    const publicField = document.getElementById("wishlistPublic");
    const errorElement = document.getElementById("wishlistFormError");

    if (!modal || !form || !modalTitle || !wishlistIdInput || !titleField || !descriptionField || !publicField) {
        return;
    }

    form.reset();
    form.dataset.mode = mode;
    wishlistIdInput.value = wishlist?.id || "";
    titleField.value = wishlist?.title || "";
    descriptionField.value = wishlist?.description || "";
    publicField.checked = wishlist ? Boolean(wishlist.isPublic) : true;
    modalTitle.textContent = mode === "edit" ? "Editar wishlist" : "Nova wishlist";

    if (errorElement) {
        errorElement.hidden = true;
        errorElement.textContent = "";
    }

    const submitButton = document.getElementById("wishlistSubmitButton");
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = mode === "edit" ? "Salvar wishlist" : "Criar wishlist";
    }

    modal.hidden = false;
    document.body.style.overflow = "hidden";
    window.setTimeout(() => titleField.focus(), 40);
}

function hideWishlistModal() {
    const modal = document.getElementById("wishlistModal");
    if (!modal) {
        return;
    }

    modal.hidden = true;
    document.body.style.overflow = "";
}

function showWishlistMovieModal(trigger) {
    const modal = document.getElementById("wishlistMovieModal");
    const form = document.getElementById("wishlistMovieForm");
    const titleElement = document.getElementById("wishlistMovieModalTitle");
    const hintElement = document.getElementById("wishlistMovieHint");
    const wishlistIdField = document.getElementById("wishlistMovieWishlistId");
    const movieTitleField = document.getElementById("wishlistMovieTitle");

    if (!modal || !form || !titleElement || !wishlistIdField || !movieTitleField) {
        return;
    }

    const wishlistId = trigger?.dataset?.wishlistId || "";
    const wishlistTitle = trigger?.dataset?.wishlistTitle || "Wishlist";

    if (!wishlistId) {
        return;
    }

    form.reset();
    wishlistIdField.value = wishlistId;
    titleElement.textContent = `Adicionar filme em ${wishlistTitle}`;
    if (hintElement) {
        hintElement.textContent = `Busque um filme para incluir em "${wishlistTitle}".`;
    }

    movieTitleField.value = "";
    movieTitleField.setAttribute("data-filme-id", "");
    movieTitleField.setAttribute("data-poster-url", "");
    clearWishlistMovieError();
    setWishlistMovieSubmitState(false);

    modal.hidden = false;
    document.body.style.overflow = "hidden";

    if (!movieTitleField.hasAttribute("data-autocomplete-init")) {
        initMovieAutocomplete(movieTitleField);
        movieTitleField.setAttribute("data-autocomplete-init", "true");
    }

    window.setTimeout(() => movieTitleField.focus(), 40);
}

function hideWishlistMovieModal() {
    const modal = document.getElementById("wishlistMovieModal");
    if (!modal) {
        return;
    }

    modal.hidden = true;
    document.body.style.overflow = "";
}

function showWishlistError(message) {
    const errorElement = document.getElementById("wishlistFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = message;
    errorElement.hidden = false;
}

function clearWishlistError() {
    const errorElement = document.getElementById("wishlistFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = "";
    errorElement.hidden = true;
}

function showWishlistMovieError(message) {
    const errorElement = document.getElementById("wishlistMovieFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = message;
    errorElement.hidden = false;
}

function clearWishlistMovieError() {
    const errorElement = document.getElementById("wishlistMovieFormError");
    if (!errorElement) {
        return;
    }

    errorElement.textContent = "";
    errorElement.hidden = true;
}

function setWishlistSubmitState(isLoading) {
    const submitButton = document.getElementById("wishlistSubmitButton");
    const form = document.getElementById("wishlistForm");
    const isEditing = form?.dataset?.mode === "edit";
    if (!submitButton) {
        return;
    }

    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading
        ? (isEditing ? "Salvando wishlist..." : "Criando wishlist...")
        : (isEditing ? "Salvar wishlist" : "Criar wishlist");
}

function setWishlistMovieSubmitState(isLoading) {
    const submitButton = document.getElementById("wishlistMovieSubmitButton");
    if (!submitButton) {
        return;
    }

    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading ? "Adicionando filme..." : "Adicionar filme";
}

function addWishlistCard(wishlist) {
    const grid = document.getElementById("wishlistGrid");
    const emptyState = document.getElementById("wishlistEmptyState");
    if (!grid) {
        return;
    }

    if (emptyState) {
        emptyState.remove();
    }

    grid.insertAdjacentHTML("afterbegin", createWishlistCardMarkup(wishlist, 0));
}

function removeWishlistCard(wishlistId) {
    const grid = document.getElementById("wishlistGrid");
    const existingCard = document.querySelector(`.wishlist-card[data-wishlist-id='${wishlistId}']`);

    if (existingCard) {
        existingCard.remove();
    }

    if (!grid || grid.querySelector(".wishlist-card")) {
        return;
    }

    grid.innerHTML = `
        <div class="review-empty wishlist-empty" id="wishlistEmptyState">
            <p>Voce ainda nao criou nenhuma wishlist. Clique em "Nova wishlist" para montar sua primeira lista.</p>
        </div>
    `;
}

function replaceWishlistCard(wishlist, preferredPage = 0) {
    const existingCard = document.querySelector(`.wishlist-card[data-wishlist-id='${wishlist.id}']`);
    if (!existingCard) {
        addWishlistCard(wishlist);
        return;
    }

    existingCard.outerHTML = createWishlistCardMarkup(wishlist, preferredPage);
}

async function parseWishlistResponse(response) {
    const rawBody = await response.text();

    if (!rawBody) {
        return {};
    }

    try {
        return JSON.parse(rawBody);
    } catch (error) {
        if (rawBody.trim().startsWith("<")) {
            throw new Error("O servidor retornou uma resposta invalida. Recarregue a pagina e tente novamente.");
        }

        throw new Error(rawBody);
    }
}

async function requestWishlist(url, options) {
    const response = await fetch(url, options);
    const data = await parseWishlistResponse(response);

    if (!response.ok) {
        throw new Error(data.erro || "Nao foi possivel salvar a wishlist.");
    }

    return data;
}

async function submitWishlistForm(event) {
    event.preventDefault();
    clearWishlistError();
    setWishlistSubmitState(true);

    const wishlistId = document.getElementById("wishlistIdInput")?.value || "";
    const title = document.getElementById("wishlistTitle")?.value.trim() || "";
    const description = document.getElementById("wishlistDescription")?.value.trim() || "";
    const isPublic = Boolean(document.getElementById("wishlistPublic")?.checked);

    if (!title) {
        setWishlistSubmitState(false);
        showWishlistError("Informe um titulo para a wishlist.");
        return;
    }

    try {
        const isEditing = Boolean(wishlistId);
        const existingCard = isEditing
            ? document.querySelector(`.wishlist-card[data-wishlist-id='${wishlistId}']`)
            : null;
        const currentPage = existingCard ? getWishlistCurrentPage(existingCard) : 0;
        const wishlist = await requestWishlist(isEditing ? `${WISHLIST_API_BASE}/${wishlistId}` : WISHLIST_API_BASE, {
            method: isEditing ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title,
                description,
                is_public: isPublic,
            }),
        });

        if (isEditing) {
            replaceWishlistCard(wishlist, currentPage);
        } else {
            addWishlistCard(wishlist);
        }
        hideWishlistModal();
        showRuntimeToast(isEditing ? "Wishlist atualizada com sucesso." : "Wishlist criada com sucesso.");
        refreshProfileStatistics();
    } catch (error) {
        showWishlistError(error.message);
    } finally {
        setWishlistSubmitState(false);
    }
}

async function submitWishlistMovieForm(event) {
    event.preventDefault();
    clearWishlistMovieError();
    setWishlistMovieSubmitState(true);

    const wishlistId = document.getElementById("wishlistMovieWishlistId")?.value || "";
    const movieTitleField = document.getElementById("wishlistMovieTitle");
    const movieTitle = movieTitleField?.value.trim() || "";
    const movieId = movieTitleField?.getAttribute("data-filme-id") || "";
    const posterUrl = movieTitleField?.getAttribute("data-poster-url") || "";

    if (!wishlistId) {
        setWishlistMovieSubmitState(false);
        showWishlistMovieError("Escolha uma wishlist valida para continuar.");
        return;
    }

    if (!movieTitle) {
        setWishlistMovieSubmitState(false);
        showWishlistMovieError("Informe o nome do filme que voce quer adicionar.");
        return;
    }

    try {
        const existingCard = document.querySelector(`.wishlist-card[data-wishlist-id='${wishlistId}']`);
        const currentPage = existingCard ? getWishlistCurrentPage(existingCard) : 0;
        const wishlist = await requestWishlist(`${WISHLIST_API_BASE}/${wishlistId}/movies`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: movieTitle,
                movie_id: movieId,
                poster_url: posterUrl,
            }),
        });

        replaceWishlistCard(wishlist, currentPage);
        hideWishlistMovieModal();
        showRuntimeToast("Filme adicionado na wishlist.");
        refreshProfileStatistics();
    } catch (error) {
        showWishlistMovieError(error.message);
    } finally {
        setWishlistMovieSubmitState(false);
    }
}

async function removeWishlistMovie(button) {
    const wishlistId = button?.dataset?.wishlistId || "";
    const wishlistMovieId = button?.dataset?.wishlistMovieId || "";

    if (!wishlistId || !wishlistMovieId) {
        return;
    }

    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "removendo...";

    try {
        const wishlistCard = button.closest(".wishlist-card");
        const currentPage = wishlistCard ? getWishlistCurrentPage(wishlistCard) : 0;
        const wishlist = await requestWishlist(
            `${WISHLIST_API_BASE}/${wishlistId}/movies/${wishlistMovieId}`,
            { method: "DELETE" }
        );
        replaceWishlistCard(wishlist, currentPage);
        showRuntimeToast("Filme removido da wishlist.");
        refreshProfileStatistics();
    } catch (error) {
        showRuntimeToast(error.message, "error");
        if (button.isConnected) {
            button.disabled = false;
            button.textContent = originalLabel;
        }
    }
}

async function deleteWishlist(button) {
    const wishlistId = button?.dataset?.wishlistId || "";
    const wishlistTitle = button?.dataset?.wishlistTitle || "esta wishlist";

    if (!wishlistId) {
        return;
    }

    const confirmed = window.confirm(`Deseja excluir "${wishlistTitle}"? Os filmes adicionados nela tambem serao removidos.`);
    if (!confirmed) {
        return;
    }

    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "excluindo...";

    try {
        await requestWishlist(`${WISHLIST_API_BASE}/${wishlistId}`, { method: "DELETE" });
        removeWishlistCard(wishlistId);
        showRuntimeToast("Wishlist excluida com sucesso.");
        refreshProfileStatistics();
    } catch (error) {
        showRuntimeToast(error.message, "error");
        if (button.isConnected) {
            button.disabled = false;
            button.textContent = originalLabel;
        }
    }
}

function initializeWishlistCatalogs() {
    document.querySelectorAll(".wishlist-card").forEach((card) => {
        renderWishlistCatalogPage(card, getWishlistCurrentPage(card));
    });
}

function bindWishlistEvents() {
    const openButton = document.getElementById("openWishlistModalButton");
    const wishlistModal = document.getElementById("wishlistModal");
    const wishlistForm = document.getElementById("wishlistForm");
    const wishlistMovieModal = document.getElementById("wishlistMovieModal");
    const wishlistMovieForm = document.getElementById("wishlistMovieForm");

    if (openButton) {
        openButton.addEventListener("click", () => showWishlistModal("create"));
    }

    if (wishlistModal) {
        wishlistModal.addEventListener("click", (event) => {
            if (event.target.closest("[data-wishlist-modal-close]")) {
                hideWishlistModal();
            }
        });
    }

    if (wishlistMovieModal) {
        wishlistMovieModal.addEventListener("click", (event) => {
            if (event.target.closest("[data-wishlist-movie-modal-close]")) {
                hideWishlistMovieModal();
            }
        });
    }

    if (wishlistForm) {
        wishlistForm.addEventListener("submit", submitWishlistForm);
    }

    if (wishlistMovieForm) {
        wishlistMovieForm.addEventListener("submit", submitWishlistMovieForm);
    }

    document.addEventListener("click", (event) => {
        const addMovieButton = event.target.closest("[data-open-wishlist-movie-modal]");
        if (addMovieButton) {
            showWishlistMovieModal(addMovieButton);
            return;
        }

        const pageButton = event.target.closest("[data-wishlist-page-action]");
        if (pageButton) {
            const wishlistCard = pageButton.closest(".wishlist-card");
            if (!wishlistCard) {
                return;
            }

            const direction = pageButton.dataset.wishlistPageAction === "prev" ? -1 : 1;
            const nextPage = getWishlistCurrentPage(wishlistCard) + direction;
            renderWishlistCatalogPage(wishlistCard, nextPage);
            return;
        }

        const editWishlistButton = event.target.closest("[data-edit-wishlist]");
        if (editWishlistButton) {
            const wishlistCard = editWishlistButton.closest(".wishlist-card");
            const wishlist = getWishlistCardData(wishlistCard);
            if (wishlist) {
                showWishlistModal("edit", wishlist);
            }
            return;
        }

        const deleteWishlistButton = event.target.closest("[data-delete-wishlist]");
        if (deleteWishlistButton) {
            deleteWishlist(deleteWishlistButton);
            return;
        }

        const removeMovieButton = event.target.closest("[data-remove-wishlist-movie]");
        if (removeMovieButton) {
            removeWishlistMovie(removeMovieButton);
        }
    });
}

function showPublicMovieModal() {
    const modal = document.getElementById("publicMovieModal");
    if (!modal) {
        return;
    }

    modal.hidden = false;
    document.body.style.overflow = "hidden";
}

function hidePublicMovieModal() {
    const modal = document.getElementById("publicMovieModal");
    if (!modal) {
        return;
    }

    modal.hidden = true;
    document.body.style.overflow = "";
}

function renderPublicMovieModalState(title, description) {
    return `
        <div class="public-detail-state">
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(description)}</p>
        </div>
    `;
}

function renderPublicMovieModalContent(movie, context = {}) {
    const genres = splitItems(movie.genero)
        .slice(0, 4)
        .map((genre) => `<span class="public-detail-chip">${escapeHtml(genre)}</span>`)
        .join("");

    const metaItems = [
        { label: "Ano", value: formatValue(movie.ano) },
        { label: "Duracao", value: formatValue(movie.duracao) },
        { label: "Classificacao", value: formatValue(movie.classificacao) },
        { label: "IMDb", value: formatValue(movie.imdb, "Sem nota") },
    ]
        .map((item) => `<span class="public-detail-chip">${item.label}: ${item.value}</span>`)
        .join("");

    const detailItems = [
        { label: "Direcao", value: formatValue(movie.diretor) },
        { label: "Elenco", value: formatValue(movie.atores) },
        { label: "Roteiro", value: formatValue(movie.roteiro) },
        { label: "Pais", value: formatValue(movie.pais) },
        { label: "Idioma", value: formatValue(movie.idioma) },
    ]
        .map(
            (item) => `
                <div class="public-detail-item">
                    <strong>${item.label}</strong>
                    <span>${item.value}</span>
                </div>
            `
        )
        .join("");

    const contextChips = [
        context.sourceLabel ? `<span class="public-detail-chip">${escapeHtml(context.sourceLabel)}</span>` : "",
        context.rating ? `<span class="public-detail-chip">Nota da review: ${escapeHtml(context.rating)}/5</span>` : "",
        context.createdAtLabel ? `<span class="public-detail-chip">${escapeHtml(context.createdAtLabel)}</span>` : "",
    ]
        .filter(Boolean)
        .join("");

    const reviewExcerpt = context.reviewContent
        ? `
            <div class="public-detail-review-note">
                <strong>Trecho da resenha</strong>
                <p>${escapeHtml(context.reviewContent)}</p>
            </div>
        `
        : "";

    return `
        <div class="public-detail-layout">
            <div class="public-detail-poster-shell">
                ${buildPublicMoviePosterMarkup(movie)}
            </div>

            <div class="public-detail-copy">
                <span class="eyebrow">Ficha do filme</span>
                <h3>${formatValue(movie.titulo, "Filme")}</h3>
                <div class="public-detail-chip-row">
                    ${metaItems}
                    ${contextChips}
                </div>
                <div class="public-detail-chip-row">
                    ${genres || '<span class="public-detail-chip">Genero nao informado</span>'}
                </div>

                <div class="public-detail-grid">
                    ${detailItems}
                </div>

                <div class="public-detail-synopsis">
                    <strong>Sinopse</strong>
                    <p>${formatValue(movie.sinopse, "Sinopse nao disponivel.")}</p>
                </div>

                ${reviewExcerpt}
            </div>
        </div>
    `;
}

async function fetchPublicMovieDetails(movieId, movieTitle) {
    const params = new URLSearchParams();
    if (movieId) {
        params.set("imdb_id", movieId);
    }
    if (movieTitle) {
        params.set("titulo", movieTitle);
    }

    const response = await fetch(`${PUBLIC_MOVIE_DETAILS_API}?${params.toString()}`);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.erro || "Nao foi possivel carregar os detalhes do filme.");
    }

    return data;
}

async function openPublicMovieModal(trigger) {
    const modalTitle = document.getElementById("publicMovieModalTitle");
    const modalContent = document.getElementById("publicMovieModalContent");

    if (!modalTitle || !modalContent) {
        return;
    }

    const movieId = (trigger.dataset.movieId || "").trim();
    const movieTitle = (trigger.dataset.movieTitle || "").trim();
    const context = {
        sourceLabel: trigger.dataset.sourceLabel || "",
        rating: trigger.dataset.rating || "",
        createdAtLabel: trigger.dataset.createdAtLabel || "",
        reviewContent: trigger.dataset.reviewContent || "",
    };

    if (!movieId && !movieTitle) {
        return;
    }

    modalTitle.textContent = movieTitle || "Detalhes do filme";
    modalContent.innerHTML = renderPublicMovieModalState(
        "Carregando detalhes",
        "Estamos buscando a ficha completa do filme para este perfil."
    );
    showPublicMovieModal();

    try {
        const movie = await fetchPublicMovieDetails(movieId, movieTitle);
        modalTitle.textContent = movie.titulo || movieTitle || "Detalhes do filme";
        modalContent.innerHTML = renderPublicMovieModalContent(movie, context);
    } catch (error) {
        modalContent.innerHTML = renderPublicMovieModalState(
            "Nao foi possivel abrir a ficha",
            error.message || "Tente novamente em instantes."
        );
    }
}

function bindPublicProfileMovieModal() {
    const modal = document.getElementById("publicMovieModal");
    if (!modal) {
        return;
    }

    document.addEventListener("click", (event) => {
        if (event.target.closest("[data-public-movie-close]")) {
            hidePublicMovieModal();
            return;
        }

        const trigger = event.target.closest("[data-public-movie-trigger]");
        if (!trigger) {
            return;
        }

        if (event.target.closest("[data-skip-public-movie-trigger]")) {
            return;
        }

        event.preventDefault();
        openPublicMovieModal(trigger);
    });

    document.querySelectorAll(".public-review-item[data-public-movie-trigger]").forEach((item) => {
        item.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") {
                return;
            }

            event.preventDefault();
            openPublicMovieModal(item);
        });
    });
}

function formatStatisticNumber(value) {
    const number = Number(value || 0);
    return number.toLocaleString("pt-BR");
}

function formatStatisticAverage(value, scale = 5) {
    if (value === null || value === undefined) {
        return "Sem nota";
    }

    const number = Number(value);
    if (Number.isNaN(number)) {
        return "Sem nota";
    }

    return `${number.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} / ${scale}`;
}

function pluralizeMovie(count) {
    return Number(count) === 1 ? "filme" : "filmes";
}

function renderStatisticCard(label, value, detail) {
    const detailMarkup = detail ? `<small>${escapeHtml(detail)}</small>` : "";
    return `
        <article class="statistics-card">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
            ${detailMarkup}
        </article>
    `;
}

function renderStatisticBars(items, emptyMessage) {
    if (!Array.isArray(items) || items.length === 0) {
        return `<p class="statistics-empty-note">${escapeHtml(emptyMessage)}</p>`;
    }

    const maxCount = Math.max(...items.map((item) => Number(item.count || 0)), 1);
    return `
        <div class="statistics-bar-list">
            ${items.map((item) => {
                const label = item.genre || item.year || "Nao informado";
                const count = Number(item.count || 0);
                const width = count > 0 ? Math.max(6, Math.round((count / maxCount) * 100)) : 0;
                return `
                    <div class="statistics-bar-item">
                        <div class="statistics-bar-label">
                            <span>${escapeHtml(label)}</span>
                            <span>${formatStatisticNumber(count)} ${pluralizeMovie(count)}</span>
                        </div>
                        <div class="statistics-bar-track" aria-hidden="true">
                            <div class="statistics-bar-fill" style="--bar-width: ${width}%;"></div>
                        </div>
                    </div>
                `;
            }).join("")}
        </div>
    `;
}

function renderRatingHighlights(statistics) {
    const highlights = [
        { label: "Maior nota", movie: statistics.highestRatedMovie },
        { label: "Menor nota", movie: statistics.lowestRatedMovie },
    ].filter((item) => item.movie);

    if (!highlights.length) {
        return '<p class="statistics-empty-note">Ainda nao ha notas suficientes.</p>';
    }

    return `
        <div class="statistics-rating-list">
            ${highlights.map((item) => `
                <div class="statistics-rating-item">
                    <span>${escapeHtml(item.label)}</span>
                    <strong>${escapeHtml(item.movie.title || "Filme")}</strong>
                    <small>${formatStatisticAverage(item.movie.rating, statistics.ratingScale || 5)}</small>
                </div>
            `).join("")}
        </div>
    `;
}

function renderProfileStatistics(statistics) {
    const totalWatched = Number(statistics.totalWatched || 0);
    const totalRatings = Number(statistics.totalRatings || 0);
    const totalLists = Number(statistics.totalLists || 0);
    const totalMoviesInLists = Number(statistics.totalMoviesInLists || 0);
    const ratingDetail = totalRatings
        ? `${formatStatisticNumber(totalRatings)} ${totalRatings === 1 ? "avaliacao" : "avaliacoes"}`
        : "Sem avaliacoes";
    const listDetail = totalMoviesInLists
        ? `${formatStatisticNumber(totalMoviesInLists)} ${pluralizeMovie(totalMoviesInLists)} em listas`
        : "Nenhum filme em listas";

    const summary = `
        <div class="statistics-summary-grid">
            ${renderStatisticCard("Filmes assistidos", formatStatisticNumber(totalWatched), statistics.definitions?.watched)}
            ${renderStatisticCard("Media das notas", formatStatisticAverage(statistics.averageRating, statistics.ratingScale || 5), ratingDetail)}
            ${renderStatisticCard("Resenhas", formatStatisticNumber(statistics.totalReviews || 0), "Publicadas no perfil")}
            ${renderStatisticCard("Listas publicas", formatStatisticNumber(totalLists), listDetail)}
        </div>
    `;

    if (!statistics.hasMovieHistory) {
        return `
            ${summary}
            <p class="statistics-empty-note">Este usuario ainda nao possui estatisticas suficientes.</p>
        `;
    }

    return `
        ${summary}
        <div class="statistics-detail-grid">
            <article class="statistics-panel">
                <h3>Generos mais vistos</h3>
                ${renderStatisticBars(statistics.topGenres, "Ainda nao ha generos suficientes.")}
            </article>
            <article class="statistics-panel">
                <h3>Filmes assistidos por ano</h3>
                ${renderStatisticBars(statistics.watchedByYear, "Ainda nao ha anos suficientes.")}
            </article>
            <article class="statistics-panel statistics-panel--wide">
                <h3>Destaques das notas</h3>
                ${renderRatingHighlights(statistics)}
            </article>
        </div>
    `;
}

function renderProfileStatisticsError(container) {
    container.className = "statistics-state statistics-state--error";
    container.innerHTML = `
        <span class="card-kicker">Erro</span>
        <p>Nao foi possivel carregar as estatisticas.</p>
    `;
}

async function loadProfileStatistics(section) {
    const url = section?.dataset?.statisticsUrl;
    const container = section?.querySelector("[data-statistics-content]");
    if (!url || !container) {
        return;
    }

    try {
        const response = await fetch(url);
        const statistics = await response.json();
        if (!response.ok) {
            throw new Error(statistics.erro || "Falha ao carregar estatisticas.");
        }

        container.className = "statistics-content";
        container.innerHTML = renderProfileStatistics(statistics);
    } catch (error) {
        renderProfileStatisticsError(container);
    }
}

function refreshProfileStatistics() {
    document.querySelectorAll("[data-profile-statistics]").forEach(loadProfileStatistics);
}

// Funções para autocomplete de filmes no modal de review
let movieSuggestionsTimeout = null;
let selectedSuggestionIndex = -1;

async function buscarSugestoesFilmes(query) {
    if (!query || query.length < 2) {
        return [];
    }

    try {
        const response = await fetch(`/sugestoes?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            return [];
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Erro ao buscar sugestões:", error);
        return [];
    }
}

function mostrarSugestoes(sugestoes, inputElement) {
    // Remover sugestões existentes
    const existingDropdown = document.querySelector('.movie-suggestions-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }

    if (!sugestoes || sugestoes.length === 0) {
        selectedSuggestionIndex = -1;
        return;
    }

    // Criar dropdown de sugestões
    const dropdown = document.createElement('div');
    dropdown.className = 'movie-suggestions-dropdown';
    dropdown.style.cssText = 'position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #ddd; border-top: none; border-radius: 0 0 4px 4px; max-height: 200px; overflow-y: auto; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';

    sugestoes.forEach((sugestao, index) => {
        const item = document.createElement('div');
        item.className = 'movie-suggestion-item';
        item.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee; display: flex; align-items: center;';

        const imgHtml = sugestao.poster ? '<img src="' + escapeHtml(sugestao.poster) + '" alt="Poster" style="width: 30px; height: 45px; object-fit: cover; margin-right: 8px;">' : '';
        item.innerHTML = imgHtml + '<div><div style="font-weight: bold;">' + escapeHtml(sugestao.titulo) + '</div><div style="font-size: 0.8em; color: #666;">' + escapeHtml(sugestao.ano || '') + '</div></div>';

        item.addEventListener('click', () => {
            inputElement.value = sugestao.titulo;
            inputElement.setAttribute('data-filme-id', sugestao.imdb_id);
            inputElement.setAttribute('data-poster-url', sugestao.poster || '');
            dropdown.remove();
            selectedSuggestionIndex = -1;
        });

        item.addEventListener('mouseenter', () => {
            selectedSuggestionIndex = index;
            atualizarSelecaoSugestoes(dropdown, index);
        });

        dropdown.appendChild(item);
    });

    // Posicionar dropdown
    const inputRect = inputElement.getBoundingClientRect();
    const modal = inputElement.closest('.review-modal-card');
    if (modal) {
        const modalRect = modal.getBoundingClientRect();
        dropdown.style.left = (inputRect.left - modalRect.left) + 'px';
        dropdown.style.top = (inputRect.bottom - modalRect.top) + 'px';
        dropdown.style.width = inputRect.width + 'px';
        modal.appendChild(dropdown);
    }

    selectedSuggestionIndex = -1;
}

function selecionarSugestaoAtual(inputElement) {
    const dropdown = document.querySelector('.movie-suggestions-dropdown');
    if (!dropdown || selectedSuggestionIndex < 0) {
        return;
    }

    const items = dropdown.querySelectorAll('.movie-suggestion-item');
    const selectedItem = items[selectedSuggestionIndex];
    if (selectedItem) {
        selectedItem.click();
        inputElement.focus();
    }
}

function navegarSugestoes(inputElement, direction) {
    const dropdown = document.querySelector('.movie-suggestions-dropdown');
    if (!dropdown) return;

    const items = dropdown.querySelectorAll('.movie-suggestion-item');
    if (items.length === 0) return;

    selectedSuggestionIndex += direction;
    if (selectedSuggestionIndex < 0) selectedSuggestionIndex = items.length - 1;
    if (selectedSuggestionIndex >= items.length) selectedSuggestionIndex = 0;

    atualizarSelecaoSugestoes(dropdown, selectedSuggestionIndex);
}

function atualizarSelecaoSugestoes(dropdown, index) {
    const items = dropdown.querySelectorAll('.movie-suggestion-item');
    items.forEach((item, i) => {
        item.style.backgroundColor = i === index ? '#f0f0f0' : 'white';
    });
}

function initMovieAutocomplete(inputElement) {
    let currentQuery = '';

    inputElement.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        inputElement.setAttribute('data-filme-id', '');
        inputElement.setAttribute('data-poster-url', '');
        currentQuery = query;

        // Limpar timeout anterior
        if (movieSuggestionsTimeout) {
            clearTimeout(movieSuggestionsTimeout);
        }

        // Remover dropdown se query for muito curta
        if (query.length < 2) {
            const existingDropdown = document.querySelector('.movie-suggestions-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
            }
            selectedSuggestionIndex = -1;
            return;
        }

        // Buscar sugestões com debounce
        movieSuggestionsTimeout = setTimeout(async () => {
            if (currentQuery === query) { // Verificar se ainda é a query atual
                const sugestoes = await buscarSugestoesFilmes(query);
                mostrarSugestoes(sugestoes, inputElement);
            }
        }, 300);
    });

    inputElement.addEventListener('keydown', (e) => {
        const dropdown = document.querySelector('.movie-suggestions-dropdown');

        if (!dropdown) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                navegarSugestoes(inputElement, 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                navegarSugestoes(inputElement, -1);
                break;
            case 'Enter':
                e.preventDefault();
                selecionarSugestaoAtual(inputElement);
                break;
            case 'Escape':
                dropdown.remove();
                selectedSuggestionIndex = -1;
                inputElement.blur();
                break;
        }
    });

    // Fechar dropdown ao clicar fora
    document.addEventListener('click', (e) => {
        if (!inputElement.contains(e.target)) {
            const dropdown = document.querySelector('.movie-suggestions-dropdown');
            if (dropdown) {
                dropdown.remove();
                selectedSuggestionIndex = -1;
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const toast = document.getElementById("toast");
    if (toast) {
        requestAnimationFrame(() => toast.classList.add("show"));
        setTimeout(() => {
            toast.classList.remove("show");
        }, 3200);
    }

    const searchForm = document.getElementById("movieSearchForm");
    if (searchForm) {
        searchForm.addEventListener("submit", (event) => {
            event.preventDefault();
            buscarFilme();
        });
    }

    const movieInput = document.getElementById("movieInput");
    document.querySelectorAll("[data-title]").forEach((button) => {
        button.addEventListener("click", () => {
            if (!movieInput) {
                return;
            }

            movieInput.value = button.dataset.title || "";
            buscarFilme();
        });
    });

    document.querySelectorAll("[data-avatar-editor]").forEach((editor) => {
        initAvatarEditor(editor);
    });

    bindReviewEvents();
    initializeReviewCarousel();
    bindWishlistEvents();
    initializeWishlistCatalogs();
    bindPublicProfileMovieModal();
    refreshProfileStatistics();
});
