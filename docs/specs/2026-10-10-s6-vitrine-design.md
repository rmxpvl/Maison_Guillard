# S6 bis — Vitrine : accueil, qui sommes-nous, contact, direction artistique — Design

> Base: `docs/specs/2026-10-10-s6-site-public-design.md` (public catalogue, already implemented on
> `Branche-S6`). This spec reshapes that public site into a "vitrine + e-shop" following the
> stakeholder's brief, and adds three static pages. Frontend only: no backend change.

## Brief (from the stakeholder)

> "Faire une vitrine de notre univers avec de belles photos, et un e-shop pour vendre quelques
> pièces. Lignes épurées et teintes naturelles qui mettent en avant l'artisanat, et une
> typographie minimaliste."

Visual references given: empreintes.com (mobilier) and gres-editions.com — lots of white space,
full-bleed photos, thin uppercase letter-spaced titles, almost no colour.

## Decisions from brainstorming

- **Home page is a pure vitrine** (not a shop grid). The catalogue moves to `/boutique`.
- **Typography: one thin sans-serif, Jost** (Google Fonts, weights 300/400/500). Body in 300;
  titles and navigation in uppercase with `letter-spacing` 0.15–0.2em. No serif anywhere.
- **Palette** (replaces the current brown accent):

  | Token | Value | Use |
  |---|---|---|
  | `--couleur-fond` | `#faf8f4` | page background |
  | `--couleur-surface` | `#ffffff` | rare raised surfaces |
  | `--couleur-texte` | `#1f1d1a` | text, logo |
  | `--couleur-texte-doux` | `#7a736b` | secondary text, availability mention |
  | `--couleur-accent` | `#b8a58c` | sand: footer background, hover lines |
  | `--couleur-filet` | `#e8e2d8` | hairlines, image placeholders |
  | `--couleur-erreur` | `#a33` | error messages |

- **Logo:** the stakeholder's identity (monogram "G" wrapped by 5–6 organic growth rings + the
  wordmark "MAISON GUILLARD") is redrawn as an **inline SVG component**, with one fix: the G's
  circle is **open** between roughly 1 and 3 o'clock, above its horizontal bar, so it reads as a
  G and not as a closed "O + bar". The SVG uses `stroke="currentColor"`, so CSS sets its colour
  (dark in the header, off-white on sand in the footer). The wordmark is real text in Jost, not
  outlined paths. The symbol alone is also exported as `public/favicon.svg`.
- **Product cards in the Grès style:** no border, no shadow, no coloured pill. 4:3 image, then
  small uppercase letter-spaced name, price, and the availability as a discreet text mention
  ("Sur commande", "Vendu"; nothing for "Disponible").
- **Buttons:** 1px outline, small uppercase letter-spaced label, filled on hover.
- **Images are ambience only** (AI-generated, provisional): workbench, wood stack, wood detail,
  contact still life. No fake person, no fake "our workshop" claim. They live in
  `frontend/src/assets/vitrine/` as WebP (~200 KB each) and are imported so Vite fingerprints them.
- **Copy is provisional and sober**: it talks about the approach (solid wood, hand-made, pieces
  built to last), never about an invented biography.
- **Contact details live in one file**, `src/config/coordonnees.js` (e-mail, phone, area), with
  example values to replace. The quote form will be added to the Contact page in the "devis"
  sub-project.
- **No burger menu**: three nav links wrap on small screens.
- **Out of scope:** newsletter, social feeds, legal pages, a CMS for the copy, real coordinates.

## Routes

| Path | Page | Change |
|---|---|---|
| `/` | `PageAccueil` | new |
| `/boutique` | `PageCatalogue` | moved from `/` |
| `/boutique/:slug` | `PageCatalogue` | moved from `/categorie/:slug` |
| `/produits/:id` | `PageFicheProduit` | unchanged (its "back" link now targets `/boutique`) |
| `/qui-sommes-nous` | `PageQuiSommesNous` | new |
| `/contact` | `PageContact` | new |
| `*` | `PageIntrouvable` | unchanged (its link now targets `/boutique`) |

`FiltreCategorie` links move to `/boutique` and `/boutique/:slug` (still keeping `?disponibilite=`).

## Layout

- **Header:** `Logo` (symbol + wordmark) on the left; `Boutique`, `Qui sommes-nous`, `Contact` in
  the centre; `Panier` (disabled until the purchase sub-project) on the right. Categories are no
  longer in the header — they stay in the shop filters. The header no longer needs the
  categories, so `Layout` stops passing them to it (it still loads them for the shop pages).
- **Footer** (sand background, off-white text): logo + one-line signature; navigation links;
  contact block from `coordonnees.js`; bottom line "© 2026 Maison Guillard".

## Pages

### Accueil (`/`)
1. **Hero:** `accueil.webp` full-bleed, ~85vh tall, `object-fit: cover`. Text placed in the image's
   empty area: title "Mobilier artisanal en bois massif", sub-line "Pièces dessinées et fabriquées
   à la main", button "Découvrir la boutique" → `/boutique`.
2. **Notre univers:** short text (left) + `matiere.webp` (right, 4:5); stacked on mobile.
3. **Pièces choisies:** up to 3 `CarteProduit` chosen by `piecesChoisies(produits, 3)` from
   `GET /api/produits` + link "Voir toute la boutique". Hidden when no produit qualifies; the usual
   loading / error states apply.
4. **Savoir-faire band:** `detail.webp` (1:1) + one sentence + link "Qui sommes-nous" →
   `/qui-sommes-nous`.

### Qui sommes-nous (`/qui-sommes-nous`)
Intro paragraph; three commitments (Bois massif / Fait à la main / Pensé pour durer) as short
titled blocks; `matiere.webp` and `detail.webp` placed between text blocks.

### Contact (`/contact`)
`contact.webp` + heading + short welcoming text + coordinates from `coordonnees.js`
(e-mail as a `mailto:` link, phone as a `tel:` link, area as text).

## Logic and tests

One new pure function in `utils/produit.js`, tested with `node --test` like the existing helpers:

```js
// Produits to feature on the home page: those with at least one photo first,
// "disponible" before "sur_commande" before "rupture", stable otherwise; at most `n`.
piecesChoisies(produits, n) -> Produit[]
```

Test cases: keeps only produits with photos; orders by availability as above; keeps API order
among equals; returns at most `n`; returns `[]` for an empty list or when no produit has photos.

## Verification

- `npm run lint`, `npm run build`, `npm test` clean; backend suite unchanged and green.
- Browser check: each route renders; header links and active state; hero text readable over the
  image; home shows the 3 real pieces; old URLs `/categorie/...` are now 404 (acceptable: never
  published); footer on every page; responsive at ~375px (no horizontal scroll, sections stacked,
  nav wrapped); logo crisp in header, footer and browser tab.
