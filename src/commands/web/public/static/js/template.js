document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelector('.nav-links');
    const links = document.querySelectorAll('.nav-links li a');
    let redirectTimeout;
    let background;

    links.forEach(link => {
        if (link.getAttribute('href') === window.location.pathname) {
            link.setAttribute("id", "active");

            // Crea l'elemento che farà da background animato
            background = document.createElement('div');
            background.classList.add('background');
            navLinks.appendChild(background);
        }

        link.addEventListener("click", (event) => setActiveAndRedirect(event, link));
    });

    let currentSelected = document.getElementById('active');

    function updateBackground(newLink, instant = false) {
        const newRect = newLink.getBoundingClientRect();
        const navRect = navLinks.getBoundingClientRect();
        const newX = newRect.left - navRect.left;

        if (currentSelected) {
            const currentRect = currentSelected.getBoundingClientRect();
            const currentX = currentRect.left - navRect.left;

            // Se ci stiamo spostando, anima la transizione dal punto attuale
            background.style.transition = instant ? "none" : "transform 0.3s ease-in-out, width 0.3s ease-in-out";
        }

        // Imposta la larghezza e la posizione
        background.style.width = `${newRect.width}px`;
        background.style.transform = `translateX(${newX}px) translateY(-50%)`;
    }

    if (currentSelected) {
        updateBackground(currentSelected, true); // Posiziona il background senza animazione
    }

    function setActiveAndRedirect(event, link) {
        clearTimeout(redirectTimeout);
        event.preventDefault();

        // Rimuove lo stato attivo precedente
        document.querySelector('.nav-links li a#active')?.removeAttribute('id');

        if (background) {
           // Aggiungi la classe 'active' al link cliccato
           updateBackground(link);

            // Esegui il redirect dopo 300 millisecondi (per vedere l'animazione)
            redirectTimeout = setTimeout(() => {
                window.location.href = link.href;
            }, 300); // Tempo per l'animazione
        }
        else {
            window.location.href = link.href;
        }
    }
});