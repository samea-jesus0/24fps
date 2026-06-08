async function buscarFilme() {
    const nome = document.getElementById("movieInput").value;
    const toast = document.getElementById("toast");

      // Mostra
      setTimeout(() => {
        toast.classList.add("show");
      }, 100);

      // Esconde depois de 3 segundos
      setTimeout(() => {
        toast.classList.remove("show");
      }, 3000);

    resultado.innerHTML = "<p>Carregando...</p>";
    const resultado = document.getElementById("resultado");

    try {
        const response = await fetch("/buscar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ nome: nome })
        });

        const data = await response.json();

        if (!response.ok) {
            resultado.innerHTML = `<p class="erro">${data.erro}</p>`;
            return;
        }

        resultado.innerHTML = `
            <div class="card">
                <img src="${data.poster}" alt="Poster do filme">
                <div class="info">
                    <h2>${data.titulo}</h2>
                    <p><strong>Ano:</strong> ${data.ano}</p>
                    <p><strong>Gênero:</strong> ${data.genero}</p>
                    <p><strong>Diretor:</strong> ${data.diretor}</p>
                    <p><strong>Atores:</strong> ${data.atores}</p>
                    <p><strong>IMDb:</strong> ${data.imdb}</p>
                    <p><strong>Sinopse:</strong> ${data.sinopse}</p>
                </div>
            </div>
        `;
    } catch (error) {
        resultado.innerHTML = `<p class="erro">Erro ao buscar o filme.</p>`;
    }
}

function hydrateMovieSearchFromUrl() {
    const input = document.getElementById("movieInput");
    const params = new URLSearchParams(window.location.search);
    const filme = params.get("filme");

    if (!input || !filme) {
        return;
    }

    input.value = filme;
    buscarFilme();
}

function renderUserSearchLoading(container) {
    container.innerHTML = `
        <div class="user-search-note">
            <span>buscando usuarios...</span>
        </div>
    `;
}

function renderUserSearchResults(container, users, query) {
    if (!users || users.length === 0) {
        container.innerHTML = `
            <div class="user-search-note">
                <span>Nenhum usuario encontrado para "${escapeHtml(query)}".</span>
            </div>
        `;
        return;
    }

    container.innerHTML = users.map((user) => `
        <a class="user-result-card" href="${escapeHtml(user.profileUrl)}">
            <img src="${escapeHtml(user.avatarUrl)}" alt="Foto de perfil de ${escapeHtml(user.displayName)}" loading="lazy">
            <div>
                <strong>${escapeHtml(user.displayName)}</strong>
                <span>${escapeHtml(user.bio || user.username || "Perfil publico 24FPS")}</span>
            </div>
        </a>
    `).join("");
}

async function buscarUsuarios() {
    const input = document.getElementById("userSearchInput");
    const results = document.getElementById("userSearchResults");

    if (!input || !results) {
        return;
    }

    const query = input.value.trim();
    if (query.length < 2) {
        results.innerHTML = `
            <div class="user-search-note">
                <span>Digite pelo menos 2 caracteres para procurar usuarios.</span>
            </div>
        `;
        input.focus();
        return;
    }

    renderUserSearchLoading(results);

    try {
        const response = await fetch(`/api/users?search=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.erro || "Nao foi possivel buscar usuarios.");
        }

        renderUserSearchResults(results, data.users || [], query);
    } catch (error) {
        results.innerHTML = `
            <div class="user-search-note user-search-note--error">
                <span>${escapeHtml(error.message || "Erro ao buscar usuarios.")}</span>
            </div>
        `;
    }
}

function redirecionar_login() {
    window.open("/login", "_blank");
}

function redirecionar_perfil() {
    window.open("/perfil");
}

function previewImage(event) {
    const input = event.target;
    const preview = document.getElementById('preview');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
        }

        reader.readAsDataURL(input.files[0]);
    }
<<<<<<< Updated upstream
}
=======
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

    hydrateMovieSearchFromUrl();

    const userSearchForm = document.getElementById("userSearchForm");
    if (userSearchForm) {
        userSearchForm.addEventListener("submit", (event) => {
            event.preventDefault();
            buscarUsuarios();
        });
    }

    document.querySelectorAll("[data-avatar-editor]").forEach((editor) => {
        initAvatarEditor(editor);
    });

    bindReviewEvents();
    initializeReviewCarousel();
});
>>>>>>> Stashed changes
