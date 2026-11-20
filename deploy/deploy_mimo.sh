#!/usr/bin/env bash
# Deploys the Mimo buyer preview to becomingbeta.com/mimo/ on the existing cPanel
# account. You run this in your own Terminal; nothing runs it automatically.
# Same conventions as chanellehenry-site/cpanel/deploy.sh: the token is typed at a
# hidden prompt, kept only in this shell, never written to disk or printed.
#
# Usage:  python3 demo/tools/build_site.py      # builds demo/dist/mimo/
#         bash deploy/deploy_mimo.sh             # first deploy (stops if /mimo exists)
#         bash deploy/deploy_mimo.sh --update    # overwrite files in an existing /mimo
#
# CI (GitHub Actions, manual only): CPANEL_TOKEN from the repo secret and
#   MIMO_NONINTERACTIVE=1 skip the prompts; MIMO_DRY_RUN=1 stops after the
#   read-only check and the plan, so nothing is created or uploaded.
#
# Touches ONLY /home/chanpdrb/becomingbeta.com/mimo/. Nothing is deleted anywhere.
# To take it down: cPanel > File Manager > becomingbeta.com > delete (or rename) the mimo folder.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../demo/dist/mimo"
SITE_ROOT="/home/chanpdrb/becomingbeta.com"
TARGET="$SITE_ROOT/mimo"
DOMAIN="${MIMO_DOMAIN:-https://becomingbeta.com}"   # override only for testing
HOST="${MIMO_CPANEL_HOST:-https://server214.web-hosting.com:2083}"
PAUSE="${MIMO_PAUSE:-6}"
UPDATE=0; [ "${1:-}" = "--update" ] && UPDATE=1

[ -f "$DIST/index.html" ] || { echo "No $DIST/index.html. Run: python3 demo/tools/build_site.py"; exit 1; }
md5of() { if command -v md5 >/dev/null; then md5 -q "$@"; else md5sum "$@" | cut -d' ' -f1; fi; }

DRY=${MIMO_DRY_RUN:-0}
if [ "${MIMO_NONINTERACTIVE:-0}" = "1" ]; then
  [ -n "${CPANEL_TOKEN:-}" ] || { echo "CPANEL_TOKEN is not set."; exit 1; }
else
  read -rsp "Paste cPanel API token (hidden): " CPANEL_TOKEN; echo
fi
case "$CPANEL_TOKEN" in *[[:space:]]*|"") echo "Token is empty or has a space/line break. Re-copy it as one string."; exit 1;; esac
trap 'unset CPANEL_TOKEN; echo "Token cleared from this shell."' EXIT

auth() { printf 'Authorization: cpanel chanpdrb:%s\n' "$CPANEL_TOKEN"; }
uapi() { # uapi <curl args...> ; prints data JSON, returns 1 on error
  local body; body=$(curl -sS --max-time 60 -H @<(auth) "$@") || { echo "curl failed"; return 1; }
  python3 -I -c 'import json,sys
try: d=json.loads(sys.argv[1])
except ValueError: print("NOT JSON (bot protection?):", sys.argv[1][:160]); sys.exit(1)
if d.get("status")!=1: print("cPanel error:", d.get("errors")); sys.exit(1)
print(json.dumps(d.get("data")))' "$body"
}
mkdir_api2() { # mkdir_api2 <parent> <name> ; succeeds if created or already there
  local body; body=$(curl -sS --max-time 60 -H @<(auth) --get "$HOST/json-api/cpanel" \
    --data-urlencode "cpanel_jsonapi_apiversion=2" --data-urlencode "cpanel_jsonapi_module=Fileman" \
    --data-urlencode "cpanel_jsonapi_func=mkdir" --data-urlencode "path=$1" \
    --data-urlencode "name=$2" --data-urlencode "permissions=0755") || { echo "curl failed"; return 1; }
  python3 -I -c 'import json,sys
try: r=json.loads(sys.argv[1]).get("cpanelresult",{})
except ValueError: print("NOT JSON:", sys.argv[1][:160]); sys.exit(1)
err=str(r.get("error") or r.get("data") or "")
ok=r.get("event",{}).get("result")==1 or "exist" in err.lower()
print("   dir", sys.argv[2], "ok" if ok else "FAILED: "+str(err)); sys.exit(0 if ok else 1)' "$body" "$1/$2"
}
fail() { echo "STOP: $1"; exit 1; }

echo "1) Read-only check of $SITE_ROOT"
LIST=$(uapi --get "$HOST/execute/Fileman/list_files" --data-urlencode "dir=$SITE_ROOT" --data-urlencode "types=file|dir") || fail "list_files"
HAS_MIMO=$(python3 -I -c 'import json,sys; print(any(i.get("file")=="mimo" for i in json.loads(sys.argv[1])))' "$LIST")
python3 -I -c 'import json,sys; [print("   ", i.get("type","?")[:4], i.get("file")) for i in json.loads(sys.argv[1])]' "$LIST"
HTACCESS=$(python3 -I -c 'import json,sys; print(any(i.get("file")==".htaccess" for i in json.loads(sys.argv[1])))' "$LIST")
if [ "$HTACCESS" = "True" ]; then
  echo "   .htaccess present; checking for rewrites that could capture /mimo/"
  HT=$(uapi --get "$HOST/execute/Fileman/get_file_content" --data-urlencode "dir=$SITE_ROOT" --data-urlencode "file=.htaccess") || fail ".htaccess read"
  python3 -I -c 'import json,sys; c=json.loads(sys.argv[1]).get("content",""); print("\n".join("      "+l for l in c.splitlines() if "Rewrite" in l) or "      (no Rewrite lines)")' "$HT"
fi
if [ "$HAS_MIMO" = "True" ] && [ $UPDATE -eq 0 ]; then
  fail "$TARGET already exists. Re-run with --update to overwrite its files, or remove it in cPanel first."
fi

echo
echo "2) Plan"
cd "$DIST"
FILES=$(find . -type f ! -name '.DS_Store' | sed 's|^\./||' | sort)
DIRS=$(printf '%s\n' $FILES | xargs -n1 dirname | grep -v '^\.$' | sort -u)
echo "   create  $TARGET/ and: $(echo $DIRS)"
for f in $FILES; do echo "   upload  $f  ->  $TARGET/$f"; done
echo "   Nothing outside $TARGET is touched. Nothing is deleted."
if [ "$DRY" = "1" ]; then echo "DRY RUN: stopping here. Nothing was created or uploaded."; exit 0; fi
if [ "${MIMO_NONINTERACTIVE:-0}" = "1" ]; then
  echo "   Non-interactive run (manual GitHub Actions dispatch with confirmation)."
else
  read -rp "Type yes to deploy: " OK; [ "$OK" = "yes" ] || { echo "Cancelled. Nothing uploaded."; exit 0; }
fi

echo "3) Folders"
mkdir_api2 "$SITE_ROOT" mimo || fail "mkdir mimo"
for d in $DIRS; do sleep 2; mkdir_api2 "$TARGET" "$d" || fail "mkdir $d"; done

echo "4) Uploading"
for f in $FILES; do
  sleep $PAUSE
  d="$TARGET"; sub=$(dirname "$f"); [ "$sub" != "." ] && d="$TARGET/$sub"
  uapi -F "dir=$d" -F "overwrite=1" -F "file-1=@$f" "$HOST/execute/Fileman/upload_files" >/dev/null || fail "upload $f"
  echo "   ok  $f"
done

echo "5) Verifying live"
sleep 3
BAD=0
for f in index.html demo.html pilot.html css/style.css js/core.js js/sa-adapter.js data/engine_output.json; do
  want=$(md5of "$f"); got=$(curl -sS "$DOMAIN/mimo/$f?v=$(date +%s)" | md5of)
  code=$(curl -s -o /dev/null -w '%{http_code}' "$DOMAIN/mimo/$f")
  [ "$want" = "$got" ] && [ "$code" = "200" ] || BAD=1
  echo "   /mimo/$f  HTTP $code  checksum $([ "$want" = "$got" ] && echo match || echo MISMATCH)"
done
code=$(curl -s -o /dev/null -w '%{http_code}' "$DOMAIN/mimo/")
echo "   /mimo/ (directory index)  HTTP $code"
code=$(curl -s -o /dev/null -w '%{http_code}' "$DOMAIN/"); echo "   existing site $DOMAIN/  HTTP $code"
curl -sS "$DOMAIN/" | grep -q "Why Beta" && echo "   existing home page marker found" || { echo "   existing home page marker NOT found: check the site"; BAD=1; }
[ $BAD -eq 0 ] && echo "Done: $DOMAIN/mimo/" || { echo "Finished with problems above."; exit 1; }
