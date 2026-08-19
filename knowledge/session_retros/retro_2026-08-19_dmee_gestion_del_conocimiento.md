# Retro 2026-08-19 — DMEE dirección estructurada, y por qué la gestión del conocimiento falló

**Resultado de la sesión:** el rechazo bancario del 21-jul cerrado y verificado · `ORDER=0` en los
7 árboles vivos · 3 herramientas nuevas · el alcance real de noviembre identificado y acotado.

**Coste:** JP tuvo que corregirme **once veces** sobre hechos, y pedirme **seis** que cargara
conocimiento que ya estaba en disco. Ese es el tema de esta retro.

---

## 1. Lo que pasó, sin adornos

### 1.1 No cargué el dominio, teniendo la regla y la herramienta

`brain_v2/load_domain.py` existe. La regla `feedback_load_the_domain_before_you_reason` (#208,
CRITICAL) existe. **La escribí yo, en esta misma sesión, tres horas antes de volver a violarla.**

Trabajé por sondas: una pregunta, una consulta RFC, una respuesta. Cada respuesta re-derivaba una
foto parcial y omitía en silencio lo que la pregunta no nombraba.

> *"Explicame como mierda va a funcionar el conocimiento no estas cargando nada."*
> *"Pero donde mierda leiste todo el conocimiento de los Companion!!!"*
> *"No veo que lo conozcas."*

Tenía razón. Del companion de 938.592 caracteres había leído cuatro fragmentos.

### 1.2 Leía una columna y daba el nodo por entendido

Sobre `MP_EXIT_FUNC` construí una especificación de cambio entera. Hay **seis** cosas que deciden
el valor de un nodo, y un nodo puede llevar mapping **y** exit a la vez — gana el exit. En
`/CGI_XML_CT_UNESCO` eso son 392 de 628 nodos: **el 62% del árbol era invisible para mí** mientras
yo daba instrucciones sobre él.

Y ni siquiera era el fondo del problema. Aunque leyera el exit, no miraba si había **configuración
detrás** que lo alimentara (`YTFI_PPC_TAG`). Con mi criterio, el estado roto que borró el bloque
del fichero me salía como correcto.

> *"lo que sigo insistiendo y no ves es que estan los codigos de las extensiones para cada elemento"*
> *"Pero eso aplica a todos los arboles y eso es lo que mas me preocupa que desconoces"*

Analizaba 3 árboles. Hay **6 formatos vivos**. La familia italiana —incluida la transfronteriza,
que es la que noviembre golpea más fuerte— no la había abierto nunca.

### 1.3 Medí sin el corte que discrimina — dos veces, en direcciones opuestas

**Sin `DORIGIN`:** miré LFA1+ADRC, dictaminé "99% sano", y **el 35% de las líneas de pago no
aparecía en la foto** porque los receptores de nómina son PERNR y no existen en LFA1. Estuve a
punto de reportar 5.128 "proveedores sin dirección" que no son proveedores.

**Sin `T042Z`:** abrí un incidente **GRAVE** diciendo que 943 empleados no podrían cobrar en
noviembre. Cobran por **cheque**. Un cheque no lleva `<PstlAdr>`. El incidente entero era
inexistente.

**Y filtrando de más:** reporté 941 proveedores afectados porque filtré por el rail CITI. Sin
filtrar son **8.149**. Nueve veces.

### 1.4 Otras correcciones que costaron tiempo

- Comparé el diseño nuevo contra **V002, que es el backup del diseño viejo**, y le dije a JP que
  repusiera unos mappings — llevándolo hacia atrás sobre su propia decisión de usar el exit.
- Le dije que borrara las condiciones de los hijos "para conseguir todo-o-nada". **Falso**:
  borrarlas no consigue nada, el campo vacío no emite igual.
- Pinté condiciones vacías (`IF <> 'X'`) por no leer `ARG1_NODE` y llegué a decirle que las había
  puesto mal. **Estaban bien.**
- Usé *"hoy lo aceptan"* como prueba de conformidad contra una norma con fecha. Su corrección
  —*"hoy no los rechaza porque no esta en vigencia"*— desarmó el argumento entero.
- Mi propio script derivaba el estado desde códigos postales comodín: `DISERA Laurel Anne`, que
  vive en **New York**, se cargaba como **Alaska**.

---

## 2. El diagnóstico

### 2.1 Las reglas no se aplican solas. Las herramientas sí.

Hay **209 feedback rules** en el brain. Hoy fallé contra al menos cinco de ellas, incluida una
CRITICAL escrita por mí horas antes.

Lo que **sí** funcionó fue lo que estaba **dentro de una herramienta**:

- `pain001_address_validator.py` cazó el error de orden y reprodujo offline el mensaje literal del
  banco.
- `dmee_tree_map.py`, una vez que evaluó la configuración PPC, marcó solo el nodo que no emitía.
- El test offline cazó que mi detector de comodines no reconocía `99999-9999` — **64 de los 68
  casos reales**. No lo vi leyendo el código: lo vi ejecutándolo.

**Una regla que exige recordarla no es un mecanismo.** Es una nota.

### 2.2 El corpus en prosa no se lee. El mapa generado sí.

El dominio DMEE tiene 40 documentos, 20 companions, 165 claims, 11 incidentes: **~667K tokens**.
Nadie lee eso, ni yo ni el siguiente. Y aunque se lea, describe el sistema **de cuando se escribió**.

Lo que sí funcionó fue `DMEE_CONFIG_POR_FORMATO.md`: **500 líneas, generadas del sistema, con la
fecha de la medida**. Se lee entero en un minuto y no puede estar desactualizado, porque se
regenera.

Ésa es la forma correcta del conocimiento operativo: **no prosa acumulada, sino un mapa generado
y fechado.** La prosa vale para el porqué; el mapa, para el qué.

### 2.3 Respondí preguntas en vez de entender el sistema

Nunca me senté a entender el modelo DMEE. Lo aprendí **siendo corregido**: que un `TECH` no emite
etiqueta, que los nodos `-XXX` son banderas de supresión a las que apuntan sus hermanos, que el
BAdI tiene dos fuentes, que una condición `campo <> mismo campo` es un interruptor de apagado.

Cada una de esas cosas la aprendí **después** de haber dado una instrucción equivocada que las
ignoraba.

---

## 3. Qué cambiar

### 3.1 El mapa antes que la respuesta

**Ante una pregunta sobre un sistema configurado, construir o refrescar su mapa completo antes de
responder.** No la parte que la pregunta toca: el mapa.

Cuesta una ejecución y evita la cadena entera de respuestas parciales. Medido hoy: el mapa de los
7 árboles tardó **90 segundos** y encontró tres defectos que ninguna de mis sondas había visto,
incluido el orden roto de SEPA que llevaba meses latente.

→ regla `feedback_build_the_map_before_answering`

### 3.2 Declarar los cortes antes de medir

**Toda medida sobre una tabla transaccional declara primero sus dimensiones discriminantes.** En
pagos son tres, y omitir cualquiera inventa un problema o esconde otro:

```
DORIGIN   quien cobra        -> cada origen tiene su fuente de verdad
T042Z     por donde sale     -> FORMI = fichero, XSCHK = cheque
rail      contra que regla   -> los bancos no piden lo mismo
```

Ya están escritos en la cabecera de `structured_address_readiness.py`, con el error que costó cada
uno.

→ regla `feedback_declare_the_cuts_before_measuring`

### 3.3 Toda herramienta reutilizable, con test offline

El test de hoy tardó cinco minutos y cazó un bug que habría cargado datos falsos en el maestro de
proveedores. **Los casos del test son errores reales, no ejemplos inventados** — así el test
documenta la trampa además de vigilarla.

→ regla `feedback_reusable_tools_carry_offline_tests`

### 3.4 Convertir reglas en mecanismos, y dejar de añadir reglas

209 reglas es más de lo que se puede aplicar. La propuesta concreta: **por cada regla nueva que se
añada, convertir una vieja en comprobación ejecutable o retirarla.** Las que hoy me habrían salvado
son mecanizables:

| Regla | Mecanismo |
|---|---|
| `load_the_domain_before_you_reason` | El hook de arranque ya existe. Que **exija** el mapa del dominio cuando se nombra un tema |
| `verify_before_alarming` | El validador ya lo hace para ficheros. Extenderlo a "antes de abrir un incidente, medir el canal" |
| `label_inferred_vs_measured` | Columna `confianza` obligatoria en todo CSV que proponga un valor — como el de FIX B |

---

## 4. Lo que sí funcionó, para no perderlo

**JP cortando en seco.** Cada corrección suya fue exacta y cambió el trabajo: *"esa configuracion
no la estas evaluando"*, *"hoy no los rechaza porque no esta en vigencia"*, *"el incidente separa
el fix entre Proveedores y Empleados"*. Ninguna era de estilo; todas eran de fondo.

**Medir en vez de opinar.** Todo lo que sobrevivió de esta sesión tiene un número detrás y la
consulta que lo produjo. Lo que no lo tenía, se cayó — incluidas tres recomendaciones mías.

**Escribir lo descartado con la medida que lo descartó.** El registro de errores vale más por sus
descartes que por sus abiertos: la campaña de limpieza de BNKA, la nómina, los híbridos. Sin esa
medida escrita, la próxima sesión los reabre.
