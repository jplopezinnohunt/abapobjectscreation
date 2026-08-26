# Output — el modelo de CÓMO SALE UN DOCUMENTO de esta instalación

> Dominio `Output`. Primer contenido real del dominio (sesión #105, 2026-08-26), nacido de
> **INC-000016471**. Antes de esto el dominio tenía `knowledge_docs: []`, `companions: []`,
> `skills: []`, coverage 20% y `primary_modules: ["FI"]` — que además era **falso**.

---

## 0. LA CORRECCIÓN QUE ABRE EL DOMINIO

`Output` estaba clasificado **STRANDED** en la columna vertebral de procesos: *"ni en un flujo ni
transversal a uno"*. **Es falso, y la prueba es el radio medido de una caída del motor de render:**

| Familia de documento | Proceso | Módulo |
|---|---|---|
| convenio de prácticas, certificados, evaluación (`YHRINT_`, 15) | **H2R** | HCM |
| contratos de personal (`YHR_CO`, 6-8) | **H2R** | HCM |
| attestations de trabajo (`YHRPA_ATT_*`, 7-9) | **H2R** | HCM |
| Personnel Action Form (`YHRPA_PAF`) | **H2R** | HCM |
| cartas de dunning (`YFI_DU`, 4-5) | **T2R / P2P** | FI |
| contratos y facturas RE-FX (`YRE_`/`ZRE_`, 6) | **A2R** | RE-FX |

> **`Output` es CROSS-CUTTING POR CONSTRUCCIÓN**, como `Integration`, `Support` y
> `Transport_Intelligence`: sirve a **todos** los procesos, y por eso no aparece en ninguno.
> `primary_modules` correcto: **HCM, FI, RE-FX** — no `FI` a secas.
>
> Esa reclasificación no es cosmética: un dominio *stranded* no tiene dueño, y por eso el canal por
> el que sale **todo PDF de la casa** estuvo caído **tres días laborables** sin que nadie lo supiera.

---

## 1. LA CADENA — de un dato a un documento fuera del edificio

```
   objeto de negocio            aplicación                motor de render            canal
  ┌────────────────┐      ┌────────────────────┐     ┌──────────────────┐     ┌──────────────┐
  │ expediente,    │      │ WebDynpro ABAP     │     │ ADS  (Adobe)     │     │ destino RFC  │
  │ contrato,      │ ───▶ │ ZPAWF_INT_AGREE    │────▶│ NO corre en ABAP │────▶│ `ADS` tipo G │
  │ factura, aviso │      │ ICF activo en P01  │     │ AS Java, otra    │     │ HTTP  :50300 │
  └────────────────┘      └────────────────────┘     │ máquina          │     └──────┬───────┘
                                   │                 └──────────────────┘            │
                          API ABAP │ FP_JOB_OPEN                                     ▼
                                   │ FP_FUNCTION_MODULE_NAME              hq-sap-sbp = SolMan PROD
                                   │ FP_JOB_CLOSE                         instancia ABAP 01 (SolMan)
                                   ▼                                      instancia Java 03 (ADS+SLD)
                          SFPI interfaz + SFPF formulario                        │
                          (YHRINT_IF_AGREEMENT_V2)                               ▼
                                                                              PDF
```

**Tres motores conviven y NO son lo mismo:**

| Motor | Compila a | ¿Pasa por ADS? | Medido en P01 |
|---|---|---|---|
| **Adobe (Interactive Forms)** | `/1BCDWB/SM*` | **SÍ** | **26 vivos** |
| **SmartForms** | `/1BCDWB/SF*` | **NO** | 11 generados |
| SAPscript | — | NO | sin medir |

Confundir `SF*` con `SM*` infla la población de Adobe y el radio de una caída.

---

## 2. LA TOPOLOGÍA — y por qué es frágil

**`hq-sap-sbp` NO es "la máquina de Adobe": es el Solution Manager de producción (SID SBP)**,
IP `172.16.4.107`. **Una máquina, dos pilas que arrancan y paran por separado:**

- **instancia ABAP 01** → Solution Manager (EWA, monitoreo, ChaRM/TMS)
- **instancia Java 03, puerto 50300** → **ADS + SLD**

P01 tiene **9 destinos RFC** a esa máquina: `ADS`, `SLD_DS_HTTP`, `SLD_DS_TARGET`, `SLD_NUC`,
`SLD_UC`, `SM_SBPCLNT200_BACK`, `SM_SBPCLNT200_TRUSTED`, `SM_SBP_TRUSTED_BACK`, `TRUSTING@SBP_*`.

> **Un reinicio de esa máquina se lleva ADS + SLD + SolMan a la vez.** Y es el **único AS Java de
> aplicación del paisaje P01**: sin respaldo, sin failover. Los otros 26 destinos tipo G a
> `SAPControl.CGI` (puertos 5NN13/5NN14) son agentes de monitoreo, no AS Java.

**Configuración del destino `ADS`** (`rfcdes`, tipo G):
```
H=hq-sap-sbp.hq.int.unesco.org  I=50300  N=/AdobeDocumentServices/Config?style=rpc
D=ADSUSER  Q=B (basic)  s=N (HTTP PLANO, sin SSL)  T=N (traza apagada)
```
**Deuda registrada:** la contraseña de un usuario de servicio cruza la red **sin cifrar en cada
render**, y no hay traza de cliente que mirar.

---

## 3. SON DOS CREDENCIALES, y confundirlas manda al log equivocado

| | Sentido | Dónde vive | ¿Visible para nosotros? |
|---|---|---|---|
| **`ADSUSER`** | **ida**: ABAP → Java (render) | UME de **Java** | **NO** — no está en `USR02` |
| **`ADS_AGENT`** | **vuelta**: Java → ABAP (`SAPMHTTP`, tcode `S000`, desde `172.16.4.107`) | `USR02` de P01 | **SÍ** |

- El *Connection Test* de **SM59 sólo prueba la IDA**. Si el bloqueado fuera `ADS_AGENT`, SM59
  daría 200 y **seguiría sin salir el PDF**.
- Un **401 de `ADSUSER` es estructuralmente invisible** para todo log ABAP nuestro: no hay sujeto
  ABAP al que atribuir el evento. **Frontera del instrumento, no hueco de datos** — no se cierra
  acumulando log.
- Rol **`ADSCALLERS`** creado **vacío a propósito** en 2021 (`D01K9B07XR`) y **sigue vacío** en
  `agr_users`: es el patrón estándar de SAP, el rol que importa vive en el UME de Java.

---

## 4. `D_DATA` — la generación de PDF **como dato**

Ésta es la fila `D_DATA` del capability_model para `Output`: dónde vive el hecho, y con qué clave.

| Qué | Dónde | Clave / cómo se lee | Estado |
|---|---|---|---|
| **el formulario** | `e071` (2,37M filas) | `OBJECT='SFPF'` → 757 totales, **43 custom** | ✅ en Gold DB |
| **la interfaz de datos** | `e071` | `OBJECT='SFPI'` → 111 totales, **15 custom** | ✅ |
| **el formulario VIVO** | `tfdir_all` (452K) | `FUNCNAME LIKE '/1BCDWB/SM%'` → **26** | ✅ **prueba de uso** |
| **SmartForms (no ADS)** | `tfdir_all` | `/1BCDWB/SF%` → 11 | ✅ |
| **el canal** | `rfcdes` (239) | `RFCDEST='ADS'`, parsear `RFCOPTIONS` | ✅ |
| **la credencial de vuelta** | `usr02` | `BNAME='ADS_AGENT'` (`UFLAG`, `GLTGB`, `TRDAT`) | ✅ |
| **el latido del host** | `rsau_audit_history` | `SLGLTRM2='172.16.4.107'` | ✅ |
| **el uso de la app** | `rsau_audit_history` | `PARAM1 LIKE '%ZPAWF_INT_AGREE%'` | ✅ |
| **el render en sí** | — | **NO EXISTE**: cero eventos `FP_*` en 6,5 meses | ❌ **no observable** |
| **nombre del formulario vivo** | `FPCONTEXT` / `FPLAYOUT` | mapea `SM000000nn` → nombre | ❌ **no extraído** |
| **estadística de uso estándar** | FM `FP_GET_USAGE_DATA` | censo con nombres en 1 llamada | ⚠️ **no usado aún** |
| **determinación de salida** | `TNAPR`, `NAST` | — | ❌ **no existen en Gold DB** |

**Los dos huecos que cierran el modelo:** extraer `FPCONTEXT`/`FPLAYOUT` (o llamar a
`FP_GET_USAGE_DATA`) para **poner nombre a los 26 vivos**, y decidir si `TNAPR`/`NAST` entran al
Gold DB para cubrir la determinación de salida.

> **El hecho más importante de esta tabla es la fila roja:** el render de un formulario Adobe **no
> deja ni un evento** en el log de auditoría. No es que la traza esté apagada — el evento no
> existe. Cualquier pregunta del tipo *"¿cuándo dejó de generarse?"* hay que contestarla por
> **proxy** (`A61_event_dating_without_a_trace`).

---

## 5. `F_INTERFACE_FILE` — disponibilidad, que sí se mide

El canal estaba etiquetado **`NO_MEDIBLE`**, con esta justificación:

> *"Un destino SALIENTE no registra en nuestro log qué hace en el sistema destino. Se mediría en el
> otro extremo. Ausencia de dato, no de riesgo."*

**Cierto del TRÁFICO. Falso de la DISPONIBILIDAD.** Se parte en dos ejes para los **239 salientes**:

| eje | valor | por qué |
|---|---|---|
| `medibilidad_trafico` | `NO_MEDIBLE_AQUI` | un saliente no registra qué hace al otro lado |
| `medibilidad_disponibilidad` | `MEDIBLE_DESDE_AQUI` | *"¿responde?"* se contesta sin credenciales en <1 s |

Y el veredicto `DEAD` de `interface_boundary.json` queda **superseded**: contaba llamadas **RFC**, y
una llamada **HTTP saliente no es RFC**. **40 de 40 destinos G/H con `observed_calls=0`** — una
tasa del 100% en una clase entera es la firma de un **instrumento ciego**, no una medida.
*(Falsador independiente: las 5 rutas al SLD figuran DEAD mientras `SAP_SLD_DATA_COLLECT` terminó
OK 126 veces empujando por una de ellas.)*

**El monitor ya existe:**
```bash
python Zagentexecution/quality_checks/ads_availability_check.py                # ADS
python Zagentexecution/quality_checks/outbound_channel_availability_check.py   # los 239
```
Primera corrida sobre la frontera: **39 probados · 6 arriba · 8 caídos · 25 indeterminados** (la
mayoría `DNS_FAIL`: son agentes `SAPControl` en hosts que no resuelven desde un portátil — límite
declarado del instrumento, mide desde donde se corre, no desde P01).

---

## 6. LA APLICACIÓN — `ZPAWF_INT_AGREE` y la familia PA-Workflow

WebDynpro ABAP **custom nuestro**, servido por ICF **en el propio P01** (nodo activo). **No es
Fiori, no es satélite, no es e-Recruiting.** Familia **`ZPAWF_` = PA-WorkFlow**: `__MAIN`, `_LWOP`,
`_SPA`, `_SEPARATION`, `_INT_HP`, `_INT_AGREE`. **Sólo hay 19 WebDynpros custom en toda la
instalación y 4 son de esta app.**

- **Uso medido:** 3.751 arranques por **210 usuarios distintos** en 6,5 meses; la familia `ZPAWF*`
  la usan **18-32 personas cada día laborable**.
- **El PDF es el paso TERMINAL**: sin él el expediente queda validado y **sin firmar**. Por eso una
  caída del motor de render es un bloqueo total aunque el flujo funcione.
- Un convenio francés son **4 renders**: `YHRINT_AGREEMENT_V2_MAIN_FR` + `_ANEX1/2/3_FR`.
- Lógica del botón: `YCL_HR_INT_WF_ASSIST`. Coautores: `N_MENARD` y `A_SEFIANI`.

*(Detalle de la familia en `knowledge/domains/HR-Workflows/`.)*

---

## 7. LO QUE FALTA (backlog del dominio)

1. **Nombrar los 26 formularios vivos** — `FPCONTEXT`/`FPLAYOUT` o `FP_GET_USAGE_DATA`.
2. **¿Qué JOBS imprimen formularios?** Si el motor cae de noche, lo que se rompe sin que nadie lo
   pulse son los jobs. (`A33_variant_content_mining`)
3. **Los otros motores**: SmartForms (11) y SAPscript — qué sale por ahí y por qué canal.
4. **Serie histórica de disponibilidad** por destino: una foto no es un monitor.
5. **`TNAPR`/`NAST` al Gold DB**, o decidir explícitamente que la determinación de salida queda
   fuera del modelo.

## RELACIONADO

Agente dueño: `document-output-discovery` · Skill: `sap_log_forensics` ·
Algoritmos: `A60_outbound_channel_availability`, `A62_lazy_generated_object_as_usage_proof`,
`A61_event_dating_without_a_trace` · Incidente: `knowledge/incidents/INC-000016471_*.md` ·
Companion: `companions/document_output_ads_companion.html` ·
`knowledge/domains/Integration/integration_map_complete.md` (flujo 8.5) ·
`knowledge/domains/HR-Workflows/README.md` (ASR, `ZPAWF`)
