async function buscarFilme() {
    const nome = document.getElementById("movieInput").value;
    const resultado = document.getElementById("resultado");

    resultado.innerHTML = "<p>Carregando...</p>";

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

function redirecionar_perfil() {
    window.open("/perfil", "_blank");
}