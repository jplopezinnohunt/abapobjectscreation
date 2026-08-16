# Recuperación — qué hacer cuando este disco muera

> Un backup que nunca se ha restaurado es una hipótesis. Todo lo de aquí abajo se ha
> **ejecutado**, no diseñado. Las cifras son las de la última prueba real.

Este documento vive en el repo, así que está en GitHub: **si el disco muere, esto se lee
desde origin**, no desde la máquina perdida.

---

## Los tres activos, y cuál protege qué

| activo | dónde vive | protección | irreemplazable |
|---|---|---|---|
| código, brain, companions, algoritmos | repo git | **origin** (GitHub) | no — está fuera |
| `~/.claude` (memoria + config) | `%USERPROFILE%\.claude` | zip en `--dest` | **SÍ** |
| Golden DB | `Zagentexecution/.../p01_gold_master_data.db` | snapshot en `--dest` | parcialmente |

**El golden es el más grande y el menos irreemplazable**: 16,33 GB que se pueden volver a
extraer de P01 en horas usando los cargadores del repo. `~/.claude` son 1,6 MB que **nada ni
nadie puede reconstruir** — son las notas de por qué se decidió cada cosa.

---

## Orden de recuperación

Este orden importa: cada paso deja utilizable el siguiente.

### 1 · El repo — primero, porque contiene todo lo demás

```bash
git clone https://github.com/jplopezinnohunt/abapobjectscreation.git
```

Recupera el código, los 193 rules, los 482 claims, los tres companions, los 40 algoritmos y
**este runbook**. Comprobar que llegó entero:

```bash
python scripts/verify_generated.py
```

### 2 · `~/.claude` — la memoria, y es lo que no se puede rehacer

```bash
python scripts/backup_golden.py --restore <ruta>/claude_home_AAAAMMDD_HHMM.zip --to ./_restore
```

Restaura a un **directorio de ensayo**, nunca encima del `~/.claude` vivo — así el simulacro
se puede hacer un martes cualquiera sin miedo. Verifica solo: cuenta ficheros del zip contra
los del disco y exige ≥50 de memoria.

**Última prueba real:** 595 ficheros del zip, 595 en disco, 474 de memoria. OK.

Luego, a mano y a propósito:
1. renombrar `~/.claude` a `~/.claude.old`
2. mover `./_restore` a `~/.claude`
3. **volver a iniciar sesión** — el token OAuth no está en la copia, por diseño

### 3 · El golden — el más lento, y el que puede esperar

Si hay snapshot:
```bash
python scripts/backup_golden.py --verify <ruta>/p01_gold_AAAAMMDD_HHMM.db
```
Comprueba integridad y contrasta los conteos de fila contra
`Zagentexecution/sap_data_extraction/golden_manifest.json`. Si cuadra, se copia en su sitio.

**Si NO hay snapshot** — y esto es lo que acota el peor caso: el golden es **reproducible**.
El manifiesto guarda las 369 tablas con sus conteos y **las reglas aplicadas a cada una**, así
que la reconstrucción es guionizada, no arqueológica:

```bash
python scripts/extraction/load_wide_tables.py --all --year 2026
python scripts/extraction/purge_simulation_runs.py --apply
```

Horas de extracción contra P01, pero **cero pérdida de conocimiento**: se sabe exactamente qué
se cargó, con qué filtros y qué reglas se aplicaron encima.

---

## Lo que NO se recupera, dicho claramente

**El token OAuth** (`.credentials.json`). Excluido a propósito: es re-obtenible iniciando
sesión, y un disco externo perdido con un token vivo dentro es un incidente distinto de uno
con notas dentro.

**Las transcripciones de sesión** (1.836 MB de `.jsonl`). Excluidas: son el 99,9% del tamaño y
no son el conocimiento — el conocimiento ya está promovido a claims, reglas y memoria. Si
importaran, el pase del steward habría fallado en su trabajo.

**Lo que no llegó a commitearse ni a promoverse.** Git no protege lo que no has empujado, y el
brain no protege lo que se quedó en el chat. Por eso el cierre tiene sus gates.

---

## El simulacro — cómo saber que esto funciona

```bash
python scripts/backup_golden.py --claude-only --dest <disco externo>
python scripts/backup_golden.py --restore <disco>/claude_home_*.zip --to /tmp/drill
```

Si la segunda dice `verificacion: OK`, la cadena entera está probada. Cuesta segundos.

**Dos defectos que solo aparecieron al probarlo**, y que son la razón de que este apartado
exista:

La primera versión del backup capturó **4 ficheros y cero de memoria** — `pathlib` resuelve
`skills/**` como directorios, no como ficheros recursivos; hacía falta `**/*`. Y peor: **escribió
el zip igualmente**. Ahora aborta si encuentra menos de 50 ficheros de memoria, porque un
backup de la memoria que no contiene memoria no es un backup, es un fichero que lo parece.

La exclusión de secretos **se verifica leyendo el zip ya escrito**, no confiando en el filtro.
Si algo se cuela, el zip se borra en vez de viajar.
