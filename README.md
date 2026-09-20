# Smart E-Learning 2

**An adaptive, bilingual, AI-powered learning platform** — built as a graduation project (ITI) and hackathon submission.

> Setup instructions live in [`SETUP.md`](./SETUP.md). This file is about *what the project is and does*.

## What it does

Smart E-Learning 2 personalizes the studying experience for every student instead of
treating everyone the same:

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

## Tech stack

Deliberately scoped to match the course curriculum — no frameworks or
languages outside what was taught:

| Layer | Technology |
|---|---|
| Backend | Python + Django |
| Database | PostgreSQL |
| AI | Google Gemini (`google-genai`) + prompt engineering |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Voice input | Web Speech API (browser-native) |
| i18n | Django's built-in translation framework |

## Architecture

The project is split into four Django apps:

- **`authentication`** — custom user model (role, points, level, study streak)
- **`learning`** — courses, lessons (content + video + AI summary),
  quizzes, questions, the hybrid adaptive+GenAI quiz engine, enrollments,
  and course progress tracking
- **`core`** — gamification (points/levels/badges), mindfulness content,
  Azkar, and the student task checklist
- No separate AI-agent app — Gemini is called directly from
  `apps/learning/services.py` (quiz questions) and `apps/learning/ai_helpers.py`
  (lesson summaries), each a single-purpose, single-shot call rather than an
  open-ended chat.

The schema (22 tables) was translated directly from a hand-drawn ERD into
Django models, migrated against a **real PostgreSQL database**, not SQLite.

## Quality — tested, not just "it runs"

Before ever being handed over, the project was verified with an automated
smoke test (`smoke_test.py`) that simulates two independent students end to
end: registering, enrolling, taking a quiz, earning points, and confirming
the adaptive engine actually reorders questions based on each student's own
performance. All checks pass against a live PostgreSQL instance.

The one thing that *couldn't* be verified automatically is the live Gemini
API call itself, since the build environment has no external network access —
see `SETUP.md` for the one-time check to run before a live demo.

## A note on lesson content

The `content` field on each `Lesson` is empty by default — this project
builds the *feature* (display page, video link, AI summary button), but the
actual curriculum text is something only you can add, since it needs to be
real, accurate material for your course. Add it per lesson from `/admin/`
under Learning → Lessons.

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
├── locale/ar/            # Arabic translation catalog
├── smoke_test.py         # automated multi-user test
├── requirements.txt
└── SETUP.md              # step-by-step local setup
```
