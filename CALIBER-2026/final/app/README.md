# Sparekit web app

Next.js 16 (App Router) + SQLite. Reads the engine output in `data/partpulse.db` (read-only) and writes approve/reject decisions to a temporary SQLite file (`/tmp` on Vercel).

## Run

```bash
npm install
npm run dev        # http://localhost:3000
npm run build && npm start   # production check
```

Rebuild the data from the repo root with `py pipeline/build_db.py && py pipeline/app_tables.py`. Stop the local server first on Windows: it holds a lock on the `.db` file.

## Pages

| Route | Question it answers |
|---|---|
| `/` | Are we ready for the next turnaround? |
| `/todo` | What should we do? (Urgent now / All parts) |
| `/parts/[id]` | What to do with this part, and why? |
| `/stock` | Where is money stuck, and where are we exposed? |
| `/forecast` | What will we need in the next 6 months? |
| `/what-if` | What if we keep more or less stock? |
| `/check` | Can we trust these numbers? |

## API

| Endpoint | Returns |
|---|---|
| `GET /api/ta-readiness?date=YYYY-MM-DD&scale=1.0` | Readiness per criticality, weekly deadlines, every turnaround part with its status |
| `GET /api/alerts?limit=8` | Urgent feed (act now / plan / use twin) |
| `GET /api/parts?action=&crit=&health=&q=&twin=1&limit=&offset=` | Filtered part list |
| `GET /api/parts/[id]` | One part: materials + forecast + policy + history + twins |
| `GET /api/scenario?budget=&holding=` | Nearest point on the engine's budget-vs-risk frontier |
| `GET /api/overview`, `/api/forecast-summary`, `/api/trust` | Stock health, demand outlook, data quality and backtest |
| `GET /api/search?q=` | Part search by name or number |
| `GET/POST/DELETE /api/decisions` | Approve/reject log in SQLite |

Criticality order follows the organiser: A > B > C > S (A highest). The product name lives in `lib/brand.ts`.

## Environment

Set these in `app/.env` locally and in the Vercel project settings. None of them belongs in git.

| Name | Needed for |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_MODEL` | AI overview, assistant, drafts. Without them the app answers from templates |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Sending from inside the app. Create the password at myaccount.google.com/apppasswords (2-step verification must be on). Without them, Send becomes a link that opens Gmail with the draft filled in |
| `SESSION_SECRET` | Signs the login cookie. Any long random string |

Demo accounts are listed on the login page. They share the password in `lib/people.ts`, and every address delivers to the one inbox set there.
