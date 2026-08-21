(function () {
    const NOTIFICATIONS_API = "/api/notifications";
    const READ_ALL_API = "/api/notifications/read";

    function escapeNotificationHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function relativeTime(value) {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return "agora";
        }

        const differenceInMinutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
        if (differenceInMinutes < 1) return "agora";
        if (differenceInMinutes < 60) return `há ${differenceInMinutes} min`;
        const differenceInHours = Math.floor(differenceInMinutes / 60);
        if (differenceInHours < 24) return `há ${differenceInHours} h`;
        const differenceInDays = Math.floor(differenceInHours / 24);
        if (differenceInDays < 7) return `há ${differenceInDays} d`;
        return date.toLocaleDateString("pt-BR");
    }

    function updateUnreadCount(root, unreadCount) {
        const count = root.querySelector("[data-notification-count]");
        if (!count) return;
        count.textContent = unreadCount;
        count.hidden = unreadCount <= 0;
    }

    function renderNotifications(root, notifications) {
        const list = root.querySelector("[data-notification-list]");
        if (!list) return;

        if (!notifications.length) {
            list.innerHTML = '<p class="notification-empty">Nenhuma notificação por aqui.</p>';
            return;
        }

        list.innerHTML = notifications.map((notification) => {
            const actor = notification.actor || {};
            const position = actor.avatarPosition || {};
            return `
                <a class="notification-item ${notification.isRead ? "" : "notification-item--unread"}" href="${escapeNotificationHtml(notification.targetUrl || "#")}" data-notification-id="${escapeNotificationHtml(notification.id)}">
                    <img class="notification-item__avatar" src="${escapeNotificationHtml(actor.avatarUrl || "")}" alt="" style="object-position: ${escapeNotificationHtml(position.x || 50)}% ${escapeNotificationHtml(position.y || 50)}%;">
                    <span class="notification-item__copy">
                        <p>${escapeNotificationHtml(notification.message || "Nova interação na sua resenha.")}</p>
                        <time datetime="${escapeNotificationHtml(notification.createdAt || "")}">${escapeNotificationHtml(relativeTime(notification.createdAt))}</time>
                    </span>
                </a>
            `;
        }).join("");
    }

    async function readResponse(response) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.erro || "Não foi possível carregar as notificações.");
        }
        return data;
    }

    async function refreshNotifications(root) {
        const list = root.querySelector("[data-notification-list]");
        const status = root.querySelector("[data-notification-menu-status]");
        if (list) list.innerHTML = '<p class="notification-loading">Carregando notificações...</p>';

        try {
            const response = await fetch(`${NOTIFICATIONS_API}?limit=30`);
            const data = await readResponse(response);
            renderNotifications(root, data.notifications || []);
            updateUnreadCount(root, data.unreadCount || 0);
            if (status) status.textContent = data.unreadCount ? `${data.unreadCount} não lida${data.unreadCount === 1 ? "" : "s"}` : "Tudo em dia";
            return data;
        } catch (error) {
            if (list) list.innerHTML = `<p class="notification-error">${escapeNotificationHtml(error.message)}</p>`;
            if (status) status.textContent = "";
            return null;
        }
    }

    async function markAllAsRead(root) {
        try {
            const response = await fetch(READ_ALL_API, { method: "POST" });
            const data = await readResponse(response);
            updateUnreadCount(root, data.unreadCount || 0);
            root.querySelectorAll(".notification-item--unread").forEach((item) => item.classList.remove("notification-item--unread"));
            const status = root.querySelector("[data-notification-menu-status]");
            if (status) status.textContent = "Tudo em dia";
        } catch (error) {
            // A lista continua disponível mesmo que a leitura não possa ser registrada agora.
        }
    }

    function setupNotifications(root) {
        const trigger = root.querySelector(".notification-trigger");
        const menu = root.querySelector("[data-notification-menu]");
        if (!trigger || !menu) return;

        refreshNotifications(root);

        trigger.addEventListener("click", async () => {
            const willOpen = menu.hidden;
            menu.hidden = !willOpen;
            trigger.setAttribute("aria-expanded", String(willOpen));
            if (!willOpen) return;

            const data = await refreshNotifications(root);
            if (data?.unreadCount) {
                await markAllAsRead(root);
            }
        });

        root.addEventListener("click", async (event) => {
            const notification = event.target.closest("[data-notification-id]");
            if (!notification) return;
            const id = notification.dataset.notificationId;
            if (!id) return;
            try {
                await fetch(`${NOTIFICATIONS_API}/${encodeURIComponent(id)}/read`, { method: "POST" });
            } catch (error) {
                // A navegação para a resenha não deve ser bloqueada por uma falha transitória.
            }
        });

        document.addEventListener("click", (event) => {
            if (!root.contains(event.target) && !menu.hidden) {
                menu.hidden = true;
                trigger.setAttribute("aria-expanded", "false");
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("[data-notifications]").forEach(setupNotifications);
    });
}());
