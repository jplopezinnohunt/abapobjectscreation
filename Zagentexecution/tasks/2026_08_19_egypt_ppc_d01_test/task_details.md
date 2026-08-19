# Prueba de aceptacion en D01 — Purpose of Payment / Egipto

**Sesion** #101 · **Fecha** 2026-08-19 · **Incidente** `INC-EGYPT-PPC` · **Ticket** `INC-000016101`
**Deadline** Citi 2026-09-05

## Requisito

Citibank Egypt exige Purpose of Payment en todo RTGS y CBFT hacia o desde Egipto desde el
2026-09-05, en *Transaction Details* o **SWIFT Field 70**. UNESCO ya tiene un framework de
purpose codes para nueve paises; Egipto es el decimo.

## Objetivo de esta prueba

Probar las DOS mitades del control en D01, por separado, antes de tocar P01:

1. **CAPTURA** — que `u917` bloquee una contabilizacion sin `LZBKZ` para un proveedor con
   banco en Egipto.
2. **RENDERIZADO** — que el fichero CGI lleve la cadena en `<RmtInf><Ustrd>`.

Son capas distintas gobernadas por dos paises distintos (nuestro banco elige la clase BAdI,
su banco elige las filas de configuracion), asi que una no prueba la otra.

## Escenario

| | |
|---|---|
| Sociedad | `UNES` |
| Proveedor | `0000318305` SilverKey Technologies Egypt |
| Banco del proveedor | Credit Agricole Egypt `AGRIEGCX`, `LFBK-BANKS = EG`, cuenta `01011110004092`, `BVTYP = USD` |
| Factura | `FB60` 250.00 USD, `XBLNR = 224938`, `GSBER = GEF`, gasto `0002086092` |
| Codigo | `LZBKZ = EG0` (pestana *Details*, campo *SCB Ind.*) |
| Pago | `F110` `LAUFD 19.08.2026` / `LAUFI EG1`, metodo `N`, propuesta |
| Medio | `SAPFPAYM` variante `1TST_USD_INT`, formato `/CGI_XML_CT_UNESCO`, salida a fichero DESACTIVADA |

Por que ese proveedor: un unico registro `LFBK`, sin ambiguedad de `BVTYP` para el
`SELECT SINGLE` de `u917`; sin bloqueos; y con `N` entre sus vias de pago permitidas.

Por que la cuenta `0002086092`: es transitoria, con grupo de status de campo `UN01`, y **no
exige objeto de coste ni imputacion FM**. Una cuenta de gasto real habria metido al AVC en
la prueba, y un fallo de presupuesto no dice nada sobre purpose of payment.

## Resultado

Ambas mitades pasan. Detalle y evidencia en `learning_summary.md`.

## Prediccion previa

Antes de ejecutar se simulo `CM003`/`CM004` sobre la configuracion leida en vivo y se
publico la cadena esperada:

```
/Payment for goods or services received/INV/224938
```

El fichero la trajo identica.
