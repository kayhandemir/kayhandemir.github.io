# UKGames website

Source of [ukgames.net](https://ukgames.net/) (served with GitHub Pages).

- English home: `/`, Turkish home: `/tr/`
- Legal pages: `/page/privacy-policy`, `/page/privacy-policy-tr`, `/page/terms`, `/page/terms-tr`
- `app-ads.txt` must stay in the root for AdMob.

## Editing

Texts and games are in `tools/build.py`; styles are in `assets/site.css`.
After editing, rebuild the HTML and commit the result:

```
python tools/build.py
```
