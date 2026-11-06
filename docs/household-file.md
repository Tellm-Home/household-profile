# The household file

Every profile is made from one file, `profiles/<house>/household.json`. It holds what we learned on the home visit. The generator turns it into the page and the PDF.

Normally Claude writes this file from your visit notes (type `/household-profile`). This guide is what Claude follows, and it's here so you can check or edit a file by hand.

Two complete examples, with made-up people: [examples/four-people](../examples/four-people/household.json) and [examples/three-people](../examples/three-people/household.json).

## How we write

- **Only what we know.** Every line must come from the visit or the household. If the notes are unclear, leave it out. A profile with one fewer line is fine; a wrong line is not.
- **About the household, in their words.** Rules are the household's preferences ("Ask before throwing anything out"), not things M does.
- **Never who orders or who decides the menu.** Leave that out entirely.
- **Short and calm.** Sentence case. No exclamation marks, no emoji. Titles, chips and labels don't end with a full stop. A sub line under a heading is one short sentence.
- **Something only one person avoids** goes on that person's card, as a `noticed` line labelled "Skips" ("Rajma, broccoli and beans"). No-gos are for the whole house; if one must name a person, say so ("Raw capsicum for Bilal").
- **Timing and planning are fine** ("The home meal is confirmed on Friday"). Who decides or orders is not.
- **Indian English and Indian names for food.** "Curd", "sabzi", "dal", "seer fish". Write it the way the household says it.

## The smallest complete file

Everything not shown here is filled in automatically: the title ("Asha & Bilal"), the greeting ("Hey Asha & Bilal,"), the avatars, and the standard headings and closing text.

```json
{
  "visit": "2026-11-04",
  "people": [
    {"name": "Asha", "diet": "veg", "likes": "Filter coffee"},
    {"name": "Bilal", "diet": "nonveg", "allergies": "Peanut allergy"}
  ],
  "hero": {"about": {"big": "One sentence about the household", "small": "An optional second, smaller line"}},
  "household": {"sub": "A vegetarian and a non-veg, one kitchen"},
  "cuisines": [{"name": "South Indian", "note": "Dosa and chutney most mornings"}],
  "platforms": ["Swiggy Instamart", "Licious"],
  "meals": {
    "sub": "One line about how they eat",
    "items": [{"name": "Breakfast", "tag": "At home", "what": "Dosa or idli with chutney"}]
  },
  "love": {"sub": "One line about what they love", "often": ["Masala dosa"], "later": ["Pongal"]},
  "spice": {"level": 2},
  "proteins": [{"name": "Paneer", "freq": 3, "label": "Day to day"}],
  "sources": {"sub": "Fresh only from the apps you trust", "groups": [{"kind": "fresh", "apps": ["instamart"]}]},
  "noticed": {"sub": "Just the way you both like it"},
  "rules": {"sub": "One line about how the kitchen runs", "facts": [{"topic": "Leftovers", "icon": "arrow_sync", "value": "Next day", "sub": "Reheated, never thrown"}]}
}
```

## Section by section

The page runs top to bottom in this order.

### Hero

| Field | What it is | Notes |
|---|---|---|
| `hero.about.big` | One sentence that sums up the household | Required. Up to about 120 characters; past 80 the text gets a little smaller |
| `hero.about.small` | An optional second line | Up to about 80 characters |
| `hero.greeting` | "Hey Asha & Bilal," | Made from the names. Set it only to use nicknames. Past 30 characters it shrinks |

### People (1 to 4)

| Field | What it is | Notes |
|---|---|---|
| `name` | First name | Required |
| `diet` | `nonveg`, `veg` or `egg` (eggetarian) | Required |
| `allergies` | "No allergies" or what it is, e.g. "Peanut allergy" | Defaults to "No allergies". Only real allergies; dislikes go in no-gos |
| `likes` | One short thing they like | Optional. Shown on their card |
| `avatar` | 1 to 24 | Optional; picked automatically. The faces are in `library/avatars` |
| `noticed` | Small personal things for "The little thing we noticed" | Optional list of `{"icon", "label", "value"}`, e.g. `{"icon": "weather_sunny", "label": "Mornings", "value": "Carrot or beetroot juice"}`. A person with none gets no card |
| `id` | Short name used by `meals.items[].each` | Made from the name (`"asha"`) |

With an odd number of people, the last card goes full width.

### Your household

| Field | What it is |
|---|---|
| `household.sub` | One line under the heading, e.g. "A non-veg kitchen for two" |
| `cuisines` | 1 to 6 cuisines they come back to: `{"name": "Kerala", "note": "Appam and egg curry for breakfast"}`. The note shows in "Food you love". The icon is chosen from the name |
| `platforms` | The apps they buy from, as people say them: "Swiggy Instamart", "Licious", "bb now". Apps without a logo show as a neat text tile |

Apps with a logo: Blinkit, Zepto, Swiggy Instamart, Swiggy, Flipkart Minutes, Amazon, bigbasket, JioMart, FirstClub, KPN Fresh, Flipkart, DMart Ready, StarQuik, Nature's Basket, More, Star Bazaar, CityMall, DealShare, Apna Mart, LoveLocal, Namdhari's, Ratnadeep, SPAR, Lulu, KisanKonnect, Pluckk, Handpickd, Gourmet Garden, Licious, FreshToHome, TenderCuts, Zappfresh, Meatigo, Nandu's, PrimeCut, Country Delight, bbdaily, Milkbasket, FTH Daily, Akshayakalpa, Sid's Farm, Pride of Cows, Provilac, Doodhvale Farms.

### Your meal preference

| Field | What it is | Notes |
|---|---|---|
| `meals.sub` | One line, e.g. "Simple mornings, a packed lunch, a light dinner" | |
| `meals.items` | One card per meal, any number | `name` (Breakfast), `tag` (a short pill: "Packed", "At home", "Light"), `what` (the main line), `sub` (a smaller line) |
| `meals.items[].each` | Different things for different people | `[{"person": "asha", "text": "Filter coffee"}]`. Shows their avatar |
| `meals.items[].art` | Pictures for the meal tile | Optional. Without it, the picture comes from the words in `what` |
| `meals.notes` | Extra cards, like how they like rice | `{"label": "Rice", "what": "Everyday rice is plain white", "sub": "..."}` |
| `meals.must` / `meals.nogo` | Must-haves and no-gos about meals | Each item is `["Text"]` or `["Text", "Smaller line under it"]` |

### Food you love

| Field | What it is | Notes |
|---|---|---|
| `love.sub` | One line, e.g. "No one cuisine every day. These three come back" | |
| `love.often` | Dishes they have often | Shown as lilac chips. Keep each under 30 characters |
| `love.later` | Dishes now and then | |

The cuisine tiles above the dishes come from `cuisines`.

### Spice and proteins

| Field | What it is |
|---|---|
| `spice.level` | 1 mild (little or no chilli), 2 medium (normal home spice), 3 hot (they ask for it spicy). Leave `spice` out if the notes don't say; the gauge is then not shown |
| `proteins` | `{"name": "Seer, kingfish", "freq": 2, "label": "Once in a while"}`. The picture is found from the name. Put the one they eat most first |

`freq` is the number of dots out of 4. Use these steps and labels, so every profile reads the same way:

| `freq` | `label` | When |
|---|---|---|
| 4 | Every day | Daily |
| 3 | Day to day | Most days, several times a week |
| 2 | Often, or Once in a while | About once or twice a week |
| 1 | Occasionally | Now and then, a few times a month |

### Where your food comes from

| Field | What it is | Notes |
|---|---|---|
| `sources.sub` | One line, e.g. "Fresh only from the apps you trust" | |
| `sources.groups` | One shelf each | `kind` is `chicken`, `seafood`, `eggs`, `fresh`, `mutton`, `dairy` or `bakery`. They always show in that order. Leave a kind out to drop its shelf. Any other kind needs a `title` and `items`, and comes last |
| `groups[].apps` | The apps for that shelf, in order of preference | Same names as `platforms`. A shelf fits 3 apps on one line |
| `groups[].note` | A small pill, e.g. "Only these two", "Under ₹10 each" | |
| `groups[].items` | What exactly, e.g. `["Pomfret", "Prawns"]` | Picks the shelf's pictures. Without it the shelf uses its usual pictures |
| `sources.filler` | Filler items, added to reach the minimum cart value | e.g. `["Curd", "Diet Coke"]` |
| `sources.stock` | Always in stock | e.g. `["Eggs", "Lemon", "Coriander"]` |

### For your kitchen (optional)

| Field | What it is |
|---|---|
| `kitchen.sub` | One line under the heading, e.g. "How the shopping is done" |
| `kitchen.must` / `kitchen.nogo` | Must-haves and no-gos about buying and storing |
| `kitchen.nogo_apps` | Apps not to buy fresh food from; they show with a red cross |

Leave out `kitchen` entirely if nothing was said about it.

### The little thing we noticed

`noticed.sub`, e.g. "Just the way you both like it". The cards come from each person's `noticed` list.

### Rules of the house

| Field | What it is | Notes |
|---|---|---|
| `rules.sub` | One line, e.g. "Nothing goes to waste or stays past its expiry" | |
| `rules.facts` | Tiles: `topic` says what it's about, `value` is the big fact, `sub` explains it | `{"topic": "Vegetables", "icon": "calendar_ltr", "value": "3 days", "sub": "The longest they are kept"}`. Keep `value` to about 10 characters. With an odd number, the last tile goes full width |
| `rules.must` / `rules.nogo` | Must-haves and no-gos for the kitchen | |

## Icons

Use any of these names in `icon` fields (they are Fluent UI icons, in `generator/fluent`):

airplane, arrow_right, arrow_shuffle, arrow_sync, backpack, bed, bowl_chopsticks, bowl_salad, box, briefcase, building_shop, calendar_clock, calendar_ltr, cart, chat, checkmark, clock, clock_alarm, cookies, dishwasher, dismiss, drink_coffee, drink_to_go, drop, fire, food, food_apple, food_cake, food_carrot, food_chicken_leg, food_egg, food_fish, food_grains, food_pizza, food_toast, guest, heart, home, key, leaf_one, leaf_three, leaf_two, note, oven, people, person, prohibited, receipt, sleep, sparkle, spatula_spoon, star, stove, temperature, timer, vehicle_truck_profile, warning, weather_moon, weather_sunny

## Pictures

Food pictures are found automatically from the words you write, using the index in [library/ingredients.md](../library/ingredients.md), which lists every name each picture answers to (okra, bhindi, lady finger, vendakkai). If something has no picture yet, the profile shows a plain icon and the build tells you which picture to ask the designer for.
