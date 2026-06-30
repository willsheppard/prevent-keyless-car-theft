# StopKeyless

Source for **[stopkeyless.com](https://stopkeyless.com)**, a free, independent site that shows car owners the manufacturer-approved way to disable keyless entry and stop relay theft.

All the instructions live in [`data/cars.json`](data/cars.json) (field reference in [`data/README.md`](data/README.md)).

## How it works

A small static-site generator. `scripts/build.py` (Python + Jinja2) renders pages from `data/cars.json` into `dist/`. The homepage finder (`index.html` + `js/app.js`) reads the same data in the browser.

```bash
pip install -r requirements.txt
python scripts/build.py            # render the whole site into dist/
```

## Help wanted

This is a community project and it relies on people who know their cars.

**Know how to disable keyless entry on a car that is missing or wrong here?** This is the single most useful thing you can give. Confirm the steps from your owner's manual or your own car, then either open an issue or edit [`data/cars.json`](data/cars.json) and send a pull request. Cite a source where you can: people rely on these instructions being correct.

---

Tested with [BrowserStack](https://www.browserstack.com/)
