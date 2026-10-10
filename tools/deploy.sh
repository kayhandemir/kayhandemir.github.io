#!/usr/bin/env bash
# Builds the site and publishes it to ukgames.games (the Hostinger VPS). The previous version stays in
# /var/www/ukgames.games/previous until the next deploy, so a bad deploy can be undone by swapping the folders back.
set -euo pipefail
cd "$(dirname "$0")/.."

SERVER="root@194.5.159.67"
KEY="$HOME/.ssh/bumperbrawl_vps"
SITE_DIR="/var/www/ukgames.games"

python tools/build.py
tar --exclude=.git --exclude=tools --exclude=README.md --exclude=CNAME --exclude=.nojekyll -czf - . |
  ssh -i "$KEY" "$SERVER" "set -e
    rm -rf $SITE_DIR/incoming && mkdir -p $SITE_DIR/incoming
    tar -xzf - -C $SITE_DIR/incoming
    chown -R www-data:www-data $SITE_DIR/incoming
    rm -rf $SITE_DIR/previous
    if [ -d $SITE_DIR/html ]; then mv $SITE_DIR/html $SITE_DIR/previous; fi
    mv $SITE_DIR/incoming $SITE_DIR/html"
echo "Published to https://ukgames.games"
