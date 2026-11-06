# Household profile generator (v7)

One template, any household. The design comes from Figma frame 199:463 (the final flow).

```bash
python3 generator/make.py <house>          # profiles/<house>/household.json → page + PDF
python3 generator/make.py <house> --no-pdf # page only, while editing
```

`make.py` runs four steps:
1. `check.py` fills in the standard text and avatars, then checks the file.
2. `build.py` writes the page.
3. `tools/measure.py` renders the page at 390px. It gets the page height and flags text that runs past its card.
4. `tools/pdf.sh` makes the PDF: a single tall page, from four 2x Chrome screenshots joined by `img2pdf.swift`.

A house's folder ends up holding:

- `household-<slug>.html` and `household-<slug>.pdf`
- `preview-full-page.png`
- `assets/`, with only the files the page uses
- `report.json`, which lists pictures that aren't drawn yet, stand-ins in use, vendors shown as text tiles, and meal pictures picked automatically

## What adapts to the data

| Section | Rule |
|---|---|
| Hero | Avatars for 1–4 people. The greeting shrinks past 22 and 30 characters. The "About" text shrinks past 80 and 120 characters. The kitchen photo is the same for everyone |
| Your household | 2 people sit side by side and 4 make a 2 × 2 grid. With an odd count, the last card goes full width. Cuisine chips wrap. Platform tiles use 2–5 columns |
| Platforms | A library logo when there is one (`library/logos`), otherwise the text tile. Names are matched loosely ("Swiggy Instamart" → instamart, aliases in `check.py`) |
| Meals | Any number of meals. Without `art`, the picture is chosen from the words in `what`. Per-person rows (`each`) show that person's avatar |
| Food you love | 1–6 cuisine tiles. With an odd count, the first tile goes full width. From 4 tiles up, the names get smaller. Dish chips get Fluent icons from their words |
| Proteins | Pictures come through the ingredient index (`library/ingredients.csv`). An ingredient that isn't drawn yet uses its stand-in, or a placeholder if it has none |
| Where your food comes from | Shelves always run in this order: chicken, seafood, eggs, fresh food and veggies. Optional `mutton`, `dairy` and `bakery` shelves come after. Each shelf has optional `items` (which pick its pictures), a `note` and `apps` |
| Rules of the house | Each tile has a `topic`, a big `value` and a `sub`. With an odd count, the last tile goes full width |

Standard text, such as section titles, the headline and the closing, lives in `DEFAULTS` in `check.py`. A household file only overrides it when it needs to.

## Pictures

- To add one, use `tools/add_illustrations.py` (or the `/add-illustrations` skill).
- To add a new ingredient or alias, edit `ROWS` in `tools/make_ingredients.py` and run it.
- The generator picks up any new `library/illustrations/<file>.png` with no code change.

## Colours (Figma 199:463)

- Icon boxes: `#C599EC`
- "Often" chips: `#BE95E2`
- The "Often" count and the M mark: `#A96ADD`
- Note pills: a blue-lilac gradient with `#3A4FC0` text

All icons are Fluent UI System Icons (`fluent/`, MIT). Any filename in that folder can be used in an `icon` field.

## Contrast

```bash
python3 generator/tools/measure.py <page.html> 390 --all
```

The known exceptions are listed in the root CLAUDE.md. `make.py --contrast` shows anything new.
