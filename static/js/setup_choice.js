// AUTHORS:
// Condoleezza Agbeko
// Jake Lockitch

document.querySelectorAll('.auth-card').forEach(card => {
    card.addEventListener('click', function(e) {
        if (e.target.tagName !== 'A') {
            window.location.href = this.dataset.url;
        }
    });
});