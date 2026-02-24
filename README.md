# Story Timeline Builder

![Story Timeline Builder Logo](static/img/logo.png)

**Live Application:** [https://story-timeline-builder-237864658489.herokuapp.com/](https://story-timeline-builder-237864658489.herokuapp.com/)

A comprehensive Django web application designed specifically for authors to plan, organise, and track complex multi-book narratives. Built to support writers managing series with intricate plots, character arcs, and world-building across multiple volumes.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [User Experience (UX) Design](#user-experience-ux-design)
  - [User Stories](#user-stories)
  - [Design Philosophy](#design-philosophy)
  - [Wireframes](#wireframes)
- [Database Schema](#database-schema)
- [Technologies Used](#technologies-used)
- [Installation & Setup](#installation--setup)
- [Deployment](#deployment)
- [Testing](#testing)
- [Credits](#credits)

---

## Project Overview

Story Timeline Builder was created to solve a specific problem for fiction authors: managing the complexity of multi-book series. Whether you're writing a trilogy or a 20-book saga, keeping track of character development, plot threads, timelines, and world-building consistency becomes exponentially harder as your story grows.

This application provides:

- **Manuscript Management**: Organise books in series order with word count tracking
- **Timeline Visualisation**: See your entire story laid out chronologically or in narrative order
- **Character Profiles**: Track character arcs, relationships, and development across books
- **Event/Scene Management**: Break down your story into manageable, taggable events
- **World Wiki**: Maintain consistency with a dedicated world-building reference system
- **AI Integration**: Optional AI-powered analysis and suggestions (Google Gemini & DeepSeek)

### Target Audience

- Fiction authors writing series (fantasy, sci-fi, thrillers, etc.)
- Creative writing students managing complex projects
- Writing teams collaborating on shared universes

---

## Features

### Core Functionality (CRUD)

✅ **Books (Manuscripts)**
- Create, edit, and delete book entries
- Track series order, word count targets, and completion status
- Upload book cover images
- Import manuscript content from .docx/.txt files

✅ **Chapters**
- Organise chapters within books
- Auto-calculate word counts from pasted content or uploaded files
- Mark chapters as complete

✅ **Events/Scenes**
- Full CRUD for story events
- Rich-text editor for detailed scene descriptions
- Categorise by story beat, emotional tone, location, and POV character
- Smart date system (exact, fuzzy, relative, or ongoing dates)
- Tag events with themes, subplots, or custom categories

✅ **Characters**
- Complete character profiles with goals, motivations, and traits
- Upload custom profile images or select cartoon avatars
- Track character introduction points and activity status

✅ **Character Relationships**
- Define relationships between characters with detailed attributes:
  - Type (friend, enemy, romantic, family, etc.)
  - Trust level, strength, power dynamics
  - Conflict sources and shared secrets
- Visualise with an interactive relationship map

✅ **Tags & Themes**
- Create custom tags for themes, locations, subplots, motifs, or tones
- Colour-coded for visual organisation

✅ **World Wiki**
- Document locations, lore, factions, magic systems, creatures, and cultures
- Attach images and link entries to specific books

### Authentication & Authorization

- **Role-based access**: Regular users vs. staff/admin
- **Secure registration & login** with hashed passwords
- **Social authentication**: Google, Twitter, and LinkedIn login via django-allauth
- **Permission-based rendering**: Staff dashboard hidden from regular users

### User Notifications

- **Activity logging**: All create/update/delete actions logged via Django signals
- **Real-time feedback**: Django messages framework displays success/error notifications
- **Recent activity widget**: Dashboard shows latest changes across all models

### Dashboard & Analytics

- **At-a-glance stats**: Books, chapters, characters, and events count
- **Progress tracking**: Visual progress bars for word count targets
- **AI-generated focus tasks**: Daily writing prompts to keep momentum
- **Character dynamics analysis**: Identify relationship gaps and opportunities

### AI Features (Optional)

- **Deep Dive Analysis**: AI-generated character insights using Google Gemini
- **Relationship Mapping**: Automated character relationship suggestions
- **Writing prompts**: Context-aware task generation

---

## User Experience (UX) Design

### User Stories

The project was developed using Agile methodology with user stories tracked in GitHub Projects:

**Epic 1: Core Story Management**
- As an author, I want to create and organise multiple books in a series
- As an author, I want to visualise my entire story on an interactive timeline
- As an author, I want to track character appearances across multiple books

**Epic 2: Planning & Organisation**
- As an author, I want to link events to specific chapters
- As an author, I want to tag events with themes and subplots
- As an author, I want to maintain a world-building wiki for consistency

**Epic 3: Character Development**
- As an author, I want to manage a detailed cast of characters
- As an author, I want to map relationships between characters
- As an author, I want to track how relationships evolve over time

**Epic 4: Productivity & AI**
- As an author, I want AI-generated writing prompts
- As an author, I want automated relationship analysis
- As an author, I want word count tracking and progress visualisation

Full project board: [GitHub Projects](https://github.com/users/denmurray10/projects/12)

### Design Philosophy

**1. Writer-Centric Interface**
- Distraction-free writing mode
- Quick actions sidebar for rapid data entry
- Keyboard shortcuts for common tasks

**2. Visual Clarity**
- Pastel colour palette for reduced eye strain during long sessions
- Consistent iconography (Bootstrap Icons)
- Colour-coded character badges and timeline markers

**3. Responsive & Accessible**
- Mobile-responsive layout (Bootstrap 5.3)
- Semantic HTML structure
- ARIA labels for screen readers
- Clear navigation hierarchy

**4. Progressive Disclosure**
- Essential features visible immediately
- Advanced features (AI, relationship maps) accessible via sidebar
- Collapsible sections to reduce cognitive load

### Design Iteration

**Initial Wireframes → Live Implementation Changes:**

1. **Dashboard Layout**: Originally planned as a 3-column grid. Changed to a flexible card-based layout with widget reordering after user feedback.
2. **Timeline View**: Moved from vertical scroll to horizontal timeline with zoom controls for better overview.
3. **Character Profiles**: Added avatar selection system after realising users needed quick visual differentiation.
4. **Navigation**: Simplified from dropdown menus to a persistent sidebar with icon + text labels.

---## Wireframes

Below are simplified wireframes showing the key user interface layouts:

### 1. Dashboard (Landing Page After Login)

```
┌───────────────────────────────────────────────────────────────────────┐
│ [Logo] Story Timeline Builder            [Search]      Hello, User ▼ │
├──────┬────────────────────────────────────────────────────────────────┤
│      │  DASHBOARD                                    [Architect View] │
│ ☰    │  ┌─────────────────────────┬─────────────────┬────────────────┐│
│ Dash │  │ Today's Focus           │ Character       │ Recent         ││
│      │  │ □ Write 500 words       │ Dynamics        │ Activity       ││
│ Manus│  │ □ Outline new scene     │ No relationships│ Deleted Book A ││
│      │  │ □ Develop character     │ tracked yet.    │ Created Event  ││
│ Chapt│  └─────────────────────────┴─────────────────┴────────────────┘│
│      │  ┌─────────────────────────┬─────────────────────────────────┐ │
│ Story│  │ Stats                   │ Your Books                      │ │
│ T  │  │ [Books] [Chars]      │ [ New Book ]                   │ │
│      │  │ [Events][Chaps]      │                                │ │
│      │  └──────────────────────┴────────────────────────────────┘ │
└──────┴────────────────────────────────────────────────────────────┘
```

### 2. Manuscript List / Create Book

```
┌───────────────────────────────────────────────────────────────────────┐
│ [Logo] Story Timeline Builder            [Search]      Hello, User ▼ │
├──────┬────────────────────────────────────────────────────────────────┤
│      │  MANUSCRIPTS                                   [ + New Book ] │
│ ☰    │                                                                │
│ Dash │  ┌──────────────────────┐  ┌──────────────────────┐            │
│      │  │ [Book Cover Image]   │  │ [Book Cover Image]   │            │
│ Manus│  │                      │  │                      │            │
│      │  │ Book 1: Title        │  │ Book 2: Title        │            │
│ Chapt│  │ Status: Drafting     │  │ Status: Planning     │            │
│      │  │ Progress: [████░░░]  │  │ Progress: [░░░░░░░]  │            │
│ Story│  │ [Edit] [Delete]      │  │ [Edit] [Delete]      │            │
│ Time │  └──────────────────────┘  └──────────────────────┘            │
└──────┴────────────────────────────────────────────────────────────┘
```

### 3. Timeline View (Interactive)

```
┌───────────────────────────────────────────────────────────────────────┐
│ [Logo] Story Timeline Builder            [Search]      Hello, User ▼ │
├──────┬────────────────────────────────────────────────────────────────┤
│      │  STORY TIMELINE                                  [ + Event ]  │
│ ☰    │                                                                │
│ Dash │  [Chronological] [Narrative]                  [ Zoom - / + ]   │
│      │                                                                │
│ Manus│  |-----------------|-----------------|-----------------|       │
│      │  [Scene 1]         [Scene 3]         [Scene 5]                 │
│ Chapt│        [Scene 2]         [Scene 4]                             │
│      │                                                                │
│ Story│  POV: [Leo ▼]  Theme: [Action ▼]                              │
└──────┴────────────────────────────────────────────────────────────┘
```

### 4. Character Management

```
┌───────────────────────────────────────────────────────────────────────┐
│ [Logo] Story Timeline Builder            [Search]      Hello, User ▼ │
├──────┬────────────────────────────────────────────────────────────────┤
│      │  CHARACTERS                                  [ + Character ]   │
│ ☰    │                                                                │
│ Dash │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│      │  │ [Avatar]      │ │ [Avatar]      │ │ [Avatar]      │         │
│ Manus│  │ Name: Leo     │ │ Name: Jamal   │ │ Name: Ethan   │         │
│      │  │ Role: Protagon│ │ Role: Support │ │ Role: Antagon │         │
│ Chapt│  │ [Profile]     │ │ [Profile]     │ │ [Profile]     │         │
│      │  └───────────────┘ └───────────────┘ └───────────────┘         │
└──────┴────────────────────────────────────────────────────────────┘
```

---

## Database Schema

The application uses a robust relational database schema built with Django's ORM:

- **User**: Django's built-in auth model (extended via allauth)
- **Book**: Represents a manuscript with word count tracking and series metadata
- **Chapter**: Organises narrative within a book
- **Character**: Detailed profiles for cast management
- **Event**: The core "building block" (scene) linked to POV, location, book, and chapter
- **Tag**: Flexible categorisation system for themes and subplots
- **CharacterRelationship**: Many-to-Many mapping with detailed bond attributes
- **WorldEntry**: Wiki entries for consistent world-building
- **ActivityLog**: Automated tracking of all user actions

---

## Technologies Used

- **Framework**: Django 4.2.27 (Python)
- **Database**: PostgreSQL (Neon.tech) / SQLite (Local)
- **Front-end**: Bootstrap 5.3.2, Bootstrap Icons, jQuery
- **Media Hosting**: Cloudinary (Image management)
- **Deployment**: Heroku
- **AI Models**: Google Gemini Pro, DeepSeek R1/V3
- **Tools**: VS Code, Git/GitHub, Figma (UI Design)

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/denmurray10/Story-timeline-builder.git
   cd Story-timeline-builder
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=your_postgres_url
   GEMINI_API_KEY=your_key
   DEEPSEEK_API_KEY=your_key
   CLOUDINARY_URL=your_cloudinary_url
   ```

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start Server:**
   ```bash
   python manage.py runserver
   ```

---

## Deployment

The project is configured for deployment on **Heroku**:

- **Procfile**: Defined for Gunicorn server
- **WhiteNoise**: Configured for efficient static file serving
- **Cloudinary**: Integrated for persistent media storage
- **dj-database-url**: For seamless PostgreSQL connection

---

## Testing

Extensive manual testing has been performed across all user stories:

- **CRUD Testing**: Verified all models can be created, edited, and deleted with real-time feedback.
- **Security Testing**: Authenticated users can only access/modify their own data.
- **Responsive Testing**: Verified layout on Chrome (Desktop), Firefox, and Safari (iOS).
- **AI Integration**: Stress-tested relationship mapping with complex story datasets.

---

## Credits

- **Developer**: [Den Murray](https://github.com/denmurray10)
- **UI/UX Inspiration**: Figma Community
- **Icons**: [Bootstrap Icons](https://icons.getbootstrap.com/)
- **Special Thanks**: AI Augmented FullStack Bootcamp
