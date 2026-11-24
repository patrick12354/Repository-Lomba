# PlantPulse runbook

Boundary: **PlantPulse never writes to DCS, SAP or any control system.** It reads a governed snapshot and produces decisions, logs and export files for humans.

## Environment variables

Locally they live in `prototype/.env` (template `prototype/.env.example`). In production they go in Vercel → Project → Settings → Environment Variables, for Production and Preview.

| Variable | Needed | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes | Model calls. Without it, AI routes return 503 and everything else still works. |
| `OPENAI_MODEL`, `OPENAI_MODEL_LIGHT` | no | Override the default models (`gpt-6.1-sol`, `gpt-6-luna`). |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | yes | Server access to the database. The service-role key never goes to the browser and never takes a `VITE_` prefix. |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | yes | Browser client (uploads through signed URLs; RLS is read-only). Leaving the URL unset builds the offline demo. |
| `AUTH_MODE`, `VITE_AUTH_MODE` | yes | `open` (trial: no sign-in, one shared sandbox) or `required` (guest and email sign-in). Keep both the same. |
| `AI_DAILY_BUDGET_USD` | yes | Rolling 24 h spend cap across the deployment (default 20). |
| `CRON_SECRET` | yes | Protects `/api/cron/due-actions`; Vercel Cron sends it automatically. |
| `RESEND_API_KEY`, `NOTIFY_FROM` | no | Due-date emails. Without them the cron runs and skips sending. |

Changing a `VITE_` variable needs a redeploy, because those are baked into the build.

## First setup

1. Supabase → SQL Editor → run `prototype/supabase/migrations/0001` to `0005` in order.
2. `cd prototype && npm run check:ai && npm run seed && npm run check:db`.
3. From the repository root, with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` exported: `python -m analytics.patterns && python -m analytics.anomaly`, then `cd prototype && npx tsx --env-file=.env scripts/label-patterns.ts`.
4. `npm run check:live` exercises every feature end to end.

## Turning sign-in on later

1. Supabase → Authentication → Sign In / Providers: enable **Email** and **Allow anonymous sign-ins**. Under URL Configuration, set the Site URL to the Vercel URL. Under Attack Protection, enable CAPTCHA so anonymous accounts cannot be minted in bulk.
2. Set `AUTH_MODE=required` and `VITE_AUTH_MODE=required` in Vercel, then redeploy.
3. Give team members roles: `update profiles set role = 'reviewer' where display_name = 'name@company.com';` (roles: viewer, engineer, reviewer, manager, data_owner).

## Rotating keys

- **OpenAI**: create a new key, replace `OPENAI_API_KEY` in Vercel, `.env` and GitHub secrets, redeploy, then revoke the old key.
- **Supabase**: Project Settings → API → roll the service-role key (and the anon key if exposed). Update Vercel, `.env` and GitHub, then redeploy.

## Ingest and publish a new snapshot

This needs the `data_owner` role, so sign-in must be on. On the Ingest snapshot page, upload the Incident Database plus any equipment, production and RCA files, then click **Ingest to staging**. Review the gates, write a reason, and click **Publish**. A blocking gate prevents publishing. The previous snapshot is archived, not deleted.

## Evals

`npm run eval:rca`, `eval:copilot` and `eval:evidence` together cost about US$0.60. Record "x of n" with the date, model and run folder in `evaluation/results.md`. Do not edit an eval's patterns after seeing its output.

## When the daily AI budget is hit

AI routes return 429 until spend over the last 24 h drops below `AI_DAILY_BUDGET_USD`. Check spend on the AI quality page or with `select feature, model, sum(cost_usd) from ai_runs where created_at > now() - interval '1 day' group by 1, 2;`. Each run reserves an estimate before the model is called, so parallel requests cannot slip past the cap. Hourly caps per account: 30 for members, 10 for guests, 60 for the shared open-mode account. All guests together may spend at most 25 % of the budget, except in open mode.

## Verifying the audit chain

`select verify_review_chain();` returns `null` when the chain is intact, or the id of the first broken entry. `review_events` rejects every UPDATE and DELETE.

## Data retention

Supabase takes daily backups (plan dependent). Uploaded evidence and source files are kept for the pilot period; removing evidence from an action unlinks it but keeps the file, because the review log references it. Sandbox data is ordinary rows marked `is_demo = true` and can be purged before a pilot with `delete from actions where is_demo; delete from rca_drafts where is_demo; delete from rca_audits where is_demo;`.
