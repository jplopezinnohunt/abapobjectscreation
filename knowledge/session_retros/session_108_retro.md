# Sesión s108 — INC-000013624 y la naturaleza de cuenta bancaria

**Fecha:** 2026-08-28 · **Entrada:** un `.eml` de Ingrid Wettie: «el cambio de cuenta no funciona»

## Qué se pidió y qué salió

Se pidió diagnosticar por qué el extracto electrónico de `NTB02-EUR01` dejó de procesarse tras
cambiar el número de cuenta. **Causa raíz en 2,8 minutos:** `T028B` (*Transaction Type of Sender
Bank*) está tecleada por el número de cuenta, `FI12` solo escribe `T012K`, y la fila quedó
huérfana. El extracto dejó de entrar **en silencio** — job en verde, ficha perfecta.

De ahí salió mucho más de lo pedido, y esa expansión fue del usuario, no mía.

## Lo que se aprendió del SISTEMA

1. **El número de cuenta vive en dos tablas de customizing**, y de 41 candidatas solo `T012K` y
   `T028B` contienen las cuentas de UNESCO.
2. **El pipeline real no era el documentado.** No es `RFEBKA00` ni SWIFT: es el job
   `EBS INTEGRATION` → `FEB_FILE_HANDLING`, variante `EBS JOB_COUPA`, sobre el share de Coupa.
   `TBTCP` no tiene ni un paso con `PROGNAME RFEB*`.
3. **El parque no es homogéneo:** 120 electrónicas · 8 manuales · 27 mixtas · 12 sin extracto. Y
   las cerradas se marcan **en el texto** (237 de 411), no con un campo.
4. **La naturaleza de una cuenta no está modelada.** Tres candidatos medidos y los tres fallan:
   YBANK clasifica geografía × divisa, `FDLEV` es binario, y el balance FS10 mete las 352 en
   `Cash with Banks` teniendo posiciones de inversión sin usar.
5. **FF67 no es configuración** — ni su cabecera (`FEBKO-ABSND`) ni su lista de cuentas, que es
   historial. Una cuenta nueva no aparece hasta su primer extracto.
6. **9 modelos de extracto, 259 reglas**, cinco para una sola cuenta.

## Los cinco ceros falsos — el patrón de la sesión

Cinco veces publiqué o estuve a punto de publicar un cero que significaba *no puedo ver*:
`T030H` leído por `KONKO` (campo inexistente) · YBANK buscado por `OBJ_NAME LIKE 'YBANK%'` cuando
se transporta como `TDAT GRW_SET` · el mismo YBANK buscado en el `E071` de P01 cuando el transporte
es `D01K*` · `ZCASH` buscado en `TSTC`/`VARID`, donde un Report Painter no vive · y el parecido
entre formatos medido por tupla exacta cuando la pregunta era de forma.

**No hacía falta una regla nueva:** las 258 ya lo cubren. Se extendió
`feedback_name_the_source_before_you_assert` con la quinta forma — *una lectura que sale bien en el
sitio equivocado tampoco es ausencia*, y es peor que una fallida porque no avisa.

## El fallo de método que costó más

**El modelo de banca ya existía y no lo miré.** `house_bank_roles.json` (211 KB) +
`bank_model_explorer.py` + el agente `bank-process-discovery`. Sus hallazgos de la noche anterior ya
publicaban `FEB_FILE_HANDLING activo` — el job que tardé **13 minutos** en descubrir, el bloque de
tiempo más caro de la sesión — y una sección `receiving_accounts` que es mi `OPERATIVA_COBRO`.

**Causa:** no corrí `load_domain.py`, que es la regla CRITICAL #208 que el propio índice ordena.
Leí el índice y me fui a medir. El índice orienta; no da competencia.

## Reparto del tiempo (medido por marcas en disco)

| bloque | % |
|---|---:|
| reconstruir el pipeline de ficheros | 59 % |
| entender el caso | 25 % |
| dejar escrito + puerta + barrido | 9 % |
| **aislar la causa** | **8 %** |

Diagnosticar fue barato. Lo caro fue re-derivar conocimiento que ya existía.

## Qué queda vivo

- **INC-000013624:** SAP COMPLETO (`T012K` + `TIBAN` + `T028B` verificados en P01) — **escalado
  aguas arriba**: el fichero no llega, jamás ha entrado uno con `UNO18EUR`.
- **PMO H144:** naturaleza de cuenta bancaria, con los dos ejes de mejora y 4 decisiones de
  Tesorería.
- **Sin cubrir:** Golden DB 21,25 GB y `~/.claude` 1,98 GB — local-only, git no los protege.

## Aterrizaje

72 comprobaciones de auditoría, 68 en verde al primer intento; los 4 huecos (dos docs sin enlazar
desde el README, este retro y el `capability_model`) cerrados después. 6 instrumentos D1–D6 · 7
claims (633–639) · 5 docs · 2 skills · 1 agente · 2 companions · 2 ficheros de memoria.
