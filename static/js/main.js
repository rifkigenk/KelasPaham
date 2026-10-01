// main.js - Vanilla JS untuk interaksi dasar

document.addEventListener('DOMContentLoaded', () => {
    // Menghilangkan flash message secara perlahan setelah 5 detik
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.transition = 'opacity 0.5s ease';
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }

    // Mencegah klik ganda pada tombol submit untuk menghindari pengiriman form berkali-kali
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                // Beri sedikit jeda agar proses submit form HTML biasa tetap berjalan
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.innerText = 'Memproses...';
                }, 10);
            }
        });
    });
});
