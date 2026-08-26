# INC-000016471 — "Create PDF Agreement" falla en la app Internship Agreement: ADS caído

**APERTURA (Track A — diagnóstico). Sesión #105, 2026-08-26.**
Estado: `TRIAGED_ROOT_CAUSE_CLASS_IDENTIFIED` — la CLASE de fallo está determinada por el propio
mensaje de error; cuál de las cuatro causas concretas es, requiere una lectura que no es nuestra.

---

## 0. TRIAJE (paso 0 obligatorio)

**Track A — DIAGNÓSTICO.** La incógnita es *por qué*.

Pero el triaje devuelve una conclusión de **encaminamiento** antes que de causa: esto es un fallo de
**infraestructura (Basis / AS Java)**, no funcional. Ni HCM, ni Recruitment, ni FI. La clasificación
del ticket ("Core Applications, Core HR+, Recruitment") apunta al equipo equivocado, y eso es
exactamente por qué el ticket ha rebotado por cuatro personas en un día mientras corre el plazo del
usuario.

---

## 1. EL TICKET, PARSEADO

| Campo | Valor |
|---|---|
| Ticket | INC-000016471 (SMART / Salesforce, `0nyMI0000007Nnt`) |
| Creado | 2026-08-25 17:32 por Service Desk |
| Asignado a | Laia Caballé, Adil Sefiani (ausente) |
| Usuario | Etienne Wintenberger — `e.wintenberger@unesco.org` |
| Departamento | ADM/DBS/SAA/ALR/AR — Audiovisual Archivist |
| Prioridad | **Critical** |
| Clasificación | Core Applications, **Core HR+, Recruitment** |
| Aplicación | "Internship Agreement" — botón **Create PDF Agreement** |
| Plazo real del usuario | se va de vacaciones el jueves **2026-08-27** |

**Síntoma, en sus palabras (FR):** no consigue crear el PDF de la *convention de stage*. La convención
**ya está validada por HRM y AO**; sólo falta imprimirla para que la firmen candidato y supervisor. Al
pulsar *Create PDF Agreement* sale el error. Ha reiniciado el PC varias veces; mismo problema **desde
esa mañana**. Ya había contactado a Christopher Cruz.

**Cadena de encaminamiento (todo el 26/08):** Caballé 08:29 "in absence of Adil, can anyone help?" →
Sabri 09:51 "I'm looping Narmin" → Allami 13:04 "do you think you can help in the absence of the
team?" → JP Lopez 09:25 UTC **"Unfortunately this time I can not help."**

Ese "no puedo ayudar" era el instinto correcto. Lo que sigue es el *por qué* y el *a quién*, que es
lo que faltaba para que el ticket dejara de rebotar.

---

## 2. EL ERROR, LEÍDO LITERALMENTE

Captura adjunta al ticket (`image001.png`):

```
500 Internal Server Error
ADS: SOAP Runtime Exception: CSoapExceptionTransport :(100101)
Server time:
```

Descomponiendo, término a término:

- **ADS** = *Adobe Document Services*. Es el motor que convierte un formulario SAP Interactive Form
  (Adobe/XFA) en un PDF. **No corre en la pila ABAP**: es una aplicación Java, en un AS Java aparte.
- **SOAP Runtime Exception / `CSoapExceptionTransport`** = el cliente SOAP del lado ABAP **no pudo
  completar la llamada HTTP**. *Transport* significa que la petición no obtuvo una respuesta HTTP
  válida — no que la respuesta trajera un error de negocio.
- **`Server time:` vacío** lo corrobora: no volvió cuerpo de respuesta con el que rellenarlo.

**Por tanto: no es el formulario, no son los datos, no es el PC del usuario.** Reiniciar el PC no
puede arreglarlo — que es exactamente lo que el usuario observó y reportó tres veces.

---

## 3. EL CANAL — MEDIDO

Destino RFC `ADS` en P01. Fuente: Gold DB, tabla `rfcdes` (239 destinos, provenance P01).
⚠️ Es una **instantánea de configuración**, no una lectura de hoy — ver §8.

```
RFCDEST  ADS
RFCTYPE  G          -> conexión HTTP a un servidor EXTERNO
RFCOPTIONS:
  H = hq-sap-sbp.hq.int.unesco.org        <- host
  I = 50300                               <- puerto
  N = /AdobeDocumentServices/Config?style=rpc   <- endpoint SOAP
  D = ADSUSER                             <- usuario
  v = %_PWD                               <- contraseña almacenada en el destino
  Q = B                                   <- autenticación BASIC
  s = N                                   <- SIN SSL: HTTP plano
  T = N                                   <- traza DESACTIVADA
```

Lo que dice esta línea:

1. **ADS vive en otro host que el ABAP productivo**: `hq-sap-sbp`, no `hq-sap-p01`. Es un sistema Java
   distinto, con su propio ciclo de vida, sus propios reinicios y su propio equipo.
2. **Puerto 50300** = puerto HTTP estándar de AS Java para el número de instancia **03** (`5<NN>00`).
3. **Autenticación básica con usuario de servicio `ADSUSER`**, contraseña guardada en el destino.
4. **`s=N`: HTTP plano, sin SSL.** *Hallazgo colateral*: las credenciales de un usuario de servicio
   cruzan la red sin cifrar en cada render de PDF. No es la causa de este incidente; es deuda que
   este incidente destapa.
5. **`T=N`: la traza está apagada.** No habrá traza del destino que mirar; el diagnóstico tiene que
   venir del lado Java.

---

## 4. LAS CUATRO COSAS QUE PRODUCEN EXACTAMENTE ESTE ERROR

Ordenadas por probabilidad, no por opinión: `CSoapExceptionTransport` acota el conjunto a fallos de
transporte, y en un ADS de destino tipo G sólo hay cuatro.

| # | Causa | Cómo se ve | Quién la mira |
|---|---|---|---|
| 1 | **AS Java / la aplicación ADS en `hq-sap-sbp` está caída o se reinició** | conexión rechazada / sin respuesta | Basis + dueño del Java |
| 2 | **`ADSUSER` bloqueado o con contraseña caducada** en el UME de Java | HTTP 401, que el cliente ABAP envuelve como excepción de transporte | Basis (UME) |
| 3 | **Ruta de red a `hq-sap-sbp:50300` cortada** (firewall, DNS, host movido) | timeout | Red / Basis |
| 4 | **Java sin recursos** — el proceso de render colgado | timeout largo | Basis |

La **#2 es la reincidente clásica**: `ADSUSER` es un usuario de servicio cuya contraseña está
almacenada del lado ABAP; cualquier política de caducidad del UME o un bloqueo por intentos fallidos
produce un 401 sin que nadie haya tocado nada. Encaja con "funcionaba ayer, falla desde esta mañana".

### La prueba que separa las cuatro es un clic

- **SM59 → destino `ADS` → Connection Test.** Sólo lee, no cambia nada. HTTP 200 → ADS está vivo,
  buscar en otro sitio. **401** → es `ADSUSER`. **Timeout / rechazo** → es host o red.
- **La prueba definitiva es funcional: transacción `SFP` → *Utilities* → *Test ADS Connection***
  (reports `FP_TEST_00` / `FP_PDF_TEST_00`). Renderiza un PDF trivial y devuelve **el texto de error
  real de ADS** en vez del SOAP envuelto. Si eso falla, queda probado que el problema no tiene nada
  que ver con la convención de prácticas ni con la app de HR.

Ninguna de las cuatro es diagnosticable ni arreglable desde el lado ABAP, y ninguna es funcional.

---

## 5. RADIO DE ALCANCE — lo que NO está en el ticket y pesa más que lo que sí

**Si ADS está caído, TODOS los formularios Adobe del paisaje están caídos a la vez**, no sólo esta
convención de prácticas. En esta instalación eso incluye, como mínimo:

- **La familia de formularios HR ASR.** `knowledge/domains/HR-Workflows/README.md` registra el *ASR
  Framework — Standard SAP Adobe Service Request HR forms, redefined* (`CL_HCMFAB_*`,
  `CL_HRASR00GEN_SERVICE`). Es decir: toda la familia de formularios de acciones de personal.
- **Potencialmente la impresión de medios de pago.** `RFFORI00` es el único programa de nuestro corpus
  extraído que lleva llamadas a formularios Adobe.

**Consecuencia operativa:** una prioridad *Critical* sobre una convención de prácticas probablemente
está **infravalorando** el incidente. La primera pregunta de vuelta al Service Desk no es "¿qué
pulsaste?" sino:

> **¿Hay alguien más desde esta mañana que no consiga generar un PDF desde SAP?**

Un solo ticket parecido convierte esto de "un usuario con un problema" en "un canal de salida caído",
y eso cambia la prioridad, el equipo y el tiempo de respuesta.

⚠️ **Límite de la medida:** nuestro corpus de código extraído es PARCIAL (812 + 335 ficheros, no el
repositorio entero). **1 acierto es un suelo, no un recuento.** No sabemos cuántos objetos de esta
instalación renderizan por ADS. Ese es un hueco real, ver §7.

---

## 6. QUIÉN LO POSEE

**Basis / SAP Tech Administrators** (`sap.admin@unesco.org`, ya está en copia desde el principio) más
quien opere la máquina AS Java `hq-sap-sbp`.

No HCM. No Recruitment. No FI. No este proyecto.

Sobre el plazo del usuario (se va el jueves 27): **sin ADS no hay PDF**. No existe una vía ABAP
alternativa para producir ese documento — el render *es* ADS. Si ADS no vuelve a tiempo, la salida es
del lado del proceso de HR (reemitir la convención por otro canal), y esa decisión es del dueño de la
aplicación Internship Agreement, no nuestra. Decirlo pronto y claro le vale más al usuario que una
espera.

---

## 7. ESTADO DEL BRAIN — esto es un PUNTO CIEGO, y ese es el hallazgo sobre nosotros

Búsqueda en todos los stores (`graph_queries.py search`):

| Término | claims | rules | incidents | annotations | code | domains |
|---|---:|---:|---:|---:|---:|---:|
| `Adobe` | 0 | 0 | 0 | 0 | 0 | 1 (Output) |
| `internship` | 0 | 0 | 0 | 0 | 0 | 0 |
| `ADSUSER` | 0 | 0 | 0 | 0 | 0 | 0 |
| `SFP` | 0 | 0 | 0 | 0 | 0 | 0 |

Todo lo que teníamos sobre ADS eran **dos líneas**:

1. `knowledge/domains/Integration/integration_map_complete.md` flujo 8.5 — *"SAP P01 → ADS (Adobe),
   HTTP, destino `ADS`, Adobe Document Services — PDF form generation, [VERIFIED] Standard SAP
   component"*, con volumen `?`.
2. `brain_v2/interface_inventory.json` — canal `RFC_DESTINATION`, artefacto `ADS`, tipo G, saliente,
   naturaleza **`NO_MEDIBLE`**: *"un destino SALIENTE no registra en nuestro log qué hace en el
   sistema destino. Se mediría en el otro extremo. Ausencia de dato, no de riesgo."*

Esa etiqueta era honesta y sigue siéndolo. Pero lo que este incidente demuestra es que **teníamos un
canal de salida entero — todos los PDF que la institución produce desde SAP — con una línea de
inventario, sin dueño declarado, sin monitor, y sin radio de alcance medido.** El dominio `Output`
está marcado *stranded* en la columna vertebral de procesos (ni en un flujo ni transversal a uno).
Esto es qué aspecto tiene un dominio *stranded* el día que se rompe.

---

## 8. LO QUE NO PUDE HACER EN ESTA SESIÓN (declarado, no omitido)

1. **La sonda en vivo contra P01 fue BLOQUEADA** por el modo de permisos de la sesión. Los valores del
   destino en §3 vienen de la instantánea del Gold DB — provenance P01, pero **no es una lectura de
   hoy**, y `rfcdes` no tiene fila en `_gold_sync_log`, así que su fecha de extracción es
   **desconocida**. Reverificar con:
   ```
   python Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py
   ```
   (creado en esta sesión, sólo lectura, `RFC_READ_TABLE` sobre `RFCDES` / `RFCDOC`).
2. **Falta una captura.** El ticket referencia `image003.png` además de la del 500; en el .eml sólo
   viajó `image001.png`. Lo que mostrara la segunda está sin leer.
3. **No sé qué es exactamente la app "Internship Agreement"** — si es WebDynpro ABAP, un Fiori, o un
   satélite que llama a SAP. Sólo sé, por el error, que su render de PDF pasa por ADS de P01. En el
   corpus extraído existe `YCL_HRWF_INTERN_GOS` (`extracted_code/HCM/YHR_PA_WF/`), clase de Generic
   Object Services de prácticas, pero **no contiene lógica de PDF ni llamadas a ADS** — comprobado. No
   es el sitio.

---

## 9. ACCIONES

| # | Acción | Quién | Estado |
|---|---|---|---|
| A1 | `SM59` → destino `ADS` → *Connection Test* en P01. Separa las cuatro causas en un clic | Basis / SAP Tech Admin | PENDIENTE |
| A2 | `SFP` → *Test ADS Connection* (`FP_PDF_TEST_00`) — devuelve el error REAL de ADS | Basis / SAP Tech Admin | PENDIENTE |
| A3 | Comprobar `ADSUSER` en el UME de Java: bloqueado / contraseña caducada | Basis | PENDIENTE |
| A4 | Verificar que la aplicación `AdobeDocumentServices` está arrancada en NWA en `hq-sap-sbp` | dueño del AS Java | PENDIENTE |
| A5 | **Preguntar al Service Desk si hay más tickets de "no se genera el PDF" desde el 25/08** — es lo que reclasifica el incidente | Service Desk | PENDIENTE |
| A6 | Reclasificar el ticket: de *Core HR+ / Recruitment* a *Basis / Infraestructura* | Service Desk | PENDIENTE |
| A7 | Decir al usuario, hoy, que sin ADS no hay PDF y que la salida para su plazo del 27 es de proceso, no técnica | quien lleve el ticket | PENDIENTE |
| A8 | **NUESTRO:** medir el radio real de ADS — cuántos objetos de P01 renderizan por Adobe. `TNAPR`/`FPCONTEXT`, o census de llamadas `FP_JOB_OPEN`/`FP_FUNCTION_MODULE_NAME` sobre el repositorio completo, no sobre el corpus parcial | este proyecto | BACKLOG |
| A9 | **NUESTRO:** dar dueño y monitor al canal ADS en el inventario de interfaces; `NO_MEDIBLE` es correcto para el tráfico, pero la DISPONIBILIDAD sí se mide desde nuestro lado (test de conexión periódico) | este proyecto | BACKLOG |
| A10 | Registrar la deuda: `s=N` en el destino ADS — basic auth de usuario de servicio sobre HTTP plano | este proyecto | BACKLOG |

---

## 10. LECCIONES

1. **`CSoapExceptionTransport` es un veredicto, no un síntoma.** *Transport* significa que no hubo
   respuesta HTTP. Eso descarta de golpe el formulario, los datos y el puesto de trabajo — y ahorra
   toda la rama de diagnóstico funcional. Leer el error literalmente, término a término, hizo más que
   cualquier búsqueda.
2. **Un usuario que dice "he reiniciado el PC tres veces y sigue igual" ya te ha dado la mitad del
   diagnóstico.** Está descartando el cliente por ti. Escucharlo es más barato que repetirlo.
3. **Un ticket clasificado por la aplicación donde el usuario estaba, no por la capa que falló,
   rebota.** Este fue por cuatro personas en un día, con prioridad Critical, sin que nadie pudiera
   hacer nada — porque todos los destinatarios eran funcionales y el fallo era de plataforma.
4. **El alcance de un fallo de plataforma nunca es el que trae el ticket.** El ticket trae *un*
   usuario porque *un* usuario escribió. La pregunta que reclasifica el incidente ("¿le pasa a alguien
   más?") cuesta un correo y no la hizo nadie en cuatro saltos.
5. **`NO_MEDIBLE` para el tráfico no es `NO_MEDIBLE` para la disponibilidad.** Marcamos ADS como no
   medible porque es saliente y no vemos qué pasa al otro lado. Cierto — y sin embargo, "¿responde?"
   se contesta desde nuestro lado con un test de conexión. Confundir las dos preguntas dejó un canal
   entero sin vigilancia.

---

## 11. RELACIONADOS

- `knowledge/domains/Integration/integration_map_complete.md` — flujo 8.5 (ADS)
- `knowledge/domains/HR-Workflows/README.md` — ASR Framework (formularios HR Adobe)
- `brain_v2/interface_inventory.json` — canal `RFC_DESTINATION` / `ADS`, `NO_MEDIBLE`
- Gold DB `rfcdes` (239 filas) — configuración del destino
- `Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py` — sonda creada aquí
- Corpus: `extracted_code/FI/SAPFPAYM/RFFORI00.abap` (único con llamadas a formularios Adobe),
  `extracted_code/HCM/YHR_PA_WF/YCL_HRWF_INTERN_GOS.abap` (prácticas, SIN lógica de PDF — descartado)
