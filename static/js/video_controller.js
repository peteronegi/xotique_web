/**
 * XOTIQUE - Global Interaction Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. SCROLL REVEAL ANIMATION ---
    const reveals = document.querySelectorAll('.reveal');
    
    const revealOnScroll = () => {
        for (let i = 0; i < reveals.length; i++) {
            let windowHeight = window.innerHeight;
            let elementTop = reveals[i].getBoundingClientRect().top;
            let elementVisible = 150;

            if (elementTop < windowHeight - elementVisible) {
                reveals[i].classList.add('active');
            }
        }
    };

    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Run once on load

    // --- 2. LIVE MEDIA PREVIEW (FOR ADMIN FORMS) ---
    // This looks for any file input in your Admin forms
    const fileInput = document.querySelector('input[type="file"]');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const [file] = this.files;
            if (file) {
                const url = URL.createObjectURL(file);
                
                // Find or create the preview container
                let previewZone = document.getElementById('live-preview');
                if (!previewZone) {
                    previewZone = document.createElement('div');
                    previewZone.id = 'live-preview';
                    previewZone.style.cssText = "margin-top: 20px; padding: 10px; border: 1px dashed var(--brand-gold); text-align: center;";
                    fileInput.after(previewZone);
                }
                
                // Render Image or Video preview based on file type
                if (file.type.includes('video')) {
                    previewZone.innerHTML = `
                        <p style="font-size: 0.6rem; color: #999; margin-bottom: 5px;">VIDEO PREVIEW</p>
                        <video src="${url}" autoplay muted loop style="width:100%; max-height:250px; object-fit:cover;"></video>
                    `;
                } else {
                    previewZone.innerHTML = `
                        <p style="font-size: 0.6rem; color: #999; margin-bottom: 5px;">IMAGE PREVIEW</p>
                        <img src="${url}" style="width:100%; max-height:250px; object-fit:cover;">
                    `;
                }
            }
        });
    }

    // --- 3. MODAL CONTROLLER (FOR FLASH MESSAGES) ---
    window.closeModal = function() {
        const modal = document.getElementById('successModal');
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }
    };

    // --- 4. SUBMIT BUTTON SPINNER ---
    const adminForm = document.querySelector('form[enctype="multipart/form-data"]');
    
    if (adminForm) {
        adminForm.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            
            if (submitBtn) {
                // Disable button to prevent double-clicks
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
                submitBtn.style.cursor = 'not-allowed';
                
                // Add the spinner text and icon
                submitBtn.innerHTML = `
                    <i class="fas fa-spinner fa-spin" style="margin-right: 10px;"></i>
                    UPLOADING TO SERVER...
                `;
            }
        });
    }
});