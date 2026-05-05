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

    return '<article class="review-slide is-active" data-review-id="' + escapeHtml(review.id) + '">' +
           '<div class="review-slide-copy">' +
           posterHtml +
           '<div class="review-slide-top">' +
           '<span class="review-film">' + escapeHtml(review.filme_titulo) + '</span>' +
           '<span class="review-rating">' + escapeHtml(review.nota || 0) + '/5</span>' +
           '</div>' +
           '<p class="review-slide-text">' + escapeHtml(review.conteudo || '').replace(/\n/g, "<br>") + '</p>' +
           '<div class="review-slide-footer">' +
           '<span class="review-date">Atualizado em hoje</span>' +
           '<button class="review-edit-button" type="button" data-review-id="' + escapeHtml(review.id) + '">Editar</button>' +
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
    const posterImg = slide.querySelector(".review-poster img");
    const posterUrl = posterImg ? posterImg.src : "";

    showReviewModal("edit", {
        id: reviewId,
        filme_titulo: filmeTitulo,
        nota: Number(nota),
        conteudo,
        filme_id: "",
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
});
