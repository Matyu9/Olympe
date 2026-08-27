// Picker utilisateur avec recherche/filtrage, façon menu déroulant filtrable (Office admin center).
// usernames : tableau de tous les noms d'utilisateur connus, injecté par le template.
function setupUserPicker(inputId, resultsId, usernames) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);

    function renderResults() {
        const query = input.value.trim().toLowerCase();
        const matches = usernames
            .filter(username => username.toLowerCase().includes(query))
            .slice(0, 20);

        results.innerHTML = '';
        matches.forEach(username => {
            const item = document.createElement('li');
            item.textContent = username;
            item.className = 'px-3 py-2 hover:bg-base-200 cursor-pointer';
            item.onclick = () => {
                input.value = username;
                results.classList.add('hidden');
            };
            results.appendChild(item);
        });
        results.classList.toggle('hidden', matches.length === 0);
    }

    input.addEventListener('input', renderResults);
    input.addEventListener('focus', renderResults);
    document.addEventListener('click', (event) => {
        if (event.target !== input && !results.contains(event.target)) {
            results.classList.add('hidden');
        }
    });
}
