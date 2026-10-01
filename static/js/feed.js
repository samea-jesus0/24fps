(() => {
    const list = document.querySelector("[data-feed-list]");
    const state = document.querySelector("[data-feed-state]");
    const refreshButton = document.querySelector("[data-feed-refresh]");

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatDate(value) {
        if (!value) return "Data não informada";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "Data não informada";
        return new Intl.DateTimeFormat("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        }).format(date);
    }

    function activityIcon(type) {
        return {
            rating: "★",
            review: "✎",
            wishlist_movie: "＋"
        }[type] || "•";
    }

    function renderActivity(activity) {
        const actor = activity.actor || {};
        const avatar = actor.avatarUrl || "/static/uploads/default-avatar.svg";
        const profileUrl = actor.profileUrl || "#";
        const movieUrl = activity.movieUrl || "#";

        let detail = "";
        if (activity.type === "rating") {
            detail = `<span class="feed-rating">${"★".repeat(Math.max(0, Number(activity.rating) || 0))}${"☆".repeat(Math.max(0, 5 - (Number(activity.rating) || 0)))}</span>`;
        } else if (activity.type === "review") {
            detail = activity.reviewUrl
                ? `<a class="feed-action-link" href="${escapeHtml(activity.reviewUrl)}">ver resenha</a>`
                : "";
        } else if (activity.type === "wishlist_movie") {
            detail = `<span class="feed-list-name">"${escapeHtml(activity.wishlistTitle || "Lista")}"</span>`;
        }

        return `
            <article class="feed-item">
                <a class="feed-avatar" href="${escapeHtml(profileUrl)}" aria-label="Perfil de ${escapeHtml(actor.displayName || "usuario")}">
                    <img src="${escapeHtml(avatar)}" alt="Avatar de ${escapeHtml(actor.displayName || "usuario")}" loading="lazy">
                </a>
                <div class="feed-item-main">
                    <div class="feed-item-top">
                        <span class="feed-type-icon" aria-hidden="true">${activityIcon(activity.type)}</span>
                        <time datetime="${escapeHtml(activity.timestamp || "")}">${escapeHtml(formatDate(activity.timestamp))}</time>
                    </div>
                    <p class="feed-item-text">${escapeHtml(activity.text || "")}</p>
                    <div class="feed-item-meta">
                        <a href="${escapeHtml(movieUrl)}">${escapeHtml(activity.movieTitle || "Filme")}</a>
                        ${detail}
                    </div>
                </div>
                ${activity.posterUrl ? `<a class="feed-poster" href="${escapeHtml(movieUrl)}"><img src="${escapeHtml(activity.posterUrl)}" alt="Pôster de ${escapeHtml(activity.movieTitle || "filme")}" loading="lazy"></a>` : ""}
            </article>
        `;
    }

    function showState(title, description) {
        if (!state) return;
        state.hidden = false;
        state.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(description)}</span>`;
    }

    async function loadFeed() {
        if (!list) return;
        list.innerHTML = "";
        showState("Carregando atividades...", "Buscando as novidades das pessoas que você segue.");
        if (refreshButton) refreshButton.disabled = true;

        try {
            const response = await fetch("/api/feed", {
                headers: { "Accept": "application/json" }
            });
            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.erro || "Não foi possível carregar o feed.");
            }

            const activities = payload.activities || [];
            if (!activities.length) {
                showState(
                    "Seu feed está vazio.",
                    "Siga outras pessoas na Plateia para acompanhar avaliações, resenhas e listas públicas."
                );
                return;
            }

            state.hidden = true;
            list.innerHTML = activities.map(renderActivity).join("");
        } catch (error) {
            showState("Não foi possível carregar o feed.", error.message || "Tente novamente.");
        } finally {
            if (refreshButton) refreshButton.disabled = false;
        }
    }

    refreshButton?.addEventListener("click", loadFeed);
    loadFeed();
})();
