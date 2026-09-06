# Job queue — ITPro.lk

ITPro.lk-ல் இருக்கும் வேலைகளை உங்கள் skills-க்கு ஏற்ப score போட்டு,
ஒரு dashboard-ல் வரிசைப்படுத்திக் காட்டும். தினமும் அதைத் திறந்து,
மேலே இருக்கும் வேலைகளுக்கு apply பண்ணுங்கள்.

Telegram தேவையில்லை. App install பண்ண வேண்டாம். Browser போதும்.

**Live URL:** `https://<your-username>.github.io/<repo-name>/`

---

## இந்த repo-வை உங்களுக்காக use பண்ண

இது ஒரு template. Fork பண்ணி, உங்கள் skills-க்கு ஏற்ப மாற்றி, உங்கள்
GitHub account-ல் host பண்ணலாம். ஒவ்வொருவருக்கும் தனித்தனி copy வேண்டும் —
scoring logic-ம் data-வும் அந்தந்த repo-வுக்குள்ளேயே இருக்கும்.

### 1. Fork பண்ணி clone பண்ணுங்கள்

GitHub-ல் இந்த repo-வை **Fork** பண்ணுங்கள் (மேலே வலது மூலையில் உள்ள
Fork பொத்தான்). பிறகு உங்கள் fork-ஐ clone பண்ணுங்கள்:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. உங்கள் skills-க்கு ஏற்ப filters மாற்றுங்கள்

`job_alert.py` கோப்பின் மேல் பகுதியில் எல்லா settings-உம் இருக்கின்றன:

| Setting | என்ன செய்யும் |
|---|---|
| `KEYWORDS` | எந்த skill-க்கு எவ்வளவு மதிப்பு. Title-ல் வந்தால் 3 மடங்கு. |
| `TITLE_BLOCKLIST` | இந்த வார்த்தை title-ல் இருந்தால் விட்டுவிடும். |
| `ALLOWED_CATEGORIES` | ITPro-வின் category ids (கீழே பட்டியல்). |
| `SCORE_THRESHOLD` | இதற்கு மேல் score வந்தால் மட்டும் காட்டும். |
| `ALLOWED_LOCATIONS` | நீங்கள் ஏற்கும் இடங்கள். |

**வேலைகள் குறைவாக வருகிறதா?** `SCORE_THRESHOLD` -ஐ 8 → 5 ஆகக் குறையுங்கள்.
**அதிகமாகவா?** 12 ஆக உயர்த்துங்கள்.
**Internship-ம் வேண்டுமா?** `TITLE_BLOCKLIST`-ல் இருந்து `"intern"` -ஐ நீக்குங்கள்.

Category ids:

| id | Category |
|---|---|
| 21 | Software Engineering |
| 38 | DevOps and Cloud |
| 39 | Quality Assurance |
| 41 | Mobile Development |
| 42 | AI and Data |
| 43 | Web Development |

### 3. Local-ல் சோதித்துப் பாருங்கள் (optional)

```bash
python job_alert.py          # docs/jobs.json உருவாக்கும்
cd docs && python -m http.server 8000
```

Browser-ல் `http://localhost:8000` திறங்கள். Terminal-ல் மட்டும் பார்க்க:
`python job_alert.py --dry-run`. Python 3.9+ மட்டும் போதும், `pip install`
எதுவும் தேவையில்லை.

### 4. GitHub-ல் push பண்ணி Pages-ஐ enable பண்ணுங்கள்

```bash
git add .
git commit -m "My filters"
git push
```

Repo → **Settings** → **Pages** → Source: **GitHub Actions** என்று
தேர்ந்தெடுங்கள். பிறகு Repo → **Actions** tab → **Refresh job queue** →
**Run workflow** (முதல் முறை கைமுறையாக run பண்ணணும்). பச்சை tick
வந்தபிறகு, Settings → Pages-ல் உங்கள் URL தெரியும்.

அதன் பிறகு workflow தானாக ஒவ்வொரு மணி நேரமும் ஓடி dashboard-ஐ update
பண்ணும், Push பண்ணும்போதும் rebuild ஆகும்.

Applied/hidden marks browser-ல் (localStorage) சேமிக்கப்படும் — எந்த
phone/laptop-ல் திறக்கிறீர்களோ, அதில் மட்டும் தெரியும்.

---

## Telegram (optional)

வேண்டுமானால் மட்டும். Settings → Secrets and variables → Actions-ல்
`TELEGRAM_BOT_TOKEN` (BotFather-ல் இருந்து), `TELEGRAM_CHAT_ID` ஆகிய
இரண்டு secrets-ஐயும் போட்டால் புதிய வேலைகளுக்கு message-ம் வரும்;
போடாவிட்டால் dashboard மட்டும் வேலை செய்யும்.
