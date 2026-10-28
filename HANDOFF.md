# IMB website: technical handoff

**Project:** New website for the Institute for Mind and Biology (IMB), University of Chicago. It replaces the WordPress site on UChicago Voices at https://imb.uchicago.edu.
**Prepared:** October 27, 2026, for Ed Vogel (Director).
**Day-to-day editor:** Anissha Warner (Administrative Director). She'll use the dashboard only; see `EDITING-GUIDE.md` and the PDF version.

---

## 1. Status at a glance

| Area | Status |
|---|---|
| All content from the old site (20 pages, 13 faculty, 15 fellows, 4 staff, 24 events, photos) | Done |
| New sections: News, Publications (DOI lookup), private site-status page | Done |
| Redirects from old WordPress addresses | Done |
| Dashboard configuration for Pages CMS (`.pages.yml`) | Written and checked against every content file, **not yet tested in Pages CMS** |
| Automatic publishing (GitHub Actions to GitHub Pages) | Written, **not yet run** (no GitHub repository yet) |
| GitHub repository | **Not created yet** |
| Custom domain `imb.uchicago.edu` | **Not switched yet.** Needs a DNS change by UChicago IT |
| Editor guide for Anissha | Done: `EDITING-GUIDE.md` and `IMB-Website-Editing-Guide.pdf` (support-contact line left blank, to fill in by hand) |
| Review demo | Done: `IMB-website-demo.zip` (opens offline) |

**Location on Ed's Mac:** `~/data/imb-website/`. It's a Git repository on the `main` branch with 2 commits:
- `e699615`: Initial version of the new IMB website
- `9fec831`: Add editing dashboard, News, and Publications

**Not committed yet:** `tools/` (link checker and PDF maker), `HANDOFF.md` (this document), a one-line list fix in `EDITING-GUIDE.md`, and a timezone fix in `build.py`, so events switch to "Past" on the Chicago date, not UTC.

**Files outside the repository** in `~/data/`: `IMB-Website-Editing-Guide.pdf` and `IMB-website-demo.zip`.

---

## 2. How it works

```
Anissha edits a form in Pages CMS  ─┐
Someone edits a file on GitHub     ─┼─>  commit to the main branch on GitHub
Daily schedule (09:00 UTC)         ─┘            │
                                                 v
                          GitHub Actions: .github/workflows/deploy.yml
                          1. pip install -r requirements.txt
                          2. python build.py   (YAML + Markdown -> HTML in _site/)
                          3. publish _site/ with GitHub Pages
                                                 │
                                                 v
                          https://<org>.github.io/<repo>/  ->  later imb.uchicago.edu
```

- **Static site.** There's no database, no server-side code and no plugins, so nothing needs security patches. Hosting on GitHub Pages is free.
- **The build is one Python script** (`build.py`, about 370 lines). It uses three libraries: Jinja2 for templates, PyYAML, and Markdown.
- **Why not Hugo or Jekyll:** downloading and running outside programs was blocked on the build machine. Plain Python is also easy for a psychology department to read and maintain.
- **Why not WordPress:** the old site's page builder (Divi) copied each faculty bio onto six pages, which made updating painful. Here, every fact is stored once.

---

## 3. Repository layout

| Path | What it is | Edited by |
|---|---|---|
| `site.yml` | Institute name, description, address, email, phone | Dashboard ("Contact details") |
| `menu.yml` | Navigation menu and footer links. `children_from: research_areas` lists the research areas automatically | Technical |
| `redirects.yml` | Old WordPress addresses mapped to new pages | Technical |
| `content/*.md` | Page text (Home, About, Research, Contact, and so on). The file name sets the URL and layout | Dashboard ("Page text") |
| `content/faculty/*.md` | One file per faculty member: name, degree, titles, photo, website, publications link, research areas; the body is the bio | Dashboard |
| `content/research/*.md` | One file per research area: name and summary; the body is an optional description | Dashboard |
| `content/news/*.md` | One file per news post: title, date, category, image, summary, draft; the body is the story | Dashboard |
| `data/fellows.yml` | List of graduate students and postdocs | Dashboard |
| `data/staff.yml` | List of administrative staff | Dashboard |
| `data/events.yml` | List of events | Dashboard |
| `data/publications.yml` | List of DOIs plus faculty authors, with optional typed-in overrides | Dashboard |
| `.cache/crossref.json` | Cached results of DOI lookups. Committed on purpose | Automatic |
| `static/` | CSS, favicon, and images (`images/people/`, `images/site/`, `images/news/`) | Dashboard uploads go here |
| `templates/*.html` | Jinja2 page templates | Technical |
| `build.py` | The site builder | Technical |
| `.pages.yml` | Pages CMS dashboard configuration | Technical |
| `.github/workflows/deploy.yml` | Build and publish workflow | Technical |
| `tools/check_links.py` | Checks every internal and external link in `_site/` | Technical |
| `tools/make_guide_pdf.py` | Rebuilds the editor-guide PDF from `EDITING-GUIDE.md` (needs Chrome) | Technical |
| `README.md` | Setup and technical reference | |
| `EDITING-GUIDE.md` | Plain-language guide for editors | |
| `_site/` | Build output (ignored by Git) | Generated |

---

## 4. What the build does

**Pages.** `content/<name>.md` becomes `/<name>/`. It uses `templates/<name>.html` if that template exists, otherwise `page.html`. `index.md` becomes `/` with `home.html`, and `404.md` becomes `/404.html`. Each research area gets `/research/<id>/`, and each news post gets `/news/<file-name>/`.

**Automatic behavior:**
- **People** are sorted by last name, ignoring text in parentheses: "Yuan Chang (YC) Leong" sorts under L.
- **Research-area pages** list every faculty member tagged with that area. Tags match the area's file name or its display name, ignoring case.
- **Events** are sorted by date and split into Upcoming and Past using today's Chicago date. The home page shows the next 3. The daily scheduled build keeps this up to date.
- **News** is sorted newest first, and the home page shows the latest 4. Posts with `draft: true` are skipped. If a post has no summary, the first 40 words are used.
- **Publications:** each DOI is looked up on Crossref (`api.crossref.org/works/<doi>`) for its title, authors (APA style, up to 10, then "et al."), journal and year. Anything typed in by hand takes priority. Results are saved in `.cache/crossref.json`, so each DOI is fetched only once: lookups run 3 at a time with up to 4 retries, since Crossref limits request rates. Faculty listed as authors get a "Featured papers (n)" button, and the Publications page has a filter by member (`?member=<slug>`).
- **Redirects:** each old address gets a small HTML page that forwards to the new one.
- **Warnings instead of failures.** A missing photo shows the person's initials. An unknown research area, a bad date, or a DOI that can't be resolved means that one item is skipped. These problems are listed:
  - on the private page **`/site-status/`**, which also shows when the site was last built (in Chicago time) and is marked `noindex`;
  - as `::warning::` notes in GitHub Actions.

  Only a genuinely broken YAML file (from hand-editing) stops a build, and then the live site stays as it was.

**Command-line options** for `build.py`:
- `--serve`: build, then preview at http://localhost:8000.
- `--base-path /repo`: prefix internal links for hosting in a subfolder. The workflow passes this automatically from `actions/configure-pages`.
- `--offline --out DIR`: write a copy that opens from disk, with relative links and `index.html` added to folder links. Used for the review demo.
- `--out DIR`: choose the output folder. The script refuses to write into the project folder itself.

---

## 5. The dashboard (Pages CMS)

- **What it is:** a free, open-source CMS (MIT license) at https://app.pagescms.org. It edits files in the GitHub repository directly and saves each change as a commit. It can also be self-hosted later if needed.
- **Collaborators** are invited **by email and don't need a GitHub account**. They can edit content and media. They can't change `.pages.yml`, manage collaborators, or use cache settings.
- **Configuration:** `.pages.yml` defines the menus and forms:
  - **News:** a collection with a date picker, category dropdown, image, draft checkbox and rich-text story.
  - **Events:** a list with a date picker. Fellows, Administration, Events and Publications each show one collapsed line per item; for that, their files store the list under a key (`events:`, `fellows:` and so on), because Pages CMS can only collapse a list that is a field, not a whole-file `list: true`. `build.py` accepts either layout.
  - **Publications:** a DOI field, plus faculty authors chosen from the Faculty collection.
  - **People:** Faculty (collection; areas chosen from Research areas), Fellows (list; role dropdown) and Administration (list).
  - **Research areas** (collection), **Page text** (11 pages) and **Contact details**.
  - A **"Publish site now"** button that re-runs the workflow through `workflow_dispatch` with a `payload` input.
  - `settings.commit.identity: user`, so commits record the editor's name.
- **Safety check:** every field stored in every content file is declared in `.pages.yml`, so saving from the dashboard can't drop data. This was checked by a script.
- **Not yet verified in the live tool:**
  - the placement of the repository-level `actions:` block;
  - how reference fields (`value: "{primary}"`) store values;
  - date formatting.

  The build already accepts dates either quoted or unquoted, and matches references by name or file name.
- **Known side effect:** saving through Pages CMS removes the `#` comments at the top of the `data/*.yml` files. That's harmless.

---

## 6. One-time setup checklist

1. **Create the GitHub repository.** Make it **public**, because free GitHub Pages needs that. Ideally put it under an IMB or UChicago GitHub *organization*, not a personal account, so ownership can pass on. Don't add a README, .gitignore or license.
2. **Commit the pending changes, then push.** On the Mac, run `brew install gh` and `gh auth login`, then:
   `cd ~/data/imb-website && git remote add origin https://github.com/<org>/imb-website.git && git push -u origin main`
3. **Turn on Pages:** **Settings → Pages → Source: GitHub Actions**. Then go to **Actions → Build and publish site → Run workflow**. The first automatic run fails if Pages wasn't turned on yet; that's expected.
4. **Check the published site** at `https://<org>.github.io/imb-website/`. Run `python tools/check_links.py` against a local build if needed.
5. **Connect Pages CMS:** sign in at app.pagescms.org with GitHub, install the Pages CMS GitHub App on the repository, and open the project. Click through every section, then save one test edit and confirm it publishes.
6. **Invite Anissha** by email as a collaborator in Pages CMS. Fill in the support contact on page 4 of the PDF guide, and send it to her.
7. **Switch the domain:**
   1. In GitHub, go to **Settings → Pages → Custom domain** and enter `imb.uchicago.edu`.
   2. Ask UChicago IT Services to point the DNS record to `<org>.github.io` (a CNAME).
   3. Once it works, tick **Enforce HTTPS**.

   The old Voices site keeps running until DNS changes, so there's no downtime. Old addresses redirect automatically.
8. **Retire the old site.** Once the new domain works, ask whoever administers UChicago Voices to unpublish the old site. Keep an export for the record.

---

## 7. Content left to review

- **Contact email** is blank in `site.yml`; add a general IMB address. The old site's footer showed only IT Services' details.
- **Perception** has no one-line summary; the old site had none.
- **The Fellows list dates from 2023.** Seven fellows' Psychology directory links now return 404, so they were removed, with a note left on each entry in `data/fellows.yml`. Those people have probably moved on.
- **Hyung-Bum Park's link** pointed to Daisy Li's page on the old site, so it was removed; add the correct link if available.
- **The four old "Latest Research" items** are now news posts dated 2023-10-01, which is when they were uploaded to the old site.
- **Events:** all 24 events are from 2023 and 2024, so the Upcoming list is empty until new events are added.
- **Changes made while migrating:**
  - three typos in bios ("Pyschology", "in in", a missing space);
  - the Psychology MA and PhD links, which were dead, now go to https://psychology.uchicago.edu/graduate-study;
  - the old Director's Message page held only placeholder text, so the director's bio and former directors now appear on the About page;
  - the empty News page was replaced by the real News section;
  - the old contact form, which was a WordPress plugin, was replaced with the address and a map.
- **Links that refuse automated checks:** a few publisher and doi.org links return 403 to the link checker but work in a browser.

---

## 8. Ongoing maintenance

**Editors (Anissha)** follow `EDITING-GUIDE.md`. Its suggested routine: add each quarter's events, post news monthly, add papers by DOI as they come out, update fellows each September, and have faculty review their bios yearly.

**Technical tasks:**
- **Add a page:**
  1. Create `content/<name>.md` with `title:` front matter.
  2. Optionally, add `templates/<name>.html`.
  3. Add the page to `.pages.yml` (Page text group) and to `menu.yml`.
- **Add a field:** add it to the content files *and* to `.pages.yml`. Then use it in a template.
- **Change dropdown options** (news categories, fellow roles): edit `.pages.yml`.
- **Change the look:** edit `static/css/style.css` (UChicago maroon `#800000`) and `templates/base.html` (header, navigation, footer).
- **Rebuild the editor-guide PDF:** run `python tools/make_guide_pdf.py`.
- **Make a review demo:** run `python build.py --offline --out ../IMB-website-demo` and zip that folder.
- **Check links:** run `python build.py && python tools/check_links.py`.

**Things to watch:**
- **GitHub turns off scheduled workflows** in public repositories after 60 days with no commits. Edits from the dashboard count as activity. After a long quiet stretch, re-enable the workflow under **Actions → Build and publish site**, or just make any edit. Until then, past events won't move off the Upcoming list.
- **Workflow action versions** (`actions/checkout@v4`, `setup-python@v5`, `configure-pages@v5`, `upload-pages-artifact@v3`, `deploy-pages@v4`) may need updating every year or two, when GitHub announces deprecations.
- **Python:** the workflow uses 3.12. The libraries in `requirements.txt` are stable and widely used.
- **If Pages CMS ever went away,** the content is still plain files in GitHub, and editing on GitHub keeps working. The `.pages.yml` format is similar to other Git-based CMS tools, such as Decap.

---

## 9. Where the content came from

The old site was WordPress (UChicago Voices, Divi theme). Content was pulled from its public REST API at `https://imb.uchicago.edu/wp-json/wp/v2/pages?per_page=100` (20 pages, no posts). Photos came from `imb.uchicago.edu/files/...` and were resized to at most 600 px (people) or 1400 px (site images) with macOS `sips`. The one-off migration scripts weren't kept; their output is the content now in the repository. The extraction logic is included in the source appendix for reference.

---

## 10. Source code

The full source of every code and configuration file is in the separate canvas **"IMB website handoff: source code"**, and in the repository itself.
