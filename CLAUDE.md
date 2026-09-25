# Atelier

A structured art critique platform. Artists post work and choose which areas
they want feedback on (composition, color, technique, concept, perspective).
Critics respond only to those areas, in their own words. The point is
feedback that answers what the artist actually asked, instead of one
generic comment box.

This is a portfolio project for internship applications. The developer is a
4th-year CS student (strong in Python, Java, C; new to web development).

## How I want to work

- I'm learning as I build. Explain *why* a change works, not just what to type.
- One step at a time. Get something working and verified before building on it.
- When you change something, tell me which files you touched and how to test it.
- Point out mistakes or risky ideas directly, including in my own suggestions.
- Keep commit-sized checkpoints. Remind me to commit when something works.

## Stack

- Django 5.2, Python 3.11, virtual environment in `venv/`
- SQLite locally (PostgreSQL planned for deployment)
- Cloudinary for image storage via `CloudinaryField`
- Plain Django templates with minimal CSS so far. HTMX planned but not added.
- Secrets in `.env` (gitignored), loaded with python-dotenv. See `.env.example`.

## Commands

```bash
source venv/bin/activate          # always first; macOS has no bare `python` outside the venv
python manage.py runserver        # http://127.0.0.1:8000/
python manage.py makemigrations <app> && python manage.py migrate
python manage.py seed --flush     # reset and reseed sample data
```

Seeded accounts: gracie_m, haley_s, sana_k, terry_lb. Password: seedpass123

## Structure

- `config/` — settings and root URLs
- `accounts/` — custom `User` (extends `AbstractUser`: bio, primary_medium, created_at). `AUTH_USER_MODEL = 'accounts.User'`
- `artworks/` — `Tag`, `Artwork`, `CritiqueRequest`; upload, detail, browse views; `management/commands/seed.py`
- `critiques/` — `Critique`, `CritiqueSection`; formset-based critique view
- `core/constants.py` — `FOCUS_AREAS`, the single source of truth for feedback areas. Not a Django app.
- `templates/` — all templates live here at project level, namespaced by app (`templates/artworks/...`), plus `registration/` for auth

## Key design decisions (please keep these)

- **Critiques are split by focus area.** `Critique` has many `CritiqueSection`s, one per area. This is the product's core idea.
- **Focus areas come from `core/constants.py`.** Both `CritiqueRequest.focus_areas` (JSONField, validated by the form) and `CritiqueSection.category` use this list. Don't add a second copy.
- **One `CritiqueRequest` per `Artwork`** (OneToOne), created in the same upload form. Many critiques per artwork.
- **No strength/growth labels.** This was tried and removed on purpose. Sections are free text; critics add praise in their own words if they want.
- **Critics may answer any subset of the requested areas**, but at least one. Enforced in `BaseCritiqueSectionFormSet.clean()`. Blank sections aren't saved.
- **Artists can't critique their own work.** Checked in the view.
- **No DB unique constraint on (artwork, user) for critiques** — kept as a view-level rule so revision threads stay possible later.

## Gotchas already hit

- `CloudinaryField` doesn't accept a Django `File` outside a form. In scripts, upload with `cloudinary.uploader.upload(path)` and assign `result['public_id']`.
- Cloudinary free plan rejects images over 10 MB.
- Seed image filenames must match exactly, including extension case (`.JPG` vs `.jpg`). macOS ignores case, Linux servers won't.
- `--flush` clears the database but not Cloudinary; old uploads must be deleted from the Media Library manually.
- Artworks created through the admin used to lack a `CritiqueRequest`. The admin now has an inline, and the critique view redirects if one is missing.
- Templates silently hide `AttributeError`s (e.g. a missing related object renders blank). Views surface them as 500s.

## Current status

V1 core loop is complete: signup/login, upload with feedback request, browse with
medium/tag/needs-critique filters, detail page, structured critiques, seed data.

## Next up

1. Small fixes: friendly error for uploads over 10 MB; stop a user critiquing the same piece twice; success message after posting a critique (Django messages framework).
2. Styling. Focus on browse, artwork detail, and critique form first.
3. README explaining the product idea, stack, and local setup.
4. Deploy (Railway or Render) with PostgreSQL.

Out of scope for now: guides/lessons, following, feeds, notifications, reputation, revision threads.
