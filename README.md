# Job queue — ITPro.lk

ITPro.lk-ல் இருக்கும் வேலைகளை உங்கள் skills-க்கு ஏற்ப score போட்டு,
ஒரு dashboard-ல் வரிசைப்படுத்திக் காட்டும். தினமும் அதைத் திறந்து,
மேலே இருக்கும் வேலைகளுக்கு apply பண்ணுங்கள்.

Telegram தேவையில்லை. App install பண்ண வேண்டாம். Browser போதும்.

**Live URL:** `https://<your-username>.github.io/<repo-name>/`

---

## என்ன செய்யும்

- ஒவ்வொரு மணி நேரமும் ITPro.lk API-ல் இருந்து வேலைகளை எடுக்கும்
- உங்கள் skills-ஐ வைத்து ஒவ்வொன்றுக்கும் score கொடுக்கும்
- Senior roles, sales roles, தூர இடங்களை filter பண்ணும்
- Score வரிசையில் dashboard-ல் காட்டும்
- **Mark applied** / **Not for me** — queue குறைந்துகொண்டே வரும்

உங்கள் applied/hidden marks browser-ல் (localStorage) சேமிக்கப்படும்.
அதனால் எந்த phone/laptop-ல் திறக்கிறீர்களோ, அதில் மட்டும் தெரியும்.

---

## Setup (சுமார் 10 நிமிடம்)

### 1. GitHub-ல் push பண்ணுங்கள்

```bash
git init
git add .
git commit -m "Job queue"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

Repo **public**-ஆக இருக்க வேண்டும் (GitHub Pages இலவசமாக வேலை செய்ய).

### 2. Pages-ஐ enable பண்ணுங்கள்

Repo → **Settings** → **Pages** → Source: **GitHub Actions** என்று தேர்ந்தெடுங்கள்.

### 3. முதல் முறை run பண்ணுங்கள்

Repo → **Actions** tab → **Refresh job queue** → **Run workflow**.

பச்சை tick வந்தபிறகு, Settings → Pages-ல் உங்கள் URL தெரியும்.
அதை phone-ல் bookmark பண்ணுங்கள் (iPhone: Share → Add to Home Screen —
app மாதிரியே திறக்கும்).

---

## முதலில் local-ல் பார்க்க

```bash
python job_alert.py          # docs/jobs.json உருவாக்கும்
cd docs && python -m http.server 8000
```

Browser-ல் `http://localhost:8000` திறங்கள்.

`jobs.json` இல்லாவிட்டால் sample data காட்டும் — layout எப்படி இருக்கும்
என்று பார்க்கலாம்.

Terminal-ல் மட்டும் பார்க்க: `python job_alert.py --dry-run`

---

## Filters-ஐ மாற்ற

`job_alert.py` மேல் பகுதியில் எல்லாம் இருக்கின்றன.

| Setting | என்ன செய்யும் |
|---|---|
| `KEYWORDS` | எந்த skill-க்கு எவ்வளவு மதிப்பு. Title-ல் வந்தால் 3 மடங்கு. |
| `TITLE_BLOCKLIST` | இந்த வார்த்தை title-ல் இருந்தால் விட்டுவிடும். |
| `ALLOWED_CATEGORIES` | ITPro-வின் category ids. |
| `SCORE_THRESHOLD` | இதற்கு மேல் score வந்தால் மட்டும் காட்டும். |
| `ALLOWED_LOCATIONS` | நீங்கள் ஏற்கும் இடங்கள். |

**வேலைகள் குறைவாக வருகிறதா?** `SCORE_THRESHOLD` -ஐ 8 → 5 ஆகக் குறையுங்கள்.
**அதிகமாகவா?** 12 ஆக உயர்த்துங்கள்.
**Internship-ம் வேண்டுமா?** `TITLE_BLOCKLIST`-ல் இருந்து `"intern"` -ஐ நீக்குங்கள்.

Push பண்ணினால் workflow தானாக ஓடி dashboard-ஐ update பண்ணும்.

### Category ids

| id | Category |
|---|---|
| 21 | Software Engineering |
| 38 | DevOps and Cloud |
| 39 | Quality Assurance |
| 41 | Mobile Development |
| 42 | AI and Data |
| 43 | Web Development |

---

## Telegram (optional)

வேண்டுமானால் மட்டும். Secrets இரண்டையும் போட்டால் புதிய வேலைகளுக்கு
message-ம் வரும்; போடாவிட்டால் dashboard மட்டும் வேலை செய்யும்.

Settings → Secrets and variables → Actions:
`TELEGRAM_BOT_TOKEN` (BotFather-ல் இருந்து), `TELEGRAM_CHAT_ID`.

---

## Files

| File | Purpose |
|---|---|
| `job_alert.py` | fetch, score, filter, export |
| `docs/index.html` | dashboard (dependency இல்லை) |
| `docs/jobs.json` | தானாக உருவாகும் data |
| `seen.json` | ஏற்கனவே பார்த்த job ids |
| `.github/workflows/job-queue.yml` | மணிக்கொருமுறை ஓடி Pages-ல் publish பண்ணும் |

Python 3.9+ மட்டும் போதும். `pip install` எதுவும் தேவையில்லை.

---

## சிக்கல் வந்தால்

**Dashboard-ல் sample data தெரிகிறது** — `jobs.json` இன்னும் உருவாகவில்லை.
Actions-ல் workflow ஒருமுறை run பண்ணுங்கள்.

**Actions fail ஆகிறது** — Settings → Pages → Source **GitHub Actions**-ஆக
இருக்கிறதா என்று பாருங்கள்.

**Applied marks காணவில்லை** — அவை browser-ல் சேமிக்கப்படுகின்றன.
வேறு phone அல்லது private window-ல் தெரியாது.

**எந்த வேலையும் வரவில்லை** — `python job_alert.py --dry-run` run பண்ணி,
`SCORE_THRESHOLD` -ஐ குறையுங்கள்.

---

## Note

ITPro.lk-ன் public API-ஐ மட்டுமே பயன்படுத்துகிறது (`/api/v1/jobs`) —
scraping இல்லை, login இல்லை, மணிக்கு ஒரு request மட்டும்.
API structure மாறினால் script-ஐ update பண்ண வேண்டியிருக்கும்.

ITPro.lk-ல் email alerts (`itpro.lk/subscribe/`) மற்றும் RSS feeds
ஏற்கனவே இருக்கின்றன. Filtering தேவையில்லை என்றால் அவையே போதும்.
