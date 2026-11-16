# @wazemars/contracts

TypeScript types generated from FastAPI's OpenAPI (source of truth: the Pydantic schemas in `apps/api/app/schemas`).

```bash
# with the API running on :8000
npm run contracts
```

Without a running API, the OpenAPI can also be written from Python (`create_app().openapi()` in
`apps/api`) and passed to `openapi-typescript` as a file. Until the web switches to `src/api.d.ts`, it uses the
hand-written types in `apps/web/lib/types.ts`; replace them with the generated ones when they are ready.
