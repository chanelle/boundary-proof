#!/usr/bin/env bash
# Read-only validation of becomingbeta.com/mimo after a deploy. No token needed.
# Usage: bash deploy/validate_mimo.sh [--pre]
#   --pre  : before first deploy. /mimo is expected to be absent; checks only
#            that the existing site and the Cal.com booking link are healthy.
# Exits non-zero if any check fails.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../demo/dist/mimo"
DOMAIN="${MIMO_DOMAIN:-https://becomingbeta.com}"
CAL="${MIMO_CAL_URL:-https://cal.com/chanelleh/30min}"
PRE=0; [ "${1:-}" = "--pre" ] && PRE=1
FAIL=0
md5of() { if command -v md5 >/dev/null; then md5 -q "$@"; else md5sum "$@" | cut -d' ' -f1; fi; }
check() { # check <label> <condition-result 0/1>
  if [ "$2" = "0" ]; then echo "  PASS  $1"; else echo "  FAIL  $1"; FAIL=1; fi
}
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 30 -L "$1"; }

echo "Existing site"
c=$(code "$DOMAIN/"); check "$DOMAIN/ returns 200 (got $c)" $([ "$c" = "200" ]; echo $?)
curl -sS --max-time 30 "$DOMAIN/" | grep -q "Why Beta"; check "home page still shows its 'Why Beta' nav" $?
c=$(code "$DOMAIN/story/"); check "$DOMAIN/story/ returns 200 (got $c)" $([ "$c" = "200" ]; echo $?)

echo "Cal.com booking"
URL="$CAL?utm_source=becomingbeta&utm_medium=mimo_landing&utm_campaign=mimo-landing-headline-v1&utm_content=variant_A&utm_term=counted&metadata%5Bmimo_variant%5D=A&metadata%5Bmimo_counted%5D=1"
c=$(code "$URL"); check "attributed booking link returns 200 (got $c)" $([ "$c" = "200" ]; echo $?)

if [ $PRE -eq 1 ]; then
  c=$(code "$DOMAIN/mimo/index.html"); echo "  INFO  $DOMAIN/mimo/index.html is $c before deploy (404 expected)"
else
  echo "Mimo pages and assets"
  for f in index.html demo.html pilot.html css/style.css js/core.js js/copy.js js/demo.js js/scenario.js js/engine-data.js js/ui-common.js js/sa-adapter.js data/engine_output.json fonts/fraunces-opsz.woff2 fonts/plex-mono-400.woff2; do
    c=$(code "$DOMAIN/mimo/$f")
    if [ -f "$DIST/$f" ]; then
      same=$([ "$(md5of "$DIST/$f")" = "$(curl -sS --max-time 30 "$DOMAIN/mimo/$f?v=$(date +%s)" | md5of)" ]; echo $?)
      check "/mimo/$f HTTP $c, matches build" $([ "$c" = "200" ] && [ "$same" = "0" ]; echo $?)
    else
      check "/mimo/$f HTTP $c" $([ "$c" = "200" ]; echo $?)
    fi
  done
  c=$(code "$DOMAIN/mimo/"); check "/mimo/ serves the landing page (got $c)" $([ "$c" = "200" ]; echo $?)
  P=$(curl -sS --max-time 30 "$DOMAIN/mimo/pilot.html")
  echo "$P" | grep -q 'cal.com/chanelleh/30min'; check "pilot page links to cal.com/chanelleh/30min" $?
  echo "$P" | grep -q '30-minute Mimo discovery call'; check "pilot page names the 30-minute Mimo discovery call" $?
  L=$(curl -sS --max-time 30 "$DOMAIN/mimo/index.html")
  echo "$L" | grep -q 'scripts.simpleanalyticscdn.com/latest.js'; check "landing loads Simple Analytics" $?
  echo "$L" | grep -q 'name="robots" content="noindex"'; check "landing is noindex (provisional name)" $?
  D=$(curl -sS --max-time 30 "$DOMAIN/mimo/demo.html")
  echo "$D" | grep -q 'Concept simulation · not live enforcement'; check "demo keeps the enforcement simulation label" $?
fi
[ $FAIL -eq 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED"; exit 1; }
