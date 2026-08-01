*&---------------------------------------------------------------------*
*& Report YFM_UPDATE_FUND_C5_ASSIGN
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFM_DISPLAY_FUND_C5_ASSIGN.

TYPES: BEGIN OF TY_FUND,
         FIKRS      TYPE FMFINCODE-FIKRS,
         FINCODE    TYPE FMFINCODE-FINCODE,
         BEZEICH    TYPE FMFINT-BEZEICH,
         BESCHR     TYPE FMFINT-BESCHR,
         ERFNAME    TYPE FMFINCODE-ERFNAME,
         ERFDAT     TYPE FMFINCODE-ERFDAT,
         AENNAME    TYPE FMFINCODE-AENNAME,
         AENDAT     TYPE FMFINCODE-AENDAT,
         TYPE       TYPE FMFINCODE-TYPE,
         FUND_TYPET TYPE FMFUNDTYPET-FUND_TYPET,
         DATAB      TYPE FMFINCODE-DATAB,
         DATBIS     TYPE FMFINCODE-DATBIS,
         AUGRP      TYPE FMFINCODE-AUGRP,
         FM_OUTPUT  TYPE YTFM_FUND_C5-FM_OUTPUT,
         ONAME      TYPE YE_FM_OUTPUT_NAME,
         ZZSECT     TYPE YTFM_OUTPUT-ZZSECT,
         C5_ID      TYPE YTFM_FUND_C5-C5_ID,
         C5_SEL     TYPE YTFM_FUND_C5-C5_SEL,
       END OF TY_FUND.


DATA GS_FMFINCODE TYPE FMFINCODE.
DATA GS_FUND_C5 TYPE YTFM_FUND_C5.
DATA GT_FUND TYPE TABLE OF TY_FUND.
DATA GO_ALV TYPE REF TO YCL_ALV.
DATA GO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.
DATA GT_COLUMNS TYPE SALV_T_COLUMN.
DATA GV_AUTH TYPE XFELD.
DATA GT_C5_SEL TYPE RANGE OF YE_FM_C5_CONTRIBUTION.

SELECTION-SCREEN BEGIN OF BLOCK B01 WITH FRAME TITLE TEXT-B01.
SELECT-OPTIONS S_FIKRS FOR GS_FMFINCODE-FIKRS.
SELECT-OPTIONS S_FUND FOR GS_FMFINCODE-FINCODE.
SELECT-OPTIONS S_TYPE FOR GS_FMFINCODE-TYPE.
SELECT-OPTIONS S_DATAB FOR GS_FMFINCODE-DATAB NO-EXTENSION.
SELECT-OPTIONS S_DATBIS FOR GS_FMFINCODE-DATBIS NO-EXTENSION.
SELECT-OPTIONS S_OUTPUT FOR GS_FUND_C5-FM_OUTPUT.
SELECT-OPTIONS S_C5_ID FOR GS_FUND_C5-C5_ID NO INTERVALS.
PARAMETERS P_C5_SEL AS CHECKBOX.
SELECTION-SCREEN END OF BLOCK B01.

START-OF-SELECTION.

  IF P_C5_SEL = ABAP_TRUE.
    APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = 'X' ) TO GT_C5_SEL.
  ENDIF.

  "Get funds
  SELECT F~FIKRS,
         F~FINCODE,
         T~BEZEICH,
         T~BESCHR,
         F~ERFNAME,
         F~ERFDAT,
         F~AENNAME,
         F~AENDAT,
         F~TYPE,
         G~FUND_TYPET,
         F~DATAB,
         F~DATBIS,
         F~AUGRP,
         C~FM_OUTPUT,
         H~ONAME,
         O~ZZSECT,
         C~C5_ID,
         C~C5_SEL
         FROM FMFINCODE AS F LEFT OUTER JOIN FMFINT AS T ON  T~SPRAS = @SY-LANGU
                                                         AND T~FIKRS = F~FIKRS
                                                         AND T~FINCODE = F~FINCODE
                             LEFT OUTER JOIN YTFM_FUND_C5 AS C ON  C~FIKRS = F~FIKRS
                                                               AND C~FINCODE = F~FINCODE
                             LEFT OUTER JOIN FMFUNDTYPET AS G ON  G~FM_AREA = F~FIKRS
                                                              AND G~FUND_TYPE = F~TYPE
                                                              AND G~LANGU = @SY-LANGU
                             LEFT OUTER JOIN YTFM_OUTPUT AS O ON O~FM_OUTPUT = C~FM_OUTPUT
                             LEFT OUTER JOIN YTFM_OUTPUT_T AS H ON  H~SPRSL = @SY-LANGU
                                                                AND H~FM_OUTPUT = C~FM_OUTPUT
         WHERE F~FIKRS IN @S_FIKRS
         AND   F~FINCODE IN @S_FUND
         AND   F~TYPE IN @S_TYPE
         AND   F~DATAB IN @S_DATAB
         AND   F~DATBIS IN @S_DATBIS
         AND   C~FM_OUTPUT IN @S_OUTPUT
         AND   C~C5_ID IN @S_C5_ID
         AND   C~C5_SEL IN @GT_C5_SEL
         INTO TABLE @GT_FUND.

  SORT GT_FUND BY FIKRS FINCODE C5_ID.

  "Check authority
  LOOP AT GT_FUND INTO DATA(LS_FUND).
    GV_AUTH = ABAP_FALSE.
    "Check FM area
    CALL FUNCTION 'FM_AUTH_CHECK_FM_AREA'
      EXPORTING
        I_FIKRS    = LS_FUND-FIKRS
        I_ACTVT    = '03'
*       I_ACTVT_A  =
*       I_MSGTY    =
      IMPORTING
        E_FLG_AUTH = GV_AUTH
*       E_FLG_AUTH_A       =
      .
    IF GV_AUTH = ABAP_FALSE.
      DELETE GT_FUND.
      CONTINUE.
    ENDIF.
    "Check fund
    CALL FUNCTION 'FMAU_AUTHORITY_FIFM'
      EXPORTING
        I_ACTVT          = '03'
*       I_ACTVT_A        = ' '
*       I_AUTH_OBJECT    = ' '
        I_FIKRS          = LS_FUND-FIKRS
*       I_DATE           = ' '
*       I_GJAHR          = ' '
*       I_VERSN          = ' '
        I_FINCODE        = LS_FUND-FINCODE
*       I_FMFCTR         = ' '
*       I_FMCI           = ' '
*       I_MSGTY          = ' '
*       I_FICA_CCT       = ' '
*       I_FICA_WCT       = ' '
*       I_BUDGET_PERIOD  =
      IMPORTING
        EX_AUTH          = GV_AUTH
*       EX_AUTH_A        =
      EXCEPTIONS
        NO_AUTHORIZATION = 1
        OTHERS           = 2.
    IF SY-SUBRC <> 0 OR GV_AUTH = ABAP_FALSE.
      DELETE GT_FUND.
      CONTINUE.
    ENDIF.
  ENDLOOP.

  "Display ALV
  GO_ALV = NEW YCL_ALV( ).
  GO_ALV->YIF_ALV_DISPLAY~INIT_ALV( CHANGING IT_TABLE = GT_FUND ).
  GO_ALV->YIF_ALV_DISPLAY~SET_MAIN_FUNCTIONS( IV_REPORT = SY-REPID ).

  TRY.
      GO_COLUMN ?= GO_ALV->MO_COLUMNS->GET_COLUMN( 'C5_SEL' ).
      GO_COLUMN->SET_CELL_TYPE( IF_SALV_C_CELL_TYPE=>CHECKBOX ).
    CATCH CX_SALV_NOT_FOUND.
  ENDTRY.
  "Set key
  GO_ALV->MO_COLUMNS->SET_KEY_FIXATION( ABAP_TRUE ).
  TRY.
      GO_COLUMN ?= GO_ALV->MO_COLUMNS->GET_COLUMN( 'FIKRS' ).
      GO_COLUMN->SET_KEY( ABAP_TRUE ).
    CATCH CX_SALV_NOT_FOUND.
  ENDTRY.
  TRY.
      GO_COLUMN ?= GO_ALV->MO_COLUMNS->GET_COLUMN( 'FINCODE' ).
      GO_COLUMN->SET_KEY( ABAP_TRUE ).
    CATCH CX_SALV_NOT_FOUND.
  ENDTRY.
  "Set sorted columns
  APPEND 'FIKRS' TO GT_COLUMNS.
  APPEND 'FINCODE' TO GT_COLUMNS.
  GO_ALV->YIF_ALV_DISPLAY~SET_SORTED_COLUMS( GT_COLUMNS ).
  "Display ALV
  GO_ALV->YIF_ALV_DISPLAY~DISPLAY_ALV( ).