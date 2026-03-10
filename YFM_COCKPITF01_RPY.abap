*&---------------------------------------------------------------------*
*&  Include           YFM_COCKPITF01
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Form  PROMPT_NEXT_STEP
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_0044   text
*----------------------------------------------------------------------*
FORM PROMPT_NEXT_STEP  USING   L_STEP.

  DATA : LV_TEXT   TYPE STRING,
         LV_ICON   TYPE ICONNAME,
         LV_ANSWER TYPE C.


  CASE L_STEP.
    WHEN 2.
      LV_TEXT = 'Go to next step, Reinitialize Budget ?'.

    WHEN 3.
      LV_TEXT = 'Go to next step, Verify Budget Structure ?'.

  ENDCASE.

  CALL FUNCTION 'POPUP_TO_CONFIRM'
    EXPORTING
*     TITLEBAR              = ' '
*     DIAGNOSE_OBJECT       = ' '
      TEXT_QUESTION         = LV_TEXT
      TEXT_BUTTON_1         = 'Yes'(001)
      ICON_BUTTON_1         = 'ICON_OKAY'
      TEXT_BUTTON_2         = 'No'(002)
      ICON_BUTTON_2         = 'ICON_CANCEL'
      DEFAULT_BUTTON        = '1'
      DISPLAY_CANCEL_BUTTON = ''
*     USERDEFINED_F1_HELP   = ' '
*     START_COLUMN          = 25
*     START_ROW             = 6
*     popup_type            = 'ICON_NEXT_STEP'
*     IV_QUICKINFO_BUTTON_1 = ' '
*     IV_QUICKINFO_BUTTON_2 = ' '
    IMPORTING
      ANSWER                = LV_ANSWER
*   TABLES
*     PARAMETER             =
    EXCEPTIONS
      TEXT_NOT_FOUND        = 1
      OTHERS                = 2.
  IF SY-SUBRC = 0.
    CASE LV_ANSWER.
      WHEN '1'.
        CASE L_STEP.
          WHEN 2.
            CALL TRANSACTION C_TRANS_2.
            W_STEP_2_DONE = ABAP_TRUE.
            PERFORM PROMPT_NEXT_STEP USING 3.
          WHEN 3.
            CALL TRANSACTION C_TRANS_3.
        ENDCASE.
      WHEN OTHERS.
    ENDCASE.
  ENDIF.


ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  OPEN_DOC
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM OPEN_DOC .
  DATA : LV_URL_DOC TYPE BDS_URI.

  DATA : LT_COMP      TYPE TABLE OF   BAPICOMPON,
         LS_COMP      TYPE BAPICOMPON,
         LT_SIGNATURE TYPE TABLE OF   BAPISIGNAT,
         LS_SIGNATURE TYPE BAPISIGNAT,
         LT_URL       TYPE TABLE OF BAPIURI,
         LS_URL       TYPE BAPIURI.


  IF GO_WORD IS NOT BOUND.
    CREATE OBJECT GO_WORD.

    GO_WORD->PREPARE_WORD( ).

  ENDIF.

  CALL FUNCTION 'BDS_BUSINESSDOCUMENT_GET_INFO'
    EXPORTING
*     LOGICAL_SYSTEM  =
      CLASSNAME       = 'ZDOC_HELP_GUIDE'
      CLASSTYPE       = 'OT'
*     CLIENT          = SY-MANDT
      OBJECT_KEY      = 'HELP_GUIDE'
*     ALL             = 'X'
*     CHECK_STATE     = ' '
    TABLES
      COMPONENTS      = LT_COMP
      SIGNATURE       = LT_SIGNATURE
*     CONNECTIONS     =
*     EXTENDED_COMPONENTS       =
    EXCEPTIONS
      NOTHING_FOUND   = 1
      PARAMETER_ERROR = 2
      NOT_ALLOWED     = 3
      ERROR_KPRO      = 4
      INTERNAL_ERROR  = 5
      NOT_AUTHORIZED  = 6
      OTHERS          = 7.
  IF SY-SUBRC = 0.
* Implement suitable error handling here
    READ TABLE LT_COMP INTO LS_COMP WITH KEY COMP_ID = 'YFM_ADD_RULEDERAVC'.
    IF SY-SUBRC = 0.
      DELETE LT_COMP WHERE DOC_COUNT NE LS_COMP-DOC_COUNT.
      DELETE LT_SIGNATURE WHERE DOC_COUNT NE LS_COMP-DOC_COUNT.
    ENDIF.
    CALL FUNCTION 'BDS_BUSINESSDOCUMENT_GET_URL'
      EXPORTING
*       LOGICAL_SYSTEM  =
        CLASSNAME       = 'ZDOC_HELP_GUIDE'
        CLASSTYPE       = 'OT'
*       CLIENT          = SY-MANDT
        OBJECT_KEY      = 'HELP_GUIDE'
*       URL_LIFETIME    =
*       STANDARD_URL_ONLY                =
*       DATA_PROVIDER_URL_ONLY           =
*       WEB_APPLIC_SERVER_URL_ONLY       =
*       URL_USED_AT     =
*       SELECTED_INDEX  =
      TABLES
        URIS            = LT_URL
        SIGNATURE       = LT_SIGNATURE
        COMPONENTS      = LT_COMP
      EXCEPTIONS
        NOTHING_FOUND   = 1
        PARAMETER_ERROR = 2
        NOT_ALLOWED     = 3
        ERROR_KPRO      = 4
        INTERNAL_ERROR  = 5
        NOT_AUTHORIZED  = 6
        OTHERS          = 7.

    IF SY-SUBRC = 0.
      READ TABLE LT_URL INTO LS_URL INDEX 1.
      IF SY-SUBRC = 0.
        LV_URL_DOC = LS_URL-URI.
        IF GV_OPEN = ABAP_FALSE.
          GO_WORD->OPEN_DOCUMENT(
            EXPORTING
              I_URL     =  LV_URL_DOC                " URL or local file FILE://xxxxxxx
              I_INPLACE =  ''                " 'X' display inplace
          ).
          GV_OPEN = ABAP_TRUE.
        ELSE.
          GO_WORD->REOPEN_DOCUMENT( I_INPLACE = ABAP_FALSE ).
        ENDIF.

      ENDIF.
    ENDIF.

  ENDIF.

ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  CHECK_ROLE_FOR_FILTER
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM CHECK_ROLE_FOR_FILTER CHANGING LLV_FMAREA.

  DATA : LT_AGR    TYPE TABLE OF BAPIAGR,
         LS_AGR    TYPE BAPIAGR,
         LT_RETURN TYPE TABLE OF BAPIRET2.



  CALL FUNCTION 'BAPI_USER_GET_DETAIL'
    EXPORTING
      USERNAME       = SY-UNAME
*     CACHE_RESULTS  = 'X'
*         IMPORTING
*     LOGONDATA      =
*     DEFAULTS       =
*     ADDRESS        =
*     COMPANY        =
*     SNC            =
*     REF_USER       =
*     ALIAS          =
*     UCLASS         =
*     LASTMODIFIED   =
*     ISLOCKED       =
*     IDENTITY       =
*     ADMINDATA      =
*     DESCRIPTION    =
    TABLES
*     PARAMETER      =
*     PROFILES       =
      ACTIVITYGROUPS = LT_AGR
      RETURN         = LT_RETURN
*     ADDTEL         =
*     ADDFAX         =
*     ADDTTX         =
*     ADDTLX         =
*     ADDSMTP        =
*     ADDRML         =
*     ADDX400        =
*     ADDRFC         =
*     ADDPRT         =
*     ADDSSF         =
*     ADDURI         =
*     ADDPAG         =
*     ADDCOMREM      =
*     PARAMETER1     =
*     GROUPS         =
*     UCLASSSYS      =
*     EXTIDHEAD      =
*     EXTIDPART      =
*     SYSTEMS        =
    .

  LOOP AT LT_AGR INTO LS_AGR.
    IF LS_AGR-AGR_NAME CS 'YS:FM:M:EXB_DERIV_RULE___:'.
      LLV_FMAREA = LS_AGR-AGR_NAME+26(4).
    ENDIF.
  ENDLOOP.


ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  BATCH_FILTER
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM BATCH_FILTER .

  CLEAR BDC_TAB.
  BDC_TAB-PROGRAM = 'SAPLBUBAS_STRAT_ENV'.
  BDC_TAB-DYNPRO = '0100'.
  BDC_TAB-DYNBEGIN = 'X'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.

  BDC_TAB-FNAM = 'BUAVCKEDRENVT-KEDRENV'.
  BDC_TAB-FVAL = '9HZ00001'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.
  BDC_TAB-FNAM = 'BDC_OKCODE'.
  BDC_TAB-FVAL = '=OK'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.

  BDC_TAB-PROGRAM = 'SAPMABADR'.
  BDC_TAB-DYNPRO = '0900'.
  BDC_TAB-DYNBEGIN = 'X'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.
  BDC_TAB-FNAM = 'BDC_OKCODE'.
  BDC_TAB-FVAL = '=VFIL'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.

  BDC_TAB-PROGRAM = 'SAPMABADR'.
  BDC_TAB-DYNPRO = '0960'.
  BDC_TAB-DYNBEGIN = 'X'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.
  BDC_TAB-FNAM = 'DYNP960-01'.
  BDC_TAB-FVAL = LV_FMAREA.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.
  BDC_TAB-FNAM = 'BDC_OKCODE'.
  BDC_TAB-FVAL = '=CONT'.
  APPEND BDC_TAB.
  CLEAR BDC_TAB.

ENDFORM.