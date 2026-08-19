# Hipotesis

**H1 — El bloqueo se dispara en D01.**
Predicho a partir de `GB931`: D01 y P01 tienen la misma validacion `UNES` con 12 pasos y el
paso 012 presente (`CONDID 1UNES###009` / `CHECKID 2UNES###009`). Falsable: si contabiliza
sin `LZBKZ`, la asignacion `OB28` en D01 no es la de P01 y todo el plan de transporte cambia.
→ **CONFIRMADA.** Rechazado con `ZFI-036` severidad `E`.

**H2 — El fichero lleva la cadena, sin ABAP.**
Predicho a partir del fuente: `FI_CGI_DMEE_EXIT_W_BADI` selecciona la clase por el pais de
NUESTRO banco casa (`FPAYHX-UBISO`), `CM002` pasa el pais de SU banco (`FPAYH-ZBNKS`) y
`CM003` filtra `WHERE LAND1 = IV_LAND1`. Ningun literal de pais en las tres capas.
Falsable: si el `<Ustrd>` sale vacio o sin la cadena, la hipotesis de "cero ABAP" cae y hace
falta desarrollo antes del 5-sep.
→ **CONFIRMADA.** `<Ustrd>/Payment for goods or services received/INV/224938</Ustrd>`.

**H3 — La cadena sera exactamente la predicha por la simulacion.**
La prediccion se publico ANTES de generar el fichero. Falsable de dos maneras distintas y
esa es su virtud: si difieren, la diferencia dice si fallo la configuracion o si fallo
nuestro modelo del codigo.
→ **CONFIRMADA**, identica caracter por caracter.

**H4 (descartada antes de probarla) — Se puede usar `ZSAPFPAYM_REPLAY` sobre un pago
existente.**
Medido: en D01 hay 158 pagos a proveedores con banco egipcio, pero todos de 2014-2022 y solo
uno tiene medio generado, del arbol CITI, que no implementa el BAdI. Y aunque hubiera uno
del arbol CGI, esos pagos llevan `LZBKZ` vacio, asi que `CM003` no encontraria fila en
`T015L` y la descripcion saldria vacia.
→ **Un replay solo puede probar fontaneria, nunca contenido.** Por eso se hizo factura nueva.
