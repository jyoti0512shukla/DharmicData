# How to Publish a Weekly Wisdom Story

## Step 1: Write the Story

Create a new JSON file in this folder: `weekly-stories/{story-id}.json`

Use kebab-case for the filename (e.g. `farmer-and-well.json`, `blind-men-elephant.json`).

**Format:**

```json
{
  "id": "farmer-and-well",
  "title": "The Farmer and the Well",
  "teaser": "A story about clever justice",
  "sections": [
    {
      "heading": null,
      "text": "First paragraph — no heading for the opening."
    },
    {
      "heading": "Section Title",
      "text": "Next section with a heading."
    }
  ],
  "moral": "One sentence moral of the story."
}
```

- **id** — must match the filename (without `.json`)
- **heading** — use `null` for the first section, give headings to the rest
- **sections** — aim for 3-5 sections, each a solid paragraph
- **moral** — shown at the bottom in a highlighted box

## Step 2: Push to GitHub

```bash
cd DharmicData
git add weekly-stories/farmer-and-well.json
git commit -m "Add weekly story: The Farmer and the Well"
git push origin main
```

## Step 3: Send Notification from Firebase

1. Go to [Firebase Console](https://console.firebase.google.com) → your project → **Messaging**
2. Click **New campaign** → **Notifications**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Title** | `This Week's Wisdom` |
   | **Body** | `The Farmer and the Well — A story about clever justice` |

4. Click **Next** → Target → **Topic** → type `all_users`
5. Click **Next** → Scheduling → **Now** (or schedule for a specific day/time)
6. Click **Next** → Additional options → **Custom data** → add two keys:

   | Key | Value |
   |-----|-------|
   | `type` | `weekly_story` |
   | `story_id` | `farmer-and-well` |

7. Click **Review** → **Publish**

## What Happens in the App

1. User sees the notification with your title and body
2. User taps it → app fetches `weekly-stories/{story_id}.json` from GitHub
3. A full-screen reading page opens with the story
4. User reads, then taps X to close and return to the app

## Tips

- **Test first**: Use "Send test message" in step 3 with your device FCM token before sending to all users
- **Body format**: Keep it short — `{Title} — {teaser}` works well
- **Scheduling**: You can schedule for Sunday morning to make it a weekly ritual
- **Premium only**: Target topic `premium_users` instead of `all_users` if you want to limit it
- **Story length**: 3-5 sections, ~150-250 words total reads well on mobile
