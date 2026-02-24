document.addEventListener("DOMContentLoaded", function() {
    loadStrategyContent();
    setupContactForm();
});

async function loadStrategyContent() {
    try {
        const response = await fetch("/strategy_content");
        const data = await response.json();

        document.getElementById("introduccion-content").innerHTML = data.introduccion;
        document.getElementById("identificacion-fuentes-content").innerHTML = data.identificacion_fuentes;
        document.getElementById("extraccion-procesamiento-content").innerHTML = data.extraccion_procesamiento;
        document.getElementById("deteccion-eventos-content").innerHTML = data.deteccion_eventos;
        document.getElementById("alertas-reportes-content").innerHTML = data.alertas_reportes;
        document.getElementById("mantenimiento-optimizacion-content").innerHTML = data.mantenimiento_optimizacion;

        // Store the full content for search functionality
        window.fullStrategyContent = data;

    } catch (error) {
        console.error("Error loading strategy content:", error);
        document.getElementById("introduccion-content").innerHTML = "<p>Error al cargar el contenido de la estrategia.</p>";
    }
}

function setupContactForm() {
    const contactForm = document.getElementById("contact-form");
    const formMessage = document.getElementById("form-message");

    contactForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const formData = new FormData(contactForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/contact", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                formMessage.className = "success-message";
                formMessage.textContent = result.message;
                contactForm.reset();
            } else {
                formMessage.className = "error-message";
                formMessage.textContent = result.error || "Error al enviar el mensaje.";
            }
        } catch (error) {
            formMessage.className = "error-message";
            formMessage.textContent = "Error de conexión al enviar el mensaje.";
            console.error("Error sending contact form:", error);
        }
    });
}

function searchContent() {
    const searchTerm = document.getElementById("search-input").value.toLowerCase();
    const searchResultsDiv = document.getElementById("search-results");
    searchResultsDiv.innerHTML = "";

    if (!searchTerm) {
        searchResultsDiv.innerHTML = "<p>Por favor, introduce un término de búsqueda.</p>";
        return;
    }

    let resultsFound = false;
    const sections = [
        { id: "introduccion", title: "Introducción", content: window.fullStrategyContent.introduccion },
        { id: "identificacion-fuentes", title: "1. Identificación y Expansión de Fuentes de Información", content: window.fullStrategyContent.identificacion_fuentes },
        { id: "extraccion-procesamiento", title: "2. Extracción y Procesamiento de Datos", content: window.fullStrategyContent.extraccion_procesamiento },
        { id: "deteccion-eventos", title: "3. Detección de Eventos y Análisis de Información", content: window.fullStrategyContent.deteccion_eventos },
        { id: "alertas-reportes", title: "4. Generación de Alertas y Reportes", content: window.fullStrategyContent.alertas_reportes },
        { id: "mantenimiento-optimizacion", title: "5. Mantenimiento y Optimización Continua", content: window.fullStrategyContent.mantenimiento_optimizacion }
    ];

    sections.forEach(section => {
        const contentLower = section.content.toLowerCase();
        if (contentLower.includes(searchTerm)) {
            resultsFound = true;
            const resultDiv = document.createElement("div");
            resultDiv.className = "search-result";
            
            const title = document.createElement("h4");
            title.textContent = section.title;
            resultDiv.appendChild(title);

            // Find and highlight occurrences
            const regex = new RegExp(`(${searchTerm})`, "gi");
            const highlightedContent = section.content.replace(regex, `<span class="highlight">$1</span>`);

            // Display a snippet around the first occurrence
            const snippetLength = 200; // characters
            const firstIndex = contentLower.indexOf(searchTerm);
            let start = Math.max(0, firstIndex - snippetLength / 2);
            let end = Math.min(section.content.length, firstIndex + searchTerm.length + snippetLength / 2);

            // Adjust start to be at the beginning of a word if possible
            if (start > 0) {
                const firstSpace = section.content.indexOf(' ', start);
                if (firstSpace !== -1 && firstSpace < firstIndex) {
                    start = firstSpace + 1;
                }
            }

            // Adjust end to be at the end of a word if possible
            if (end < section.content.length) {
                const lastSpace = section.content.lastIndexOf(' ', end);
                if (lastSpace !== -1 && lastSpace > firstIndex + searchTerm.length) {
                    end = lastSpace;
                }
            }

            const snippet = highlightedContent.substring(start, end);
            const snippetP = document.createElement("p");
            snippetP.innerHTML = `...${snippet}...`;
            resultDiv.appendChild(snippetP);

            searchResultsDiv.appendChild(resultDiv);
        }
    });

    if (!resultsFound) {
        searchResultsDiv.innerHTML = "<p>No se encontraron resultados para su búsqueda.</p>";
    }
}

function clearSearch() {
    document.getElementById("search-input").value = "";
    document.getElementById("search-results").innerHTML = "";
}

