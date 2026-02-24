# Sadhana — Content Update Guide

This guide explains how to update app content **without releasing a new app version**. All dynamic content lives in this DharmicData repo. The Sadhana app fetches it on launch.

**How it works:** The app loads bundled (offline) data first, then checks this repo for updates. If the remote version is newer, it replaces the local data and caches it on disk for offline use.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [App Config](#app-config)
3. [Live Darshan (Temples)](#live-darshan)
4. [Hindu Calendar (Panchang)](#hindu-calendar)
5. [Aarti / Chalisa / Mantra (Lyrics)](#lyrics)
6. [Stories (Katha)](#stories)
7. [Testing Changes](#testing-changes)

---

## Quick Reference

| Content | File to Edit | Bump Version? |
|---------|-------------|---------------|
| Add/remove temple streams | `live-darshan-catalog.json` | Yes (`version` field) |
| Add/fix festivals, improve templates | `hindu-calendar.json` | Yes (`version` field) |
| Add new aarti/chalisa/mantra | `lyrics-catalog.json` + `lyrics/{id}.json` | No |
| Add new story | `stories/stories-catalog.json` + `stories/{id}.json` | No (use `version` per entry) |
| Change remote URLs, API keys, labels | `app-config.json` | No |

After editing, **commit and push to `main`**. Changes go live within minutes (GitHub raw CDN cache is ~5 min).

---

## App Config

**File:** `app-config.json`

This is the master config file fetched on every app launch. It controls remote URLs, display labels, and API keys.

```json
{
  "image_cache_days": 7,
  "lyrics_type_labels": {
    "aarti": { "hi": "आरती", "en": "Aarti" },
    "chalisa": { "hi": "चालीसा", "en": "Chalisa" }
  },
  "lyrics_type_order": ["aarti", "chalisa", "bhajan", "mantra", "stotra"],
  "lyrics_remote_base_url": "https://raw.githubusercontent.com/.../lyrics/",
  "stories_remote_base_url": "https://raw.githubusercontent.com/.../stories/",
  "darshan_remote_url": "https://raw.githubusercontent.com/.../live-darshan-catalog.json",
  "calendar_remote_url": "https://raw.githubusercontent.com/.../hindu-calendar.json",
  "feedback_email": "jyoti0512shukla@gmail.com"
}
```

**What you can change here:**
- `lyrics_type_labels` — add a new type (e.g. `"kavita"`) with Hindi/English labels
- `lyrics_type_order` — reorder or add types in the filter bar
- `image_cache_days` — how long story images are cached before re-downloading
- Remote URLs — if you move content to a different host
- `feedback_email` — change the support email

---

## Live Darshan

**File:** `live-darshan-catalog.json`

### Add a New Temple

1. Open `live-darshan-catalog.json`
2. Add a new entry to the `temples` array:

```json
{
  "id": "tirupati-balaji",
  "name": "तिरुपति बालाजी",
  "nameEn": "Tirupati Balaji Temple",
  "deity": "Vishnu ji",
  "location": "Tirupati, Andhra Pradesh",
  "streamUrl": "https://livebhagwan.com/...",
  "youtubeVideoId": "YOUTUBE_VIDEO_ID",
  "streamType": "web",
  "category": "vishnu",
  "aartiInfo": "6:00 AM - 9:00 PM"
}
```

3. If the temple needs a new category, add it to the `categories` array:

```json
{ "id": "devi", "name": "Devi", "nameHi": "देवी" }
```

4. **Bump `version`** (e.g. `1` → `2`) at the top of the file
5. Commit and push

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (lowercase, hyphenated) |
| `name` | Yes | Hindi name |
| `nameEn` | Yes | English name |
| `deity` | Yes | Deity name (used for icon: "Ganesh ji", "Shiva ji", "Krishna ji", "Vishnu ji", etc.) |
| `location` | Yes | City, State |
| `streamUrl` | Yes | Fallback web URL if YouTube embed fails |
| `youtubeVideoId` | No | YouTube video/live ID for in-app embed |
| `streamType` | Yes | Usually `"web"` |
| `category` | Yes | Must match a category `id` |
| `aartiInfo` | No | Aarti timing text (shown below temple name) |

### Update a YouTube Stream ID

YouTube live stream IDs change periodically. To update:
1. Find the new video ID from the temple's YouTube channel
2. Update `youtubeVideoId` for that temple
3. Bump `version`, commit and push

---

## Hindu Calendar

**File:** `hindu-calendar.json`

This file contains festivals, ekadashis, vrats, and event templates for 2025-2030.

### Structure

```json
{
  "version": 1,
  "description": "Hindu Calendar - Festivals, Vrats & Ekadashi (2025-2030)",
  "sources": ["TithiToday", "calendar-bharat", "prokerala", "drikpanchang"],
  "templates": {
    "template_key": {
      "significance": "Why this day matters",
      "practices": ["Fast", "Pray", "Charity"],
      "avoid": ["Grains", "Rice"]
    }
  },
  "events": [
    {
      "date": "2026-03-10",
      "name": "Maha Shivaratri",
      "category": "festival",
      "tithi": "Chaturdashi",
      "paksha": "Krishna Paksha",
      "template": "maha_shivaratri",
      "pujaId": "shivratri-puja"
    }
  ]
}
```

### Add a New Event

1. Add a template (if it doesn't already exist) in the `templates` object:

```json
"navratri_day1": {
  "significance": "First day of Navratri. Worship of Maa Shailputri.",
  "practices": ["Fast", "Offer red flowers", "Light akhand jyoti"],
  "avoid": ["Non-veg food", "Alcohol"]
}
```

2. Add the event to the `events` array:

```json
{
  "date": "2026-10-01",
  "name": "Navratri Day 1 - Shailputri",
  "category": "festival",
  "tithi": "Pratipada",
  "paksha": "Shukla Paksha",
  "template": "navratri_day1",
  "pujaId": null
}
```

3. Bump `version`, commit and push

### Improve Existing Templates

To improve the significance text, add Hindi, or expand practices:
1. Find the template key in `templates`
2. Edit the text
3. Bump `version`, commit and push

### Categories

| Category | What it covers |
|----------|---------------|
| `ekadashi` | All 24 ekadashis per year |
| `festival` | Major festivals (Diwali, Holi, Navratri, etc.) |
| `vrat` | Fasting days (Karva Chauth, Santoshi Mata, etc.) |
| `purnima` | Full moon days |
| `auspicious` | Auspicious occasions (Akshaya Tritiya, etc.) |

### Link to Puja Guide

If a Puja guide exists in the app for a festival, set `pujaId` to match the puja's ID. The app will show a "Puja Guide" button on the calendar event.

---

## Lyrics

**Catalog:** `lyrics-catalog.json`
**Content files:** `lyrics/{id}.json`

### Add a New Aarti/Chalisa/Mantra

**Step 1:** Add a catalog entry to `lyrics-catalog.json`:

```json
{
  "id": "durga-chalisa",
  "name": "श्री दुर्गा चालीसा",
  "nameEn": "Durga Chalisa",
  "deity": "Durga",
  "category": "goddess",
  "type": "chalisa",
  "source": "remote"
}
```

**Step 2:** Create `lyrics/durga-chalisa.json`:

```json
{
  "id": "durga-chalisa",
  "name": "श्री दुर्गा चालीसा",
  "nameEn": "Durga Chalisa",
  "deity": "Durga",
  "category": "goddess",
  "sourceUrl": "https://...",
  "sourceName": "Traditional",
  "sections": [
    {
      "id": "doha-1",
      "title": "दोहा",
      "titleEn": "Doha",
      "verses": [
        {
          "lineHindi": "नमो नमो दुर्गे सुख करनी",
          "lineEn": "Namo Namo Durge Sukh Karni"
        }
      ]
    },
    {
      "id": "chaupai",
      "title": "चौपाई",
      "titleEn": "Chaupai",
      "verses": [
        {
          "lineHindi": "...",
          "lineEn": "..."
        }
      ]
    }
  ]
}
```

**Step 3:** Commit and push both files.

### Field Reference — Catalog Entry

| Field | Required | Values |
|-------|----------|--------|
| `id` | Yes | Unique, lowercase, hyphenated |
| `name` | Yes | Hindi name |
| `nameEn` | Yes | English name |
| `deity` | Yes | Deity name |
| `category` | Yes | `"god"`, `"goddess"`, `"vedic"`, `"saint"` |
| `type` | Yes | `"aarti"`, `"chalisa"`, `"bhajan"`, `"mantra"`, `"stotra"` |
| `source` | Yes | `"remote"` for new additions, `"bundle"` for bundled ones |

### Add a New Type

If you want to add a completely new type (e.g. `"kavita"`):
1. Add entries with `"type": "kavita"` in the catalog
2. Add the label in `app-config.json` → `lyrics_type_labels`
3. Add `"kavita"` to `lyrics_type_order` in `app-config.json`

---

## Stories

**Catalog:** `stories/stories-catalog.json`
**Content files:** `stories/{id}.json`
**Images:** `story-images/{image-id}.png`

### Add a New Story

**Step 1:** Add a catalog entry to `stories/stories-catalog.json`:

```json
{
  "id": "panchatantra-thirsty-crow",
  "title": "The Thirsty Crow",
  "titleHi": "प्यासा कौआ",
  "category": "panchatantra",
  "ageGroup": "3-6",
  "readTimeMinutes": 2,
  "moral": "Where there's a will, there's a way.",
  "moralHi": "जहाँ चाह, वहाँ राह।",
  "coverImage": "thirsty-crow",
  "tags": ["cleverness", "determination", "animals"],
  "bundled": false,
  "version": 1
}
```

**Step 2:** Create `stories/panchatantra-thirsty-crow.json`:

```json
{
  "id": "panchatantra-thirsty-crow",
  "title": "The Thirsty Crow",
  "titleHi": "प्यासा कौआ",
  "category": "panchatantra",
  "ageGroup": "3-6",
  "readTimeMinutes": 2,
  "moral": "Where there's a will, there's a way.",
  "moralHi": "जहाँ चाह, वहाँ राह।",
  "coverImage": "thirsty-crow",
  "tags": ["cleverness", "determination", "animals"],
  "version": 1,
  "sections": [
    {
      "heading": null,
      "text": "On a hot summer day, a crow was very thirsty...",
      "image": "thirsty-crow-01"
    },
    {
      "heading": "A Clever Idea",
      "text": "He saw a pot with a little water at the bottom...",
      "image": "thirsty-crow-02"
    }
  ]
}
```

**Step 3:** Add scene images to `story-images/`:
- `story-images/thirsty-crow-01.png`
- `story-images/thirsty-crow-02.png`

Image recommendations: 800x600px, PNG, under 500KB each.

**Step 4:** Commit and push all files.

### Update an Existing Story

1. Edit the story JSON in `stories/{id}.json`
2. Bump `version` in **both** the catalog entry and the story file (e.g. `1` → `2`)
3. The app will auto-download the updated version

### Categories

Current categories: `panchatantra`, `epic` (Ramayana/Mahabharata stories).
You can add new categories freely — the app groups by whatever `category` value you use.

---

## Testing Changes

### Before Pushing

1. Validate JSON syntax — use any JSON validator or `python3 -m json.tool < file.json`
2. Check that all `id` values are unique within their file
3. Verify YouTube video IDs are correct by visiting `https://www.youtube.com/watch?v=VIDEO_ID`

### After Pushing

1. Wait ~5 minutes for GitHub raw CDN cache to refresh
2. Open Sadhana app (or kill and relaunch)
3. Navigate to the relevant section
4. Pull-to-refresh (Live Darshan) or reopen the screen (Calendar, Lyrics, Stories)
5. Check Xcode console for `[LiveDarshan]`, `[Calendar]`, `[AartiService]`, `[StoryService]` logs

### Quick Validation Commands

```bash
# Validate all JSON files
for f in *.json stories/*.json lyrics/*.json; do
  python3 -m json.tool < "$f" > /dev/null 2>&1 || echo "INVALID: $f"
done

# Check a remote URL is accessible
curl -s -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/jyoti0512shukla/DharmicData/main/live-darshan-catalog.json
```

---

## Repo Structure

```
DharmicData/
├── app-config.json                 # Master config (URLs, labels, API keys)
├── live-darshan-catalog.json       # Temple live stream catalog
├── hindu-calendar.json             # Festivals, ekadashis, vrats (2025-2030)
├── lyrics-catalog.json             # Aarti/chalisa/mantra catalog
├── lyrics/                         # Individual lyrics JSON files
│   ├── gayatri-mantra.json
│   └── ...
├── stories/
│   ├── stories-catalog.json        # Stories catalog
│   ├── panchatantra-blue-jackal.json
│   └── ...
├── story-images/                   # Scene illustrations for stories
│   ├── blue-jackal-01.png
│   └── ...
├── SrimadBhagvadGita/              # Scripture data (bundled, not fetched remotely)
├── Ramcharitmanas/
├── ValmikiRamayana/
├── Mahabharata/
├── Rigveda/
├── Yajurveda/
├── AtharvaVeda/
└── docs/
    └── CONTENT_UPDATE_GUIDE.md     # This file
```
