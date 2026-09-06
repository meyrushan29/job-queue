# Job queue — ITPro.lk

**Language:** [English](README.md) · [தமிழ்](README.ta.md) · සිංහල

ITPro.lk හි ඇති සෑම රැකියාවක්ම ඔබේ කුසලතාවලට (skills) අනුව ලකුණු දී,
dashboard එකක හොඳම match එක මුලින්ම එන ලෙස පෙළගස්වා පෙන්වයි. දිනපතා එය
විවෘත කර, ඉහළින්ම ඇති රැකියාවලට apply කරන්න.

Telegram අවශ්‍ය නැත. App install කිරීමට අවශ්‍ය නැත. Browser එකක් ප්‍රමාණවත්.

**Live URL:** `https://<your-username>.github.io/<repo-name>/`

---

## මෙම repo එක ඔබටත් භාවිත කරන්නේ කෙසේද

මෙය template එකකි. Fork කර, ඔබේ කුසලතාවලට අනුව වෙනස් කර, ඔබේම GitHub
ගිණුමේ host කළ හැක. සෑම කෙනෙකුටම වෙනම copy එකක් අවශ්‍යයි — scoring
logic සහ data එම repo එක තුළම පවතී.

### 1. Fork කර clone කරන්න

GitHub හි මෙම repo එක **Fork** කරන්න (ඉහළ දකුණු කෙළවරේ ඇති Fork
බොත්තම). පසුව ඔබේ fork එක clone කරන්න:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. ඔබේ කුසලතාවලට අනුව filters වෙනස් කරන්න

`job_alert.py` ගොනුවේ ඉහළ කොටසේ සියලුම settings තිබේ:

| Setting | කරන්නේ මොකක්ද |
|---|---|
| `KEYWORDS` | කුමන skill එකට කොපමණ අගයක්ද. Title එකේ තිබුණොත් 3 ගුණයක්. |
| `TITLE_BLOCKLIST` | මෙම වචනය title එකේ තිබුණොත් එම රැකියාව මඟහරියි. |
| `ALLOWED_CATEGORIES` | ITPro හි category ids (පහත ලැයිස්තුව). |
| `SCORE_THRESHOLD` | මින් ඉහළ score එකක් ලැබුණොත් පමණක් පෙන්වයි. |
| `ALLOWED_LOCATIONS` | ඔබ පිළිගන්නා ස්ථාන. |

**රැකියා අඩුවෙන් එනවාද?** `SCORE_THRESHOLD` එක 8 → 5 දක්වා අඩු කරන්න.
**වැඩිපුරද?** 12 දක්වා වැඩි කරන්න.
**Internship ද ඕනෑ?** `TITLE_BLOCKLIST` වෙතින් `"intern"` ඉවත් කරන්න.

Category ids:

| id | Category |
|---|---|
| 21 | Software Engineering |
| 38 | DevOps and Cloud |
| 39 | Quality Assurance |
| 41 | Mobile Development |
| 42 | AI and Data |
| 43 | Web Development |

### 3. Local එකේ පරීක්ෂා කර බලන්න (optional)

```bash
python job_alert.py          # docs/jobs.json සාදයි
cd docs && python -m http.server 8000
```

Browser එකේ `http://localhost:8000` විවෘත කරන්න. Terminal එකේ පමණක්
බලන්න: `python job_alert.py --dry-run`. Python 3.9+ ප්‍රමාණවත්,
`pip install` කිසිවක් අවශ්‍ය නැත.

### 4. GitHub වෙත push කර Pages enable කරන්න

```bash
git add .
git commit -m "My filters"
git push
```

Repo → **Settings** → **Pages** → Source: **GitHub Actions** ලෙස
තෝරන්න. පසුව Repo → **Actions** tab → **Refresh job queue** →
**Run workflow** (පළමු වතාවට manual ලෙස run කළ යුතුයි). කොළ tick
එක පෙන්වූ පසු, Settings → Pages හි ඔබේ URL එක පෙනේවි.

ඉන් පසු workflow එක ස්වයංක්‍රීයව සෑම පැයකටම වරක් run වී dashboard
එක update කරයි, push කරන විටත් rebuild වේ.

Applied/hidden marks browser එකේ (localStorage) save වේ — ඔබ mark
කරන phone/laptop එකේ පමණක් පෙනේ.

---

## Telegram (optional)

අවශ්‍ය නම් පමණයි. Settings → Secrets and variables → Actions හි
`TELEGRAM_BOT_TOKEN` (BotFather වෙතින්), `TELEGRAM_CHAT_ID` යන දෙක
දැමුවහොත් අලුත් රැකියාවලට message එකක් එයි; නොදැමුවහොත් dashboard
එක පමණක් වැඩ කරයි.
