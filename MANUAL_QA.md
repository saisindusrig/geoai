# Manual QA Checklist — GeoAI 3D Construction Planner

Use this checklist before a public demo or production deploy. Mark each item **Pass / Fail / N/A**.

> All outputs are **preliminary planning only** — not final engineering drawings or legal approvals.

---

## Prerequisites

- [ ] Backend running (`uvicorn app.main:app --reload` or Render URL)
- [ ] Frontend running (`npm run dev` or Netlify URL)
- [ ] `NEXT_PUBLIC_API_URL` points to backend
- [ ] Demo works without API keys (mock mode) OR keys configured on **backend only**

Quick API smoke:

- [ ] `GET /health` or `GET /api/health` → `{ "status": "ok" }`
- [ ] `GET /api/system/status` → database mode, providers
- [ ] `GET /api/projects/demo` → Demo Flyover project with boundary

---

## Demo flow (critical path)

Run in order without refreshing unless noted.

| Step | Action | Pass |
|------|--------|------|
| 1 | Open **Dashboard** | |
| 2 | Click **Demo Flyover (Bengaluru)** | |
| 3 | Open **Workspace** — map loads, boundary/alignment visible | |
| 4 | Expand **Readiness** — pills + check summary | |
| 5 | Expand **Survey Mode** — enable or see PostGIS message | |
| 6 | Open **Map** page — draw tools, site suggestions | |
| 7 | Open **3D Model** — Cesium loads (or graceful fallback) | |
| 8 | Open **Estimate / BOQ** — line items or empty state | |
| 9 | Open **Cost** — summary or empty state | |
| 10 | Open **Timeline** — schedule or empty state | |
| 11 | Open **Report** — export cards + readiness | |
| 12 | **Export PDF** — downloads, does not crash | |
| 13 | **Export CSV** — downloads or fallback row | |
| 14 | **Export GeoJSON** — downloads site geometry | |

---

## Core pages

### Public / app shell

| Page | Route | Checks |
|------|-------|--------|
| Landing | `/` | Hero, CTA to dashboard, dark theme, disclaimer |
| Login | `/login` | Register + sign in, error alerts, redirect to `?next=` target |
| Dashboard | `/dashboard` | Project list, demo card, new project link, skip link (Tab) |
| New project | `/projects/new` | Wizard steps, validation, creates project |

### Project workspace

| Page | Route | Checks |
|------|-------|--------|
| Workspace | `/projects/[id]/workspace` | Map + 3D, drawing tools, parameters, AI panel |
| Map | `/projects/[id]/map` | Boundary/alignment, suggestions, tools |
| 3D Model | `/projects/[id]/model` | Model toggle, excavation layer, navigation |
| Analysis | `/projects/[id]/analysis` | Site analysis or run prompt |
| Estimate | `/projects/[id]/estimate` | BOQ table readable |
| Cost | `/projects/[id]/cost` | Low/medium/high range |
| Scenarios | `/projects/[id]/scenarios` | Scenario list/compare |
| Timeline | `/projects/[id]/timeline` | Phasing chart/list |
| Report | `/projects/[id]/report` | Exports, PDF preview, disclaimer |

### Admin / settings

| Page | Route | Checks |
|------|-------|--------|
| Settings | `/settings` | System status panel |
| Providers | `/settings/api-keys` | Shows configured/not configured (no raw keys) |
| Rates | `/admin/rates` | Table editable |
| Templates | `/admin/templates` | Template list |
| Audit log | `/admin/audit` | Event list loads (admin only) |
| Usage | `/admin/usage` | Plan usage summary (admin only) |

---

## Visual QA

- [ ] **Dark theme** consistent (no light panels, readable text)
- [ ] **Mobile (~390px)** — bottom nav, **More** menu (Escape closes, focus trap), no horizontal overflow, drawers work
- [ ] **Tablet (~768px)** — sidebar collapses appropriately
- [ ] **Desktop (~1440px)** — workspace layout balanced
- [ ] **Sidebar/header** — active route highlighted
- [ ] **Dropdowns / selects** — dark styling, readable options
- [ ] **Modals** — centered, scrollable, close works
- [ ] **Buttons** — hover/disabled states visible
- [ ] **Tables** — row contrast, horizontal scroll on small screens
- [ ] **Loading states** — spinners/skeletons, no blank flash
- [ ] **Empty states** — helpful message + next action
- [ ] **Error states** — retry button, no crash
- [ ] **Map controls** — basemap, layers, draw tools usable
- [ ] **Survey warnings** — PostGIS message on SQLite
- [ ] **Accuracy badges** — tier visible, compact in sidebar
- [ ] **Report export cards** — download links work, PDF preview opens

---

## Browser / device matrix

| Environment | Landing | Dashboard | Demo flow | Exports |
|-------------|---------|-----------|-----------|---------|
| Chrome desktop | | | | |
| Edge desktop | | | | |
| Mobile width ~390px | | | | |
| Tablet width ~768px | | | | |
| Large desktop ~1440px | | | | |

---

## PostGIS / survey (Docker required)

Skip if running SQLite-only demo.

- [ ] `docker compose up -d` + `alembic upgrade head`
- [ ] Settings shows **Full survey mode (PostGIS)**
- [ ] Survey Mode enable succeeds
- [ ] GCP CSV import (valid + invalid file handling)
- [ ] Survey validation run

---

## Production deploy smoke (after Render + Netlify)

- [ ] Backend `/api/health` from public URL
- [ ] Backend `/api/system/status` — `postgis_available` as expected
- [ ] Frontend loads and calls API (no CORS errors in console)
- [ ] No API keys in frontend bundle (check Network → no OpenAI keys)
- [ ] `APP_SECRET` not default in production
- [ ] Demo path works on live URLs

---

## Known acceptable limitations

- SQLite dev mode: limited survey imports, "Limited GIS mode" badge
- No API keys: mock AI, OSM/Esri imagery fallbacks
- Cesium Ion / Google 3D: optional; 2D map still works
- ESLint warnings: none expected after latest cleanup

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Developer | | | |
| QA | | | |
| Demo presenter | | | |
