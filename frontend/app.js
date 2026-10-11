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

window.isDonationExpired = function(donation) {
    if (!donation) return false;
    if (donation.status === 'Expired') return true;
    if (!['Available', 'Expired'].includes(donation.status)) return false;
    if (donation.is_expired) return true;
    if (donation.expiry_datetime) {
        const exp = new Date(donation.expiry_datetime);
        if (!isNaN(exp) && new Date() > exp) return true;
    }
    const prep = donation.preparation_time || donation.timestamp;
    if (prep) {
        const prepDate = new Date(prep);
        if (!isNaN(prepDate)) {
            const diffHrs = (new Date() - prepDate) / (1000 * 60 * 60);
            if (diffHrs >= 48) return true;
        }
    }
    return false;
};

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

    // Fresh available food safe for human consumption
    let freshList = allDonations.filter(d => d.status === 'Available' && !isDonationExpired(d));

    if (filter === 'veg') {
        freshList = freshList.filter(d => (d.diet_type || '').toLowerCase() === 'veg');
    } else if (filter === 'non-veg') {
        freshList = freshList.filter(d => (d.diet_type || '').toLowerCase() === 'non-veg');
    }

    renderDonations(freshList, donationGrid, false);
}

window.switchFoodChannel = function(channel) {
    const humanSec = document.getElementById('humanFoodSection');
    const expiredSec = document.getElementById('expiredFoodSection');
    const humanBtn = document.getElementById('channelHumanBtn');
    const expiredBtn = document.getElementById('channelExpiredBtn');
    const sideHuman = document.getElementById('sidebarHumanBtn');
    const sideExpired = document.getElementById('sidebarExpiredBtn');

    if (channel === 'human') {
        if (humanSec) humanSec.style.display = 'block';
        if (expiredSec) expiredSec.style.display = 'none';

        if (humanBtn) {
            humanBtn.classList.add('active');
            humanBtn.style.background = '#166534';
            humanBtn.style.color = '#FFFFFF';
        }
        if (expiredBtn) {
            expiredBtn.classList.remove('active');
            expiredBtn.style.background = 'transparent';
            expiredBtn.style.color = '#64748B';
        }
        if (sideHuman) sideHuman.classList.add('active');
        if (sideExpired) sideExpired.classList.remove('active');
    } else {
        if (humanSec) humanSec.style.display = 'none';
        if (expiredSec) expiredSec.style.display = 'block';

        if (expiredBtn) {
            expiredBtn.classList.add('active');
            expiredBtn.style.background = '#DC2626';
            expiredBtn.style.color = '#FFFFFF';
        }
        if (humanBtn) {
            humanBtn.classList.remove('active');
            humanBtn.style.background = 'transparent';
            humanBtn.style.color = '#64748B';
        }
        if (sideExpired) sideExpired.classList.add('active');
        if (sideHuman) sideHuman.classList.remove('active');
    }
};

window.allExpiredDonations = [];

window.renderExpiredShelf = function(expiredList) {
    const shelf = document.getElementById('expiredFoodShelf');
    const track = document.getElementById('expiredSlideTrack');
    const countEl = document.getElementById('expiredSlideCount');

    if (!shelf || !track) return;

    if (!expiredList || expiredList.length === 0) {
        if (countEl) countEl.innerText = '0 Items Expired';
        track.innerHTML = `
            <div style="padding: 24px; color: #15803D; font-weight: 700; background: #F0FDF4; border-radius: 12px; border: 1.5px solid #86EFAC; width: 100%; display: flex; align-items: center; gap: 12px;">
                <i class="fa-solid fa-circle-check" style="font-size: 1.5rem; color: #16A34A;"></i>
                <div>
                    <div>Zero Food Waste Left Unrescued!</div>
                    <div style="font-size: 0.82rem; color: #15803D; font-weight: 500;">No expired food donations at this moment. All active donations are fresh for human consumption.</div>
                </div>
            </div>
        `;
        return;
    }

    if (countEl) {
        countEl.innerText = `${expiredList.length} ${expiredList.length === 1 ? 'Item' : 'Items'} Expired`;
    }

    track.innerHTML = '';
    expiredList.forEach(d => {
        let imgUrl = d.image_path && d.image_path.trim() !== '' ? 
            (d.image_path.startsWith('http') || d.image_path.startsWith('/') ? d.image_path : '/' + d.image_path) : 
            '/hero_food.jpg';

        const title = (d.food_name && d.food_name !== 'undefined') ? d.food_name : (d.food_type || 'Food Item').replace('_', ' ').toUpperCase();
        const prep = d.preparation_time || d.timestamp;
        let repurposeCategory = 'Animal Shelters 🐾';
        let repurposeIcon = 'fa-paw';
        let repurposeBg = '#FEF3C7';
        let repurposeColor = '#92400E';

        if (prep) {
            const diffHrs = (new Date() - new Date(prep)) / (1000 * 60 * 60);
            if (diffHrs >= 96) {
                repurposeCategory = 'Bio-Composting 🌿';
                repurposeIcon = 'fa-leaf';
                repurposeBg = '#ECFDF5';
                repurposeColor = '#065F46';
            }
        }

        const slideCard = document.createElement('div');
        slideCard.className = 'expired-slide-card';
        slideCard.style.cssText = `
            min-width: 290px;
            max-width: 290px;
            background: #FFFFFF;
            border-radius: 14px;
            border: 1.5px solid #FDBA74;
            padding: 14px;
            box-shadow: 0 4px 14px rgba(234, 88, 12, 0.08);
            flex-shrink: 0;
            scroll-snap-align: start;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        `;

        slideCard.innerHTML = `
            <div>
                <div style="position: relative; margin-bottom: 10px; border-radius: 10px; overflow: hidden; height: 135px; background: #F1F5F9;">
                    <img src="${imgUrl}" onerror="this.onerror=null; this.src='/hero_food.jpg';" style="width: 100%; height: 100%; object-fit: cover; filter: saturate(0.85);" alt="${title}">
                    <span style="position: absolute; top: 8px; right: 8px; background: rgba(220, 38, 38, 0.92); color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; display: flex; align-items: center; gap: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.2);">
                        <i class="fa-solid fa-clock"></i> Expired for Humans
                    </span>
                    <span style="position: absolute; bottom: 8px; left: 8px; background: rgba(15, 23, 42, 0.75); color: #F8FAFC; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem;">
                        #${d.id}
                    </span>
                </div>

                <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 800; color: #1C2520; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${title}">
                    ${title}
                </h4>

                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 8px; line-height: 1.4;">
                    <div><i class="fa-solid fa-weight-hanging" style="color: #EA580C; width: 16px;"></i> <strong>${d.quantity || 'N/A'}</strong> Servings</div>
                    <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${d.pickup_address || 'Address on file'}">
                        <i class="fa-solid fa-location-dot" style="color: #EA580C; width: 16px;"></i> ${d.pickup_address || 'Address on file'}
                    </div>
                </div>

                <div style="background: ${repurposeBg}; border: 1px solid rgba(0,0,0,0.06); border-radius: 8px; padding: 6px 10px; font-size: 0.78rem; color: ${repurposeColor}; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; font-weight: 600;">
                    <i class="fa-solid ${repurposeIcon}"></i>
                    <span>Auto-Diverted: <strong>${repurposeCategory}</strong></span>
                </div>
            </div>

            <button onclick="updateStatus(${d.id}, 'Claimed')" class="btn-claim" style="background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%); color: white; border: none; border-radius: 8px; padding: 9px 12px; font-size: 0.82rem; font-weight: 700; cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 3px 8px rgba(234, 88, 12, 0.25);">
                <i class="fa-solid fa-recycle"></i> Rescue for ${repurposeCategory.split(' ')[0]}
            </button>
        `;

        track.appendChild(slideCard);
    });
};

window.renderExpiredGrid = function(list) {
    const grid = document.getElementById('expiredFullGrid');
    if (!grid) return;

    grid.innerHTML = '';
    if (!list || list.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 40px; color: #64748B;">
                <i class="fa-solid fa-recycle" style="font-size: 2.2rem; color: #EA580C; margin-bottom: 10px;"></i>
                <p>No repurposed food items matching this filter.</p>
            </div>
        `;
        return;
    }

    list.forEach(d => {
        let imgUrl = d.image_path && d.image_path.trim() !== '' ? 
            (d.image_path.startsWith('http') || d.image_path.startsWith('/') ? d.image_path : '/' + d.image_path) : 
            '/hero_food.jpg';

        const title = (d.food_name && d.food_name !== 'undefined') ? d.food_name : (d.food_type || 'Food Item').replace('_', ' ').toUpperCase();
        const prep = d.preparation_time || d.timestamp;
        let repurposeCategory = 'Animal Shelters 🐾';
        let repurposeIcon = 'fa-paw';
        let repurposeBg = '#FEF3C7';
        let repurposeColor = '#92400E';

        if (prep) {
            const diffHrs = (new Date() - new Date(prep)) / (1000 * 60 * 60);
            if (diffHrs >= 96) {
                repurposeCategory = 'Bio-Composting 🌿';
                repurposeIcon = 'fa-leaf';
                repurposeBg = '#ECFDF5';
                repurposeColor = '#065F46';
            }
        }

        const card = document.createElement('div');
        card.className = 'donation-card';
        card.style.border = '1.5px solid #FDBA74';
        card.style.background = '#FFFFFF';

        card.innerHTML = `
            <div style="position: relative; margin-bottom: 12px; border-radius: 8px; overflow: hidden; height: 150px; background: #F1F5F9;">
                <img src="${imgUrl}" onerror="this.onerror=null; this.src='/hero_food.jpg';" style="width: 100%; height: 100%; object-fit: cover;" alt="${title}">
                <span style="position: absolute; top: 8px; right: 8px; background: rgba(220, 38, 38, 0.92); color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">
                    <i class="fa-solid fa-clock-rotate-left"></i> Expired for Humans
                </span>
                <span style="position: absolute; bottom: 8px; left: 8px; background: rgba(15, 23, 42, 0.8); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem;">
                    #${d.id}
                </span>
            </div>

            <div class="card-header" style="margin-bottom: 8px;">
                <div class="badges" style="display:flex; gap:6px; flex-wrap:wrap;">
                    <span class="status-badge" style="background:${repurposeBg}; color:${repurposeColor}; font-weight:700;">
                        <i class="fa-solid ${repurposeIcon}"></i> For ${repurposeCategory}
                    </span>
                    <span class="status-badge" style="background:#FEE2E2; color:#DC2626;">Diverted</span>
                </div>
            </div>

            <h3 style="margin-bottom: 6px;">${title}</h3>
            <span class="donor-name" style="margin-bottom: 10px;">by ${d.pickup_address || d.address || 'Donor on File'}</span>

            <div class="card-details" style="margin-bottom: 14px;">
                <div class="detail-item">
                    <i class="fa-solid fa-weight-hanging" style="color: #EA580C;"></i>
                    <span>${d.quantity || 'N/A'} Servings</span>
                </div>
                <div class="detail-item">
                    <i class="fa-solid fa-fire-burner" style="color: #EA580C;"></i>
                    <span>Prepared: ${d.preparation_time ? new Date(d.preparation_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Earlier'}</span>
                </div>
                <div class="detail-item" style="width:100%;">
                    <i class="fa-solid fa-location-dot" style="color: #EA580C;"></i>
                    <span>${d.pickup_address || d.address || 'Address on file'}</span>
                </div>
            </div>

            <button onclick="updateStatus(${d.id}, 'Claimed')" class="btn-claim" style="background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%); color: white; border: none; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px;">
                <i class="fa-solid fa-recycle"></i> Rescue for ${repurposeCategory.split(' ')[0]}
            </button>
        `;

        grid.appendChild(card);
    });
};

window.filterExpiredGrid = function(subType) {
    const allBtn = document.getElementById('expFilterAll');
    const animalBtn = document.getElementById('expFilterAnimal');
    const compostBtn = document.getElementById('expFilterCompost');

    [allBtn, animalBtn, compostBtn].forEach(b => {
        if (b) b.classList.remove('active');
    });

    if (subType === 'animal' && animalBtn) animalBtn.classList.add('active');
    else if (subType === 'compost' && compostBtn) compostBtn.classList.add('active');
    else if (allBtn) allBtn.classList.add('active');

    const list = window.allExpiredDonations || [];
    let filtered = list;

    if (subType === 'animal') {
        filtered = list.filter(d => {
            const prep = d.preparation_time || d.timestamp;
            if (!prep) return true;
            const diffHrs = (new Date() - new Date(prep)) / (1000 * 60 * 60);
            return diffHrs < 96;
        });
    } else if (subType === 'compost') {
        filtered = list.filter(d => {
            const prep = d.preparation_time || d.timestamp;
            if (!prep) return false;
            const diffHrs = (new Date() - new Date(prep)) / (1000 * 60 * 60);
            return diffHrs >= 96;
        });
    }

    renderExpiredGrid(filtered);
};

window.slideExpiredShelf = function(direction) {
    const track = document.getElementById('expiredSlideTrack');
    if (track) {
        track.scrollBy({ left: direction * 300, behavior: 'smooth' });
    }
};

async function fetchDonations(pageType) {
    const grid = pageType === 'find-food' ? donationGrid : deliveryGrid;

    try {
        const response = await fetch('/api/donations');
        const donations = await response.json();

        // Save globally
        allDonations = donations;

        if (pageType === 'find-food') {
            const fresh = [];
            const expired = [];

            donations.forEach(d => {
                if (isDonationExpired(d)) {
                    expired.push(d);
                } else if (d.status === 'Available') {
                    fresh.push(d);
                }
            });

            // Update badge counters
            const humanCountEl = document.getElementById('humanCountBadge');
            const expiredCountEl = document.getElementById('expiredCountBadge');
            if (humanCountEl) humanCountEl.innerText = fresh.length;
            if (expiredCountEl) expiredCountEl.innerText = expired.length;

            window.allExpiredDonations = expired;

            // 1. Render fresh food strictly in human food section
            renderDonations(fresh, grid, false);

            // 2. Automatically populate and slide expired food into the shelf and grid!
            renderExpiredShelf(expired);
            renderExpiredGrid(expired);

        } else {
            const tasks = donations.filter(d => ['Claimed', 'Pickup Assigned', 'Picked Up'].includes(d.status));
            renderDonations(tasks, grid, true);
        }

    } catch (error) {
        console.error('Error fetching donations:', error);
        if (grid) grid.innerHTML = '<p style="text-align: center;">Failed to load data.</p>';
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
// --- Live Expiry Logic (Human Food Countdown & Auto-Divert) ---
let isAutoDiverting = false;

setInterval(() => {
    document.querySelectorAll('.expiry-cnt').forEach(el => {
        const prepStr = el.getAttribute('data-prep');
        if (!prepStr) return;

        const now = new Date();
        const start = new Date(prepStr);
        if (isNaN(start.getTime())) return;

        // Human Safe Expiry (48 hours from preparation)
        const humanExpiry = new Date(start.getTime() + (48 * 60 * 60 * 1000));
        let diffMs = humanExpiry - now;

        if (diffMs <= 0) {
            el.innerHTML = '<i class="fa-solid fa-arrow-right-arrow-left"></i> Safe Window Ended &bull; Auto-Diverted to Expired Shelf';
            el.className = 'expiry-cnt expired';
            // Auto-refresh find-food if on the page so expired meals migrate automatically!
            if (!isAutoDiverting && document.getElementById('donationGrid')) {
                isAutoDiverting = true;
                setTimeout(() => {
                    isAutoDiverting = false;
                    fetchDonations('find-food');
                }, 1200);
            }
            return;
        }

        const hrs = Math.floor(diffMs / (1000 * 60 * 60));
        const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        const secs = Math.floor((diffMs % (1000 * 60)) / 1000);

        el.innerHTML = `<i class="fa-solid fa-utensils"></i> Safe for Humans: ${hrs}h ${mins}m ${secs}s`;
        el.className = 'expiry-cnt safe';
        if (hrs < 6) el.classList.add('warning');
        if (hrs < 1) el.classList.add('urgent');
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
    .expiry-cnt.expired { background: rgba(239, 68, 68, 0.15); color: #dc2626; font-weight: 700; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);


function renderDonations(data, grid, isDeliveryView) {
    grid.innerHTML = '';

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
                <p>${isDeliveryView ? 'No active deliveries assigned.' : 'No fresh food donations matching this criteria.'}</p>
            </div>
        `;
        return;
    }

    data.forEach(donation => {
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

        let actionButton = '';
        if (!isDeliveryView) {
            actionButton = `
                <div style="display:flex; gap:10px;">
                    <button class="btn-claim" style="flex:1;" onclick="updateStatus(${donation.id}, 'Claimed')"><i class="fa-solid fa-hand-holding-heart"></i> Claim Food</button>
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
            ? `<div class="expiry-cnt" data-prep="${prepTime}">Calculating safe window...</div>`
            : '';

        let emergencyTag = '';
        const desc = donation.instructions || '';
        if (desc.toUpperCase().includes('EMERGENCY')) {
            emergencyTag = `<div style="background: #ef4444; color: white; text-align: center; font-weight: bold; font-size: 0.8rem; padding: 6px; border-radius: 4px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"><i class="fa-solid fa-triangle-exclamation"></i> EMERGENCY DONATION</div>`;
        } else if (desc.toUpperCase().includes('BULK')) {
            emergencyTag = `<div style="background: #f59e0b; color: #1e293b; text-align: center; font-weight: bold; font-size: 0.8rem; padding: 6px; border-radius: 4px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"><i class="fa-solid fa-champagne-glasses"></i> BULK EVENT DONATION</div>`;
        }

        const title = (donation.food_name && donation.food_name !== 'undefined') ? donation.food_name : (donation.food_type || donation.foodType || 'Food').replace('_', ' ').toUpperCase();

        card.innerHTML = `
            ${imageHtml}
            <div class="card-header">
                <div class="food-icon"><i class="fa-solid ${icon}"></i></div>
                <div class="badges">
                    ${dietTypeBadge}
                    <span class="status-badge ${badgeClass}">${donation.status}</span>
                    <span class="status-badge" style="background:#DCFCE7; color:#15803D; font-weight:700;"><i class="fa-solid fa-circle-check"></i> For Humans (Safe)</span>
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
