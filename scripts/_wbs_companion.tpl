<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Proyecto / WBS — UNESCO SAP · el modelo, quién lo escribe y qué informa</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--un-blue:#0079c1;--un-dark:#1a3a5c;--un-grey:#5a6c84;--bg:#f5f7fa;--card:#fff;
 --border:#dde3eb;--ok:#2c8b50;--bad:#c93a3a;--warn:#dd6b20;--purple:#664b9b}
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
 color:var(--un-dark);background:var(--bg)}
.container{max-width:1280px;margin:0 auto;padding:0 18px 60px}
header{background:linear-gradient(135deg,#0079c1,#1a3a5c);color:#fff;padding:34px 0 30px;margin-bottom:26px}
header .container{padding-bottom:0}
h1{margin:0 0 6px;font-size:27px;font-weight:600}
.sub{opacity:.92;font-size:15px;max-width:940px}
.meta{margin-top:14px;font-size:12px;opacity:.75}
h2{font-size:19px;margin:34px 0 12px;padding-bottom:7px;border-bottom:2px solid var(--border)}
h3.vh{font-size:13px;letter-spacing:.06em;margin:24px 0 6px;padding-left:9px;
 border-left:4px solid var(--un-grey)}
h3.vh em{font-style:normal;font-weight:400;color:var(--un-grey);font-size:12px;margin-left:8px}
h3.aban{border-color:var(--bad);color:var(--bad)}
h3.adop{border-color:var(--ok);color:var(--ok)}
h3.noinfo{border-color:var(--warn);color:var(--warn)}
h3.uso{border-color:var(--un-blue);color:var(--un-blue)}
h3.resid{border-color:var(--un-grey);color:var(--un-grey)}
h3.vacio{border-color:var(--purple);color:var(--purple)}
code{background:#eef2f7;padding:1px 5px;border-radius:3px;font-size:12.5px}
.note{font-size:12.5px;color:var(--un-grey)}
.orient{background:#fff;border:1px solid var(--border);border-left:5px solid var(--un-blue);
 border-radius:6px;padding:6px 20px 18px;margin-bottom:8px}
.honest{background:#eef2f7;border-radius:5px;padding:10px 13px;font-size:12.5px;color:var(--un-grey)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--border);border-top:3px solid var(--un-blue);
 border-radius:6px;padding:13px 15px}
.kpi b{display:block;font-size:23px;color:var(--un-blue)}
.kpi span{font-size:12px;color:var(--un-grey)}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:13px}
th,td{padding:7px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:middle}
th{background:#eef2f7;font-size:11.5px;letter-spacing:.05em;color:var(--un-grey)}
table.det{font-size:12px}
td.num{text-align:right;color:var(--un-grey);white-space:nowrap}
td.n{text-align:right;font-weight:700;color:var(--un-blue);white-space:nowrap}
td.md{color:var(--un-grey);font-size:11.5px}
td.sp{width:230px}
.spark{display:flex;align-items:flex-end;gap:1px;height:30px}
.spark i{width:6px;background:var(--un-grey);opacity:.55;border-radius:1px 1px 0 0}
.spark i.hi{background:var(--ok);opacity:.9}
.spark i.mid{background:var(--un-blue);opacity:.75}
.spark i.lo{background:var(--bad);opacity:.5}
.sparklab{font-size:10.5px;color:var(--un-grey);margin-top:2px}
.hbar{display:inline-block;height:9px;background:var(--un-blue);border-radius:2px;
 vertical-align:middle;margin-right:6px}
.scroll{overflow-x:auto}
.lesson{background:#fff8ef;border-left:4px solid var(--warn);padding:11px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
.warn{background:#fdecec;border-left:4px solid var(--bad);padding:12px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}
.pl{background:var(--card);border:1px solid var(--border);border-top:3px solid var(--un-blue);
 border-radius:6px;padding:13px 15px}
.pl b{display:block;margin-bottom:5px}
.pl span{font-size:12.5px;color:var(--un-grey)}
.repro{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--ok);
 border-radius:6px;padding:12px 15px;margin-bottom:11px}
.repro .rh{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.repro .rh b{font-size:14px}
.repro .rh span{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;font-weight:700;color:var(--un-blue)}
.repro pre{margin:0;background:#1a3a5c;color:#e8eef5;padding:11px 13px;border-radius:4px;
 font-size:11.5px;line-height:1.45;overflow-x:auto;white-space:pre}
.repro .cav{margin-top:8px;font-size:12.5px;color:var(--un-grey)}
.closing{background:#f0f7fc;border:1px solid var(--border);border-left:5px solid var(--purple);
 border-radius:6px;padding:16px 22px;margin-top:34px}
.closing h2{border:0;margin-top:4px}
.tl{border-left:2px solid var(--border);margin:14px 0 4px 8px;padding-left:18px}
.tl .ev{position:relative;padding:9px 0}
.tl .ev:before{content:"";position:absolute;left:-25px;top:15px;width:9px;height:9px;
 border-radius:50%;background:var(--un-blue)}
.tl .ev b{display:block;font-size:13.5px}
.tl .ev span{font-size:12.5px;color:var(--un-grey)}
.tl .ev.key:before{background:var(--bad);width:12px;height:12px;left:-26px}
footer{margin-top:40px;font-size:12px;color:var(--un-grey);border-top:1px solid var(--border);padding-top:14px}
@media(max-width:900px){.three{grid-template-columns:1fr}}
</style></head><body>
<header><div class="container">
<h1>Proyecto / WBS — el modelo y quién lo escribe</h1>
<div class="sub">El elemento PEP es <b>donde un proyecto se encuentra con el dinero</b>: lleva
 la imputación sobre la que aterriza cada apunte. Su extensión custom es el mayor bloque de
 capacidad preconstruida de toda la instalación — <b>@NFIELDS@ campos</b> — y leerlos de uno en
 uno da una respuesta equivocada de tres maneras distintas.</div>
<div class="meta"><b>Cifras, tendencias y veredictos: GENERADOS</b> por el algoritmo A19
 (<code>process_mining/wbs_model.py</code>) en cada build — no pueden derivar. <b>La
 interpretación está ESCRITA</b> en <code>scripts/_wbs_companion.tpl</code>. Nunca editar el
 HTML.</div>
</div></header>
<div class="container">

<div class="orient">
<h2 style="border:0;margin-top:6px">0 · Si no conoces nada de esto, empieza aquí</h2>
<p><b>Qué es un elemento PEP.</b> Un proyecto en SAP se descompone en un árbol de elementos —
 la <i>estructura de desglose de trabajo</i>, WBS. Cada hoja de ese árbol es una <b>imputación
 contable</b>: cuando alguien compra algo o cobra una nómina contra el proyecto, el apunte
 aterriza en un elemento PEP concreto. Por eso lo que el elemento sepa de sí mismo determina
 lo que la organización puede responder después.</p>
<div class="kpis">
 <div class="kpi"><b>@ROWS@</b><span>elementos PEP</span></div>
 <div class="kpi"><b>@NFIELDS@</b><span>campos custom</span></div>
 <div class="kpi" style="grid-column:span 2"><span style="font-size:13px">@VERDICTS@</span></div>
</div>

<h2 style="border:0">0b · Las tres lecturas que este análisis existe para impedir</h2>
<ol style="font-size:13.5px">
 <li><b>La tasa de llenado sola miente.</b> Un campo numérico o NUMC <b>nunca está en
  blanco</b> — vale cero — así que una prueba de «no vacío» contó diez de los @NFIELDS@ como
  llenos al 100% cuando uno de ellos está al 0,45% real. El vacío <b>depende del tipo</b>.</li>
 <li><b>Una tasa plana esconde una curva.</b> <code>YYE_DONOR</code> está al 18,5% global, que
  se lee como «un campo que nadie adoptó». Medido <b>por año de creación</b> va del 82% en 2002
  al 5% en 2026: <b>fue</b> la práctica y algo lo desplazó. Un número bajo y plano y uno que
  decae significan cosas opuestas.</li>
 <li><b>Poblado no es informativo.</b> <code>YYE_IMPL_AGENCY</code> está lleno en el 42% de los
  elementos y lleva <b>un solo valor distinto</b>. Tiene tasa de llenado y no informa de nada.
  La cardinalidad es el segundo eje, y sin ella el primero engaña.</li>
</ol>
<p class="honest">Por eso cada campo se mide en <b>tres ejes</b> — llenado según su tipo,
 tendencia por año de creación, y valores distintos — y solo se entiende cuando los tres
 coinciden. El veredicto de cada uno sale de los tres juntos, no de ninguno por separado.</p>
</div>

<h2>1 · Los @NFIELDS@ campos, por veredicto</h2>
@GROUPS@

<h2>2 · Quién escribe el maestro</h2>
<p class="note">La respuesta cambió, y con ella cambió todo lo demás. El primer elemento PEP
 escrito por la interfaz lleva fecha <b>@FIRST@</b>.</p>
<div class="scroll"><table class="det"><tr><th>año</th><th>PEP creados</th>
<th>por la interfaz</th><th>cuota</th></tr>@WROWS@</table></div>
<p class="lesson">El maestro de proyectos <b>ya no lo escriben personas</b>. Y eso reordena la
 lectura de todos los campos de arriba: la tasa de llenado de un campo es una propiedad de
 <b>quien lo escribe</b>, no de su utilidad. Cuando cambia el escritor, cambian todas las
 tasas — y no porque nadie decidiera nada sobre el campo.</p>

<h2>3 · La gramática de los identificadores se limpió sola</h2>
<p class="note">Formas distintas que toma <code>YYE_BENEF1</code>, por año. <code>D</code> es un
 dígito y <code>A</code> una letra: la <i>forma</i> del identificador, no su valor.</p>
<div class="scroll"><table class="det" style="max-width:560px"><tr><th>año</th>
<th>formas distintas</th><th>las más frecuentes</th></tr>@GROWS@</table></div>
<p class="lesson">Mientras lo llenaban personas convivían varias formas. Cuando entró la
 interfaz <b>convergió a una sola</b>. Una interfaz no solo llena más rápido: <b>quita la
 varianza que mete la mano humana</b> — y la dispersión anterior mide lo que esa mano estaba
 costando. Al revés también sirve: <b>una gramática que colapsa FECHA una automatización</b>.</p>

<h2>4 · Dónde vive el donante, que no es donde parece</h2>
<p class="note">La pregunta «quién financió este proyecto» <b>no se responde desde el maestro de
 proyectos</b>. La dimensión no se fue del sistema: dejó de ser un atributo y pasó a ser una
 entidad, y una entidad vive en una tabla maestra distinta.</p>
<div class="three">
 <div class="pl"><b>En SAP · el maestro de CLIENTES</b><span><b>5.401 de 12.517</b> clientes de
  <code>KNA1</code> (43,1%) en seis grupos de cuenta de donante: <code>OGIN</code> 4.010,
  <code>MSOT</code> 459, <code>MSAC</code> 431, <code>MSCO</code> 185, <code>DELG</code> 185,
  <code>UNAG</code> 131. Un objeto con dirección, país y categoría — donde antes había una
  cadena como «SWITZ.» entre 763 valores sin control.</span></div>
 <div class="pl"><b>En el Core Planner · un ROL</b><span>consumido en solo lectura del proyecto
  hermano bajo ADR-007: <code>Workplan_Organisation_Role__c</code> con <b>5.777 filas</b> de
  donante sobre <b>2.738 planes</b>, 2,11 por plan, con <code>Donor_Category__c</code> y
  <code>Original_Donor_Agreement__c</code> al lado.</span></div>
 <div class="pl"><b>El puente · va a BW, no a ECC</b><span><code>SF Account → ZGMSPNSR</code>,
  <code>Donor_Category__c → ZDONOR_CA</code>, ISO de país → <code>ZDON_CTRY</code>, por fichero
  plano. <b>Nada en ese camino escribe <code>FMFINCODE-SPONSOR</code></b>, que está lleno en el
  0,2% de los fondos. Y no hay ninguna tabla de GM en el golden.</span></div>
</div>
<div class="warn"><b>Para el diseño futuro:</b> el enlace proyecto→donante <b>no existe</b> en
 el modelo SAP. Se responde por el plan de trabajo del Core Planner, o por el maestro de
 clientes si lo que trazas es el movimiento del dinero. Pero hay una excepción que importa: en
 los 367 elementos marcados con <code>YYE_POC</code> el donante <b>sí llega</b>, con nombre
 completo y coincidiendo con la lista del Core Planner. La vía existe y funciona — cubre un
 tercio de las raíces extrapresupuestarias nuevas. <b>No hay que construirla, hay que
 extenderla.</b></div>

<h2>5 · Cómo reproducir cada cifra</h2>
<p class="note">Cada consulta se ejecutó contra el golden. Base:
 <code>Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db</code>, procedencia
 P01, solo lectura. O directamente: <code>python process_mining/wbs_model.py</code>.</p>

<div class="repro"><div class="rh"><b>Llenado de un campo, sin contar los ceros</b><span>el eje 1</span></div>
<pre>SELECT COUNT(*) FROM PRPS
WHERE YYE_PRCTO IS NOT NULL AND trim(trim(YYE_PRCTO),'0.')&lt;&gt;'';</pre>
<div class="cav"><code>trim(X,'0.')</code> quita ceros y puntos de los extremos, así
 <code>'0.00'</code> y <code>'00000000'</code> colapsan a vacío mientras <code>'7.00'</code>
 conserva su 7. Sin esto <code>YYE_PRCTO</code> da 100% en vez de 0,45%.</div></div>

<div class="repro"><div class="rh"><b>La tendencia por año de creación</b><span>el eje 2</span></div>
<pre>SELECT substr(ERDAT,1,4) y, COUNT(*),
       SUM(CASE WHEN trim(YYE_DONOR)&lt;&gt;'' THEN 1 ELSE 0 END)
FROM PRPS GROUP BY y HAVING COUNT(*)&gt;200 ORDER BY y;</pre>
<div class="cav">Sin agrupar por <code>ERDAT</code> el 18,5% de <code>YYE_DONOR</code> parece un
 campo que nadie usó. Con ella es una curva de abandono de veinticuatro años.</div></div>

<div class="repro"><div class="rh"><b>Cardinalidad</b><span>el eje 3</span></div>
<pre>SELECT COUNT(DISTINCT YYE_IMPL_AGENCY) FROM PRPS
WHERE trim(YYE_IMPL_AGENCY)&lt;&gt;'';</pre>
<div class="cav">Devuelve <b>1</b>. Un campo lleno en el 42% con un solo valor no informa de
 nada, y ninguna tasa de llenado lo detecta.</div></div>

<div class="repro"><div class="rh"><b>Quién escribe, y desde cuándo</b><span>@FIRST@</span></div>
<pre>SELECT MIN(ERDAT) FROM PRPS WHERE trim(ERNAM)='MULESOFT';

SELECT substr(ERDAT,1,4) y, COUNT(*),
       SUM(CASE WHEN trim(ERNAM)='MULESOFT' THEN 1 ELSE 0 END)
FROM PRPS GROUP BY y ORDER BY y;</pre>
<div class="cav">La primera fila que escribió un usuario técnico <b>ES</b> el arranque de la
 integración, y la rampa de su cuota es el traspaso. Más preciso que cualquier documento de
 proyecto, y sale de datos que ya tienes.</div></div>

<div class="repro"><div class="rh"><b>Los grupos de cuenta de donante</b><span>5.401 de 12.517</span></div>
<pre>SELECT KTOKD, COUNT(*) FROM KNA1 GROUP BY KTOKD ORDER BY 2 DESC;</pre>
<div class="cav">Los seis de donante son <code>OGIN</code>, <code>MSOT</code>,
 <code>MSAC</code>, <code>MSCO</code>, <code>DELG</code> y <code>UNAG</code>. El nombre del
 grupo lo dice el maestro; nosotros solo lo contamos.</div></div>

<div class="closing">
<h2>6 · Comentario final — cómo ha evolucionado la solución en estos años</h2>
<p>Nada de lo anterior se diseñó de una vez. El modelo que hay hoy es el <b>sedimento de
 cuatro decisiones separadas por veinte años</b>, y ninguna borró a la anterior: por eso
 conviven campos en uso, campos en abandono y campos que nunca arrancaron, en la misma tabla y
 con el mismo prefijo.</p>
<div class="tl">
 <div class="ev"><b>2002 — el donante como texto libre</b><span>El 82% de los elementos PEP
  creados ese año llevan <code>YYE_DONOR</code>, con 763 valores distintos y sin control:
  «VOL.CONT.», «SWITZ.», «PRIV. FUND.». Era la práctica, y era a mano.</span></div>
 <div class="ev"><b>2002-2020 — la erosión lenta</b><span>La misma cifra baja casi cada año:
  64% en 2005, 39% en 2008, 26% en 2011, 13% en 2014, 9% en 2017. Nadie decidió apagarlo; se
  fue dejando de rellenar. <code>YYE_TYP_SOU</code> y <code>YYE_EXEC</code> siguen la misma
  curva.</span></div>
 <div class="ev"><b>2013-2020 — un piloto que empieza y termina</b><span>
  <code>YYE_COOP_AGENCY</code> aparece en 2013, llega a 92 elementos en 2018 y cae a 0 o 1 al
  año desde 2021. Lleva exactamente tres valores — UNESCO, Banco Mundial, UNIDO — así que no
  era una clasificación: era un acuerdo de cofinanciación concreto.</span></div>
 <div class="ev key"><b>2022 — alguien vuelve a llenarlo, a mano</b><span>Tres campos suben
  JUNTOS de ~20% a 50% de los elementos nuevos, al unísono. Y aparece la bandera
  <code>YYE_POC</code>, puesta por tres personas primero y dos después. Un piloto manual, año y
  medio antes de que existiera la interfaz.</span></div>
 <div class="ev key"><b>15 de diciembre de 2023 — Core Manager escribe su primer PEP</b><span>
  Uno. Luego 6 el día 18, 20 el 19, 36 el 22. El arranque técnico cabe en cuatro días de
  diciembre.</span></div>
 <div class="ev"><b>2024 — el traspaso</b><span>49% de los PEP nuevos en enero, <b>91% en
  febrero</b>, y entre el 80 y el 98% cada mes desde entonces. La gramática de los
  identificadores converge a una sola forma. El maestro deja de escribirlo la
  organización.</span></div>
 <div class="ev"><b>2024-2026 — la meseta</b><span>La cobertura de la clasificación completa
  sube al 26%, 32% y 31% de las raíces extrapresupuestarias nuevas, y ahí se queda. Dos
  tercios siguen llegando sin ella, y no sabemos qué los distingue.</span></div>
</div>
<p class="lesson"><b>Lo que esta historia enseña sobre el modelo, más allá de las fechas.</b>
 Ninguna de las cuatro etapas retiró lo de la anterior, así que el estado actual no es un
 diseño: es una <b>acumulación</b>. Y el cambio decisivo no fue funcional sino de <b>autoría</b>
 — cuando el escritor pasó de ser una persona a ser una interfaz, cambiaron a la vez la
 cobertura, la calidad de los valores y la gramática, sin que nadie tomara ninguna decisión
 sobre ningún campo en concreto.</p>
<p class="honest"><b>Lo que NO está registrado:</b> ninguna de las cuatro transiciones consta
 en ningún artefacto del brain como decisión — ni quién la tomó, ni cuándo, ni por qué. Todo lo
 de arriba está <b>reconstruido de las fechas de creación de los propios datos</b>. Es
 evidencia sólida de QUÉ pasó y ninguna de POR QUÉ.</p>
</div>

<footer>Fuente: <code>brain_v2/project_wbs_model.json</code> (algoritmo A19). Regenerar:
<code>python process_mining/wbs_model.py</code> y luego
<code>python scripts/build_wbs_companion.py</code></footer>
</div></body></html>
