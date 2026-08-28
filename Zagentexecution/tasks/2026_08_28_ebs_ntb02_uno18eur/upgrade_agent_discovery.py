# -*- coding: utf-8 -*-
"""Lo que hay que cambiar en el agente para que DESCUBRA oportunidades y no solo informe.

Sale de lo medido en s108, no de una opinion: ningun minero por si solo encontro una sola
oportunidad. Todas salieron de CRUZAR dos o mas, y las formas del cruce se repiten.
"""
import io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BLOQUE = """
## Cómo se DESCUBRE una oportunidad (s108 — sale de lo medido, no de una opinión)

**Ningún minero encontró por sí solo una sola oportunidad.** Cada uno contesta una pregunta;
las oportunidades viven en el **cruce**. Medido: «11 cuentas tienen el modelo montado y no lo
usan» necesitó cruzar el cableado (`house_bank_ebs_wiring_check`) × el canal
(`bank_statement_channel_census`) × el comportamiento (`bank_account_behaviour_signature`) × los
formatos (`ebs_format_consolidation`). Ninguno de los cuatro lo dice solo.

**Tu trabajo no es correr los seis. Es cruzarlos.** Si tu salida se puede obtener ejecutando un
solo instrumento, sobras.

### Las cinco FORMAS de oportunidad que funcionaron — pásalas todas

Son genéricas: sirven para cualquier objeto de este dominio y para otros dominios.

| Forma | Pregunta | Lo que encontró en s108 |
|---|---|---|
| **① Existe y no se usa** | ¿qué está configurado y no se ejercita? | 11 cuentas con modelo de extracto asignado y sin usar → 6 reales |
| **② Se mueve sin su contraparte** | ¿qué ocurre sin el registro que debería acompañarlo? | 3 mandatos mueven saldo **sin ni un extracto** |
| **③ Entra y no produce nada** | ¿qué se procesa sin efecto aguas abajo? | 5 cuentas, **2.321 extractos**, cero movimiento contable |
| **④ Único donde otros comparten** | ¿qué se sostiene para uno solo? | 5 formatos para **una** cuenta cada uno; 73 reglas para 6 cuentas |
| **⑤ Dos fuentes discrepan** | ¿dónde el comportamiento contradice la etiqueta? | `receiving_accounts` (A44) vs `OPERATIVA_COBRO`; naturaleza por texto vs por conducta |

**La ⑤ es la más productiva y la más incómoda**: cuando dos medidas del mismo objeto no
coinciden, **una de las dos está mal** — y averiguar cuál es el hallazgo, no el desacuerdo.

### Antes de publicar cualquier cifra — los tres cortes que salvaron s108 cinco veces

1. **DENOMINADOR.** ¿Contra qué población? Las cuentas **cerradas** se marcan en el TEXTO
   (`T012T-TEXT1` empieza por `CLOSED`: 237 de 411). Sin ese corte, 2 de los 4 primeros
   «cables rotos» eran cuentas cerradas hace años.
2. **APLICABILIDAD.** ¿La regla aplica a esa población? El extracto **manual** no necesita
   `T028B`: exigírselo publicaba un defecto inexistente. Sólo 131 de 143 son electrónicas.
3. **MOVIMIENTO.** ¿El objeto hace algo? `CBE01-ETB02` tenía el modelo montado y sin usar — y
   está **durmiente**: cero extractos, cero pagos, cero movimiento. No es oportunidad.

Y el corte transversal: **siempre por SOCIEDAD**. `CBE01-ETB02` recibe 543 extractos al año en
ICBA y cero en UNES. En proporción, UIL tiene el 40 % de anomalías y UNES el 10 % — el agregado
lo invierte.

### Dimensiona antes de proponer, aunque te quite la razón

En s108 «7 cuentas se teclean a mano» parecía un ahorro de trabajo. Medido: **1.712 líneas en
dos años**, cuando **una sola** cuenta electrónica procesa 11.669. **El argumento del ahorro de
tecleo era falso** y decirlo habría sido vender humo. La oportunidad real era otra —esas líneas
no compensan solas, y son cuentas que pagan millones sin corroboración bancaria— y solo apareció
al medir.

**Regla:** una oportunidad sin tamaño medido no se propone. Y si el tamaño la desmonta, se dice.

### Y declara siempre el límite de lo que puedes ver

Tener el modelo asignado **no prueba** que el fichero pueda llegar: la restricción puede estar
aguas arriba, en el banco. Esa frase al lado de la propuesta es lo que la convierte en accionable
en vez de en una idea bonita — separa «esto lo arreglo yo» de «esto hay que reclamarlo».
"""

p = ".claude/agents/bank-process-discovery.md"
s = io.open(p, encoding="utf-8").read()
if "Cómo se DESCUBRE una oportunidad" in s:
    print("agente: ya estaba")
else:
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + "\n\n" + BLOQUE.strip() + "\n")
    print("agente: bloque de descubrimiento anadido")

# el skill de EBS tambien tiene que llevar los tres cortes: es lo que se lee ANTES de medir
p2 = ".claude/skills/sap_bank_statement_recon/SKILL.md"
s2 = io.open(p2, encoding="utf-8").read()
CORTES = """
## Before publishing any number over the account estate — three cuts, five times each in s108

1. **DENOMINATOR** — closed accounts are marked **in the text** (`T012T-TEXT1` starts with
   `CLOSED`: **237 of 411** in UNES). There is no status field. Without this cut, 2 of the first
   4 "broken wiring" findings were accounts closed years ago.
2. **APPLICABILITY** — does the rule even apply? A **manual** statement does not need `T028B`;
   only **131 of 143** accounts that receive statements are electronic. Demanding it publishes a
   defect that does not exist.
3. **MOVEMENT** — does the object actually do anything? `CBE01-ETB02` had the model wired and
   unused, and is **dormant**: zero statements, zero payments, zero movement. Not an opportunity.

Cross-cutting: **always split by company code.** `CBE01-ETB02` gets 543 statements a year in
ICBA and zero in UNES. By proportion UIL has 40 % anomalies and UNES 10 % — the aggregate
inverts it.

**And size an opportunity before proposing it, even when that kills it.** "7 accounts typed by
hand" looked like a clerical saving; measured, it is **1,712 lines in two years** against
**11,669** for a single electronic account. The saving argument was false. The real opportunity
was elsewhere — those lines never auto-clear, and the accounts pay millions with no bank
corroboration.

"""
if "three cuts, five times each" in s2:
    print("skill: ya estaba")
else:
    anc = "## E2E Bank Statement Chain"
    if anc in s2:
        io.open(p2, "w", encoding="utf-8").write(s2.replace(anc, CORTES.strip() + "\n\n" + anc, 1))
        print("skill: los tres cortes anadidos")
    else:
        print("skill: SIN ANCLA")
