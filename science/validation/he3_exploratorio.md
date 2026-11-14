# HE3 exploratorio (14 de noviembre de 2026)

**Esto no reemplaza el resultado de HE3** (`he3_resultados.md`, que no se sostiene). Estas tres
variantes se corrieron después de ver ese resultado, así que sus p son exploratorios: sirven para
decidir qué medir la próxima vez, no para afirmar la hipótesis. Cada variante calibra solo con
trechos de calibración (sol ≤ 606) y mide con los de medición. Script: `he3_exploratorio.py`.

| Variante | n cal / med | Pesos de A (pendiente, capa, inestabilidad) | A < B | B < C |
| --- | --- | --- | --- | --- |
| Trechos de 1 a 3 km | 9 / 9 | 4, **0.46**, 1.0 | 5–3, p = 0.29, r = 0.20 | 5–3, p = 0.16, r = 0.35 |
| NOAH-H como fracción intransitable | 18 / 18 | 4, **10** (tope de la rejilla), 1.0 | 6–9, p = 0.97 | 9–8, p = 0.25, r = 0.17 |
| Calibrar también la pendiente | 18 / 18 | **0.1**, 0, 0.1 | sin pares discordantes | 9–7, p = 0.25, r = 0.17 |

«5–3» quiere decir que gana en 5 trechos y pierde en 3. Ninguna variante cumple p < 0.025 y r ≥ 0.3.

## Qué sugiere

- **La escala importa.** Con trechos de 1 a 3 km, la calibración sí le da peso a NOAH-H (0.46): la
  pérdida baja de 50.7 m a 46.7 m. Con 0.5 a 1 km le daba 0. En la medición no se confirma, pero con
  9 pares la prueba tiene poco poder. Es lo primero que conviene medir con más trechos o con una
  grilla más fina.
- **La fracción intransitable sobreajusta.** La calibración la lleva al tope de la rejilla, como si
  las ondulaciones grandes fueran prohibidas, pero en la medición la ruta queda peor que sin la capa
  (gana 6, pierde 9).
- **A 25 m por celda, el rover se parece a la línea recta.** Si también se calibra la pendiente,
  todos los pesos bajan casi a cero. Perseverance esquiva obstáculos más chicos que una celda con su
  navegación autónoma, y eso no se ve en esta grilla.

## Para la próxima vez

1. Trechos de 1 a 3 km sobre una grilla más fina (HiRISE de 1 m donde haya cobertura), fijados de
   antemano.
2. Validar contra recorridos a pie (Apolo) en vez de un rover, porque la hipótesis es sobre personas.
