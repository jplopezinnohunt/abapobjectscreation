*&---------------------------------------------------------------------*
*& Report  YAM_PO_GLACCT
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*

REPORT  YAM_PO_GLACCT.

TABLES: ANLA,
        EKKN,
        EKKO,
        EKPO.


PARAMETERS: P_BUKRS LIKE ANLA-BUKRS DEFAULT 'UNES' OBLIGATORY.

SELECT-OPTIONS: P_ANLKL FOR ANLA-ANLKL,
                P_ANLN1 FOR ANLA-ANLN1,
                P_AKTIV FOR ANLA-AKTIV.

SELECTION-SCREEN SKIP 2.
SELECTION-SCREEN ULINE.
PARAMETERS: P_DEBUG AS CHECKBOX.


DATA: W_PONUM LIKE EKPO-EBELN,
      W_POPOS LIKE EKPO-EBELP,
      W_IND TYPE I,
      W_POS(5).


DATA: BEGIN OF T_ERR OCCURS 0,
        ANLN1 LIKE ANLA-ANLN1,
        INVZU LIKE ANLA-INVZU,
        ETEXT(50),
      END OF T_ERR.


DATA: BEGIN OF T_GLACCT OCCURS 0,
        SAKTO LIKE EKKN-SAKTO,
        NETPR LIKE EKPO-NETPR,
        NETWR LIKE EKKN-NETWR,
      END OF T_GLACCT.


START-OF-SELECTION.

REFRESH: T_ERR.

CLEAR ANLA.
SELECT *
      FROM ANLA
      WHERE BUKRS = P_BUKRS
        AND ANLN1 IN P_ANLN1
        AND ANLKL IN P_ANLKL
        AND AKTIV IN P_AKTIV.

  CHECK ANLA-DEAKT IS INITIAL. "not retired
  CHECK NOT ANLA-AKTIV IS INITIAL. "capitalized
  IF ANLA-INVZU IS INITIAL.
    CLEAR T_ERR.
    T_ERR-ANLN1 = ANLA-ANLN1.
    T_ERR-INVZU = ANLA-INVZU.
    T_ERR-ETEXT = 'Empty Inventory note (PO number) in asset record'.
    APPEND T_ERR.
  ENDIF.
  CHECK ANLA-INVZU <> SPACE. "PO number is there

  CLEAR: EKPO, W_PONUM, W_POPOS, W_POS.
  SPLIT ANLA-INVZU AT '-' INTO: W_PONUM W_POS.
  IF SY-SUBRC <> 0.
    CLEAR T_ERR.
    T_ERR-ANLN1 = ANLA-ANLN1.
    T_ERR-INVZU = ANLA-INVZU.
    T_ERR-ETEXT = 'Invalid format of PO number/item in asset record'.
    APPEND T_ERR.
  ENDIF.

  W_IND = 5 - STRLEN( W_POS ).
  W_POPOS+W_IND = W_POS.
  SELECT SINGLE * FROM EKPO WHERE EBELN = W_PONUM AND EBELP = W_POPOS.
  IF SY-SUBRC <> 0.
    CLEAR T_ERR.
    T_ERR-ANLN1 = ANLA-ANLN1.
    T_ERR-INVZU = ANLA-INVZU.
    T_ERR-ETEXT = 'PO number/item not found in PO items table'.
    APPEND T_ERR.

   ELSE.

     CLEAR: EKKN, EKKO.
     SELECT SINGLE * FROM EKKO WHERE EBELN = EKPO-EBELN.

     SELECT *
           FROM EKKN
           WHERE EBELN = EKPO-EBELN
             AND EBELP = EKPO-EBELP.

       CLEAR T_GLACCT.
       T_GLACCT-SAKTO = EKKN-SAKTO.
*       if ekkn-netwr = 0.
*         if ekko-waers <> 'USD'.
*           CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
*           EXPORTING
*             DATE                    = anla-aktiv
*             FOREIGN_AMOUNT          = ekpo-netpr
*             FOREIGN_CURRENCY        = ekko-waers
*             LOCAL_CURRENCY          = 'USD'
*          IMPORTING
**            EXCHANGE_RATE           =
**            FOREIGN_FACTOR          =
*            LOCAL_AMOUNT            = t_glacct-netpr
**            LOCAL_FACTOR            =
**            EXCHANGE_RATEX          =
**            FIXED_RATE              =
**            DERIVED_RATE_TYPE       =
*          EXCEPTIONS
*            NO_RATE_FOUND           = 1
*            OVERFLOW                = 2
*            NO_FACTORS_FOUND        = 3
*            NO_SPREAD_FOUND         = 4
*            DERIVED_2_TIMES         = 5
*            OTHERS                  = 6
*                   .
*           IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*           ENDIF.
*          else.
*            t_glacct-netpr = ekpo-netpr.
*         endif. "ekko-waers
*         append t_glacct.
*
*        else. "ekkn-netwr
*          if ekko-waers <> 'USD'.
*            CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
*            EXPORTING
*              DATE                    = anla-aktiv
*              FOREIGN_AMOUNT          = ekkn-netwr
*              FOREIGN_CURRENCY        = ekko-waers
*              LOCAL_CURRENCY          = 'USD'
*           IMPORTING
**            EXCHANGE_RATE           =
**            FOREIGN_FACTOR          =
*             LOCAL_AMOUNT            = t_glacct-netwr
**            LOCAL_FACTOR            =
**            EXCHANGE_RATEX          =
**            FIXED_RATE              =
**            DERIVED_RATE_TYPE       =
*           EXCEPTIONS
*             NO_RATE_FOUND           = 1
*             OVERFLOW                = 2
*             NO_FACTORS_FOUND        = 3
*             NO_SPREAD_FOUND         = 4
*             DERIVED_2_TIMES         = 5
*             OTHERS                  = 6
*                   .
*            IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*            ENDIF.
*          else.
*            t_glacct-netwr = ekkn-netwr.
*         endif. "ekko-waers
*         collect t_glacct.
*       endif. "ekkn-netwr

       IF EKKN-VPROZ = 0.
         T_GLACCT-NETPR = EKPO-NETPR.
        ELSE. "ekkn-vproz
          T_GLACCT-NETPR = EKPO-NETPR * EKKN-VPROZ / 100.
       ENDIF. "ekkn-vproz
       IF EKKO-WAERS <> 'USD'.
         CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
           EXPORTING
             DATE                    = ANLA-AKTIV
             FOREIGN_AMOUNT          = T_GLACCT-NETPR
             FOREIGN_CURRENCY        = EKKO-WAERS
             LOCAL_CURRENCY          = 'USD'
          IMPORTING
**            EXCHANGE_RATE           =
**            FOREIGN_FACTOR          =
            LOCAL_AMOUNT            = T_GLACCT-NETWR
**            LOCAL_FACTOR            =
**            EXCHANGE_RATEX          =
**            FIXED_RATE              =
**            DERIVED_RATE_TYPE       =
          EXCEPTIONS
            NO_RATE_FOUND           = 1
            OVERFLOW                = 2
            NO_FACTORS_FOUND        = 3
            NO_SPREAD_FOUND         = 4
            DERIVED_2_TIMES         = 5
            OTHERS                  = 6
                   .
           IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
           ENDIF.
          ELSE.
            T_GLACCT-NETWR = T_GLACCT-NETPR.
         ENDIF. "ekko-waers
         COLLECT T_GLACCT.

*debug
IF P_DEBUG = 'X'.
  WRITE: / ANLA-ANLKL, ANLA-ANLN1, T_GLACCT-NETPR.
ENDIF. "p_debug

     ENDSELECT. "ekkn

  ENDIF. "ekpo sy-subrc
ENDSELECT. "anla

END-OF-SELECTION.


SORT T_GLACCT.
CLEAR T_GLACCT.
LOOP AT T_GLACCT.
  AT END OF SAKTO.
    SUM.
    WRITE: /
           T_GLACCT-SAKTO,
*           t_glacct-netpr,
           T_GLACCT-NETWR.
  ENDAT.
  AT LAST.
    SUM.
    ULINE.
    FORMAT COLOR 3.
    WRITE: /
           T_GLACCT-SAKTO,
*           t_glacct-netpr,
           T_GLACCT-NETWR.
    FORMAT COLOR OFF.
  ENDAT.
ENDLOOP. "t_glacct

SKIP 2.
ULINE.
FORMAT COLOR 6.
WRITE: / 'Error log:'.
WRITE: / 'Asset number|PO/item number |Error text '.
FORMAT COLOR OFF.
ULINE.
SORT T_ERR.
LOOP AT T_ERR.
  WRITE: /
         T_ERR-ANLN1,
         T_ERR-INVZU,
         T_ERR-ETEXT.
ENDLOOP. "t_err