console.log('EcoBite Client Loaded');
if (typeof window !== 'undefined') window.appVersion = '3.1';

// Navbar Scroll Effect
const navbar = document.querySelector('.navbar');

if (navbar) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = '#FFFFFF';
            navbar.style.boxShadow = '0 4px 16px rgba(28, 37, 32, 0.06)';
        } else {
            navbar.style.background = '#FFFFFF';
            navbar.style.boxShadow = '0 2px 10px rgba(28, 37, 32, 0.04)';
        }
    });
}

// --- Handle Donation Form Submission ---
// Logic moved to donate.html for reliability
const donationForm = document.getElementById('donationForm');
if (donationForm) {
    // Listener removed to prevent conflicts
}

function showToast() {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// --- Find Food Page Logic ---
const donationGrid = document.getElementById('donationGrid');
const deliveryGrid = document.getElementById('deliveryGrid');
let allDonations = []; // Store for client-side filtering

if (donationGrid) {
    setupFilters();
    fetchDonations('find-food');
} else if (deliveryGrid) {
    fetchDonations('delivery');
}

function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    if (!filterBtns.length) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // UI Update
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Filter Logic
            const filter = btn.getAttribute('data-filter') || btn.innerText.toLowerCase();
            applyFilter(filter);
        });
    });
}

function getClass(donation) {
    // 1. Raw/Packaged -> Human (simplify for prototype)
    if (donation.food_type && (donation.food_type.includes('raw') || donation.food_type.includes('pack'))) {
        return 'human';
    }

    // 2. Cooked -> Time Based
    const prepTime = donation.preparation_time || donation.timestamp;
    if (!prepTime) return 'human'; // Fallback if no time

    const diffMs = new Date() - new Date(prepTime);
    const diffHrs = diffMs / (1000 * 60 * 60);

    if (diffHrs < 48) return 'human';
    if (diffHrs < 96) return 'animal';
    if (diffHrs < 120) return 'compost';
    return 'landfill';
}

function applyFilter(filter) {
    if (!allDonations.length) return;

    // Always filter for Available first (on Find Food page)
    let filtered = allDonations.filter(d => d.status === 'Available');

    // Category Filter
    if (filter !== 'all') {
        filtered = filtered.filter(d => getClass(d) === filter);
    }

    renderDonations(filtered, donationGrid, false);
}

async function fetchDonations(pageType) {
    const grid = pageType === 'find-food' ? donationGrid : deliveryGrid;

    try {
        const response = await fetch('/api/donations');
        const donations = await response.json();

        // Save globally
        allDonations = donations;

        if (pageType === 'find-food') {
            renderDonations(donations.filter(d => d.status === 'Available'), grid, false);
        } else {
            const tasks = donations.filter(d => ['Claimed', 'Picked Up'].includes(d.status));
            renderDonations(tasks, grid, true);
        }

    } catch (error) {
        console.error('Error fetching donations:', error);
        grid.innerHTML = '<p style="text-align: center;">Failed to load data.</p>';
    }
}


// --- Location Logic ---
let userLocation = null;

if (navigator.geolocation && donationGrid) {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            if (donationGrid && donationGrid.children.length > 0) fetchDonations('find-food');
        },
        (error) => {
            console.log('Location access denied or error:', error);
        }
    );
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const d = R * c;
    return d.toFixed(1);
}

function deg2rad(deg) {
    return deg * (Math.PI / 180);
}

function formatFreshness(timestamp) {
    if (!timestamp) return 'Unknown freshness';
    const prepTime = new Date(timestamp);
    const now = new Date();
    const diffMs = now - prepTime;
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHrs < 0) return 'Freshly Prepared'; // Future time correction
    if (diffHrs === 0) {
        return `Prepared ${diffMins} mins ago`;
    }
    return `Prepared ${diffHrs} hr ${diffMins} min ago`;
}

// --- Live Expiry Logic ---
// --- Live Expiry Logic (Dual Phase) ---
setInterval(() => {
    document.querySelectorAll('.expiry-cnt').forEach(el => {
        const prepStr = el.getAttribute('data-prep'); // We will use prep time as base
        if (!prepStr) return;

        const now = new Date();
        const start = new Date(prepStr);

        // Phase 1: Human (48 hours from prep)
        const humanExpiry = new Date(start.getTime() + (48 * 60 * 60 * 1000));

        // Phase 2: Animal (Human + 48 hours = 96 hours total)
        const animalExpiry = new Date(start.getTime() + (96 * 60 * 60 * 1000));

        let diffMs = humanExpiry - now;
        let mode = 'human';

        if (diffMs <= 0) {
            // Human time passed, check Animal time
            diffMs = animalExpiry - now;
            mode = 'animal';
        }

        if (diffMs <= 0) {
            el.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Fully Expired';
            el.className = 'expiry-cnt expired';
            return;
        }

        const hrs = Math.floor(diffMs / (1000 * 60 * 60));
        const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        const secs = Math.floor((diffMs % (1000 * 60)) / 1000);

        if (mode === 'human') {
            el.innerHTML = `<i class="fa-solid fa-utensils"></i> For Humans: ${hrs}h ${mins}m ${secs}s`;
            el.className = 'expiry-cnt safe';
            if (hrs < 6) el.classList.add('warning'); // Getting close to end of human phase
        } else {
            el.innerHTML = `<i class="fa-solid fa-paw"></i> For Animals: ${hrs}h ${mins}m ${secs}s`;
            el.className = 'expiry-cnt animal-mode'; // New class for animal phase
        }

    });
}, 1000);

// CSS for Timers
const style = document.createElement('style');
style.innerHTML = `
    .expiry-cnt {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 6px 10px;
        border-radius: 6px;
        margin-bottom: 10px;
        display: inline-block;
        width: 100%;
        text-align: center;
        background: rgba(255,255,255,0.05);
        color: #94a3b8;
    }
    .expiry-cnt.safe { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .expiry-cnt.warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .expiry-cnt.urgent { 
        background: rgba(239, 68, 68, 0.2); 
        color: #f87171; 
        animation: pulse 2s infinite; 
    }
    .expiry-cnt.expired { background: rgba(255,255,255,0.1); color: #94a3b8; text-decoration: line-through; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);


function renderDonations(data, grid, isDeliveryView) {
    grid.innerHTML = '';

    // Sort logic: Urgent (soonest expiry) first!
    // But keep claimed/picked up in logical order if needed?
    // Let's sort filtered list passed to this function.
    // If it's a "Available" list, sort by urgency.

    if (!isDeliveryView) {
        data.sort((a, b) => {
            const dateA = a.expiry_datetime ? new Date(a.expiry_datetime) : new Date('2099-01-01');
            const dateB = b.expiry_datetime ? new Date(b.expiry_datetime) : new Date('2099-01-01');
            return dateA - dateB;
        });
    }

    if (data.length === 0) {
        grid.innerHTML = `
            <div class="loading-state">
                <i class="fa-solid ${isDeliveryView ? 'fa-clipboard-check' : 'fa-basket-shopping'}"></i>
                <p>${isDeliveryView ? 'No active deliveries assigned.' : 'No active donations found nearby.'}</p>
            </div>
        `;
        return;
    }

    data.forEach(donation => { // Removed reverse() to respect sort
        const card = document.createElement('div');
        card.className = 'donation-card';
        card.setAttribute('data-id', donation.id);

        let icon = 'fa-utensils';
        if (donation.food_type === 'raw_ingredients') icon = 'fa-carrot';
        if (donation.food_type === 'packaged_snacks') icon = 'fa-cookie-bite';

        let badgeClass = 'available';
        if (donation.status === 'Claimed') badgeClass = 'claimed';
        if (donation.status === 'Picked Up') badgeClass = 'available';

        let distanceTag = '';
        if (userLocation) {
            const mockDonorLat = userLocation.lat + (Math.random() * 0.02 - 0.01);
            const mockDonorLng = userLocation.lng + (Math.random() * 0.02 - 0.01);
            const dist = calculateDistance(userLocation.lat, userLocation.lng, mockDonorLat, mockDonorLng);
            distanceTag = `<span style="font-size: 0.8rem; color: var(--primary-color); margin-left: auto;">
                            <i class="fa-solid fa-route"></i> ${dist} km away
                           </span>`;
        }

        function isDonationExpired(donation) {
            if (donation.expiry_datetime) {
                const exp = new Date(donation.expiry_datetime);
                if (!isNaN(exp) && new Date() > exp) return true;
            }
            const prep = donation.preparation_time || donation.timestamp;
            if (prep) {
                const prepDate = new Date(prep);
                if (!isNaN(prepDate)) {
                    const diffHrs = (new Date() - prepDate) / (1000 * 60 * 60);
                    if (diffHrs >= 96) return true;
                }
            }
            return false;
        }

        let actionButton = '';
        if (!isDeliveryView) {
            const isExpired = isDonationExpired(donation);
            const claimBtn = isExpired 
                ? `<button class="btn-claim" style="flex:1; background: #94a3b8; color: white; cursor: not-allowed;" disabled><i class="fa-solid fa-ban"></i> Expired</button>`
                : `<button class="btn-claim" style="flex:1;" onclick="updateStatus(${donation.id}, 'Claimed')">Claim</button>`;

            actionButton = `
                <div style="display:flex; gap:10px;">
                    ${claimBtn}
                    <button class="btn-claim" style="flex:1; background: #3b82f6;" onclick="if(window.openChat) window.openChat(${donation.id}, 'Donor', ${donation.donor_id}); else alert('Chat available on Dashboard')">
                        <i class="fa-solid fa-comments"></i> Chat
                    </button>
                </div>
            `;
        } else {
            if (donation.status === 'Claimed') {
                actionButton = `<button class="btn-claim" onclick="updateStatus(${donation.id}, 'Picked Up')"><i class="fa-solid fa-box-open"></i> Confirm Pickup</button>`;
            } else if (donation.status === 'Picked Up') {
                actionButton = `<button class="btn-claim" style="background: var(--primary-color); color: white;" onclick="updateStatus(${donation.id}, 'Delivered')"><i class="fa-solid fa-check"></i> Confirm Delivery</button>`;
            }
        }

        let imageHtml = '';
        if (donation.image_path && donation.image_path.trim() !== '') {
            const imgUrl = donation.image_path.startsWith('http') || donation.image_path.startsWith('/') ? donation.image_path : '/' + donation.image_path;
            imageHtml = `<img src="${imgUrl}" alt="${donation.food_name || 'Food'}" onerror="this.onerror=null; this.src='/hero_food.jpg';" style="width:100%; height:160px; object-fit:cover; border-radius:8px; margin-bottom:12px;">`;
        } else {
            imageHtml = `<div style="width:100%; height:130px; background:linear-gradient(135deg, #FFF8F0 0%, #EAE5DE 100%); display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:8px; margin-bottom:12px; color:var(--primary-orange);"><i class="fa-solid fa-utensils" style="font-size:2rem; margin-bottom:6px;"></i><span style="font-size:0.8rem; font-weight:600; color:var(--forest-green);">EcoBite Food Rescue</span></div>`;
        }

        let dietTypeBadge = '';
        if (donation.diet_type) {
            dietTypeBadge = `<span class="status-badge" style="background:${donation.diet_type === 'Veg' ? '#e8f5e9' : '#ffebee'}; color:${donation.diet_type === 'Veg' ? '#2e7d32' : '#c62828'}; margin-left:5px;">${donation.diet_type}</span>`;
        }

        // Expiry Badge
        const prepTime = donation.preparation_time || donation.timestamp;
        const expiryHtml = donation.status === 'Available'
            ? `<div class="expiry-cnt" data-prep="${prepTime}">Calculating...</div>`
            : '';

        let emergencyTag = '';
        const desc = donation.instructions || '';
        // Check case-insensitive for 'emergency'
        if (desc.toUpperCase().includes('EMERGENCY')) {
            emergencyTag = `<div style="background: #ef4444; color: white; text-align: center; font-weight: bold; font-size: 0.8rem; padding: 6px; border-radius: 4px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"><i class="fa-solid fa-triangle-exclamation"></i> EMERGENCY DONATION</div>`;
        }
        else if (desc.toUpperCase().includes('BULK')) {
            emergencyTag = `<div style="background: #f59e0b; color: #1e293b; text-align: center; font-weight: bold; font-size: 0.8rem; padding: 6px; border-radius: 4px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"><i class="fa-solid fa-champagne-glasses"></i> BULK EVENT DONATION</div>`;
        }

        // Use proper title if available
        const title = (donation.food_name && donation.food_name !== 'undefined') ? donation.food_name : (donation.food_type || donation.foodType || 'Food').replace('_', ' ').toUpperCase();

        card.innerHTML = `
            ${imageHtml}
            <div class="card-header">
                <div class="food-icon"><i class="fa-solid ${icon}"></i></div>
                <div class="badges">
                    ${dietTypeBadge}
                    <span class="status-badge ${badgeClass}">${donation.status}</span>
                    <span class="status-badge" style="background:#e0f2fe; color:#0369a1; text-transform:capitalize;">For ${getClass(donation)}</span>
                </div>
            </div>
            
            ${emergencyTag}
            <h3>${title}</h3>
            
            ${expiryHtml}
            
            <span class="donor-name">by ${donation.pickup_address || donation.address || 'Unknown'}</span>
            
            <div class="card-details">
                <div class="detail-item">
                    <i class="fa-solid fa-weight-hanging"></i>
                    <span>${donation.quantity} Servings</span>
                </div>
                <!-- Removed Old Freshness Logic in favor of Timer -->
                <div class="detail-item">
                    <i class="fa-regular fa-clock"></i>
                    <span>Posted: ${new Date(donation.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div class="detail-item">
                    <i class="fa-solid fa-fire-burner"></i>
                    <span>Prepared: ${donation.preparation_time ? new Date(donation.preparation_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown'}</span>
                </div>
                <div class="detail-item" style="width: 100%;">
                    <i class="fa-solid fa-location-dot"></i>
                    <span>${donation.pickup_address || donation.address}</span>
                    ${distanceTag}
                </div>
            </div>
            
            ${actionButton}
        `;

        grid.appendChild(card);
    });
}

window.updateStatus = async function (id, newStatus) {
    try {
        const response = await fetch('/api/update-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, status: newStatus })
        });

        if (response.ok) {
            showToast();
            if (document.getElementById('donationGrid')) fetchDonations('find-food');
            if (document.getElementById('deliveryGrid')) fetchDonations('delivery');
        } else {
            alert('Failed to update status');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
// --- Mobile Navbar Toggle ---
const mobileToggle = document.querySelector('.mobile-toggle');
const navLinks = document.querySelector('.nav-links');

if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');

        // Optional: Change icon (bars -> times)
        const icon = mobileToggle.querySelector('i');
        if (icon) {
            if (navLinks.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-xmark');
            } else {
                icon.classList.remove('fa-xmark');
                icon.classList.add('fa-bars');
            }
        }
    });

    // Close menu when clicking a link
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            const icon = mobileToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-xmark');
                icon.classList.add('fa-bars');
            }
        });
    });
}

// --- Emergency & Broadcast System ---
async function checkEmergencyStatus() {
    try {
        // 1. Check SOS (High Priority)
        const sosRes = await fetch('/api/sos/active');
        const sosAlerts = await sosRes.json();

        if (sosAlerts.length > 0) {
            showEmergencyBanner('SOS', sosAlerts[0]);
            return; // SOS takes precedence
        }

        // 2. Check Broadcasts
        const bcRes = await fetch('/api/broadcast/active');
        const broadcast = await bcRes.json();

        if (broadcast) {
            showEmergencyBanner('Broadcast', broadcast);
        }

    } catch (e) { console.error('Emergency check failed', e); }
}

function showEmergencyBanner(type, data) {
    // Remove existing
    const existing = document.getElementById('emergency-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'emergency-banner';

    let bgColor = '#3b82f6'; // Info Blue
    let icon = 'fa-bullhorn';
    let title = 'System Message';
    let msg = '';

    if (type === 'SOS') {
        bgColor = '#ef4444'; // Red
        icon = 'fa-triangle-exclamation';
        title = `SOS ALERT: ${data.title}`;
        msg = `${data.message} (${data.location})`;
    } else {
        // Broadcast
        // Updated to match DB schema: title, description, area, contact_details
        if (data.level === 'Warning') bgColor = '#f59e0b';
        if (data.level === 'Critical') bgColor = '#ef4444';
        title = data.title || (data.level === 'Critical' ? 'CRITICAL ALERT' : 'System Announcement');

        msg = `<strong>${data.area}</strong><br>${data.description}<br><br><i class="fa-solid fa-phone"></i> ${data.contact_details}`;
    }

    banner.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        z-index: 10000;
        max-width: 350px;
        animation: slideIn 0.5s ease-out;
        border: 1px solid rgba(255,255,255,0.2);
    `;

    banner.innerHTML = `
        <div style="display:flex; align-items:flex-start; gap:15px;">
            <div style="font-size:1.5rem;"><i class="fa-solid ${icon}"></i></div>
            <div>
                <h3 style="margin:0 0 5px 0; font-size:1.1rem; font-weight:700;">${title}</h3>
                <p style="margin:0; font-size:0.95rem; line-height:1.4;">${msg}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background:none; border:none; color:white; cursor:pointer;"><i class="fa-solid fa-xmark"></i></button>
        </div>
    `;

    document.body.appendChild(banner);

    // Add animation style if not exists
    if (!document.getElementById('anim-style')) {
        const style = document.createElement('style');
        style.id = 'anim-style';
        style.innerHTML = `@keyframes slideIn { from { transform: translateX(100%); opacity:0; } to { transform: translateX(0); opacity:1; } }`;
        document.head.appendChild(style);
    }
}

// Start Polling (Every 30 seconds)
checkEmergencyStatus();
setInterval(checkEmergencyStatus, 30000);
