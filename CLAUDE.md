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
- `artworks/` — `Tag`, `Artwork`, `CritiqueRequest`; upload, detail, browse, edit, delete views; `management/commands/seed.py`
- `critiques/` — `Critique`, `CritiqueSection`; formset-based create/edit views, delete view
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
- **One critique per person per artwork**, enforced by an `.exists()` check at the top of `create_critique` (before the POST branch, so a double submit can't slip through). View-level on purpose, per the point above. Deleting your critique frees you to write a new one.
- **Editing a critique syncs its sections.** Filled + existing → update, filled + new → create, cleared → the `CritiqueSection` is deleted. So clearing a box genuinely drops that area. The formset still requires at least one non-blank area.
- **The edit form's category list is a union** of the artist's requested areas and any area the critique already answered. Without the second half, an edit would silently drop sections if the request ever changed.
- **`CritiqueSectionForm.clean_body()` strips whitespace**, so a space-filled box counts as blank everywhere. Both the formset's "at least one area" check and the edit sync depend on this.
- **Artwork edits cover text only** — `title`, `description`, `medium`, `tags` via `ArtworkEditForm`. The image and focus areas are deliberately excluded: critics responded to that specific image and those specific areas, so swapping either would leave critiques answering something invisible.
- **Deleting an artwork hard-deletes its critiques** (existing `on_delete=CASCADE`, no migration). Chosen over archiving for simplicity; the confirm page tells the artist how many critiques will go.
- **Destructive actions are POST-only.** GET renders a confirmation page. A GET that deletes data fires on crawlers and link previews.
- **Cloudinary cleanup lives in a `post_delete` signal** on `Artwork`, not in the delete view, so it also runs for admin deletes and for cascades from a deleted user. Its `except Exception` is deliberate: the DB row is already gone, so a Cloudinary network error must not become a 500.
- **Tag checkboxes are grouped by `Tag.category`** via `grouped_tag_choices()`, shared by `ArtworkForm` and `ArtworkEditForm`. Grouping only affects rendering; `ModelMultipleChoiceField` still validates against the queryset.

## Gotchas already hit

- `CloudinaryField` doesn't accept a Django `File` outside a form. In scripts, upload with `cloudinary.uploader.upload(path)` and assign `result['public_id']`.
- Cloudinary free plan rejects images over 10 MB.
- Seed image filenames must match exactly, including extension case (`.JPG` vs `.jpg`). macOS ignores case, Linux servers won't.
- `--flush` clears the database but not Cloudinary; old uploads must be deleted from the Media Library manually. `manage.py flush` does not fire `post_delete`, so the `Artwork` cleanup signal does not help here — only real deletes.
- `CloudinaryField`'s form field is `CloudinaryFileField`, which subclasses plain `FileField`, **not** `ImageField`. It does no image validation at all — a renamed `.txt` uploads happily. `ArtworkForm.clean_image()` checks size and verifies content with Pillow.
- Pillow's `verify()` consumes the file object. Rewind with `seek(0)` afterwards or the upload to Cloudinary sends zero bytes — a bug that only shows up when the upload actually runs.
- Artworks created through the admin used to lack a `CritiqueRequest`. The admin now has an inline, and the critique view redirects if one is missing.
- Templates silently hide `AttributeError`s (e.g. a missing related object renders blank). Views surface them as 500s.

## Current status

V1 core loop is complete: signup/login, upload with feedback request, browse with
medium/tag/needs-critique filters, detail page, structured critiques, seed data.

Since then: upload validation (size + real image check), duplicate-critique guard,
Django messages wired into `base.html`, edit/delete for critiques, edit/delete for
artworks, Cloudinary cleanup on delete, grouped tag checkboxes, `requirements.txt`.

## Next up

1. ~~Small fixes: friendly error for uploads over 10 MB; stop a user critiquing the same piece twice; success message after posting a critique.~~ Done.
2. Styling. Focus on browse, artwork detail, and critique form first.
   Static files aren't set up yet — no `static/` dir and no `STATICFILES_DIRS`.
   Page-specific CSS currently goes in the `{% block extra_head %}` in `base.html`;
   move to a real stylesheet as part of this step.
3. README explaining the product idea, stack, and local setup.
4. Deploy (Railway or Render) with PostgreSQL.

Out of scope for now: guides/lessons, following, feeds, notifications, reputation, revision threads.
