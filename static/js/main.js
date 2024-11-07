// Highlight the active navigation link
document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".menu a");

    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });
});
// Welcome button interaction on the home page
document.addEventListener("DOMContentLoaded", function () {
    const welcomeButton = document.getElementById("welcome-button");

    if (welcomeButton) {
        welcomeButton.addEventListener("click", function () {
            alert("Welcome to the Anti-Doping Education Platform!");
        });
    }
});
// Expand/collapse podcast descriptions on the Podcasts page
document.addEventListener("DOMContentLoaded", function () {
    const podcastTitles = document.querySelectorAll(".podcast-title");

    podcastTitles.forEach(title => {
        title.addEventListener("click", function () {
            const description = this.nextElementSibling;
            if (description.style.display === "none") {
                description.style.display = "block";
            } else {
                description.style.display = "none";
            }
        });
    });
});
