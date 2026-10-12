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

## Contact form

`tools/server/contact_server.py` runs on the VPS as `ukgames-contact.service` (127.0.0.1:8081, behind nginx at
`/api/contact`). It keeps messages in `/var/lib/ukgames-contact/messages.jsonl` for 90 days and emails them through
Gmail SMTP. The Gmail app password lives only on the server, in `/etc/ukgames-contact.env` (`SMTP_PASSWORD=`).
To update the handler: copy the file to `/opt/ukgames-contact/` and `systemctl restart ukgames-contact`.

## Live game stats

`tools/server/stats_server.py` runs on the VPS as `ukgames-stats.service` (127.0.0.1:8082, behind nginx at
`/api/event` and `/api/stats`). Bumper Brawl posts anonymous events to `/api/event` (game opened, a heartbeat every
minute, game created, match started/ended; see `GameStats.cs` in the game). The home pages show the numbers in the
live ticker under the header (`site.js`), which stays hidden while `/api/stats` has nothing to show. Counters are in
`/var/lib/ukgames-stats/stats.db` (SQLite, per day in UTC and in total).
Google Analytics forwarding is optional: fill in `GA_MEASUREMENT_ID` and `GA_API_SECRET` in `/etc/ukgames-stats.env`
(GA4 > Admin > Data streams > Measurement Protocol API secrets) and restart the service; events arrive as `bb_*`.
To update the handler: copy the file to `/opt/ukgames-stats/` and `systemctl restart ukgames-stats`.
