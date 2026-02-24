# Story Timeline Builder

![Story Timeline Builder Logo](static/img/logo.png)

**Live Application:** [https://story-timeline-builder-237864658489.herokuapp.com/](https://story-timeline-builder-237864658489.herokuapp.com/)

A comprehensive Django web application designed specifically for authors to plan, organise, and track complex multi-book narratives. Built to support writers managing series with intricate plots, character arcs, and world-building across multiple volumes.

---

## Table of Contents

- [1. Ideation & Scoping](#1-ideation--scoping)
  - [Problem Statement](#problem-statement)
  - [Purpose](#purpose)
  - [Target Audience](#target-audience)
- [2. Features](#2-features)
  - [MVP Features](#mvp-features)
  - [Additional Features](#additional-features)
- [3. User Experience (UX) Design](#3-user-experience-ux-design)
  - [User Stories](#user-stories)
  - [Design Philosophy](#design-philosophy)
  - [Wireframes](#wireframes)
- [4. Technical Design](#4-technical-design)
  - [Data Model](#data-model)
  - [User Flow](#user-flow)
- [5. Technologies Used](#5-technologies-used)
- [6. Installation & Setup](#6-installation--setup)
- [7. Deployment & Testing](#7-deployment--testing)
- [8. Credits](#8-credits)

---

## 1. Ideation & Scoping

### Problem Statement
Fiction authors, especially those writing long-running series, struggle to maintain consistency and narrative momentum across thousands of pages. Managing complex character arcs, evolving relationships, and chronological timelines across multiple books often leads to:
- **Plot Holes**: Forgetting when a specific event happened relative to others.
- **Inconsistency**: Losing track of world-building rules or character traits.
- **Cognitive Overload**: Spending more time managing notes than actually writing.

### Purpose
The **Story Timeline Builder** provides an intuitive, centralised platform for authors to map out their entire narrative universe. By digitalising the "story bible," it allows writers to:
- Visualise chronological vs. narrative sequence.
- Track character development and relationships dynamically.
- Maintain a consistent world wiki.
- Use AI-assisted prompts to overcome writer's block.

### Target Audience
- **Series Authors**: Writers managing trilogies or extensive sagas (e.g., the user's 20-book series project).
- **World Builders**: Authors of fantasy/sci-fi needing a consistent reference for lore.
- **Plotters**: Writers who prefer detailed outlining and scene-by-scene planning.

---

## 2. Features

### MVP Features (Current Scope)
To alleviate the core problem of narrative disorganisation, the MVP includes:
- **User Authentication**: Secure registration and login to ensure private, persistent story data.
- **Manuscript Management**: CRUD operations for books to organise series structure.
- **Scene/Event Tracking**: A foundational system to record and edit scenes with smart dating.
- **Character Profiles**: Basic cast management to track who is in the story.
- **Activity Logging**: Automated tracking of changes to provide a "recent activity" overview.

### Additional Features (Iteration 2 & 3)
- **Interactive Timeline**: Visual horizontal layout for high-level plotting.
- **Relationship Mapping**: Visualising bonds and dynamics between characters.
- **AI Integration**: Deep dive character analysis and daily task generation.
- **World Wiki**: A dedicated codex for world-building consistency.
- **Manuscript Import**: Uploading .docx files to auto-populate the database.

---

## 3. User Experience (UX) Design

### User Stories
User stories are framed within the context of solving the narrative complexity problem:
- **As a busy author**, I want a dashboard with "Today's Focus" tasks so I can immediately know what to work on and reduce planning stress.
- **As a series plotter**, I want to link events to specific books and chapters so I have a clear overview of my story's structure.
- **As a world-builder**, I want to tag events with themes and locations to ensure I don't create geographical or thematic plot holes.

### Design Philosophy
The UI focuses on **reducing cognitive load**:
- **Clean Interface**: Minimalist cards and soft pastel colours to prevent eye strain.
- **Quick Actions**: One-click entry points for New Event/Character from any page.
- **Architect View**: A toggle to switch between high-level planning and detail-oriented drafting.

### Wireframes

#### Dashboard (Foundational Solution for Stress Reduction)
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
│ Time │  │ [Books] [Chars]         │ [ New Book ]                    │ │
└──────┴────────────────────────────────────────────────────────────┘
```

#### Manuscript List
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
└──────┴────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Design

### Data Model
The database structure is designed to ensure **privacy and personalisation**:
- **User ↔ Book (1:N)**: All story data is linked to a specific user, ensuring authors' IP remains private and their experience is personalised.
- **Book ↔ Chapter ↔ Event (Hierarchy)**: Maintains structural integrity, reflecting how real books are organised.
- **Character ↔ Event (M:N)**: Tracks appearances, solving the "who is where?" problem.

### User Flow
1. **Landing/Registration**: User enters the platform.
2. **Dashboard**: User sees AI-suggested tasks and recent activity.
3. **Manuscript Setup**: User creates a book and adds chapters.
4. **World Building**: User adds characters and world entries.
5. **Timeline Mapping**: User adds events, linking them to chapters and POV characters.

---

## 5. Technologies Used
- **Django 4.2.27**: Robust backend framework.
- **Neon PostgreSQL**: Scalable relational database.
- **Cloudinary**: Persistent image storage for covers and avatars.
- **Heroku**: Cloud hosting platform.
- **Google Gemini / DeepSeek**: AI engines for narrative analysis.

---

## 6. Installation & Setup
1. Clone the repo.
2. Create `venv` and `pip install -r requirements.txt`.
3. Configure `.env` with `DATABASE_URL` and `SECRET_KEY`.
4. `python manage.py migrate` and `python manage.py runserver`.

---

## 7. Deployment & Testing
Deployed on Heroku using Gunicorn and WhiteNoise.
Manual testing verified for:
- User story completion.
- Form validation and error message clarity.
- Responsive design across screen sizes.

---

## 8. Credits
- Developed by **Den Murray**.
- Built as a Capstone Project for the AI Augmented FullStack Bootcamp.
