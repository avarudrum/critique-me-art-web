# Atelier

**A structured art critique platform.**

Most places to share art give you one comment box, and you get back "nice!" or advice
on things you never asked about. On Atelier, artists choose which areas they want
feedback on when they upload a piece: **composition, color, technique, concept or
perspective**. Critics reply only to those areas, in their own words.

## Try it

**Live site:** <https://YOUR-APP.herokuapp.com/>

Browsing needs an account. To look around without signing up, log in with the demo account:

| Username | Password      |
|----------|---------------|
| `demo`   | `demopass123` |

It's a shared account, so anything you post with it is visible to the next visitor.

## How it works

1. **Upload.** An artist posts a piece, tags its medium, technique and subject, picks
   the focus areas they want critiqued, and can add a note saying what they're unsure about.
2. **Browse.** Members browse a gallery they can filter by medium, tag, or pieces still
   waiting for a critique.
3. **Critique.** A critic first picks which of the requested areas they'll answer. A text
   box opens for each one they pick. They can answer any of the requested areas, but at
   least one.
4. **Read.** Critiques show on the artwork page as a collapsible thread. Each entry shows
   the author, the areas answered and the date, and the author's name links to their
   profile so you can judge who's giving the advice.

## Features

- Sign up, log in and log out, with a public landing page. Browsing requires an account.
- Upload with real image validation (size limit plus a content check with Pillow),
  stored on Cloudinary
- Grouped tag picker, ranked by how often each tag is used, with a
  "did you mean…?" check that stops near-duplicate tags like *watercolor* / *watercolour*
- Edit and delete for both artworks and critiques. Deletes need a POST and a
  confirmation page first, and deleting an artwork also removes its image from Cloudinary.
- Artist profiles with a bio, primary medium and their past work and critiques
- One critique per person per artwork, and artists can't critique their own work

## Technical highlights

- **Critiques split by area.** A `Critique` has many `CritiqueSection`s, one per focus
  area. The list of areas is defined once, in `core/constants.py`, and every part of
  the app reads it from there.
- **No JavaScript, on purpose.** The slideshow, every dropdown, the critique thread and
  the pick-your-areas-first form are all built from `<details>`, hidden radios and
  checkboxes, `:has()` and flex `order`.
- **Query-conscious views.** Tag and medium lookups reuse prefetched data instead of
  running a query per artwork, so the browse page takes the same number of queries
  however many artworks it shows.
- **Validation that can't leave junk behind.** New tags are created only when the form
  is saved, never while it's being validated, so a form that fails leaves no orphan tags.
- **Hand-written CSS with a "gallery wall" design.** Warm paper, near-black ink, one
  sienna accent, and thin rules instead of boxes and shadows. Artwork is never cropped.

## Stack

| Layer    | Choice                                                       |
|----------|--------------------------------------------------------------|
| Backend  | Django 5.2, Python 3.11                                      |
| Database | SQLite locally, PostgreSQL in production                     |
| Images   | Cloudinary                                                   |
| Frontend | Django templates, one hand-written stylesheet, no build step |
| Hosting  | Heroku (gunicorn, WhiteNoise for static files)               |

## Project layout

```
accounts/    custom User model, signup, profiles, profile settings
artworks/    Tag, Artwork, CritiqueRequest; upload, browse, detail, edit, delete; seed command
critiques/   Critique, CritiqueSection; create, edit, delete
core/        shared constants (the focus areas) and form helpers
config/      settings and root URLs
templates/   all templates, namespaced by app
static/css/  the stylesheet
```

## Running locally

You need Python 3.11 and a free [Cloudinary](https://cloudinary.com/) account for image storage.

```bash
git clone <this repo>
cd atelier
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # then fill in the values below
python manage.py migrate
python manage.py runserver        # http://127.0.0.1:8000/
```

`.env` goes in the project root, next to `manage.py`:

| Variable                                        | Notes                                                   |
|-------------------------------------------------|---------------------------------------------------------|
| `SECRET_KEY`                                    | Any long random string for local use                    |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | From your Cloudinary dashboard |
| `DEBUG`                                         | Set to `True` locally. Defaults to `False`, which is what a server should run |
| `ALLOWED_HOSTS`                                 | Optional, defaults to `127.0.0.1,localhost`             |

### Sample data

```bash
python manage.py seed             # add sample users, artworks and critiques
python manage.py seed --flush     # wipe the sample data and reseed
```

On your local copy, seeded accounts all use the password `seedpass123` (for example
`gracie_m`, `haley_s`). These passwords don't work on the live site; use the demo account there.

The seed images live in `seed_images/`, which is not checked into the repo. Without
that folder, `seed` stops with an error and creates nothing. Create an empty
`seed_images/` folder to get just the users, then upload your own work through the site.

## Deployment

The live site runs on Heroku with Heroku Postgres. Heroku deploys from this repo: the
`Procfile` starts gunicorn and runs migrations before each release, and the Python
buildpack runs `collectstatic` for WhiteNoise to serve. The settings are the same
`.env` variables as above, set as Heroku config vars, plus:

| Variable               | Notes                                                        |
|------------------------|--------------------------------------------------------------|
| `DATABASE_URL`         | Set automatically by the Heroku Postgres add-on              |
| `ALLOWED_HOSTS`        | The app's domain, e.g. `your-app.herokuapp.com`             |
| `CSRF_TRUSTED_ORIGINS` | The same domain with `https://` in front                     |

`DEBUG` stays unset in production. When it's off, Django redirects to HTTPS and marks
cookies secure-only.

## Roadmap

- Automated test suite
- HTMX for things plain HTML can't do well, such as keeping the chosen image after a
  validation error
