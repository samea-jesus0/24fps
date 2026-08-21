(function () {
    const REVIEW_INTERACTIONS_API = "/api/reviews";

    function escapeSocialHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatCommentDate(value) {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "agora";
        return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
    }

    async function readInteractionResponse(response) {
        const rawBody = await response.text();
        let data = {};
        try {
            data = rawBody ? JSON.parse(rawBody) : {};
        } catch (error) {
            throw new Error("Não foi possível concluir esta interação. Entre novamente e tente de novo.");
        }

        if (!response.ok) {
            throw new Error(data.erro || "Não foi possível concluir esta interação.");
        }
        return data;
    }

    function getReviewId(card) {
        return (card?.dataset.reviewId || "").trim();
    }

    function updateInteractionSummary(card, payload) {
        if (!payload) return;
        const likeButton = card.querySelector("[data-review-like]");
        const commentCount = card.querySelector("[data-review-comment-count]");

        if (likeButton) {
            const isLiked = Boolean(payload.likedByCurrentUser);
            likeButton.setAttribute("aria-pressed", String(isLiked));
            likeButton.querySelector("[data-review-like-label]").textContent = isLiked ? "Curtido" : "Curtir";
            likeButton.querySelector("[data-review-like-count]").textContent = payload.likeCount || 0;
            likeButton.querySelector("[aria-hidden='true']").textContent = isLiked ? "♥" : "♡";
        }

        if (commentCount) {
            commentCount.textContent = payload.commentCount || 0;
        }
    }

    function renderComments(card, comments, highlightedCommentId = null) {
        const list = card.querySelector("[data-review-comments-list]");
        if (!list) return;

        if (!comments?.length) {
            list.innerHTML = '<p class="review-comments__empty">Ainda não há comentários nesta resenha.</p>';
            return;
        }

        list.innerHTML = comments.map((comment) => {
            const user = comment.user || {};
            const position = user.avatarPosition || {};
            const highlighted = String(comment.id) === String(highlightedCommentId);
            return `
                <article id="comment-${escapeSocialHtml(comment.id)}" class="review-comment-item ${highlighted ? "review-comment-item--highlighted" : ""}">
                    <img class="review-comment-item__avatar" src="${escapeSocialHtml(user.avatarUrl || "")}" alt="" style="object-position: ${escapeSocialHtml(position.x || 50)}% ${escapeSocialHtml(position.y || 50)}%;">
                    <div class="review-comment-item__copy">
                        <strong>${escapeSocialHtml(user.displayName || "Usuário")}</strong>
                        <p>${escapeSocialHtml(comment.content || "")}</p>
                        <time datetime="${escapeSocialHtml(comment.createdAt || "")}">${escapeSocialHtml(formatCommentDate(comment.createdAt))}</time>
                    </div>
                </article>
            `;
        }).join("");
    }

    async function loadInteractions(card, options = {}) {
        const reviewId = getReviewId(card);
        if (!reviewId) return null;
        if (card.dataset.interactionsLoaded === "true" && !options.force) return null;

        const list = card.querySelector("[data-review-comments-list]");
        if (list) list.innerHTML = '<p class="review-comments__loading">Carregando comentários...</p>';

        try {
            const response = await fetch(`${REVIEW_INTERACTIONS_API}/${encodeURIComponent(reviewId)}/interactions`);
            const payload = await readInteractionResponse(response);
            updateInteractionSummary(card, payload);
            renderComments(card, payload.comments, options.highlightedCommentId);
            card.dataset.interactionsLoaded = "true";
            return payload;
        } catch (error) {
            if (list) list.innerHTML = `<p class="review-comments__empty">${escapeSocialHtml(error.message)}</p>`;
            return null;
        }
    }

    function showCommentError(card, message = "") {
        const error = card.querySelector("[data-review-comment-error]");
        if (!error) return;
        error.textContent = message;
        error.hidden = !message;
    }

    async function toggleLike(button) {
        const card = button.closest("[data-review-interactions]");
        const reviewId = getReviewId(card);
        if (!card || !reviewId || button.disabled) return;

        const isLiked = button.getAttribute("aria-pressed") === "true";
        button.disabled = true;
        try {
            const response = await fetch(`${REVIEW_INTERACTIONS_API}/${encodeURIComponent(reviewId)}/likes`, {
                method: isLiked ? "DELETE" : "POST",
            });
            const payload = await readInteractionResponse(response);
            updateInteractionSummary(card, payload);
            card.dataset.interactionsLoaded = "false";
        } catch (error) {
            if (typeof showRuntimeToast === "function") {
                showRuntimeToast(error.message, "error");
            }
        } finally {
            button.disabled = false;
        }
    }

    async function submitComment(form) {
        const card = form.closest("[data-review-interactions]");
        const reviewId = getReviewId(card);
        const textarea = form.querySelector("textarea[name='content']");
        const submitButton = form.querySelector("button[type='submit']");
        const content = textarea?.value.trim() || "";
        if (!card || !reviewId || !textarea || !submitButton) return;

        showCommentError(card);
        if (!content) {
            showCommentError(card, "Escreva um comentário antes de publicar.");
            textarea.focus();
            return;
        }

        submitButton.disabled = true;
        try {
            const response = await fetch(`${REVIEW_INTERACTIONS_API}/${encodeURIComponent(reviewId)}/comments`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content }),
            });
            await readInteractionResponse(response);
            textarea.value = "";
            await loadInteractions(card, { force: true });
        } catch (error) {
            showCommentError(card, error.message);
        } finally {
            submitButton.disabled = false;
        }
    }

    function openTargetedReview() {
        const params = new URLSearchParams(window.location.search);
        const reviewId = params.get("review");
        if (!reviewId) return;

        const card = document.getElementById(`review-${reviewId}`);
        if (!card) return;
        const panel = card.querySelector("[data-review-comments-panel]");
        if (panel) panel.hidden = false;
        card.classList.add("review-comment-item--highlighted");
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        loadInteractions(card, { highlightedCommentId: params.get("comment") });
    }

    function bindReviewInteractions() {
        const cards = document.querySelectorAll("[data-review-interactions]");
        if (!cards.length) return;

        document.addEventListener("click", (event) => {
            const likeButton = event.target.closest("[data-review-like]");
            if (likeButton) {
                event.preventDefault();
                toggleLike(likeButton);
                return;
            }

            const commentsButton = event.target.closest("[data-review-toggle-comments]");
            if (commentsButton) {
                event.preventDefault();
                const card = commentsButton.closest("[data-review-interactions]");
                const panel = card?.querySelector("[data-review-comments-panel]");
                if (!panel) return;
                panel.hidden = !panel.hidden;
                if (!panel.hidden) loadInteractions(card);
            }
        });

        document.addEventListener("submit", (event) => {
            const form = event.target.closest("[data-review-comment-form]");
            if (!form) return;
            event.preventDefault();
            submitComment(form);
        });

        openTargetedReview();
    }

    document.addEventListener("DOMContentLoaded", bindReviewInteractions);
}());
