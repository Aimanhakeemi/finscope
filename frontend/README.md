# FinScope frontend

React + TypeScript + Vite dashboard. Scaffold in milestone M1.

## Setup

```bash
npm create vite@latest . -- --template react-ts
npm i recharts
npm i -D tailwindcss postcss autoprefixer vitest @testing-library/react
npx tailwindcss init -p
```

## Structure (target)

```
src/
├── api/client.ts          # typed fetch wrapper around VITE_API_BASE
├── pages/
│   ├── Import.tsx          # CSV upload + column mapping
│   ├── Dashboard.tsx       # category totals, monthly trend, top merchants
│   ├── Subscriptions.tsx   # detected recurring charges
│   ├── Alerts.tsx          # anomalies
│   └── Ask.tsx             # NL question box -> answer + generated SQL
├── components/
│   ├── CategoryBarChart.tsx
│   ├── MonthlyTrendChart.tsx
│   └── DataTable.tsx
└── App.tsx
```

## Env

`VITE_API_BASE` — base URL of the FastAPI service (default `http://localhost:8000`).

## Scripts

| command | purpose |
| --- | --- |
| `npm run dev` | dev server on :5173 |
| `npm run build` | production build (checked in CI) |
| `npm test` | Vitest component tests |
