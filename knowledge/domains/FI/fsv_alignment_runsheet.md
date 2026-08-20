# FSV — hoja de lanzamiento para SCU0 / SCMP (P01 → D01 y V01)

**Medido 2026-08-20 (s102), lectura en vivo.** Referencia = **P01**. Chart of accounts **UNES**.
Instrumento de medición y verificación: `Zagentexecution/quality_checks/fsv_alignment_check.py`.

---

## 0. Por qué SCU0/SCMP y no un transporte desde P01

| Sistema | `T000.CCCATEGORY` | `CCCORACTIV` | Lectura |
|---|---|---|---|
| **P01** 350 | `P` Producción | **`2` = no se permiten cambios** · `CCNOCLIIND='3'` | **cerrado**: no se puede grabar customizing ni orden |
| D01 350 | `C` Desarrollo | `1` grabación automática | abierto |
| V01 350 | `T` Test | `1` grabación automática | abierto |

No hay **ningún** FM remote-enabled para mantener la FSV (comprobado en `TFDIR WHERE FMODE='R'`
contra FSV / BILANZ / ERGSL / FIN_STATEMENT). Y `FAGL_011*` son tablas **estándar**, así que el
`INSERT` plano está prohibido. **SCU0 lee P01 y escribe en el destino**, que es donde el cliente
está abierto: no hay violación de paisaje.

Dominio de transporte único: **`DOMAIN_P01`** (D01, V01, P01, TS3).

---

## 1. Destino RFC a usar

| Desde | Destino | Host | Mandante | Usuario | Nota |
|---|---|---|---|---|---|
| **D01** | **`P01`** | `172.16.4.100` sysnr 00 | **350** | *(vacío → usuario conectado)* | ✅ **el recomendado** |
| D01 | `P01_N` | `172.16.4.100` | 350 | *(vacío)* | alternativa idéntica |
| D01 | `TRUSTED@P01_0020309457` | `HQ-SAP-P01.hq.int.unesco.org` | *(hereda)* | *(trusted, SNC)* | si el anterior pide clave |
| **V01** | **`P01MDT350`** | `hq-sap-p01` | **350** | `ALEREMOTE` | ✅ **el recomendado en V01** |
| V01 | `TRUSTED@P01_0020309457` | `HQ-SAP-P01.HQ.INT.UNESCO.ORG` | *(hereda)* | *(trusted, SNC)* | alternativa |

> ⚠️ **En V01 el destino llamado `P01` está VACÍO** (sin host ni mandante): no sirve, aunque
> aparezca en la lista. Usar `P01MDT350`.
> `FINBTR@P01CLNT350` apunta a **otro host** (`10.101.23.115` desde D01, `hq-sap-v01` desde V01):
> no es el P01 que usamos. No usarlo.

---

## 2. SCU0 — selección manual: qué teclear

En *New Comparison Based On* → **Manual selection** → **Create** → popup *Selection by: Manual Input*.

⛔ **NO uses el objeto `F011`.** Existe (tipo `L`, objeto lógico) pero solo contiene
`T011`, `T011T` y `RFDT` — el almacenamiento **clásico**. El contenido real de esta instalación
vive en las tablas `FAGL_011*`, y `OBJSL` confirma que **ningún objeto de customizing las cubre**.
Comparar por `F011` da un diff casi vacío y una falsa sensación de alineación.

**Teclear las tablas, con `Typ` = tabla** (el botón F4 de la columna da la lista):

| # | Object name | Por qué | Huecos D01 | Huecos V01 |
|---|---|---|---|---|
| 1 | **`FAGL_011ZC`** | asignación cuenta → posición. **El que resuelve el ticket** | **195** faltan · 11 difieren | **131** faltan · 2 difieren |
| 2 | **`FAGL_011PC`** | jerarquía de posiciones (`PARENT`/`CHILD`) | **287** faltan · 38 difieren | **278** faltan · 47 difieren |
| 3 | **`FAGL_011QT`** | textos de posición | 179 faltan · 148 difieren | 96 faltan · 140 difieren |
| 4 | **`FAGL_011SC`** | sets asociados a posiciones | 51 faltan · **229 difieren** | 22 faltan · **213 difieren** |
| 5 | `T011` | cabecera de versiones | 0 · 0 ✅ | 0 · 0 ✅ |
| 6 | `T011T` | textos de versión | 0 · 0 ✅ | 0 · 0 ✅ |
| 7 | `FAGL_011VC` | contrapartidas | 0 · 0 ✅ | 0 · 0 ✅ |
| 8 | `FAGL_011FC` | áreas funcionales | vacía en P01 | vacía en P01 |

**Orden de ejecución: 2 → 3 → 1 → 4.** La jerarquía y los textos de posición primero: una
asignación de cuenta apunta a un `ERGSL` que tiene que existir antes.

Las cuatro últimas ya están alineadas — inclúyelas solo si quieres la evidencia de que lo están.

---

## 3. SCMP — comparación tabla a tabla

`SCMP` pide **una** tabla/vista y el destino RFC. Es la vía si prefieres ir de una en una o si
SCU0 devuelve demasiado ruido.

```
Transacción SCMP
  Table/View        : FAGL_011ZC        (luego FAGL_011PC, FAGL_011QT, FAGL_011SC)
  RFC Destination   : P01               (desde D01)   /   P01MDT350   (desde V01)
  Restricción útil  : KTOPL = UNES  ·  VERSN = FS10
```

---

## 4. Acotar el alcance antes de lanzarlo

La deriva de `FAGL_011ZC` se reparte casi mitad y mitad entre dos versiones:

| | FS10 | FS11 |
|---|---|---|
| faltan en D01 | 111 | 84 |
| faltan en V01 | 65 | 66 |

**Si `FS11` no está viva, el trabajo se reduce a la mitad.** Hay 4 versiones (`FS01`, `FS02`,
`FS10`, `FS11`) y no está determinado cuáles se usan. Determinarlo **antes** de lanzar la
alineación.

### La fila concreta del ticket
```
VERSN FS10 · ERGSL 1.1.1.1 "Cash with Banks" · KTOPL UNES · VONKT 0004041015 · BISKT 0004041019
```
Existe **solo en P01**. En D01 el último intervalo de esa posición llega a `0004041013`; en V01, a
`0004041014`. Por eso las cuentas nuevas no quedan mapeadas fuera de producción aunque la cuenta
sí se haya copiado. **Un rango no cubre nada si la fila del rango no existe.**

---

## 5. Después: verificar con el dato, no con el log del ajuste

```bash
python Zagentexecution/quality_checks/fsv_alignment_check.py --systems D01,V01
```
Exit 0 = alineado. Y el cruce de la otra mitad del problema:
```bash
python Zagentexecution/quality_checks/ob09_vs_variant_check.py --systems P01,D01,V01
```

---

## 6. Lo que SCU0/SCMP NO arreglan

- **Las variantes de F.05.** `VARID.TRANSPORT='F'`: no se transportan y no son customizing
  comparable. `UNES_DEPOSIT` tiene **tres contenidos distintos** en los tres sistemas (P01: 16
  valores sueltos; D01: rango 4041011-13; V01: rangos 4041011-14 y 5091010-12). Se corrigen a mano
  en cada sistema.
- **`T030H` / OB09.** Es customizing y sí se puede comparar, pero no está en esta hoja: usar
  `ob09_vs_variant_check.py` para el alcance.
