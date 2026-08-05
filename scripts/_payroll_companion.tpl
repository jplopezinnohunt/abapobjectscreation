<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Nómina end-to-end — UNESCO SAP · el motor, las compuertas y el posting</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--un-blue:#0079c1;--un-dark:#1a3a5c;--un-grey:#5a6c84;--bg:#f5f7fa;--card:#fff;
 --border:#dde3eb;--ok:#2c8b50;--bad:#c93a3a;--warn:#dd6b20}
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
 color:var(--un-dark);background:var(--bg)}
.container{max-width:1280px;margin:0 auto;padding:0 18px 60px}
header{background:linear-gradient(135deg,#0079c1,#1a3a5c);color:#fff;padding:34px 0 30px;margin-bottom:26px}
header .container{padding-bottom:0}
h1{margin:0 0 6px;font-size:27px;font-weight:600}
.sub{opacity:.92;font-size:15px;max-width:920px}
.meta{margin-top:14px;font-size:12px;opacity:.75}
h2{font-size:19px;margin:34px 0 12px;padding-bottom:7px;border-bottom:2px solid var(--border)}
h3.camph{font-size:13px;letter-spacing:.05em;color:var(--un-grey);margin:22px 0 10px;
 border-left:4px solid var(--un-blue);padding-left:9px}
code{background:#eef2f7;padding:1px 5px;border-radius:3px;font-size:12.5px}
.note{font-size:12.5px;color:var(--un-grey)}
.orient{background:#fff;border:1px solid var(--border);border-left:5px solid var(--un-blue);
 border-radius:6px;padding:6px 20px 18px;margin-bottom:8px}
.honest{background:#eef2f7;border-radius:5px;padding:10px 13px;font-size:12.5px;color:var(--un-grey)}
ol.trap{font-size:13.5px;padding-left:20px}
ol.trap li{margin:9px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--border);border-top:3px solid var(--un-blue);
 border-radius:6px;padding:13px 15px}
.kpi b{display:block;font-size:23px;color:var(--un-blue)}
.kpi span{font-size:12px;color:var(--un-grey)}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{background:#eef2f7;font-size:11.5px;letter-spacing:.05em;color:var(--un-grey)}
table.det{font-size:12px}
td.num{text-align:right;color:var(--un-grey);white-space:nowrap}
td.n{text-align:right;font-weight:700;color:var(--un-blue);white-space:nowrap}
td.md{color:var(--un-grey);font-size:11.5px}
tr.cust td:first-child code{background:#e8f4ea;color:var(--ok);font-weight:700}
tr.bad td{background:#fdecec}
.scroll{overflow-x:auto}
.lesson{background:#fff8ef;border-left:4px solid var(--warn);padding:11px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
.warn{background:#fdecec;border-left:4px solid var(--bad);padding:12px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
.names{line-height:2.1}
.repro{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--ok);
 border-radius:6px;padding:12px 15px;margin-bottom:11px}
.repro .rh{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.repro .rh b{font-size:14px}
.repro .rh span{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;font-weight:700;color:var(--un-blue)}
.repro pre{margin:0;background:#1a3a5c;color:#e8eef5;padding:11px 13px;border-radius:4px;
 font-size:11.5px;line-height:1.45;overflow-x:auto;white-space:pre}
.repro .cav{margin-top:8px;font-size:12.5px;color:var(--un-grey)}
.chain{display:flex;flex-direction:column}
.chain .step{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--un-blue);
 border-radius:5px;padding:10px 14px}
.chain .step b{display:block;font-size:13px}
.chain .step span{font-size:12.5px;color:var(--un-grey)}
.chain .lnk{padding:5px 0 5px 22px;border-left:2px dashed var(--border);margin-left:14px;
 font-size:12px;color:var(--un-grey)}
footer{margin-top:40px;font-size:12px;color:var(--un-grey);border-top:1px solid var(--border);padding-top:14px}
</style></head><body>
<header><div class="container">
<h1>Nómina end-to-end</h1>
<div class="sub">La nómina calcula el mayor gasto de la organización en una capa que <b>no es
 ABAP ni son datos</b>: esquemas, reglas, wage types y features. Un <i>grep</i> no la alcanza y
 una búsqueda de tablas no la reconoce. Fue invisible en este brain hasta que una pregunta
 sobre el budget rate forzó la puerta.</div>
<div class="meta"><b>Cifras y tablas: GENERADAS</b> de <code>brain_v2/payroll_discovery.json</code>
 en cada build — no pueden derivar. <b>La interpretación está ESCRITA</b> en
 <code>scripts/build_payroll_companion.py</code>: si el modelo cambia, hay que reescribirla.
 Nunca editar el HTML.</div>
</div></header>
<div class="container">

<div class="orient">
<h2 style="border:0;margin-top:6px">0 · Si no conoces nada de esto, empieza aquí</h2>
<p><b>Qué es esta capa.</b> Un <b>esquema</b> es la receta de cálculo: una lista ordenada de
 pasos que llaman a otros esquemas y a <b>reglas</b>. Una <b>regla</b> es una mini-decisión
 sobre un importe. Un <b>wage type</b> es cada concepto que entra o sale — salario base,
 subsidio, retención. Y una <b>feature</b> es un árbol de decisión que devuelve un valor según
 el perfil del empleado.</p>
<p><b>Por qué nada de lo que sueles buscar la encuentra.</b> Nada de eso vive en un programa
 ABAP ni en una tabla de negocio: vive en tablas de configuración con nombres como
 <code>T52C1</code>, <code>T52C5</code>, <code>T512T</code>, <code>T549D</code>. Buscar el
 nombre de un mecanismo en el código no da nada — <b>porque el mecanismo no tiene nombre en el
 código</b>.</p>
<div class="kpis">
 <div class="kpi"><b>@SCHEMAS@</b><span>esquemas, <b>@CUSTSCHEMAS@ custom</b></span></div>
 <div class="kpi"><b>@RULES@</b><span>reglas, @CUSTRULES@ custom</span></div>
 <div class="kpi"><b>@WT@</b><span>wage types</span></div>
 <div class="kpi"><b>@FEAT@</b><span>features, <b>@CUSTFEAT@ custom</b></span></div>
 <div class="kpi"><b>@RULELINES@</b><span>líneas de regla</span></div>
</div>
<p class="honest"><b>Lo que NO está registrado:</b> por qué el diseño es así. Dos tercios de
 los esquemas son custom y no consta ninguna decisión que lo justifique. Lo de abajo describe
 lo que el sistema HACE, leído de su configuración y sus documentos. El porqué hay que
 preguntárselo a la organización.</p>

<h2 style="border:0">0b · Las cuatro trampas, cada una aprendida cayendo en ella</h2>
<ol class="trap">
 <li><b>Lo configurado no es lo que corre.</b> 72 wage types «Constant Dollar» están
  configurados de forma idéntica y <b>ninguno postea</b>. Una tabla de configuración no puede
  informar de que su propio contenido está dormido: hay que contrastarla contra los documentos
  que debería producir.</li>
 <li><b>El 89% del detalle era simulación.</b> Un run de posting escribe documentos sea real o
  no, y nada en la fila lo distingue. Sumarlo sin filtrar dio una cifra <b>nueve veces</b> más
  alta. El discriminador estaba a una tabla de distancia: si el run produjo documento
  contable.</li>
 <li><b>El vacío de un campo depende de su tipo.</b> Un campo numérico nunca está en blanco —
  vale cero— así que una prueba de «no vacío» lo cuenta como lleno. Diez campos parecían llenos
  al 100% y uno estaba al 0,45%.</li>
 <li><b>FI resume varias posiciones de nómina en una.</b> Una línea de <code>PPDIT</code> de
  46,80 son 10,96 + 35,84 de <code>PPOIX</code>. El join multiplica: hay que agregar del lado
  cuya granularidad quieres, nunca a través.</li>
</ol>
</div>

<h2>1 · El motor — los esquemas y a quién llaman</h2>
<p class="note">Un esquema llama a otros, y <b>esa lista de llamadas ES el flujo</b>. Ordenados
 por pasos activos, que es donde se concentra la lógica. En verde los custom.</p>
<div class="scroll"><table class="det"><tr><th>esquema</th><th>activos</th><th>pasos</th>
<th>llama a</th><th>a quién</th></tr>@EROWS@</table></div>

<h2>2 · La lógica — dónde está la masa custom</h2>
<p class="note">De @RULES@ reglas, @CUSTRULES@ son custom. Pero el tamaño importa más que el
 número: una regla de 224 líneas es un programa disfrazado.</p>
<div class="scroll"><table class="det" style="max-width:420px"><tr><th>regla</th>
<th>líneas</th></tr>@LROWS@</table></div>

<h2>3 · La salida — las familias que SON un mecanismo</h2>
<p class="note">@LESSON@</p>
<div class="scroll"><table class="det"><tr><th>familia</th><th>miembros</th>
<th>frases en su texto</th></tr>@FROWS@</table></div>
<p class="lesson">La familia <code>9*</code> es el caso: 99 miembros de los que <b>72 dicen
 «Constant Dollar»</b>. Ni el esquema ni el texto de las reglas la nombran nunca. Así apareció
 el budget rate de personal — buscando desde la SALIDA hacia atrás, no desde el driver hacia
 delante.</p>

<h2>4 · Las compuertas — las @CUSTFEAT@ features custom, nombradas</h2>
<p class="note">Una feature es un perímetro que ninguna búsqueda de código o de tablas
 encuentra. <code>YYCDR</code> es la que decide qué empleados entran en el budget rate de
 personal: 2.086 de 23.700.</p>
<div class="names">@GNAMES@</div>
<p class="lesson">@HOWREAD@</p>

<h2>5 · El maestro, y CÓMO se mantiene</h2>
<p class="note">El hallazgo no es el volumen: es la proporción de cambios <b>sin transacción</b>.
 Esos no vienen de una persona en una pantalla, vienen de un programa o una interfaz. En rojo,
 por encima del 40%.</p>
<div class="scroll"><table class="det"><tr><th>objeto</th><th>con transacción</th>
<th>SIN transacción</th><th>%</th><th>transacciones principales</th></tr>@MROWS@</table></div>
<p class="note"><code>PA0001</code> —la asignación organizativa sobre la que deciden las
 features— tiene @PA0001@ filas en el golden.</p>

<h2>6 · El posting — los enhancements sobre el camino</h2>
<p class="note">Todos custom, y concentrados en <code>RPCIPE00</code> y
 <code>RPCIPE00_OLD</code>. <code>ZHR_POSTING_ACCOUNTS_RETRO</code> lleva el nombre de la
 determinación de cuentas: ahí viviría cualquier desviación local del estándar.</p>
<div class="scroll"><table class="det"><tr><th>enhancement</th><th>tipo</th>
<th>objeto enganchado</th></tr>@PROWS@</table></div>

<h2>7 · La cadena — del wage type a la cuenta de mayor</h2>
<div class="chain">
 <div class="step"><b>PPOIX</b><span>el índice por empleado: lleva <code>LGART</code> (wage
  type), <code>BETRG</code> (importe) y <code>KOMOK</code> (la cuenta simbólica de 4
  caracteres)</span></div>
 <div class="lnk">↓ <code>TSLIN</code> = <code>LINUM</code></div>
 <div class="step"><b>PPDIX</b><span>el índice de documento: <code>RUNID</code>+<code>LINUM</code>
  → <code>DOCNUM</code>+<code>DOCLIN</code></span></div>
 <div class="lnk">↓ <code>DOCNUM</code> + <code>DOCLIN</code></div>
 <div class="step"><b>PPDIT</b><span>las posiciones: <code>KTOSL</code> (la clave de operación
  de FI, 3 caracteres) y <code>HKONT</code> (la cuenta de mayor resuelta), más
  <code>FISTL</code>/<code>GEBER</code>, la imputación de FM</span></div>
 <div class="lnk">↓ <code>AWKEY</code> = <code>DOCNUM</code>, <code>AWTYP='HRPAY'</code></div>
 <div class="step"><b>BKPF</b><span>el documento contable. Solo llegan aquí los runs
  reales</span></div>
</div>
<h3 class="camph">Dónde aterriza: @RESROWS@ posiciones reales</h3>
<p class="note">Una clave de operación abre a varias cuentas, pero <b>@RESONE@ de @RESACC@
 cuentas pertenecen a UNA sola clave</b>. Uno-a-muchos ida, uno-a-uno vuelta: la cuenta se
 decide <b>más allá</b> de la clave — la clave viene del maestro del empleado, la cuenta del
 wage type.</p>
<div class="scroll"><table class="det"><tr><th>clave FI</th><th>cuentas</th>
<th>cuáles</th></tr>@KROWS@</table></div>
<div class="warn"><b>Por qué la búsqueda por configuración no podía funcionar:</b>
 <code>T030-KTOSL</code> es CHAR(3) y una cuenta simbólica de nómina es CHAR(4). Son dos claves
 distintas con el mismo nombre de campo, y unirlas es imposible por construcción. Tres
 extracciones lo persiguieron antes de que medir los dos anchos terminara la línea en una
 llamada.</div>

<h2>8 · Las simulaciones — el 89% del detalle</h2>
<p class="note">De 2.316 runs de nómina de 2026, <b>488 están enteros en FI y 1.828 enteros
 fuera. Cero parciales.</b> Un run transfiere entero o no transfiere, así que los 1.828 son
 simulaciones — y ninguno de sus 89.420 documentos aparece en <code>bkpf</code> bajo ningún
 <code>AWTYP</code>.</p>
<div class="warn">El golden se <b>purgó</b> a lo final: <code>ppoix</code> 12.795.641 →
 1.302.607, <code>ppdix</code> 4.165.836 → 444.886, <code>ppdit</code> 4.046.412 → 434.681. De
 21,0 a 2,18 millones de filas. <code>PPDHD</code> <b>no</b> se purgó a propósito: es la
 evidencia de que las simulaciones existieron, y <code>bkpf</code> solo cubre 2024-2026, así
 que el discriminador no puede juzgar sus runs antiguos.</div>

<h2>9 · Cómo reproducir cada cifra</h2>
<p class="note">Cada consulta <b>se ejecutó contra el golden y devolvió el número que tiene al
 lado</b>. Base: <code>Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db</code>,
 procedencia P01, solo lectura.</p>

<div class="repro"><div class="rh"><b>Los 67 esquemas y cuáles son custom</b><span>67 · 45 custom</span></div>
<pre>SELECT SCHEM, COUNT(*) pasos,
       SUM(CASE WHEN DELET&lt;&gt;'*' THEN 1 ELSE 0 END) activos
FROM T52C1 GROUP BY SCHEM ORDER BY activos DESC;</pre>
<div class="cav">Custom = el nombre empieza por Y o Z. <code>DELET='*'</code> marca el paso
 desactivado, y contarlos como activos infla el tamaño del esquema.</div></div>

<div class="repro"><div class="rh"><b>Las 19 features custom</b><span>19 de 2.888</span></div>
<pre>SELECT NAMEN, STRUC FROM T549D
WHERE substr(NAMEN,1,1) IN ('Y','Z') ORDER BY NAMEN;</pre>
<div class="cav">Para LEER una feature hace falta su programa generado:
 <code>/1PAPA/FEAT&lt;mandante&gt;&lt;NOMBRE&gt;</code>, vía <code>RPY_PROGRAM_READ</code>. El
 árbol que se mantiene en PE03 no es invisible — simplemente no está donde nadie mira.</div></div>

<div class="repro"><div class="rh"><b>La familia Constant Dollar</b><span>72</span></div>
<pre>SELECT LGART, LGTXT FROM T512T
WHERE SPRSL='E' AND MOLGA='UN'
  AND upper(LGTXT) LIKE '%CONSTANT DOLLAR%';</pre>
<div class="cav">Buscar por el TEXTO y no por el código es lo que la encuentra. Los 72
 comparten el stem <code>9</code> pero el stem solo no los separa de los otros 27 de esa
 familia.</div></div>

<div class="repro"><div class="rh"><b>Cuántos de esos postean de verdad</b><span>0</span></div>
<pre>SELECT COUNT(DISTINCT LGART) FROM ppoix WHERE LGART IN (
  SELECT LGART FROM T512T WHERE SPRSL='E' AND MOLGA='UN'
  AND upper(LGTXT) LIKE '%CONSTANT DOLLAR%');</pre>
<div class="cav">La pareja de consultas ES el hallazgo. Ninguna de las dos sola dice nada, y
 la primera sola dice algo falso.</div></div>

<div class="repro"><div class="rh"><b>Runs simulados contra posteados</b><span>2.316 · 488</span></div>
<pre>SELECT COUNT(DISTINCT h.RUNID),
       COUNT(DISTINCT CASE WHEN k.BELNR IS NOT NULL THEN h.RUNID END)
FROM ppdhd h LEFT JOIN bkpf k ON k.AWKEY=h.DOCNUM AND k.AWTYP='HRPAY'
WHERE substr(h.BUDAT,1,4)='2026';</pre>
<div class="cav">Solo vale donde <code>bkpf</code> tiene cobertura — 2024 a 2026. Fuera de ahí
 todo run parece simulación y no lo es.</div></div>

<div class="repro"><div class="rh"><b>Cadena entera hasta el wage type</b><span>solo 999S</span></div>
<pre>SELECT DISTINCT o.LGART, o.KOMOK, t.KTOSL, t.HKONT
FROM ppdit t
JOIN ppdix x ON x.DOCNUM=t.DOCNUM AND x.DOCLIN=t.DOCLIN
JOIN ppoix o ON o.RUNID=x.RUNID AND o.TSLIN=x.LINUM
WHERE ltrim(t.HKONT,'0') LIKE '999%';</pre>
<div class="cav">Para SUMAR por aquí hay que elegir el lado: el join multiplica porque FI
 resume varias posiciones de nómina en una.</div></div>

<div class="repro"><div class="rh"><b>Mantenimiento del maestro por vía</b><span>hasta 46,1% sin transacción</span></div>
<pre>SELECT OBJECTCLAS, TCODE, COUNT(*)
FROM cdhdr WHERE OBJECTCLAS LIKE 'HR_IT%'
GROUP BY OBJECTCLAS, TCODE ORDER BY 3 DESC;</pre>
<div class="cav">Un <code>TCODE</code> vacío no es un dato que falte: significa que el cambio
 NO vino de un diálogo. Es la señal de una interfaz o un programa, y es lo que hay que
 explicar.</div></div>

<footer>Fuente: <code>brain_v2/payroll_discovery.json</code> (algoritmo A16, siete partes) ·
<code>brain_v2/claims/claims.json</code>. Regenerar:
<code>python scripts/build_payroll_companion.py</code></footer>
</div></body></html>
