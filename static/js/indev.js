(function () {
    var elementos = document.querySelectorAll(".reveal");

    // Si el navegador no soporta el detector, todo queda visible
    if (!("IntersectionObserver" in window)) return;

    document.body.classList.add("reveal-activo");

    var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (entrada.isIntersecting) {
                entrada.target.classList.add("visible");
                observador.unobserve(entrada.target);
            }
        });
    }, { threshold: 0.2 });

    elementos.forEach(function (el) { observador.observe(el); });
})();