# -*- coding: utf-8 -*-
"""Propaga a TODOS los sitios que hablan de FF67 el hecho de que su lista de cuentas es
HISTORIAL, no configuracion — y por tanto una cuenta nueva no aparece hasta su primer extracto.

Es la regla de referencias cruzadas: no basta con escribirlo donde lo descubri. El momento en
que alguien necesita saberlo es DESPUES de un alta o un cambio de numero, mirando FF67 y sin
ver su cuenta. Ahi es donde tiene que estar.
"""
import io, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MD = """
> ⚠️ **Una cuenta nueva NO aparece en FF67 hasta que llega su primer extracto — y eso no es un
> defecto.** La lista de cuentas de FF67 es **historial de extractos recibidos**, no configuración.
> Probado el 2026-08-28: ofrece el par `(SP0000000MX7, UNO10)`, que **no existe en `T012K`** —NTB01
> usa hoy `SP0000000MXL`— pero sí en `FEBKO.ABSND`, con 10 extractos cuyo último es del
> **05.03.2015**. Una lista derivada de configuración no puede producir eso.
> **Ante «la cuenta nueva no está en FF67»: no revises la ficha del banco, comprueba si ha llegado
> algún extracto.** (claim 639 · INC-000013624)
"""

HTML = """<div class="card">
  <h3 style="color:var(--orange)">&#9888; Una cuenta nueva NO aparece en FF67 hasta su primer extracto (s108)</h3>
  <p style="margin-bottom:12px">La lista de cuentas de FF67 es <b>historial de extractos recibidos</b>, no configuraci&oacute;n.
  Probado el 2026-08-28: ofrece el par <code>(SP0000000MX7, UNO10)</code>, que <b>no existe en <code>T012K</code></b>
  &mdash;NTB01 usa hoy <code>SP0000000MXL</code>&mdash; pero s&iacute; en <code>FEBKO.ABSND</code>, con 10 extractos cuyo
  &uacute;ltimo es del <b>05.03.2015</b>. Una lista derivada de configuraci&oacute;n no puede producir una fila de 2015 de una
  cuenta que despu&eacute;s cambi&oacute; de clave de banco.</p>
  <p><b>Consecuencia operativa:</b> tras un alta o un cambio de n&uacute;mero de cuenta, la cuenta <b>no estar&aacute;</b> en FF67
  hasta que se procese su primer extracto. <b>Eso no es un defecto y no significa que la configuraci&oacute;n est&eacute; mal.</b>
  Ante un usuario que dice &laquo;la cuenta nueva no est&aacute; en FF67&raquo;: no revisar la ficha del banco &mdash; comprobar
  si ha llegado alg&uacute;n extracto. Caso: INC-000013624, donde la configuraci&oacute;n estaba completa y verificada y el
  usuario segu&iacute;a reportando que el cambio no funcionaba.</p>
</div>

"""

def md(path, ancla, texto=MD, antes=True):
    if not os.path.exists(path):
        return "NO EXISTE"
    s = io.open(path, encoding="utf-8").read()
    if "no aparece en FF67 hasta" in s or "NO aparece en FF67" in s:
        return "ya estaba"
    if ancla not in s:
        return "SIN ANCLA (%s)" % ancla[:40]
    s = s.replace(ancla, (texto.strip() + "\n\n" + ancla) if antes else (ancla + "\n" + texto.strip()), 1)
    io.open(path, "w", encoding="utf-8").write(s)
    return "OK"

R = {}

# 1. procedimiento de banco casa — el momento exacto en que hace falta
R["house_bank_configuration.md"] = md(
    "knowledge/domains/Treasury/house_bank_configuration.md",
    "### La puerta de cierre — no se declara terminado sin esto")

# 2. el pipeline de ficheros — donde ya se explica ABSND
R["ebs_file_pipeline_and_jobs.md"] = md(
    "knowledge/domains/Treasury/ebs_file_pipeline_and_jobs.md",
    "## Cómo se comprueba que un canal está vivo")

# 3. censo de canales — quien mira canales acaba mirando FF67
R["bank_statement_channels_by_company.md"] = md(
    "knowledge/domains/Treasury/bank_statement_channels_by_company.md",
    "## Los procesos que hay que definir")

# 4. companion EBS
p = "companions/bank_statement_ebs_companion.html"
s = io.open(p, encoding="utf-8").read()
anc = "<!-- s108 - LA OPORTUNIDAD, DIMENSIONADA -->"
if "NO aparece en FF67 hasta su primer extracto" in s:
    R["companion EBS"] = "ya estaba"
elif anc in s:
    io.open(p, "w", encoding="utf-8").write(
        s.replace(anc, '<div class="panel">\n' + HTML + '</div>\n\n' + anc, 1))
    R["companion EBS"] = "OK"
else:
    R["companion EBS"] = "SIN ANCLA"

# 5. memoria del incidente
p = "C:/Users/jp_lopez/.claude/projects/c--Users-jp-lopez-projects-abapobjectscreation/memory/incident_ebs_account_number_change_orphans_t028b.md"
s = io.open(p, encoding="utf-8").read()
old = ("- **La cabecera de FF67 no es configuración**: es `FEBKO-ABSND`, la identidad que traía el ÚLTIMO\n"
       "  fichero importado. Tras un cambio muestra el valor viejo para siempre, y eso es correcto.")
new = ("- **FF67 no es configuración, ni su cabecera ni su lista de cuentas.** La cabecera es\n"
       "  `FEBKO-ABSND`, la identidad que traía el ÚLTIMO fichero importado: tras un cambio muestra el\n"
       "  valor viejo para siempre. Y **la lista de cuentas es historial de extractos recibidos**, así que\n"
       "  **una cuenta nueva no aparece hasta que llega su primer extracto**. Probado: la lista ofrece\n"
       "  `(SP0000000MX7, UNO10)`, par que no existe en `T012K` pero sí en `FEBKO` con 10 extractos de\n"
       "  hasta 2015. **Ante «la cuenta nueva no está en FF67»: comprobar si ha llegado extracto, no\n"
       "  revisar la ficha del banco.** (claim 639)")
if "lista de cuentas es historial" in s:
    R["memoria"] = "ya estaba"
elif old in s:
    io.open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
    R["memoria"] = "OK"
else:
    R["memoria"] = "SIN ANCLA"

for k, v in R.items():
    print("  %-40s %s" % (k, v))
