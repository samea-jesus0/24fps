(function () {
    function redirectToLogin() {
        window.location.href = '/login';
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function setFollowButtonState(button, isFollowing, labelText) {
        if (!button) {
            return;
        }

        button.dataset.isFollowing = String(Boolean(isFollowing));
        button.classList.toggle('is-following', Boolean(isFollowing));
        button.textContent = labelText || (isFollowing ? 'Seguindo' : 'Seguir');
        button.setAttribute('aria-pressed', String(Boolean(isFollowing)));
    }

    function getFollowStatusValues(targetId) {
        const button = document.querySelector(`[data-follow-toggle][data-user-id="${CSS.escape(String(targetId))}"]`);
        if (!button) {
            return null;
        }
        return {
            button,
            followingCount: document.querySelector(`[data-follow-count="following"][data-user-id="${CSS.escape(String(targetId))}"]`),
            followerCount: document.querySelector(`[data-follow-count="followers"][data-user-id="${CSS.escape(String(targetId))}"]`),
        };
    }

    function updateCounter(element, value) {
        if (!element) {
            return;
        }
        element.textContent = String(value ?? 0);
    }

    function updateFollowUi(targetId, payload) {
        const elements = getFollowStatusValues(targetId);
        const profileFollowingCount = payload.profileFollowingCount ?? payload.followingCount ?? 0;
        const profileFollowerCount = payload.profileFollowerCount ?? payload.followerCount ?? 0;

        if (elements && elements.button) {
            setFollowButtonState(elements.button, Boolean(payload.isFollowing), payload.isFollowing ? 'Seguindo' : 'Seguir');
        }

        const profileFollowingElements = document.querySelectorAll(`[data-follow-count="following"][data-user-id="${CSS.escape(String(targetId))}"]`);
        const profileFollowerElements = document.querySelectorAll(`[data-follow-count="followers"][data-user-id="${CSS.escape(String(targetId))}"]`);

        profileFollowingElements.forEach((item) => updateCounter(item, profileFollowingCount));
        profileFollowerElements.forEach((item) => updateCounter(item, profileFollowerCount));
    }

    function renderFollowModalList(users) {
        const modalList = document.getElementById('followModalList');
        const modalState = document.getElementById('followModalState');
        if (!modalList || !modalState) {
            return;
        }

        if (!users.length) {
            modalList.innerHTML = '';
            modalState.hidden = false;
            modalState.textContent = 'Nenhum usuario encontrado.';
            return;
        }

        modalState.hidden = true;
        modalList.innerHTML = users.map((user) => {
            const avatar = user.avatarUrl || '/static/uploads/default-avatar.svg';
            const displayName = user.displayName || user.username || 'Usuario';
            const username = user.username ? `@${user.username}` : '';

            return `
                <button type="button" class="follow-user-item" data-follow-user-link="${escapeHtml(String(user.profileUrl || '#'))}">
                    <img src="${escapeHtml(avatar)}" alt="Avatar de ${escapeHtml(displayName)}" loading="lazy">
                    <span class="follow-user-item__copy">
                        <strong>${escapeHtml(displayName)}</strong>
                        ${username ? `<small>${escapeHtml(username)}</small>` : ''}
                    </span>
                </button>
            `;
        }).join('');

        modalList.querySelectorAll('[data-follow-user-link]').forEach((button) => {
            button.addEventListener('click', () => {
                const target = button.getAttribute('data-follow-user-link');
                if (target) {
                    window.location.href = target;
                }
            });
        });
    }

    async function loadFollowList(userId, type) {
        const modalTitle = document.getElementById('followModalTitle');
        const modalState = document.getElementById('followModalState');
        const modalList = document.getElementById('followModalList');
        if (!modalTitle || !modalState || !modalList) {
            return;
        }

        modalTitle.textContent = type === 'followers' ? 'Seguidores' : 'Seguindo';
        modalState.hidden = false;
        modalState.textContent = 'Carregando usuarios...';
        modalList.innerHTML = '';

        const endpoint = type === 'followers' ? `/api/users/${userId}/followers` : `/api/users/${userId}/following`;

        try {
            const response = await fetch(endpoint, { headers: { 'Accept': 'application/json' } });
            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.erro || 'Nao foi possivel carregar a lista.');
            }

            const users = payload.users || [];
            if (!users.length) {
                modalState.hidden = false;
                modalState.textContent = type === 'followers' ? 'Você ainda não tem seguidores.' : 'Você ainda não segue ninguém.';
                modalList.innerHTML = '';
                return;
            }

            renderFollowModalList(users);
        } catch (error) {
            modalState.hidden = false;
            modalState.textContent = error.message || 'Nao foi possivel carregar a lista.';
        }
    }

    function bindFollowModal() {
        const modal = document.getElementById('followUserModal');
        const closeButtons = document.querySelectorAll('[data-follow-modal-close]');
        const openButtons = document.querySelectorAll('[data-follow-list-open]');

        if (!modal) {
            return;
        }

        closeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                modal.hidden = true;
            });
        });

        modal.addEventListener('click', (event) => {
            if (event.target === modal || event.target.classList.contains('review-modal-backdrop')) {
                modal.hidden = true;
            }
        });

        openButtons.forEach((button) => {
            button.addEventListener('click', async () => {
                const userId = button.getAttribute('data-user-id');
                const type = button.getAttribute('data-follow-list-open');
                if (!userId || !type) {
                    return;
                }
                modal.hidden = false;
                await loadFollowList(userId, type);
            });
        });
    }

    function bindFollowButtons() {
        const buttons = document.querySelectorAll('[data-follow-toggle]');

        buttons.forEach((button) => {
            button.addEventListener('click', async () => {
                const userId = button.getAttribute('data-user-id');
                const isAuthenticated = button.getAttribute('data-authenticated') === 'true';
                if (!isAuthenticated) {
                    redirectToLogin();
                    return;
                }

                if (!userId) {
                    return;
                }

                const isFollowing = button.dataset.isFollowing === 'true';
                const method = isFollowing ? 'DELETE' : 'POST';
                const url = `/api/users/${userId}/follow`;

                button.disabled = true;
                button.textContent = '...';

                try {
                    const response = await fetch(url, { method, headers: { 'Accept': 'application/json' } });
                    const payload = await response.json();
                    if (response.status === 401) {
                        redirectToLogin();
                        return;
                    }
                    if (!response.ok) {
                        throw new Error(payload.erro || 'Nao foi possivel atualizar o relacionamento.');
                    }

                    updateFollowUi(Number(userId), payload);
                } catch (error) {
                    if (error.message && error.message.includes('self')) {
                        return;
                    }
                    const nextText = button.dataset.isFollowing === 'true' ? 'Seguindo' : 'Seguir';
                    setFollowButtonState(button, button.dataset.isFollowing === 'true', nextText);
                } finally {
                    button.disabled = false;
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        bindFollowButtons();
        bindFollowModal();
    });
})();
