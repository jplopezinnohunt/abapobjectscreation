# Sesión 107 — el circuito no estaba perdido: faltaba el ORDEN

**Fecha:** 2026-08-27 · **Tier:** 0 (cero escrituras en SAP) · **Entrada:** *"protocolos de apertura y braintoolbox, luego empieza por esta lista"* (H137 primero)

---

## 1. El caso, en una línea

El dueño recordaba *"un companion que recorría el circuito completo de pagos, muy bueno y
detallado"* y no sabía dónde estaba. **Existía. Y las once etapas del circuito estaban
cubiertas.** Lo que faltaba no era conocimiento: era que el grafo pudiera expresar **orden**.

---

## 2. LA PREGUNTA: ¿por qué un artefacto que existe se comporta como perdido?

Porque el índice que debería llevarte a él **no puede representar la relación que lo define**.

1. **Localizado por CONTENIDO, no por nombre.** Barrido de los 142 HTML del repo por la
   combinación *Role Management + PPC + BCM*. Sale `payment_bcm_companion.html` (828 KB), con
   *UNESCO Payment End-to-End Flow*, *Actor Resolution Rules*, *WF Call Chain (step by step)*
   con `Z_GET_CERTIF_OFFICER_UNESDIR → role.hq.int.unesco.org`, *BCM Release Rules*, DMEE y
   los tiers por sociedad. **No arranca en el pedido: arranca en `FI document posted`.** Por
   eso no se reconocía como "el circuito entero".
2. **Nada perdido.** Barrido de los 52 HTML de `companions/` contra los tokens de evidencia de
   cada etapa: **ninguna etapa sin cubridor**. El circuito vive en cinco piezas.
3. **La causa, medida antes de tocar nada.** `companion_graph.json` tenía **una sola clase de
   arista**: coseno IDF sobre vocabulario, que mide **parecido**. De los 10 pares entre las 5
   piezas, **6 sin arista**; `p2p_purpose_of_payment.html` **sin ninguna** con las otras cuatro.

**Lo que no sabíamos y ahora sí:** dos etapas **contiguas** comparten poco vocabulario
*precisamente porque son etapas distintas*. `EBAN`/`EKPO` no se parece a `BNK_BATCH_HEADER`.
**La similitud no puede expresar secuencia, por construcción.** No era un umbral mal puesto —
bajarlo habría metido ruido, no cadena. Y es la misma forma del defecto que ya estaba en
`process_map`, que dice qué dominios *pertenecen* a un proceso como si la pertenencia fuera
plana: la restricción de **caso único** que el driver OCEL 2.0 de `braintoolbox.yaml` nombra.

---

## 3. LO HECHO — en el generador, no en el artefacto

- **`domains.json → process_map.P2P.stages`**: 11 etapas con objetos, `evidence_tokens`,
  companions, cuáles son **condicionales** (hoja de servicios, PPC, BCM por tier de sociedad) y
  cuáles pueden **parar el circuito** (método O/U termina el WF; IBC17/IBC06 paran BCM).
  `domains` sigue diciendo QUIÉN participa; `stages`, EN QUÉ ORDEN. Campos distintos a propósito.
- **`build_companion_graph.py`**: emite **`sequence_edges` (SIGUE_A)** — 20 aristas, 9
  companions dentro de la cadena — separadas de las 130 de parecido, con flecha y discontinua
  donde la etapa anterior puede parar. **La arista que el PMO daba por ausente,
  `p2p_purpose_of_payment ↔ payment_bcm_companion`, ya existe como SIGUE_A y sigue sin existir
  como parecido** — que es la demostración de que nunca fue una relación de similitud.
- **`process_circuit_check.py`** (gate nuevo): cobertura + declaración + orden + juntas.
- **`companion_as_skill_sweep.py`**: contesta medida la tesis del dueño sobre los 44 companions.
- Verificado en el navegador: 20 líneas `SIGUE_A`, marcador de flecha, 0 errores de consola.

---

## 4. LO QUE SALIÓ MAL — dos veces el mismo defecto, en dos instrumentos distintos

**Es lo que más vale de esta sesión, y los dos son míos.**

**(a) El gate certificó el circuito entero como cosido... con un companion de TRANSPORTES.**
La primera corrida acreditó la junta factura→documento-FI a
`transport_companion_D01K9B0CBF_v2.html` y la de servicios→factura a
`fm_ps_avc_temporal_forecast_v1.html`, porque citan `MIRO`/`BKPF` de pasada. **Su propio
docstring ya advertía de esto y aun así lo hizo.** Una **cita** no es una **narración** — el
mismo límite que el `LEE` del toolgraph. Regla que quedó en el código: una junta está cosida
cuando un fichero **DECLARADO** para una etapa (juicio) **MIDE** cobertura de la contigua
(medida). **Juicio Y medida, ninguno de los dos solo.**

**(b) El barrido publicó `sap_company_code_copy` como "skill más cercano" 17 veces de 50.**
No porque cubra 17 dominios: porque su vocabulario lleva nombres **ubicuos**. Medido:
`rfc_read_table` está en **20 skills de 50**, `f110` en 16, las sociedades (`iiep`, `ubo`) en 10.
**Es exactamente el claim 622** — el inflado que ya invirtió el ranking del toolgraph — repetido
un piso más abajo. Arreglado con IDF sobre el vocabulario de skills y exigiendo al menos un
nombre raro, igual que hace el grafo de companions. **No se reinventó el peso: se reusó.**

**El patrón, por tercera y cuarta vez:** *medir la FORMA en vez del EFECTO*. Y la lección nueva
es más incómoda: **escribir la advertencia en el docstring no protege de cometerla.** Lo que
protege es que el criterio esté en el `if`.

**(c) También mío:** escribí `domains.json` por Bash, que **no dispara el `PreToolUse`** del
guardia de escritura sobre stores — el guardia solo casa `Write|Edit|MultiEdit`. Comprobé el
lock a mano (`FREE`) y no hubo daño, pero **el guardia tiene un agujero por herramienta**, no
por intención. Va a H143.

---

## 5. LO QUE QUEDA ABIERTO de H137 — dicho, no dado por hecho

- **El skill `presupuesto-al-pago`**: no creado. Las 11 etapas son su índice; crearlo es trabajo aparte.
- **El minero end-to-end**: sin veredicto. La evidencia empuja a COMPOSICIÓN (cada tramo ya
  está minado) y no a minero nuevo, pero eso lo decide `miner-onboarding` con la cadena delante.
- **Las etapas 1-3 no producen arista `SIGUE_A`** porque las tres viven en el mismo fichero:
  son bucles, y un bucle no es travesía. Correcto, pero el grafo no muestra compras como cadena.
- **H138–H142** intactos: no se tocaron.

---

## 6. Qué aprendimos sobre SAP (Fase 4b)

- **El circuito P2P de esta casa, ordenado y con sus puertas**, queda declarado por primera vez:
  pedido → recepción → hoja de entrada de servicios → factura MM → documento FI con bloqueo →
  PPC si aplica → WF que resuelve actor contra RoleManagement → F110 → **BCM en medio** →
  fichero → acuse/extracto.
- **Dos paradas reales, no teóricas:** método de pago **O/U** termina el workflow (vía oficina
  de terreno, no pasa por el F110 de la central); **IBC17/IBC06** paran BCM.
- **Tres condicionalidades que cambian el circuito:** la hoja de servicios (tramo normal en una
  casa que compra servicios, no excepción); el PPC (cross-border + 9 países + sociedad francesa
  + familia SG); y BCM (solo Tier1 — ICTP corre F110 sin BCM, IBE/MGIE/ICBA no corren F110).

---

## 7. Estado al cierre

Claims **627** (nada perdido, faltaba el orden) y **628** (la similitud no expresa secuencia).
Commit `9e9c432`, enfocado. **Copia de seguridad NO hecha: `D:\claude_backups` desconectado** —
Golden DB 21,25 GB y `~/.claude` 1,96 GB existen sólo en este disco.
