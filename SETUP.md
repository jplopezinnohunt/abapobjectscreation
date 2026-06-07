# SETUP — Operar este proyecto desde cualquier dispositivo

Guía única para dejar **operativo** este proyecto en una máquina nueva (otra PC,
una sesión en la nube, etc.). El objetivo es **interoperabilidad multi-device**:
clonas el repo y, siguiendo estos pasos, tienes el proyecto funcionando.

> **Modelo mental:** GitHub es la **única fuente de verdad**. Todo lo importante
> vive en git y viaja perfecto. Hay exactamente **2 cosas que git NO trae** (la
> Gold DB y los secretos) — esas se traen por un canal aparte (sección 4).

---

## 0. Qué viaja por git y qué no

| Categoría | ¿En git? | Cómo se obtiene en un device nuevo |
|-----------|----------|------------------------------------|
| Código (`lib/`, `scripts/`, ABAP/SAP extraído) | ✅ Sí | `git clone` |
| **Brain** (`brain_v2/`, `knowledge/`, skills, incidentes) | ✅ Sí | `git clone` |
| Companions, configs de agentes, docs de dominio | ✅ Sí | `git clone` |
| Dependencias Node (`node_modules/`) | ❌ No | `npm install` (paso 2) |
| Dependencias Python (`venv/`) | ❌ No | `pip install` (paso 3) |
| Artefactos generados del brain (`brain_v2/output/`) | ❌ No | `python brain_v2/rebuild_all.py` (paso 5) |
| **Gold DB** (`*.db` — 68+ tablas SAP) | ❌ No (gitignored) | Canal aparte (sección 4) |
| **Secretos** (`.env`, credenciales SAP) | ❌ No (gitignored) | Canal aparte (sección 4) |

---

## 1. Clonar

```bash
git clone <url-del-repo> abapobjectscreation
cd abapobjectscreation
```

**Lo PRIMERO que hace cualquier agente/sesión** (regla obligatoria del proyecto):
leer `brain_v2/brain_state.json` — un solo archivo con toda la inteligencia del
proyecto (12 capas). Ver `CLAUDE.md` → "MANDATORY FIRST ACTION".

---

## 2. Dependencias Node (automatización Playwright/SAP)

```bash
npm install
```

Instala (de `package.json`): `playwright`, `@playwright/test`, `@playwright/mcp`,
`playwright-sap`.

> Solo necesario si vas a **ejecutar automatización SAP** en este device. Para
> trabajo de brain/conocimiento/autoría no hace falta.

---

## 3. Dependencias Python

El **brain (`brain_v2/`) NO necesita librerías externas** — corre con solo Python
estándar (3.9+). Esto es clave: la inteligencia del proyecto funciona en cualquier
device con solo tener Python.

Para el **tooling avanzado** (extracción SAP, MCP backend) sí hay dependencias:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r Zagentexecution/SAP_MCP/requirements.txt
```

> ⚠️ Ese `requirements.txt` incluye `pywin32` (solo Windows). En Mac/Linux,
> instala solo lo que necesites; el brain no requiere nada de eso.

---

## 4. Las 2 cosas que git NO trae (canal aparte)

### 4a. Secretos / credenciales SAP

Nunca van a git (correcto). En un device nuevo, crea el `.env` a partir de la
plantilla:

```bash
cp Zagentexecution/mcp-backend-server-python/.env.example \
   Zagentexecution/mcp-backend-server-python/.env
# luego edita el .env con los valores reales
```

Variables esperadas (de `.env.example`):

```
SAP_ASHOST=...     # host/IP del servidor SAP
SAP_SYSNR=00
SAP_CLIENT=800
SAP_USER=...
SAP_PASSWD=...
SAP_LANG=EN
```

> Guarda estos valores en un gestor de secretos / bóveda — **no** en git, no en
> chat. Trasládalos manualmente al device nuevo.

### 4b. Gold DB (`p01_gold_master_data.db`)

La base de datos con 68+ tablas SAP extraídas. **Está gitignored** (`*.db`), así
que NO viene con el clone. El código la espera en:

```
Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db
```

Para tenerla en un device nuevo, una de estas opciones:

1. **Copiarla** desde un backup / almacenamiento compartido a la ruta de arriba.
2. **Re-extraerla** de SAP (requiere VPN + sesión SAP) con los scripts de
   `scripts/extraction/`.

> 💡 **Recomendación de portabilidad:** mantén un backup de la Gold DB en un
> almacenamiento persistente (no-git) y, si trabajas en varias máquinas, considera
> exponer su ruta por variable de entorno para no depender de la ruta fija.

---

## 5. Reconstruir artefactos del brain (si hace falta)

Los artefactos generados (`brain_v2/output/`) son reconstruibles:

```bash
python brain_v2/rebuild_all.py
```

Verificar que el brain está fresco:

```bash
python brain_v2/graph_queries.py stats
```

---

## 6. Preflight (validación de sesión)

El proyecto tiene guardrails ejecutables. Al iniciar trabajo:

```bash
python scripts/session_preflight.py --mode start
```

---

## 7. Checklist rápido para un device nuevo

- [ ] `git clone` + `cd`
- [ ] Leer `brain_v2/brain_state.json` (acción obligatoria #1)
- [ ] `npm install` (solo si harás automatización SAP)
- [ ] `pip install -r Zagentexecution/SAP_MCP/requirements.txt` (solo tooling avanzado)
- [ ] Crear `.env` desde `.env.example` con credenciales reales (canal aparte)
- [ ] Colocar la Gold DB en `Zagentexecution/sap_data_extraction/sqlite/` (canal aparte)
- [ ] `python brain_v2/graph_queries.py stats` para verificar el brain
- [ ] `python scripts/session_preflight.py --mode start`

---

## Disciplina multi-device (lo que mantiene todo sincronizado)

> **PC → push → otro device trabaja → push → PC pull.**

- Al terminar en cualquier device: `git add -A && git commit && git push`.
- Al empezar en cualquier device: `git pull` primero.
- Nunca edites la misma rama en dos devices a la vez sin pushear en medio.
- Lo que no está en GitHub, no existe para los demás devices.

---

## Límite conocido: ejecución contra SAP

Autoría / brain / conocimiento → **cualquier device** (incluida la nube/teléfono).
**Ejecutar y ver cambios contra SAP** → solo desde una máquina **dentro del VPN**
(GlobalProtect con SSO+MFA). La nube no alcanza SAP. Ver `CLAUDE.md` →
"workstation-bridge architecture".
