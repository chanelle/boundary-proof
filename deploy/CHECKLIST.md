# Mimo preview: deployment checklist

Workflow: https://github.com/chanelle/chanellehenry-site/actions/workflows/deploy-mimo.yml
(manual only; lives on `case-study-restructure`, the site repo's default branch)

Builds from pinned BoundaryProof commit `a1319ca`. Touches only `/home/chanpdrb/becomingbeta.com/mimo/`. Deletes nothing.

## 1. Dry run (safe, nothing uploaded)
1. Open the workflow link, click **Run workflow**.
2. Leave **mode = dry-run**, leave confirm blank, leave the commit as is. Run.
3. Expect green. The log should show:
   - engine + demo tests pass
   - `built demo/dist/mimo/ with 19 files`
   - health checks: home page 200 with "Why Beta", `/story/` 200, Cal.com booking link 200
   - read-only listing of `/home/chanpdrb/becomingbeta.com` and no existing `mimo`
   - `DRY RUN: stopping here. Nothing was created or uploaded.`
4. If it fails at the token step, the `CPANEL_TOKEN` secret is missing or expired: re-save it in repo Settings → Secrets → Actions.
5. If the listing shows `.htaccess` Rewrite lines, read them before deploying: a catch-all rewrite could swallow `/mimo/`.

## 2. Deploy (needs your explicit go)
1. **Run workflow** with **mode = deploy** and confirm = `deploy becomingbeta.com/mimo`.
2. Expect the validation step to end with `ALL CHECKS PASSED`:
   - 14 `/mimo` files return 200 and match the build checksums
   - `/mimo/` serves the landing page
   - pilot page links to `cal.com/chanelleh/30min` and names the 30-minute Mimo discovery call
   - Simple Analytics loads; page is noindex; enforcement simulation label present
   - existing home page and `/story/` still serve

## 3. After deploy (you, about 10 minutes)
- [ ] Open https://becomingbeta.com/mimo/ on your phone and laptop. Click through all 8 scenes.
- [ ] Visit once with `?internal=1` on each of your own devices so your traffic is excluded.
- [ ] Make one test booking from each variant (`?variant=A`, then `?variant=B` in a private window; these are tagged `excluded_forced_variant`). Confirm `utm_content` shows on each booking's details page in Cal.com, then cancel both.
- [ ] In Simple Analytics, confirm events named `mimo_landing_view_a` / `_b` appear from a real (non-internal) visit.
- [ ] Only then report conversion numbers.

## Updating later
Change the commit input to the new tested BoundaryProof commit and run with **mode = update** plus the confirmation phrase.

## Taking it down
cPanel → File Manager → `becomingbeta.com` → rename or delete the `mimo` folder. Nothing else depends on it.
