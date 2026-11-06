---
name: add-illustrations
description: Add new food pictures to the household profile library, from the Figma file or from PNGs exported by hand, and add new ingredients to the index. Use when someone says they drew or added new illustrations, pastes a Figma link to the illustrations, drops PNGs in a folder, or wants a new ingredient the profiles can show.
---

# Add food pictures to the library

Pictures live in `library/illustrations/<file>.png`. The index `library/ingredients.csv` (made by `generator/tools/make_ingredients.py`) says which names each picture answers to. The list of what is still to draw is `library/ingredients.md`.

Every picture must be a PNG with a transparent background, cropped tight, at least ~150px tall.

## From the Figma file (needs the Figma connector)

The designer keeps the pictures in Figma file `oNxq6P6BXhjgCKiZENgWb3`, section "Vegetable illustrations" (node `260:21802`) on the page "Review - Household Profile". Each picture is a layer named after the ingredient ("Seer fish"), usually a small frame holding an image rectangle and a label.

1. With `use_figma` (read only), list the new layers: for each item frame, its name and the `imageHash` of the IMAGE fill inside it. Compare against `library/ingredients.csv` (column `have`) to find the ones not in the library yet. Return names and hashes only.
2. `download_assets` returns at most 20 source images per node and doesn't say which is which. So with `use_figma`, make temporary frames named `TMP export N`, each holding clones of at most 20 of the image rectangles, placed to the right of everything on the page. Return their ids.
3. Call `download_assets` on each temporary frame and `curl` every `rawImages` URL into one new empty folder. The URLs are short-lived; don't print or save them anywhere else.
4. Delete the temporary frames with `use_figma` (only nodes named `TMP export …`).
5. Save the `[[layer name, imageHash], …]` list as `map.json` and run:
   ```bash
   python3 generator/tools/add_illustrations.py --dir <download folder> --map map.json
   ```
   Figma's image hash is the SHA-1 of the file, so every download is matched to its layer exactly.

## From PNGs exported by hand

Export each layer as PNG (2x) with its layer name as the file name, put them in one folder, then:

```bash
python3 generator/tools/add_illustrations.py --dir <folder>
```

## Read the result

- **Added**: done. The index and `library/ingredients.md` are updated automatically.
- **Already in the library**: left alone. Only add `--replace` if the person says the new drawing should replace the old one.
- **Not in the ingredient index**: a new ingredient. Add a row for it to `ROWS` in `generator/tools/make_ingredients.py`, in the right category: `(file, name, aliases separated by |, priority "", stand_in "")`. File names are lowercase with hyphens. Aliases are every name a household might write: English, Hindi and the South Indian names (okra: `okra|bhindi|lady finger|ladies finger|vendakkai`). Check that no alias is already used by another row. Run `python3 generator/tools/make_ingredients.py`, then the import again.
- **No transparent background / too small**: ask for a new export.

## Check it

Make a quick contact sheet (an HTML grid of the added files with their names), screenshot it with headless Chrome and look at it, so a wrong match is caught before anyone builds a profile. Then rebuild one profile that uses a new picture and look at it.

Finally tell the person what was added and how many pictures are still to draw (the first line of `library/ingredients.md`). If the repository is set up with GitHub, offer to commit the new pictures so the team gets them.
