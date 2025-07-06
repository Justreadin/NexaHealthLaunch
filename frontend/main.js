// Initialize animations with GSAP
gsap.registerPlugin(ScrollTrigger);

// Animate elements on scroll
document.querySelectorAll('section').forEach((section, index) => {
    gsap.from(section, {
        opacity: 0,
        y: 50,
        duration: 1,
        scrollTrigger: {
            trigger: section,
            start: "top 80%",
            toggleActions: "play none none none"
        }
    });
});

// Custom cursor effect
const cursor = document.getElementById('cursor');
if (window.matchMedia("(pointer: fine)").matches) {
    document.addEventListener('mousemove', (e) => {
        gsap.to(cursor, {
            x: e.clientX,
            y: e.clientY,
            duration: 0.5,
            ease: "power2.out"
        });
    });
    
    // Highlight links on hover
    document.querySelectorAll('a, button').forEach(el => {
        el.addEventListener('mouseenter', () => {
            gsap.to(cursor, { scale: 2, duration: 0.3 });
        });
        el.addEventListener('mouseleave', () => {
            gsap.to(cursor, { scale: 1, duration: 0.3 });
        });
    });
} else {
    cursor.style.display = 'none';
}

// Mobile menu toggle
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
const closeMenuButton = document.getElementById('close-menu');

mobileMenuButton.addEventListener('click', () => {
    mobileMenu.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
});

closeMenuButton.addEventListener('click', () => {
    mobileMenu.classList.add('hidden');
    document.body.style.overflow = '';
});

// Close menu when clicking on links
mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        mobileMenu.classList.add('hidden');
        document.body.style.overflow = '';
    });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// Form submission to FastAPI backend
const betaForm = document.getElementById('beta-form');
if (betaForm) {
    betaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form elements
        const form = e.target;
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        
        // Show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing...`;
        
        try {
            // Prepare the data
            const formValues = {
                name: formData.get('name'),
                email: formData.get('email'),
                interest: formData.get('interest'),
                timestamp: new Date().toISOString()
            };
            
            const response = await fetch('https://lyrecal.onrender.com/api/submissions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formValues)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Show success message
            Swal.fire({
                icon: 'success',
                title: 'Thank you!',
                text: 'Your submission has been received. We\'ll be in touch soon.',
                confirmButtonColor: '#3b82f6',
            });
            
            // Reset form
            form.reset();
            
        } catch (error) {
            console.error('Error submitting form:', error);
            
            // Show error message
            Swal.fire({
                icon: 'error',
                title: 'Submission Failed',
                text: 'There was an error submitting your form. Please try again.',
                confirmButtonColor: '#3b82f6',
            });
            
        } finally {
            // Reset button state
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
}

// Initialize select dropdown styling
document.addEventListener('DOMContentLoaded', () => {
    // Fix select dropdown text color
    const selectElements = document.querySelectorAll('select');
    selectElements.forEach(select => {
        // Set default text color
        select.style.color = '#ffffff';
        
        // Handle change events to maintain visibility
        select.addEventListener('change', function() {
            this.style.color = '#ffffff';
        });
    });
    
    // Lazy load images
    if ('loading' in HTMLImageElement.prototype) {
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const image = entry.target;
                        image.src = image.dataset.src;
                        imageObserver.unobserve(image);
                    }
                });
            });

            lazyImages.forEach(image => {
                imageObserver.observe(image);
            });
        }
    }
    
    // Add scroll class to body
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            document.body.classList.add('scrolled');
        } else {
            document.body.classList.remove('scrolled');
        }
    });
});

// Service Worker for PWA functionality
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(registration => {
            console.log('ServiceWorker registration successful');
        }).catch(err => {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}