/**
 * AeroScheduler Expert System - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // Highlight the active nav link based on current URL
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(function (link) {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});
