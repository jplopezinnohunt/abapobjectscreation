# -*- coding: utf-8 -*-
"""Documenta el hueco 'mismo modelo, uso distinto' en el companion y en el doc de dominio."""
import io

BLOQUE = """<!-- s108 - MISMO MODELO, USO DISTINTO -->
<div class="panel">
  <div class="card">
    <h3 style="color:var(--cyan)">&#129513; Mismo modelo de extracto, uso distinto &mdash; d&oacute;nde est&aacute; el hueco (s108)</h3>
    <p style="margin-bottom:14px">Un extracto se procesa seg&uacute;n su <b>grupo de formato</b> (<code>T028B.VGTYP</code>), y cada
    grupo arrastra su juego de reglas de <code>T028G</code>. <b>Ese juego es el modelo.</b> La pregunta que nadie hab&iacute;a
    hecho: para un modelo dado, <b>&iquest;qu&eacute; bancos lo usan y cu&aacute;les no</b>, teni&eacute;ndolo asignado igual? Medido en P01 sobre
    UNES, ventana 2025-2026.</p>
    <table>
      <tr><th>Formato</th><th>Ctas</th><th>Electr&oacute;nico</th><th>Mixto</th><th>Manual</th><th>Sin extracto</th><th>Bancos que NO lo procesan</th></tr>
      <tr><td><b>XRT940</b></td><td>104</td><td>70</td><td>26</td><td style="color:var(--orange)"><b>7</b></td><td style="color:var(--red)">1</td><td>BLN01 &middot; BMN01 &middot; BTE01 &middot; CBE01 &middot; ECO08</td></tr>
      <tr><td>TR_TRNF</td><td>17</td><td>14</td><td>0</td><td>0</td><td style="color:var(--red)"><b>3</b></td><td>NTB01</td></tr>
      <tr><td>SOG_FR &middot; SOG_FRB &middot; SCB19_IQ &middot; CIT04_US &middot; CIT21_CA &middot; CIT24_GA &middot; SOG_EUR4</td><td>15</td><td>15</td><td>0</td><td>0</td><td>0</td><td>&mdash; ninguno</td></tr>
      <tr><td><i>(sin modelo)</i></td><td>8</td><td>0</td><td>0</td><td>1</td><td>7</td><td>BRA01 &middot; BTE01 &middot; DEU01 &middot; DEU02 &middot; <b>NTB02</b> &middot; UBS02 &middot; UNDP</td></tr>
    </table>
  </div>

  <div class="card">
    <h3 style="color:var(--orange)">&#9873; El hueco: 11 cuentas tienen el modelo montado y no lo usan</h3>
    <p style="margin-bottom:14px"><b>7 se teclean a mano</b> teniendo <code>XRT940</code> asignado &mdash; el mismo modelo que
    <b>96 cuentas procesan electr&oacute;nicamente</b>. Y <b>4 no reciben nada</b> con el modelo ya construido.</p>
    <table>
      <tr><th>Cuenta</th><th>Div.</th><th>Canal</th><th>Extractos</th><th>Banco</th></tr>
      <tr><td>UNES/BLN01-USD01</td><td>USD</td><td>MANUAL</td><td>168</td><td>Blue Nile Mashreg &mdash; Jartum</td></tr>
      <tr><td>UNES/BLN01-SDD01</td><td>SDG</td><td>MANUAL</td><td>126</td><td>Blue Nile Mashreg &mdash; Jartum</td></tr>
      <tr><td>UNES/BMN01-CUP02</td><td>CUP</td><td>MANUAL</td><td>63</td><td>Banco Metropolitano &mdash; La Habana</td></tr>
      <tr><td>UNES/BMN01-EUR01</td><td>EUR</td><td>MANUAL</td><td>49</td><td>Banco Metropolitano &mdash; La Habana</td></tr>
      <tr><td>UNES/BTE01-IRR02</td><td>IRR</td><td>MANUAL</td><td>40</td><td>Bank Tejarat &mdash; Teher&aacute;n</td></tr>
      <tr><td>UNES/ECO08-ZWG01</td><td>ZWG</td><td>MANUAL</td><td>10</td><td>Ecobank &mdash; Harare</td></tr>
      <tr><td>UNES/BTE01-EUR01</td><td>EUR</td><td>MANUAL</td><td>8</td><td>Bank Tejarat &mdash; Teher&aacute;n</td></tr>
      <tr><td>UNES/CBE01-ETB02</td><td>ETB</td><td style="color:var(--red)">SIN EXTRACTO</td><td>0</td><td>Commercial Bank of Ethiopia</td></tr>
      <tr><td>UNES/NTB01-USD04 &middot; USD05 &middot; USD06</td><td>USD</td><td style="color:var(--red)">SIN EXTRACTO</td><td>0</td><td>Northern Trust &mdash; mandatos PIMCO / JP Morgan / RAMP</td></tr>
    </table>
    <p style="margin-top:14px;color:var(--green)"><b>Por qu&eacute; esto importa: el coste en SAP es CERO.</b> El modelo ya est&aacute;
    construido, probado y corriendo para 96 cuentas. Para esas 7 no hay que dise&ntilde;ar reglas ni transportar customizing.</p>
    <p style="margin-top:10px;color:var(--orange)">&#9888; <b>Y lo que la medida NO dice:</b> tener el modelo asignado no
    prueba que el fichero <i>pueda</i> llegar. La restricci&oacute;n est&aacute; <b>aguas arriba</b> &mdash; que el banco emita MT940 y que
    el fichero alcance el share de Coupa. Todos son bancos locales de contextos dif&iacute;ciles (Jartum, La Habana, Teher&aacute;n,
    Harare, Addis Abeba), y es plausible que ah&iacute; est&eacute; el l&iacute;mite real. <b>Eso convierte el trabajo en una conversaci&oacute;n de
    canal con el banco, no en un proyecto de configuraci&oacute;n</b> &mdash; y esa distinci&oacute;n es la que hace la lista accionable.</p>
  </div>

  <div class="card">
    <h3 style="color:var(--purple)">&#127919; El caso que responde la pregunta en su forma m&aacute;s pura</h3>
    <p><b>Northern Trust, <code>NTB01</code>, formato <code>TR_TRNF</code>, seis cuentas del mismo banco y el mismo
    modelo:</b> <code>USD01</code>, <code>USD02</code> y <code>USD03</code> reciben extracto a diario;
    <code>USD04</code>, <code>USD05</code> y <code>USD06</code> no reciben nada. Mismo banco, mismo custodio, mismo
    formato, misma configuraci&oacute;n.</p>
    <p style="margin-top:10px"><b>No es el banco y no es el formato: es la cuenta.</b> Las tres que no reciben son los
    mandatos de inversi&oacute;n (PIMCO, JP Morgan, RAMP) &mdash; y <b>mueven saldo</b> (3 a 5 periodos con movimiento en 2025-2026)
    sin ning&uacute;n extracto bancario que lo corrobore. &Eacute;se es el hueco de control, y es la raz&oacute;n por la que la
    <b>naturaleza</b> de la cuenta tiene que estar declarada: es lo &uacute;nico que explica por qu&eacute; tres hermanas s&iacute; y tres
    no.</p>
  </div>
</div>

"""

ANC = "<!-- ═══════════════════════ E2E CHAIN ═══════════════════════ -->"

p = "companions/bank_statement_ebs_companion.html"
s = io.open(p, encoding="utf-8").read()
if "Mismo modelo de extracto, uso distinto" in s:
    print("companion: ya estaba")
elif ANC in s:
    io.open(p, "w", encoding="utf-8").write(s.replace(ANC, BLOQUE + ANC, 1))
    print("companion: actualizado")
else:
    print("companion: ANCLA NO ENCONTRADA")

SEC = """## La pregunta que hay que responder: mismo modelo, uso distinto

Para un modelo dado, **¿qué bancos lo usan y cuáles no, teniéndolo asignado igual?**

| Formato | Ctas | Electrónico | Mixto | Manual | Sin extracto | Bancos que NO lo procesan |
|---|---:|---:|---:|---:|---:|---|
| **XRT940** | 104 | 70 | 26 | **7** | 1 | BLN01 · BMN01 · BTE01 · CBE01 · ECO08 |
| TR_TRNF | 17 | 14 | 0 | 0 | **3** | NTB01 |
| los otros 7 formatos | 15 | 15 | 0 | 0 | 0 | — ninguno |
| *(sin modelo)* | 8 | 0 | 0 | 1 | 7 | BRA01 · BTE01 · DEU01 · DEU02 · **NTB02** · UBS02 · UNDP |

### El hueco: 11 cuentas tienen el modelo montado y no lo usan

**Siete se teclean a mano** teniendo `XRT940` asignado — el mismo modelo que **96 cuentas
procesan electrónicamente**:

| Cuenta | Canal | Extractos | Banco |
|---|---|---:|---|
| BLN01-USD01 · SDD01 | manual | 168 · 126 | Blue Nile Mashreg — Jartum |
| BMN01-CUP02 · EUR01 | manual | 63 · 49 | Banco Metropolitano — La Habana |
| BTE01-IRR02 · EUR01 | manual | 40 · 8 | Bank Tejarat — Teherán |
| ECO08-ZWG01 | manual | 10 | Ecobank — Harare |
| CBE01-ETB02 | sin extracto | 0 | Commercial Bank of Ethiopia |
| NTB01-USD04 · USD05 · USD06 | sin extracto | 0 | Northern Trust — mandatos |

**El coste en SAP es cero.** El modelo está construido, probado y corriendo para 96 cuentas: no
hay que diseñar reglas ni transportar customizing.

> ⚠️ **Lo que la medida NO dice:** tener el modelo asignado no prueba que el fichero *pueda*
> llegar. La restricción está **aguas arriba** — que el banco emita MT940 y que el fichero
> alcance el share de Coupa. Los cinco son bancos locales de contextos difíciles (Jartum, La
> Habana, Teherán, Harare, Addis Abeba) y es plausible que ahí esté el límite real. **Eso
> convierte el trabajo en una conversación de canal con el banco, no en un proyecto de
> configuración** — y esa distinción es la que hace la lista accionable en vez de una idea.

### El caso puro: mismo banco, mismo formato, comportamiento opuesto

**Northern Trust `NTB01`, formato `TR_TRNF`, seis cuentas:** `USD01/02/03` reciben extracto a
diario; `USD04/05/06` no reciben nada. Mismo banco, mismo custodio, mismo formato, misma
configuración.

**No es el banco y no es el formato: es la cuenta.** Las tres que no reciben son los mandatos
de inversión, y **mueven saldo sin ningún extracto que lo corrobore**. Ése es el hueco de
control — y la razón por la que la naturaleza de la cuenta tiene que estar declarada: es lo
único que explica por qué tres hermanas sí y tres no.

"""

p2 = "knowledge/domains/Treasury/ebs_format_models.md"
s2 = io.open(p2, encoding="utf-8").read()
anc2 = "## Las 9 sin modelo asignado"
if "mismo modelo, uso distinto" in s2:
    print("doc: ya estaba")
elif anc2 in s2:
    io.open(p2, "w", encoding="utf-8").write(s2.replace(anc2, SEC + anc2, 1))
    print("doc: actualizado")
else:
    print("doc: ANCLA NO ENCONTRADA")
