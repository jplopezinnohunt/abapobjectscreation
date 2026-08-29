# Oportunidades, riesgos y desafíos — lo que los mineros encuentran

> **GENERADO.** No editar a mano: `python scripts/build_oportunidades.py` lo reescribe del bus `process_mining/mining_findings.json`. Última generación: **2026-08-29**.

> Cada corrida de un minero **reemplaza lo suyo**, así que lo que desaparece de aquí es lo que dejó de encontrarse — y eso también es información.

**28 hallazgos vivos** de 13 mineros: 🔴 RIESGO 6 · 🟠 DESAFIO 10 · 🟢 OPORTUNIDAD 4 · ⚪ DATO 8


⚠️ **10 desafíos esperan que alguien conteste.** Un desafío no es un fallo ni una mejora: es una pregunta que el minero no puede resolver solo, y el minero es quien mejor puede formularla porque tiene los datos delante.


---

## 🔴 RIESGO (6)

*puede hacer daño si nadie actúa · va a quien responde del control*


### Cuentas VIVAS sin ningun extracto bancario: nada corrobora lo que el banco dice

- **Tamaño:** 12 cuentas vivas, 1 de ellas de sociedades distintas de UNES
- **Evidencia:** cero cabeceras en FEBKO en toda la ventana
- **No se puede ver:** no se si MUEVEN dinero: eso lo mide bank_account_behaviour_signature. Sin cruzarlo, esto es una lista, no un riesgo dimensionado
- **Acción:** cruzar con behaviour_signature antes de escalar
- ***1 días abierto** · lo encuentra `bank_statement_channel_census` · P01 · 20250101 -> hoy*
- <sub>denominador: 402 cuentas de banco casa; 237 excluidas por llevar CLOSED en T012T-TEXT1 (no hay campo de estado: es una convencion humana); quedan 165 vivas</sub>

### El extracto TECLEADO mete una persona en el eslabon de ENTRADA, donde el canal automatico no tiene ninguna (JOBBATCH)

- **Tamaño:** 34 cuentas VIVAS reciben algun extracto tecleado (8 de ellas al 100%) · 40 usuarios con nombre lo hacen · las mas tecleadas: UNES/BLN01-SDD01 100%, UNES/BLN01-USD01 100%, UNES/BMN01-CUP02 100%, UNES/BMN01-EUR01 100%, UNES/BTE01-EUR01 100%
- **Evidencia:** FEBKO.EUSER de esas cuentas
- **No se puede ver:** solo veo QUIEN teclea. Si esa misma persona ademas contabiliza o compensa el documento resultante (BKPF.USNAM) o emite pagos (REGUH), eso NO lo mide este minero
- **Acción:** cruzar EUSER contra BKPF.USNAM y REGUH de la misma cuenta
- ***1 días abierto** · lo encuentra `bank_statement_channel_census` · P01 · 20250101 -> hoy*
- <sub>denominador: 402 cuentas de banco casa; 237 excluidas por llevar CLOSED en T012T-TEXT1 (no hay campo de estado: es una convencion humana); quedan 165 vivas</sub>

### TODAS las cuentas de mandato de inversion carecen de extracto bancario, y aun asi se presentan en el balance como Cash and Cash Equivalents

- **Tamaño:** 4 de 4 cuentas de mandato
- **Evidencia:** cero FEBKO y posicion FS10 = 1.1.1.1 Cash with Banks
- **No se puede ver:** la pata de EFECTIVO de un mandato de custodia es legitimamente efectivo: NO se afirma error contable
- **Acción:** preguntar a Finanzas: si el saldo es efectivo, por que no llega extracto
- ***1 días abierto** · lo encuentra `bank_account_nature_model` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS (excluidas las marcadas CLOSED en el texto)</sub>

### Cuentas que MUEVEN SALDO sin recibir ni un extracto bancario: nada corrobora el movimiento

- **Tamaño:** 3 cuenta(s), UNES/NTB01-USD04 2 periodos; UNES/NTB01-USD05 4 periodos; UNES/NTB01-USD06 2 periodos
- **Evidencia:** GLT0 con movimiento y cero cabeceras en FEBKO
- **No se puede ver:** no se si el banco emite extracto y no llega, o no lo emite
- **Acción:** reclamar el extracto al banco o declarar por que no aplica
- ***1 días abierto** · lo encuentra `bank_account_behaviour_signature` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS (excluidas las marcadas CLOSED en el texto)</sub>

### El que TECLEA el extracto de una cuenta que paga es tambien el que EMITE el dinero por ella: no queda ningun tercero en el circuito SAP

- **Tamaño:** 316 pagos de 1085 (29%) y 888672.99 USD de 3853131.79 (23%), emitidos por alguien que ademas teclea y contabiliza el extracto de ESA cuenta. 13 personas, 13 cuentas.
- **Evidencia:** FEBKO.EUSER × FEBEP.BELNR→BKPF.USNAM × REGUH.VBLNR→BKPF.USNAM × PAYR.PRIUS
- **No se puede ver:** la firma FISICA del cheque prenumerado (dos firmas) NO esta en SAP: este instrumento mide CONCENTRACION DE CONTROL, no ausencia de control ni fraude
- **Acción:** declarar por cuenta quien teclea y quien paga, y que no sean la misma persona; o documentar el control fisico compensatorio
- ***1 días abierto** · lo encuentra `bank_statement_sod_check` · P01 · 20250101 → hoy*
- <sub>denominador: cuentas de UNES que reciben AL MENOS un extracto tecleado a mano: 38, de las que 33 estan vivas (el resto llevan CLOSED en T012T-TEXT1). NO es la etiqueta de canal MANUAL, que solo cubre 8.</sub>

### REGUP_SCENARIOS NO es una copia de REGUP: es una UNION DE ESCENARIOS, y la columna que dice de que escenario viene cada fila nunca se guardo. Por construccion no puede tener clave unica, asi que su delta es imposible tal como esta

- **Tamaño:** 207.779 filas para 205.708 claves SAP COMPLETAS (LAUFD+LAUFI+XVORL+ZBUKR+LIFNR+KUNNR+EMPFG+VBLNR+BELNR+BUZEI+GJAHR). Las que colisionan comparten TODA la clave y difieren solo en el IMPORTE: 1310.60 / 3868.81 / 0.00 para la misma
- **Evidencia:** tras deduplicar 2.301 copias byte a byte y anadir XVORL, KUNNR y EMPFG desde P01, el indice unico sigue sin poder crearse. Volcado de las filas en colision: solo difiere WRBTR
- **No se puede ver:** no he confirmado con quien la creo que la union sea intencionada. Lo que esta MEDIDO es que hay filas con la clave SAP completa repetida y distinto importe, y eso no puede pasar en REGUP de verdad
- **Acción:** decidir que se quiere: (a) dejarla como esta y aceptar que no tiene delta -- se refresca por barrido y se DICE; o (b) extraer REGUP de verdad a una tabla propia con su clave, y dejar REGUP_SCENARIOS como lo que es, un derivado de simulacion. Mientras tanto va 121 dias por detras del resto de la cadena del pago
- **Puede contestarlo:** DBS
- ***hoy** · lo encuentra `gold_delta/REGUP_SCENARIOS (s109)` · Golden · LAUFD 2016-2026*
- <sub>denominador: las 207.779 filas de REGUP_SCENARIOS tras deduplicar</sub>

---

## 🟠 DESAFIO (10)

*no cuadra y el minero no puede resolverlo solo · **necesita que alguien conteste***


### Cuentas manuales que llevan meses sin extracto sin que nada lo detecte: no se si es un incumplimiento o si la cuenta dejo de usarse y nadie lo declaro

- **Tamaño:** UNES/BTE01-EUR01 369 dias; UNES/BTE01-USD01 260 dias; UNES/CIT03-USD02 182 dias; UNES/ECO08-ZWG01 157 dias
- **Evidencia:** ultimo FEBKO.AZDAT frente al ritmo propio de cada cuenta
- **No se puede ver:** NO existe en ninguna parte del sistema un responsable declarado ni una cadencia esperada por cuenta. Se deduce del log, a posteriori
- **Acción:** preguntar a: Tesoreria (BFM/MO) y la oficina de terreno de cada cuenta
- **Puede contestarlo:** Tesoreria (BFM/MO) y la oficina de terreno de cada cuenta
- ***1 días abierto** · lo encuentra `bank_statement_channel_census` · P01 · 20250101 -> hoy*
- <sub>denominador: 402 cuentas de banco casa; 237 excluidas por llevar CLOSED en T012T-TEXT1 (no hay campo de estado: es una convencion humana); quedan 165 vivas</sub>

### No se puede distinguir 'este banco no manda extracto' de 'se dejo de hacer'

- **Tamaño:** 12 cuentas vivas sin extracto y sin declaracion de si les corresponde
- **Evidencia:** T012K vivas con cero FEBKO; la unica marca de estado es CLOSED en el texto
- **No se puede ver:** el formulario de alta YA pregunta '¿extracto electronico? si/no' y esa respuesta no se guarda en ninguna parte del sistema
- **Acción:** preguntar a: Tesoreria: declarar por cuenta si se espera extracto y por que canal
- **Puede contestarlo:** Tesoreria: declarar por cuenta si se espera extracto y por que canal
- ***1 días abierto** · lo encuentra `bank_statement_channel_census` · P01 · 20250101 -> hoy*
- <sub>denominador: 402 cuentas de banco casa; 237 excluidas por llevar CLOSED en T012T-TEXT1 (no hay campo de estado: es una convencion humana); quedan 165 vivas</sub>

### Cuentas que recibian con regularidad y llevan dias mudas mientras su sociedad sigue recibiendo: no se si el banco dejo de mandar o si nadie lo procesa

- **Tamaño:** 8 cuenta(s): UNES/BLN01-SDD01; UNES/BLN01-USD01; UNES/BMN01-EUR01; UNES/BMN01-CUP02; UNES/CIT03-RUB02; UNES/SOG06-HTG01
- **Evidencia:** ultimo FEBKO.AZDAT frente al maximo de su sociedad
- **No se puede ver:** no puedo ver el directorio del banco desde aqui
- **Acción:** preguntar a: Tesoreria (BFM/MO) y el equipo de interfaces
- **Puede contestarlo:** Tesoreria (BFM/MO) y el equipo de interfaces
- ***1 días abierto** · lo encuentra `house_bank_ebs_wiring_check` · P01 · 2025-2026*
- <sub>denominador: 402 cuentas T012K; se excluyen las CERRADAS (marca CLOSED en T012T-TEXT1: 237 de 411 con texto) y las de extracto MANUAL, que no necesitan T028B</sub>

### La NATURALEZA de la cuenta no esta declarada en ninguna parte del sistema: se deduce del texto libre, y en la mayoria no hay ni texto reconocible

- **Tamaño:** 139 de 165 cuentas vivas sin ninguna senal (84%)
- **Evidencia:** ni pertenencia a un set YBANK ni palabra reconocible en T012T
- **No se puede ver:** YBANK clasifica geografia x divisa, no naturaleza; SKB1-FDLEV es binario; y el balance mete todas las cuentas en Cash with Banks
- **Acción:** preguntar a: Tesoreria: declarar el vocabulario y extender YBANK
- **Puede contestarlo:** Tesoreria: declarar el vocabulario y extender YBANK
- ***1 días abierto** · lo encuentra `bank_account_nature_model` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS (excluidas las marcadas CLOSED en el texto)</sub>

### Cuentas de la MISMA naturaleza no coinciden en su configuracion: o es una regla que nadie escribio, o es deriva

- **Tamaño:** 11 combinaciones naturaleza x elemento sin consenso: A_LA_VISTA/BNKN2 29%, MANDATO_INVERSION/T028B 75%, MANDATO_INVERSION/BNKN2 25%, MANDATO_INVERSION/IBAN 25%, MANDATO_INVERSION/OBA1 75%, OPERATIVA/IBAN 80%, SIN_CLASIFICAR/T035D 81%, SIN_CLASIFICAR/BNKN2 38%
- **Evidencia:** porcentaje de cuentas del grupo que tienen el elemento
- **No se puede ver:** no se cual de las dos es sin preguntar: el dato no lo distingue
- **Acción:** preguntar a: Tesoreria / DBS: decidir si es regla o deriva
- **Puede contestarlo:** Tesoreria / DBS: decidir si es regla o deriva
- ***1 días abierto** · lo encuentra `bank_config_profile_by_nature` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS de todas las sociedades</sub>

### Cuentas VIVAS que no pagan, no reciben y no mueven: no se si estan cerradas de hecho y nadie lo declaro

- **Tamaño:** 9 cuentas: UIL/DEU01-EUR02, UNES/BRA01-BRL01, UNES/BRA01-BRL02, UNES/CBE01-ETB02, UNES/DEU01-EUR01, UNES/DEU02-EUR01, UNES/NTB02-EUR02, UNES/UBS02-CHF01
- **Evidencia:** cero en los tres ejes durante toda la ventana
- **No se puede ver:** 'CLOSED' en el texto es la unica marca de estado y estas no la llevan
- **Acción:** preguntar a: Tesoreria: cerrarlas o declarar por que siguen abiertas
- **Puede contestarlo:** Tesoreria: cerrarlas o declarar por que siguen abiertas
- ***1 días abierto** · lo encuentra `bank_account_behaviour_signature` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS (excluidas las marcadas CLOSED en el texto)</sub>

### El censo de canales publica UNA persona por cuenta manual; medido son hasta 5 por cuenta y 41 en total, y 31 de las 39 cuentas afectadas no estan etiquetadas MANUAL. Dos medidas del mismo objeto no coinciden

- **Tamaño:** 39 cuentas vs 8 publicadas · 41 personas vs 4 publicadas · 13.942 lineas tecleadas vs 1.712 publicadas
- **Evidencia:** FEBKO.EFART='M' agrupado por cuenta y EUSER, frente a channel_census.json campo 'quien' (solo el usuario mas frecuente)
- **No se puede ver:** el log dice quien lo hizo, nunca quien DEBIA hacerlo
- **Acción:** corregir el denominador del censo: la poblacion es 'recibe algun extracto tecleado', no 'esta etiquetada MANUAL'
- **Puede contestarlo:** BFM/TRS (Baizid Gazi, Anssi Yli-Hietanen) + DBS
- ***1 días abierto** · lo encuentra `bank_statement_sod_check` · P01 · 20250101 → hoy*
- <sub>denominador: cuentas de UNES que reciben AL MENOS un extracto tecleado a mano: 38, de las que 33 estan vivas (el resto llevan CLOSED en T012T-TEXT1). NO es la etiqueta de canal MANUAL, que solo cubre 8.</sub>

### ¿Existe el escenario de ONE-TIME PAYER en UNESCO, y como se identifica? Se busco y NO aparece: las filas sin proveedor no son perceptores ocasionales

- **Tamaño:** 0 de 78.122 filas sin LIFNR tienen PERNR; ninguna encaja con el patron CPD clasico (que llevaria LIFNR de cuenta colectiva). 317.769 filas SI traen NAME1 junto a un LIFNR relleno, que seria el sitio donde mirar si el escenario existe
- **Evidencia:** REGUH: LIFNR, PERNR, NAME1/STRAS/ORT01 y DORIGIN, 2025-2026
- **No se puede ver:** pregunta de JP, marcada por el como escenario IMPORTANTE. Buscado, no encontrado -- lo que no prueba que no exista
- **Acción:** confirmar con BFM si UNESCO paga alguna vez a un perceptor sin ficha, y por que via
- **Puede contestarlo:** BFM/TRS
- ***hoy** · lo encuentra `pregunta abierta (s109)` · Golden (procedencia P01) · LAUFD 2025-2026*
- <sub>denominador: las 577.103 filas de REGUH con LAUFD >= 20250101</sub>

### Las PROPUESTAS de pago sin proveedor se cortan en 2026-03, pero REGUH tiene datos hasta 2026-05. O no hubo propuestas en abril y mayo, o falta dato

- **Tamaño:** 2025-01 a 2026-03, con picos en 2025-11 (16.438), 2025-12 (12.332) y 2026-01 (16.360) -- cierre de ejercicio. Cero en 2026-04 y 2026-05. En total REGUH tiene 358.106 propuestas en 2024-2026, ~10% de la tabla
- **Evidencia:** REGUH XVORL='X' agrupado por mes de LAUFD; marca de agua de REGUH en LAUFD <= 20260512
- **No se puede ver:** no se si las propuestas se BORRAN al ejecutarse, en cuyo caso su ausencia reciente seria lo normal y no un hueco
- **Acción:** preguntar a BFM si una propuesta sobrevive a su ejecucion; si no sobrevive, esto no es un hallazgo
- **Puede contestarlo:** BFM/TRS
- ***hoy** · lo encuentra `pregunta abierta (s109)` · Golden (procedencia P01) · LAUFD 2025-2026*
- <sub>denominador: las 577.103 filas de REGUH con LAUFD >= 20250101</sub>

### El Golden guarda 30 de los 180 campos de REGUH -- el 17%. Eso explica por que las columnas se siguen 'cayendo' de una en una cuando un minero las pide

- **Tamaño:** REGUH 30/180. Hoy hubo que anadir RBETR a REGUH, BNKN2 a T012K, PRIUS/ZALDT a PAYR, AKBLN a FEBEP y BLART/VBLNR a REGUP -- 7 columnas en 5 tablas, descubiertas por ERROR una a una hasta que se diffearon todas de golpe
- **Evidencia:** DD03L de P01 frente a PRAGMA table_info del Golden
- **No se puede ver:** guardar los 180 no es gratis ni necesariamente correcto: la pregunta no es 'por que faltan 150' sino 'que 150 no vamos a echar de menos'. No lo se
- **Acción:** un diff sistematico campo a campo entre P01 y el Golden para las tablas que mas se usan, y decidir el corte a proposito en vez de por acumulacion
- **Puede contestarlo:** DBS
- ***hoy** · lo encuentra `medido a mano (s109)` · Golden + P01 · n/a*
- <sub>denominador: los 180 campos de REGUH en P01</sub>

---

## 🟢 OPORTUNIDAD (4)

*se puede mejorar · va a quien decide dónde invertir esfuerzo*


### Hay cuentas con el modelo de extracto electronico YA MONTADO que no lo usan

- **Tamaño:** 12 cuentas (7 se teclean a mano, 5 no reciben nada), frente a 145 que si lo procesan electronicamente con ese mismo modelo
- **Evidencia:** T028B tiene fila para su BANKN actual y FEBKO.EFART no es 'E'
- **No se puede ver:** tener el modelo asignado NO prueba que el fichero pueda llegar: la restriccion puede estar aguas arriba, en que el banco emita MT940
- **Acción:** preguntar a esos bancos si emiten MT940 -- el coste en SAP es cero
- ***1 días abierto** · lo encuentra `bank_statement_channel_census` · P01 · 20250101 -> hoy*
- <sub>denominador: 402 cuentas de banco casa; 237 excluidas por llevar CLOSED en T012T-TEXT1 (no hay campo de estado: es una convencion humana); quedan 165 vivas</sub>

### Filas de T028B con numeros de cuenta que ya no son de ninguna cuenta viva: el rastro acumulado de cambios que nadie barrio

- **Tamaño:** 2 filas huerfanas de 169
- **Evidencia:** T028B.KTONR sin correspondencia en T012K.BANKN
- **No se puede ver:** no se si alguna se dejo a proposito como historico
- **Acción:** borrar tras confirmar que su cuenta ya no recibe
- ***1 días abierto** · lo encuentra `house_bank_ebs_wiring_check` · P01 · 2025-2026*
- <sub>denominador: 402 cuentas T012K; se excluyen las CERRADAS (marca CLOSED en T012T-TEXT1: 237 de 411 con texto) y las de extracto MANUAL, que no necesitan T028B</sub>

### Modelos de extracto que existen para UN SOLO banco: cada uno es un modelo entero -- con su prueba y su riesgo -- sosteniendo muy pocas cuentas

- **Tamaño:** 5 modelos, 73 reglas para 6 cuentas, sobre un total de 241 reglas
- **Evidencia:** T028B agrupado por VGTYP y T028G contado por modelo
- **No se puede ver:** parecido alto NO significa consolidable: absorber uno dentro de otro puede CAMBIAR su algoritmo y con el la contabilizacion
- **Acción:** mirar primero los pares con parecido alto, no los mas pequenos
- ***1 días abierto** · lo encuentra `ebs_format_consolidation` · P01 · 2025-2026*
- <sub>denominador: 142 cuentas VIVAS de UNES, 131 con extracto en la ventana</sub>

### Cuentas que reciben extractos y no producen NINGUN movimiento contable: trabajo que se procesa sin efecto

- **Tamaño:** 5 cuentas, 2097 extractos en la ventana
- **Evidencia:** FEBKO con cabeceras y GLT0 sin periodos con movimiento
- **No se puede ver:** puede que sean extractos a cero legitimos, o que la contabilizacion vaya a otro mayor: el dato no lo distingue
- **Acción:** mirar una de ellas en FEBAN antes de generalizar
- ***1 días abierto** · lo encuentra `bank_account_behaviour_signature` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS (excluidas las marcadas CLOSED en el texto)</sub>

---

## ⚪ DATO (8)

*un hecho relevante que no es ninguna de las tres · va al conocimiento*


### La naturaleza YA PREDICE la configuracion de pago, aunque nadie la haya declarado

- **Tamaño:** 10 de 10 OPERATIVAS estan en determinacion de banco; de las demas naturalezas, 11
- **Evidencia:** T042I frente a la naturaleza derivada
- **No se puede ver:** correlacion medida, no regla declarada en el sistema
- **Acción:** es el argumento para declarar la naturaleza (PMO H144)
- ***1 días abierto** · lo encuentra `bank_config_profile_by_nature` · P01 · 2025-2026*
- <sub>denominador: 165 cuentas VIVAS de todas las sociedades</sub>

### Ninguna cuenta cuyo extracto se teclea a mano pasa por BCM, y no es un defecto: sus pagos son 100% metodo cheque prenumerado (REGUH.RZAWE='3'), y BCM libera FICHEROS

- **Tamaño:** 17 de 17 cuentas pagadoras con CERO lotes BCM
- **Evidencia:** BNK_BATCH_ITEM por ZBUKR+HBKID · REGUH.RZAWE
- **No se puede ver:** BCM no puede cubrirlas: no hay fichero que liberar
- **Acción:** el control de estos pagos vive fuera de SAP — nombrar donde
- ***1 días abierto** · lo encuentra `bank_statement_sod_check` · P01 · 20250101 → hoy*
- <sub>denominador: cuentas de UNES que reciben AL MENOS un extracto tecleado a mano: 38, de las que 33 estan vivas (el resto llevan CLOSED en T012T-TEXT1). NO es la etiqueta de canal MANUAL, que solo cubre 8.</sub>

### RESUELTO: 5 de 16 incidentes nombraban su dominio con un alias que la ontologia no conocia (HR, MM, CTS, MasterDataConfig). Anadidos los 4 alias con la evidencia del incidente que los justifica; la puerta de ontologia ahora RECORRE los incidentes y falla si un nombre no resuelve

- **Tamaño:** 5 de 16 incidentes · 4 alias · resolvedor de 64 a 68 nombres · sin resolver: 0
- **Evidencia:** brain_v2/capability_model/ontology.json domains[].aliases + _alias_evidence · validate_ontology.py sources() ahora rinde incidents.json · probado inyectando un dominio falso: exit 1 por la razon correcta, verde al restaurar
- **No se puede ver:** PUBLIQUE ESTA CIFRA MAL DOS VECES. Primero '11 de 19 dominios inventados' contando BASIS, Security, Infrastructure y Brain_Architecture, que son claves transversales registradas. Luego '9 de 16' ignorando domains[].aliases y subdomain_aliases, con lo que Payment y BCM -- que YA eran alias de Payment_BCM -- contaban como inventados. La cifra buena, 5, sale de usar el resolvedor del proyecto (load_index) en vez de un conjunto hecho a mano. Tres medidas del mismo objeto, dos falsas, un solo modo de fallo: DENOMINADOR INCOMPLETO
- **Acción:** hecho. Y de paso: work_triad_check ahora resuelve por domains[].registry_keys -- Treasury_EBS es canonico y se registra como 'Treasury', y por no leer eso la sonda daba registro vacio. Casi edito el incidente para contentar a la sonda: el dato estaba bien y la sonda mal
- **Puede contestarlo:** DBS (dueño de la ontologia)
- ***hoy** · lo encuentra `work_triad_check (manual, s109)` · repo · todo el corpus*
- <sub>denominador: los 16 incidentes de primera clase de brain_v2/incidents/incidents.json</sub>

### RESUELTO: el Golden tenia el 28,8% de las cabeceras de extracto de la ventana. Refrescado por delta puro el 2026-08-29: 31.416 -> 94.082 filas, 2024-01-01 a 2026-08-28, ningun mes flaco, 0 duplicados, ni un DELETE

- **Tamaño:** FEBKO 28,8% -> 100% · T012K +BNKN2 · PAYR +PRIUS/ZALDT · FEBEP +AKBLN · REGUH +RBETR · REGUP +BLART/VBLNR
- **Evidencia:** brain_v2/gold_coverage.json, medido P01 vs Golden el 2026-08-29
- **No se puede ver:** solo se midieron 6 tablas de las ~22 que tocan estos mineros. REGUH, REGUP, BKPF, PAYR, BNK_BATCH_ITEM y GLT0 NO se midieron -- y no se midieron a proposito: contar en P01 con RFC_READ_TABLE arrastra las filas, y saber el numero de FEBKO ya costo 61.769 filas por el cable
- **Acción:** PASO DE EXTRACCION, no una lectura a P01: refrescar FEBKO/FEBEP de la ventana y T035D. `scripts/extraction/gold_refresh.py`. Hasta entonces _golden.exige() se NIEGA, que es la conducta correcta: mejor no publicar que publicar un tercio
- **Puede contestarlo:** DBS
- ***hoy** · lo encuentra `manual (s109) — NO hay script que lo refresque; se cierra a mano` · Golden vs P01 · AZDAT 20250101-20261231*
- <sub>denominador: las 6 tablas medidas de las ~22 que leen los 7 mineros de banca</sub>

### RESUELTO: los tres bloqueos para refrescar FEBKO. (1) pk-upsert borra -> no se uso: delta propio sin un solo DELETE. (2) 62 columnas revientan el buffer -> troceado de 8, medido. (3) el backup sigue pendiente y JP lo dio por asumido

- **Tamaño:** 31.416 -> 94.082 filas · 11 meses que faltaban, entrados · 38.764 duplicados que yo mismo cree, quitados
- **Evidencia:** gold_refresh.py refresh_pk_upsert lineas 136-138 (DELETE de las claves ausentes) · read_p01 linea 77 no trocea campos · FEBKO_2024_2026 tiene 62 columnas · PRAGMA table_info y MIN/MAX(AZDAT) sobre el Golden
- **No se puede ver:** y la causa real de los 13 meses fallidos NO era ninguna de las que dije: era `AZDAT <= '<mes>31'`, el 31 de febrero, que SAP devuelve como SAPSQL_DATA_LOSS
- **Acción:** (1) BACKUP del Golden primero: son 22,9 GB y D: no esta conectado, asi que no hay copia. (2) `where` que cubra TODO el alcance de la tabla (AZDAT >= '20240101'), NO solo el hueco, o el upsert borra 2024 entero. (3) trocear campos en read_p01, o curar FEBKO con el subconjunto de columnas que los mineros usan de verdad
- **Puede contestarlo:** DBS
- ***hoy** · lo encuentra `manual (s109) — NO hay script que lo refresque; se cierra a mano` · Golden + P01 · AZDAT 20240101 → hoy*
- <sub>denominador: las 15 tablas de Payment/transaction sin spec curada, de 318 en el registro (34 curadas)</sub>

### RESUELTO: las filas de REGUH sin clave son pagos a PERSONAS registradas como CLIENTES (KUNNR relleno), con perceptor divergente. La muestra las identifica: expertos del IPCC -- ZNME2='IPCC', ZNME3/4='INTERGOVERNMENTAL PANEL ON CLIMATE CHANGE' -- pagados contra su ficha de CLIENTE, no de proveedor

- **Tamaño:** KUNNR CIERRA la clave: en el grupo que el Golden repite 2.075 veces hay 2.075 KUNNR distintos. Es UNA columna, no un problema de diseno
- **Evidencia:** field_coverage_sampler sobre REGUH XVORL='X' AND LIFNR='': 38 campos con valor de 177, 23 ausentes del Golden. Verificacion directa de KUNNR en P01 sobre la clave duplicada
- **No se puede ver:** QUE SEAN pagos a personas via ficha de cliente lo digo por los valores de la muestra (10 filas), no por una regla de negocio confirmada. Y JP ya corrigio una vez que 'no existen pagos a clientes': aqui el hecho MEDIDO es que el campo KUNNR esta relleno, no como se llama eso en el negocio
- **Acción:** anadir KUNNR a REGUH en el Golden. Solo ese: el bloque Z* (ZNME1, ZSTRA, ZORT1...) es la direccion del perceptor y ya esta cubierta por NAME1/STRAS/ORT01. Con KUNNR, REGUH admite indice unico y su delta se desbloquea
- **Puede contestarlo:** BFM/TRS — que son las filas FI-AR en una corrida de pago
- ***hoy** · lo encuentra `gold_delta/REGUH (s109)` · Golden · toda la tabla*
- <sub>denominador: las 3.707.737 filas de REGUH en el Golden</sub>

### RESUELTO: las filas de REGUH sin clave son pagos a PERSONAS registradas como CLIENTES (KUNNR relleno), con perceptor divergente. La muestra las identifica: expertos del IPCC -- ZNME2='IPCC', ZNME3/4='INTERGOVERNMENTAL PANEL ON CLIMATE CHANGE' -- pagados contra su ficha de CLIENTE, no de proveedor

- **Tamaño:** KUNNR CIERRA la clave: en el grupo que el Golden repite 2.075 veces hay 2.075 KUNNR distintos. Es UNA columna, no un problema de diseno
- **Evidencia:** field_coverage_sampler sobre REGUH XVORL='X' AND LIFNR='': 38 campos con valor de 177, 23 ausentes del Golden. Verificacion directa de KUNNR en P01 sobre la clave duplicada
- **No se puede ver:** QUE SEAN pagos a personas via ficha de cliente lo digo por los valores de la muestra (10 filas), no por una regla de negocio confirmada. Y JP ya corrigio una vez que 'no existen pagos a clientes': aqui el hecho MEDIDO es que el campo KUNNR esta relleno, no como se llama eso en el negocio
- **Acción:** anadir KUNNR a REGUH en el Golden. Solo ese: el bloque Z* (ZNME1, ZSTRA, ZORT1...) es la direccion del perceptor y ya esta cubierta por NAME1/STRAS/ORT01. Con KUNNR, REGUH admite indice unico y su delta se desbloquea
- **Puede contestarlo:** BFM/TRS
- ***hoy** · lo encuentra `pregunta abierta (s109)` · Golden (procedencia P01) · LAUFD 2025-2026*
- <sub>denominador: las 577.103 filas de REGUH con LAUFD >= 20250101</sub>

### Las propuestas de pago NO son BCM, y BCM no marca nada en REGUH: es una capa aparte que solo recoge pagos YA EJECUTADOS

- **Tamaño:** 0 de 207.862 propuestas (XVORL='X') tienen fila en BNK_BATCH_ITEM. Al reves, los 95.385 items BCM que casan apuntan TODOS a XVORL vacio. Y REGUH tiene 180 campos en P01 sin NI UNO de BCM: los BNKL*/BNKN*/BNKS* son datos bancarios del perceptor y FM_STATUS es de Gestion de Fondos
- **Evidencia:** REGUH LEFT JOIN BNK_BATCH_ITEM por LAUFD+LAUFI+ZBUKR+VBLNR sobre 2025-2026; DD03L de P01 para el diccionario de REGUH
- **No se puede ver:** el cruce usa LAUFD+LAUFI+ZBUKR+VBLNR. Una propuesta no tiene VBLNR asignado todavia, asi que el cero es CONSISTENTE con el mecanismo pero no lo prueba por si solo -- lo que lo cierra es que no exista ningun campo BCM en los 180 de REGUH
- **Acción:** para saber si un pago paso por BCM se va a BNK_BATCH_ITEM, nunca a un flag de REGUH
- ***hoy** · lo encuentra `medido a mano (s109)` · Golden + P01 (diccionario) · LAUFD 2025-2026*
- <sub>denominador: las 577.103 filas de REGUH con LAUFD >= 20250101 y los 116.934 items BCM del mismo periodo</sub>

---

## De dónde sale cada uno

| Minero | Hallazgos |
|---|---:|
| `bank_statement_channel_census` | 5 |
| `bank_account_behaviour_signature` | 3 |
| `bank_statement_sod_check` | 3 |
| `pregunta abierta (s109)` | 3 |
| `bank_account_nature_model` | 2 |
| `house_bank_ebs_wiring_check` | 2 |
| `bank_config_profile_by_nature` | 2 |
| `medido a mano (s109)` | 2 |
| `manual (s109) — NO hay script que lo refresque; se cierra a mano` | 2 |
| `gold_delta/REGUP_SCENARIOS (s109)` | 1 |
| `ebs_format_consolidation` | 1 |
| `work_triad_check (manual, s109)` | 1 |
| `gold_delta/REGUH (s109)` | 1 |

> Un minero que no aparece aquí **no está limpio: está mudo**. O no busca, o no publica. Las dos cosas hay que arreglarlas.

