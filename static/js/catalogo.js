function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function truncateText(text, maxLength = 150) {
    const safeText = String(text || "");
    return safeText.length <= maxLength ? safeText : `${safeText.slice(0, maxLength).trim()}...`;
}

function renderPoster(movie) {
    if (movie.poster) {
        return `<img class="movie-poster" src="${escapeHtml(movie.poster)}" alt="Poster de ${escapeHtml(movie.titulo)}" loading="lazy">`;
    }

    return `<div class="movie-poster-placeholder">Poster nao disponivel</div>`;
}

function renderMovieCard(movie) {
    const genreTags = (movie.generos || [])
        .slice(0, 3)
        .map((genre) => `<span class="tag">${escapeHtml(genre)}</span>`)
        .join("");

    return `
        <article class="movie-card">
            <div class="movie-poster-wrap">
                ${renderPoster(movie)}
            </div>

            <div class="movie-body">
                <div>
                    <h4 class="movie-title">${escapeHtml(movie.titulo || "Filme")}</h4>
                    <p class="movie-subtitle">${escapeHtml(movie.ano_label || "Ano nao informado")} | ${escapeHtml(movie.duracao || "Duracao nao informada")}</p>
                </div>

                <div class="movie-tags">
                    ${genreTags || '<span class="tag">Genero nao informado</span>'}
                </div>

                <div class="movie-extra">
                    <span class="extra-pill">IMDb ${escapeHtml(movie.imdb || "N/A")}</span>
                    <span class="extra-pill">${escapeHtml(movie.classificacao || "Nao informado")}</span>
                    <span class="extra-pill">${escapeHtml(movie.pais || "Pais nao informado")}</span>
                </div>

                <p class="movie-description">${escapeHtml(truncateText(movie.sinopse || "Sinopse nao disponivel.", 170))}</p>

                <div class="movie-extra">
                    <span class="extra-pill">Direcao: ${escapeHtml(movie.diretor || "Nao informado")}</span>
                </div>
            </div>
        </article>
    `;
}

function renderSection(section) {
    return `
        <section class="catalog-section" data-section-slug="${escapeHtml(section.slug)}">
            <div class="section-head">
                <div class="section-copy">
                    <span class="section-kicker">genero</span>
                    <h3>${escapeHtml(section.title)}</h3>
                    <p>${escapeHtml(section.description || "")}</p>
                    <div class="section-meta">
                        <span class="meta-pill">${section.movie_count} exibidos agora</span>
                        <span class="meta-pill">${escapeHtml(section.results_label || `${section.total_filtered_movies} encontrados neste genero`)}</span>
                    </div>
                </div>

                <aside class="section-note">
                    <span class="note-kicker">porque ver</span>
                    <p>${escapeHtml(section.note || "Um genero para mudar o ritmo da sessao e descobrir novos filmes.")}</p>
                </aside>
            </div>

            <div class="movie-grid">
                ${(section.movies || []).map(renderMovieCard).join("")}
            </div>

            ${section.has_more ? `
                <div class="section-footer">
                    <button
                        type="button"
                        class="action-btn"
                        data-load-more="${escapeHtml(section.slug)}"
                        data-next-page="${Number(section.current_page || 1) + 1}">
                        carregar mais filmes de ${escapeHtml(section.title.toLowerCase())}
                    </button>
                </div>
            ` : ""}
        </section>
    `;
}

function renderGlobalLoadMore(sections) {
    const expandableSections = (sections || []).filter((section) => section.has_more);
    if (!expandableSections.length) {
        return "";
    }

    const sectionSlugs = expandableSections.map((section) => section.slug).join(",");

    return `
        <div class="catalog-footer">
            <button
                type="button"
                class="action-btn action-btn--primary"
                data-load-more-all="${escapeHtml(sectionSlugs)}">
                carregar mais filmes
            </button>
        </div>
    `;
}

function renderCatalogSections(sections) {
    return `${(sections || []).map(renderSection).join("")}${renderGlobalLoadMore(sections)}`;
}

function updateCatalogFooter(sectionsContainer, sections) {
    const currentFooter = sectionsContainer.querySelector(".catalog-footer");
    if (currentFooter) {
        currentFooter.remove();
    }

    sectionsContainer.insertAdjacentHTML("beforeend", renderGlobalLoadMore(sections));
}

function buildLoadingMarkup() {
    return `
        <div class="loading-state">
            <span class="loading-badge">carregando catalogo</span>
            <div class="loading-grid">
                <div class="loading-card"></div>
                <div class="loading-card"></div>
                <div class="loading-card"></div>
            </div>
        </div>
    `;
}

function renderEmptyState() {
    return `
        <div class="empty-state">
            <span class="loading-badge">nenhum resultado</span>
            <h3>Nenhum filme combinou com os filtros atuais.</h3>
            <p>Tente limpar alguns filtros, mudar o genero em destaque ou ampliar o intervalo de anos.</p>
        </div>
    `;
}

function renderErrorState(message) {
    return `
        <div class="error-state">
            <span class="loading-badge">erro</span>
            <h3>Nao deu para carregar o catalogo agora.</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

function createOptionMarkup(options, placeholder, includeEmptyOption = true) {
    const items = [];
    if (includeEmptyOption) {
        items.push(`<option value="">${escapeHtml(placeholder)}</option>`);
    }

    (options || []).forEach((option) => {
        if (typeof option === "string") {
            items.push(`<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`);
        } else {
            items.push(`<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`);
        }
    });

    return items.join("");
}

function populateDynamicFilters(form, options) {
    const configs = {
        categories: { placeholder: "Todos os generos", includeEmptyOption: false },
        countries: { placeholder: "Todos os paises" },
        duration_buckets: { placeholder: "Qualquer duracao" },
        classifications: { placeholder: "Qualquer classificacao" },
        languages: { placeholder: "Todos os idiomas" },
        sort_options: { placeholder: "Ordem recomendada", includeEmptyOption: false },
    };

    form.querySelectorAll("[data-dynamic-options]").forEach((select) => {
        const key = select.dataset.dynamicOptions;
        const config = configs[key] || { placeholder: "Selecione" };
        const previousValue = select.value;
        select.innerHTML = createOptionMarkup(options[key], config.placeholder, config.includeEmptyOption !== false);
        select.value = previousValue || (key === "categories" ? "all" : key === "sort_options" ? "featured" : "");
    });

    const yearMinInput = form.elements.namedItem("year_min");
    const yearMaxInput = form.elements.namedItem("year_max");
    const bounds = options.year_bounds || {};

    if (yearMinInput && bounds.min) {
        yearMinInput.min = bounds.min;
        yearMinInput.max = bounds.max || "";
        yearMinInput.placeholder = String(bounds.min);
    }

    if (yearMaxInput && bounds.max) {
        yearMaxInput.min = bounds.min || "";
        yearMaxInput.max = bounds.max;
        yearMaxInput.placeholder = String(bounds.max);
    }
}

function syncFormWithFilters(form, filters) {
    Object.entries(filters || {}).forEach(([key, value]) => {
        const field = form.elements.namedItem(key);
        if (field) {
            field.value = value == null ? "" : String(value);
        }
    });
}

function serializeForm(form) {
    const params = new URLSearchParams();
    const formData = new FormData(form);

    for (const [key, value] of formData.entries()) {
        const normalized = String(value).trim();
        if (!normalized || normalized === "all" || (key === "sort" && normalized === "featured")) {
            continue;
        }
        params.set(key, normalized);
    }

    return params;
}

const catalogState = {
    sectionPages: {},
    abortController: null,
};

function resetSectionPages() {
    catalogState.sectionPages = {};
}

function buildCatalogParams(form) {
    const params = serializeForm(form);

    Object.entries(catalogState.sectionPages).forEach(([slug, page]) => {
        if (page > 1) {
            params.set(`section_page_${slug}`, String(page));
        }
    });

    return params;
}

function updateStats(payload) {
    document.querySelector("[data-stat-visible-movies]").textContent = payload.stats.visible_movies;
    document.querySelector("[data-stat-sections]").textContent = payload.stats.visible_sections;
    document.querySelector("[data-stat-available]").textContent = payload.stats.available_movies;
}

function findOptionLabel(options, key, value) {
    if (!value) {
        return "";
    }

    const collection = options[key] || [];
    const found = collection.find((item) => (typeof item === "string" ? item === value : item.value === value));
    return !found ? value : (typeof found === "string" ? found : found.label);
}

function updateFeedback(payload) {
    const title = document.querySelector("[data-feedback-title]");
    const text = document.querySelector("[data-feedback-text]");
    const chips = document.querySelector("[data-active-filters]");
    const filters = payload.applied_filters || {};
    const options = payload.options || {};

    title.textContent = `${payload.stats.visible_movies} filmes em ${payload.stats.visible_sections} generos`;
    text.textContent = "Os resultados abaixo refletem sua selecao atual e continuam organizados por genero.";

    const activeFilters = [];
    if (filters.search) activeFilters.push(`Busca: ${filters.search}`);
    if (filters.category && filters.category !== "all") activeFilters.push(`Genero foco: ${findOptionLabel(options, "categories", filters.category)}`);
    if (filters.year_min) activeFilters.push(`Ano min: ${filters.year_min}`);
    if (filters.year_max) activeFilters.push(`Ano max: ${filters.year_max}`);
    if (filters.country) activeFilters.push(`Pais: ${filters.country}`);
    if (filters.duration) activeFilters.push(`Duracao: ${findOptionLabel(options, "duration_buckets", filters.duration)}`);
    if (filters.classification) activeFilters.push(`Classificacao: ${filters.classification}`);
    if (filters.language) activeFilters.push(`Idioma: ${filters.language}`);
    if (filters.sort && filters.sort !== "featured") activeFilters.push(`Ordenacao: ${findOptionLabel(options, "sort_options", filters.sort)}`);

    chips.innerHTML = activeFilters.map((label) => `<span class="filter-chip">${escapeHtml(label)}</span>`).join("");
}

function setLoadMoreButtonState(button, isLoading) {
    if (!button) {
        return;
    }

    if (isLoading) {
        button.dataset.originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = "carregando...";
        return;
    }

    button.disabled = false;
    button.textContent = button.dataset.originalLabel || button.textContent;
    delete button.dataset.originalLabel;
}

function updatePartialSection(sectionsContainer, sections, partialSectionSlug) {
    const nextSection = (sections || []).find((section) => section.slug === partialSectionSlug);
    const currentSection = sectionsContainer.querySelector(`[data-section-slug="${partialSectionSlug}"]`);

    if (nextSection && currentSection) {
        currentSection.outerHTML = renderSection(nextSection);
    } else if (nextSection) {
        sectionsContainer.insertAdjacentHTML("beforeend", renderSection(nextSection));
    } else if (currentSection) {
        currentSection.remove();
    }

    const remainingSections = sectionsContainer.querySelectorAll(".catalog-section");
    if (!remainingSections.length) {
        sectionsContainer.innerHTML = renderEmptyState();
        return;
    }

    updateCatalogFooter(sectionsContainer, sections);
}

async function loadCatalog(options = {}) {
    const { partialSectionSlug = null } = options;
    const form = document.getElementById("catalogForm");
    const sectionsContainer = document.getElementById("catalogSections");

    if (!partialSectionSlug) {
        sectionsContainer.innerHTML = buildLoadingMarkup();
    }

    if (catalogState.abortController) {
        catalogState.abortController.abort();
    }

    const controller = new AbortController();
    catalogState.abortController = controller;
    const response = await fetch(`/api/catalogo?${buildCatalogParams(form).toString()}`, { signal: controller.signal });
    const payload = await response.json();

    populateDynamicFilters(form, payload.options || {});
    syncFormWithFilters(form, payload.applied_filters || {});
    catalogState.sectionPages = payload.section_pages || {};
    updateStats(payload);

    if (!response.ok || payload.error) {
        document.querySelector("[data-feedback-title]").textContent = "Nao foi possivel carregar o catalogo.";
        document.querySelector("[data-feedback-text]").textContent = payload.error || "Tente novamente em instantes.";
        document.querySelector("[data-active-filters]").innerHTML = "";

        if (!partialSectionSlug) {
            sectionsContainer.innerHTML = renderErrorState(payload.error || "Falha na comunicacao com a API.");
        }
        return;
    }

    updateFeedback(payload);

    if (!payload.sections || payload.sections.length === 0) {
        sectionsContainer.innerHTML = renderEmptyState();
        return;
    }

    if (partialSectionSlug) {
        updatePartialSection(sectionsContainer, payload.sections, partialSectionSlug);
        return;
    }

    sectionsContainer.innerHTML = renderCatalogSections(payload.sections);
}

function debounce(callback, wait) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = window.setTimeout(() => callback(...args), wait);
    };
}

function handleLoadError(message) {
    document.getElementById("catalogSections").innerHTML = renderErrorState(message);
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("catalogForm");
    const clearButton = document.getElementById("clearFiltersBtn");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        resetSectionPages();
        await loadCatalog();
    });

    const debouncedLoad = debounce(() => {
        resetSectionPages();
        loadCatalog().catch((error) => {
            if (error.name !== "AbortError") {
                handleLoadError("Falha ao atualizar filtros.");
            }
        });
    }, 350);

    form.querySelectorAll("select").forEach((select) => {
        select.addEventListener("change", () => {
            resetSectionPages();
            loadCatalog().catch((error) => {
                if (error.name !== "AbortError") {
                    handleLoadError("Falha ao atualizar filtros.");
                }
            });
        });
    });

    form.querySelectorAll('input[type="search"], input[type="number"]').forEach((input) => {
        input.addEventListener("input", debouncedLoad);
    });

    clearButton.addEventListener("click", () => {
        form.reset();
        resetSectionPages();
        const categoryField = form.elements.namedItem("category");
        const sortField = form.elements.namedItem("sort");
        if (categoryField) categoryField.value = "all";
        if (sortField) sortField.value = "featured";
        loadCatalog().catch((error) => {
            if (error.name !== "AbortError") {
                handleLoadError("Falha ao limpar filtros.");
            }
        });
    });

    document.addEventListener("click", (event) => {
        const globalButton = event.target.closest("[data-load-more-all]");
        if (globalButton) {
            const slugs = (globalButton.dataset.loadMoreAll || "")
                .split(",")
                .map((slug) => slug.trim())
                .filter(Boolean);

            slugs.forEach((slug) => {
                catalogState.sectionPages[slug] = (catalogState.sectionPages[slug] || 1) + 1;
            });

            loadCatalog().catch((error) => {
                if (error.name !== "AbortError") {
                    handleLoadError("Falha ao carregar mais filmes.");
                }
            });
            return;
        }

        const button = event.target.closest("[data-load-more]");
        if (!button) {
            return;
        }

        const slug = button.dataset.loadMore;
        const nextPage = Number(button.dataset.nextPage || "2");
        catalogState.sectionPages[slug] = nextPage;
        setLoadMoreButtonState(button, true);
        loadCatalog({ partialSectionSlug: slug }).catch((error) => {
            if (error.name !== "AbortError") {
                handleLoadError("Falha ao carregar mais filmes neste genero.");
            }
        }).finally(() => {
            setLoadMoreButtonState(button, false);
        });
    });

    loadCatalog().catch((error) => {
        if (error.name !== "AbortError") {
            handleLoadError("Falha ao carregar o catalogo inicial.");
        }
    });
});
