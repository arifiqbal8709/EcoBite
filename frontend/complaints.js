/* ==============================================================================
   ECOBITE CENTRALIZED COMPLAINT MANAGEMENT SYSTEM - FRONTEND ENGINE
   ============================================================================== */

window.EcoBiteComplaints = (function() {

    let activePollingInterval = null;
    let currentUserSession = null;

    // Fetch logged in session
    async function initUserSession() {
        try {
            const res = await fetch('/api/me');
            if (res.ok) {
                const data = await res.json();
                if (data.authenticated && data.user) {
                    currentUserSession = data.user;
                }
            }
        } catch (e) {
            console.warn('Session check warning:', e);
        }
    }

    // Category priority calculation preview
    function getCategoryPriority(cat) {
        const criticals = ['Food Safety Complaint', 'Fraud or Suspicious Activity', 'Security Problem'];
        const highs = ['Delivery Delay', 'Pickup Problem', 'OTP Verification Problem'];
        const mediums = ['Food Donation Problem', 'NGO Claim Issue', 'Incorrect Donation Information', 'Account/Login Issue', 'AI Food Scanner Problem', 'Technical Issue'];
        
        if (criticals.includes(cat)) return 'CRITICAL';
        if (highs.includes(cat)) return 'HIGH';
        if (mediums.includes(cat)) return 'MEDIUM';
        return 'LOW';
    }

    // Auto-update priority selector on category change
    function handleCategoryChange(catSelectId, prioritySelectId) {
        const catSelect = document.getElementById(catSelectId);
        const prioSelect = document.getElementById(prioritySelectId);
        if (catSelect && prioSelect) {
            catSelect.addEventListener('change', () => {
                const autoPrio = getCategoryPriority(catSelect.value);
                prioSelect.value = autoPrio;
            });
        }
    }

    // Render Status Badge HTML
    function renderStatusBadge(status) {
        const s = (status || 'OPEN').toUpperCase();
        let cls = 'cmp-badge-open';
        let label = s.replace('_', ' ');

        if (s === 'IN_PROGRESS') { cls = 'cmp-badge-in_progress'; label = 'In Progress'; }
        else if (s === 'WAITING_FOR_USER') { cls = 'cmp-badge-waiting_for_user'; label = 'Waiting for User'; }
        else if (s === 'RESOLVED') { cls = 'cmp-badge-resolved'; label = 'Resolved'; }
        else if (s === 'CLOSED') { cls = 'cmp-badge-closed'; label = 'Closed'; }
        else if (s === 'REOPENED') { cls = 'cmp-badge-reopened'; label = 'Reopened'; }

        return `<span class="cmp-badge ${cls}"><i class="fa-solid fa-circle" style="font-size:0.5rem"></i> ${label}</span>`;
    }

    // Render Priority Badge HTML
    function renderPriorityBadge(priority) {
        const p = (priority || 'MEDIUM').toUpperCase();
        let cls = 'cmp-priority-medium';
        if (p === 'CRITICAL') cls = 'cmp-priority-critical';
        else if (p === 'HIGH') cls = 'cmp-priority-high';
        else if (p === 'LOW') cls = 'cmp-priority-low';

        return `<span class="cmp-priority ${cls}">${p}</span>`;
    }

    // Submit Complaint Form AJAX
    async function submitComplaintForm(event, formId, roleDefault = 'Donor') {
        event.preventDefault();
        const form = document.getElementById(formId);
        if (!form) return;

        const btn = form.querySelector('button[type="submit"]');
        const origBtnHtml = btn ? btn.innerHTML : 'Submit';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Submitting...';
        }

        try {
            const formData = new FormData(form);
            if (!formData.get('user_role')) {
                formData.append('user_role', currentUserSession ? currentUserSession.role : roleDefault);
            }

            const res = await fetch('/api/complaints/submit', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (data.success) {
                alert(`✅ Complaint Registered Successfully!\nTicket Number: ${data.ticket_number}\nPriority: ${data.priority}`);
                form.reset();
                // Refresh complaints list
                loadUserComplaints();
                if (typeof switchTab === 'function') {
                    // Stay on complaints or switch to history list
                }
            } else {
                alert(`❌ Submission Failed: ${data.message}`);
            }
        } catch (err) {
            alert(`❌ Network or Server Error: ${err.message}`);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origBtnHtml;
            }
        }
    }

    // Load User Complaints List (For Donor, NGO, Delivery Dashboards)
    async function loadUserComplaints(containerId = 'userComplaintsListContainer') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            container.innerHTML = `
                <div style="text-align:center; padding: 40px; color: #475569;">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size:2rem; color: #E85D04;"></i>
                    <p style="margin-top: 10px;">Loading your complaint tickets...</p>
                </div>
            `;

            const res = await fetch('/api/complaints/my');
            if (!res.ok) throw new Error('Failed to load tickets');
            const data = await res.json();

            if (!data.complaints || data.complaints.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center; padding: 40px; background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 16px;">
                        <i class="fa-solid fa-headset" style="font-size:2.5rem; color: #E85D04; margin-bottom: 12px;"></i>
                        <h3 style="margin: 0 0 6px 0;">No Complaints Found</h3>
                        <p style="color: #475569; margin: 0;">You haven't submitted any complaints or support tickets yet.</p>
                    </div>
                `;
                return;
            }

            let html = '';
            data.complaints.forEach(c => {
                const dateStr = c.created_at ? new Date(c.created_at).toLocaleString() : '';
                html += `
                    <div class="cmp-ticket-card">
                        <div class="cmp-ticket-header">
                            <div class="cmp-ticket-meta">
                                <strong>${c.short_ticket}</strong> (${c.ticket_number}) • <span style="color:#1B3022;">${c.category}</span>
                            </div>
                            <div>
                                ${renderPriorityBadge(c.priority)}
                                ${renderStatusBadge(c.status)}
                            </div>
                        </div>
                        <h3 class="cmp-ticket-title">${escapeHtml(c.subject)}</h3>
                        <p style="color: #475569; font-size: 0.92rem; margin: 0 0 12px 0;">${escapeHtml(c.description.substring(0, 140))}${c.description.length > 140 ? '...' : ''}</p>
                        <div class="cmp-ticket-footer">
                            <span><i class="fa-regular fa-clock"></i> Submitted: ${dateStr}</span>
                            <button class="btn-cmp-view" onclick="EcoBiteComplaints.openTicketModal(${c.id})">
                                <i class="fa-solid fa-comments"></i> View Details & Replies (${c.reply_count || 0})
                            </button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

        } catch (e) {
            container.innerHTML = `<div style="color:red; padding: 20px;">Failed to load complaints: ${e.message}</div>`;
        }
    }

    // Open Complaint Ticket Modal (User & Admin Ticket Detail Drawer)
    async function openTicketModal(complaintId, isAdminView = false) {
        let modal = document.getElementById('cmpTicketModal');
        if (!modal) {
            // Dynamically inject modal container if missing
            modal = document.createElement('div');
            modal.id = 'cmpTicketModal';
            modal.className = 'cmp-modal-overlay';
            modal.innerHTML = `
                <div class="cmp-modal-box">
                    <div class="cmp-modal-header">
                        <h2 id="cmpModalTitle">Support Ticket Details</h2>
                        <button class="cmp-modal-close" onclick="EcoBiteComplaints.closeTicketModal()"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div class="cmp-modal-body" id="cmpModalBody">
                        <div style="text-align:center; padding: 30px;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        modal.classList.add('active');
        const modalBody = document.getElementById('cmpModalBody');
        modalBody.innerHTML = `<div style="text-align:center; padding: 40px; color:#E85D04;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p>Loading ticket discussion...</p></div>`;

        try {
            const res = await fetch(`/api/complaints/${complaintId}`);
            if (!res.ok) throw new Error('Ticket not found or permission denied');
            const data = await res.json();

            const c = data.complaint;
            const replies = data.replies || [];
            const history = data.history || [];

            // Build Timeline Steps
            const isSubmitted = true;
            const isReviewing = ['IN_PROGRESS', 'WAITING_FOR_USER', 'RESOLVED', 'CLOSED'].includes(c.status);
            const isActionReq = c.status === 'WAITING_FOR_USER';
            const isResolved = ['RESOLVED', 'CLOSED'].includes(c.status);

            let timelineHtml = `
                <div class="cmp-timeline-wrapper">
                    <div class="cmp-timeline-steps">
                        <div class="cmp-timeline-step completed">
                            <div class="cmp-timeline-icon"><i class="fa-solid fa-check"></i></div>
                            <div class="cmp-timeline-label">Submitted</div>
                        </div>
                        <div class="cmp-timeline-step ${isReviewing ? (isResolved ? 'completed' : 'active') : ''}">
                            <div class="cmp-timeline-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
                            <div class="cmp-timeline-label">Under Review</div>
                        </div>
                        <div class="cmp-timeline-step ${isActionReq ? 'active' : (isResolved ? 'completed' : '')}">
                            <div class="cmp-timeline-icon"><i class="fa-solid fa-comments"></i></div>
                            <div class="cmp-timeline-label">${isActionReq ? 'Action Required' : 'In Discussion'}</div>
                        </div>
                        <div class="cmp-timeline-step ${isResolved ? 'completed' : ''}">
                            <div class="cmp-timeline-icon"><i class="fa-solid fa-shield-halved"></i></div>
                            <div class="cmp-timeline-label">Resolved</div>
                        </div>
                    </div>
                </div>
            `;

            // Build Conversation Thread
            let threadHtml = '';
            if (replies.length === 0) {
                threadHtml = `<div style="text-align:center; color:#64748B; padding:16px; font-style:italic;">No replies yet. Admin will respond shortly.</div>`;
            } else {
                replies.forEach(r => {
                    const isInternal = r.is_internal_note == 1;
                    let msgClass = r.sender_role.toLowerCase() === 'admin' ? 'cmp-msg-admin' : 'cmp-msg-user';
                    if (isInternal) msgClass = 'cmp-msg-internal';

                    threadHtml += `
                        <div class="cmp-chat-msg ${msgClass}">
                            <div class="cmp-msg-meta">
                                <strong>${r.sender_name} (${r.sender_role}) ${isInternal ? '🔒 INTERNAL NOTE' : ''}</strong>
                                <span>${new Date(r.created_at).toLocaleString()}</span>
                            </div>
                            <div>${escapeHtml(r.message)}</div>
                            ${r.attachment_path ? `<div style="margin-top:8px;"><a href="/${r.attachment_path}" target="_blank" style="color:inherit; font-weight:700;"><i class="fa-solid fa-paperclip"></i> View Attached Evidence</a></div>` : ''}
                        </div>
                    `;
                });
            }

            // Build Attachment View
            let attachmentHtml = '';
            if (c.attachment_path) {
                attachmentHtml = `
                    <div style="margin-top:14px; padding:12px; background:#FAF7F2; border-radius:10px; border:1px solid #EAE5DE;">
                        <strong><i class="fa-solid fa-image"></i> Uploaded Evidence:</strong><br>
                        <a href="/${c.attachment_path}" target="_blank">
                            <img src="/${c.attachment_path}" alt="Complaint Evidence" style="max-width:220px; max-height:160px; border-radius:8px; margin-top:6px; border:1px solid #CBD5E1;">
                        </a>
                    </div>
                `;
            }

            // Admin Control Panel (If viewing in admin context)
            let adminControls = '';
            if (isAdminView) {
                adminControls = `
                    <div style="background:#FAF7F2; padding:16px; border-radius:12px; margin-top:20px; border:1px solid #EAE5DE;">
                        <h4 style="margin:0 0 10px 0; color:#1B3022;"><i class="fa-solid fa-sliders"></i> Admin Control Actions</h4>
                        <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
                            <label style="font-weight:600; font-size:0.88rem;">Status:</label>
                            <select id="adminStatusSelect_${c.id}" style="padding:6px 10px; border-radius:6px; border:1px solid #CBD5E1;">
                                <option value="OPEN" ${c.status === 'OPEN' ? 'selected' : ''}>OPEN</option>
                                <option value="IN_PROGRESS" ${c.status === 'IN_PROGRESS' ? 'selected' : ''}>IN_PROGRESS</option>
                                <option value="WAITING_FOR_USER" ${c.status === 'WAITING_FOR_USER' ? 'selected' : ''}>WAITING_FOR_USER</option>
                                <option value="RESOLVED" ${c.status === 'RESOLVED' ? 'selected' : ''}>RESOLVED</option>
                                <option value="CLOSED" ${c.status === 'CLOSED' ? 'selected' : ''}>CLOSED</option>
                                <option value="REOPENED" ${c.status === 'REOPENED' ? 'selected' : ''}>REOPENED</option>
                            </select>

                            <label style="font-weight:600; font-size:0.88rem;">Priority:</label>
                            <select id="adminPrioritySelect_${c.id}" style="padding:6px 10px; border-radius:6px; border:1px solid #CBD5E1;">
                                <option value="LOW" ${c.priority === 'LOW' ? 'selected' : ''}>LOW</option>
                                <option value="MEDIUM" ${c.priority === 'MEDIUM' ? 'selected' : ''}>MEDIUM</option>
                                <option value="HIGH" ${c.priority === 'HIGH' ? 'selected' : ''}>HIGH</option>
                                <option value="CRITICAL" ${c.priority === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
                            </select>

                            <button class="btn-cmp-submit" style="padding:6px 14px; font-size:0.85rem;" onclick="EcoBiteComplaints.updateAdminStatus(${c.id})">
                                Update Status & Priority
                            </button>
                        </div>
                    </div>
                `;
            }

            // Reopen Option for Users if Resolved/Closed
            let reopenHtml = '';
            if (!isAdminView && ['RESOLVED', 'CLOSED'].includes(c.status)) {
                reopenHtml = `
                    <div style="background:#FFF5F5; border:1px solid #FEB2B2; padding:14px; border-radius:12px; margin-top:16px;">
                        <p style="margin:0 0 8px 0; font-weight:600; color:#9B2C2C;">Is your issue still not resolved?</p>
                        <button class="btn-cmp-submit" style="background:#E53E3E;" onclick="EcoBiteComplaints.reopenTicketPrompt(${c.id})">
                            <i class="fa-solid fa-rotate-left"></i> Reopen Complaint Ticket
                        </button>
                    </div>
                `;
            }

            modalBody.innerHTML = `
                <div style="margin-bottom: 18px; display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div>
                        <h3 style="margin:0 0 4px 0; font-size:1.2rem; color:#1C2520;">${escapeHtml(c.subject)}</h3>
                        <span style="color:#475569; font-size:0.9rem;">Ticket #${c.ticket_number} (${c.short_ticket}) • Category: <strong>${c.category}</strong></span>
                    </div>
                    <div>
                        ${renderPriorityBadge(c.priority)}
                        ${renderStatusBadge(c.status)}
                    </div>
                </div>

                <div style="background:#FAF7F2; padding:14px 18px; border-radius:12px; border:1px solid #EAE5DE; margin-bottom:18px;">
                    <strong>Complainant:</strong> ${c.full_name} (${c.user_role}) • ${c.email} ${c.phone ? '• ' + c.phone : ''}<br>
                    <strong>Description:</strong> ${escapeHtml(c.description)}
                    ${c.related_donation_id ? `<br><strong>Related Donation ID:</strong> #${c.related_donation_id}` : ''}
                    ${c.related_delivery_id ? `<br><strong>Related Delivery ID:</strong> #${c.related_delivery_id}` : ''}
                    ${attachmentHtml}
                </div>

                ${timelineHtml}

                <h4 style="margin: 0 0 10px 0; color:#1B3022;"><i class="fa-solid fa-comments"></i> Support Conversation</h4>
                <div class="cmp-chat-thread" id="chatThreadBox">
                    ${threadHtml}
                </div>

                <!-- Reply Input Form -->
                <form id="ticketReplyForm_${c.id}" onsubmit="EcoBiteComplaints.submitReply(event, ${c.id}, ${isAdminView})" style="margin-top:14px;">
                    <div style="display:flex; gap:10px; margin-bottom:8px;">
                        <textarea name="message" rows="3" placeholder="Type your reply message..." required style="width:100%; padding:10px; border-radius:8px; border:1px solid #EAE5DE; font-family:inherit;"></textarea>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <input type="file" name="attachment" accept="image/*" style="font-size:0.85rem;">
                        
                        <div style="display:flex; gap:10px; align-items:center;">
                            ${isAdminView ? `
                                <label style="font-size:0.85rem; font-weight:600; cursor:pointer;">
                                    <input type="checkbox" name="is_internal_note" value="1"> Internal Admin Note
                                </label>
                            ` : ''}
                            <button type="submit" class="btn-cmp-submit">
                                <i class="fa-solid fa-paper-plane"></i> Send Reply
                            </button>
                        </div>
                    </div>
                </form>

                ${adminControls}
                ${reopenHtml}
            `;

            // Scroll chat to bottom
            const chatBox = document.getElementById('chatThreadBox');
            if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

        } catch (err) {
            modalBody.innerHTML = `<div style="color:red; padding:20px;">Failed to load ticket details: ${err.message}</div>`;
        }
    }

    function closeTicketModal() {
        const modal = document.getElementById('cmpTicketModal');
        if (modal) modal.classList.remove('active');
    }

    // Submit Reply AJAX
    async function submitReply(event, complaintId, isAdminView) {
        event.preventDefault();
        const form = document.getElementById(`ticketReplyForm_${complaintId}`);
        if (!form) return;

        const formData = new FormData(form);

        try {
            const res = await fetch(`/api/complaints/${complaintId}/reply`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                // Re-open ticket modal to reflect fresh message
                openTicketModal(complaintId, isAdminView);
                // Refresh list in background
                if (isAdminView) loadAdminComplaints();
                else loadUserComplaints();
            } else {
                alert(`Error sending reply: ${data.message}`);
            }
        } catch (e) {
            alert(`Error: ${e.message}`);
        }
    }

    // Admin status & priority update AJAX
    async function updateAdminStatus(complaintId) {
        const statSelect = document.getElementById(`adminStatusSelect_${complaintId}`);
        const prioSelect = document.getElementById(`adminPrioritySelect_${complaintId}`);
        if (!statSelect || !prioSelect) return;

        const newStatus = statSelect.value;
        const newPriority = prioSelect.value;

        try {
            const res = await fetch(`/api/admin/complaints/${complaintId}/update-status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: newStatus,
                    priority: newPriority,
                    notes: `Status changed to ${newStatus}, Priority set to ${newPriority}`
                })
            });

            const data = await res.json();
            if (data.success) {
                alert(data.message);
                openTicketModal(complaintId, true);
                loadAdminComplaints();
            } else {
                alert(`Failed: ${data.message}`);
            }
        } catch (e) {
            alert(`Error: ${e.message}`);
        }
    }

    // Reopen Ticket Prompt for User
    async function reopenTicketPrompt(complaintId) {
        const reason = prompt('Please describe why you are reopening this complaint:', 'Issue is still occurring.');
        if (!reason) return;

        try {
            const res = await fetch(`/api/complaints/${complaintId}/reopen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason })
            });

            const data = await res.json();
            if (data.success) {
                alert('Ticket reopened successfully! Support team has been notified.');
                openTicketModal(complaintId, false);
                loadUserComplaints();
            } else {
                alert(`Reopen failed: ${data.message}`);
            }
        } catch (e) {
            alert(`Error: ${e.message}`);
        }
    }

    // ADMIN DASHBOARD COMPLAINT CENTER (Matches Reference Image!)
    async function loadAdminComplaints() {
        const container = document.getElementById('adminComplaintsTableContainer');
        if (!container) return;

        const searchVal = document.getElementById('adminCmpSearch') ? document.getElementById('adminCmpSearch').value : '';
        const roleVal = document.getElementById('adminCmpRole') ? document.getElementById('adminCmpRole').value : 'all';
        const statusVal = document.getElementById('adminCmpStatus') ? document.getElementById('adminCmpStatus').value : 'all';
        const priorityVal = document.getElementById('adminCmpPriority') ? document.getElementById('adminCmpPriority').value : 'all';

        try {
            const query = `?search=${encodeURIComponent(searchVal)}&role=${encodeURIComponent(roleVal)}&status=${encodeURIComponent(statusVal)}&priority=${encodeURIComponent(priorityVal)}`;
            const res = await fetch(`/api/admin/complaints${query}`);
            if (!res.ok) throw new Error('Failed to load admin complaints');
            const data = await res.json();

            // Update real summary stat counts
            if (data.stats) {
                if (document.getElementById('cmpStatTotal')) document.getElementById('cmpStatTotal').innerText = data.stats.total || 0;
                if (document.getElementById('cmpStatNew')) document.getElementById('cmpStatNew').innerText = data.stats.new || 0;
                if (document.getElementById('cmpStatInProgress')) document.getElementById('cmpStatInProgress').innerText = data.stats.in_progress || 0;
                if (document.getElementById('cmpStatWaitingUser')) document.getElementById('cmpStatWaitingUser').innerText = data.stats.waiting_user || 0;
                if (document.getElementById('cmpStatResolved')) document.getElementById('cmpStatResolved').innerText = data.stats.resolved || 0;
                if (document.getElementById('cmpStatReopened')) document.getElementById('cmpStatReopened').innerText = data.stats.reopened || 0;
                if (document.getElementById('cmpStatCritical')) document.getElementById('cmpStatCritical').innerText = data.stats.critical || 0;
            }

            if (!data.complaints || data.complaints.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center; padding: 40px; background: #FFFFFF; border-radius: 12px; color: #64748B;">
                        <i class="fa-solid fa-folder-open" style="font-size: 2.2rem; color: #E85D04; margin-bottom: 10px;"></i>
                        <p style="margin:0;">No complaints match the current filter criteria.</p>
                    </div>
                `;
                return;
            }

            // Render Complaint Cards matching the user's uploaded reference UI!
            let html = '';
            data.complaints.forEach(c => {
                const dateStr = c.created_at ? new Date(c.created_at).toLocaleDateString() : '';
                html += `
                    <div class="cmp-ticket-card" style="background: #FFFFFF;">
                        <div class="cmp-ticket-header">
                            <div class="cmp-ticket-meta">
                                <strong>${c.short_ticket}</strong> (${c.ticket_number}) • <span style="color:#E85D04; font-weight:700;">${c.user_role}</span> • ${c.full_name} (${c.email})
                            </div>
                            <div>
                                ${renderPriorityBadge(c.priority)}
                                ${renderStatusBadge(c.status)}
                            </div>
                        </div>
                        <h3 class="cmp-ticket-title">${escapeHtml(c.subject)}</h3>
                        <p style="color: #475569; font-size: 0.92rem; margin: 0 0 12px 0;">${escapeHtml(c.description)}</p>
                        <div class="cmp-ticket-footer">
                            <span>Category: <strong>${c.category}</strong> • ${dateStr}</span>
                            <button class="btn-cmp-view" onclick="EcoBiteComplaints.openTicketModal(${c.id}, true)">
                                <i class="fa-regular fa-comment-dots"></i> View & Reply
                            </button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

        } catch (e) {
            container.innerHTML = `<div style="color:red; padding:20px;">Error loading complaints: ${e.message}</div>`;
        }
    }

    function exportComplaintsCSV() {
        window.location.href = '/api/admin/complaints/export';
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Start auto polling for complaints update
    function startPolling(userRole = 'user') {
        if (activePollingInterval) clearInterval(activePollingInterval);
        activePollingInterval = setInterval(() => {
            if (userRole === 'admin') {
                loadAdminComplaints();
            } else {
                loadUserComplaints();
            }
        }, 8000); // 8-second refresh
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
        initUserSession();
    });

    return {
        initUserSession,
        handleCategoryChange,
        submitComplaintForm,
        loadUserComplaints,
        loadAdminComplaints,
        openTicketModal,
        closeTicketModal,
        submitReply,
        updateAdminStatus,
        reopenTicketPrompt,
        exportComplaintsCSV,
        startPolling
    };

})();
