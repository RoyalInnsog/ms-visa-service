# MS Visa Service — Suratgarh · Ultra-Premium Web Portal

A standalone, mobile-first, high-conversion website for **MS Visa Service** (Behind Roadways Bus Stand, RHB Colony, Suratgarh, Rajasthan 335804 · +91 90797 08998).

Design language: *departure-hall trust* — diplomatic navy, royal sapphire & gold-seal accents, Playfair Display prestige headers, a GSAP scroll-drawn flight route through the 4-stage visa journey, and a Three.js particle globe (lazy-loaded, reduced-motion aware).

## Run locally

```bash
cd ms-visa-service-website
python3 -m http.server 8080
# open http://localhost:8080
```

No build step. Everything ships in one `index.html`.

## Add the photography

Drop real photos into `images/` with these exact names — the elegant placeholders disappear automatically:

| File | Content | Ideal size |
|---|---|---|
| `images/hero_graduate.jpg` | Graduate holding passport, face top-center | 1200×1380 |
| `images/canada_study.jpg` | Canada campus / maple emblem | 1280×900 |
| `images/uk_europe_visa.jpg` | UK university campus | 1280×900 |
| `images/australia_visa.jpg` | Australia student lifestyle | 1280×900 |
| `images/europe_germany_visa.jpg` | European campus architecture | 1280×900 |
| *(office photo optional)* | counselling desk scene | 1280×900 |

## Deploy

```bash
python3 scripts/deploy_github.py     # → GitHub Pages (needs GITHUB_TOKEN)
python3 scripts/deploy_cloudflare.py # → Cloudflare Pages (needs CF_API_TOKEN + CF_ACCOUNT_ID)
```

## Tech notes

- GSAP 3.15 + ScrollTrigger + MotionPathPlugin via jsDelivr
- Three.js r185 via import-map dynamic import (skipped on reduced-motion / no WebGL; static orbit fallback always present)
- WhatsApp deep links pre-fill full profile from the eligibility calculator
- LocalBusiness JSON-LD schema with 5.0 rating for local SEO
