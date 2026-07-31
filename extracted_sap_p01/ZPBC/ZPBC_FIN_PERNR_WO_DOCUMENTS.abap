*&---------------------------------------------------------------------*
*& Report  ZPBC_FIN_PERNR_WO_DOCUMENTS
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*

REPORT  ZPBC_FIN_PERNR_WO_DOCUMENTS.

INFOTYPES: 0724.
TABLES: PERNR, HRFPM_FPM_POS.
DATA GT_P0724 LIKE P0724 OCCURS 0 WITH HEADER LINE.
DATA GR_ENDDA TYPE RANGE OF ENDDA WITH HEADER LINE.
DATA LT_INT_TIMES TYPE HRFPM_ACC_INTEGRATION_TIMES_IT.
DATA ENC_ENGINE_EXISTING TYPE FLAG.

PARAMETERS BEGDA TYPE HRFPM_FPM_POS-BEGDA OBLIGATORY.
PARAMETERS ENDDA TYPE HRFPM_FPM_POS-ENDDA DEFAULT '99991231'."OBLIGATORY.

GET PERNR.

  IF NOT ENDDA IS INITIAL AND GR_ENDDA[] IS INITIAL.
    GR_ENDDA-OPTION = 'LE'.
    GR_ENDDA-SIGN   = 'I'.
    GR_ENDDA-LOW    = ENDDA.
    APPEND GR_ENDDA.
  ENDIF.

  IF NOT P0724 IS INITIAL AND P0724-SUBTY IS INITIAL.

    PERFORM CHECK_INTEGRATION(SAPLHRFPM_INTERFACE_FUNCTIONS)
                                        USING    PERNR-PERNR
                                                 P0724-BEGDA
                                                 P0724-ENDDA
                                        CHANGING LT_INT_TIMES
                                                  ENC_ENGINE_EXISTING
                                        IF FOUND.
    READ TABLE LT_INT_TIMES
          WITH KEY INTEGRATION = '1'
          TRANSPORTING NO FIELDS.

    IF SY-SUBRC = 0.

      SELECT SINGLE OBJID INTO CORRESPONDING FIELDS OF HRFPM_FPM_POS
            FROM HRFPM_FPM_POS WHERE OBJID = PERNR-PERNR
             AND BEGDA GE BEGDA
             AND ENDDA IN GR_ENDDA[].

      IF SY-SUBRC <> 0.
        APPEND P0724 TO GT_P0724.
      ENDIF.
    ENDIF.
  ENDIF.

END-OF-SELECTION.


*{   DELETE         D11K953765                                        1
*\  BREAK-POINT.
*}   DELETE

  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
   EXPORTING
*   I_INTERFACE_CHECK                 = ' '
*   I_BYPASSING_BUFFER                = ' '
*   I_BUFFER_ACTIVE                   = ' '
*   I_CALLBACK_PROGRAM                = ' '
*   I_CALLBACK_PF_STATUS_SET          = ' '
*   I_CALLBACK_USER_COMMAND           = ' '
*   I_CALLBACK_TOP_OF_PAGE            = ' '
*   I_CALLBACK_HTML_TOP_OF_PAGE       = ' '
*   I_CALLBACK_HTML_END_OF_LIST       = ' '
      I_STRUCTURE_NAME                  = 'P0724'
*   I_BACKGROUND_ID                   = ' '
*   I_GRID_TITLE                      =
*   I_GRID_SETTINGS                   =
*   IS_LAYOUT                         =
*   IT_FIELDCAT                       =
*   IT_EXCLUDING                      =
*   IT_SPECIAL_GROUPS                 =
*   IT_SORT                           =
*   IT_FILTER                         =
*   IS_SEL_HIDE                       =
*   I_DEFAULT                         = 'X'
      I_SAVE                            = 'U'
*   IS_VARIANT                        =
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
      T_OUTTAB                          = GT_P0724[]
* EXCEPTIONS
*   PROGRAM_ERROR                     = 1
*   OTHERS                            = 2
            .

  IF SY-SUBRC <> 0.
    BREAK-POINT.
  ENDIF.