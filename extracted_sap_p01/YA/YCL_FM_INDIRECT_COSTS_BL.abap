* ==== CLASS POOL YCL_FM_INDIRECT_COSTS_BL ====
CLASS-POOL .
*"* class pool for class YCL_FM_INDIRECT_COSTS_BL

*"* local type definitions
INCLUDE YCL_FM_INDIRECT_COSTS_BL======CCDEF.

*"* class YCL_FM_INDIRECT_COSTS_BL definition
*"* public declarations
  INCLUDE YCL_FM_INDIRECT_COSTS_BL======CU.
*"* protected declarations
  INCLUDE YCL_FM_INDIRECT_COSTS_BL======CO.
*"* private declarations
  INCLUDE YCL_FM_INDIRECT_COSTS_BL======CI.
ENDCLASS. "YCL_FM_INDIRECT_COSTS_BL definition

*"* macro definitions
INCLUDE YCL_FM_INDIRECT_COSTS_BL======CCMAC.
*"* local class implementation
INCLUDE YCL_FM_INDIRECT_COSTS_BL======CCIMP.

CLASS YCL_FM_INDIRECT_COSTS_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_INDIRECT_COSTS_BL implementation


* ---- YCL_FM_INDIRECT_COSTS_BL======CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_FUND,
      FIKRS     TYPE FMFINCODE-FIKRS,
      FINCODE   TYPE FMFINCODE-FINCODE,
      TYPE      TYPE FMFINCODE-TYPE,
      FM_OUTPUT TYPE YE_FM_OUTPUT,
      ZZSECT    TYPE YTFM_OUTPUT-ZZSECT,
      OTYPE     TYPE YTFM_OUTPUT-OTYPE,
      ONAME     TYPE YTFM_OUTPUT_T-ONAME,
    END OF TY_FUND .
  TYPES:
    BEGIN OF TY_PERIOD,
      ID(1) TYPE N,
      GJAHR TYPE FMIT-RYEAR,
      BEGFP TYPE FM_PERIODE,
      ENDFP TYPE FM_PERIODE,
    END OF TY_PERIOD .
  TYPES:
    TTY_PERIOD TYPE TABLE OF TY_PERIOD .
  TYPES:
    BEGIN OF TY_DATA,
      ZZSECT    TYPE YTFM_OUTPUT-ZZSECT,
      ONAME     TYPE YTFM_OUTPUT_T-ONAME,
      FM_OUTPUT TYPE YE_FM_OUTPUT,
      WAERS     TYPE WAERS,
      ALLOC     TYPE WERTV9,
      EXPEND    TYPE WERTV9,
      OBLIG     TYPE WERTV9,
      MCA       TYPE WERTV9,
    END OF TY_DATA .
  TYPES:
    TTY_DATA TYPE TABLE OF TY_DATA .
  TYPES:
    BEGIN OF TY_FMBD,
      FM_AREA  TYPE FMBH-FM_AREA,
      DOCYEAR  TYPE FMBH-DOCYEAR,
      DOCNR    TYPE FMBH-DOCNR,
      RPMAX    TYPE FMBL-RPMAX,
      DOCDATE  TYPE FMBH-DOCDATE,
      DOCLN    TYPE FMBL-DOCLN,
      FISCYEAR TYPE FMBL-FISCYEAR,
      BUDTYPE  TYPE FMBL-BUDTYPE,
      FUND     TYPE FMBL-FUND,
      FUNDSCTR TYPE FMBL-FUNDSCTR,
      WAERS    TYPE FM01-WAERS,
      LVAL01   TYPE FMBL-LVAL01,
      LVAL02   TYPE FMBL-LVAL02,
      LVAL03   TYPE FMBL-LVAL03,
      LVAL04   TYPE FMBL-LVAL04,
      LVAL05   TYPE FMBL-LVAL05,
      LVAL06   TYPE FMBL-LVAL06,
      LVAL07   TYPE FMBL-LVAL07,
      LVAL08   TYPE FMBL-LVAL08,
      LVAL09   TYPE FMBL-LVAL09,
      LVAL10   TYPE FMBL-LVAL10,
      LVAL11   TYPE FMBL-LVAL11,
      LVAL12   TYPE FMBL-LVAL12,
      LVAL13   TYPE FMBL-LVAL13,
      LVAL14   TYPE FMBL-LVAL14,
      LVAL15   TYPE FMBL-LVAL15,
      LVAL16   TYPE FMBL-LVAL16,
    END OF TY_FMBD .
  TYPES:
    BEGIN OF TY_FMI1,
      FMBELNR TYPE FMIFIHD-FMBELNR,
      FIKRS   TYPE FMIFIHD-FIKRS,
      FMBUZEI TYPE FMIFIIT-FMBUZEI,
      BTART   TYPE FMIFIIT-BTART,
      RLDNR   TYPE FMIFIIT-RLDNR,
      GJAHR   TYPE FMIFIIT-GJAHR,
      STUNR   TYPE FMIFIIT-STUNR,
      BUDAT   TYPE FMIFIHD-BUDAT,
      TRBTR   TYPE FMIFIIT-TRBTR,
      TWAER   TYPE FMIFIIT-TWAER,
      FKBTR   TYPE FMIFIIT-FKBTR,
      WAERS   TYPE FM01-WAERS,
      FONDS   TYPE FMIFIIT-FONDS,
      FISTL   TYPE FMIFIIT-FISTL,
      FIPEX   TYPE FMIFIIT-FIPEX,
      WRTTP   TYPE FMIFIIT-WRTTP,
      KNGJAHR TYPE FMIFIIT-KNGJAHR,
      KNBELNR TYPE FMIFIIT-KNBELNR,
      WWERT   TYPE BKPF-WWERT,
      KURS2   TYPE BKPF-KURS2,
    END OF TY_FMI1 .
  TYPES:
    BEGIN OF TY_FMI2,
      REFBN TYPE FMIOI-REFBN,
      REFBT TYPE FMIOI-REFBT,
      RFORG TYPE FMIOI-RFORG,
      RFPOS TYPE FMIOI-RFPOS,
      RFKNT TYPE FMIOI-RFKNT,
      RFETE TYPE FMIOI-RFETE,
      RCOND TYPE FMIOI-RCOND,
      RFTYP TYPE FMIOI-RFTYP,
      RFSYS TYPE FMIOI-RFSYS,
      BTART TYPE FMIOI-BTART,
      RLDNR TYPE FMIOI-RLDNR,
      GJAHR TYPE FMIOI-GJAHR,
      STUNR TYPE FMIOI-STUNR,
      FONDS TYPE FMIOI-FONDS,
      FISTL TYPE FMIOI-FISTL,
      FIPEX TYPE FMIOI-FIPEX,
      WRTTP TYPE FMIOI-WRTTP,
      FIKRS TYPE FMIOI-FIKRS,
      BUDAT TYPE FMIOI-BUDAT,
      TRBTR TYPE FMIOI-TRBTR,
      TWAER TYPE FMIOI-TWAER,
      FKBTR TYPE FMIOI-FKBTR,
      WAERS TYPE FM01-WAERS,
    END OF TY_FMI2 .
  TYPES:
    BEGIN OF TY_FUND_C5,
           FIKRS     TYPE FIKRS,
           FINCODE   TYPE BP_GEBER,
           YEAR_FROM TYPE YE_CA_YEAR_FROM,
           YEAR_TO   TYPE YE_CA_YEAR_TO,
         END OF TY_FUND_C5 .

  DATA MP_C5_SEL TYPE YE_FM_C5_CONTRIBUTION .
  DATA MO_CURRENCY_OP TYPE REF TO YCL_CA_CURRENCY_OP .
  CONSTANTS C_USD TYPE WAERS VALUE 'USD' ##NO_TEXT.
  DATA MV_CONVERSION_USD TYPE BOOLEAN .
  DATA MO_CONV_RATE TYPE REF TO YCL_FM_CONVERSION_RATE .
  DATA MP_FIKRS TYPE FIKRS .
  DATA:
    MT_FMBD TYPE TABLE OF TY_FMBD .
  DATA:
    MT_FMI1 TYPE SORTED TABLE OF TY_FMI1 WITH NON-UNIQUE KEY FIKRS FONDS .
  DATA:
    MT_FMI2 TYPE SORTED TABLE OF TY_FMI2 WITH NON-UNIQUE KEY FIKRS FONDS .
  DATA MV_BLDAT TYPE BLDAT .
  DATA MV_BEGDA TYPE BEGDA .
  DATA MV_ENDDA TYPE ENDDA .
  DATA MV_REPID TYPE SY-REPID .
  DATA MT_OFFICE4 TYPE TTY_DATA .
  DATA MT_OUTPUT TYPE TTY_DATA .
  DATA MT_PERIOD TYPE TTY_PERIOD .
  DATA:
    MT_FUND TYPE SORTED TABLE OF TY_FUND WITH UNIQUE KEY FIKRS FINCODE .
  DATA MP_VERSI TYPE VERSN .
  DATA:
    MR_TYPE1 TYPE RANGE OF FM_FUNDTYPE .
  DATA:
    MR_FUND TYPE RANGE OF BP_GEBER .
  DATA:
    MT_FUND_C5 TYPE SORTED TABLE OF TY_FUND_C5 WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MR_SECTOR TYPE RANGE OF ZHR_SECT .
  DATA:
    MR_OUTPUT TYPE RANGE OF YE_FM_OUTPUT .
  DATA:
    MT_LIST TYPE TABLE OF YSFM_INDIRECT_COST_LIST .
  DATA:
    MT_OUTPUT_TXT TYPE SORTED TABLE OF YTFM_OUTPUT_T WITH UNIQUE KEY SPRSL FM_OUTPUT .
  DATA:
    MR_WRTTP_EXP TYPE RANGE OF FM_WRTTP .
  DATA:
    MR_WRTTP_OBL TYPE RANGE OF FM_WRTTP .
  DATA:
    MR_GJAHR TYPE RANGE OF GJAHR .
  DATA:
    MR_C5_ID TYPE RANGE OF YE_FM_C5_ID .
  DATA MO_COLUMNS TYPE REF TO CL_SALV_COLUMNS_TABLE .
  DATA MO_DISPLAY_SETTINGS TYPE REF TO CL_SALV_DISPLAY_SETTINGS .
  DATA MO_FUNCTIONS TYPE REF TO CL_SALV_FUNCTIONS_LIST .
  DATA MO_SALV_TABLE TYPE REF TO CL_SALV_TABLE .
  DATA MO_LAYOUT TYPE REF TO CL_SALV_LAYOUT .

  METHODS CONVERT_AMOUNT
    IMPORTING
      !IV_AMOUNT TYPE FM_FKBTR
      !IV_CURRENCY TYPE WAERS
      !IV_KURSF TYPE KURSF OPTIONAL
      !IV_DATE TYPE DATUM
    EXPORTING
      !EV_AMOUNT TYPE FM_FKBTR .
  METHODS SET_HEADER .
  METHODS COMPUTE_DATA .
  METHODS GET_CASE_ID
    IMPORTING
      !IS_FUND TYPE TY_FUND
      !IV_GJAHR TYPE GJAHR
    RETURNING
      VALUE(RV_CASE_ID) TYPE YE_FM_CASE_ID .
  METHODS EXTRACT_AMOUNT
    IMPORTING
      !IS_FM_DATA TYPE TY_FMBD
      !IV_PERIOD_RATE TYPE BOOLEAN DEFAULT ABAP_FALSE
    RETURNING
      VALUE(RV_AMOUNT) TYPE HSLXX9 .
  METHODS PREPARE_DATA .
  METHODS READ_DATA_FROM_DB .
  METHODS SET_COLUMNS .
  METHODS SET_DISPLAY_SETTINGS .
  METHODS SET_FUNCTIONS .
  METHODS SET_LAYOUT .

* ---- YCL_FM_INDIRECT_COSTS_BL======CM001 ----
  METHOD COMPUTE_DATA.

    DATA LT_LIST TYPE TABLE OF YSFM_INDIRECT_COST_LIST.
    DATA LS_LIST TYPE YSFM_INDIRECT_COST_LIST.
    DATA LV_ALLOC_SUM TYPE WERTV9.
    DATA LV_EXPEND_SUM TYPE WERTV9.
    DATA LV_OBLIG_SUM TYPE WERTV9.
    DATA LS_OFFICE4 TYPE TY_DATA.
    DATA LS_CUMUL TYPE YSFM_INDIRECT_COST_DATA.

    LOOP AT MT_OUTPUT INTO DATA(LS_OUTPUT).

      AT NEW ZZSECT.
        CLEAR: LT_LIST, LV_ALLOC_SUM, LV_EXPEND_SUM, LV_OBLIG_SUM.
      ENDAT.

      AT NEW FM_OUTPUT.
        READ TABLE MT_OUTPUT_TXT INTO DATA(LS_OUTPUT_TXT) WITH KEY FM_OUTPUT = LS_OUTPUT-FM_OUTPUT.
        IF SY-SUBRC <> 0.
          CLEAR LS_OUTPUT_TXT.
        ENDIF.
      ENDAT.

      MOVE-CORRESPONDING LS_OUTPUT TO LS_LIST.
      LS_LIST-ODESC = LS_OUTPUT_TXT-ODESC.
      ADD LS_OUTPUT-ALLOC TO LV_ALLOC_SUM.
      ADD LS_OUTPUT-EXPEND TO LV_EXPEND_SUM.
      ADD LS_OUTPUT-OBLIG TO LV_OBLIG_SUM.
      APPEND LS_LIST TO LT_LIST.

      AT END OF ZZSECT.
        CLEAR: LS_OFFICE4, LS_CUMUL.
        "Aggregate office4 amounts
        READ TABLE MT_OFFICE4 INTO LS_OFFICE4 WITH KEY ZZSECT = LS_OUTPUT-ZZSECT.
        LOOP AT LT_LIST INTO LS_LIST.
          "Allocation
          LS_LIST-ALLOC_WEIGHT = LS_LIST-ALLOC * 100 / LV_ALLOC_SUM.
          ADD LS_LIST-ALLOC TO LS_CUMUL-ALLOC.
          ADD LS_LIST-ALLOC_WEIGHT TO LS_CUMUL-ALLOC_WEIGHT.
          IF LS_CUMUL-ALLOC = LV_ALLOC_SUM AND LS_CUMUL-ALLOC_WEIGHT <> 100.
            "Readjust weight if necessary
            LS_LIST-ALLOC_WEIGHT = LS_LIST-ALLOC_WEIGHT - ( LS_CUMUL-ALLOC_WEIGHT - 100 ).
            LS_CUMUL-ALLOC_WEIGHT = 100.
          ENDIF.
          LS_LIST-ALLOC_4 = LS_OFFICE4-ALLOC * LS_LIST-ALLOC_WEIGHT / 100.
          "expenditure
          LS_LIST-EXPEND_WEIGHT = LS_LIST-EXPEND * 100 / LV_EXPEND_SUM.
          ADD LS_LIST-EXPEND TO LS_CUMUL-EXPEND.
          ADD LS_LIST-EXPEND_WEIGHT TO LS_CUMUL-EXPEND_WEIGHT.
          IF LS_CUMUL-EXPEND = LV_EXPEND_SUM AND LS_CUMUL-EXPEND_WEIGHT <> 100.
            "Readjust weight if necessary
            LS_LIST-EXPEND_WEIGHT = LS_LIST-EXPEND_WEIGHT - ( LS_CUMUL-EXPEND_WEIGHT - 100 ).
            LS_CUMUL-EXPEND_WEIGHT = 100.
          ENDIF.
          LS_LIST-EXPEND_4 = LS_OFFICE4-EXPEND * LS_LIST-EXPEND_WEIGHT / 100.
          "Obligation
          LS_LIST-OBLIG_WEIGHT = LS_LIST-OBLIG * 100 / LV_OBLIG_SUM.
          ADD LS_LIST-OBLIG TO LS_CUMUL-OBLIG.
          ADD LS_LIST-OBLIG_WEIGHT TO LS_CUMUL-OBLIG_WEIGHT.
          IF LS_CUMUL-OBLIG = LV_OBLIG_SUM AND LS_CUMUL-OBLIG_WEIGHT <> 100.
            "Readjust weight if necessary
            LS_LIST-OBLIG_WEIGHT = LS_LIST-OBLIG_WEIGHT - ( LS_CUMUL-OBLIG_WEIGHT - 100 ).
            LS_CUMUL-OBLIG_WEIGHT = 100.
          ENDIF.
          LS_LIST-OBLIG_4 = LS_OFFICE4-OBLIG * LS_LIST-OBLIG_WEIGHT / 100.
          "MCA
*          ls_list-mca_weight = ls_list-mca * 100 / lv_mca_sum.
*          ADD ls_list-mca TO ls_cumul-mca.
*          ADD ls_list-mca_weight TO ls_cumul-mca_weight.
*          IF ls_cumul-mca = lv_mca_sum AND ls_cumul-mca_weight <> 100.
*            "Readjust weight if necessary
*            ls_list-mca_weight = ls_list-mca_weight - ( ls_cumul-mca_weight - 100 ).
*            ls_cumul-mca_weight = 100.
*          ENDIF.
*          ls_list-mca_4 = ls_office4-mca * ls_list-mca_weight / 100.
          APPEND LS_LIST TO MT_LIST.
        ENDLOOP.
      ENDAT.

    ENDLOOP.

    SORT MT_LIST.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM002 ----
  METHOD DISPLAY_ALV.

    MV_REPID = IV_REPID.

    "Init ALV
    TRY.
        CALL METHOD CL_SALV_TABLE=>FACTORY
*      EXPORTING
*        list_display   = IF_SALV_C_BOOL_SAP=>FALSE
*        r_container    =
*        container_name =
          IMPORTING
            R_SALV_TABLE = MO_SALV_TABLE
          CHANGING
            T_TABLE      = MT_LIST.
      CATCH CX_SALV_MSG .
    ENDTRY.

    "ALV functions activation
    ME->SET_FUNCTIONS( ).

    "ALV columns
    ME->SET_COLUMNS( ).

    "ALV layout
    ME->SET_LAYOUT( ).

    "Header
    ME->SET_HEADER( ).

    "ALV display settings
    ME->SET_DISPLAY_SETTINGS( ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM003 ----
  METHOD EXTRACT_AMOUNT.

    DATA LV_FIELDNAME TYPE FIELDNAME.
    DATA LV_NUM(3) TYPE N.
    DATA LV_DATE TYPE DATUM.
    FIELD-SYMBOLS <FM_DATA> TYPE ANY.

    DO 16 TIMES.
      ADD 1 TO LV_NUM.
      LV_FIELDNAME = |IS_FM_DATA-LVAL{ LV_NUM+1(2) }|.
      ASSIGN (LV_FIELDNAME) TO <FM_DATA>.
      CHECK <FM_DATA> IS ASSIGNED.
      RV_AMOUNT = RV_AMOUNT - <FM_DATA>.
*      IF iv_period_rate = abap_false.   "convert at sy-datum
*        rv_amount = rv_amount - ( <fm_data> / mo_conv_rate->get_rate( is_fm_data-waers ) ).   "Convert and Inverse sign
*      ELSE.   "convert at amount period
*        rv_amount = rv_amount - ( <fm_data> / mo_conv_rate->get_rate( iv_waers = is_fm_data-waers
*                                                                      iv_gjahr = is_fm_data-docyear
*                                                                      iv_perio = lv_num ) ).   "Convert and Inverse sign
*      ENDIF.
      UNASSIGN <FM_DATA>.
    ENDDO.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM004 ----
  METHOD GET_CASE_ID.

    DATA LS_YSFM1 TYPE YSFM1.

    CLEAR RV_CASE_ID.
    MOVE-CORRESPONDING IS_FUND TO LS_YSFM1.

    CHECK IV_GJAHR <= '2023'.  "Only for biennium until 41 C/5

    "Set IBF flag from C/5 assignment
    LOOP AT MT_FUND_C5 TRANSPORTING NO FIELDS WHERE FIKRS = IS_FUND-FIKRS
                                              AND   FINCODE = IS_FUND-FINCODE
                                              AND   YEAR_FROM <= IV_GJAHR
                                              AND   YEAR_TO >= IV_GJAHR.
      EXIT.
    ENDLOOP.
    IF SY-SUBRC = 0.
      LS_YSFM1-ZZIBF = ABAP_TRUE.
    ELSE.
      LS_YSFM1-ZZIBF = ABAP_FALSE.
    ENDIF.

    TRY.
        CALL METHOD CL_HRPA_FEATURE=>GET_VALUE
          EXPORTING
            FEATURE       = 'YFM01'
            STRUC_CONTENT = LS_YSFM1
          IMPORTING
            RETURN_VALUE  = RV_CASE_ID.
      CATCH CX_HRPA_VIOLATED_ASSERTION .
        "error in feature
        MESSAGE TEXT-M01 TYPE 'E'.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM005 ----
  METHOD GET_DATA.

    IF IV_BLDAT IS INITIAL.
      MV_BLDAT = '99991231'.
    ELSE.
      MV_BLDAT = IV_BLDAT.
    ENDIF.

    MV_CONVERSION_USD = IV_USD_CURRENCY.

    ME->READ_DATA_FROM_DB( ).
    ME->PREPARE_DATA( ).
    ME->COMPUTE_DATA( ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM006 ----
  METHOD PREPARE_DATA.

    DATA LS_DATA TYPE TY_DATA.
    DATA LV_CASE_ID TYPE YE_FM_CASE_ID.
    DATA LV_DATE TYPE DATUM.


    LOOP AT MT_FUND INTO DATA(LS_FUND) WHERE ZZSECT IN MR_SECTOR.
      CLEAR LS_DATA.
      MOVE-CORRESPONDING LS_FUND TO LS_DATA.

      "Get budget only for USD FM area
      IF MV_CONVERSION_USD = ABAP_FALSE.
        "Get allocation data
        LOOP AT MT_FMBD INTO DATA(LS_FMBD) WHERE FM_AREA = LS_FUND-FIKRS
                                           AND   FUND = LS_FUND-FINCODE.
          "Determine case id with feature YFM01
          LV_CASE_ID = ME->GET_CASE_ID( IS_FUND = LS_FUND
                                        IV_GJAHR = LS_FMBD-FISCYEAR ).
          CHECK ( LV_CASE_ID = 'I' AND LS_FMBD-BUDTYPE = '1000' ) OR  "OPG-IBF case
                ( LV_CASE_ID = SPACE AND LS_FMBD-BUDTYPE = '3000' ).  "General case
          LS_DATA-ALLOC = LS_DATA-ALLOC + ME->EXTRACT_AMOUNT( LS_FMBD ).
          LS_DATA-WAERS = LS_FMBD-WAERS.
        ENDLOOP.
      ENDIF.

      "Get expenditure and obligation
      LOOP AT MT_FMI1 INTO DATA(LS_FMI1) WHERE FIKRS = LS_FUND-FIKRS
                                         AND   FONDS = LS_FUND-FINCODE.
        IF LS_FMI1-WRTTP IN MR_WRTTP_EXP.
          IF MV_CONVERSION_USD = ABAP_TRUE.
            CHECK LS_FMI1-TRBTR IS NOT INITIAL.  "to avoid currency adjustment amount
            IF LS_FMI1-WWERT IS NOT INITIAL.
              LV_DATE = LS_FMI1-WWERT.
            ELSE.
              LV_DATE = LS_FMI1-BUDAT.
            ENDIF.
            ME->CONVERT_AMOUNT( EXPORTING IV_AMOUNT = LS_FMI1-TRBTR
                                          IV_CURRENCY = LS_FMI1-TWAER
                                          IV_KURSF = LS_FMI1-KURS2
                                          IV_DATE = LV_DATE
                                IMPORTING EV_AMOUNT = LS_FMI1-FKBTR ).
            LS_DATA-WAERS = C_USD.
          ENDIF.
          LS_DATA-EXPEND = LS_DATA-EXPEND - LS_FMI1-FKBTR.
        ENDIF.

*        IF ls_fmi1-wrttp IN mr_wrttp_obl.
*          ls_data-oblig = ls_data-oblig - ls_fmi1-fkbtr.
*        ENDIF.
      ENDLOOP.
      IF SY-SUBRC = 0 AND LS_DATA-WAERS IS INITIAL.
        LS_DATA-WAERS = LS_FMI1-WAERS.
      ENDIF.

      LOOP AT MT_FMI2 INTO DATA(LS_FMI2) WHERE FIKRS = LS_FUND-FIKRS
                                         AND   FONDS = LS_FUND-FINCODE.
        IF LS_FMI2-WRTTP IN MR_WRTTP_EXP.
          IF MV_CONVERSION_USD = ABAP_TRUE.
            CHECK LS_FMI2-TRBTR IS NOT INITIAL.  "to avoid currency adjustment amount
            ME->CONVERT_AMOUNT( EXPORTING IV_AMOUNT = LS_FMI2-TRBTR
                                          IV_CURRENCY = LS_FMI2-WAERS
                                          IV_DATE = LS_FMI2-BUDAT
                                IMPORTING EV_AMOUNT = LS_FMI2-FKBTR ).
            LS_DATA-WAERS = C_USD.
          ENDIF.
          LS_DATA-EXPEND = LS_DATA-EXPEND - LS_FMI2-FKBTR.
        ENDIF.

*        IF ls_fmi2-wrttp IN mr_wrttp_obl.
*          ls_data-oblig = ls_data-oblig - ls_fmi2-fkbtr.
*        ENDIF.
      ENDLOOP.
      IF SY-SUBRC = 0 AND LS_DATA-WAERS IS INITIAL.
        LS_DATA-WAERS = LS_FMI2-WAERS.
      ENDIF.

      "Check amounts are not null
      CHECK LS_DATA-ALLOC IS NOT INITIAL OR
            LS_DATA-EXPEND IS NOT INITIAL OR
            LS_DATA-OBLIG IS NOT INITIAL.
      CASE LS_FUND-OTYPE.
        WHEN 'OUTPUT'.
          COLLECT LS_DATA INTO MT_OUTPUT.
        WHEN 'OFFICE4'.
          CLEAR: LS_DATA-FM_OUTPUT, LS_DATA-ONAME.
          COLLECT LS_DATA INTO MT_OFFICE4.
      ENDCASE.
    ENDLOOP.

    SORT: MT_OUTPUT, MT_OFFICE4.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM007 ----
  METHOD READ_DATA_FROM_DB.

    DATA LR_BUDTYPE  TYPE RANGE OF BUKU_BUDTYPE.
    DATA LR_FIPEX TYPE RANGE OF FM_FIPEX.
    DATA LR_WRTTP TYPE RANGE OF FM_WRTTP.
    DATA LS_GJAHR LIKE LINE OF MR_GJAHR.
    DATA LR_FIKRS TYPE RANGE OF FIKRS.
    DATA LT_IBF TYPE RANGE OF YE_FM_C5_CONTRIBUTION.

    "Budget type
    LR_BUDTYPE = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = '1000' )
                          ( SIGN = 'I' OPTION = 'EQ' LOW = '3000' ) ).
    "Commitment item
    LR_FIPEX = VALUE #( ( SIGN = 'E' OPTION = 'EQ' LOW = 'GAINS' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'REVENUE' ) ).

    "Get Value type for expenditure
    SELECT 'I', 'EQ', WRTTP INTO TABLE @MR_WRTTP_EXP FROM YTFM_WRTTP_GR WHERE WRTTP_GRP = 'IC_EXP'.
    SORT MR_WRTTP_EXP.
    "Get Value type for obligation
*    SELECT 'I', 'EQ', wrttp INTO TABLE @mr_wrttp_obl FROM ytfm_wrttp_gr WHERE wrttp_grp = 'IC_OBL'.
*    SORT mr_wrttp_obl.
    APPEND LINES OF MR_WRTTP_EXP TO LR_WRTTP.
*    APPEND LINES OF mr_wrttp_obl TO lr_wrttp.

    "set period to analyze
    READ TABLE MR_GJAHR INTO LS_GJAHR INDEX 1.
    IF SY-SUBRC <> 0.  "No period set => exit
      EXIT.
    ENDIF.
    MV_BEGDA = |{ LS_GJAHR-LOW(4) }0101|.
    IF LS_GJAHR-HIGH IS INITIAL.
      MV_ENDDA = |{ LS_GJAHR-LOW(4) }1231|.
    ELSE.
      MV_ENDDA = |{ LS_GJAHR-HIGH(4) }1231|.
    ENDIF.

    "Do USD conversion if necessary
    IF MV_CONVERSION_USD = ABAP_TRUE.
      "Initialize conversion rate class for FM
      LR_FIKRS = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = MP_FIKRS ) ) .
      MO_CONV_RATE = NEW YCL_FM_CONVERSION_RATE( IV_TARGET_WAERS = 'USD'
                                                 IV_BEGDA = MV_BEGDA
                                                 IV_ENDDA = MV_ENDDA
                                                 IT_FIKRS_RANGE = LR_FIKRS
                                                 IV_TYPE = 'D' ).
      READ TABLE MO_CONV_RATE->MT_CONV TRANSPORTING NO FIELDS WITH KEY FIKRS = MP_FIKRS.
      IF SY-SUBRC <> 0.
        MV_CONVERSION_USD = ABAP_FALSE.
      ELSE.
        "initialize currency operation class
        MO_CURRENCY_OP = NEW YCL_CA_CURRENCY_OP( ).
      ENDIF.
    ENDIF.

    "Set IBF flag in range
    IF MP_C5_SEL = ABAP_TRUE.
      APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = ABAP_TRUE ) TO LT_IBF.
    ENDIF.


    "get fund master data
    SELECT DISTINCT A~FIKRS AS FIKRS,
                    A~FINCODE AS FINCODE,
                    A~TYPE AS TYPE,
                    D~FM_OUTPUT,
                    B~ZZSECT AS ZZSECT,
                    B~OTYPE AS OTYPE,
                    C~ONAME AS ONAME
           FROM FMFINCODE AS A
           LEFT OUTER JOIN YTFM_FUND_C5 AS D ON  D~FIKRS = A~FIKRS
                                             AND D~FINCODE = A~FINCODE
           LEFT OUTER JOIN YTFM_OUTPUT AS B ON B~FM_OUTPUT = D~FM_OUTPUT
           LEFT OUTER JOIN YTFM_OUTPUT_T AS C ON  C~SPRSL = @SY-LANGU
                                              AND C~FM_OUTPUT = D~FM_OUTPUT
           WHERE A~FIKRS = @MP_FIKRS
           AND   A~FINCODE IN @MR_FUND
           AND   A~DATAB <= @MV_ENDDA
           AND   A~DATBIS >= @MV_BEGDA
           AND   A~TYPE IN @MR_TYPE1
           AND   D~FM_OUTPUT <> '0000000000'
           AND   D~FM_OUTPUT IN @MR_OUTPUT
           AND   D~C5_SEL IN @LT_IBF
           AND   D~C5_ID IN @MR_C5_ID
           INTO TABLE @MT_FUND.

    CHECK MT_FUND IS NOT INITIAL.

    "Get fund assignment to C/5 period (to replace IBF flag)
    SELECT A~FIKRS, A~FINCODE, B~YEAR_FROM, B~YEAR_TO
           FROM YTFM_FUND_C5 AS A LEFT OUTER JOIN YTFM_C5 AS B ON B~C5_ID = A~C5_ID
           FOR ALL ENTRIES IN @MT_FUND
           WHERE A~FIKRS = @MT_FUND-FIKRS
           AND   A~FINCODE = @MT_FUND-FINCODE
           INTO TABLE @MT_FUND_C5.

    "Get output text table
    SELECT * FROM YTFM_OUTPUT_T WHERE SPRSL = @SY-LANGU
           INTO TABLE @MT_OUTPUT_TXT.

    "Get data for allocation
    SELECT H~FM_AREA,
           H~DOCYEAR,
           H~DOCNR,
           L~RPMAX,
           H~DOCDATE,
           L~DOCLN,
           L~FISCYEAR,
           L~BUDTYPE,
           L~FUND,
           L~FUNDSCTR,
           F~WAERS,
           L~LVAL01,
           L~LVAL02,
           L~LVAL03,
           L~LVAL04,
           L~LVAL05,
           L~LVAL06,
           L~LVAL07,
           L~LVAL08,
           L~LVAL09,
           L~LVAL10,
           L~LVAL11,
           L~LVAL12,
           L~LVAL13,
           L~LVAL14,
           L~LVAL15,
           L~LVAL16
           FROM FMBH AS H
           INNER JOIN FMBL AS L ON  L~FM_AREA = H~FM_AREA
                                AND L~DOCYEAR = H~DOCYEAR
                                AND L~DOCNR = H~DOCNR
           LEFT OUTER JOIN FM01 AS F ON F~FIKRS = H~FM_AREA
           FOR ALL ENTRIES IN @MT_FUND
           WHERE H~FM_AREA = @MT_FUND-FIKRS
           AND   L~FUND = @MT_FUND-FINCODE
           AND   H~VERSION = @MP_VERSI
           AND   H~DOCDATE <= @MV_BLDAT    "Document date
           AND   L~FISCYEAR IN @MR_GJAHR
           AND   L~CMMTITEM IN @LR_FIPEX
           AND   L~VALTYPE = 'B1'
           AND   L~BUDTYPE IN @LR_BUDTYPE
           INTO TABLE @MT_FMBD.

    "Get data for expenditure / obligation
    SELECT H~FMBELNR,
           H~FIKRS,
           I~FMBUZEI,
           I~BTART,
           I~RLDNR,
           I~GJAHR,
           I~STUNR,
           H~BUDAT,
           I~TRBTR,
           I~TWAER,
           I~FKBTR,
           F~WAERS,
           I~FONDS,
           I~FISTL,
           I~FIPEX,
           I~WRTTP,
           I~KNGJAHR,
           I~KNBELNR,
           K~WWERT,
           K~KURS2
           FROM FMIFIHD AS H
           INNER JOIN FMIFIIT AS I ON  I~FMBELNR = H~FMBELNR
                                   AND I~FIKRS = H~FIKRS
           LEFT OUTER JOIN FM01 AS F ON F~FIKRS = H~FIKRS
           LEFT OUTER JOIN BKPF AS K ON  K~BUKRS = I~BUKRS
                                     AND K~BELNR = I~KNBELNR
                                     AND K~GJAHR = I~KNGJAHR
           FOR ALL ENTRIES IN @MT_FUND
           WHERE H~FIKRS = @MT_FUND-FIKRS
           AND   I~FONDS = @MT_FUND-FINCODE
           AND   I~GJAHR IN @MR_GJAHR
           AND   H~BUDAT <= @MV_BLDAT  "Posting date
           AND   I~FIPEX IN @LR_FIPEX
           AND   I~WRTTP IN @LR_WRTTP
           AND   H~LOEKZ = @ABAP_FALSE
           INTO TABLE @MT_FMI1.

*    SELECT a~refbn,
*           a~refbt,
*           a~rforg,
*           a~rfpos,
*           a~rfknt,
*           a~rfete,
*           a~rcond,
*           a~rftyp,
*           a~rfsys,
*           a~btart,
*           a~rldnr,
*           a~gjahr,
*           a~stunr,
*           a~fonds,
*           a~fistl,
*           a~fipex,
*           a~wrttp,
*           a~fikrs,
*           a~budat,
*           a~trbtr,
*           a~twaer,
*           a~fkbtr,
*           f~waers
*           FROM fmioi AS a
*           LEFT OUTER JOIN fm01 AS f ON f~fikrs = a~fikrs
*           FOR ALL ENTRIES IN @mt_fund
*           WHERE a~fikrs = @mt_fund-fikrs
*           AND   a~fonds = @mt_fund-fincode
*           AND   a~gjahr IN @mr_gjahr
*           AND   a~loekz = @abap_false
*           AND   a~budat <= @mv_bldat    "Posting date
*           AND   a~fipex IN @lr_fipex
*           AND   a~wrttp IN @lr_wrttp
*           INTO TABLE @mt_fmi2.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM008 ----
  METHOD SET_COLUMNS.

    DATA LT_COLUMNS TYPE SALV_T_COLUMN_REF.
    DATA LS_COLUMNS TYPE LINE OF SALV_T_COLUMN_REF.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.

    MO_COLUMNS = MO_SALV_TABLE->GET_COLUMNS( ).
    "Column width optimization
    MO_COLUMNS->SET_OPTIMIZE( ABAP_TRUE ).
    "mo_columns->set_key_fixation( abap_true ).

    IF MV_CONVERSION_USD = ABAP_TRUE.
      TRY.
          LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'ALLOC' ).
          LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).
        CATCH CX_SALV_NOT_FOUND.
      ENDTRY.
    ENDIF.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'ALLOC_WEIGHT' ).
        IF MV_CONVERSION_USD = ABAP_TRUE.
          LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).
        ELSE.
          LO_COLUMN->SET_LONG_TEXT( 'Allocation % in sector' ).
          LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        ENDIF.
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'ALLOC_4' ).
        IF MV_CONVERSION_USD = ABAP_TRUE.
          LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).
        ELSE.
          LO_COLUMN->SET_LONG_TEXT( 'Office4 allocation' ).
          LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        ENDIF.
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'EXPEND_WEIGHT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Expenditure % in sector' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'EXPEND_4' ).
        LO_COLUMN->SET_LONG_TEXT( 'Office4 expenditure' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'OBLIG' ).
        LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).   "NME20220907 deactivate obligation
        "lo_column->set_long_text( 'Office4 obligation' ).
        "lo_column->set_fixed_header_text( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.
    TRY.

        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'OBLIG_WEIGHT' ).
        LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).   "NME20220907 deactivate obligation
        "lo_column->set_long_text( 'Obligation % in sector' ).
        "lo_column->set_fixed_header_text( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'OBLIG_4' ).
        LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).   "NME20220907 deactivate obligation
        "lo_column->set_long_text( 'Office4 obligation' ).
        "lo_column->set_fixed_header_text( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'MCA_WEIGHT' ).
        LO_COLUMN->SET_LONG_TEXT( 'MCA % in sector' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'MCA_4' ).
        LO_COLUMN->SET_LONG_TEXT( 'Office4 MCA' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_COLUMNS->GET_COLUMN( 'FM_OUTPUT' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM009 ----
  METHOD SET_DISPLAY_SETTINGS.

    MO_DISPLAY_SETTINGS = MO_SALV_TABLE->GET_DISPLAY_SETTINGS( ).
    "mo_display_settings->set_list_header( text-tit ).
    MO_DISPLAY_SETTINGS->SET_STRIPED_PATTERN( ABAP_TRUE ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00A ----
  METHOD SET_FUNCTIONS.

    DATA LO_EVENTS TYPE REF TO CL_SALV_EVENTS_TABLE.

    MO_FUNCTIONS = MO_SALV_TABLE->GET_FUNCTIONS( ).
    MO_FUNCTIONS->SET_ALL( ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00B ----
  METHOD SET_LAYOUT.

    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.

    MO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = MV_REPID.
    MO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    MO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00D ----
  METHOD SET_SELECTION_VALUES.

    FIELD-SYMBOLS <LT_RANGE> TYPE ANY TABLE.
    FIELD-SYMBOLS <LV_PARAM> TYPE ANY.
    DATA LV_SELNAME TYPE FIELDNAME.

    LV_SELNAME = IV_SELNAME.
    CASE IV_KIND.
      WHEN 'S'.   "SELECT-OPTIONS
        REPLACE 'S_' IN LV_SELNAME WITH 'MR_'.
        ASSIGN (LV_SELNAME) TO <LT_RANGE>.
        CHECK <LT_RANGE> IS ASSIGNED.
        <LT_RANGE> = IT_VALUE.
      WHEN 'P'. "PARAMETERS
        REPLACE 'P_' IN LV_SELNAME WITH 'MP_'.
        ASSIGN (LV_SELNAME) TO <LV_PARAM>.
        CHECK <LV_PARAM> IS ASSIGNED.
        <LV_PARAM> = IV_VALUE.
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00E ----
  METHOD UPDATE_DATA_HUB.

    DATA LS_INDCO TYPE YTDH_INDCO.
    DATA LS_RETURN TYPE BAPIRETURN1.

    "First delete entries related to selection
    IF IV_DELETE_OLD = ABAP_FALSE.
      DELETE FROM YTDH_INDCO WHERE FIKRS = MP_FIKRS
                             AND   FTYPG = IV_FTYPG
                             AND   ZZSECT IN MR_SECTOR
                             AND   BEGDA = MV_BEGDA
                             AND   ENDDA = MV_ENDDA
                             AND   BLDAT = MV_BLDAT.
    ELSE.
      DELETE FROM YTDH_INDCO WHERE FIKRS = MP_FIKRS
                             AND   FTYPG = IV_FTYPG.
    ENDIF.

    "Then insert records in YTDH_INDCO
    SORT MT_LIST.
    LOOP AT MT_LIST INTO DATA(LS_LIST).
      CLEAR LS_INDCO.
      MOVE-CORRESPONDING LS_LIST TO LS_INDCO.
      LS_INDCO-FIKRS = MP_FIKRS.
      LS_INDCO-FTYPG = IV_FTYPG.
      LS_INDCO-BEGDA = MV_BEGDA.
      LS_INDCO-ENDDA = MV_ENDDA.
      LS_INDCO-BLDAT = MV_BLDAT.
      LS_INDCO-UDATE = SY-DATUM.
      LS_INDCO-UNAME = SY-UNAME.
      INSERT YTDH_INDCO FROM LS_INDCO.
      IF SY-SUBRC <> 0.
        LS_RETURN-TYPE = 'E'.
        LS_RETURN-ID = 'YFM1'.
        LS_RETURN-NUMBER = '005'.
        LS_RETURN-MESSAGE_V1 = 'YTDH_INDCO'.
        LS_RETURN-MESSAGE_V2 = LS_INDCO-FM_OUTPUT.
        MESSAGE ID LS_RETURN-ID TYPE LS_RETURN-TYPE NUMBER LS_RETURN-NUMBER
              WITH LS_RETURN-MESSAGE_V1 LS_RETURN-MESSAGE_V2 LS_RETURN-MESSAGE_V3 LS_RETURN-MESSAGE_V4
              INTO LS_RETURN-MESSAGE.
        APPEND LS_RETURN TO ET_RETURN.
      ENDIF.
    ENDLOOP.

    IF IV_MODE_TEST = ABAP_TRUE.
      ROLLBACK WORK.
    ELSE.
      COMMIT WORK.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00F ----
  METHOD SET_HEADER.

    DATA LO_HEADER TYPE REF TO CL_SALV_FORM_LAYOUT_GRID.
    DATA LV_STRING TYPE STRING.
    DATA LV_BEGDA_C(10) TYPE C.
    DATA LV_ENDDA_C(10) TYPE C.

    LO_HEADER = NEW CL_SALV_FORM_LAYOUT_GRID( COLUMNS = 1 ).

    LV_STRING = |FM area: { MP_FIKRS }|.
    LO_HEADER->CREATE_LABEL( ROW = 1
                             COLUMN = 1
                             TEXT = LV_STRING ).

    WRITE MV_BEGDA TO LV_BEGDA_C.
    WRITE MV_ENDDA TO LV_ENDDA_C.
    LV_STRING = |Period from { LV_BEGDA_C } to { LV_ENDDA_C }|.
    LO_HEADER->CREATE_TEXT( ROW = 2
                            COLUMN = 1
                            TEXT = LV_STRING ).

    WRITE MV_BLDAT TO LV_BEGDA_C.
    LV_STRING = |Until document date: { LV_BEGDA_C }|.
    LO_HEADER->CREATE_TEXT( ROW = 3
                            COLUMN = 1
                            TEXT = LV_STRING ).

    "Blank line
    CLEAR LV_STRING.
    LO_HEADER->CREATE_TEXT( ROW = 4
                            COLUMN = 1
                            TEXT = LV_STRING ).

    MO_SALV_TABLE->SET_TOP_OF_LIST( LO_HEADER ).

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CM00G ----
  METHOD CONVERT_AMOUNT.

    DATA LV_RATE TYPE UKURS_CURR.
    DATA LV_SUBRC TYPE SY-SUBRC.
    DATA LV_AMOUNT_IN TYPE WERTV9.
    DATA LV_AMOUNT_OUT TYPE WERTV9.
    DATA LV_FOREIGN_FACTOR TYPE YE_CA_DECIMAL_FACTOR.
    DATA LV_DECIMAL_FACTOR TYPE YE_CA_DECIMAL_FACTOR.

    "If transaction currency = target currency, no conversion.
    IF IV_CURRENCY = C_USD.
      EV_AMOUNT = IV_AMOUNT.
      EXIT.
    ENDIF.

    IF IV_KURSF <> 0.
      LV_FOREIGN_FACTOR = MO_CURRENCY_OP->GET_FOREIGN_FACTOR( IV_SOURCE_CURRENCY = IV_CURRENCY
                                                              IV_TARGET_CURRENCY = C_USD
                                                              IV_DATE = IV_DATE ).
      LV_DECIMAL_FACTOR = MO_CURRENCY_OP->GET_DECIMAL_FACTOR( IV_CURRENCY ).
      IF IV_KURSF < 0.
        EV_AMOUNT = IV_AMOUNT / ABS( IV_KURSF ) * LV_FOREIGN_FACTOR * LV_DECIMAL_FACTOR.
      ELSEIF IV_KURSF > 0.
        EV_AMOUNT = IV_AMOUNT * IV_KURSF * LV_FOREIGN_FACTOR * LV_DECIMAL_FACTOR.
      ENDIF.
      EXIT.
    ENDIF.

    READ TABLE MO_CONV_RATE->MT_CONV INTO DATA(LS_CONV) WITH KEY FIKRS = MP_FIKRS.
    IF IV_CURRENCY = LS_CONV-WAERS.   "FM area currency: use buffered rate
      IF IV_DATE BETWEEN MV_BEGDA AND MV_ENDDA.
        LV_RATE = MO_CONV_RATE->GET_RATE_AT_DATE( IV_WAERS = LS_CONV-WAERS IV_DATE = IV_DATE ).
      ELSE.
        LV_RATE = MO_CONV_RATE->GET_EXCHANGE_RATE( IV_WAERS = LS_CONV-WAERS IV_DATE = IV_DATE ).
      ENDIF.
      IF LV_RATE <> 0.
        EV_AMOUNT = IV_AMOUNT / LV_RATE.
      ELSE.
        EV_AMOUNT = IV_AMOUNT.
      ENDIF.
    ELSE.    "Other than FM area currency
      LV_AMOUNT_IN = IV_AMOUNT.
      MO_CONV_RATE->CONVERT_AMOUNT( EXPORTING IV_DATE = IV_DATE
                                              IV_LOCAL_AMOUNT = LV_AMOUNT_IN
                                              IV_LOCAL_CURRENCY = IV_CURRENCY
                                              IV_TARGET_CURRENCY = C_USD
                                    IMPORTING EV_TARGET_AMOUNT = LV_AMOUNT_OUT
                                              EV_SUBRC = LV_SUBRC ).
      IF LV_SUBRC = 0.
        EV_AMOUNT = LV_AMOUNT_OUT.
      ELSE.
        EV_AMOUNT = IV_AMOUNT.
      ENDIF.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_INDIRECT_COSTS_BL======CO ----
PROTECTED SECTION.

* ---- YCL_FM_INDIRECT_COSTS_BL======CU ----
CLASS YCL_FM_INDIRECT_COSTS_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  METHODS GET_DATA
    IMPORTING
      !IV_BLDAT TYPE BLDAT
      !IV_USD_CURRENCY TYPE XFELD DEFAULT ABAP_FALSE .
  METHODS UPDATE_DATA_HUB
    IMPORTING
      !IV_FTYPG TYPE YE_FM_FUND_TYPE_GROUP
      !IV_MODE_TEST TYPE BOOLEAN DEFAULT ABAP_TRUE
      !IV_DELETE_OLD TYPE BOOLEAN DEFAULT ABAP_FALSE
    EXPORTING
      VALUE(ET_RETURN) TYPE BAPIRETURN1_TABTYPE .
  METHODS SET_SELECTION_VALUES
    IMPORTING
      !IV_SELNAME TYPE RSSCR_NAME
      !IV_KIND TYPE RSSCR_KIND
      !IV_VALUE TYPE ANY OPTIONAL
      !IT_VALUE TYPE ANY TABLE OPTIONAL .
  METHODS DISPLAY_ALV
    IMPORTING
      !IV_REPID TYPE SY-REPID DEFAULT SY-REPID .