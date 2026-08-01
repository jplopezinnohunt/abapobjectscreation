*&---------------------------------------------------------------------*
*& Report  YFI_ACCT_BUSAREA
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*

REPORT  YFI_ACCT_BUSAREA.

INCLUDE Y_ALV_GRID.

TABLES: BSEG,
        BSIS.


PARAMETERS: P_BUKRS LIKE BSIS-BUKRS OBLIGATORY.

SELECT-OPTIONS: P_HKONT FOR BSIS-HKONT OBLIGATORY.

PARAMETERS: P_GJAHR LIKE BSIS-GJAHR OBLIGATORY.

SELECT-OPTIONS: P_BUDAT FOR BSIS-BUDAT,
                P_GSBER FOR BSIS-GSBER.



DATA: BEGIN OF T_DOCS OCCURS 0,
        BUKRS LIKE BSIS-BUKRS,
        BLART LIKE BSIS-BLART,
        BELNR LIKE BSIS-BELNR,
        ACCT1 LIKE BSIS-HKONT,
        BUAR1 LIKE BSIS-GSBER,
        FCTR1 LIKE BSIS-FISTL,
        FUND1 LIKE BSIS-GEBER,
        SUM01 LIKE BSIS-DMBTR,
        ACCT2 LIKE BSIS-HKONT,
        BUAR2 LIKE BSEG-GSBER,
        FCTR2 LIKE BSEG-FISTL,
        FUND2 LIKE BSEG-GEBER,
        SUM02 LIKE BSEG-DMBTR,
      END OF T_DOCS.

START-OF-SELECTION.

CLEAR BSIS.
SELECT *
      FROM BSIS
      WHERE BUKRS = P_BUKRS
        AND HKONT IN P_HKONT
        AND GJAHR = P_GJAHR
        AND BUDAT IN P_BUDAT
        AND GSBER IN P_GSBER.
  CLEAR BSEG.
  SELECT *
        FROM BSEG
        WHERE BUKRS = BSIS-BUKRS
          AND BELNR = BSIS-BELNR
          AND GJAHR = BSIS-GJAHR.
    IF BSEG-GSBER <> BSIS-GSBER.
      CLEAR T_DOCS.
      MOVE-CORRESPONDING BSIS TO T_DOCS.
      T_DOCS-ACCT1 = BSIS-HKONT.
      T_DOCS-ACCT2 = BSEG-HKONT.
      T_DOCS-BUAR1 = BSIS-GSBER.
      T_DOCS-BUAR2 = BSEG-GSBER.
      T_DOCS-FCTR1 = BSIS-FISTL.
      T_DOCS-FCTR2 = BSEG-FISTL.
      T_DOCS-FUND1 = BSIS-GEBER.
      T_DOCS-FUND2 = BSEG-GEBER.
      T_DOCS-SUM01 = BSIS-DMBTR.
      IF BSIS-SHKZG = 'H'.
        T_DOCS-SUM01 = T_DOCS-SUM01 * -1.
      ENDIF.
      T_DOCS-SUM02 = BSEG-DMBTR.
      IF BSEG-SHKZG = 'H'.
        T_DOCS-SUM02 = T_DOCS-SUM02 * -1.
      ENDIF.
      APPEND T_DOCS.
    ENDIF. "gsber
  ENDSELECT. "bseg
ENDSELECT. "bsis

END-OF-SELECTION.


SORT T_DOCS BY BUKRS BLART BELNR.

PERFORM DEFAULT_LAYOUT USING 'FI: documents with different B/Areas'.

M_FIELDCAT 'BUKRS' 'BSIS' '' '' ''.
M_FIELDCAT 'BLART' 'BSIS' '' '' ''.
M_FIELDCAT 'BELNR' 'BSIS' '' '' ''.
M_FIELDCAT 'ACCT1' 'BSIS' 'HKONT' '' ''.
M_FIELDCAT 'BUAR1' 'BSIS' 'GSBER' '' ''.
M_FIELDCAT 'FCTR1' 'BSIS' 'FISTL' '' ''.
M_FIELDCAT 'FUND1' 'BSIS' 'GEBER' '' ''.
M_FIELDCAT 'SUM01' 'BSIS' 'DMBTR' '' ''.
M_FIELDCAT 'ACCT2' 'BSEG' 'HKONT' '' ''.
M_FIELDCAT 'BUAR2' 'BSEG' 'GSBER' '' ''.
M_FIELDCAT 'FCTR2' 'BSEG' 'FISTL' '' ''.
M_FIELDCAT 'FUND2' 'BSEG' 'GEBER' '' ''.
M_FIELDCAT 'SUM02' 'BSEG' 'DMBTR' '' ''.


CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
  EXPORTING
*   I_INTERFACE_CHECK                 = ' '
*   I_BYPASSING_BUFFER                = ' '
*   I_BUFFER_ACTIVE                   = ' '
    I_CALLBACK_PROGRAM                = 'YFI_ACCT_BUSAREA'
*   I_CALLBACK_PF_STATUS_SET          = ' '
    I_CALLBACK_USER_COMMAND           = 'SHOWFIDOC'
*   I_CALLBACK_TOP_OF_PAGE            = ' '
*   I_CALLBACK_HTML_TOP_OF_PAGE       = ' '
*   I_CALLBACK_HTML_END_OF_LIST       = ' '
*   I_STRUCTURE_NAME                  =
*   I_BACKGROUND_ID                   = ' '
*   I_GRID_TITLE                      =
*   I_GRID_SETTINGS                   =
    IS_LAYOUT                         = LS_LAYOUT
    IT_FIELDCAT                       = LT_FIELDCAT
*   IT_EXCLUDING                      =
*   IT_SPECIAL_GROUPS                 =
*   IT_SORT                           =
*   IT_FILTER                         =
*   IS_SEL_HIDE                       =
*   I_DEFAULT                         = 'X'
    I_SAVE                            = 'X'
    IS_VARIANT                        = LS_VARIANT
*   IT_EVENTS                         =
*   IT_EVENT_EXIT                     =
*   IS_PRINT                          =
*   IS_REPREP_ID                      =
*   I_SCREEN_START_COLUMN             = 0
*   I_SCREEN_START_LINE               = 0
*   I_SCREEN_END_COLUMN               = 0
*   I_SCREEN_END_LINE                 = 0
*   I_HTML_HEIGHT_TOP                 = 0
*   I_HTML_HEIGHT_END                 = 0
*   IT_ALV_GRAPHICS                   =
*   IT_HYPERLINK                      =
*   IT_ADD_FIELDCAT                   =
*   IT_EXCEPT_QINFO                   =
*   IR_SALV_FULLSCREEN_ADAPTER        =
* IMPORTING
*   E_EXIT_CAUSED_BY_CALLER           =
*   ES_EXIT_CAUSED_BY_USER            =
  TABLES
    T_OUTTAB                          = T_DOCS
* EXCEPTIONS
*   PROGRAM_ERROR                     = 1
*   OTHERS                            = 2
          .
IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.



FORM SHOWFIDOC USING R_COMM LIKE SY-UCOMM
                     RS_SELFIELD TYPE SLIS_SELFIELD.

  CLEAR T_DOCS.
  READ TABLE T_DOCS INDEX RS_SELFIELD-TABINDEX.

  CALL FUNCTION 'FI_DOCUMENT_DISPLAY_RFC'
    EXPORTING
      I_BELNR       = T_DOCS-BELNR
      I_BUKRS       = T_DOCS-BUKRS
      I_GJAHR       = P_GJAHR.

ENDFORM. "ShowFIDoc