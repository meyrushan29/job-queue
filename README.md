# Job queue — ITPro.lk

**Language:** English · [தமிழ்](README.ta.md) · [සිංහල](README.si.md)

Scores every job on ITPro.lk against your skills and lists them on a dashboard, best match first. Open it daily and apply to the ones at the top.

No Telegram required. No app to install. A browser is enough.

**Live URL:** `https://<your-username>.github.io/<repo-name>/`

---

## Using this repo for yourself

This is a template. Fork it, adjust it to your own skills, and host it on your own GitHub account. Everyone needs their own copy — the scoring logic and data live inside each repo.

### 1. Fork and clone

**Fork** this repo on GitHub (the Fork button, top right). Then clone your fork:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Tune the filters to your skills

All the settings live at the top of `job_alert.py`:

| Setting | What it does |
|---|---|
| `KEYWORDS` | How much each skill is worth. A hit in the title counts triple. |
| `TITLE_BLOCKLIST` | Skip the job if this word appears in the title. |
| `ALLOWED_CATEGORIES` | ITPro's category ids (list below). |
| `SCORE_THRESHOLD` | Only show jobs scoring above this. |
| `ALLOWED_LOCATIONS` | Locations you'd actually accept. |

**Too few jobs showing up?** Lower `SCORE_THRESHOLD` from 8 to 5.
**Too many?** Raise it to 12.
**Want internships too?** Remove `"intern"` from `TITLE_BLOCKLIST`.

Category ids:

| id | Category |
|---|---|
| 21 | Software Engineering |
| 38 | DevOps and Cloud |
| 39 | Quality Assurance |
| 41 | Mobile Development |
| 42 | AI and Data |
| 43 | Web Development |

### 3. Try it locally first (optional)

```bash
python job_alert.py          # builds docs/jobs.json
cd docs && python -m http.server 8000
```

Open `http://localhost:8000` in a browser. To preview in the terminal only: `python job_alert.py --dry-run`. Python 3.9+ is all you need — no `pip install` required.

### 4. Push to GitHub and enable Pages

```bash
git add .
git commit -m "My filters"
git push
```

Repo → **Settings** → **Pages** → set Source to **GitHub Actions**. Then Repo → **Actions** tab → **Refresh job queue** → **Run workflow** (the first run has to be triggered by hand). Once the green tick appears, your URL will show up under Settings → Pages.

After that, the workflow refreshes the dashboard automatically every hour, and rebuilds whenever you push.

Applied/hidden marks are saved in the browser (localStorage) — they only show up on the device you marked them from.

---

## Telegram (optional)

Only if you want it. Add `TELEGRAM_BOT_TOKEN` (from BotFather) and `TELEGRAM_CHAT_ID` under Settings → Secrets and variables → Actions to get a message for new matches; leave them unset and the dashboard works on its own.
