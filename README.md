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
