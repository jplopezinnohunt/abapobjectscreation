# Lo que dejo esta prueba

## El resultado

```xml
<RmtInf>
  <Ustrd>/Payment for goods or services received/INV/224938</Ustrd>
</RmtInf>
```

50 caracteres, de 140 que admite el nodo. Identico a la prediccion.

Y el bloqueo, por la otra mitad: `FB60` sin `LZBKZ` -> rechazado con `ZFI-036` severidad `E`,
*"Enter the payment purpose code (SCB) for the respective country"*. Ningun otro de los doce
pasos de la validacion `UNES` usa ese mensaje, asi que el rechazo es atribuible a este
control y no a otro.

## Los dos paises del mecanismo, visibles en el mismo fichero

```
<DbtrAgt><BIC>SOGEFRPP</BIC><PstlAdr><Ctry>FR</Ctry>     <- NUESTRO banco elige la CLASE (_FR)
<CdtrAgt><BIC>AGRIEGCX</BIC>...<Ctry>EG</Ctry>           <- SU banco elige las FILAS (LAND1='EG')
```

Lo que el companion describia leyendo el fuente queda observable en la salida. Y responde la
pregunta que abrio el caso: **no hace falta desarrollo**. No hay literal de pais en ninguna
de las tres capas (`u917` lee `LFBK-BANKS`, `CM002` pasa `ZBNKS`, `CM003` filtra
`WHERE LAND1 = IV_LAND1`).

Trazabilidad: el `Ref.number 0102209014` de la pantalla del medio es el `<MsgId>` del fichero.

## Lo que se aprendio por el camino, y vale mas que el resultado

1. **El ensamblador concatena sin separador implicito.** `BUILD_VALUE` es
   `ev_value_c = |{ iv_value_c }{ iv_value_to_add }|`. Un `SEPARATOR` vacio no separa: pega.
2. **Un blanco FINAL no se puede guardar en un `CHAR`; uno INICIAL si.** `PPC_VALUE` es
   `CHAR(60)`: el espacio del final ES el relleno. Se probo grabando `" INV"` por `SM30` y
   releyendo por RFC: un blanco delante, cero detras. Por tanto la separacion va **delante**
   de un literal y nunca detras — y nunca justo antes de un `PAY_FIELD`, que es dinamico.
3. **`SPLIT ... AT space INTO a b` mete en el ultimo destino el resto INCLUYENDO separadores.**
   Dos espacios en `ZWCK1` producen una narrativa que empieza por blanco.
4. **Los tres defectos anteriores eran invisibles en `SM30`** y los cazo el mismo instrumento:
   `RFC_READ_TABLE` **sin `.strip()`**, contando blancos.
5. **La cuenta importa para el diseno de la prueba.** `0002086092` no exige imputacion FM, asi
   que el AVC no entra. Una cuenta de gasto real habria metido presupuesto en una prueba de
   configuracion.
6. **El campo `LZBKZ` esta en la pestana *Details* de FB60**, no en *Payment*.
7. **La variante `1TST_USD_INT` la creo M. Spronk el 2024-03-25**, un dia antes de los
   transportes que construyeron el framework. Reutilizarla en vez de crear otra fue gratis.

## Ficheros

- `UNES_SOGE_03INTUSD_20260819_EG1.xml` — el medio generado, tal cual
- `UNES_SOGE_03INTUSD_20260819_EG1_pretty.xml` — el mismo, indentado, para leerlo

## Claims

524 (el ensamblador y los blancos) · 525 (el nodo lleva el exit) · 526 (lo construido y sus
desviaciones) · **527 (esta prueba)** · 528 (nomina y payment requests no llegan a estos
paises) · 529 (`T015L INA` roto en P01, encontrado al mecanizar esto)
