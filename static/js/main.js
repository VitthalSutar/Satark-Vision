// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Initialize loading spinners
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading-spinner"></div>';
    }
}

function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// Animate numbers in stats counters
function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Initialize stat counters when they become visible
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && entry.target.classList.contains('stats-counter')) {
            const target = parseInt(entry.target.getAttribute('data-target'), 10);
            animateValue(entry.target, 0, target, 2000);
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.stats-counter').forEach((counter) => {
    observer.observe(counter);
});

// Add page transition effect
document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('page-transition');
});

// Initialize progress bars
document.querySelectorAll('.progress-custom').forEach(progress => {
    const bar = progress.querySelector('.progress-bar-custom');
    const targetWidth = bar.getAttribute('data-width');
    setTimeout(() => {
        bar.style.width = targetWidth + '%';
    }, 100);
});

// Floating Action Button scroll to top
const fab = document.querySelector('.fab');
if (fab) {
    window.onscroll = function() {
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            fab.style.display = "flex";
        } else {
            fab.style.display = "none";
        }
    };
    
    fab.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}