/**
 * Account Dropdown Component
 * Clean, minimal account dropdown for Story Timeline Builder
 */

document.addEventListener('DOMContentLoaded', function () {
    // Create the dropdown component
    function createAccountDropdown() {
        const container = document.getElementById('account-dropdown-container');
        if (!container) return;

        // Get user data from Django template variables (passed via data attributes)
        const username = container.dataset.username || 'admin';
        const userInitial = container.dataset.userInitial || (username.charAt(0).toUpperCase());
        const userRole = container.dataset.userRole || 'Member';

        // Create the dropdown HTML
        const dropdownHTML = `
            <div class="account-dropdown-wrapper">
                <!-- Popup Card (hidden by default) -->
                <div class="account-dropdown-card" id="accountDropdownCard">
                    <div class="account-label">Account</div>
                    <div class="account-username">${username}</div>
                    <hr class="account-divider">
                    <a href="/account/" class="account-menu-item">
                        <i class="bi bi-person-circle"></i>
                        <span>Account Settings</span>
                    </a>
                    <hr class="account-divider">
                    <form action="/logout/" method="post" class="account-logout-form">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${container.dataset.csrf || getCSRFToken()}">
                        <button type="submit" class="account-menu-item account-logout">
                            <i class="bi bi-box-arrow-right"></i>
                            <span>Sign Out</span>
                        </button>
                    </form>
                </div>
                
                <!-- Bottom Trigger Bar (always visible) -->
                <div class="account-trigger-bar" id="accountTriggerBar">
                    <div class="account-avatar">${userInitial}</div>
                    <div class="account-trigger-info">
                        <div class="account-trigger-username">${username}</div>
                        <div class="account-trigger-role">${userRole}</div>
                    </div>
                    <div class="account-chevron">
                        <i class="bi bi-chevron-down"></i>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = dropdownHTML;

        // Add event listeners
        const triggerBar = document.getElementById('accountTriggerBar');
        const dropdownCard = document.getElementById('accountDropdownCard');

        if (triggerBar && dropdownCard) {
            // Toggle dropdown on trigger bar click
            triggerBar.addEventListener('click', function (e) {
                e.stopPropagation();
                const isVisible = dropdownCard.style.display === 'block';
                dropdownCard.style.display = isVisible ? 'none' : 'block';
                updateChevron(!isVisible);
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', function (e) {
                if (!container.contains(e.target)) {
                    dropdownCard.style.display = 'none';
                    updateChevron(false);
                }
            });

            // Prevent closing when clicking inside dropdown
            dropdownCard.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }
    }

    // Helper function to get CSRF token from DOM as fallback
    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) return csrfToken.value;

        // Try to get from cookie as last resort
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue || '';
    }

    // Update chevron rotation
    function updateChevron(isOpen) {
        const chevron = document.querySelector('.account-chevron i');
        if (chevron) {
            chevron.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }

    // Initialize the dropdown
    createAccountDropdown();
});