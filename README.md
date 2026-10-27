# Institute for Mind and Biology website

The website of the Institute for Mind and Biology (IMB) at the University of Chicago.

- **Editors:** see **[EDITING-GUIDE.md](EDITING-GUIDE.md)**. All everyday updates are made in a web dashboard (Pages CMS), with no coding.
- **This file** is for whoever sets up hosting, or needs to change how the site works.

---

## How it works

All content lives in plain text files in this repository. When a change is saved, whether from the dashboard or on GitHub, a GitHub Action runs `build.py`. That script turns the files into a static website and publishes it with GitHub Pages. There's no database, no server, and nothing to patch for security.

| Content                         | Where it lives                    | One file per… |
|---------------------------------|-----------------------------------|---------------|
| News posts                      | `content/news/`                   | post          |
| Faculty (bio, photo, areas)     | `content/faculty/`                | person        |
| Research areas                  | `content/research/`               | area          |
| Page text (Home, About, …)      | `content/*.md`                    | page          |
| Fellows, staff                  | `data/fellows.yml`, `data/staff.yml` | (one list) |
| Events                          | `data/events.yml`                 | (one list)    |
| Publications (DOIs)             | `data/publications.yml`           | (one list)    |
| Contact details                 | `site.yml`                        |               |
| Menu, footer links              | `menu.yml` (not in the dashboard) |               |
| Redirects from old addresses    | `redirects.yml`                   |               |
| Look and layout                 | `templates/`, `static/css/style.css` |            |
| Dashboard forms                 | `.pages.yml`                      |               |

Things the build does automatically:
- **Sorting.** People are sorted by last name, events by date, and news newest first.
- **Events** move from "Upcoming" to "Past" on their own. The site rebuilds daily for this.
- **Research-area pages and the "Our Research" menu** are generated from the faculty's area tags.
- **Publications.** Editors enter only a DOI, and the title, authors, journal and year are fetched from Crossref. Results are cached in `.cache/crossref.json`, which is committed so builds don't depend on Crossref being up.
- **Mistakes don't block publishing.** A missing photo, an unknown research area, or a bad date or DOI produces a warning. The affected item is skipped (or shown with initials) and everything else still publishes. Warnings appear on the private page **`/site-status/`** (not indexed by search engines) and as yellow notes in GitHub Actions. Only a genuinely broken file, such as invalid YAML from hand-editing, stops a build. In that case the live site stays as it was.

## Previewing locally

You'll need Python 3. Run these commands from inside this folder (e.g. `cd ~/data/imb-website` first):

```bash
pip install -r requirements.txt
```

```bash
python build.py --serve
```

Open http://localhost:8000.

To make a copy you can zip and email for review, which opens by double-clicking `index.html`:

```bash
python build.py --offline --out ../IMB-website-demo
```

---

## One-time setup

### 1. Hosting on GitHub Pages
1. Create a **public** GitHub repository, ideally under an IMB or UChicago organization so it isn't tied to one person, and push this folder to it.
2. In the repository, go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.
3. Go to **Actions → Build and publish site → Run workflow**. The site appears at `https://<org>.github.io/<repo>/`.

### 2. The editing dashboard (Pages CMS)
1. Go to **https://app.pagescms.org** and sign in with GitHub, as a user with admin access to the repository.
2. When prompted, install the **Pages CMS GitHub App** and give it access to this repository.
3. Open the repository in Pages CMS. The menus come from `.pages.yml`. Check that each section opens and saves correctly; this configuration hasn't been tested against a live repository yet.
4. **Invite Anissha (and any other editors) as collaborators by email** in the repository's settings in Pages CMS. Collaborators **don't need a GitHub account**; they can edit content and photos but can't change the configuration.
5. Fill in the support contact at the bottom of `EDITING-GUIDE.md`, and send it to them.

### 3. Custom domain (imb.uchicago.edu)
1. In GitHub, go to **Settings → Pages → Custom domain**, enter `imb.uchicago.edu`, and save.
2. Ask UChicago IT Services to change the `imb.uchicago.edu` DNS record to a CNAME pointing to `<org>.github.io`.
3. Once it works, tick **Enforce HTTPS**.

Old WordPress addresses, such as `/staff-profile-2/` and `/cognition/`, redirect to the new pages via `redirects.yml`.

---

## Making technical changes

- **Menu:** edit `menu.yml`. `children_from: research_areas` lists every research area automatically.
- **New page:** add `content/<name>.md`. It's published at `/<name>/` using `templates/page.html`, or `templates/<name>.html` if one exists. Add it to `.pages.yml` so editors can change its text, and to `menu.yml` if it belongs in the menu.
- **New field for editors:** add it to the content file *and* to `.pages.yml`. The dashboard should only ever save fields it knows about, so keep the two in sync.
- **News categories, fellow roles:** these drop-down options are set in `.pages.yml`.
