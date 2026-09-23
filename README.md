# Smart E-Learning 2

**An adaptive, bilingual, AI-powered learning platform.**

> Setup instructions live in [`SETUP.md`](./SETUP.md).

## How to run it

1. Install PostgreSQL and create a database with UTF8 encoding.
2. Copy `.env.example` to `.env` and fill in your database credentials and
   `GEMINI_API_KEY`.
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py seed_mindfulness` (registers the bundled azkar/dua images)
6. `python manage.py createsuperuser`
7. `python manage.py runserver`, then open `http://127.0.0.1:8000/`

Full details, troubleshooting, and the multi-day Git workflow are in
[`SETUP.md`](./SETUP.md).

## Features

- **Adaptive + AI-Hybrid Quiz Engine** — every quiz mixes 7 questions from the
  teacher's own question bank (matched to the student's difficulty level) with
  3 fresh questions generated on-the-spot by Gemini at the same level — each
  clearly tagged in the UI as "Teacher Bank 📘" or "GenAI Created 🤖". Student
  level (Easy/Medium/Hard) is assessed dynamically from their own quiz history,
  not set manually.
- **Real lesson content + AI summarization** — each lesson has a written
  content field and an optional video link (added by the teacher via the
  admin), plus a one-click "Summarize this lesson" button that asks Gemini
  for a short bullet-point recap.
- **Gamification** — points, levels, and badges tied to real actions (enrolling,
  passing a quiz, completing a self-added task). Every point-earning event is
  logged individually, not just summed into one number.
- **Mindfulness reminders** — a Pomodoro-style pop-up every 25 minutes with a
  verse, hadith, or motivational note, plus a dedicated Azkar card on the
  dashboard and a closing dua on logout.
- **True bilingual UI (English/Arabic)** — one click flips all text and the
  page direction (LTR ↔ RTL). English is the default language.

<!--
  If you add more Generative AI features later (a chatbot, an agentic tool
  with function-calling, etc.), document them here: what they do, which
  model/API they call, and any new setup steps (env vars, packages).
-->

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python + Django |
| Database | PostgreSQL |
| AI | Google Gemini (`google-genai`) + prompt engineering |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Voice input | Web Speech API (browser-native) |
| i18n | Django's built-in translation framework |

## Architecture

The project is split into three Django apps:

- **`authentication`** — custom user model (role, points, level, study streak)
- **`learning`** — courses, lessons (content + video + AI summary),
  quizzes, questions, the hybrid adaptive+GenAI quiz engine, enrollments,
  and course progress tracking
- **`core`** — gamification (points/levels/badges), mindfulness content,
  Azkar, and the student task checklist

Gemini is called directly from `apps/learning/services.py` (quiz questions)
and `apps/learning/ai_helpers.py` (lesson summaries) — each a single-purpose,
single-shot call.

The schema (22 tables) was translated from an ERD into Django models,
migrated against a real PostgreSQL database.

## Quality

The project is verified with an automated smoke test (`smoke_test.py`) that
simulates two independent students end to end: registering, enrolling, taking
a quiz, earning points, and confirming the adaptive engine reorders questions
based on each student's own performance — against a live PostgreSQL instance.

## A note on lesson content

The `content` field on each `Lesson` is empty by default. Add real curriculum
text per lesson from `/admin/` under Learning → Lessons.

## Project structure

```
smart_e_learning_2/
├── apps/
│   ├── authentication/   # custom user, register/login
│   ├── learning/         # courses, lessons, quizzes, hybrid adaptive+GenAI engine, ai_helpers.py (summaries)
│   ├── core/             # gamification, mindfulness, task checklist
├── config/               # Django settings, root urls
├── templates/            # HTML templates (EN source, AR translations)
├── static/               # CSS, JS (mindfulness popup, particle background)
├── media/                # uploaded azkar/dua images
├── locale/ar/            # Arabic translation catalog
├── smoke_test.py         # automated multi-user test
├── requirements.txt
└── SETUP.md              # step-by-step local setup
```
