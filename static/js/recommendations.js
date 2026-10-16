(function () {
    const container = document.querySelector("[data-recommendations]");
    const refreshButton = document.querySelector("[data-recommendations-refresh]");

    if (!container) {
        return;
    }

    let rotation = 0;

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function renderMovie(movie) {
        const genres = (movie.genres || [])
            .slice(0, 3)
            .map((genre) => `<span class="recommendation-genre">${escapeHtml(genre)}</span>`)
            .join("");
        const poster = movie.poster
            ? `<img src="${escapeHtml(movie.poster)}" alt="Pôster de ${escapeHtml(movie.title)}" loading="lazy">`
            : '<div class="recommendation-poster-placeholder">Pôster indisponível</div>';
        const synopsis = movie.synopsis || "Sinopse indisponível.";
        const rating = movie.rating ? `IMDb ${escapeHtml(movie.rating)}` : "Nota indisponível";

        return `
            <article class="recommendation-card">
                <div class="recommendation-poster">${poster}</div>
                <div class="recommendation-copy">
                    <div class="recommendation-meta">${genres}</div>
                    <h3>${escapeHtml(movie.title)}</h3>
                    <span class="recommendation-rating">${rating}</span>
                    <p>${escapeHtml(synopsis)}</p>
                    <small>${escapeHtml(movie.reason)}</small>
                </div>
            </article>
        `;
    }

    async function loadRecommendations(rotate = false) {
        if (rotate) {
            rotation += 1;
        }
        container.innerHTML = '<p class="recommendation-state">Buscando sugestões para o seu perfil...</p>';
        if (refreshButton) {
            refreshButton.disabled = true;
        }

        try {
            const response = await fetch(`/api/recommendations?rotation=${rotation}`, {
                cache: "no-store",
                headers: { Accept: "application/json" },
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.erro || "Não foi possível carregar as recomendações.");
            }

            const recommendations = data.recommendations || [];
            container.innerHTML = recommendations.length
                ? recommendations.map(renderMovie).join("")
                : '<p class="recommendation-state">Ainda não encontramos sugestões. Avalie filmes ou adicione títulos à sua wishlist para personalizar esta seleção.</p>';
        } catch (error) {
            container.innerHTML = `<p class="recommendation-state recommendation-state--error">${escapeHtml(error.message || "Não foi possível carregar as recomendações agora.")}</p>`;
        } finally {
            if (refreshButton) {
                refreshButton.disabled = false;
            }
        }
    }

    if (refreshButton) {
        refreshButton.addEventListener("click", () => loadRecommendations(true));
    }
    loadRecommendations();
})();
