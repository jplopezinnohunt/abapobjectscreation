# -*- coding: utf-8 -*-
"""Anade al companion la OPORTUNIDAD explicada y dimensionada, con la verificacion de
movimiento que la hace real (o que descarta una cuenta de la lista)."""
import io

BLOQUE = """<!-- s108 - LA OPORTUNIDAD, DIMENSIONADA -->
<div class="panel">
  <div class="card">
    <h3 style="color:var(--green)">&#128200; La oportunidad, dimensionada &mdash; y no es la que parec&iacute;a</h3>
    <p style="margin-bottom:14px">Siete cuentas se teclean a mano teniendo <code>XRT940</code> asignado, el mismo modelo que
    96 cuentas procesan solas. La tentaci&oacute;n es venderlo como ahorro de trabajo administrativo. <b>Medido, ese argumento
    es d&eacute;bil y hay que decirlo:</b> son <b>1.712 l&iacute;neas en dos a&ntilde;os</b> &mdash; unas 856 al a&ntilde;o, ~3 l&iacute;neas por d&iacute;a h&aacute;bil
    repartidas entre siete cuentas. Para comparar: <b>una sola cuenta electr&oacute;nica</b>, ECO08-USD01, procesa
    <b>11.669 l&iacute;neas</b> en el mismo periodo. Las siete manuales juntas son el <b>15 %</b> de esa una.</p>
    <p><b>La oportunidad no es el tecleo. Son las otras tres capas.</b></p>
  </div>

  <div class="card">
    <h3 style="color:var(--orange)">&#9888; Capa 1 &mdash; lo tecleado no compensa solo, y eso s&iacute; genera trabajo</h3>
    <p style="margin-bottom:14px">Un extracto manual recibe reglas <code>MXXD</code>/<code>MXXC</code>, que llevan
    <b>algoritmo 000: sin compensaci&oacute;n autom&aacute;tica</b>. Un extracto electr&oacute;nico del mismo formato recibe
    <code>SUBD</code>/<code>SUBC</code> con <b>algoritmo 015</b>, que casa por asignaci&oacute;n. Medido:</p>
    <table>
      <tr><th>Cuenta</th><th>Extractos</th><th>L&iacute;neas</th><th>Reglas que reciben</th><th>&iquest;Compensa solo?</th></tr>
      <tr><td colspan="5" style="background:var(--surface-2)"><b>MANUALES</b> &mdash; con XRT940 asignado</td></tr>
      <tr><td>BTE01-IRR02</td><td>40</td><td>808</td><td>MXXD 789 &middot; MXXC 19</td><td style="color:var(--red)">NO</td></tr>
      <tr><td>BLN01-SDD01</td><td>126</td><td>362</td><td>MXXD 322 &middot; MXXC 40</td><td style="color:var(--red)">NO</td></tr>
      <tr><td>BLN01-USD01</td><td>168</td><td>240</td><td>MXXD 212 &middot; MXXC 28</td><td style="color:var(--red)">NO</td></tr>
      <tr><td>BMN01-CUP02</td><td>63</td><td>183</td><td>MXXD 165 &middot; MXXC 18</td><td style="color:var(--red)">NO</td></tr>
      <tr><td>BMN01-EUR01</td><td>49</td><td>67</td><td>MXXD 59 &middot; MXXC 8</td><td style="color:var(--red)">NO</td></tr>
      <tr><td>ECO08-ZWG01</td><td>10</td><td>43</td><td>MXXD 32 &middot; MXXC 11</td><td style="color:var(--red)">NO &middot; <b>35 de 43 sin documento FI</b></td></tr>
      <tr><td>BTE01-EUR01</td><td>8</td><td>9</td><td>MXXD 9</td><td style="color:var(--red)">NO</td></tr>
      <tr><td colspan="5" style="background:var(--surface-2)"><b>CONTROL</b> &mdash; mismo formato, entran electr&oacute;nicos</td></tr>
      <tr><td>ECO08-USD01</td><td>434</td><td>11.669</td><td>SUBD 11.043 &middot; SUBC 386</td><td style="color:var(--green)">S&Iacute;, algoritmo 015</td></tr>
      <tr><td>ECO05-XAF01</td><td>432</td><td>7.303</td><td>SUBD 6.630 &middot; SUBC 554</td><td style="color:var(--green)">S&Iacute;, algoritmo 015</td></tr>
    </table>
    <p style="margin-top:14px"><b>1.712 l&iacute;neas que caen enteras en la cola de FEBAN</b> para casarlas a mano despu&eacute;s.
    El tecleo del extracto es la punta; el trabajo real est&aacute; aguas abajo.</p>
  </div>

  <div class="card">
    <h3 style="color:var(--red)">&#128272; Capa 2 &mdash; son cuentas que PAGAN y mueven dinero, no cuentas dormidas</h3>
    <p style="margin-bottom:14px">Verificaci&oacute;n obligada antes de llamar oportunidad a nada: <b>&iquest;tienen movimiento?</b>
    Seis de las siete no solo lo tienen &mdash; son <b>PAGADORAS</b>. Movimiento acumulado 2025-2026 en moneda local de la
    sociedad, y n&uacute;mero de pagos emitidos:</p>
    <table>
      <tr><th>Cuenta</th><th>Comportamiento</th><th>Pagos</th><th>Periodos con movimiento</th><th>Movimiento acumulado</th></tr>
      <tr><td>BLN01-USD01</td><td>PAGADORA</td><td>27</td><td>39</td><td>4.067.040</td></tr>
      <tr><td>BTE01-IRR02</td><td>PAGADORA</td><td><b>355</b></td><td>33</td><td>1.743.129</td></tr>
      <tr><td>BLN01-SDD01</td><td>PAGADORA</td><td>2</td><td>39</td><td>1.312.078</td></tr>
      <tr><td>BMN01-EUR01</td><td>PAGADORA</td><td>35</td><td>31</td><td>514.903</td></tr>
      <tr><td>BMN01-CUP02</td><td>PAGADORA</td><td>4</td><td>31</td><td>278.886</td></tr>
      <tr><td>BTE01-EUR01</td><td>PAGADORA</td><td>11</td><td>22</td><td>76.904</td></tr>
      <tr><td>ECO08-ZWG01</td><td>OPERATIVA_COBRO</td><td>0</td><td>11</td><td>27.206</td></tr>
      <tr style="opacity:.6"><td>CBE01-ETB02</td><td>DURMIENTE</td><td>0</td><td><b>0</b></td><td><b>0</b></td></tr>
    </table>
    <p style="margin-top:14px;color:var(--orange)"><b>Y esa verificaci&oacute;n descarta una:</b> <code>CBE01-ETB02</code> no
    tiene extractos, ni pagos, ni movimiento. Tiene el modelo montado y no hace nada. <b>No es una oportunidad: es una
    cuenta que hay que declarar cerrada o explicar.</b> La lista real son <b>seis</b>.</p>
  </div>

  <div class="card">
    <h3 style="color:var(--purple)">&#129331; Capa 3 &mdash; qui&eacute;n lo sostiene, y cu&aacute;nto lleva callado</h3>
    <p style="margin-bottom:14px"><b>Diez personas</b> han tecleado esos extractos, no las cuatro que sugiere el usuario
    dominante de cada cuenta. Y hay cuentas que llevan meses mudas sin que nada lo detecte:</p>
    <table>
      <tr><th>Cuenta</th><th>&Uacute;ltimo extracto</th><th>Silencio</th><th>Qui&eacute;n lo hace</th></tr>
      <tr><td>BTE01-IRR02</td><td>25.08.2026</td><td>3 d</td><td>B_TASHAKORI 21 &middot; R_KARAM 19</td></tr>
      <tr><td>BLN01-SDD01</td><td>20.08.2026</td><td>8 d</td><td>K_ABDULLAH 109 &middot; R_ABEYE 12 &middot; H_YAHIA 5</td></tr>
      <tr><td>BLN01-USD01</td><td>18.08.2026</td><td>10 d</td><td>K_ABDULLAH 117 &middot; R_ABEYE 35 &middot; H_YAHIA 15</td></tr>
      <tr><td>BMN01-CUP02</td><td>14.08.2026</td><td>14 d</td><td>J_MONTANO-PU 55 &middot; JJ_FERRAN-RO 7</td></tr>
      <tr><td>BMN01-EUR01</td><td>28.07.2026</td><td style="color:var(--orange)">31 d</td><td>J_MONTANO-PU 46 &middot; JJ_FERRAN-RO 3</td></tr>
      <tr><td>ECO08-ZWG01</td><td>16.06.2026</td><td style="color:var(--red)"><b>73 d</b></td><td>R_MUSAKWA 9</td></tr>
      <tr><td>BTE01-EUR01</td><td>01.04.2026</td><td style="color:var(--red)"><b>149 d</b></td><td>B_TASHAKORI 6 &middot; R_KARAM 2</td></tr>
    </table>
    <p style="margin-top:14px">Ninguna de esas dos &uacute;ltimas ha disparado nada. <b>No hay responsable declarado ni cadencia
    esperada en ning&uacute;n sitio</b> &mdash; se deduce del log, a posteriori.</p>
  </div>

  <div class="card">
    <h3 style="color:var(--cyan)">&#9989; La oportunidad, dicha con precisi&oacute;n</h3>
    <p style="margin-bottom:12px"><b>No es ahorrar tecleo.</b> 856 l&iacute;neas al a&ntilde;o no justifican un proyecto, y decir lo
    contrario ser&iacute;a vender humo. Es esto:</p>
    <ol style="margin:0 0 12px 20px;padding:0;line-height:1.75">
      <li><b>Seis cuentas que pagan y mueven millones</b> no tienen extracto electr&oacute;nico, y por tanto <b>ninguna
      corroboraci&oacute;n autom&aacute;tica</b> de lo que el banco dice. Una de ellas emiti&oacute; <b>355 pagos</b> en dos a&ntilde;os.</li>
      <li><b>1.712 l&iacute;neas no compensan solas</b> por usar reglas MXX* con algoritmo 000: van enteras a FEBAN. El
      trabajo est&aacute; aguas abajo, no en el tecleo.</li>
      <li><b>Depende de diez personas</b> en Jart&uacute;m, La Habana, Teher&aacute;n y Harare, sin due&ntilde;o ni cadencia declarados. Dos
      cuentas llevan 73 y 149 d&iacute;as mudas y nadie lo ha notado.</li>
      <li><b>El coste en SAP de cerrarlo es CERO</b>: el modelo <code>XRT940</code> ya est&aacute; construido, probado y
      corriendo para 96 cuentas.</li>
    </ol>
    <p style="color:var(--orange)">&#9888; <b>Y el l&iacute;mite honesto:</b> tener el modelo no prueba que el fichero pueda
    llegar. La restricci&oacute;n est&aacute; aguas arriba &mdash; que el banco emita MT940 y alcance el share de Coupa &mdash; y son bancos
    locales de contextos dif&iacute;ciles. <b>Puede que para algunas la respuesta correcta siga siendo manual</b>; entonces lo
    que falta no es autom&aacute;tica sino <b>declarar due&ntilde;o, cadencia y vigilancia</b>. Las dos salidas son legit&iacute;mas; lo que
    no lo es es que hoy no se pueda distinguir cu&aacute;l aplica.</p>
    <p style="margin-top:12px"><b>El primer paso no cuesta nada:</b> preguntar a esos cuatro bancos si emiten MT940. Si
    alguno dice que s&iacute;, esa cuenta se enchufa sin tocar configuraci&oacute;n.</p>
  </div>
</div>

"""

ANC = "<!-- s108 - MISMO MODELO, USO DISTINTO -->"
p = "companions/bank_statement_ebs_companion.html"
s = io.open(p, encoding="utf-8").read()
if "La oportunidad, dimensionada" in s:
    print("companion: ya estaba")
elif ANC in s:
    io.open(p, "w", encoding="utf-8").write(s.replace(ANC, BLOQUE + ANC, 1))
    print("companion: oportunidad anadida")
else:
    print("companion: ANCLA NO ENCONTRADA")
