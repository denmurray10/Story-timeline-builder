import sys

content = """{% extends 'timeline/base.html' %}
{% load static %}
{% block title %}{{ character.name }} - Character Profile{% endblock %}

{% block extra_css %}
<style>
    :root {
        --char-accent: {{ character.color_code|default:"#6366f1" }};
    }
    
    .font-dm-serif {
        font-family: 'DM Serif Display', serif;
    }

    .tracking-widest { letter-spacing: 0.1em; }
    .uppercase { text-transform: uppercase; }

    .card-premium {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease-in-out;
        height: 100%;
        margin-bottom: 0;
    }
    .card-premium:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    
    .card-header-premium {
        background: transparent;
        border-bottom: 1px solid #f1f5f9;
        padding: 1.25rem 1.5rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .trait-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #94a3b8;
        display: block;
        margin-bottom: 0.25rem;
    }

    .form-control-premium {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-size: 0.9rem;
        padding: 0.5rem 0.75rem;
        background-color: #f8fafc;
        width: 100%;
        color: #1e293b;
        transition: all 0.2s;
    }
    .form-control-premium:focus {
        border-color: #6366f1;
        outline: none;
        background-color: #ffffff;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    textarea.form-control-premium {
        min-height: 100px;
        background-color: #ffffff;
        border-style: dashed;
    }
    textarea.form-control-premium:focus {
        border-style: solid;
    }

    .portrait-container {
        aspect-ratio: 4/5;
        border-radius: 12px;
        background-color: #f1f5f9;
        position: relative;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        cursor: pointer;
    }
    .portrait-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .portrait-overlay {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.5);
        color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.2s;
        border: 2px dashed rgba(255,255,255,0.5);
        border-radius: 12px;
    }
    .portrait-container:hover .portrait-overlay {
        opacity: 1;
    }

    .btn-action {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 999px;
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #475569;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.2s;
    }
    .btn-action:hover {
        background: #f8fafc;
        color: #0f172a;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .btn-action-primary {
        background: #0f172a;
        color: white;
        border-color: #0f172a;
    }
    .btn-action-primary:hover {
        background: #1e293b;
        color: white;
    }
    
    .timeline-pill {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.8rem;
        flex-shrink: 0;
        border: 2px solid #f1f5f9;
        background: white;
        color: #94a3b8;
        position: relative;
        z-index: 2;
    }
    .timeline-pill.written {
        background: #0f172a;
        color: white;
        border-color: #0f172a;
    }
    .timeline-event {
        position: relative;
        padding-bottom: 2rem;
    }
    .timeline-line {
        position: absolute;
        left: 15px;
        top: 32px;
        bottom: 0;
        width: 2px;
        background: #f1f5f9;
        z-index: 1;
    }
    .timeline-event:last-child .timeline-line {
        display: none;
    }

    .rel-node {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid white;
        background-size: cover;
        background-position: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
    }
    .rel-node:hover {
        transform: scale(1.1);
    }
    
    .form-switch .form-check-input {
        width: 2.5em;
        height: 1.25em;
    }

    .avatar-option {
        cursor: pointer;
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 4px;
        transition: all 0.2s;
        aspect-ratio: 1;
    }
    .avatar-option img {
        width: 100%;
        height: 100%;
        border-radius: 8px;
    }
    .avatar-option.selected {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.1);
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid pb-5">
    
    <!-- Header Row -->
    <div class="row align-items-end mb-4 pb-3 border-bottom">
        <div class="col-md-7">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-2" style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
                    <li class="breadcrumb-item"><a href="{% url 'character_list' %}" class="text-decoration-none text-muted hover-primary">Characters</a></li>
                    <li class="breadcrumb-item active text-dark" aria-current="page">Profile</li>
                </ol>
            </nav>
            <h1 class="font-dm-serif display-4 fw-bold text-dark mb-2" style="line-height: 1;">{{ character.name }}</h1>
            <div class="d-flex align-items-center gap-3">
                <span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 uppercase tracking-widest py-2 px-3">
                    {{ character.get_role_display }}
                </span>
                <span class="text-muted" style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">
                    Introduced In: <strong class="text-dark">{{ character.introduction_book.title|default:"Unknown Book" }}</strong>
                </span>
            </div>
        </div>
        <div class="col-md-5 mt-4 mt-md-0 d-flex flex-wrap justify-content-md-end gap-2">
            <button type="button" id="syncCharacterBtn" class="btn-action">
                <i class="bi bi-arrow-repeat fs-6"></i> Sync AI
            </button>
            <button type="button" id="deepDiveBtn" class="btn-action">
                <i class="bi bi-magic fs-6 text-primary"></i> Deep Dive
            </button>
            <button type="submit" form="main-character-form" class="btn-action btn-action-primary">
                <i class="bi bi-floppy fs-6"></i> Save Changes
            </button>
        </div>
    </div>

    <!-- Main Form -->
    <form id="main-character-form" method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <div class="d-none">
            {{ form.profile_image }}
            {{ form.avatar_id }}
        </div>

        <div class="row g-4">
            
            <!-- COLUMN 1: Visual Identity & Physicals -->
            <div class="col-lg-3">
                <div class="card-premium">
                    <div class="card-header-premium border-bottom-0 pb-0">
                        <i class="bi bi-person-bounding-box text-muted"></i> Identity
                    </div>
                    <div class="card-body p-4 pt-3 flex-grow-0">
                        
                        <!-- Portrait Container -->
                        <div class="portrait-container border shadow-sm mb-4" onclick="document.getElementById('{{ form.profile_image.id_for_label }}').click()">
                            {% if character.profile_pic_url %}
                            <img src="{{ character.profile_pic_url }}" id="profilePreview" class="portrait-img">
                            {% else %}
                            <div id="profilePlaceholder" class="w-100 h-100 d-flex flex-column align-items-center justify-content-center text-muted bg-light">
                                <i class="bi bi-person fs-1 opacity-50"></i>
                                <span class="uppercase tracking-widest mt-2" style="font-size: 0.65rem; font-weight: 700;">No Photo</span>
                            </div>
                            {% endif %}
                            
                            <button type="button" id="generatePortraitBtn" class="btn btn-light rounded-circle shadow-sm position-absolute" style="bottom: 10px; right: 10px; width: 36px; height: 36px; padding: 0; z-index: 10;" title="Generate AI Portrait" onclick="event.stopPropagation(); generatePortraitCall();">
                                <i class="bi bi-magic text-primary"></i>
                            </button>
                            
                            <div class="portrait-overlay">
                                <i class="bi bi-upload fs-2 mb-2"></i>
                                <span class="uppercase tracking-widest fw-bold" style="font-size: 0.7rem;">Upload Image</span>
                            </div>
                        </div>

                        <!-- Physical Specs -->
                        <h6 class="uppercase tracking-widest text-muted border-bottom pb-2 mb-3" style="font-size: 0.65rem; font-weight: 800;">Physical Attributes</h6>
                        <div class="row g-2 mb-4">
                            <div class="col-6">
                                <label class="trait-label">Age</label>
                                <input type="text" name="age" class="form-control-premium" value="{{ form.age.value|default_if_none:'' }}">
                            </div>
                            <div class="col-6">
                                <label class="trait-label">Height</label>
                                <input type="text" name="height" class="form-control-premium" value="{{ form.height.value|default_if_none:'' }}">
                            </div>
                            <div class="col-6">
                                <label class="trait-label">Eyes</label>
                                <input type="text" name="eyes" class="form-control-premium" value="{{ form.eyes.value|default_if_none:'' }}">
                            </div>
                            <div class="col-6">
                                <label class="trait-label">Hair</label>
                                <input type="text" name="hair" class="form-control-premium" value="{{ form.hair.value|default_if_none:'' }}">
                            </div>
                        </div>
                        
                        <!-- Avatars -->
                        <h6 class="uppercase tracking-widest text-muted border-bottom pb-2 mb-3 mt-2" style="font-size: 0.65rem; font-weight: 800;">Default Avatars</h6>
                        <div class="row g-2 mb-4" id="avatar-selector">
                            <div class="col-3"><div class="avatar-option {% if character.avatar_id == 'hero' %}selected{% endif %}" data-id="hero"><img src="{% static 'img/avatars/hero.svg' %}"></div></div>
                            <div class="col-3"><div class="avatar-option {% if character.avatar_id == 'villain' %}selected{% endif %}" data-id="villain"><img src="{% static 'img/avatars/villain.svg' %}"></div></div>
                            <div class="col-3"><div class="avatar-option {% if character.avatar_id == 'sage' %}selected{% endif %}" data-id="sage"><img src="{% static 'img/avatars/sage.svg' %}"></div></div>
                            <div class="col-3"><div class="avatar-option {% if character.avatar_id == 'rogue' %}selected{% endif %}" data-id="rogue"><img src="{% static 'img/avatars/rogue.svg' %}"></div></div>
                        </div>

                        <!-- Brand Colour -->
                        <label class="trait-label">Theme Tint</label>
                        <div class="d-flex align-items-center gap-2">
                            <input type="color" name="color_code" class="form-control form-control-color border-0 p-1" value="{{ form.color_code.value|default:'#6366f1' }}" style="height: 35px; width: 45px; border-radius: 8px;">
                            <span class="text-muted" style="font-size: 0.7rem;">Timeline color representation</span>
                        </div>

                    </div>
                    
                    <div class="card-footer bg-light border-top p-4">
                        <div class="d-flex align-items-center gap-3">
                            <div class="form-check form-switch m-0">
                                <input class="form-check-input" type="checkbox" role="switch" name="is_active" id="id_is_active" {% if form.is_active.value %}checked{% endif %}>
                                <label class="form-check-label fw-bold ms-2" for="id_is_active" style="font-size: 0.85rem;">Active character</label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- COLUMN 2: Psychology & Story -->
            <div class="col-lg-5">
                <div class="d-flex flex-column gap-4 h-100">
                    
                    <!-- Relationships Panel -->
                    <div class="card-premium">
                        <div class="card-header-premium flex-wrap justify-content-between">
                            <div class="d-flex align-items-center gap-2">
                                <i class="bi bi-bezier2 text-muted"></i> Social Dynamics
                            </div>
                            <a href="{% url 'relationship_map' %}" class="text-decoration-none text-primary" style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">
                                View Map <i class="bi bi-box-arrow-up-right"></i>
                            </a>
                        </div>
                        <div class="card-body p-0 position-relative overflow-hidden" style="min-height: 250px; background: #fafafa;">
                            <!-- Simplified Map Mockup -->
                            <svg class="position-absolute w-100 h-100" style="z-index: 0; opacity: 0.3;">
                                {% for rel in relationships %}
                                <line x1="50%" y1="50%" x2="{% cycle '20%' '80%' '50%' %}" y2="{% cycle '20%' '20%' '80%' %}" stroke="{{ rel.get_color_code }}" stroke-width="2" />
                                {% endfor %}
                            </svg>
                            <div class="d-flex align-items-center justify-content-center h-100 position-absolute w-100" style="z-index: 10;">
                                <!-- Primary Node -->
                                <div class="d-flex flex-column align-items-center me-4">
                                    <div class="rel-node shadow-lg border-opacity-50" style="width: 72px; height: 72px; border-width: 4px; border-color: white; background-image: url('{{ character.profile_pic_url }}');">
                                        {% if not character.profile_pic_url %}<div class="w-100 h-100 bg-primary bg-opacity-10 d-flex align-items-center justify-content-center rounded-circle"><i class="bi bi-person text-primary"></i></div>{% endif %}
                                    </div>
                                    <span class="badge bg-white text-dark shadow-sm border mt-n2 rounded-pill px-3" style="z-index: 5;">You</span>
                                </div>
                                
                                <!-- Contacts -->
                                <div class="position-absolute w-100 h-100" style="pointer-events: none;">
                                    {% for rel in relationships|slice:":3" %}
                                    {% with other=rel.character_a %}
                                    {% if other == character %}{% with other=rel.character_b %}{% endwith %}{% endif %}
                                    <div class="position-absolute d-flex flex-column align-items-center" style="left: {% cycle '20%' '75%' '50%' %}; top: {% cycle '25%' '30%' '80%' %}; pointer-events: auto;">
                                        <div class="rel-node border-light" style="background-image: url('{{ other.profile_pic_url }}');">
                                            {% if not other.profile_pic_url %}<div class="w-100 h-100 bg-light d-flex align-items-center justify-content-center rounded-circle"><i class="bi bi-person text-muted"></i></div>{% endif %}
                                        </div>
                                        <span class="badge bg-white bg-opacity-75 text-dark border shadow-sm mt-1 px-2" style="font-size: 0.6rem;">{{ other.name|truncatechars:12 }}</span>
                                    </div>
                                    {% endwith %}
                                    {% endfor %}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Psychology -->
                    <div class="card-premium">
                        <div class="card-header-premium">
                            <i class="bi bi-heart-pulse text-muted"></i> Deep Psychology
                        </div>
                        <div class="card-body p-4">
                            <div class="row g-4">
                                <div class="col-md-6 border-end">
                                    <div class="d-flex align-items-center gap-2 mb-2">
                                        <i class="bi bi-star-fill text-warning"></i>
                                        <label class="trait-label m-0 text-dark">Core Desire</label>
                                    </div>
                                    <textarea name="core_desire" class="form-control-premium" style="min-height: 80px;" placeholder="What does they want most?">{{ form.core_desire.value|default_if_none:'' }}</textarea>
                                </div>
                                <div class="col-md-6">
                                    <div class="d-flex align-items-center gap-2 mb-2">
                                        <i class="bi bi-virus text-danger"></i>
                                        <label class="trait-label m-0 text-dark">Fatal Flaw</label>
                                    </div>
                                    <textarea name="fatal_flaw" class="form-control-premium" style="min-height: 80px;" placeholder="What weakness will be their downfall?">{{ form.fatal_flaw.value|default_if_none:'' }}</textarea>
                                </div>
                                <div class="col-12 mt-4 pt-4 border-top">
                                    <label class="trait-label text-dark mb-2"><i class="bi bi-journal-text text-primary me-2"></i> Bio / General Description</label>
                                    <textarea name="description" class="form-control-premium" style="min-height: 150px;">{{ form.description.value|default_if_none:'' }}</textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                </div>
            </div>

            <!-- COLUMN 3: Plot Integration & Timeline -->
            <div class="col-lg-4">
                <div class="d-flex flex-column gap-4 h-100">
                    
                    <!-- System Details -->
                    <div class="card-premium" style="background: #0f172a;">
                        <div class="card-body p-4 text-white">
                            <h6 class="uppercase tracking-widest text-secondary border-bottom border-secondary border-opacity-25 pb-3 mb-4" style="font-size: 0.7rem; font-weight: 800;">System Attributes</h6>
                            
                            <div class="d-flex flex-column gap-3">
                                <div>
                                    <label class="trait-label text-secondary mb-1">Archetype Role</label>
                                    <select name="role" class="form-select bg-dark text-white border-secondary border-opacity-50" style="font-size: 0.9rem;">
                                        {% for choice in form.role.field.choices %}
                                        <option value="{{ choice.0 }}" {% if form.role.value == choice.0 %}selected{% endif %}>{{ choice.1 }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <div class="row g-2">
                                    <div class="col-6">
                                        <label class="trait-label text-secondary mb-1">Debut Book</label>
                                        <select name="introduction_book" class="form-select bg-dark text-white border-secondary border-opacity-50 px-2 py-1" style="font-size: 0.8rem;">
                                            {% for choice in form.introduction_book.field.choices %}
                                            <option value="{{ choice.0 }}" {% if form.introduction_book.value == choice.0|stringformat:"i" or form.introduction_book.value == choice.0 %}selected{% endif %}>{{ choice.1 }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>
                                    <div class="col-6">
                                        <label class="trait-label text-secondary mb-1">Debut Chapter</label>
                                        <select name="introduction_chapter" class="form-select bg-dark text-white border-secondary border-opacity-50 px-2 py-1" style="font-size: 0.8rem;">
                                            {% for choice in form.introduction_chapter.field.choices %}
                                            <option value="{{ choice.0 }}" {% if form.introduction_chapter.value == choice.0|stringformat:"i" or form.introduction_chapter.value == choice.0 %}selected{% endif %}>{{ choice.1 }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Events Timeline -->
                    <div class="card-premium flex-grow-1">
                        <div class="card-header-premium bg-light">
                            <i class="bi bi-clock-history text-muted"></i> Story Timeline Context
                        </div>
                        <div class="card-body p-4 overflow-auto" style="max-height: 500px;">
                            
                            {% if events %}
                                {% for event in events %}
                                <div class="timeline-event d-flex gap-3">
                                    <div class="timeline-line"></div>
                                    <div class="timeline-pill {% if event.is_written %}written{% endif %} shadow-sm">
                                        {{ forloop.counter }}
                                    </div>
                                    <div class="flex-grow-1 bg-white border rounded-3 p-3 shadow-sm hover-shadow-lg transition">
                                        <div class="d-flex justify-content-between align-items-start mb-2">
                                            <h6 class="m-0 fw-bold text-dark" style="font-size: 0.9rem;">{{ event.title|truncatechars:35 }}</h6>
                                            <span class="badge bg-light text-muted border" style="font-size: 0.65rem;">CH {% if event.chapter %}{{ event.chapter.chapter_number }}{% else %}-{% endif %}</span>
                                        </div>
                                        <p class="text-muted m-0" style="font-size: 0.8rem; line-height: 1.4;">{{ event.description|truncatechars:70 }}</p>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="text-center py-5 text-muted">
                                    <i class="bi bi-calendar-x fs-1 opacity-25 mb-3 d-block"></i>
                                    <span class="uppercase tracking-widest fw-bold" style="font-size: 0.7rem;">Not assigned to any plot events</span>
                                </div>
                            {% endif %}
                            
                        </div>
                        <div class="card-footer bg-white border-top text-center py-3">
                            <span class="badge bg-primary bg-opacity-10 text-primary uppercase tracking-widest p-2">Total Apperances: {{ events.count }}</span>
                        </div>
                    </div>

                </div>
            </div>

        </div>
    </form>
</div>

<!-- AI Deep Dive Modal -->
<div class="modal fade" id="deepDiveModal" tabindex="-1" aria-labelledby="deepDiveModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content border-0 shadow-lg rounded-4">
      <div class="modal-header border-0 pb-0">
        <h5 class="modal-title font-dm-serif text-primary" id="deepDiveModalLabel"><i class="bi bi-magic"></i> Deep Dive Insight</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body p-4">
        <div id="deepDiveContent" class="p-3 bg-light rounded-3 text-dark italic" style="font-size: 1.05rem; line-height: 1.6; border-left: 4px solid #6366f1;">
            <!-- Content inject -->
        </div>
      </div>
      <div class="modal-footer border-0 pt-0 justify-content-between">
        <span class="text-muted tracking-widest uppercase" style="font-size: 0.6rem;">Powered by Project Penn</span>
        <button type="button" class="btn btn-light" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    function generatePortraitCall() {
        if (!confirm('Generate a new AI portrait for this character?')) return;
        
        const btn = document.getElementById('generatePortraitBtn');
        const icon = btn.querySelector('i');
        btn.disabled = true;
        icon.className = 'bi bi-arrow-repeat text-primary animate-spin';
        
        fetch("{% url 'api_generate_portrait' character.pk %}", {
            method: 'POST',
            headers: { 'X-CSRFToken': '{{ csrf_token }}' }
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            icon.className = 'bi bi-magic text-primary';
            if (data.status === 'success') {
                const preview = document.getElementById('profilePreview');
                if (preview) preview.src = data.image_url;
                else window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(err => {
            btn.disabled = false;
            icon.className = 'bi bi-magic text-primary';
            console.error(err);
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        
        // Custom spinning CSS
        const style = document.createElement('style');
        style.textContent = `
            .animate-spin { animation: spin 1s linear infinite; display: inline-block; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
        `;
        document.head.appendChild(style);
        
        // Deep Dive
        const deepDiveBtn = document.getElementById('deepDiveBtn');
        const deepDiveContent = document.getElementById('deepDiveContent');
        const deepDiveModal = new bootstrap.Modal(document.getElementById('deepDiveModal'));
        
        if (deepDiveBtn) {
            deepDiveBtn.addEventListener('click', function() {
                const icon = this.querySelector('i');
                const origClass = icon.className;
                icon.className = 'bi bi-arrow-repeat animate-spin text-primary fs-6';
                if(!this.dataset.loading) this.dataset.loading = "1"; else return;
                
                fetch("{% url 'api_character_deep_dive' %}", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' },
                    body: JSON.stringify({ character_id: '{{ character.id }}' })
                })
                .then(res => res.json())
                .then(data => {
                    this.dataset.loading = "";
                    icon.className = origClass;
                    if (data.status === 'success') {
                        deepDiveContent.innerHTML = data.response;
                        deepDiveModal.show();
                    } else alert('Error: ' + data.message);
                })
                .catch(err => {
                    this.dataset.loading = "";
                    icon.className = origClass;
                });
            });
        }

        // Sync Trigger
        const syncBtn = document.getElementById('syncCharacterBtn');
        if (syncBtn) {
            syncBtn.addEventListener('click', function() {
                if (!confirm('Sync empty boxes using AI analysis from the book?')) return;
                
                const icon = this.querySelector('i');
                const origClass = icon.className;
                icon.className = 'bi bi-arrow-repeat animate-spin fs-6 text-primary';
                
                fetch("{% url 'api_character_sync' %}", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' },
                    body: JSON.stringify({ character_id: '{{ character.id }}' })
                })
                .then(res => res.json())
                .then(data => {
                    icon.className = origClass;
                    if (data.status === 'success') {
                        alert('Sync complete! Refreshing metadata...');
                        window.location.reload();
                    } else alert('Error: ' + data.message);
                })
                .catch(err => {
                    icon.className = origClass;
                });
            });
        }

        // Avatar Picker
        const avatarOptions = document.querySelectorAll('.avatar-option');
        const avatarIdInput = document.querySelector('input[name="avatar_id"]');
        const imageInput = document.querySelector('input[name="profile_image"]');
        
        avatarOptions.forEach(option => {
            option.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                avatarOptions.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                
                if (avatarIdInput) avatarIdInput.value = id;
                
                const img = this.querySelector('img');
                const preview = document.getElementById('profilePreview');
                const placeholder = document.getElementById('profilePlaceholder');
                
                if (img && (preview || placeholder)) {
                    if (preview) {
                        preview.src = img.src;
                    } else {
                        const newPreview = document.createElement('img');
                        newPreview.id = 'profilePreview';
                        newPreview.src = img.src;
                        newPreview.className = 'portrait-img';
                        placeholder.parentNode.replaceChild(newPreview, placeholder);
                    }
                    if (imageInput) imageInput.value = '';
                }
            });
        });

        // Profile File Input
        if (imageInput) {
            imageInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.getElementById('profilePreview');
                        const placeholder = document.getElementById('profilePlaceholder');
                        if (preview) {
                            preview.src = e.target.result;
                        } else if (placeholder) {
                            const newPreview = document.createElement('img');
                            newPreview.id = 'profilePreview';
                            newPreview.src = e.target.result;
                            newPreview.className = 'portrait-img';
                            placeholder.parentNode.replaceChild(newPreview, placeholder);
                        }
                        
                        avatarOptions.forEach(opt => opt.classList.remove('selected'));
                        if (avatarIdInput) avatarIdInput.value = '';
                    }
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }

    });
</script>
{% endblock %}
"""

with open("c:\\Users\\denni\\OneDrive\\Documents\\Vs projects\\Story-timeline-builder\\Story-timeline-builder-1\\templates\\timeline\\character_detail.html", "w", encoding="utf-8") as f:
    f.write(content)
