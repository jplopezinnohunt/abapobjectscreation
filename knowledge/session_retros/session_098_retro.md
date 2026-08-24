---
name: Sesión 098 — retro RECONSTRUIDO
description: Budget Rate, nómina end-to-end, la cadena fondo-WBS-trabajo y el filtro de realidad. Retro reconstruido el 2026-08-24 desde commits, memorias y artefactos, porque la sesión cerró sin escribirlo.
type: project
---

# Sesión 098 — retro reconstruido

> ⚠️ **Este retro NO se escribió en su momento.** Se reconstruye el **2026-08-24** desde los
> commits del 2026-08-02 al 2026-08-05, las 108 memorias de método que dejó etiquetadas, los
> tres companions que creó y las reglas que nacieron entonces.
>
> **Falta por tanto lo único que un retro escribe y la evidencia no guarda: qué se decidió no
> hacer, y por qué.** Lo demás está aquí porque quedó en artefactos.

## Cómo se descubrió que faltaba

Auditando la alcanzabilidad del conocimiento (sesión 103) apareció que **la 98 tenía 108
memorias de método y ningún retro** — el único hueco concreto al mirar hacia atrás, sobre 37
documentos creados en 60 días de los que solo 3 estaban huérfanos.

Es un buen ejemplo de que el conocimiento **del dato** sobrevive por sí solo (queda en stores)
mientras el **relato** se pierde si nadie lo escribe.

## Lo que produjo, por hilos

### Budget Rate — el hilo más largo

Doce commits seguidos, y el recorrido tiene forma de investigación real:

- El impacto, medido: **1,22 M USD sobre 9.407 parejas verificadas**, luego **2,37 M USD** por
  las cuatro rutas (A14).
- **Son DOS mecanismos**, no uno, y la fecha de conversión cierra 2024.
- Corrección honesta a mitad: *"el impacto solo sobre imputaciones financieras, y 2024 era
  coincidencia de tasas"*.
- **El lado de personal nunca se adoptó**: construido, pilotado, corrió **un solo mes — enero
  de 2025** — y paró. Perímetro decodificado: **2.086 empleados, el 8,8%**.
- La ruta 2 *"nunca estuvo vacía: vivía en una tabla que el golden tenía a 13 columnas"* — un
  extracto incompleto haciendo pasar por ausente algo que existía.
- Cierra con `A15`: el conocimiento como grafo, **17 sujetos y 20 aristas tipadas**.

### Nómina end-to-end (A16)

- **El puente nómina→FM es una tabla CUSTOM, `T9POST`**, y el enlace a mayor no está donde se
  buscaba.
- La determinación de cuentas **se lee en los documentos, no en la configuración**.
- **BR for Staff son 72 tipos Constant Dollar.**
- Y el defecto más caro: *"solo runs FINALES — las simulaciones inflaban el impacto nueve
  veces"*. Ese es el hallazgo que origina `A18`.

### A18 — el filtro de realidad

Lo registrado contra lo ocurrido, **en las dos direcciones**: qué filas nunca llegaron a ser
reales, y qué configuración no produce nada. Nace directamente del error anterior.

### PS y el donante

- *"El donante NO se fue de SAP — se fue del maestro de PROYECTOS."*
- *"Nada desplazó al donante: la dimensión SE FUE, y ahora escribe el maestro una interfaz."*
- `YYE_POC` marca la vía nueva del **Core Planner**.
- **Core Manager arrancó el 15-dic-2023 y cambió del todo en feb-2024.**
- `PRPS`: no es una capa dormida, son **31 campos en TRES ciclos de vida distintos**.
- Y una capa de clasificación entera del WBS, **construida y vacía**.

### A10 — la cadena fondo → WBS → trabajo

Reconstruida **por gramática, no por claves**: no hay clave ajena que una las tres cosas, así
que la convención de nombres se contrasta contra la estructura.

### A17 — gobierno de cambios

Qué cambia en producción, qué viaja por transporte y quién. Con un hallazgo incómodo: **el
editor ES la vía normal de los rangos**.

## Lo que dejó en los stores

| | |
|---|---|
| Memorias de método | **108** — 41 CARRIER, 39 TRAP, 17 INSTRUMENT, 7 METHOD, 4 SUBSTRATE |
| Companions | `budget_rate_companion_v1` · `payroll_end_to_end_companion_v1` · `project_wbs_companion_v1` |
| Algoritmos | A10, A14, A15, A16, A17, A18 |
| Regla | **#187 — un companion NOMBRA los objetos, nunca los cuenta** |

## Las lecciones que sí quedaron escritas

**El steward se murió a mitad.** Dos commits lo dicen: *"reparado lo que dejó el steward al
morir"* y *"la lección del steward muerto"*. Un pase de promoción que muere deja el trabajo a
medias y **parece completado**.

**Correr el paquete expuso defectos en los propios algoritmos** — dos en A18 y uno grave en
A16, encontrados al ejecutarlos juntos y no por separado.

**Una cifra obsoleta cazada en la memoria** durante el pase de steward: los stores también
envejecen.

## Lo que este retro NO puede recuperar

- Qué se decidió **no** hacer y por qué.
- Qué preguntas quedaron abiertas al cerrar.
- Cuánto costó cada hilo, y cuál se atascó.

Eso solo lo guarda un retro escrito en su momento. Es exactamente el argumento de por qué el
cierre de sesión lo exige.
