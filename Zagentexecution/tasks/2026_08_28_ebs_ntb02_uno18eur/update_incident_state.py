# -*- coding: utf-8 -*-
"""Actualiza el estado de INC-000013624: el lado SAP quedo COMPLETO y la causa restante
esta aguas arriba. Verificado leyendo el destino, no la pantalla."""
import json, io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BLOQUE = """
## 8. ACTUALIZACIÓN 2026-08-28 tarde — el lado SAP está COMPLETO; la causa restante está aguas arriba

**La fila de `T028B` ya está grabada y transportada.** Verificado leyendo el destino en los dos
sistemas, no la pantalla:

```
D01  SP0000000MX7 | 18747647 | TR_TRNF | NTB02-EUR1 | UNES     ✅
P01  SP0000000MX7 | 18747647 | TR_TRNF | NTB02-EUR1 | UNES     ✅
```

Con eso, **las tres piezas de configuración que dependían del número de cuenta están correctas**:
`T012K` (BANKN + BNKN2), `TIBAN` (IBAN nuevo desde 17.08) y `T028B`. **No queda nada que hacer en
SAP.**

### Y sin embargo no entra nada. Lo medido:

| Comprobación | Resultado |
|---|---|
| ¿Algún extracto con `UNO18EUR`, alguna vez? | **NINGUNO** — cero filas en `FEBKO` en toda la historia |
| Último de NTB02/EUR01 | estadillo **2997, 14.08.2026**, importado el 15.08 |
| ¿Entra algo de otros bancos? | sí — **102 · 109 · 108** extractos los días 25, 26 y 27.08 |
| ¿NTB02 en ese rango? | **0** |
| Ficheros que mencionen NTB02 en el directorio de ERRORES de Coupa | **0** |

**Conclusión: el fichero no llega.** No es que SAP lo rechace — no hay nada que rechazar. Northern
Trust / Coupa no están emitiendo el extracto de la cuenta UNO18.

### Por qué FF67 no ofrece la cuenta nueva — y no es un defecto

El usuario reporta que al crear un extracto manual la cuenta nueva no aparece en la lista.
**La lista de FF67 no se deriva de la configuración: contiene el historial de extractos recibidos.**

La prueba está en la propia captura del usuario: muestra el par `SP0000000MX7` + `UNO10`, y **esa
combinación no existe en `T012K`** — NTB01 tiene hoy clave de banco `SP0000000MXL`. Lo que sí
existe es en `FEBKO`:

```
SP0000000MX7   UNO10USD    n=10     último 05.03.2015
SP0000000MX7   UNO11USD    n=10     último 05.03.2015
SP0000000MX7   UNO12EUR    n=2233   último 14.08.2026
```

Coincide par por par. Una lista derivada de configuración **no puede** producir una fila de 2015 de
una cuenta que desde entonces cambió de clave de banco.

> ⚠️ **Lo que está probado y lo que no.** Probado: la lista **no** sale (solo) de `T012K`, porque
> contiene un par ausente de `T012K`. Fuertemente respaldado: coincide exactamente con
> `FEBKO.ABSND`. **No leído:** el fuente de `SAPMF40K` — el module pool devuelve 25 líneas sin
> includes por `RPY_PROGRAM_READ`, así que no se afirma de qué tabla lee exactamente.

**Consecuencia práctica:** `UNO18EUR` aparecerá en FF67 **cuando llegue su primer extracto**, no
antes. Que hoy no esté es el síntoma, no la causa.

### Lo que hay que hacer ahora — y ya no es de DBS

1. **Reclamar a Northern Trust / Coupa** que emitan el extracto de la cuenta UNO18. El SSI del
   25.06 (`Consolidation UNO18`, IBAN GB42…647) prueba que la cuenta existe; no que el extracto se
   esté enviando.
2. **Confirmar con qué identidad lo van a emitir.** SAP espera `UNO18EUR` en el `:25:` — es lo que
   tiene `T012K.BNKN2`. Si el banco emite otra cosa (por ejemplo el número `18747647`), hay que
   saberlo: la resolución se hace por `BANKN` **o** `BNKN2`, y ambas están puestas, pero conviene
   confirmarlo antes de que llegue el primero.
3. **Cuando entre el primero, borrar la fila vieja** `11939389` de `T028B`. Nunca antes.
4. Mientras tanto, si Tesorería necesita el saldo, se puede **teclear el extracto en FF67** — la
   configuración lo soporta desde ahora.

**Estado: SAP COMPLETO — ESCALADO AGUAS ARRIBA.**
"""

p = "knowledge/incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md"
s = io.open(p, encoding="utf-8").read()
anc = "\n## Registro\n"
if "ACTUALIZACIÓN 2026-08-28 tarde" in s:
    print("doc: ya estaba")
elif anc in s:
    io.open(p, "w", encoding="utf-8").write(s.replace(anc, "\n" + BLOQUE.strip() + "\n\n---\n" + anc, 1))
    print("doc: actualizado")
else:
    io.open(p, "a", encoding="utf-8").write("\n" + BLOQUE)
    print("doc: anadido al final")

# encabezado del estado
s = io.open(p, encoding="utf-8").read()
s = s.replace("**Estado:** CAUSA RAÍZ CONFIRMADA — acción de configuración pendiente",
              "**Estado:** SAP COMPLETO (T012K + TIBAN + T028B verificados en P01) — "
              "ESCALADO AGUAS ARRIBA: el fichero no llega")
io.open(p, "w", encoding="utf-8").write(s)

# registro de primera clase
P = "brain_v2/incidents/incidents.json"
inc = json.load(io.open(P, encoding="utf-8"))
for r in inc:
    if r.get("id") == "INC-000013624":
        r["status"] = "SAP_SIDE_COMPLETE_ESCALATED_UPSTREAM"
        r["resolution_state"] = (
            "2026-08-28 tarde: la fila T028B (SP0000000MX7 / 18747647 / TR_TRNF / NTB02-EUR1) esta "
            "GRABADA y transportada -- verificado leyendo D01 y P01, no la pantalla. Con T012K y "
            "TIBAN ya correctos, las TRES piezas que dependen del numero de cuenta estan puestas y "
            "no queda nada que hacer en SAP. Y aun asi no entra nada: JAMAS ha llegado un extracto "
            "con UNO18EUR (cero filas en FEBKO en toda la historia), NTB02 sigue sin recibir desde "
            "el 14.08 mientras los demas bancos entraron 102/109/108 extractos los dias 25/26/27, y "
            "el directorio de ERRORES de Coupa no tiene ni un fichero que mencione NTB02. El fichero "
            "NO LLEGA: no es que SAP lo rechace. Escalado a Northern Trust / Coupa."
        )
        r["ff67_no_es_defecto"] = (
            "El usuario reporta que la cuenta nueva no aparece al crear un extracto manual. La lista "
            "de FF67 NO se deriva de la configuracion: contiene el HISTORIAL de extractos recibidos. "
            "Prueba: la captura del usuario muestra el par SP0000000MX7 + UNO10, que NO existe en "
            "T012K (NTB01 usa hoy SP0000000MXL) pero SI en FEBKO.ABSND con 10 extractos cuyo ultimo "
            "es del 05.03.2015. Coincide par por par. Una lista derivada de configuracion no puede "
            "producir esa fila. UNO18EUR aparecera cuando llegue su primer extracto, no antes. NO "
            "LEIDO: el fuente de SAPMF40K (module pool, 25 lineas sin includes por RPY_PROGRAM_READ), "
            "asi que no se afirma de que tabla lee exactamente."
        )
json.dump(inc, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("incidents.json: estado actualizado")
