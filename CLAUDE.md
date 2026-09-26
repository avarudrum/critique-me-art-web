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
- Plain Django templates, one hand-written stylesheet, no CSS framework and no
  build step. **No JavaScript at all** — the tag overflow and the landing-page
  critique slideshow are both pure CSS, deliberately. HTMX planned but not added.
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
- `accounts/` — custom `User` (extends `AbstractUser`: bio, primary_medium, created_at). `AUTH_USER_MODEL = 'accounts.User'`. Signup, profile and profile-editing views; `LoginForm`/`LogoutWithNoticeView` exist only so auth pages match the rest of the site
- `artworks/` — `Tag`, `Artwork`, `CritiqueRequest`; upload, detail, browse, edit, delete views, plus `home` (the landing page, routed from `config/urls.py` at `/`); `management/commands/seed.py`
- `critiques/` — `Critique`, `CritiqueSection`; formset-based create/edit views, delete view
- `core/constants.py` — `FOCUS_AREAS`, the single source of truth for feedback areas. Not a Django app.
- `templates/` — all templates live here at project level, namespaced by app (`templates/artworks/...`), plus `registration/` for auth
- `static/css/atelier.css` — the whole stylesheet, in numbered sections. `STATICFILES_DIRS` points here; `STATIC_ROOT` is `staticfiles/` for `collectstatic` at deploy time
- `core/forms.py` — `NoLabelSuffixMixin`, shared by every form

## Key design decisions (please keep these)

- **Critiques are split by focus area.** `Critique` has many `CritiqueSection`s, one per area. This is the product's core idea.
- **Focus areas come from `core/constants.py`.** Both `CritiqueRequest.focus_areas` (JSONField, validated by the form) and `CritiqueSection.category` use this list. Don't add a second copy.
- **One `CritiqueRequest` per `Artwork`** (OneToOne), created in the same upload form. Many critiques per artwork.
- **No strength/growth labels.** This was tried and removed on purpose. Sections are free text; critics add praise in their own words if they want.
- **Critics may answer any subset of the requested areas**, but at least one. Enforced in `BaseCritiqueSectionFormSet.clean()`. Blank sections aren't saved.
- **Artists can't critique their own work.** Checked in the view.
- **Browsing is behind a login.** `browse` and `artwork_detail` are `@login_required`, and the nav only offers them to members. `/` is the public landing page and the only thing a visitor sees. `LOGIN_URL`/`LOGIN_REDIRECT_URL` send them to browse once they're in, and `?next=` returns them to whatever they were trying to reach.
- **Logging out says so.** `LogoutWithNoticeView` adds the message *after* `super().dispatch()`: `auth_logout()` calls `session.flush()`, so anything queued beforehand is discarded with the old session. Every other action in the app confirms itself; logout shouldn't be the exception.
- **Signing up logs you straight in.** `SignUpView.form_valid()` calls `login()` — they just chose the password, so making them retype it is friction with nothing behind it.
- **Profiles live at `/artist/<username>/`, wired in `config/urls.py`.** Deliberately *not* under `accounts/`: a `<str:username>` route there would shadow Django's own `accounts/logout/` and `accounts/password_reset/`. Readable by any member, not just the owner — seeing what someone has written before is how you judge their critique.
- **`bio` and `primary_medium` finally have a UI** (`ProfileForm`, `/accounts/settings/`). They had been on the model since the start but were admin-only, so a profile page would have rendered permanently empty.
- **The nav is three groups:** wordmark, `.nav-sections` (Browse, Upload) beside it, and `.nav-account` pushed right by `margin-left: auto`. The auto margin lives on the account group — putting it on the wordmark shoves *everything* right.
- **The landing page critique is a slideshow with no JavaScript.** A hidden radio
  group drives it: the radios sit ahead of the nav and track as siblings, and the
  CSS reaches them with `~`. The tabs are the focus-area names rather than dots,
  so clicking through *is* the product idea. One selector pair per slide, five
  being the ceiling by design (one section per area, five areas in
  `core.constants.FOCUS_AREAS`). The radios are `.visually-hidden` but stay
  focusable, so the group is arrow-key navigable; the focus ring is drawn on the
  matching tab because the radio itself is off-screen.
- **The landing page shows one real critique, not a mock-up.** `artworks.views.home`
  picks it by *substance* — most areas answered, then longest — never by recency or
  by which artwork has the most critiques. Those heuristics would have put a
  one-word "nice!" on the front page, because that is literally what the newest
  critique on the most-critiqued artwork was. The section is wrapped in
  `{% if example %}`, so an empty database just omits it. Three queries.
  It reuses `.artwork-plate`, `.focus-list` and `.critique-section` so it reads
  as part of the site rather than a marketing panel.
- **The landing page is three left-aligned blocks sharing one grid.** Statement,
  then the definition, then the critique specimen, separated by hairline rules and
  equal spacing. The definition and the specimen both use `.grid-2`, so the word
  *atelier* sits on the same column edge as the artwork below it and its
  definition on the same edge as the critique. **The alignment is the structure:**
  there is no ornament on this page, and adding any back is the thing that made
  earlier versions look homemade. An earlier design set the definition as a tinted
  panel with an accent bar; that reads as a framework alert component, not a
  gallery label. The decorative rule above the headline went the same way.
- **The accent appears twice on the landing page and nowhere else in the hero:**
  *critique* in the headline and the tagline beneath it, both italic serif in
  `--accent`. Resist adding a third.
- **Copy is a studio voice, not a product voice.** Plain, concrete, a bit dry. No "empowering artists to unlock feedback". Section names stay boring and obvious ("Browse", not "The wall") — the voice belongs in the landing page and helper text, not in navigation.
- **`description` is capped at 1200 characters and `artist_note` at 600.** `TextField(max_length=...)` is form-level only — the DB column stays TEXT — which is what's wanted: it validates and puts a `maxlength` on the textarea, so the browser stops them first.
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
- **The tag picker is never paginated.** `GroupedTagSelect` hides a category's long tail behind a `<details>` instead. Collapsed options stay in the DOM, so a ticked box inside one still submits — paging would split one form across requests and silently drop selections made on a page the user navigated away from. Two knobs: `visible_per_group = 8` and `min_overflow = 3` (don't collapse a tail so short that the toggle costs more than it saves). In practice nothing collapses until a category has 11 tags.
- **Usage decides which tags are visible, alphabet decides their order.** `grouped_tag_choices()` orders by `Count('artworks')` so the least-used tags fall into the overflow; `GroupedTagSelect.get_context()` then re-sorts each half by name so chips don't shuffle around as counts change.
- **A `<details>` renders `open` when it hides a ticked box** (`overflow_has_selection`), so someone editing an artwork can always see every tag they chose.
- **New tags are checked for near-duplicates before they are created.** `similar_tags()` runs two passes: `difflib.get_close_matches` at cutoff 0.8 for close spellings ('watercolor' → 'watercolour', 'charcole' → 'charcoal'), then per-word prefix overlap for multi-word names difflib scores too low ('pastel' vs 'oil pastel' is only 0.75, 'oils' vs 'oil paint' 0.46). The second pass compares against each *word* of the existing name rather than using `in`, so 'ink' matches 'acrylic ink' without also matching 'linework', and it needs 3 characters to start since 2-letter prefixes match far too much.
- **The "did you mean" prompt is a hard stop, not a warning.** A soft warning would still create the duplicate, which defeats the point. The artist either clicks a suggestion or explicitly confirms. Both are plain submit buttons (`use_existing_tag`, `confirm_new_medium`), so the flow needs no JavaScript.
- **The medium box has its own Add button** (`MediumEntry` widget, `add_medium`). A bare text field gave no sign anything had happened — the artist typed a medium and only found out on save whether it was reused or created. Making it a widget rather than template markup means `as_p` still renders the field normally and the button comes along with it.
- **Every medium-box button is an *interim* submit** (`INTERIM_BUTTONS`): it updates the form and re-renders, and only the form's own submit button saves. `is_valid()` returns False for an interim press whatever else is true, so nothing can save from one — important, because `full_clean()` prunes unrelated errors for display and pruning does *not* put anything back into `cleaned_data`, so a caller trusting a pruned-to-empty error dict would blow up in `save_m2m()`.
- **On an interim press the views re-render without saving** and rebuild `CritiqueRequestForm` *unbound from the same POST data*, so the artist keeps their focus areas and note without being shown errors for a form they haven't finished. They trigger cleaning by touching `form.errors`, not `is_valid()`, since the latter is now always False there.
- **Both outcomes are announced.** Inline while editing (`medium_notice`: 'selected' = ticked an existing tag, 'pending' = will be created on save) and again after saving via Django messages (`medium_outcome`: 'reused' / 'created'). Reusing an existing tag used to be entirely silent, which left artists unsure whether their medium had registered at all.
- **Nothing is created on an Add press**, only on save. Typing a brand-new medium and abandoning the form still leaves no orphan tag.
- **`use_existing_tag` is folded into the submitted data in `__init__`**, before any cleaning, so the rest of the form behaves as if the artist had ticked the box themselves. The id is not trusted — it goes through `tags`, which validates against the queryset. `_select_suggested_tag()` reads through the widget and writes with `setlist` or `[]` depending on the copy, because `request.POST` is an immutable multi-value QueryDict while a plain dict is also valid form input.
- **An exact (case-insensitive) match short-circuits before suggestions**, so typing an existing medium in any casing just reuses it silently.
- **Medium is a tag, not a field.** `Artwork.medium` (free-text CharField) was removed in migration `0002`. It duplicated the medium-category tags on every artwork and produced one-off values like `'graphite and charcoal'` that polluted the browse dropdown. Medium is now whichever tags have `category == 'medium'`.
- **An artwork may have several mediums, but needs at least one.** Enforced in `GroupedTagsMixin.clean()`, not the database, so the browse filter stays complete. Multiple mediums are the point: 'Reaching out' is graphite *and* charcoal.
- **`new_medium` is a free-text escape hatch, medium only.** An artist whose medium isn't listed types it and it becomes a `Tag(category='medium')`. Technique and subject stay a curated list so they don't fill with near-duplicates.
- **The new tag is created in `save()`, never in `clean()`.** Creating during validation leaves orphan tags whenever the surrounding request fails for another reason — on upload, `CritiqueRequestForm` is validated alongside and either can fail. `save()` mutates `cleaned_data['tags']`, which `save_m2m()` reads later, so it works with both `commit=True` and the views' `commit=False` pattern.
- **New medium lookup is `name__iexact`.** `Tag.name` is unique but that constraint is case-sensitive, so 'Oil'/'oil'/' oil ' would otherwise become three tags. A name already taken by a non-medium tag is rejected with a pointer to the right list, rather than silently attaching a subject tag as a medium.
- **`Artwork.medium_names()` filters `self.tags.all()` in Python**, not with `.filter(category=...)`. The views already `prefetch_related('tags')`, so this reuses that cache instead of firing a query per artwork on browse. Verified: 2 queries total for the whole page.
- **The browse `medium` query param is a Tag id**, not a name. Medium and tag are applied as two separate `.filter()` calls, which means "has both tags" — one combined call would ask for a single tag matching both ids. The queryset is `.distinct()` because each join can repeat a row. The Tag dropdown excludes medium-category tags, since medium has its own dropdown.
- **`accounts.User.primary_medium` is still free text** and has the same smell as the old `Artwork.medium`. Left alone for now; worth revisiting if profiles get a browse/filter feature.

## Styling

Gallery wall, not web app. Warm paper, near-black ink, **one** sienna accent,
thin rules instead of boxes and shadows, and enough air that the artwork is the
loudest thing on screen.

- **Everything is a token.** Colours, fonts, spacing and widths are custom
  properties on `:root` in `atelier.css`. Change the palette there, not in rules.
- **Type pairing:** Cormorant Garamond for display and anything quoted
  (titles, legends, artist notes, ledes); Inter for UI and body. Loaded from
  Google Fonts in `base.html`, with a system fallback stack.
- **`.eyebrow`** is the repeated small-caps label used above section headings.
- **Artwork is never cropped.** Browse tiles and the detail plate both use
  `object-fit: contain` on paper, which reads as a mat. Uniform tiles with
  `cover` would crop the work, which is the wrong trade on a critique site.
  The detail plate is capped at `76vh` so a tall portrait doesn't strand the
  metadata column beside a run of empty paper.
- **The generic button rule is scoped to `.site-main`** so it can't catch the
  nav's logout button. Buttons that need a different look (`.btn-danger`,
  `.medium-entry-add`) override it later in the file and need at least (0,1,1)
  specificity to win — hence the compound selectors.
- **Structure comes from alignment, never ornament.** Shared column edges,
  hairline rules and consistent spacing. Decorative elements that carry no
  structure are what make a page read as homemade — a landing-page flourish was
  added, resized twice, moved, and finally deleted, and deleting it was the fix.
- **A shorthand property silently erases the longhands it covers.** Bitten twice:
  `.site-main { padding: … 0 … }` zeroed `.shell`'s horizontal gutter on every
  page, and `background: var(--paper-raised)` wiped the select chevron's
  `background-image`. When two rules of equal specificity touch one element, use
  the longhand (`padding-block`, `background-color`) in the later one.
- **Labels have no trailing colon**, via `NoLabelSuffixMixin`. They are styled as
  letterspaced caps, and letter-spacing puts a gap before the colon.
- **Long text must be actively contained.** Grid and flex children default to
  `min-width: auto` and refuse to shrink below their content, so one long word
  in a card widens its track and pushes text over the artwork beside it. Every
  layout child is opted down to `min-width: 0`, `body` sets
  `overflow-wrap: break-word`, and card text is line-clamped. Measured: with
  those guards removed a single artwork's title stretched to 2287px inside a
  1280px viewport.
- **Selects are drawn, not native.** `appearance: none` plus an inline-SVG chevron. The shared input rule must use `background-color`, not the `background` shorthand, or it resets `background-image` and wipes the chevron — and the select rule has to come *after* it.
- **A `<select>` is sized by its widest `<option>`**, so the browse filters are
  capped (`max-width`) rather than left to size themselves — tag names run to 50
  characters, wider than a phone, and an uncapped select sets the page width.
- **An element carrying `.shell` plus a layout class must not use the `padding`
  shorthand.** `<main class="site-main shell">` had `.shell { padding: 0 1.8rem }`
  silently overridden by `.site-main { padding: 2.8rem 0 4.5rem }` — same
  specificity, later in the file, so the shorthand zeroed the horizontal gutter
  everywhere. It went unnoticed for ages because above 1120px the `max-width`
  centring fakes a gutter; below it, content sat flush against the window edge.
  Those rules use `padding-block` now. Check with
  `getComputedStyle(el).paddingLeft`, not by eye.
- **`.site-nav` must wrap.** Without `flex-wrap`, the nav can't fit on a narrow
  screen and forces the whole document wider than the viewport, which shifts
  every page sideways, not just the header.
- **Option labels are chips, not labels.** The global `label` rule is
  uppercase-caps, which made each checkbox option read as a heading. The tag
  picker and `div.focus-picker` both restyle their labels back to sentence case.

### Checking a layout actually works

Screenshots lie about layout. Two measurements caught real bugs that eyeballing
missed, both worth repeating after any layout change:

```js
// horizontal overflow — run via chromium --dump-dom at several widths
document.documentElement.scrollWidth > window.innerWidth
getComputedStyle(document.querySelector('.site-nav')).paddingLeft  // gutter alive?
el.getBoundingClientRect().left                                    // columns aligned?
```

A screenshot also cannot click, so interactive CSS (the slideshow) has to be
driven — click each label, then read `getComputedStyle(slide).display` — or all
you have verified is that the first slide renders.

## Gotchas already hit

- **Tests that save an `Artwork` with a real file upload hit your real Cloudinary account.** `CloudinaryField` uploads when the model is *saved*, not when the form validates, and Django's test database being throwaway doesn't help: dropping it never touches Cloudinary. Test scripts leaked tiny red-square PNGs into the Media Library this way. When writing the real test suite, give artworks a string public id (`image='fake_id'`) instead of a file, or patch `cloudinary.uploader.upload`. Related: the `post_delete` cleanup signal also fires in tests, calling `cloudinary.uploader.destroy` on whatever id the artwork has — harmless for a fake id, but it does reach the network.
- `{# ... #}` is a **single-line** comment. Spanning one across several lines does
  not comment anything out — the whole thing renders to the page as visible text.
  Use `{% comment %}...{% endcomment %}` for anything multi-line.
- Django escapes apostrophes to `&#x27;` in rendered output, so asserting on a
  message's raw text (`You're logged out`) fails even when the page is correct.
  Check `response.context['messages']` for content and match the escaped form in
  HTML.
- Headless Chrome clamps `--window-size` to a **500px minimum width**. Asking for
  390 renders at 500 and crops, which looks exactly like a layout bug. Measure
  overflow by comparing `documentElement.scrollWidth` to `window.innerWidth`
  via `--dump-dom`, don't eyeball narrow screenshots.

- `CloudinaryField` doesn't accept a Django `File` outside a form. In scripts, upload with `cloudinary.uploader.upload(path)` and assign `result['public_id']`.
- Cloudinary free plan rejects images over 10 MB.
- Seed image filenames must match exactly, including extension case (`.JPG` vs `.jpg`). macOS ignores case, Linux servers won't.
- `--flush` clears the database but not Cloudinary; old uploads must be deleted from the Media Library manually. `manage.py flush` does not fire `post_delete`, so the `Artwork` cleanup signal does not help here — only real deletes.
- `CloudinaryField`'s form field is `CloudinaryFileField`, which subclasses plain `FileField`, **not** `ImageField`. It does no image validation at all — a renamed `.txt` uploads happily. `ArtworkForm.clean_image()` checks size and verifies content with Pillow.
- Pillow's `verify()` consumes the file object. Rewind with `seek(0)` afterwards or the upload to Cloudinary sends zero bytes — a bug that only shows up when the upload actually runs.
- Artworks created through the admin used to lack a `CritiqueRequest`. The admin now has an inline, and the critique view redirects if one is missing.
- Templates silently hide `AttributeError`s (e.g. a missing related object renders blank). Views surface them as 500s.
- Reversing a `RemoveField` re-adds the column using the definition recorded in that migration. A `NOT NULL` column with no default cannot be added back to a table that already has rows — SQLite raises `IntegrityError: NOT NULL constraint failed`. Migration `0002` inserts an `AlterField` giving `medium` a `default=''` *before* the `RemoveField` purely so the migration can be reversed.
- Django renders form widgets through a **private template engine** that only sees `django/forms/templates` and app-level template dirs — it cannot see the project-level `templates/`. `FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'` in settings routes widget rendering through `TEMPLATES` instead, which is what lets `templates/artworks/widgets/` work. That setting requires `'django.forms'` in `INSTALLED_APPS`, or Django's own built-in widget templates stop resolving.
- `label_suffix` cannot be set as a class attribute — `BaseForm.__init__` assigns
  `self.label_suffix` unconditionally and would overwrite it. `NoLabelSuffixMixin`
  passes it through `kwargs` instead. `LoginView` builds its own form, so it has
  to be handed `accounts.forms.LoginForm` explicitly in `config/urls.py`.
- `display: inline-block` on a `<summary>` removes the default disclosure
  triangle, leaving the toggle looking like inert text. The tag picker's "N more"
  draws its own `+`/`–` marker.
- A declared `forms.Field` on a plain (non-`Form`) mixin is **not** picked up — Django's form metaclass only collects from base classes that have `declared_fields`. `GroupedTagsMixin` adds `new_medium` in `__init__` instead, which also places it after the tag chips.

## Current status

V1 core loop is complete: signup/login, upload with feedback request, browse with
medium/tag/needs-critique filters, detail page, structured critiques, seed data.

Since then, roughly in order:

- upload validation (size cap + a real image check with Pillow), `requirements.txt`
- duplicate-critique guard; Django messages wired into `base.html`
- edit/delete for critiques and for artworks, with Cloudinary cleanup on delete
- medium folded into tags (`artworks/0002`, drops `Artwork.medium`)
- the tag picker: grouped by category, usage-ranked, overflow disclosure,
  near-duplicate detection, and an explicit Add button with visible outcomes
- full styling pass; static files set up
- browsing put behind a login; landing page rebuilt as the public face
- profiles at `/artist/<username>/` with bio/medium editing (`accounts/0002`)
- signup auto-login, logout confirmation
- `description`/`artist_note`/`bio` length caps (`artworks/0003`)

**Still uncommitted at time of writing** — several rounds of the above. Check
`git status`; new *untracked* paths are easy to miss and the app breaks without
them (`static/`, `core/forms.py`, `templates/accounts/`, and the migrations).

## Next up

1. ~~Small fixes: friendly error for uploads over 10 MB; stop a user critiquing the same piece twice; success message after posting a critique.~~ Done.
2. ~~Styling.~~ Done — see the Styling section above. Every page is styled and
   static files are set up. `{% block extra_head %}` still exists in `base.html`
   for page-specific additions, but nothing uses it now.
3. **Deploy** (Railway or Render) with PostgreSQL. Recommended before the README,
   which needs the live URL and the real setup steps. Already done: `SECRET_KEY`,
   `DEBUG` and `ALLOWED_HOSTS` from env, and `STATIC_ROOT`. Still needed:
   `dj-database-url` + `psycopg`, **whitenoise** (with `DEBUG=False` Django stops
   serving static files entirely, so the site deploys looking completely
   unstyled — this is the one that catches people), `gunicorn` and a start
   command, `CSRF_TRUSTED_ORIGINS` for the deployed domain, and the matching
   `requirements.txt` additions.
4. README explaining the product idea, stack, and local setup.

**Tests are still not in the repo.** Every `tests.py` is empty. A lot of test
logic has been written and thrown away in scratch files; porting it is mostly
transcription. Worth doing before the tag refactor below or before deploy,
whichever comes first — `GroupedTagsMixin` is the most intricate code here
(interim submits, error pruning, `is_valid()` deliberately returning False) and
it is exactly the sort of thing that breaks quietly.

### Tag growth plan

Steps 1 and 2 are built (overflow disclosure and "did you mean", both above).
Remaining steps, to be done only when the tag list actually justifies them:

3. **Filter box** — ~15 lines of vanilla JS hiding non-matching chips as you type.
   Worth it once a category realistically passes ~30. Everything stays in the DOM,
   so selections are still safe.
4. Server-side autocomplete via HTMX only matters at thousands of tags.

Open items on the tag work:

- **Free-text creation is still medium-only.** Extending it to technique and
  subject means generalising `new_medium` into a per-category field; `similar_tags()`
  already takes a `category` argument for exactly that.
- **Casing is normalised only on lookup, not on write.** `Underpainting` and
  `Impressionism` are still stored capitalised while everything else is lowercase.
  A `Tag.save()` that lowercases would fix it going forward, plus a one-off data
  migration for what's there.
- **Unused tags are never pruned.** `Tag.objects.annotate(n=Count('artworks')).filter(n=0)`
  is the report; whether to auto-hide or delete them is a product call.
- **Any validation error on upload loses the chosen image**, because browsers
  won't repopulate a file input. The medium box's Add button and the "did you
  mean" prompt both add round trips that hit this. Inherent to non-JS file
  inputs — HTMX is the real fix, and this is the strongest argument for adding it.
- **Enter in any text field triggers Add**, because browsers submit via the first
  submit button in DOM order and `MediumEntry` renders one mid-form. Harmless (an
  interim press preserves input and shows no spurious errors) and it gives the
  medium box the Enter-to-add behaviour it wants, but it is why the main submit
  button cannot simply be moved earlier in the markup.

Out of scope for now: guides/lessons, following, feeds, notifications, reputation, revision threads.
