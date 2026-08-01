* ==== CLASS POOL YCL_FM_FI_COMPARE_BL_TMP ====
CLASS-POOL .
*"* class pool for class YCL_FM_FI_COMPARE_BL_TMP

*"* local type definitions
INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CCDEF.

*"* class YCL_FM_FI_COMPARE_BL_TMP definition
*"* public declarations
  INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CU.
*"* protected declarations
  INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CO.
*"* private declarations
  INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CI.
ENDCLASS. "YCL_FM_FI_COMPARE_BL_TMP definition

*"* macro definitions
INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CCMAC.
*"* local class implementation
INCLUDE YCL_FM_FI_COMPARE_BL_TMP======CCIMP.

CLASS YCL_FM_FI_COMPARE_BL_TMP IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_FI_COMPARE_BL_TMP implementation


* ---- YCL_FM_FI_COMPARE_BL_TMP======CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_FMCI,
      FIPEX TYPE FMCI-FIPEX,
      POTYP TYPE FMCI-POTYP,
    END OF TY_FMCI .
  TYPES:
    BEGIN OF TY_TOTAL_DATA,
      HKONT TYPE HKONT,
      "twaer TYPE twaer,
      GJAHR TYPE GJAHR,
      BETRG TYPE WERTV9,
      WAERS TYPE WAERH,
    END OF TY_TOTAL_DATA .
  TYPES:
    BEGIN OF TY_RESULT,
      HKONT      TYPE HKONT,
      TXT50      TYPE TXT50_SKAT,
      "twaer      TYPE twaer,
      GJAHR      TYPE GJAHR,
      WAERS      TYPE WAERH,
      BETRG_FM   TYPE WERTV9,
      BETRG_FI   TYPE WERTV9,
      BETRG_DIFF TYPE WERTV9,
      BRATE_DIFF TYPE WERTV9,
      EXCHA_DIFF TYPE WERTV9,
      TOTAL_DIFF TYPE WERTV9,
      STATUS     TYPE P_99S_STATU,
    END OF TY_RESULT .
  TYPES:
    BEGIN OF TY_FMI,
      FMBELNR TYPE FM_BELNR,
      FMBUZEI TYPE FM_BUZEI,
      BUKRS   TYPE BUKRS,
      GJAHR   TYPE GJAHR,
      FIKRS   TYPE FIKRS,
      FISTL   TYPE FISTL,
      FINCODE TYPE BP_GEBER,
      GSBER   TYPE GSBER,
      FIPEX   TYPE FM_FIPEX,
      WRTTP   TYPE CO_WRTTP,
      VRGNG   TYPE CO_VORGANG,
      BTART   TYPE FM_BTART,
      BUDAT   TYPE BUDAT,
      FKBTR   TYPE FM_FKBTR,
      TRBTR   TYPE FM_TRBTR,
      TWAER   TYPE TWAER,
      HKONT   TYPE HKONT,
      KNBELNR TYPE BELNR_D,
      KNGJAHR TYPE GJAHR,
      KNBUZEI TYPE BUZEI,
*      refbn          TYPE co_refbn,
*      rfpos          TYPE cc_rfpos,
*      zzbrimpact     TYPE ze_braffected,
*      zzamountbrlc   TYPE ze_amountbr_lc,
*      zzamountbrdiff TYPE ze_amountbr_diff,
    END OF TY_FMI .
  TYPES:
    TTY_FMI TYPE TABLE OF TY_FMI .
  TYPES:
    BEGIN OF TY_DETAIL,
      HKONT          TYPE FMIFIIT-HKONT,
      FIKRS          TYPE FMIFIIT-FIKRS,
      FMBELNR        TYPE FMIFIIT-FMBELNR,
      FMBUZEI        TYPE FMIFIIT-FMBUZEI,
      FKBTR          TYPE FMIFIIT-FKBTR,
      TRBTR          TYPE FMIFIIT-TRBTR,
      TWAER          TYPE FMIFIIT-TWAER,
      FISTL          TYPE FMIFIIT-FISTL,
      FINCODE        TYPE FMIFIIT-FONDS,
      FIPEX          TYPE FMIFIIT-FIPEX,
      GSBER          TYPE FMIFIIT-BUS_AREA,
      WRTTP          TYPE FMIFIIT-WRTTP,
      KNGJAHR        TYPE FMIFIIT-KNGJAHR,
      KNBELNR        TYPE FMIFIIT-KNBELNR,
      KNBUZEI        TYPE FMIFIIT-KNBUZEI,
      BUDAT          TYPE BKPF-BUDAT,
      SHKZG          TYPE BSEG-SHKZG,
      DMBTR          TYPE BSEG-DMBTR,
      WRBTR          TYPE BSEG-WRBTR,
      PSWSL          TYPE BSEG-PSWSL,
      ZZBRIMPACT     TYPE ZE_BRAFFECTED,
      ZZAMOUNTBRDIFF TYPE ZE_AMOUNTBR_DIFF,
      FINAL_DIFF     TYPE WERTV9,
    END OF TY_DETAIL .
  TYPES:
    BEGIN OF TY_SAKNR,
      SAKNR  TYPE SKAT-SAKNR,
      TEXT50 TYPE SKAT-TXT50,
    END OF TY_SAKNR .
  TYPES:
    BEGIN OF TY_BSEG,
      BUKRS TYPE BSEG-BUKRS,
      BELNR TYPE BSEG-BELNR,
      GJAHR TYPE BSEG-GJAHR,
      BUZEI TYPE BSEG-BUZEI,
      SHKZG TYPE BSEG-SHKZG,
      HKONT TYPE BSEG-HKONT,
      DMBTR TYPE BSEG-DMBTR,
      WRBTR TYPE BSEG-WRBTR,
      PSWSL TYPE BSEG-PSWSL,
      "waers TYPE bkpf-waers,
      BUDAT TYPE BKPF-BUDAT,
      WWERT TYPE BKPF-WWERT,
    END OF TY_BSEG .
  TYPES:
    BEGIN OF TY_FUND,
      FIKRS   TYPE FIKRS,
      FINCODE TYPE BP_GEBER,
      TYPE    TYPE FM_FUNDTYPE,
    END OF TY_FUND .

  DATA MV_DISPLAY_RESTRICTION TYPE CHAR1 .
  DATA MV_FI_INT TYPE LVC_INT .
  DATA MV_FM_INT TYPE LVC_INT .
  DATA MS_RESULT_SELECTED TYPE TY_RESULT .
  DATA MV_EXP_SIGN TYPE CHAR1 .
  DATA MV_REV_SIGN TYPE CHAR1 .
  DATA MO_BR_EXCHANGE_RATE_BL TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL .
  DATA MV_FIKRS TYPE FIKRS .
  DATA:
    MT_FM_TOTAL TYPE SORTED TABLE OF TY_TOTAL_DATA WITH UNIQUE KEY HKONT GJAHR .
  DATA:
    MT_FI_TOTAL TYPE SORTED TABLE OF TY_TOTAL_DATA WITH UNIQUE KEY HKONT GJAHR .
  DATA MP_BUKRS TYPE BUKRS .
  DATA MP_GJAHR TYPE GJAHR .
  DATA MR_MONAT TYPE FIRANGE_T_MONAT.
  DATA MR_HKONT TYPE YTTFI_HKONT_RANGE.
  DATA:
    MR_WRTTP TYPE RANGE OF FM_WRTTP .
  DATA MV_WAERS TYPE WAERS .
  DATA MO_SALV_TABLE TYPE REF TO CL_SALV_TABLE .
  DATA:
    MT_RESULT TYPE TABLE OF TY_RESULT .
  DATA:
    MT_FMCI TYPE SORTED TABLE OF TY_FMCI WITH UNIQUE KEY FIPEX .
  DATA:
    MT_DETAIL TYPE SORTED TABLE OF TY_DETAIL WITH NON-UNIQUE KEY HKONT .
  DATA:
    MT_SAKNR TYPE SORTED TABLE OF TY_SAKNR WITH UNIQUE KEY SAKNR .
  DATA:
    MT_BSEG TYPE SORTED TABLE OF TY_BSEG WITH UNIQUE KEY BUKRS BELNR GJAHR BUZEI .
  DATA:
    MT_BSEG_READ TYPE SORTED TABLE OF TY_BSEG WITH UNIQUE KEY BUKRS BELNR GJAHR BUZEI .
  DATA:
    MT_FUND TYPE SORTED TABLE OF TY_FUND WITH UNIQUE KEY FIKRS FINCODE .

  METHODS GET_FI_DETAIL .
  METHODS GET_FUND_TYPE
    IMPORTING
      !IV_FIKRS      TYPE FIKRS
      !IV_FINCODE    TYPE BP_GEBER
    RETURNING
      VALUE(RV_TYPE) TYPE FM_FUNDTYPE .
  METHODS SET_COLOR
    IMPORTING
      !IV_TYPE        TYPE CHAR2
      !IV_NEW         TYPE XFELD DEFAULT ABAP_FALSE
      !IV_ADD         TYPE XFELD DEFAULT ABAP_FALSE
    RETURNING
      VALUE(RT_COLOR) TYPE LVC_T_SCOL .
  METHODS GET_SAKNR_TXT .
  METHODS GET_FI_LINE
    IMPORTING
      !IV_BUKRS TYPE BUKRS
      !IV_BELNR TYPE BELNR_D
      !IV_GJAHR TYPE GJAHR
      !IV_BUZEI TYPE BUZEI
    EXPORTING
      !ES_BSEG  TYPE TY_BSEG
      !EV_FIRST TYPE XFELD .
  METHODS HANDLE_USER_COMMAND
      FOR EVENT ADDED_FUNCTION OF CL_SALV_EVENTS_TABLE
    IMPORTING
      !E_SALV_FUNCTION .
  METHODS SET_FM_AMOUNT_SIGN
    IMPORTING
      !IV_FIPEX  TYPE FM_FIPEX
    CHANGING
      !CS_AMOUNT TYPE ANY .
  METHODS EXTRACT_GLOBAL_AMOUNT
    IMPORTING
      !IV_BR_IMPACT     TYPE ZE_BRAFFECTED
      !IV_HKONT         TYPE HKONT
    EXPORTING
      VALUE(EV_BR_DIFF) TYPE WERTV9 .
  METHODS GET_FM_DETAIL .
  METHODS COMPARE_FM_FI_TOTAL .
  METHODS GET_FI_TOTAL .
  METHODS GET_FM_ACCOUNTS
    RETURNING
      VALUE(RV_SUBRC) TYPE SY-SUBRC .
  METHODS GET_FM_TOTAL .

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM001 ----
  METHOD COMPARE_FM_FI_TOTAL.

    DATA LS_RESULT TYPE TY_RESULT.
    DATA LT_FMI TYPE TTY_FMI.

    LOOP AT MT_FI_TOTAL INTO DATA(LS_FI_TOTAL).
      CLEAR: LS_RESULT.
      MOVE-CORRESPONDING LS_FI_TOTAL TO LS_RESULT.
      LS_RESULT-BETRG_FI = LS_FI_TOTAL-BETRG.
      "Get G/L account text
      READ TABLE MT_SAKNR INTO DATA(LS_SAKNR) WITH KEY SAKNR = LS_FI_TOTAL-HKONT.
      IF SY-SUBRC = 0.
        LS_RESULT-TXT50 = LS_SAKNR-TEXT50.
      ENDIF.
      "Get corresponding FM line
      READ TABLE MT_FM_TOTAL INTO DATA(LS_FM_TOTAL) WITH KEY HKONT = LS_FI_TOTAL-HKONT
                                                             "twaer = ls_fi_total-twaer
                                                             GJAHR = LS_FI_TOTAL-GJAHR.
      IF SY-SUBRC = 0.
        LS_RESULT-BETRG_FM = LS_FM_TOTAL-BETRG.
        DELETE MT_FM_TOTAL INDEX SY-TABIX.
        "BR difference
        ME->EXTRACT_GLOBAL_AMOUNT( EXPORTING IV_BR_IMPACT = 'X'
                                             IV_HKONT = LS_FM_TOTAL-HKONT
                                             "iv_twaer = ls_fm_total-twaer
                                   IMPORTING EV_BR_DIFF = LS_RESULT-BRATE_DIFF ).
        "Exchange rate difference
        ME->EXTRACT_GLOBAL_AMOUNT( EXPORTING IV_BR_IMPACT = 'E'
                                             IV_HKONT = LS_FM_TOTAL-HKONT
                                             "iv_twaer = ls_fm_total-twaer
                                   IMPORTING EV_BR_DIFF = LS_RESULT-EXCHA_DIFF ).
      ENDIF.
      "FI FM difference
      LS_RESULT-BETRG_DIFF = LS_RESULT-BETRG_FM - LS_RESULT-BETRG_FI.
      IF LS_RESULT-BETRG_DIFF = 0 AND MV_DISPLAY_RESTRICTION = C_DIFF_DATABASE.
        CONTINUE.
      ENDIF.
      "Total difference
      LS_RESULT-TOTAL_DIFF = LS_RESULT-BETRG_DIFF + LS_RESULT-BRATE_DIFF + LS_RESULT-EXCHA_DIFF.
      IF LS_RESULT-TOTAL_DIFF = 0.
        IF MV_DISPLAY_RESTRICTION = C_DIFF_BR.
          CONTINUE.
        ENDIF.
        WRITE ICON_LED_GREEN TO LS_RESULT-STATUS AS ICON.
      ELSE.
        WRITE ICON_LED_RED TO LS_RESULT-STATUS AS ICON.
      ENDIF.
      "Set to table result
      APPEND LS_RESULT TO MT_RESULT.
    ENDLOOP.

    "Manage remaining resords tn FM total table
    LOOP AT MT_FM_TOTAL INTO LS_FM_TOTAL.
      CLEAR LS_RESULT.
      MOVE-CORRESPONDING LS_FM_TOTAL TO LS_RESULT.
      "Get G/L account text
      READ TABLE MT_SAKNR INTO LS_SAKNR WITH KEY SAKNR = LS_FM_TOTAL-HKONT.
      IF SY-SUBRC = 0.
        LS_RESULT-TXT50 = LS_SAKNR-TEXT50.
      ENDIF.
      "BR difference
      ME->EXTRACT_GLOBAL_AMOUNT( EXPORTING IV_BR_IMPACT = 'X'
                                           IV_HKONT = LS_FM_TOTAL-HKONT
                                           "iv_twaer = ls_fm_total-twaer
                                 IMPORTING EV_BR_DIFF = LS_RESULT-BRATE_DIFF ).
      "Exchange rate difference
      ME->EXTRACT_GLOBAL_AMOUNT( EXPORTING IV_BR_IMPACT = 'E'
                                           IV_HKONT = LS_FM_TOTAL-HKONT
                                           "iv_twaer = ls_fm_total-twaer
                                 IMPORTING EV_BR_DIFF = LS_RESULT-EXCHA_DIFF ).
      "FI FM difference
      LS_RESULT-BETRG_FM = LS_RESULT-BETRG_DIFF = LS_FM_TOTAL-BETRG.
      "Total difference
      LS_RESULT-TOTAL_DIFF = LS_RESULT-BETRG_DIFF + LS_RESULT-BRATE_DIFF + LS_RESULT-EXCHA_DIFF.
      IF LS_RESULT-TOTAL_DIFF = 0.
        WRITE ICON_LED_GREEN TO LS_RESULT-STATUS AS ICON.
      ELSE.
        WRITE ICON_LED_RED TO LS_RESULT-STATUS AS ICON.
      ENDIF.
      "Set to table result
      APPEND LS_RESULT TO MT_RESULT.
    ENDLOOP.

    CLEAR: MT_FM_TOTAL, MT_FI_TOTAL.

    SORT MT_RESULT.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM002 ----
  METHOD CONSTRUCTOR.

    MP_BUKRS = IV_BUKRS.
    MP_GJAHR = IV_GJAHR.
    MR_MONAT = IT_MONAT.
    MR_HKONT = IT_HKONT.
    "mr_waers = it_waers.

    "Get local currency and FM area from company code
    SELECT SINGLE WAERS, FIKRS FROM T001 WHERE BUKRS = @MP_BUKRS INTO ( @MV_WAERS, @MV_FIKRS ).

    "Set Value type
    MR_WRTTP = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = '54' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = '57' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = '61' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = '66' ) ).

    "instanciate BR business logic class
    MO_BR_EXCHANGE_RATE_BL = NEW YCL_FM_BR_EXCHANGE_RATE_BL( ).

    "Get Commitment item attributes
    SELECT FIPEX, POTYP FROM FMCI WHERE FIKRS = @MV_FIKRS
                                  AND   GJAHR = '0000'
                        INTO TABLE @MT_FMCI.

    "Get sign for expenditure
    CALL FUNCTION 'FM_SIGN_GET_FOR_EXPENDITURE'
      IMPORTING
        E_SIGN          = MV_EXP_SIGN
        E_SIGN_REVENUES = MV_REV_SIGN.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM003 ----
  METHOD DISPLAY_TOTAL.

    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.
    DATA LO_LAYOUT TYPE REF TO CL_SALV_LAYOUT.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.

    TRY.
        CALL METHOD CL_SALV_TABLE=>FACTORY
*      EXPORTING
*        list_display   = IF_SALV_C_BOOL_SAP=>FALSE
*        r_container    =
*        container_name =
          IMPORTING
            R_SALV_TABLE = MO_SALV_TABLE
          CHANGING
            T_TABLE      = MT_RESULT.
      CATCH CX_SALV_MSG .
    ENDTRY.

    "mo_salv_table->get_functions( )->set_all( ).
    MO_SALV_TABLE->SET_SCREEN_STATUS( PFSTATUS = 'SALV_STATUS'
                                      REPORT   = IV_REPID
                                      SET_FUNCTIONS = MO_SALV_TABLE->C_FUNCTIONS_ALL ).

    DATA(LO_EVENTS) = MO_SALV_TABLE->GET_EVENT( ).
    SET HANDLER ME->HANDLE_USER_COMMAND FOR LO_EVENTS.

    "ALV layout
    LO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = IV_REPID.
    LO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    LO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).
    LO_LAYOUT->SET_DEFAULT( ABAP_TRUE ).

    MO_SALV_TABLE->GET_DISPLAY_SETTINGS( )->SET_STRIPED_PATTERN( ABAP_TRUE ).

    MO_SALV_TABLE->GET_COLUMNS( )->SET_OPTIMIZE( ABAP_TRUE ).

    "set column title
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'BETRG_FM' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Total of FM amounts' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'BETRG_FI' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Total of FI amounts' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'BETRG_DIFF' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI FM difference' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'BRATE_DIFF' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'BR difference' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'EXCHA_DIFF' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Exchange difference' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'TOTAL_DIFF' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Total difference' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= MO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'STATUS' ).
        LO_COLUMN->SET_ALIGNMENT( IF_SALV_C_ALIGNMENT=>CENTERED ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.


    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM004 ----
  METHOD EXTRACT_GLOBAL_AMOUNT.

    CLEAR: EV_BR_DIFF.

    LOOP AT MT_DETAIL INTO DATA(LS_DETAIL) WHERE HKONT = IV_HKONT
                                           "AND   twaer = iv_twaer
                                           AND ZZBRIMPACT = IV_BR_IMPACT.
      ADD LS_DETAIL-ZZAMOUNTBRDIFF TO EV_BR_DIFF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM005 ----
  METHOD GET_FI_DETAIL.

*    SELECT s~bukrs, s~belnr, s~gjahr, s~buzei, s~shkzg, s~hkont, s~dmbtr, s~wrbtr, s~pswsl "k~waers
*           FROM bseg AS s
**           INNER JOIN bkpf AS k ON  k~bukrs = s~bukrs
**                                AND k~belnr = s~belnr
**                                AND k~gjahr = s~gjahr
*           WHERE s~bukrs = @mp_bukrs
*           AND   s~gjahr = @mp_gjahr
*           AND   s~hkont IN @mr_hkont
*           "AND   ( k~waers IN @mr_waers OR s~pswsl IN @mr_waers )
*           INTO TABLE @mt_bseg.
*
*    "DELETE mt_bseg WHERE waers NOT IN mr_waers AND pswsl NOT IN mr_waers.

    SELECT S~BUKRS, S~BELNR, S~GJAHR, S~BUZEI, S~SHKZG, S~HKONT, S~DMBTR, S~WRBTR, S~PSWSL, S~BUDAT, K~WWERT
           FROM BSIS AS S
           INNER JOIN BKPF AS K ON  K~BUKRS = S~BUKRS
                                AND K~BELNR = S~BELNR
                                AND K~GJAHR = S~GJAHR
           WHERE S~BUKRS = @MP_BUKRS
           AND   S~HKONT IN @MR_HKONT
           AND   S~GJAHR = @MP_GJAHR
           AND   S~MONAT IN @MR_MONAT
           INTO TABLE @MT_BSEG.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM006 ----
  METHOD GET_FI_LINE.

    CLEAR: ES_BSEG, EV_FIRST.

    "Check if BSEG entry already read
    READ TABLE MT_BSEG_READ INTO ES_BSEG WITH KEY BUKRS = IV_BUKRS
                                                  BELNR = IV_BELNR
                                                  GJAHR = IV_GJAHR
                                                  BUZEI = IV_BUZEI.
    IF SY-SUBRC <> 0.
      READ TABLE MT_BSEG INTO ES_BSEG WITH KEY BUKRS = IV_BUKRS
                                               BELNR = IV_BELNR
                                               GJAHR = IV_GJAHR
                                               BUZEI = IV_BUZEI.
      IF ES_BSEG IS NOT INITIAL.
        DELETE MT_BSEG INDEX SY-TABIX.
        INSERT ES_BSEG INTO TABLE MT_BSEG_READ.
      ENDIF.
      EV_FIRST = ABAP_TRUE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM007 ----
  METHOD GET_FI_TOTAL.

    DATA LT_GLT0 TYPE TABLE OF GLT0.
    DATA LV_NUM(2) TYPE N.
    DATA LV_FIELDNAME TYPE FIELDNAME.
    DATA LS_TOTAL TYPE TY_TOTAL_DATA.
    FIELD-SYMBOLS <AMOUNT> TYPE ANY.
    DATA LT_TOTAL TYPE TABLE OF TY_TOTAL_DATA.

    SELECT * FROM GLT0 WHERE RLDNR = '00'
                       AND   RRCTY = '0'
                       AND   RVERS = '001'
                       AND   BUKRS = @MP_BUKRS
                       AND   RYEAR = @MP_GJAHR
                       AND   RACCT IN @MR_HKONT
                       "AND   rtcur IN @mr_waers
             INTO TABLE @LT_GLT0.

    LOOP AT LT_GLT0 INTO DATA(LS_GLT0).
      CLEAR: LV_NUM, LS_TOTAL.
      LS_TOTAL-HKONT = LS_GLT0-RACCT.
      LS_TOTAL-GJAHR = LS_GLT0-RYEAR.
      "ls_total-twaer = ls_glt0-rtcur.
      LS_TOTAL-WAERS = MV_WAERS.
      DO 16 TIMES.
        ADD 1 TO LV_NUM.
        CHECK LV_NUM IN MR_MONAT.
        LV_FIELDNAME = |LS_GLT0-HSL{ LV_NUM }|.
        ASSIGN (LV_FIELDNAME) TO <AMOUNT>.
        ADD <AMOUNT> TO LS_TOTAL-BETRG.
      ENDDO.
      MULTIPLY LS_TOTAL-BETRG BY -1.
      CHECK LS_TOTAL-BETRG IS NOT INITIAL.
      COLLECT LS_TOTAL INTO LT_TOTAL.
    ENDLOOP.

    DELETE LT_TOTAL WHERE BETRG = 0.

    INSERT LINES OF LT_TOTAL INTO TABLE MT_FI_TOTAL.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM008 ----
  METHOD GET_FM_ACCOUNTS.

    DATA LT_SAKNR TYPE RANGE OF SAKNR.

    RV_SUBRC = 0.

    "Get FM accounts: with commitment item = 30
    SELECT 'I', 'EQ', SKB1~SAKNR FROM SKB1
                                 LEFT OUTER JOIN FMCI ON  FMCI~FIKRS = @MV_FIKRS
                                                      AND FMCI~GJAHR = '0000'
                                                      AND FMCI~FIPEX = SKB1~FIPOS
                                 WHERE SKB1~BUKRS = @MP_BUKRS
                                 AND   SKB1~SAKNR IN @MR_HKONT
                                 AND   FMCI~FIVOR = '30'
                            INTO TABLE @LT_SAKNR.
    IF LT_SAKNR IS NOT INITIAL.
      MR_HKONT = LT_SAKNR.
    ELSE.
      RV_SUBRC = 8.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM009 ----
  METHOD GET_FM_DETAIL.

    TYPES LTY_AMOUNT TYPE FM_FKBTRPY.
    DATA LS_DETAIL TYPE TY_DETAIL.
    DATA LT_FMI TYPE TTY_FMI.
    DATA LS_FM_TOTAL TYPE TY_TOTAL_DATA.
    DATA LS_FI_TOTAL TYPE TY_TOTAL_DATA.
    DATA LV_DATE TYPE DATUM.

    SELECT T~FMBELNR,
           T~FMBUZEI,
           T~BUKRS,
           T~GJAHR,
           T~FIKRS,
           T~FISTL,
           T~FONDS AS FINCODE,
           T~BUS_AREA AS GSBER,
           T~FIPEX,
           T~WRTTP,
           T~VRGNG,
           T~BTART,
           H~BUDAT,
           T~FKBTR,
           T~TRBTR,
           T~TWAER,
           T~HKONT,
           T~KNBELNR,
           T~KNGJAHR,
           T~KNBUZEI
           FROM FMIFIIT AS T LEFT OUTER JOIN FMIFIHD AS H ON  H~FMBELNR = T~FMBELNR
                                                          AND H~FIKRS = T~FIKRS
                             WHERE T~FIKRS = @MV_FIKRS
                             "AND   ( t~btart <> @fmfi_con_btart_reduction OR t~vrgng <> @fmfi_con_orgvg_goods_receipt )
                             "AND   t~btart <> @fmfi_con_btart_cfold
                             AND   T~BTART = '0100'
                             AND   T~RLDNR = '9A'
                             AND   T~GJAHR = @MP_GJAHR
                             AND   T~PERIO IN @MR_MONAT
                             AND   T~WRTTP IN @MR_WRTTP
                             AND   T~BUKRS = @MP_BUKRS
                             AND   T~HKONT IN @MR_HKONT
           INTO TABLE @LT_FMI.

    LOOP AT LT_FMI INTO DATA(LS_FMI).
      "Check if sign to be changed
      SET_FM_AMOUNT_SIGN( EXPORTING IV_FIPEX = LS_FMI-FIPEX
                          CHANGING CS_AMOUNT = LS_FMI-FKBTR ).
      SET_FM_AMOUNT_SIGN( EXPORTING IV_FIPEX = LS_FMI-FIPEX
                         CHANGING CS_AMOUNT = LS_FMI-TRBTR ).
      "Get corresponding FI detail line
      ME->GET_FI_LINE( EXPORTING IV_BUKRS = LS_FMI-BUKRS
                                 IV_BELNR = LS_FMI-KNBELNR
                                 IV_GJAHR = LS_FMI-KNGJAHR
                                 IV_BUZEI = LS_FMI-KNBUZEI
                       IMPORTING ES_BSEG = DATA(LS_BSEG)
                                 EV_FIRST = DATA(LV_BSEG_FIRST) ).
      "Initiate detail table
      CLEAR LS_DETAIL.
      MOVE-CORRESPONDING LS_FMI TO LS_DETAIL.

      "Check for Budget rate amounts: only if difference between FI and FM for account
      CLEAR LS_FM_TOTAL.
      READ TABLE MT_FM_TOTAL INTO LS_FM_TOTAL WITH KEY HKONT = LS_FMI-HKONT
                                                       GJAHR = LS_FMI-GJAHR.
      CLEAR LS_FI_TOTAL.
      READ TABLE MT_FI_TOTAL INTO LS_FI_TOTAL WITH KEY HKONT = LS_FMI-HKONT
                                                       GJAHR = LS_FMI-GJAHR.
      IF LS_FM_TOTAL-BETRG <> LS_FI_TOTAL-BETRG.
        "Check conditions for budget rate
        IF MO_BR_EXCHANGE_RATE_BL->CHECK_CONDITIONS( IV_BUKRS = LS_FMI-BUKRS
                                                     IV_FIKRS = LS_FMI-FIKRS
                                                     IV_GSBER = LS_FMI-GSBER
                                                     IV_WAERS = LS_FMI-TWAER
                                                     IV_FIPEX = LS_FMI-FIPEX
                                                     IV_VRGNG = LS_FMI-VRGNG
                                                     IV_FTYPE = ME->GET_FUND_TYPE( IV_FIKRS = LS_FMI-FIKRS
                                                                                   IV_FINCODE = LS_FMI-FINCODE ) ) = ABAP_TRUE.
          "If translation date is different from posting date, use translation date
          IF LS_BSEG-WWERT IS NOT INITIAL.
            LV_DATE = LS_BSEG-WWERT.
          ELSE.
            LV_DATE = LS_BSEG-BUDAT.
          ENDIF.
          "Calculate BR impact
          MO_BR_EXCHANGE_RATE_BL->GET_BR_IMPACT( EXPORTING IV_BUKRS = LS_FMI-BUKRS
                                                           IV_GJAHR = LS_FMI-GJAHR
                                                           IV_FKBTRP = CONV LTY_AMOUNT( LS_FMI-FKBTR )
                                                           IV_TRBTRP = CONV LTY_AMOUNT( LS_FMI-TRBTR )
                                                           IV_TWAER = LS_FMI-TWAER
                                                           IV_WRTTP = LS_FMI-WRTTP
                                                           IV_VRGNG = LS_FMI-VRGNG
                                                           IV_BTART = LS_FMI-BTART
                                                           IV_BUDAT = LV_DATE
                                                           IV_BSEG_DMBTR = LS_BSEG-DMBTR
                                                           IV_BSEG_SHKZG = LS_BSEG-SHKZG
                                                           IV_FINCODE = LS_FMI-FINCODE
                                                 IMPORTING EV_ZZBRIMPACTED = LS_DETAIL-ZZBRIMPACT
                                                           EV_ZZAMOUNTBRDIFF = LS_DETAIL-ZZAMOUNTBRDIFF ).
        ENDIF.
      ENDIF.

      "Fill detail table
      IF LS_BSEG-SHKZG = 'H'.
        MULTIPLY LS_BSEG-DMBTR BY -1.
        MULTIPLY LS_BSEG-WRBTR BY -1.
      ENDIF.
      IF LV_BSEG_FIRST = ABAP_TRUE.
        LS_DETAIL-SHKZG = LS_BSEG-SHKZG.
        LS_DETAIL-DMBTR = LS_BSEG-DMBTR.
        LS_DETAIL-WRBTR = LS_BSEG-WRBTR.
        LS_DETAIL-PSWSL = LS_BSEG-PSWSL.
      ENDIF.

      "Set final difference
      LS_DETAIL-FINAL_DIFF = LS_DETAIL-FKBTR - LS_DETAIL-DMBTR - LS_DETAIL-ZZAMOUNTBRDIFF.

      INSERT LS_DETAIL INTO TABLE MT_DETAIL.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00A ----
  METHOD GET_FM_TOTAL.

    DATA LT_FMIT TYPE TABLE OF FMIT.
    DATA LV_NUM(2) TYPE N.
    DATA LV_FIELDNAME TYPE FIELDNAME.
    DATA LS_TOTAL TYPE TY_TOTAL_DATA.
    FIELD-SYMBOLS <AMOUNT> TYPE ANY.
    DATA LT_TOTAL TYPE TABLE OF TY_TOTAL_DATA.

    "Get FM total
    SELECT * FROM FMIT WHERE RLDNR = '9A'
                       AND   RRCTY = '0'     "Actual
                       AND   RVERS = '000'
                       AND   RYEAR = @MP_GJAHR
                       "AND   rtcur IN @mr_waers
                       AND   RWRTTP IN @MR_WRTTP
                       AND   RBUKRS = @MP_BUKRS
                       AND   ( RBTART <> @FMFI_CON_BTART_REDUCTION OR RVRGNG <> @FMFI_CON_ORGVG_GOODS_RECEIPT )
                       AND   RBTART <> @FMFI_CON_BTART_CFOLD
                       AND   RHKONT IN @MR_HKONT
             INTO TABLE @LT_FMIT.

    LOOP AT LT_FMIT INTO DATA(LS_FMIT).
      CLEAR: LV_NUM, LS_TOTAL.
      LS_TOTAL-HKONT = LS_FMIT-RHKONT.
      LS_TOTAL-GJAHR = LS_FMIT-RYEAR.
      "ls_total-twaer = ls_fmit-rtcur.
      LS_TOTAL-WAERS = MV_WAERS.
      DO 16 TIMES.
        ADD 1 TO LV_NUM.
        CHECK LV_NUM IN MR_MONAT.
        LV_FIELDNAME = |LS_FMIT-HSL{ LV_NUM }|.
        ASSIGN (LV_FIELDNAME) TO <AMOUNT>.
        ADD <AMOUNT> TO LS_TOTAL-BETRG.
      ENDDO.
      CHECK LS_TOTAL-BETRG IS NOT INITIAL.
      "Check if sign to be changed
*      set_fm_amount_sign( EXPORTING iv_fipex = ls_fmit-rfipex
*                          CHANGING cs_amount = ls_total-betrg ).
      COLLECT LS_TOTAL INTO LT_TOTAL.
    ENDLOOP.

    DELETE LT_TOTAL WHERE BETRG = 0.

    INSERT LINES OF LT_TOTAL INTO TABLE MT_FM_TOTAL.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00B ----
  METHOD GET_FUND_TYPE.

    DATA LS_FUND TYPE TY_FUND.

    READ TABLE MT_FUND INTO LS_FUND WITH KEY FIKRS = IV_FIKRS
                                             FINCODE = IV_FINCODE.
    IF SY-SUBRC <> 0.
      SELECT SINGLE FIKRS, FINCODE, TYPE FROM FMFINCODE WHERE FIKRS = @IV_FIKRS
                                                        AND   FINCODE = @IV_FINCODE
                                         INTO @LS_FUND.
      IF SY-SUBRC <> 0.
        LS_FUND-FIKRS = IV_FIKRS.
        LS_FUND-FINCODE = IV_FINCODE.
      ENDIF.
      INSERT LS_FUND INTO TABLE MT_FUND.
    ENDIF.

    RV_TYPE = LS_FUND-TYPE.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00C ----
  METHOD GET_SAKNR_TXT.

    CLEAR MT_SAKNR.

    SELECT SAKNR, TXT50 FROM SKAT WHERE SPRAS = @SY-LANGU
                                  AND   KTOPL = 'UNES'
                                  AND   SAKNR IN @MR_HKONT
                        INTO TABLE @MT_SAKNR.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00D ----
  METHOD GET_TOTAL_DATA.

    IF IV_30_ONLY = ABAP_TRUE.
      IF ME->GET_FM_ACCOUNTS( ) <> 0.
        MESSAGE TEXT-I01 TYPE 'I'.
        EXIT.
      ENDIF.
    ENDIF.

    """"Display restriction:
    " D: Only difference between FM and FI in database
    " B: Only difference including Budget Rate impact
    " N: No restriction, display all
    MV_DISPLAY_RESTRICTION = IV_DISPLAY_RESTRICTION.

    ME->GET_SAKNR_TXT( ).

    ME->GET_FM_TOTAL( ).
    ME->GET_FI_TOTAL( ).
    ME->GET_FI_DETAIL( ).
    ME->GET_FM_DETAIL( ).
    ME->COMPARE_FM_FI_TOTAL( ).

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00E ----
  METHOD HANDLE_USER_COMMAND.

    TYPES: BEGIN OF LTY_SELECTION.
             INCLUDE TYPE TY_DETAIL.
             TYPES: CELL_COLOR TYPE LVC_T_SCOL,
           END OF LTY_SELECTION.

    DATA LT_SELECTION TYPE TABLE OF LTY_SELECTION.
    DATA LS_SELECTION TYPE LTY_SELECTION.
    DATA LO_POPUP TYPE REF TO YCL_CA_ALV_IN_POPUP.
    DATA LV_TITLE TYPE TEXT50.
    DATA LS_CELL_COLOR TYPE LINE OF LVC_T_SCOL.

    DATA(LT_ROWS) = MO_SALV_TABLE->GET_SELECTIONS( )->GET_SELECTED_ROWS( ).
    READ TABLE LT_ROWS INTO DATA(LV_ROW) INDEX 1.
    IF SY-SUBRC <> 0.
      MESSAGE I024(YCOMMON).
      EXIT.
    ENDIF.

    CLEAR MS_RESULT_SELECTED.
    READ TABLE MT_RESULT INTO MS_RESULT_SELECTED INDEX LV_ROW.
    CHECK SY-SUBRC = 0.

    CASE E_SALV_FUNCTION.
      WHEN 'YDETAIL'.
        LOOP AT MT_DETAIL INTO DATA(LS_DETAIL) WHERE HKONT = MS_RESULT_SELECTED-HKONT.
          CLEAR LS_SELECTION.
          MOVE-CORRESPONDING LS_DETAIL TO LS_SELECTION.
          APPEND LS_SELECTION TO LT_SELECTION.
        ENDLOOP.
        SORT LT_SELECTION BY KNBELNR ASCENDING KNBUZEI ASCENDING SHKZG DESCENDING.
        "Set color.
        CLEAR: LS_SELECTION, MV_FM_INT, MV_FI_INT.
        LOOP AT LT_SELECTION ASSIGNING FIELD-SYMBOL(<LS_SELECTION>).
          APPEND LINES OF SET_COLOR( IV_TYPE = 'FM' ) TO <LS_SELECTION>-CELL_COLOR.
          IF <LS_SELECTION>-KNGJAHR <> LS_SELECTION-KNGJAHR OR
             <LS_SELECTION>-KNBELNR <> LS_SELECTION-KNBELNR OR
             <LS_SELECTION>-KNBUZEI <> LS_SELECTION-KNBUZEI.
            APPEND LINES OF SET_COLOR( IV_TYPE = 'FI' IV_NEW = 'X' ) TO <LS_SELECTION>-CELL_COLOR.
          ELSE.
            APPEND LINES OF SET_COLOR( IV_TYPE = 'FI' ) TO <LS_SELECTION>-CELL_COLOR.
          ENDIF.
          IF <LS_SELECTION>-FINAL_DIFF <> 0.
            APPEND LINES OF SET_COLOR( IV_TYPE = 'DI' ) TO <LS_SELECTION>-CELL_COLOR.
          ENDIF.
          LS_SELECTION = <LS_SELECTION>.
        ENDLOOP.
        "Put FI lines without FM correspondance
        LOOP AT MT_BSEG INTO DATA(LS_BSEG) WHERE HKONT = MS_RESULT_SELECTED-HKONT.
          CLEAR LS_SELECTION.
          LS_SELECTION-HKONT = LS_BSEG-HKONT.
          LS_SELECTION-KNGJAHR = LS_BSEG-GJAHR.
          LS_SELECTION-KNBELNR = LS_BSEG-BELNR.
          LS_SELECTION-KNBUZEI = LS_BSEG-BUZEI.
          IF LS_BSEG-SHKZG = 'H'.
            MULTIPLY LS_BSEG-DMBTR BY -1.
            MULTIPLY LS_BSEG-WRBTR BY -1.
          ENDIF.
          LS_SELECTION-DMBTR = LS_BSEG-DMBTR.
          LS_SELECTION-WRBTR = LS_BSEG-WRBTR.
          LS_SELECTION-PSWSL = LS_BSEG-PSWSL.
          LS_SELECTION-FINAL_DIFF = - LS_BSEG-DMBTR.
          IF LS_SELECTION-FINAL_DIFF <> 0.
            APPEND LINES OF SET_COLOR( IV_TYPE = 'DI' ) TO LS_SELECTION-CELL_COLOR.
          ENDIF.
          APPEND LINES OF SET_COLOR( IV_TYPE = 'FI' IV_NEW = 'X' IV_ADD = 'X' ) TO LS_SELECTION-CELL_COLOR.
          APPEND LS_SELECTION TO LT_SELECTION.
        ENDLOOP.

        "Call ALV popup
        LO_POPUP = NEW YCL_CA_ALV_IN_POPUP( ).
        LV_TITLE = |Detail FM / FI lines for account { MS_RESULT_SELECTED-HKONT }|.
        LO_POPUP->EXECUTE( EXPORTING IV_TITLE = LV_TITLE
                                     IV_END_COL = 180
                                     IO_ALV_EXTENDED = ME
                           CHANGING CT_TABLE = LT_SELECTION ).
        FREE LO_POPUP.
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00F ----
  METHOD SET_COLOR.

    DATA LS_COLOR TYPE LVC_S_SCOL.
    DATA LV_COL TYPE LVC_COL.
    DATA LV_INT TYPE LVC_INT.

    CLEAR RT_COLOR.

    CASE IV_TYPE.
      WHEN 'FM'.
        LV_COL = COL_GROUP.
        IF MV_FM_INT = 0.
          MV_FM_INT = 1.
        ELSE.
          MV_FM_INT = 0.
        ENDIF.
        RT_COLOR = VALUE #( ( FNAME = 'FMBELNR' COLOR-COL = LV_COL COLOR-INT = MV_FM_INT )
                            ( FNAME = 'FMBUZEI' COLOR-COL = LV_COL COLOR-INT = MV_FM_INT )
                            ( FNAME = 'FKBTR' COLOR-COL = LV_COL COLOR-INT = MV_FM_INT )
                            ( FNAME = 'TRBTR' COLOR-COL = LV_COL COLOR-INT = MV_FM_INT )
                            ( FNAME = 'TWAER' COLOR-COL = LV_COL COLOR-INT = MV_FM_INT ) ).
      WHEN 'FI'.
        IF IV_ADD = ABAP_FALSE.
          LV_COL = COL_POSITIVE.
        ELSE.
          LV_COL = COL_KEY.
        ENDIF.
        IF IV_NEW = ABAP_TRUE.
          IF MV_FI_INT = 0.
            MV_FI_INT = 1.
          ELSE.
            MV_FI_INT = 0.
          ENDIF.
          APPEND VALUE #( FNAME = 'BUDAT' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
          APPEND VALUE #( FNAME = 'SHKZG' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
          APPEND VALUE #( FNAME = 'DMBTR' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
          APPEND VALUE #( FNAME = 'WRBTR' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
          APPEND VALUE #( FNAME = 'WAERS' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
        ENDIF.
        APPEND VALUE #( FNAME = 'KNGJAHR' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
        APPEND VALUE #( FNAME = 'KNBELNR' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
        APPEND VALUE #( FNAME = 'KNBUZEI' COLOR-COL = LV_COL COLOR-INT = MV_FI_INT ) TO RT_COLOR.
      WHEN 'DI'.
        APPEND VALUE #( FNAME = 'FINAL_DIFF' COLOR-COL = COL_NEGATIVE COLOR-INT = 0 ) TO RT_COLOR.
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00G ----
  METHOD SET_FM_AMOUNT_SIGN.

    READ TABLE MT_FMCI INTO DATA(LS_FMCI) WITH KEY FIPEX = IV_FIPEX.
    IF SY-SUBRC = 0.
      CASE LS_FMCI-POTYP.
        WHEN '3'.
          IF MV_EXP_SIGN = '+'.
            MULTIPLY CS_AMOUNT BY -1.
          ENDIF.
        WHEN '2' OR '5'.
          IF MV_REV_SIGN = '-'.
            MULTIPLY CS_AMOUNT BY -1.
          ENDIF.
      ENDCASE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CM00H ----
  METHOD YIF_ALV_EXTENDED~ADD_ALV_PROPERTIES.

    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.
    DATA LO_HEADER TYPE REF TO CL_SALV_FORM_LAYOUT_GRID.
    DATA LO_SALV_DISPLAY_SETTINGS TYPE REF TO CL_SALV_DISPLAY_SETTINGS.
    DATA LS_COLOR TYPE LVC_S_SCOL.

    CO_SALV_TABLE->GET_FUNCTIONS( )->SET_ALL( ).
    CO_SALV_TABLE->GET_COLUMNS( )->SET_OPTIMIZE( ABAP_TRUE ).

    "Set header list
    LO_SALV_DISPLAY_SETTINGS = CO_SALV_TABLE->GET_DISPLAY_SETTINGS( ).
    LO_SALV_DISPLAY_SETTINGS->SET_LIST_HEADER( |G/L Account { MS_RESULT_SELECTED-HKONT } { MS_RESULT_SELECTED-TXT50 }| ).
    LO_SALV_DISPLAY_SETTINGS->SET_LIST_HEADER_SIZE( CL_SALV_DISPLAY_SETTINGS=>C_HEADER_SIZE_LARGE ).

    "Set column for cell enabling
    TRY.
        CO_SALV_TABLE->GET_COLUMNS( )->SET_COLOR_COLUMN( 'CELL_COLOR' ).
      CATCH CX_SALV_DATA_ERROR.
    ENDTRY.

    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'FMBELNR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FM doc' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'FMBUZEI' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FM item' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'FKBTR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FM Local amount' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'TRBTR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FM TC amount' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'FIPEX' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'CI' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'WRTTP' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Val type' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'TWAER' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FM TCurr' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'KNBELNR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI doc' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'KNBUZEI' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI item' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
        LO_COLUMN->SET_ALIGNMENT( IF_SALV_C_ALIGNMENT=>CENTERED ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'SHKZG' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'D/C' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
        LO_COLUMN->SET_ALIGNMENT( IF_SALV_C_ALIGNMENT=>CENTERED ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'DMBTR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI Local amount' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
        LO_COLUMN->SET_ZERO( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'WRBTR' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI TC amount' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
        LO_COLUMN->SET_ZERO( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'PSWSL' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'FI TCurr' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'ZZBRIMPACT' ).
        LO_COLUMN->SET_ALIGNMENT( IF_SALV_C_ALIGNMENT=>CENTERED ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.
        LO_COLUMN ?= CO_SALV_TABLE->GET_COLUMNS( )->GET_COLUMN( 'FINAL_DIFF' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Final diff' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    "Set sum
    TRY.
        CO_SALV_TABLE->GET_AGGREGATIONS( )->ADD_AGGREGATION( COLUMNNAME = 'FKBTR'
                                                             AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
        CO_SALV_TABLE->GET_AGGREGATIONS( )->ADD_AGGREGATION( COLUMNNAME = 'DMBTR'
                                                             AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
        CO_SALV_TABLE->GET_AGGREGATIONS( )->ADD_AGGREGATION( COLUMNNAME = 'ZZAMOUNTBRDIFF'
                                                             AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
        CO_SALV_TABLE->GET_AGGREGATIONS( )->ADD_AGGREGATION( COLUMNNAME = 'FINAL_DIFF'
                                                             AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
      CATCH CX_SALV_ERROR.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CO ----
PROTECTED SECTION.

* ---- YCL_FM_FI_COMPARE_BL_TMP======CU ----
CLASS YCL_FM_FI_COMPARE_BL_TMP DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES YIF_ALV_EXTENDED .

  CONSTANTS C_NO_RESTRICTION TYPE CHAR1 VALUE 'N' ##NO_TEXT.
  CONSTANTS C_DIFF_DATABASE TYPE CHAR1 VALUE 'D' ##NO_TEXT.
  CONSTANTS C_DIFF_BR TYPE CHAR1 VALUE 'B' ##NO_TEXT.

  METHODS DISPLAY_TOTAL
    IMPORTING
      !IV_REPID TYPE SY-REPID OPTIONAL .
  METHODS GET_TOTAL_DATA
    IMPORTING
      !IV_30_ONLY TYPE FM30ONLY
      !IV_DISPLAY_RESTRICTION TYPE CHAR1 .
  METHODS CONSTRUCTOR
    IMPORTING
      !IV_BUKRS TYPE BUKRS
      !IV_GJAHR TYPE GJAHR
      !IT_MONAT TYPE FIRANGE_T_MONAT
      !IT_HKONT TYPE YTTFI_HKONT_RANGE OPTIONAL .