function escapeRankingHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function rankingMovieUrl(movie) {
    const params = new URLSearchParams();
    params.set("titulo", movie.title || "Filme");
    if (movie.movieId) {
        params.set("imdb_id", movie.movieId);
    }
    return `/pesquisa?${params.toString()}`;
}

function rankingCard(movie, variant, posterFallback) {
    const position = Number(movie.position) || 0;
    const poster = movie.poster || posterFallback;
    const average = Number(movie.averageRating);
    const averageLabel = Number.isFinite(average)
        ? average.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })
        : "—";
    const ratingCount = Number(movie.ratingCount) || 0;
    const year = movie.year ? `<span class="ranking-card-year">${escapeRankingHtml(movie.year)}</span>` : "";
    const genres = Array.isArray(movie.genres)
        ? movie.genres.filter(Boolean).map((genre) => `<li>${escapeRankingHtml(genre)}</li>`).join("")
        : "";
    const className = variant === "podium"
        ? `ranking-card ranking-card--podium ranking-card--${["first", "second", "third"][position - 1] || "other"}`
        : "ranking-card ranking-card--list";

    return `
        <article class="${className}">
            <a class="ranking-card-link" href="${escapeRankingHtml(rankingMovieUrl(movie))}" aria-label="Abrir detalhes de ${escapeRankingHtml(movie.title || "Filme")}">
                <div class="ranking-card-poster">
                    <img src="${escapeRankingHtml(poster)}" alt="Pôster de ${escapeRankingHtml(movie.title || "Filme")}" loading="lazy" onerror="this.onerror=null;this.src='${escapeRankingHtml(posterFallback)}'">
                    <span class="ranking-position">${position}º</span>
                </div>
                <div class="ranking-card-copy">
                    ${year}
                    <h3>${escapeRankingHtml(movie.title || "Filme sem título")}</h3>
                    <div class="ranking-card-metrics">
                        <span class="ranking-rating">${averageLabel} ★</span>
                        <span class="ranking-count">${ratingCount} ${ratingCount === 1 ? "avaliação" : "avaliações"}</span>
                    </div>
                    ${genres ? `<ul class="ranking-genres" aria-label="Gêneros">${genres}</ul>` : ""}
                </div>
            </a>
        </article>
    `;
}

function setRankingState(element, type, title, message) {
    element.hidden = false;
    element.className = `ranking-state ranking-state--${type}`;
    element.innerHTML = `<strong>${escapeRankingHtml(title)}</strong><span>${escapeRankingHtml(message)}</span>`;
}

async function loadMovieRanking() {
    const state = document.querySelector("[data-ranking-state]");
    const podium = document.querySelector("[data-ranking-podium]");
    const list = document.querySelector("[data-ranking-list]");
    const restSection = document.querySelector("[data-ranking-rest-section]");
    const note = document.querySelector("[data-ranking-note]");
    if (!state || !podium || !list || !restSection || !note) return;

    try {
        const response = await fetch("/api/ranking", { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error("A API retornou uma resposta indisponível.");
        const payload = await response.json();
        const ranking = Array.isArray(payload.ranking) ? payload.ranking.slice(0, 5) : [];

        if (!ranking.length) {
            setRankingState(
                state,
                "empty",
                "Ainda não há filmes no ranking.",
                `Cada filme precisa de pelo menos ${Number(payload.minimumRatings) || 5} avaliações de pessoas diferentes.`,
            );
            return;
        }

        state.hidden = true;
        const posterFallback = podium.dataset.posterFallback;
        podium.innerHTML = ranking
            .slice(0, 3)
            .map((movie) => rankingCard(movie, "podium", posterFallback))
            .join("");
        list.innerHTML = ranking
            .slice(3)
            .map((movie) => `<li>${rankingCard(movie, "list", posterFallback)}</li>`)
            .join("");
        restSection.hidden = ranking.length <= 3;

        if (ranking.length < 5) {
            note.hidden = false;
            note.textContent = `Mostrando ${ranking.length} ${ranking.length === 1 ? "filme elegível" : "filmes elegíveis"}. O ranking não completa posições sem avaliações suficientes.`;
        }
    } catch (error) {
        setRankingState(
            state,
            "error",
            "Não foi possível carregar o ranking.",
            "Tente atualizar a página em instantes.",
        );
    }
}

document.addEventListener("DOMContentLoaded", loadMovieRanking);
