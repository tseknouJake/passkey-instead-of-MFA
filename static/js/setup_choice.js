// Add click handlers to cards (no inline onclick)
document.querySelectorAll('.auth-card').forEach(card => {
    card.addEventListener('click', function(e) {
        // Don't trigger if clicking the link directly
        if (e.target.tagName !== 'A') {
            window.location.href = this.dataset.url;
        }
    });
});