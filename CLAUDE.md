# M household profiles

M is a home-cook service in India. After a home visit, each household gets a profile: a phone-width page and PDF of how their kitchen runs. This repository builds it from one JSON file per house.

Most people using this are not technical. Speak plainly, do the file work yourself, and don't show JSON or code unless asked.

## Commands

- Make or update a profile: the `/household-profile` skill. Under the hood: `python3 generator/make.py <house>` (checks, builds, checks the fit, makes the PDF).
- Check a household file only: `python3 generator/check.py profiles/<house>/household.json`
- Add food pictures: the `/add-illustrations` skill (`generator/tools/add_illustrations.py`)
- Rebuild the ingredient index after editing `generator/tools/make_ingredients.py`: `python3 generator/tools/make_ingredients.py`
- Contrast report for design work: `python3 generator/tools/measure.py <page.html> 390 --all`

The household file format and the writing rules are in [docs/household-file.md](docs/household-file.md). Read it before writing or editing any household file.

## Rules

- **Only facts from the visit.** Never invent content to fill a section; leave it out and say what was left out.
- **Nothing about who orders or who decides the menu.** Rules are the household's preferences, not things M does.
- **Privacy.** `profiles/` holds real households and is git-ignored. Never commit it, never copy real household content into `examples/`, `docs/` or code, and never send a profile anywhere yourself. Examples use made-up people only.
- **Making a profile never changes the design.** Don't edit `generator/build.py`, the CSS or `library/` while making a profile. Design changes are separate work for the designer.
- Don't commit or push unless the person asks.

## Design

- Source of truth: Figma file `oNxq6P6BXhjgCKiZENgWb3`, frame `199:463` (the final flow). Illustrations are in section `260:21802`, avatars in `260:21037` and logos in `260:21912`.
- Figtree is the only typeface (no serif). Primary purple `#A96ADD`. Figma lilacs: icon boxes `#C599EC`, "Often" chips `#BE95E2`. Note pills: blue-lilac gradient with `#3A4FC0` text.
- All icons are Fluent UI System Icons (`generator/fluent`, MIT).
- Accepted contrast exceptions (make.py hides them): the "About your household" label at 50% opacity (3.06:1, by request), the "Household Profile" tag on the photo, and white text on the lilac "Often" chips (2.45:1) with the lilac "Often" count (2.85:1). The chips and count are kept as in Figma until the designer decides otherwise.
- App logos in `library/logos` are third-party trademarks, used internally to show which apps a household uses. `sources.csv` records where each came from.
- Figma asset and screenshot URLs are short-lived secrets: don't paste them into files or messages.

## Requirements

macOS with Google Chrome, Python 3 and Swift (both come with `xcode-select --install`). The PDF step uses `sips` and Swift, so it only runs on a Mac.
