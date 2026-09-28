# My Anime Blog

A personal blog built with **Python and Django**. You write posts (with photos placed anywhere in the text) in a simple editor, and visitors read them on your own website.

**Pages:** Home · Blogs · About me · Contact, with a **search box in the top right**.
**Look:** your own anime pictures as the background, with soft dark panels so text stays easy to read.

## What's inside

| Feature | How it works |
| --- | --- |
| Write posts whenever you want | Django admin panel with a rich text editor (CKEditor 5) |
| Photos anywhere in a post | Upload from the editor's image button, then align left / right / centre and resize |
| Drafts and scheduling | Save as *Draft*, or pick a future publish time |
| Search | Top-right box searches titles, summaries, post text and topics |
| Topics | Tag posts (Anime, Coding, ...) and filter the blog list by topic |
| About me and Contact | Edited in the admin. Contact messages are saved in the admin (and optionally emailed) |
| Anime backgrounds | Drop pictures in `static/backgrounds/`. One picture is fixed, several become a slideshow |
| Only you can post | Writing is behind your admin login. Visitors can only read |

## Run it on your computer

You need Python 3.10 or newer.

```bash
# 1. Get the code
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the requirements
pip install -r requirements.txt

# 4. Set up the database
python manage.py migrate

# 5. Create your admin login (this is how you'll write posts)
python manage.py createsuperuser

# 6. (Optional) add three demo posts so the site isn't empty
python manage.py seed_demo

# 7. Start the site
python manage.py runserver
```

Open <http://127.0.0.1:8000> to see the site and <http://127.0.0.1:8000/admin> to write.

## Your anime backgrounds

Copy your pictures into `static/backgrounds/` (`.jpg`, `.png`, `.webp`, ...). Refresh the page. That's it.

- 1 picture: fixed background. 2 or more: fades between them every 12 seconds.
- Prefer one random picture per page load instead? Set `BACKGROUND_MODE=random` in `.env`.
- Aim for about 1920 px wide and under 1.5 MB each so pages load fast.

> **Copyright:** anime art you downloaded usually belongs to its artist. That's fine on your own computer, but check the license before you make the repo public or put the site online. To keep the pictures out of GitHub, uncomment the `static/backgrounds/*` lines at the bottom of `.gitignore`.

## Writing a post

1. Go to `/admin` and log in.
2. Click **Posts → Add post**.
3. Fill in the title, a short summary, and (optionally) a cover image.
4. Write in the editor. Use the **image button** to add a photo anywhere. Click a photo in the editor to align, resize or caption it.
5. Pick topics, set **Status** to *Published*, and click **Save**.

Fill in your name, photo, story and links under **About & contact details**.

## Settings

Copy `.env.example` to `.env` and edit it. Useful values:

| Variable | Meaning |
| --- | --- |
| `DJANGO_SECRET_KEY` | Long random secret. **Required** when `DJANGO_DEBUG=False` |
| `DJANGO_DEBUG` | `True` on your computer, `False` online |
| `DJANGO_ALLOWED_HOSTS` | Your domain(s), comma separated |
| `BACKGROUND_MODE` | `slideshow` or `random` |
| `SITE_NAME` | The name shown in the header (default "My Blog") |
| `CONTACT_NOTIFY_EMAIL` | Optional email for new contact messages (needs email settings in `config/settings.py`) |

Change your timezone with `TIME_ZONE` in `config/settings.py`.

## Put it online

PythonAnywhere (free tier available) is the simplest home for a Django site:

1. Push this repo to GitHub and clone it on PythonAnywhere.
2. Create a virtualenv and run `pip install -r requirements.txt`.
3. Create a `.env` with `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS=yourname.pythonanywhere.com`.
4. Run `python manage.py migrate`, `python manage.py createsuperuser` and `python manage.py collectstatic`.
5. In the **Web** tab, point the WSGI file at `config.wsgi`, then add two static mappings:
   `/static/` → `<project>/staticfiles` and `/media/` → `<project>/media`.

Uploaded photos live in `media/` and the posts live in `db.sqlite3`. Neither is stored in Git, so **back them up** from time to time. Other hosts (Render, Railway, a VPS) work too: use `gunicorn config.wsgi` and serve `/media/` from persistent storage.

## Push this project to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Django blog"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

`.gitignore` already keeps your database, uploads and `.env` secrets out of the repo.

## Project layout

```
config/            Django settings, main URLs, WSGI
blog/              The blog app
  models.py        Post, Topic, SiteProfile (About), ContactMessage
  views.py         Home, blog list + search, post page, About, Contact
  admin.py         The writing screens
  templates/blog/  Page templates
templates/         base.html (header, search, background) and 404 page
static/css/        style.css (all the look and feel)
static/js/         main.js (background slideshow)
static/backgrounds/  Put your anime pictures here
```

## Tests

```bash
python manage.py test
```
