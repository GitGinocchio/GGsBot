document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelector('.nav-links');
    const navItems = document.querySelectorAll('.nav-links li a');
    let activeItem = document.querySelector('.nav-links li a.active');
    let isHovering = false;
    let hoverItem = null;
    
    // Imposta l'elemento attivo iniziale
    if (activeItem) {
        updateBackgroundPosition(activeItem);
    } else if (navItems.length > 0) {
        // Se non c'è un elemento attivo, usa il primo elemento come fallback
        navItems[0].classList.add('active');
        activeItem = navItems[0];
        updateBackgroundPosition(activeItem);
    }
    
    // Listener per l'hover su ogni elemento della navbar
    navItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            isHovering = true;
            hoverItem = this;
            
            // Resetta il colore del testo per tutti gli elementi
            navItems.forEach(navItem => {
                if (navItem !== this) {
                    navItem.style.color = '#fff';
                } else {
                    navItem.style.color = '#000';
                }
            });
            
            updateBackgroundPosition(this);
        });
    });
    
    // Listener per quando il mouse esce dalla navbar
    navLinks.addEventListener('mouseleave', function() {
        isHovering = false;
        hoverItem = null;
        
        if (activeItem) {
            // Resetta i colori del testo per tutti gli elementi
            navItems.forEach(navItem => {
                if (navItem === activeItem) {
                    navItem.style.color = '#000';
                } else {
                    navItem.style.color = '#fff';
                }
            });
            
            // Torna all'elemento attivo
            updateBackgroundPosition(activeItem);
        }
    });
    
    function updateBackgroundPosition(element) {
        // Calcola la posizione e dimensione dell'elemento
        const rect = element.getBoundingClientRect();
        const navRect = navLinks.getBoundingClientRect();
        
        // Calcola la posizione relativa al contenitore della navbar
        const left = rect.left - navRect.left;
        const width = rect.width;
        
        // Applica il posizionamento tramite variabili CSS personalizzate
        navLinks.style.setProperty('--background-left', `${left}px`);
        navLinks.style.setProperty('--background-width', `${width}px`);
    }
    
    // Imposta l'elemento attivo in base al percorso corrente
    function setActiveItemByPath() {
        const currentPath = window.location.pathname;
        let found = false;
        
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            const isActive = (
                href === currentPath ||
                (href === '/' && (currentPath === '/' || currentPath === '/index.html')) ||
                (href !== '/' && currentPath.startsWith(href))
            );
            
            if (isActive) {
                item.classList.add('active');
                activeItem = item;
                
                // Se non c'è hover, aggiorna il colore dell'elemento attivo
                if (!isHovering) {
                    item.style.color = '#000';
                    updateBackgroundPosition(item);
                }
                
                found = true;
            } else {
                item.classList.remove('active');
                
                // Se non c'è hover, tutti gli elementi non attivi sono bianchi
                if (!isHovering) {
                    item.style.color = '#fff';
                }
            }
        });
        
        // Se nessun elemento corrisponde, usa Home come fallback
        if (!found && navItems.length > 0) {
            navItems[0].classList.add('active');
            activeItem = navItems[0];
            if (!isHovering) {
                navItems[0].style.color = '#000';
                updateBackgroundPosition(activeItem);
            }
        }
    }
    
    // Esegui subito e quando cambia URL
    setActiveItemByPath();
    window.addEventListener('popstate', setActiveItemByPath);
    
    // Aggiungi CSS personalizzato per le variabili
    const style = document.createElement('style');
    style.textContent = `
        .nav-links::after {
            left: var(--background-left, 0);
            width: var(--background-width, 0);
        }
    `;
    document.head.appendChild(style);
});