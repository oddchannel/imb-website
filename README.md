# Institute for Mind and Biology website

This is the website for the Institute for Mind and Biology (IMB) at the University of Chicago.

All of the site's content is kept in simple text files. To change the site, you edit one of those files. When you save the change on GitHub, the site rebuilds and publishes itself, usually within a couple of minutes. You don't need to know any code.

---

## Where everything lives

| To change…                                        | Edit this file              |
|---------------------------------------------------|-----------------------------|
| Faculty members (bios, photos, links, research areas) | `data/faculty.yml`      |
| Fellows (graduate students & postdocs)            | `data/fellows.yml`          |
| Administration / staff                            | `data/staff.yml`            |
| Events                                            | `data/events.yml`           |
| "Latest Research" on the home page                | `data/highlights.yml`       |
| Research area names and one-line summaries        | `data/research_areas.yml`   |
| Page text (Home intro, About, Research, Contact…) | `content/*.md`              |
| Menu, address, contact email, footer links        | `site.yml`                  |
| Photos and images                                 | `static/images/`            |

**Each person is listed once.** The research-area pages (Cognition, Perception, etc.) are built automatically from the `areas:` tags in `data/faculty.yml`. To add someone to an area, add the tag to their entry there.

Events are **sorted automatically** and move from "Upcoming" to "Past" on their own, so you only ever add events, never move them.

---

## Two ways to edit

### Option A: Fill in forms (easiest)

1. Go to **https://app.pagescms.org** and sign in with GitHub.
2. Open this website's repository.
3. Choose **Faculty**, **Fellows**, **Administration**, **Events**, or **Home page research highlights** from the menu, make your change in the form, and click **Save**.

Photos can be uploaded directly in the form.

> Note: saving through Pages CMS removes the explanatory `#` comments at the top of the data files. That's harmless; this guide covers the same information.

### Option B: Edit the file on GitHub

1. On GitHub, open the file you want (see the table above).
2. Click the ✏️ pencil icon (**Edit this file**).
3. Make your change. Copy an existing entry and change the details; that's the easiest way to keep the format right.
4. Click **Commit changes…**, write a short note (e.g. "Add spring cookout"), and confirm.

To add a photo: open the `static/images/people/` folder, click **Add file → Upload files**, then put its path (e.g. `/images/people/smith.jpg`) in the person's `photo:` line.

---

## Common tasks (Option B examples)

### Add an event
Add this anywhere in `data/events.yml`:

```yaml
- title: Cookie Hour
  date: 2025-11-12
  time: 3:30 PM
  location: BPSB Atrium
  description: Optional extra details.
```

The date **must** be written as year-month-day: `2025-11-12`.

### Add a fellow
In `data/fellows.yml`:

```yaml
- name: "Jane Doe"
  role: Graduate Student
  lab: Kay Lab
  photo: /images/people/fellow-jane-doe.jpg
  link: https://psychology.uchicago.edu/people/...
```

If there's no photo, leave `photo:` empty and the site shows the person's initials instead.

### Remove someone
Delete their whole entry, from their `- name:` line down to the line just before the next `- name:`.

### Add a faculty member
Copy an existing faculty entry in `data/faculty.yml` and change it. Valid research `areas` are:
`cognition`, `perception`, `development`, `neuroendocrinology`, `computational-neuroscience`.

### Change page text
Files in `content/` are written in Markdown. Plain paragraphs are just text. A blank line starts a new paragraph, `## Heading` makes a heading, and `[link text](https://...)` makes a link. Leave the block between the two `---` lines at the top alone unless you know what it does.

---

## Formatting rules (YAML files)

- **Indent with spaces, never tabs.** Keep the same indentation as the entries around you.
- If a value contains a colon followed by a space (`: `), or starts with a special character, wrap it in double quotes: `title: "Note: rescheduled"`.
- Long text such as a bio goes after `bio: |` on the following lines, indented 4 spaces. Leave a blank line between paragraphs.

**If you make a mistake, nothing breaks.** The site checks your edit before publishing. If something is wrong (a typo in a research area, a photo file that doesn't exist, a badly written date), the update is not published and the live site stays as it was. To see the error message, open the repository's **Actions** tab and click the failed run (marked with a red ✗). The message names the file and the person or event to fix.

---

## Previewing on your own computer (optional)

You'll need Python 3. Then run:

```bash
pip install -r requirements.txt
```

```bash
python build.py --serve
```

Open http://localhost:8000 to see the site. Run the command again after making changes.

---

## One-time setup (for whoever sets up hosting)

1. Create a GitHub repository (ideally under a UChicago or IMB GitHub organization so it isn't tied to one person) and upload this folder.
2. In the repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The site will publish to `https://<org>.github.io/<repo>/`. The workflow in `.github/workflows/deploy.yml` handles everything, including a daily rebuild so past events are moved automatically.
4. **Custom domain:** to serve it at `imb.uchicago.edu`, enter the domain under **Settings → Pages → Custom domain**, and ask UChicago IT Services to point the `imb.uchicago.edu` DNS record at GitHub Pages (a CNAME to `<org>.github.io`). Old addresses from the previous WordPress site (e.g. `/staff-profile-2/`, `/cognition/`) automatically redirect to the new pages.
5. Give editors access: add them as collaborators on the repository (they need a free GitHub account).

### How it works (for the technically curious)

`build.py` is a short Python script that reads the YAML/Markdown files, fills in the HTML templates in `templates/`, and writes a plain static website into `_site/`. Styling is in `static/css/style.css`. There's no database, no plugins, and nothing to patch or update for security.
