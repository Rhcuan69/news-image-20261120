[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Rhcuan69/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Rhcuan69/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

# The World in One Day — Friday 20 November 2026

Entry for make.fun bounty **news-image-20261120**: sum up 20 November 2026's
world news in one image — https://make.fun/bounty/news-image-20261120

`main.py` copies the pre-rendered front page `news-20-nov-2026.png`
(1024×1024, 19 KB) to `/output/entry.png`. Deterministic, no network,
Python stdlib only. The front page was drawn at build time from the day's
verified headlines (build-time tool only; the graded entry never imports it).
The renderer is pure stdlib too — its own PNG encoder and bitmap font, no
Pillow, no numpy.

## The seven stories

1. **Russia hits Kyiv bridges in overnight barrage** — eight killed as more
   than 400 drones and 110 missiles strike; three Dnipro bridges damaged.
   (Reuters / The Times)
2. **Russian missiles and drone enter Poland** — two missiles and a jet drone
   cross in; jets scrambled; Warsaw seeks NATO aid. (Reuters / Just Security)
3. **Cyclone Akvan makes landfall in Odisha** — crosses coast near Gopalpur;
   over 300,000 sheltered; no deaths reported. (Reuters / The Hindu BusinessLine)
4. **Estonia to close border with Russia** — crossings shut from 1 December
   for six months; Moscow vows to respond. (Reuters / Just Security)
5. **Iraqi forces enter militia stronghold** — troops move into Jurf al-Sakhar
   in a deal to curb Kataib Hezbollah. (Reuters / Al Jazeera)
6. **Stocks slide worldwide as AI sell-off deepens** — Asian shares head for
   worst week since 2020; US futures fall. (Reuters / Investopedia)
7. **Mamdani plans to close Rikers by 2032** — mayor unveils plan to shut the
   jail complex and cut inmates to about 4,100. (AP / CNN)

All seven were first reported on Friday 20 November 2026, worded as
reported, without hype or invented facts.

## How to run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (byte-identical on every run)
```

Re-render the image (pure stdlib, no dependencies):

```sh
python3 tools/render_news.py
```

## License

MIT — see [LICENSE](LICENSE).
