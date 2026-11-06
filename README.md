# M household profiles

After a home visit we send each household a profile: a one-page phone-sized PDF of how their kitchen runs, covering who lives there, what they eat, where their food comes from and the rules of the house.

This project makes that profile from your visit notes. You don't write any code: Claude does the work, and you check what it wrote.

## Start here

You need a Mac with the [Claude app](https://claude.ai/download) and [Google Chrome](https://www.google.com/chrome) installed. You don't need a GitHub account.

Open the Claude app, go to the **Code** tab, and send this:

> Download https://github.com/Tellm-Home/household-profile into my Documents folder (or update it if it's already there), follow its CLAUDE.md, and make a household profile from these notes: *(paste your visit notes, a call transcript or the form answers)*

Claude downloads the project into `Documents/household-profile`, checks your Mac, and drafts the profile. It then shows you a short summary that lists anything it wasn't sure about. Correct it or say it's right, and Claude builds the PDF. **That PDF is what you send.**

Next time, either send the same message with new notes or open the `household-profile` folder in the Code tab and type `/household-profile`. Either way you get the latest pictures and fixes first.

## For Claude

If you were given this link, the setup steps are in the "Setting up on a new Mac" section of [CLAUDE.md](CLAUDE.md). In short:
- clone (or `git pull`) into `~/Documents/household-profile`; it's public, so no sign-in is needed
- check for Apple's command line tools and Chrome
- build `examples/four-people`
- follow `.claude/skills/household-profile/SKILL.md` from that folder

## Your profiles

Everything for a house stays in its own folder on your Mac, `Documents/household-profile/profiles/<house>/`:

| File | What it is |
|---|---|
| `notes.md` | Your notes, as you gave them |
| `household.json` | What Claude took from them. Ask Claude to change anything |
| `household-<house>.pdf` | **The one to send** |
| `household-<house>.html` | The same page, for a browser |

To change a profile later, open the folder in Claude and say what to change ("Bilal is now vegetarian", "add Zepto for eggs"). Claude rebuilds the PDF.

**Household details never go to GitHub.** The `profiles/` folder is excluded on purpose, because it holds names and home details. If a colleague needs to take over a house, send them that house's folder.

## For the designer

- **New food pictures:** add them to the Figma file (section "Vegetable illustrations"), then in Claude type `/add-illustrations` with the Figma link. Claude downloads them, matches them to their file names and updates the list of what's still to draw, [library/ingredients.md](library/ingredients.md). Then ask Claude to commit and push the new pictures, so everyone gets them the next time they pull.
- **A new ingredient** (one that isn't on the list yet): ask Claude to add it. It goes into the index with all its names (English, Hindi, regional), so profiles find it whatever the household calls it.
- **Design changes** go in `generator/build.py`. The design source is Figma frame 199:463, the final flow. Details are in [generator/README.md](generator/README.md).

## What's in here

| Folder | What it holds |
|---|---|
| `docs/household-file.md` | Every field of a profile, and how we write them |
| `examples/` | Two complete profiles, with made-up people |
| `generator/` | The code that builds the page and PDF |
| `library/` | Food pictures, avatars and backgrounds. App logos belong to their owners and are only used to show which apps a household uses |
| `.claude/skills/` | The `/household-profile` and `/add-illustrations` commands |
| `profiles/` | Your households. On your Mac only, never on GitHub |

## If something goes wrong

- **"Google Chrome is needed"**: install Chrome into Applications.
- **"xcode-select" or "python3" errors, or the PDF step fails**: Apple's command line tools are missing. Ask Claude to install them, or run `xcode-select --install` in Terminal.
- **The page looks unstyled in the PDF**: the font loads from the internet, so check you're online and build again.
- **Anything else**: ask Claude what went wrong. It can read the error.
