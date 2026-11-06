---
name: household-profile
description: Make or update an M household profile (the HTML page and PDF sent to a household after the home visit) from visit notes, a call transcript, a filled form or a voice-note transcript. Use when someone says "make a household profile", "new house", "profile for <names>", pastes visit notes, or asks to change something in an existing profile.
---

# Make a household profile

You turn what the team learned on a home visit into `profiles/<house>/household.json`, then build the page and PDF with one command. The person you're helping is usually not technical: talk in plain words, never show them JSON unless they ask, and do the file work yourself.

## 1. Get the notes

First, quietly get the latest pictures and fixes: run `git pull` in the project folder. Skip it if there's no internet, and never discard local changes without asking.


- If they pasted notes, attached a file or named one, use that. If not, ask them to paste the visit notes or a transcript. That is the only thing you need to start.
- Updating an existing house: open `profiles/<house>/household.json`, make the change they asked for, and skip to step 4.

## 2. Draft the household file

Read [docs/household-file.md](../../../docs/household-file.md) first, every time; it is the spec. Look at [examples/four-people/household.json](../../../examples/four-people/household.json) for a full file.

Then write `profiles/<slug>/household.json` (slug from the names, e.g. `asha-bilal`), and save their notes next to it as `profiles/<slug>/notes.md` so the source stays with the profile.

Rules that matter more than anything else:

- **Only what the notes say.** Never invent a dish, an app, a rule, an allergy or a number to fill a section. If the notes don't cover something, leave that field or section out. Omitting is always better than guessing.
- **Nothing about who orders or who decides the menu.**
- **Rules are the household's preferences**, written about them ("Ask before throwing anything out"), never about M staff or what M does.
- **Allergies are only real allergies, and only if the visit covered them.** Don't write "No allergies" unless the notes say so; leave `allergies` out instead. Dislikes and avoids go in no-gos ("Peanuts", "An avoid, not an allergy").
- House voice: short, calm, sentence case, no exclamation marks, no emoji, Indian food names as the household says them.
- Don't set `avatar`, `title`, `greeting` or the standard headings; they are filled in. Set them only if the person asks.
- Proteins: use the `freq` and `label` steps in the guide (4 Every day, 3 Day to day, 2 Often or Once in a while, 1 Occasionally) so every profile reads the same. If the notes don't say how often, leave `freq` and `label` out rather than guessing.
- Spice: only if the notes say. "Spicy" is 3, "normal" or "medium" is 2, "mild" or "not spicy" is 1. If they don't say, leave `spice` out.
- Something only one person avoids goes on their card as a "Skips" line in `noticed`, not in the house no-gos.

## 3. Check it with the person before building

Show a short plain-language summary, not the JSON:

- who lives there (names, diet, allergies)
- cuisines, apps, meals, the top proteins, spice level
- the rules and no-gos
- **Left out:** anything in the notes you weren't sure about, each with the question that would settle it

Ask them to confirm or correct. Wait for their answer. Apply their corrections.

## 4. Build

```bash
python3 generator/make.py <slug>
```

It checks the file, builds the page, checks every line fits on a phone, and makes the PDF (about 15 seconds). It also writes scratch files in `generator/tools/.tmp/`; that's normal. Read its output:

- **"The household file needs fixing"**: fix those fields yourself and run it again.
- **"Text that doesn't fit"**: shorten that text (keep the meaning, keep the household's words where you can) and run again. "Too many apps on the … shelf" means more than 3 apps on one shelf: keep the 3 they use most for that shelf and ask the person if that's right.
- **"No picture yet"**: not a blocker. The profile shows a plain icon. Tell the person which picture is missing so they can ask the designer; if the item has a close match in [library/ingredients.md](../../../library/ingredients.md) under a different name, use that name instead.
- **"No food word found"**: a meal or note shows a generic picture. Set its `art` to a picture from [library/ingredients.md](../../../library/ingredients.md) that fits (file name without `.png`), or leave it if nothing fits.
- **"Shown as a text tile"**: the app has no logo. That's fine and looks intended.
- **"Worth a look"**: fix anything that breaks the writing rules; mention the rest.

Run again until it says **Ready to send**.

## 5. Hand it over

Tell them where the files are, as links:

- the PDF: `profiles/<slug>/household-<slug>.pdf` (this is what gets sent)
- the page: `profiles/<slug>/household-<slug>.html`

Offer to show the page before they send it: start the `profiles` preview server (`.claude/launch.json`) and open `http://localhost:8778/profiles/<slug>/household-<slug>.html`, or give them the HTML file to open in Chrome. Mention anything still missing (pictures, questions left open).

## Don't

- Don't change the design, the CSS, or anything in `generator/` or `library/` while making a profile. If the person wants a design change, say it's a change for everyone and should go through the designer.
- Don't commit or push `profiles/`. Household files hold names and home details and stay on this computer (`.gitignore` already keeps them out).
- Don't send the PDF anywhere yourself.
