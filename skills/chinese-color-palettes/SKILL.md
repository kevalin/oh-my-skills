---
name: chinese-color-palettes
description: 16 curated traditional Chinese color palettes (中国传统色) from colors.app.stdrc.cc — each with 5 roles (background / text / primary / accent / auxiliary) and exact HEX values. Use when a design needs a Chinese-traditional color mood matched to content (cards, covers, posters, slides, charts). Includes mood-matching guide and color rules.
platforms: [linux]
---

# Chinese Color Palettes (中国传统色)

16 production-tested traditional Chinese color palettes, each with a 5-role structure and exact HEX values. Data file: `assets/palettes.json` (source: https://colors.app.stdrc.cc — classic palette gallery).

## Palette structure (5 roles per palette)

| Role | Usage |
|---|---|
| 背景色 background | page/card background |
| 文本色 text (ink) | body text on background |
| 主色 primary | main brand/emphasis color |
| 强调色 accent | highlights, callouts |
| 辅助色 auxiliary | secondary decoration |

## Palette quick reference (bg / ink / primary / accent / auxiliary)

| # | Palette | Mood (气质) | Hex |
|---|---|---|---|
| 1 | 青出于蓝 | 沉稳知性 professional | #F7F4ED / #2B333E / #1661AB / #1772B4 / #2775B6 |
| 2 | 落红有情 | 温柔浪漫 romantic | #FBECDE / #80766E / #F0ADA0 / #CE5777 / #F34718 |
| 3 | 水绿相宜 | 清新自然 healing | #EEF7F2 / #314A43 / #579572 / #1BA784 / #22A2C3 |
| 4 | 白立五色 | 现代极简 high-contrast | #F1F0ED / #2F2F35 / #1661AB / #F43E06 / #FCC307 |
| 5 | 宫墙丹黄 | 喜庆传统 festive | #F7F4ED / #483332 / #ED5126 / #FCC307 / #5BAE23 |
| 6 | 江山青绿 | 山水雅致 classical | #F7F4ED / #617172 / #B9DEC9 / #2C9678 / #1661AB |
| 7 | 烟霞桃绛 | 烟霞婉约 poetic | #E2E1E4 / #80766E / #F0ADA0 / #EA517F / #EE2C79 |
| 8 | 霁雪岚青 | 清冷高级 premium | #D8E3E7 / #5E616D / #2775B6 / #22A2C3 / #158BB8 |
| 9 | 春融 | 春日明快 spring | #EEF7F2 / #CAD3C3 / #55BB8A / #FBA414 / #EA517F |
| 10 | 秋实 | 秋收丰盛 autumn | #F7F4ED / #DE7622 / #BEC936 / #F34718 / #4D4030 |
| 11 | 冬夜 | 静谧深邃 night | #F1F0ED / #5E616D / #2E317C / #1661AB / #1E131D |
| 12 | 霜叶丹砂 | 秋叶复古 vintage | #F1F0ED / #80766E / #BE7E4A / #ED5126 / #F43E06 |
| 13 | 国潮金朱 | 国潮醒目 bold | #F7F4ED / #2F2F35 / #FFD111 / #F43E06 / #4D1018 |
| 14 | 青瓷雾岚 | 青瓷温润 celadon | #D8E3E7 / #617172 / #92B3A5 / #22A2C3 / #5E616D |
| 15 | 山茶暖棕 | 温暖复古 woody | #FBECDE / #4F4032 / #BE7E4A / #CF7543 / #5C1E19 |
| 16 | 海棠绛紫 | 艳丽绛紫 vibrant | #E2E1E4 / #4F383E / #F03752 / #AD6598 / #1E131D |

## How to choose a palette (match content mood)

1. Read the content, extract its **core mood** (calm / romantic / fresh / festive / classical / premium / bold / warm ...)
2. Match to the Mood column above; when two fit, prefer the one whose primary color supports the content's key metaphor
3. Apply the 5-role structure strictly: background, ink, primary, accent, auxiliary — never swap roles arbitrarily

## Color rules (CRAP-consistent)

- **Value/lightness contrast first**: ink must be readable on background (all 16 palettes are pre-verified light-background + dark-ink)
- ≤3 main colors in use at a time (background + ink + one primary is a safe default)
- Same function, same color (one accent color for all highlights)
- Warm palettes (宫墙丹黄/国潮金朱/山茶暖棕) advance — use for energetic/festive content
- Cool palettes (青出于蓝/霁雪岚青/冬夜) recede — use for calm/professional content
- Watch neutral tinting: in a warm palette, white/gray backgrounds pick up the warm cast

## Data file

`assets/palettes.json` — machine-readable, same 5-role structure, ready for theme generation:

```json
{ "palettes": [ { "name": "青出于蓝", "swatches": [ {"role": "背景色", "name": "鱼肚白", "hex": "#F7F4ED"} ... ] } ] }
```

## License

MIT — data from the public classic-palette gallery at colors.app.stdrc.cc.
