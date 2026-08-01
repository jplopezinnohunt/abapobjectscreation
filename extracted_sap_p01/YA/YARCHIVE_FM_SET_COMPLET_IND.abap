REPORT YARCHIVE_FM_SET_COMPLET_IND.

*******************************************************************
* PROGRAM        YARCHIVE_FM_SET_COMPLET_IND                      *
* TITLE          YARCHIVE_FM_SET_COMPLET_IND                      *
* AUTHOR         TAL DEBORAH                                      *
* DATE WRITTEN   10/07/007                                        *
* R/3 RELEASE    4.7                                              *
*******************************************************************
* PROGRAM TYPE   Report                                           *
* DEV.CLASS      YE                                               *
* LOGICAL DB     FMF                                              *
*******************************************************************
*******************************************************************
*                             TABLES                              *
*******************************************************************
TABLES: KBLP.

*******************************************************************
*                         INTERNAL TABLES                         *
*******************************************************************
DATA : BEGIN OF T_KBLP OCCURS 10.
DATA : BELNR LIKE KBLP-BELNR.
DATA : END OF T_KBLP.

*******************************************************************
*                       SELECTION-SCREEN                          *
*******************************************************************
SELECT-OPTIONS : S_DATE FOR SY-DATUM.

PARAMETERS : P_TEST AS CHECKBOX.

*******************************************************************
*                         TREATMENT                               *
*******************************************************************
START-OF-SELECTION.

SELECT * INTO CORRESPONDING FIELDS OF TABLE T_KBLP FROM KBLP
  WHERE ERDAT IN S_DATE AND ( AEDAT IN S_DATE OR AEDAT EQ '00000000' )
    AND ERLKZ EQ SPACE  AND WTFREE EQ 0.

IF P_TEST IS NOT INITIAL.
  WRITE 'Test Mode'.
ENDIF.

LOOP AT T_KBLP.
  WRITE : /, T_KBLP-BELNR.
  IF P_TEST IS INITIAL.
    UPDATE KBLP SET ERLKZ = 'X' WHERE BELNR = T_KBLP-BELNR.
    WRITE 'updated'.
  ENDIF.
ENDLOOP.

END-OF-SELECTION.