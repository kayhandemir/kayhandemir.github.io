# UKGames website

Source of [ukgames.games](https://ukgames.games/), served by nginx on the Hostinger VPS (194.5.159.67).
This repository is the source and the backup. GitHub Pages still serves it on the old domain ukgames.net until that
expires; every page sends visitors there to the same page on ukgames.games.

- English home: `/`, Turkish home: `/tr/`
- Legal pages: `/page/privacy-policy`, `/page/privacy-policy-tr`, `/page/terms`, `/page/terms-tr`
  (account deletion for Google Play: `/page/privacy-policy#delete-account`)
- `app-ads.txt` must stay in the root for AdMob.

## Editing

Texts and games are in `tools/build.py`, legal texts in `tools/content/`, styles in `assets/site.css`.
After editing, rebuild the HTML, publish it and commit the result:

```
python tools/build.py      # only rebuild
bash tools/deploy.sh       # rebuild and publish to ukgames.games (needs ~/.ssh/bumperbrawl_vps)
```

## Bumper Brawl web build

The game is played at `/bumperbrawl/play/` (the site's play buttons link there). Its files live outside the site
folder that `deploy.sh` replaces, in `/var/www/ukgames.games/games/bumperbrawl/play/`, and nginx serves them through
`/etc/nginx/snippets/bumperbrawl-play.conf` (included in the site's server block): the gzip `.unityweb` files go out
with `Content-Encoding: gzip`, the wasm as `application/wasm`, cached for a year (hashed names). To update it, upload a
Gzip + decompression fallback web build (the itch one) to `play_new`, `chown -R www-data:www-data` it, then swap:
`play` -> `play_old`, `play_new` -> `play`.

## Contact form

`tools/server/contact_server.py` runs on the VPS as `ukgames-contact.service` (127.0.0.1:8081, behind nginx at
`/api/contact`). It keeps messages in `/var/lib/ukgames-contact/messages.jsonl` for 90 days and emails them through
Gmail SMTP. The Gmail app password lives only on the server, in `/etc/ukgames-contact.env` (`SMTP_PASSWORD=`).
To update the handler: copy the file to `/opt/ukgames-contact/` and `systemctl restart ukgames-contact`.

## Live game stats

`tools/server/stats_server.py` runs on the VPS as `ukgames-stats.service` (127.0.0.1:8082, behind nginx at
`/api/event`, `/api/stats` and `/api/funnel`). Bumper Brawl posts anonymous events to `/api/event` (game opened with
its loading time and days since the device first played, a heartbeat every minute, game created, match started/ended,
and each player's steps into play once per launch; see `GameStats.cs` in the game). `/api/funnel` lists the last 14
days of steps, new and returning players (with D1 retention) and loading time, per platform. The home pages show the numbers in the
live ticker under the header (`site.js`), which stays hidden while `/api/stats` has nothing to show. Counters are in
`/var/lib/ukgames-stats/stats.db` (SQLite, per day in UTC and in total).
Google Analytics forwarding is optional: fill in `GA_MEASUREMENT_ID` and `GA_API_SECRET` in `/etc/ukgames-stats.env`
(GA4 > Admin > Data streams > Measurement Protocol API secrets) and restart the service; events arrive as `bb_*`.
To update the handler: copy the file to `/opt/ukgames-stats/` and `systemctl restart ukgames-stats`.
