# FinScope — Visual Design Direction

This document defines FinScope's visual system: a "statement" aesthetic that
favours legible numbers over dashboard chrome. Treat the tokens below as fixed;
changing them is a deliberate design decision, not a casual edit.

## Concept: "Statement"

FinScope should feel like a **well-made bank statement**, not a dashboard. The
numbers are the subject. Money is tabular data, so every amount, total, and axis
label is set in a monospace with tabular figures and right-aligned like a printed
ledger. Everything around the numbers is quiet: warm paper, ink text, hairline
rules, one restrained accent.

Primary theme is **light (paper)**. A proper **dark** theme ships alongside it
with a toggle in the masthead.

---

## Color tokens

Define as CSS custom properties on `:root` (light) and `:root[data-theme="dark"]`.
Never hard-code a hex outside this table.

### Light (paper) — default
| token | value | use |
| --- | --- | --- |
| `--paper` | `#FBFAF6` | page background |
| `--paper-sunk` | `#F1EEE6` | recessed panels, table header rows, inputs |
| `--ink` | `#1C1B18` | primary text, numbers |
| `--ink-soft` | `#6B675E` | labels, captions, secondary text |
| `--rule` | `#DAD5C9` | all hairline borders and dividers |
| `--ledger` | `#1F6F4A` | the one accent: positive amounts, links, active nav, primary button |
| `--ledger-wash` | `#E7F0EA` | subtle positive-row background |
| `--flag` | `#B23A2E` | outflows, alerts, negative amounts, destructive |
| `--flag-wash` | `#F6E9E7` | subtle alert-row background |

### Dark
| token | value |
| --- | --- |
| `--paper` | `#161512` |
| `--paper-sunk` | `#1F1E1A` |
| `--ink` | `#ECE8DD` |
| `--ink-soft` | `#9A968A` |
| `--rule` | `#33302A` |
| `--ledger` | `#4FB07E` |
| `--ledger-wash` | `#18241D` |
| `--flag` | `#E0685A` |
| `--flag-wash` | `#2A1C19` |

Chart series: income = `--ledger`, spend = `--flag`. Gridlines = `--rule`. No
drop shadows anywhere in the app.

---

## Typography

Three faces, from Google Fonts (self-host via `@fontsource-variable/*` packages so
there is no external request; if that is impractical, a single `<link>` in
`index.html` is acceptable).

| role | face | notes |
| --- | --- | --- |
| Display / headings | **Space Grotesk** | 600–700. Page titles and the wordmark only. Tight tracking (`-0.02em`) on large sizes. |
| Body / UI | **Hanken Grotesk** | 400/500. All prose, buttons, nav, form text. |
| Numbers / data / code | **IBM Plex Mono** | 400/500, `font-feature-settings: "tnum"`. Every currency value, every numeric table cell, chart axis ticks, and the generated SQL on the Ask page. |

### Scale
| element | spec |
| --- | --- |
| Page title | Space Grotesk 700 · 30px · `-0.02em` · `--ink` |
| Section eyebrow | Hanken Grotesk 600 · 12px · uppercase · `0.09em` letter-spacing · `--ink-soft` |
| Body | Hanken Grotesk 400 · 15px / 1.55 · `--ink` |
| Statement "net" figure | IBM Plex Mono 500 · 38px · `tnum` · `--ink` |
| Table numeric cell | IBM Plex Mono 400 · 14px · `tnum` · right-aligned |
| Label / caption | Hanken Grotesk 500 · 12px · `--ink-soft` |

Negative amounts render as `− $36,885.55` (real minus sign `−`, space, then `$`).
Positive render as `+ $83,006.98` only in the statement header; elsewhere no `+`.

---

## Layout

### Masthead (every page)
Slim bar, hairline rule underneath.
```
FinScope                         Dashboard  Import  Subscriptions  Alerts   ☾
‾‾‾‾‾‾‾‾                                                                   (theme)
```
- Wordmark: Space Grotesk 700, with a 2px `--ledger` underline under just the word.
- Nav: plain Hanken Grotesk text links, `--ink-soft`; active = `--ink` with a 2px
  `--ledger` underline.
- Theme toggle: far right, a small text control `LIGHT` / `DARK` in IBM Plex Mono
  11px, or a sun/moon glyph. Persist choice to `localStorage`.

### Dashboard — signature element
Replace the three stat cards with a **statement header block**: a bordered panel
(`1px --rule`, 4px radius, `--paper`) laid out like the top of a paper statement.
```
┌─────────────────────────────────────────────────────────────┐
│  STATEMENT PERIOD            Sep 1, 2025 — Aug 1, 2026       │
│                                                             │
│  Opening balance                                    $0.00   │
│  Total in                                    + $83,006.98   │
│  Total out                                   − $36,885.55   │
│  ═══════════════════════════════════════════════════════    │  ← double rule
│  Net position                                 $46,121.43    │  ← 38px mono
└─────────────────────────────────────────────────────────────┘
```
- Right-aligned mono numbers, label column left in `--ink-soft`.
- The line above "Net position" is a **double hairline** (accounting-total
  convention) — a real detail that encodes meaning, not decoration.
- Optional single flourish: the net figure counts up once on load (~500ms),
  skipped under `prefers-reduced-motion`.

Below the header: the two charts side by side (stack on mobile), each in a plain
panel with a section eyebrow ("SPEND BY CATEGORY", "MONTHLY TREND") — no rounded
shadowed card, just `1px --rule` and 4px radius. Then "TOP MERCHANTS" as a ledger
table (see below). Then the forecast card, same panel treatment.

Chart plot containers use an explicit height so Recharts can resolve its
`ResponsiveContainer`: 300px at desktop widths and 260px below 840px.

### Transactions page

The dashboard shows the 10 most recent transactions, with a `10 most recent`
caption and a `View all transactions →` link. The `/transactions` page is the
full ledger: it displays 50 rows per page, keeps inline category editing, and
provides category, recurring, anomaly, and date-range filters above the table.

### Charts (Recharts restyle)
- Colors from tokens only. Income line `--ledger`, spend line `--flag`.
- Gridlines `--rule`, 1px. Axis text: IBM Plex Mono 11px `--ink-soft`.
- No gradient fills, no shadows, no rounded bar caps beyond the existing 4px.
- Tooltip: `--paper` bg, `1px --rule`, mono numbers.
- Legend: small, mono, top-right.

### Ledger table (Subscriptions, Top merchants, Alerts, Ask results)
- Header row: `--paper-sunk` background, labels in section-eyebrow style.
- Body rows separated by `1px --rule`; row hover = `--paper-sunk`.
- Text columns left (Hanken Grotesk), numeric columns right (IBM Plex Mono `tnum`).
- **Totals row** (Subscriptions "total monthly cost", Ask aggregate): preceded by a
  double hairline, label in `--ink`, value bold mono.
- Wrap in `overflow-x: auto` on mobile.

### Subscriptions page
Ledger table: Merchant · Cadence · Monthly cost · Next expected · (status dot).
`price_changed` rows get a small `--flag` "price up" tag. Inactive rows dimmed to
`--ink-soft`. Double-rule total row at the bottom: "Total — X / month · Y / year".

### Alerts page
Each alert is a table row with a 2px `--flag` left border and a `--flag-wash`
background on hover. Amount in mono `--flag`. Reason in `--ink-soft` below the
merchant. Empty state: "No unusual charges in this period." (not a sad face — an
all-clear statement).

### Ask page
- Question input: `--paper-sunk`, `1px --rule`, 4px radius, focus = 1px `--ledger`
  ring. Placeholder: `e.g. how much did I spend on coffee since June?`
- Generated SQL: shown in a sunk panel with a "QUERY" eyebrow, IBM Plex Mono 13px,
  `--ink-soft`, wrapped, read-only. This is a feature, not an afterthought — the
  point is that the answer is auditable.
- Result: ledger table. Single-number answers get the statement-figure treatment
  (large mono).
- LLM-disabled state (no API key): a plain panel — "Natural-language questions
  need an API key. Add `ANTHROPIC_API_KEY` to your `.env` to enable this." No error
  styling; it is a configuration note.

---

## Components

| component | spec |
| --- | --- |
| Primary button | `--ledger` bg, `--paper` text, 4px radius, Hanken Grotesk 500, 14px, `10px 16px` padding. Hover: 8% darken. |
| Secondary button | transparent, `--ink` text, `1px --rule` border, same metrics. |
| Input / select | `--paper-sunk` bg, `1px --rule`, 4px radius, focus `1px --ledger` ring (`box-shadow: 0 0 0 1px var(--ledger)`). |
| Panel | `--paper` bg, `1px --rule`, 4px radius, `20px` padding, section eyebrow as the heading. No shadow. |
| Hairline | `1px solid --rule`. Double rule = two 1px lines 3px apart, or `border-top: 3px double --rule`. |
| Status dot | 6px circle: `--ledger` active, `--ink-soft` inactive. |

Border radius is **4px everywhere** (not 0, not 12px). Spacing scale: 4 / 8 / 12 /
16 / 24 / 40 / 64.

---

## Motion

Restrained. All of it respects `prefers-reduced-motion: reduce` (then: no
transforms, opacity-only or nothing).
- Route change: content fades + rises 8px over 200ms.
- Net figure: one-time count-up on dashboard load, ~500ms ease-out.
- Links / table rows: 120ms color transition on hover.
- Nothing else. No parallax, no ambient animation, no staggered card reveals.

---

## Quality floor

- Responsive to 360px: masthead nav wraps or collapses to a menu; charts stack;
  tables scroll inside `overflow-x: auto`; the statement header stays readable.
- Visible keyboard focus on every interactive element (the `--ledger` ring).
- Color is never the only signal: alerts have the left border + the word, positive
  vs negative also carries the `+` / `−`.
- Contrast: `--ink` on `--paper` and `--ink-soft` on `--paper` both meet WCAG AA.

---

## What NOT to do

- No purple/blue "fintech" gradients, no glassmorphism, no neon.
- No shadows, no glon, no rounded-2xl cards.
- Don't turn it into a newspaper: this is a *statement*, so keep it roomy and
  right-aligned, not dense columns with zero radius.
- Don't add icons for decoration. A few functional glyphs (theme toggle, status
  dot, external-link) only.
- Don't invent new accent colors. `--ledger` and `--flag` are the whole palette.
