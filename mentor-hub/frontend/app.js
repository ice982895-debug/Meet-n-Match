const API_URL = "http://localhost:8000/api";

const hero_section = document.getElementById('hero-section');
const form_section = document.getElementById('form-section');
const result_section = document.getElementById('results-section');
const mentor_section = document.getElementById('mentors-section');
const form = document.getElementById('match-form');
const loading_indicator = document.getElementById('loading');
const mentor_grid = document.getElementById('mentors-grid');
const directory_grid = document.getElementById('directory-grid');
const modal = document.getElementById('success-modal');

// State
let selectedTools = new Set();
let selectedInterests = new Set();
let currentPage = 1;

// --- Navigation ---
function showSection(sectionId) {
    // Hide all main sections
    [hero_section, form_section, result_section, mentor_section].forEach(el => {
        el.classList.add('hidden');
    });
    // Show target
    document.getElementById(sectionId).classList.remove('hidden');
    // Hide mobile menu if open
    document.querySelector('.mobile-menu')?.classList.add('hidden');
}

document.getElementById('nav-home').addEventListener('click', (e) => { e.preventDefault(); showSection('hero-section'); });
document.getElementById('nav-mentors').addEventListener('click', (e) => {
    e.preventDefault();
    showSection('mentors-section');
    loadDirectory();
    // Also load meta for the filter dropdown
    fetch(`${API_URL}/meta`).then(r => r.json()).then(d => {
        const select = document.getElementById('filter-role');
        if (select.children.length <= 1) { // Only if not populated
            d.job_titles.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                select.appendChild(opt);
            });
        }
    });
});

// Mobile Nav
const menuToggle = document.querySelector('.menu-toggle');
if (menuToggle) {
    menuToggle.addEventListener('click', () => {
        document.querySelector('.mobile-menu').classList.toggle('hidden');
    });
}
document.getElementById('mob-nav-home')?.addEventListener('click', () => { showSection('hero-section'); });
document.getElementById('mob-nav-mentors')?.addEventListener('click', () => {
    showSection('mentors-section');
    loadDirectory();
});

document.getElementById('cta-btn').addEventListener('click', () => {
    showSection('form-section');
    loadMetadata();
});

document.getElementById('back-btn').addEventListener('click', () => {
    showSection('form-section');
});

// --- Data Loading ---
async function loadMetadata(jobTitle = null) {
    try {
        let url = `${API_URL}/meta`;
        if (jobTitle) {
            url += `?job_title=${encodeURIComponent(jobTitle)}`;
        }

        const res = await fetch(url);
        const data = await res.json();

        // Only repopulate job titles if we are doing the initial load
        if (!jobTitle) {
            populateSelect('job-title', data.job_titles);
        }

        populateTags('tools-container', data.tools, selectedTools);
        populateTags('interests-container', data.interests, selectedInterests);
    } catch (err) {
        console.error("Failed to load metadata:", err);
        // alert("Could not connect to backend. Ensure FastAPI is running!");
    }
}

// Event Listener for Job Title Change
const jobTitleSelect = document.getElementById('job-title');
if (jobTitleSelect) {
    jobTitleSelect.addEventListener('change', (e) => {
        const selectedTitle = e.target.value;
        if (selectedTitle) {
            selectedTools = new Set();
            selectedInterests = new Set();
            loadMetadata(selectedTitle);
        }
    });
}

function populateSelect(elementId, items) {
    const select = document.getElementById(elementId);
    // Keep placeholder content (first child)
    const placeholder = select.firstElementChild;
    select.innerHTML = '';
    select.appendChild(placeholder);

    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        select.appendChild(option);
    });
}

function populateTags(containerId, items, stateSet) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    // Limit to top 30 items for UI cleanliness
    items.slice(0, 30).forEach(item => {
        const wrapper = document.createElement('div');
        const id = `${containerId}-${item.replace(/\s+/g, '-')}`;

        wrapper.innerHTML = `
            <input type="checkbox" id="${id}" value="${item}" class="tag-checkbox">
            <label for="${id}" class="tag-label">${item}</label>
        `;

        container.appendChild(wrapper);

        // Listener
        wrapper.querySelector('input').addEventListener('change', (e) => {
            if (e.target.checked) stateSet.add(e.target.value);
            else stateSet.delete(e.target.value);
        });
    });
}

// --- Form Submission ---
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // UI Updates
    showSection('results-section');
    mentor_grid.innerHTML = '';
    loading_indicator.classList.remove('hidden');

    const payload = {
        job_title: document.getElementById('job-title').value,
        years_of_experience: parseInt(document.getElementById('experience').value),
        tools: Array.from(selectedTools),
        interests: Array.from(selectedInterests),
        bio: document.getElementById('bio').value
    };

    try {
        const res = await fetch(`${API_URL}/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const matches = await res.json();
        renderMatches(matches);
    } catch (err) {
        console.error(err);
        mentor_grid.innerHTML = '<p class="error">Failed to match. Please try again.</p>';
    } finally {
        loading_indicator.classList.add('hidden');
    }
});

function renderMatches(matches) {
    mentor_grid.innerHTML = '';

    if (matches.length === 0) {
        mentor_grid.innerHTML = '<p>No exact matches found. Try broadening your criteria.</p>';
        return;
    }

    matches.forEach(mentor => {
        const card = createMentorCard(mentor, true);
        mentor_grid.appendChild(card);
    });
}

function createMentorCard(mentor, isMatch = false) {
    const card = document.createElement('div');
    card.className = 'mentor-card';

    // Calculate percentage for display if score exists
    let headerAction = '';
    if (isMatch) {
        const percentage = Math.round(mentor.match_score * 100);
        headerAction = `<div class="match-badge">${percentage}% Match</div>`;
    }

    // Tags preview (first 3)
    const visibleTags = [...(mentor.tools || []).slice(0, 2), ...(mentor.interests || []).slice(0, 1)];
    const tagsHtml = visibleTags.map(t => `<span class="mini-tag">${t}</span>`).join('');

    card.innerHTML = `
        <div class="mentor-header">
            <span class="mentor-role">${mentor.job_title}</span>
            <span class="mentor-exp">${mentor.years_of_experience} years exp</span>
            ${headerAction}
        </div>
        
        <p class="mentor-bio">${mentor.bio}</p>
        
        <div class="tags-preview">
            ${tagsHtml}
            ${((mentor.tools?.length || 0) + (mentor.interests?.length || 0)) > 3 ? '<span class="mini-tag">+more</span>' : ''}
        </div>
        
        <button class="btn-outline request-btn">Request Mentorship</button>
    `;

    card.querySelector('.request-btn').addEventListener('click', () => {
        modal.classList.remove('hidden');
    });

    return card;
}

// --- Directory Logic ---
async function loadDirectory() {
    const role = document.getElementById('filter-role').value;
    const tool = document.getElementById('filter-tool').value;
    const interest = document.getElementById('filter-interest').value;

    const loading = document.getElementById('directory-loading');
    loading.classList.remove('hidden');
    directory_grid.innerHTML = '';

    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: 9,
        });
        if (role) params.append('role', role);
        if (tool) params.append('tool', tool);
        if (interest) params.append('interest', interest);

        const res = await fetch(`${API_URL}/mentors?${params.toString()}`);
        const data = await res.json();

        data.data.forEach(mentor => {
            directory_grid.appendChild(createMentorCard(mentor));
        });

        // Update Pagination Info
        document.getElementById('page-info').textContent = `Page ${data.page} of ${data.total_pages}`;
        document.getElementById('prev-page').disabled = data.page <= 1;
        document.getElementById('next-page').disabled = data.page >= data.total_pages;

    } catch (err) {
        console.error("Directory error", err);
    } finally {
        loading.classList.add('hidden');
    }
}

// Initial Listeners for Filters
document.getElementById('apply-filters').addEventListener('click', () => {
    currentPage = 1;
    loadDirectory();
});

document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadDirectory();
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    currentPage++;
    loadDirectory();
});

// Modal Close
document.getElementById('close-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
});
