# Eldwyld Shop — Launch Runbook

Goal: **$1/day passive** ($30/mo). First product: The Forager's Grimoire at $9
→ ~3–4 sales/month to hit target.

## Status
- [x] Product built — 23-page printable grimoire, US Letter + A4 PDFs (`forager-grimoire/dist/`)
- [x] Customer bundle zipped (`dist/The-Foragers-Grimoire.zip`)
- [x] Listing images rendered (`dist/marketing/` — hero, what's-inside, pin)
- [x] Listing copy written (`forager-grimoire/LISTING.md`)
- [ ] **Shopify connector reconnected** ← the one thing Claude needs from Ellis
- [ ] Product created on Shopify (Claude can do via connector)
- [ ] Digital delivery attached (Shopify Digital Downloads app — manual, ~3 min)
- [ ] Product set ACTIVE + on Online Store channel
- [ ] First 5 pins posted to Pinterest (see MARKETING.md)

## Step 1 — Reconnect Shopify (Ellis, ~1 min)
The connector token expired mid-session. Re-authorize the Shopify connector in
claude.ai → Settings → Connectors, then tell Claude **"go"** in a session with this repo.

## Step 2 — Create the product (Claude, via connector)
1. `create-product` with title/description/tags/price from `LISTING.md`, status DRAFT.
2. Images: use the raw GitHub URLs (branch `claude/build-revenue-stream-q7mj1t`):
   - `https://raw.githubusercontent.com/Eldwyld/Eldwyld/claude/build-revenue-stream-q7mj1t/shop/forager-grimoire/dist/marketing/hero-square.png`
   - `.../dist/marketing/whats-inside.png`
   - `.../dist/pages/page-01.png`, `page-07.png`, `page-05.png`, `page-11.png`, `page-06.png`
3. Variant: single, price 9.00, compare-at 14.00, SKU `ELD-GRIM-001`,
   **untracked inventory**, and (via GraphQL) `requiresShipping: false`.
4. Create collection "The Eldwyld Archives — Printables" and add the product.

## Step 3 — Digital delivery (Ellis, ~3 min, one time)
1. Shopify admin → Apps → search **"Digital Downloads"** (free, by Shopify) → install.
2. Open the app → attach `The-Foragers-Grimoire.zip` (get it from
   `shop/forager-grimoire/dist/` in this repo, or ask Claude to re-send it) to the product.
3. In app settings: fulfill digital orders automatically.

## Step 4 — Go live
- Set product status ACTIVE (Claude or Ellis).
- Confirm it's published to the Online Store sales channel.
- Test: place a 100%-discount test order OR use Shopify's Bogus gateway to
  verify the download email arrives.

## Step 5 — Traffic (the actual bottleneck)
Passive ≠ zero marketing; it means marketing that compounds. Pinterest is the
engine for this niche (witchy printables are a top Pinterest category and pins
surface in search for years). Full plan + ready-made captions: `MARKETING.md`.

## Path past $1/day
Same pipeline, more SKUs (each reuses the design system in `src/`):
1. **The Witch's Planner** (undated weekly + sabbats) — $12
2. **Worldbuilder's Codex** (worldbuilding template pack — taps the other half
   of the Eldwyld brand) — $9
3. **Bundle all three** — $24 ("The Archivist's Bundle")
4. Etsy as a second channel once 2–3 SKUs exist (Etsy brings its own search
   traffic; $0.20/listing + fees, listings can point buyers to eldwyld.com).
