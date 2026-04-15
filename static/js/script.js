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
});
