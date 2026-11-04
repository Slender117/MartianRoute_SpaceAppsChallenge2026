# @wazemars/contracts

Tipos TypeScript generados desde el OpenAPI de FastAPI (fuente de verdad: los esquemas Pydantic en `apps/api/app/schemas`).

```bash
# con la API corriendo en :8000
npm run contracts
```

Mientras no se genere `src/api.d.ts`, la web usa los tipos escritos a mano en `apps/web/lib/types.ts`; reemplázalos por los generados cuando estén listos.
