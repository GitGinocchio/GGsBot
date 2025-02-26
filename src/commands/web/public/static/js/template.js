document.addEventListener('DOMContentLoaded', function() {
    console.log(window.location.pathname);
    
    const currentActive = document.getElementById('active');
    if (currentActive) { currentActive.removeAttribute("id"); }
    
    const links = document.querySelectorAll('.nav-links li a');
    links.forEach(link => {
        if (link.getAttribute('href') === window.location.pathname) {
            link.setAttribute("id", "active");
        }
    });

    function setActiveAndRedirect(event, link) {
        event.preventDefault(); // Previene il comportamento di default (il redirect immediato)

        const currentActive = document.getElementById('active');
        currentActive.removeAttribute("id");
        
        // Aggiungi la classe 'active' al link cliccato
        link.setAttribute("id", "active");
        
        // Esegui il redirect dopo 300 millisecondi (per vedere l'animazione)
        /*
        setTimeout(function() {
            window.location.href = link.href;
        }, 10000); // Tempo per l'animazione
        */
    }
});