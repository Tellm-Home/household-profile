# M household profiles

After a home visit we send each household a profile: a one-page phone-sized PDF of how their kitchen runs, covering who lives there, what they eat, where their food comes from and the rules of the house.

This repository makes that profile from your visit notes. You don't need to write any code: Claude does the work, and you check what it wrote.

## Make a profile

1. In GitHub Desktop, click **Fetch origin**, then **Pull** if it offers. This gets the latest pictures and fixes.
2. Open the Claude app, go to the **Code** tab and open the `household-profile` folder.
3. Type `/household-profile` and paste your visit notes, a call transcript or the form answers.
4. Claude drafts the profile and shows you a short summary, including anything it wasn't sure about. Correct it or say it's right.
5. Claude builds it and gives you the PDF. That PDF is what you send.

Everything for a house stays in its own folder on your Mac, `profiles/<house>/`:

| File | What it is |
|---|---|
| `notes.md` | Your notes, as you gave them |
| `household.json` | What Claude took from them. Ask Claude to change anything |
| `household-<house>.pdf` | **The one to send** |
| `household-<house>.html` | The same page, for a browser |

To change a profile later, open the folder in Claude and say what to change ("Bilal is now vegetarian", "add Zepto for eggs"). Claude rebuilds the PDF.

**Household details never go to GitHub.** The `profiles/` folder is excluded on purpose, because it holds names and home details. If a colleague needs to take over a house, send them that house's folder.

## One-time setup (Mac)

1. **Get access.** You need a GitHub account. Ask the person who manages this repository to add you.
2. **Install these apps:**
   - [Claude](https://claude.ai/download), signed in with your work account
   - [GitHub Desktop](https://desktop.github.com), signed in with your GitHub account
   - [Google Chrome](https://www.google.com/chrome), which makes the PDF
3. **Install Apple's command line tools.** Open Terminal, paste this and press Return, then click Install in the window that appears:
   ```bash
   xcode-select --install
   ```
   If it says they're already installed, you're done.
4. **Download this repository.** In GitHub Desktop, choose **File → Clone repository**, pick `household-profile` and save it in your Documents folder.
5. **Check it works.** Open the folder in Claude's Code tab and type: *build the four-people example*. You should get a PDF in `examples/four-people/`.

## For the designer

- **New food pictures:** add them to the Figma file (section "Vegetable illustrations"), then in Claude type `/add-illustrations` with the Figma link. Claude downloads them, matches them to their file names and updates the list of what's still to draw, [library/ingredients.md](library/ingredients.md). Then commit and push the change in GitHub Desktop so everyone gets it.
- **A new ingredient** (one that isn't on the list yet): ask Claude to add it. It goes into the index with all its names (English, Hindi, regional), so profiles find it whatever the household calls it.
- **Design changes** go in `generator/build.py`. The design source is Figma frame 199:463, the final flow. Details are in [generator/README.md](generator/README.md).

## What's in here

| Folder | What it holds |
|---|---|
| `docs/household-file.md` | Every field of a profile, and how we write them |
| `examples/` | Two complete profiles, with made-up people |
| `generator/` | The code that builds the page and PDF |
| `library/` | Food pictures, app logos, avatars and backgrounds |
| `.claude/skills/` | The `/household-profile` and `/add-illustrations` commands |
| `profiles/` | Your households. On your Mac only, never on GitHub |

## If something goes wrong

- **"Google Chrome is needed"**: install Chrome into Applications.
- **"xcode-select" or "python3" errors, or the PDF step fails**: run step 3 of the setup again.
- **The page looks unstyled in the PDF**: the font loads from the internet, so check you're online and build again.
- **Anything else**: ask Claude what went wrong. It can read the error.
