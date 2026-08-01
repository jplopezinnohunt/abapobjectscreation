* ==== CLASS POOL YCL_FM_CONSTANT_DOLLAR_BL_V2 ====
CLASS-POOL .
*"* class pool for class YCL_FM_CONSTANT_DOLLAR_BL_V2

*"* local type definitions
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CCDEF.

*"* class YCL_FM_CONSTANT_DOLLAR_BL_V2 definition
*"* public declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CU.
*"* protected declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CO.
*"* private declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CI.
ENDCLASS. "YCL_FM_CONSTANT_DOLLAR_BL_V2 definition

*"* macro definitions
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CCMAC.
*"* local class implementation
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL_V2==CCIMP.

CLASS YCL_FM_CONSTANT_DOLLAR_BL_V2 IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_CONSTANT_DOLLAR_BL_V2 implementation


* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_FUND,
      FIKRS   TYPE FMFINCODE-FIKRS,
      FINCODE TYPE FMFINCODE-FINCODE,
      TYPE    TYPE FMFINCODE-TYPE,
      DATAB   TYPE FMFINCODE-DATAB,
      DATBIS  TYPE FMFINCODE-DATBIS,
      BESCHR  TYPE FMFINT-BESCHR,
      BEZEICH TYPE FMFINT-BEZEICH,
    END OF TY_FUND .
  TYPES:
    BEGIN OF TY_FUND_C5,
      FIKRS     TYPE FIKRS,
      FINCODE   TYPE BP_GEBER,
      C5_ID     TYPE YE_FM_C5_ID,
      C5_SEL    TYPE YE_FM_C5_CONTRIBUTION,
      FM_OUTPUT TYPE YE_FM_OUTPUT,
      ONAME     TYPE YE_FM_OUTPUT_NAME,
      OTYPE     TYPE YE_FM_OUTPUT_TYPE,
    END OF TY_FUND_C5 .
  TYPES:
    BEGIN OF TY_FMBDT,
      FIKRS     TYPE FMBDT-RFIKRS,    "FM area
      FINCODE   TYPE FMBDT-RFUND,     "Fund
      FISTL     TYPE FMBDT-RFUNDSCTR, "Fund center
      GJAHR     TYPE FMBDT-RYEAR,     "Fiscal year
      "waers     TYPE waers,           "Currency
      FIPEX     TYPE FMBDT-RCMMTITEM, "Commitment item
      BUDTYPE_9 TYPE FMBDT-BUDTYPE_9, "Budget type
      HSLVT     TYPE FMBDT-HSLVT,     "Carry forward
      HSL01     TYPE FMBDT-HSL01,
      HSL02     TYPE FMBDT-HSL02,
      HSL03     TYPE FMBDT-HSL03,
      HSL04     TYPE FMBDT-HSL04,
      HSL05     TYPE FMBDT-HSL05,
      HSL06     TYPE FMBDT-HSL06,
      HSL07     TYPE FMBDT-HSL07,
      HSL08     TYPE FMBDT-HSL08,
      HSL09     TYPE FMBDT-HSL09,
      HSL10     TYPE FMBDT-HSL10,
      HSL11     TYPE FMBDT-HSL11,
      HSL12     TYPE FMBDT-HSL12,
      HSL13     TYPE FMBDT-HSL13,
      HSL14     TYPE FMBDT-HSL14,
      HSL15     TYPE FMBDT-HSL15,
      HSL16     TYPE FMBDT-HSL16,
      RLDNR     TYPE FMBDT-RLDNR,   "To avoid distinct with FOR ALL ENTRIES
      RRCTY     TYPE FMBDT-RRCTY,   "To avoid distinct with FOR ALL ENTRIES
      RVERS     TYPE FMBDT-RVERS,   "To avoid distinct with FOR ALL ENTRIES
      ROBJNR    TYPE FMBDT-ROBJNR,  "To avoid distinct with FOR ALL ENTRIES
      COBJNR    TYPE FMBDT-COBJNR,  "To avoid distinct with FOR ALL ENTRIES
      SOBJNR    TYPE FMBDT-SOBJNR,  "To avoid distinct with FOR ALL ENTRIES
      RTCUR     TYPE FMBDT-RTCUR,   "To avoid distinct with FOR ALL ENTRIES
      DRCRK     TYPE FMBDT-DRCRK,   "To avoid distinct with FOR ALL ENTRIES
      RPMAX     TYPE FMBDT-RPMAX,   "To avoid distinct with FOR ALL ENTRIES
    END OF TY_FMBDT .
  TYPES:
    BEGIN OF TY_FMIFI,
      FIKRS    TYPE FMIFIIT-FIKRS,
      FINCODE  TYPE FMIFIIT-FONDS,
      FISTL    TYPE FMIFIIT-FISTL,
      GJAHR    TYPE FMIFIIT-GJAHR,
      WRTTP    TYPE FMIFIIT-WRTTP,
      FIPEX    TYPE FMIFIIT-FIPEX,
      TRBTR    TYPE FMIFIIT-TRBTR,
      TWAER    TYPE FMIFIIT-TWAER,
      FKBTR    TYPE FMIFIIT-FKBTR,
      VRGNG    TYPE FMIFIIT-VRGNG,
      BUDAT    TYPE FMIFIHD-BUDAT,
      BLART    TYPE FMIFIHD-BLART,
      BUS_AREA TYPE FMIFIIT-BUS_AREA,
      BUKRS    TYPE FMIFIIT-BUKRS,
      KNGJAHR  TYPE FMIFIIT-KNGJAHR,
      KNBELNR  TYPE FMIFIIT-KNBELNR,
      KNBUZEI  TYPE FMIFIIT-KNBUZEI,
      AWTYP    TYPE FMIFIHD-AWTYP,
      AWREF    TYPE FMIFIHD-AWREF,
      AWORG    TYPE FMIFIHD-AWORG,
      FMBELNR  TYPE FMIFIIT-FMBELNR,  "To avoid distinct with FOR ALL ENTRIES
      FMBUZEI  TYPE FMIFIIT-FMBUZEI,  "To avoid distinct with FOR ALL ENTRIES
      BTART    TYPE FMIFIIT-BTART,    "To avoid distinct with FOR ALL ENTRIES
      RLDNR    TYPE FMIFIIT-RLDNR,    "To avoid distinct with FOR ALL ENTRIES
      STUNR    TYPE FMIFIIT-STUNR,    "To avoid distinct with FOR ALL ENTRIES
    END OF TY_FMIFI .
  TYPES:
    BEGIN OF TY_BSEG,
      BUKRS TYPE BSEG-BUKRS,
      BELNR TYPE BSEG-BELNR,
      GJAHR TYPE BSEG-GJAHR,
      BUZEI TYPE BSEG-BUZEI,
      SHKZG TYPE BSEG-SHKZG,
      DMBTR TYPE BSEG-DMBTR,
      BUDAT TYPE BKPF-BUDAT,
      WWERT TYPE BKPF-WWERT,
    END OF TY_BSEG .
  TYPES:
    BEGIN OF TY_FMIOI,
      FIKRS   TYPE FMIOI-FIKRS,
      FINCODE TYPE FMIOI-FONDS,
      FISTL   TYPE FMIOI-FISTL,
      GJAHR   TYPE FMIOI-GJAHR,
      WRTTP   TYPE FMIOI-WRTTP,
      FIPEX   TYPE FMIOI-FIPEX,
      TRBTR   TYPE FMIOI-TRBTR,
      TWAER   TYPE FMIOI-TWAER,
      FKBTR   TYPE FMIOI-FKBTR,
      VRGNG   TYPE FMIOI-VRGNG,
      REFBN   TYPE FMIOI-REFBN, "To avoid distinct with FOR ALL ENTRIES
      REFBT   TYPE FMIOI-REFBT, "To avoid distinct with FOR ALL ENTRIES
      RFORG   TYPE FMIOI-RFORG, "To avoid distinct with FOR ALL ENTRIES
      RFPOS   TYPE FMIOI-RFPOS, "To avoid distinct with FOR ALL ENTRIES
      RFKNT   TYPE FMIOI-RFKNT, "To avoid distinct with FOR ALL ENTRIES
      RFETE   TYPE FMIOI-RFETE, "To avoid distinct with FOR ALL ENTRIES
      RCOND   TYPE FMIOI-RCOND, "To avoid distinct with FOR ALL ENTRIES
      RFTYP   TYPE FMIOI-RFTYP, "To avoid distinct with FOR ALL ENTRIES
      RFSYS   TYPE FMIOI-RFSYS, "To avoid distinct with FOR ALL ENTRIES
      BTART   TYPE FMIOI-BTART, "To avoid distinct with FOR ALL ENTRIES
      RLDNR   TYPE FMIOI-RLDNR, "To avoid distinct with FOR ALL ENTRIES
      STUNR   TYPE FMIOI-STUNR, "To avoid distinct with FOR ALL ENTRIES
    END OF TY_FMIOI .
  TYPES:
    BEGIN OF TY_LIST,
      FIKRS                  TYPE FMIT-FIKRS,   "FM area
      FINCODE                TYPE FMIT-RFONDS,  "Fund
      TYPE                   TYPE FMFINCODE-TYPE,
      DATAB                  TYPE FMFINCODE-DATAB,
      DATBIS                 TYPE FMFINCODE-DATBIS,
      BESCHR                 TYPE FMFINT-BESCHR,
      BEZEICH                TYPE FMFINT-BEZEICH,
      C5_ID                  TYPE YTFM_FUND_C5-C5_ID,
      FM_OUTPUT              TYPE YTFM_FUND_C5-FM_OUTPUT,
      ONAME                  TYPE YE_FM_OUTPUT_NAME,
      OTYPE                  TYPE YE_FM_OUTPUT_TYPE,
      C5_SEL                 TYPE YTFM_FUND_C5-C5_SEL,
      BUDGET_UNORE           TYPE WERTV9,   "Budget in FM area currency (UNORE) =>keep as it is in V2
      NPC_EXPENSES_UNORE     TYPE WERTV9,   "NPC expenses in USD (UNORE) => new in V2
      NPC_EXPENSES_BR_IMPACT TYPE WERTV9,   "NPC expenses BR impact => new in V2
      NPC_EXPENSES_TOTAL     TYPE WERTV9,   "NPC total expenses at BR => new in V2
      PC_EXPENSES_UNORE      TYPE WERTV9,   "PC expenses in USD (UNORE) => new in V2
      PC_EXPENSES_BR_IMPACT  TYPE WERTV9,   "PC expenses BR impact => new in V2
      PC_EXPENSES_TOTAL      TYPE WERTV9,   "PC total expenses at BR => new in V2
      PC_COMMIT_UNORE        TYPE WERTV9,   "PC commitments in USD (UNORE) => new in V2
      NPC_COMMIT_UNORE       TYPE WERTV9,   "NPC commitments in USD (UNORE) => new in V2
      PC_COMMIT_BR_IMPACT    TYPE WERTV9,   "PC commitments BR impact => new in V2
      NPC_COMMIT_BR_IMPACT   TYPE WERTV9,   "NPC commitments BR impact => new in V2
      COMMIT_TOTAL           TYPE WERTV9,   "Total commitments at BR impact => new in V2
      AVAILABLE              TYPE WERTV9,   "budget_unore - expenses - commitments =>keep as it is in V2
      EXPENSES_BR_IMPACT     TYPE WERTV9,   "Impact BR expenses => new in V2
      COMMIT_BR_IMPACT       TYPE WERTV9,   "Impact Br commitmenets => new in V2
      TOTAL_BR_IMPACT        TYPE WERTV9,   "Total BR impact => new in V2
      COLFIELD               TYPE LVC_T_SCOL,  "Field color
    END OF TY_LIST .
  TYPES:
    BEGIN OF TY_LIST_DET,
      FIKRS                  TYPE FMIT-FIKRS,   "FM area
      FINCODE                TYPE FMIT-RFONDS,  "Fund
      TYPE                   TYPE FMFINCODE-TYPE,
      DATAB                  TYPE FMFINCODE-DATAB,
      DATBIS                 TYPE FMFINCODE-DATBIS,
      BESCHR                 TYPE FMFINT-BESCHR,
      BEZEICH                TYPE FMFINT-BEZEICH,
      C5_ID                  TYPE YTFM_FUND_C5-C5_ID,
      FM_OUTPUT              TYPE YTFM_FUND_C5-FM_OUTPUT,
      ONAME                  TYPE YE_FM_OUTPUT_NAME,
      OTYPE                  TYPE YE_FM_OUTPUT_TYPE,
      FM_AMOUNT_TYPE         TYPE GENFM_SPVAL,
      FM_AMOUNT_TYPE_TEXT    TYPE TEXT20,
      FM_DOC                 TYPE FM_BELNR, "FM document: FMBELNR from FMIFIIT or REFBN from FMIOI
      FM_POS                 TYPE CC_RFPOS, "FM document position: FMBUZEI for FMIFIIT or RFPOS for FMIOI
      GJAHR                  TYPE GJAHR,
      FIPEX                  TYPE FM_FIPEX,
      VRGNG                  TYPE J_VORGANG,
      VRGNG_TXT              TYPE TEXT30,
      AWTYP                  TYPE AWTYP,
      AWTYP_TXT              TYPE TEXT_TYP,
      AWREF                  TYPE AWREF,
      AWORG                  TYPE AWORG,
      NPC_EXPENSES_UNORE     TYPE WERTV9,   "NPC expenses in USD (UNORE) => new in V2
      NPC_EXPENSES_BR_IMPACT TYPE WERTV9,   "NPC expenses BR impact => new in V2
      PC_EXPENSES_UNORE      TYPE WERTV9,   "PC expenses in USD (UNORE) => new in V2
      PC_EXPENSES_BR_IMPACT  TYPE WERTV9,   "PC expenses BR impact => new in V2
      PC_COMMIT_UNORE        TYPE WERTV9,   "PC commitments in USD (UNORE) => new in V2
      NPC_COMMIT_UNORE       TYPE WERTV9,   "NPC commitments in USD (UNORE) => new in V2
      PC_COMMIT_BR_IMPACT    TYPE WERTV9,   "PC commitments BR impact => new in V2
      NPC_COMMIT_BR_IMPACT   TYPE WERTV9,   "NPC commitments BR impact => new in V2
      COLFIELD               TYPE LVC_T_SCOL,  "Field color
    END OF TY_LIST_DET .
  TYPES:
    TTY_LIST_DET TYPE TABLE OF TY_LIST_DET .
  TYPES:
    BEGIN OF TY_TJ01T,
      VRGNG TYPE TJ01T-VRGNG,
      TXT   TYPE TJ01T-TXT,
    END OF TY_TJ01T .
  TYPES:
    BEGIN OF TY_TTYPT,
      AWTYP TYPE TTYPT-AWTYP,
      OTEXT TYPE TTYPT-OTEXT,
    END OF TY_TTYPT .
  TYPES:
    BEGIN OF TY_MESSAGE,
      STATUS  TYPE P_99S_STATU,
      MESSAGE TYPE ETMESSAGE,
    END OF TY_MESSAGE .

  DATA MV_ROW_D TYPE INT4 .
  DATA MV_ROW_H TYPE INT4 .
  DATA MP_CDATE TYPE DATUM .
  DATA MV_SEQUENCE TYPE YE_BC_SEQUENCE_6 .
  DATA MV_LIST_TYPE TYPE CHAR1 .
  DATA MO_BR_EXCHANGE_RATE_BL TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL .
  CONSTANTS C_CUTOFF_YEAR TYPE GJAHR VALUE '2025' ##NO_TEXT.
  DATA MP_EUREXP TYPE XFELD .
  DATA MV_REPID TYPE SY-REPID .
  CONSTANTS C_EUR TYPE WAERS VALUE 'EUR' ##NO_TEXT.
  CONSTANTS C_USD TYPE WAERS VALUE 'USD' ##NO_TEXT.
  DATA MP_FILTER TYPE XFELD .
  DATA MP_PCT TYPE NUM2 .
  DATA MV_CONST_RATE TYPE TVRT_KKURS .
  DATA MV_FM_WAERS TYPE FM_WAERS .
  DATA:
    MT_FUND TYPE SORTED TABLE OF TY_FUND WITH UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FUND_C5 TYPE SORTED TABLE OF TY_FUND_C5 WITH UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMBDT TYPE SORTED TABLE OF TY_FMBDT WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMIFI TYPE SORTED TABLE OF TY_FMIFI WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_BSEG TYPE SORTED TABLE OF TY_BSEG WITH UNIQUE KEY BUKRS BELNR GJAHR BUZEI .
  DATA:
    MT_FMIOI TYPE SORTED TABLE OF TY_FMIOI WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_LIST TYPE TABLE OF TY_LIST .
  DATA MT_LIST_DET TYPE TTY_LIST_DET .
  DATA MV_BEGDA TYPE BEGDA .
  DATA MV_ENDDA TYPE ENDDA .
  DATA MP_FIKRS TYPE FIKRS .
  DATA:
    MR_TYPE TYPE RANGE OF FM_FUNDTYPE .
  DATA:
    MR_FUND TYPE RANGE OF BP_GEBER .
  DATA:
    MR_FICTR TYPE RANGE OF FISTL .
  DATA MP_BEGFY TYPE GJAHR .
  DATA MP_ENDFY TYPE GJAHR .
  DATA MO_SALV_TABLE TYPE REF TO CL_SALV_TABLE .
  DATA:
    MT_FIPEX_PC TYPE RANGE OF FM_FIPEX .
  DATA:
    MT_FIPEX_PC_IMPACT TYPE RANGE OF FM_FIPEX .
  DATA:
    MT_FIPEX_NPC TYPE RANGE OF FM_FIPEX .
  DATA:
    MT_VRGNG TYPE RANGE OF CO_VORGANG .
  DATA:
    MR_C5_ID TYPE RANGE OF YE_FM_C5_ID .
  DATA:
    MT_TJ01T TYPE SORTED TABLE OF TY_TJ01T WITH UNIQUE KEY VRGNG .
  DATA:
    MT_TTYPT TYPE SORTED TABLE OF TY_TTYPT WITH UNIQUE KEY AWTYP .
  DATA:
    MT_MESSAGE TYPE TABLE OF TY_MESSAGE .
  DATA:
    MT_HIST_HEAD TYPE TABLE OF YTFM_BR_REP_H .
  DATA:
    MT_HIST_DETAIL TYPE TABLE OF YTFM_BR_REP_D .

  METHODS GET_BUSINESS_TRANSACTION_TEXT
    IMPORTING
      !IV_VRGNG      TYPE J_VORGANG
    RETURNING
      VALUE(RV_TEXT) TYPE TEXT30 .
  METHODS SET_TOTALS
    CHANGING
      !CS_LIST TYPE TY_LIST .
  METHODS GET_AMOUNT_TYPE_TEXT
    IMPORTING
      !IV_AMOUNT_TYPE TYPE GENFM_SPVAL
    RETURNING
      VALUE(RV_TEXT)  TYPE TEXT20 .
  METHODS GET_OBJECT_TYPE_TEXT
    IMPORTING
      !IV_AWTYP      TYPE AWTYP
    RETURNING
      VALUE(RV_TEXT) TYPE TEXT_TYP .
  METHODS SET_DATA_TO_ALV_LIST_TABLES
    IMPORTING
      VALUE(IS_LIST)     TYPE TY_LIST
      VALUE(IT_DETAIL_1) TYPE TTY_LIST_DET
      VALUE(IT_DETAIL_2) TYPE TTY_LIST_DET OPTIONAL .
  METHODS GET_HISTORY_FROM_DB .
  METHODS INSERT_INTO_DETAIL_TABLE
    IMPORTING
      !IT_DETAIL TYPE TTY_LIST_DET .
  METHODS SET_COLOR
    IMPORTING
      !IV_FNAME       TYPE LVC_FNAME
      !IV_COL         TYPE ANY
      !IV_INT         TYPE LVC_INT
    RETURNING
      VALUE(RS_COLOR) TYPE LVC_S_SCOL .
  METHODS DETERMINE_COMMITMENT_AMOUNTS
    IMPORTING
      !IS_FUND              TYPE TY_FUND
      !IV_C5_ID             TYPE YE_FM_C5_ID
    EXPORTING
      !EV_PC_COM_UNORE      TYPE WERTV9
      !EV_NPC_COM_UNORE     TYPE WERTV9
      !EV_PC_COM_BR_IMPACT  TYPE WERTV9
      !EV_NPC_COM_BR_IMPACT TYPE WERTV9
      !ET_DETAIL            TYPE TTY_LIST_DET .
  METHODS GET_BR_IMPACT
    IMPORTING
      !IS_FMIFI     TYPE TY_FMIFI
    EXPORTING
      !EV_BR_IMPACT TYPE WERTV9 .
  METHODS DETERMINE_BUDGET_AMOUNT
    IMPORTING
      !IV_FIKRS   TYPE FIKRS
      !IV_FINCODE TYPE BP_GEBER
    EXPORTING
      !EV_AMOUNT  TYPE WERTV9 .
  METHODS DETERMINE_EXPENSES_AMOUNTS
    IMPORTING
      !IS_FUND              TYPE TY_FUND
      !IV_C5_ID             TYPE YE_FM_C5_ID
    EXPORTING
      !EV_NPC_EXP_UNORE     TYPE WERTV9
      !EV_NPC_EXP_BR_IMPACT TYPE WERTV9
      !EV_PC_EXP_UNORE      TYPE WERTV9
      !EV_PC_EXP_BR_IMPACT  TYPE WERTV9
      !ET_DETAIL            TYPE TTY_LIST_DET .
  CLASS-METHODS GET_CONSTANT_RATE
    IMPORTING
      !IV_DATE       TYPE DATUM
    RETURNING
      VALUE(RV_RATE) TYPE TVRT_KKURS .
  CLASS-METHODS GET_FM_AREA_CURRENCY
    IMPORTING
      !IV_FIKRS       TYPE FIKRS
    RETURNING
      VALUE(RV_WAERS) TYPE WAERS .
  METHODS PREPARE_DATA
    IMPORTING
      !IS_FUND       TYPE TY_FUND
    EXPORTING
      !ES_LIST       TYPE TY_LIST
      !ET_DETAIL_EXP TYPE TTY_LIST_DET
      !ET_DETAIL_COM TYPE TTY_LIST_DET .
  METHODS SET_COLUMNS .
  METHODS GET_EXPENSES_FROM_DB .
  METHODS GET_BUDGET_FROM_DB .
  METHODS INITIALIZE .
  METHODS GET_FUND_FROM_DB .
  METHODS SET_DISPLAY_SETTINGS .
  METHODS SET_FUNCTIONS .
  METHODS SET_LAYOUT .

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM001 ----
  METHOD DETERMINE_BUDGET_AMOUNT.

    DATA LV_FIELDNAME TYPE FIELDNAME.
    DATA LV_NUM(2) TYPE N.
    FIELD-SYMBOLS <FIELD> TYPE ANY.

    CLEAR EV_AMOUNT.

    LOOP AT MT_FMBDT INTO DATA(LS_FMBDT) WHERE FIKRS = IV_FIKRS
                                         AND   FINCODE = IV_FINCODE.
      EV_AMOUNT = EV_AMOUNT - LS_FMBDT-HSLVT.   "subtract to inverse sign
      CLEAR LV_NUM.
      DO 16 TIMES.
        ADD 1 TO LV_NUM.
        LV_FIELDNAME = |LS_FMBDT-HSL{ LV_NUM }|.
        ASSIGN (LV_FIELDNAME) TO <FIELD>.
        CHECK <FIELD> IS ASSIGNED.
        EV_AMOUNT = EV_AMOUNT - <FIELD>.
      ENDDO.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM002 ----
  METHOD DETERMINE_EXPENSES_AMOUNTS.

    DATA LV_NPC_BR_IMPACT TYPE WERTV9.
    DATA LS_DETAIL TYPE TY_LIST_DET.

    CLEAR: EV_NPC_EXP_UNORE, EV_NPC_EXP_BR_IMPACT, EV_PC_EXP_UNORE, EV_PC_EXP_BR_IMPACT, ET_DETAIL.

    LOOP AT MT_FMIFI INTO DATA(LS_FMIFI) WHERE FIKRS = IS_FUND-FIKRS
                                         AND   FINCODE = IS_FUND-FINCODE.

      CHECK LS_FMIFI-TRBTR <> 0 OR LS_FMIFI-FKBTR <> 0.

      CLEAR LS_DETAIL.
      MOVE-CORRESPONDING IS_FUND TO LS_DETAIL.
      LS_DETAIL-C5_ID = IV_C5_ID.
      LS_DETAIL-GJAHR = LS_FMIFI-GJAHR.
      LS_DETAIL-FIPEX = LS_FMIFI-FIPEX.

      "inverse sign
      LS_FMIFI-TRBTR = LS_FMIFI-TRBTR * -1.
      LS_FMIFI-FKBTR = LS_FMIFI-FKBTR * -1.

      "Fill NPC expenses in UNORE
      IF LS_FMIFI-FIPEX IN MT_FIPEX_NPC.
        ADD LS_FMIFI-FKBTR TO EV_NPC_EXP_UNORE.
        LS_DETAIL-NPC_EXPENSES_UNORE = LS_FMIFI-FKBTR.
      ENDIF.

      "Fill PC expenses in UNORE
      IF LS_FMIFI-FIPEX IN MT_FIPEX_PC.
        ADD LS_FMIFI-FKBTR TO EV_PC_EXP_UNORE.
        LS_DETAIL-PC_EXPENSES_UNORE = LS_FMIFI-FKBTR.
      ENDIF.

      "Fill PC BR impact
      IF LS_FMIFI-FIPEX IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIFI-FKBTR TO EV_PC_EXP_BR_IMPACT.
        LS_DETAIL-PC_EXPENSES_BR_IMPACT = LS_FMIFI-FKBTR.
      ENDIF.

      "Fill NPC BR impact
      IF LS_FMIFI-TWAER = C_EUR.
        IF LS_FMIFI-FIPEX IN MT_FIPEX_NPC.
          IF LS_FMIFI-GJAHR < C_CUTOFF_YEAR.
            LV_NPC_BR_IMPACT = ( LS_FMIFI-TRBTR / MV_CONST_RATE ) - LS_FMIFI-FKBTR.
          ELSE.
            ME->GET_BR_IMPACT( EXPORTING IS_FMIFI = LS_FMIFI
                               IMPORTING EV_BR_IMPACT = LV_NPC_BR_IMPACT ).
          ENDIF.
          ADD LV_NPC_BR_IMPACT TO EV_NPC_EXP_BR_IMPACT.
          LS_DETAIL-NPC_EXPENSES_BR_IMPACT = LV_NPC_BR_IMPACT.
        ENDIF.
      ENDIF.

      IF MV_LIST_TYPE = 'D'.
        LS_DETAIL-FM_AMOUNT_TYPE = '1'.
        LS_DETAIL-FM_AMOUNT_TYPE_TEXT = ME->GET_AMOUNT_TYPE_TEXT( LS_DETAIL-FM_AMOUNT_TYPE ).
        "Get business transaction text.
        LS_DETAIL-VRGNG = LS_FMIFI-VRGNG.
        LS_DETAIL-VRGNG_TXT = ME->GET_BUSINESS_TRANSACTION_TEXT( IV_VRGNG = LS_DETAIL-VRGNG ).
        "Get object type text
        LS_DETAIL-AWTYP = LS_FMIFI-AWTYP.
        LS_DETAIL-AWTYP_TXT = ME->GET_OBJECT_TYPE_TEXT( IV_AWTYP = LS_DETAIL-AWTYP ).
        READ TABLE MT_TTYPT INTO DATA(LS_TTYPT) WITH KEY AWTYP = LS_FMIFI-AWTYP.
        LS_DETAIL-AWREF = LS_FMIFI-AWREF.
        LS_DETAIL-AWORG = LS_FMIFI-AWORG.
        LS_DETAIL-FM_DOC = LS_FMIFI-FMBELNR.
        LS_DETAIL-FM_POS = LS_FMIFI-FMBUZEI.
        APPEND LS_DETAIL TO ET_DETAIL.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM003 ----
  METHOD DISPLAY_ALV.

    MV_REPID = IV_REPID.

    TRY.
        CASE MV_LIST_TYPE.
          WHEN 'M'.
            CL_SALV_TABLE=>FACTORY( IMPORTING R_SALV_TABLE = MO_SALV_TABLE
                                    CHANGING  T_TABLE      = MT_LIST ).
          WHEN 'D'.
            CL_SALV_TABLE=>FACTORY( IMPORTING R_SALV_TABLE = MO_SALV_TABLE
                                    CHANGING  T_TABLE      = MT_LIST_DET ).
        ENDCASE.
      CATCH CX_SALV_MSG .
    ENDTRY.

    "ALV functions activation
    ME->SET_FUNCTIONS( ).

    "ALV columns
    ME->SET_COLUMNS( ).

    "ALV layout
    ME->SET_LAYOUT( ).

    "ALV display settings
    ME->SET_DISPLAY_SETTINGS( ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).


  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM004 ----
  METHOD GET_BUDGET_FROM_DB.

    DATA LR_FIPEX TYPE RANGE OF FM_FIPEX.
    DATA LR_BUDTYPE TYPE RANGE OF BUKU_BUDTYPE.

    LR_FIPEX = VALUE #( ( SIGN = 'E' OPTION = 'EQ' LOW = 'GAINS' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'REVENUE' ) ).
    LR_BUDTYPE = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = '3000' )
                          ( SIGN = 'I' OPTION = 'EQ' LOW = '4000' ) ).

    "Get FM budget data
    SELECT A~RFIKRS AS FIKRS,
           A~RFUND AS FINCODE,
           A~RFUNDSCTR AS FISTL,
           A~RYEAR AS GJAHR,
           A~RCMMTITEM AS FIPEX,
           A~BUDTYPE_9,
           A~HSLVT,
           A~HSL01,
           A~HSL02,
           A~HSL03,
           A~HSL04,
           A~HSL05,
           A~HSL06,
           A~HSL07,
           A~HSL08,
           A~HSL09,
           A~HSL10,
           A~HSL11,
           A~HSL12,
           A~HSL13,
           A~HSL14,
           A~HSL15,
           A~HSL16,
           A~RLDNR,
           A~RRCTY,
           A~RVERS,
           A~ROBJNR,
           A~COBJNR,
           A~SOBJNR,
           A~RTCUR,
           A~DRCRK,
           A~RPMAX
           FROM FMBDT AS A
           FOR ALL ENTRIES IN @MT_FUND
           WHERE A~RFIKRS = @MT_FUND-FIKRS
           AND   A~RFUND = @MT_FUND-FINCODE
           AND   A~RLDNR = '9F'
           AND   A~RVERS = '000'
           AND   A~RYEAR BETWEEN @MP_BEGFY AND @MP_ENDFY
           AND   A~RFUNDSCTR IN @MR_FICTR
           AND   A~RCMMTITEM IN @LR_FIPEX
           AND   A~VALTYPE_9 = 'B1'
           AND   A~WFSTATE_9 = 'P'
           AND   A~BUDTYPE_9 IN @LR_BUDTYPE
           INTO TABLE @MT_FMBDT.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM005 ----
  METHOD GET_CONSTANT_RATE.

    CLEAR RV_RATE.
    SELECT SINGLE KWERT INTO @DATA(LV_KWERT) FROM T511K WHERE MOLGA = 'UN'
                                                        AND   KONST = 'ZCUSD'
                                                        AND   ENDDA >= @IV_DATE
                                                        AND   BEGDA <= @IV_DATE.
    IF SY-SUBRC = 0.
      RV_RATE = LV_KWERT / 100000.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM006 ----
  METHOD GET_DATA.

    "Initialize data
    ME->INITIALIZE( ).
    "Get fund
    ME->GET_FUND_FROM_DB( ).
    CHECK MT_FUND IS NOT INITIAL.
    "Get budget
    ME->GET_BUDGET_FROM_DB( ).
    "Get expenses
    ME->GET_EXPENSES_FROM_DB( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM007 ----
  METHOD GET_EXPENSES_FROM_DB.

    DATA LR_FIPEX TYPE RANGE OF FM_FIPEX.
    DATA LR_WRTTP TYPE RANGE OF FM_WRTTP.

    LR_FIPEX = VALUE #( ( SIGN = 'E' OPTION = 'EQ' LOW = 'GAINS' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'REVENUE' ) ).

    "Get value types for incurred expenses
    SELECT 'I', 'EQ', WRTTP FROM YTFM_WRTTP_GR WHERE WRTTP_GRP = 'INCURRED'
                            INTO TABLE @LR_WRTTP.

    "Get data for realized
    SELECT A~FIKRS AS FIKRS,
           A~FONDS AS FINCODE,
           A~FISTL,
           A~GJAHR,
           A~WRTTP,
           A~FIPEX,
           A~TRBTR,
           A~TWAER,
           A~FKBTR,
           A~VRGNG,
           H~BUDAT,
           H~BLART,
           A~BUS_AREA,
           A~BUKRS,
           A~KNGJAHR,
           A~KNBELNR,
           A~KNBUZEI,
           H~AWTYP,
           H~AWREF,
           H~AWORG,
           A~FMBELNR,
           A~FMBUZEI,
           A~BTART,
           A~RLDNR,
           A~STUNR
           FROM FMIFIIT AS A
           LEFT OUTER JOIN FMIFIHD AS H ON  H~FMBELNR = A~FMBELNR
                                        AND H~FIKRS  = A~FIKRS
           FOR ALL ENTRIES IN @MT_FUND
           WHERE A~FIKRS = @MT_FUND-FIKRS
           AND   A~FONDS = @MT_FUND-FINCODE
           AND   A~RLDNR = '9A'
           AND   A~GJAHR BETWEEN @MP_BEGFY AND @MP_ENDFY
           AND   A~FISTL IN @MR_FICTR
           AND   A~FIPEX IN @LR_FIPEX
           AND   A~WRTTP IN @LR_WRTTP
          INTO TABLE @MT_FMIFI.

    "Get BSEG corresponding lines
    IF MT_FMIFI IS NOT INITIAL.
      SELECT S~BUKRS, S~BELNR, S~GJAHR, S~BUZEI, S~SHKZG, S~DMBTR, K~BUDAT, K~WWERT
             FROM BSEG AS S
             INNER JOIN BKPF AS K ON  K~BUKRS = S~BUKRS
                                  AND K~BELNR = S~BELNR
                                  AND K~GJAHR = S~GJAHR
             FOR ALL ENTRIES IN @MT_FMIFI
             WHERE S~BUKRS = @MT_FMIFI-BUKRS
             AND   S~BELNR = @MT_FMIFI-KNBELNR
             AND   S~GJAHR = @MT_FMIFI-KNGJAHR
             AND   S~BUZEI = @MT_FMIFI-KNBUZEI
             INTO TABLE @MT_BSEG.
    ENDIF.


    CLEAR LR_WRTTP.
    "Get value types for incurred expenses
    SELECT 'I', 'EQ', WRTTP FROM YTFM_WRTTP_GR WHERE WRTTP_GRP = 'COM_RES'
                            INTO TABLE @LR_WRTTP.

    "Get data for commitment
    SELECT A~FIKRS,
           A~FONDS AS FINCODE,
           A~FISTL,
           A~GJAHR,
           A~WRTTP,
           A~FIPEX,
           A~TRBTR,
           A~TWAER,
           A~FKBTR,
           A~VRGNG,
           A~REFBN,
           A~REFBT,
           A~RFORG,
           A~RFPOS,
           A~RFKNT,
           A~RFETE,
           A~RCOND,
           A~RFTYP,
           A~RFSYS,
           A~BTART,
           A~RLDNR,
           A~STUNR
           FROM FMIOI AS A
           FOR ALL ENTRIES IN @MT_FUND
           WHERE A~FIKRS = @MT_FUND-FIKRS
           AND   A~FONDS = @MT_FUND-FINCODE
           AND   A~RLDNR = '9A'
           AND   A~GJAHR BETWEEN @MP_BEGFY AND @MP_ENDFY
           AND   A~FISTL IN @MR_FICTR
           AND   A~FIPEX IN @LR_FIPEX
           AND   A~WRTTP IN @LR_WRTTP
           INTO TABLE @MT_FMIOI.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM008 ----
  METHOD GET_FM_AREA_CURRENCY.

    SELECT SINGLE WAERS INTO @RV_WAERS FROM FM01 WHERE FIKRS = @IV_FIKRS.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM009 ----
  METHOD GET_FUND_FROM_DB.

    SELECT DISTINCT A~FIKRS,
                    A~FINCODE,
                    A~TYPE,
                    A~DATAB,
                    A~DATBIS,
                    B~BESCHR,
                    B~BEZEICH
                    FROM FMFINCODE AS A
                    INNER JOIN FMFINT AS B ON  B~SPRAS = @SY-LANGU
                                           AND B~FIKRS = A~FIKRS
                                           AND B~FINCODE = A~FINCODE
                    LEFT OUTER JOIN YTFM_FUND_C5 AS C ON  C~FIKRS = A~FIKRS
                                                      AND C~FINCODE = A~FINCODE
                    WHERE A~FIKRS = @MP_FIKRS
                    AND   A~FINCODE IN @MR_FUND
                    AND   A~DATAB <= @MV_ENDDA
                    AND   A~DATBIS >= @MV_BEGDA
                    AND   A~TYPE IN @MR_TYPE
                    AND   C~C5_ID IN @MR_C5_ID
                    INTO TABLE @MT_FUND.

    CHECK MT_FUND IS NOT INITIAL.

    "Get C5 assignment for fiscal year
    SELECT A~FIKRS, A~FINCODE, A~C5_ID, A~C5_SEL, A~FM_OUTPUT, T~ONAME, O~OTYPE
           FROM YTFM_FUND_C5 AS A
           INNER JOIN YTFM_C5 AS C ON C~C5_ID = A~C5_ID
           LEFT OUTER JOIN YTFM_OUTPUT AS O ON O~FM_OUTPUT = A~FM_OUTPUT
           LEFT OUTER JOIN YTFM_OUTPUT_T AS T ON  T~SPRSL = @SY-LANGU
                                              AND T~FM_OUTPUT = A~FM_OUTPUT
           FOR ALL ENTRIES IN @MT_FUND
           WHERE A~FIKRS = @MT_FUND-FIKRS
           AND   A~FINCODE = @MT_FUND-FINCODE
           AND   C~YEAR_FROM <= @MP_ENDFY
           AND   C~YEAR_TO >= @MP_BEGFY
           AND   A~C5_ID IN @MR_C5_ID
           INTO TABLE @MT_FUND_C5.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00A ----
  METHOD INITIALIZE.

    "Get begin and end dates from selection period
    MV_BEGDA = |{ MP_BEGFY }0101|.
    MV_ENDDA = |{ MP_ENDFY }1231|.

    "Get FM area currency
    MV_FM_WAERS = GET_FM_AREA_CURRENCY( MP_FIKRS ).

    "Get constant rate at first date of biennium
    MV_CONST_RATE = GET_CONSTANT_RATE( IV_DATE = MV_BEGDA ).

    "Get PC commitment items
    SELECT 'I', 'EQ', FIPEX FROM FMCI WHERE FIPUP = 'PC' INTO TABLE @MT_FIPEX_PC.

    "Get NPC commitment items
    SELECT 'I', 'EQ', FIPEX FROM FMCI WHERE FIPUP = 'NPC' INTO TABLE @MT_FIPEX_NPC.

    "Fill commitment item for personnel cost impact
    MT_FIPEX_PC_IMPACT = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDO' )
                                  ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDCE' )
                                  ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDSP' ) ).

    "Business transaction HR
    MT_VRGNG = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRM1' )   "PBC pre-commitment
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRM2' )   "PBC commitment
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRP1' ) )."Payroll posting

    "instanciate BR business logic class
    MO_BR_EXCHANGE_RATE_BL = NEW YCL_FM_BR_EXCHANGE_RATE_BL( ).

    "Get Business transaction texts
    SELECT VRGNG, TXT FROM TJ01T WHERE SPRAS = @SY-LANGU INTO TABLE @MT_TJ01T.

    "Get object type texts
    SELECT AWTYP, OTEXT FROM TTYPT WHERE SPRAS = @SY-LANGU INTO TABLE @MT_TTYPT.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00B ----
  METHOD PRELIMINARY_CHECKS.

    DATA LV_BEGBI TYPE DATUM.
    DATA LV_ENDBI TYPE DATUM.

    IF GET_FM_AREA_CURRENCY( IV_FIKRS ) <> C_USD.
      ES_RETURN-ID = 'YFM1'.
      ES_RETURN-NUMBER = '015'.
      ES_RETURN-TYPE = 'E'.
      EXIT.
    ENDIF.

    "Check period
    IF IV_BEGFY > IV_ENDFY.
      ES_RETURN-ID = 'YFM1'.
      ES_RETURN-NUMBER = '014'.
      ES_RETURN-TYPE = 'E'.
      ES_RETURN-MESSAGE_V1 = YCL_CA_UTILITIES=>CONVERT_TO_MSGV( IV_BEGFY ).
      ES_RETURN-MESSAGE_V2 = YCL_CA_UTILITIES=>CONVERT_TO_MSGV( IV_ENDFY ).
      EXIT.
    ENDIF.
    "Check all include in a biennium
    YCL_CA_UTILITIES=>GET_BIENNIUM_FOR_DATE( EXPORTING IV_DATE = |{ IV_BEGFY }0101|
                                             IMPORTING EV_BEGBI = LV_BEGBI
                                                       EV_ENDBI = LV_ENDBI ).
    IF IV_BEGFY <> LV_BEGBI(4) OR IV_ENDFY <> LV_ENDBI(4).
      ES_RETURN-ID = 'YFM1'.
      ES_RETURN-NUMBER = '018'.
      ES_RETURN-TYPE = 'E'.
      EXIT.
    ENDIF.

    IF GET_CONSTANT_RATE( IV_DATE = LV_BEGBI ) = 0.
      ES_RETURN-ID = 'YFM1'.
      ES_RETURN-NUMBER = '016'.
      ES_RETURN-TYPE = 'E'.
      ES_RETURN-MESSAGE_V1 = C_USD.
      ES_RETURN-MESSAGE_V2 = YCL_CA_UTILITIES=>CONVERT_TO_MSGV( LV_BEGBI ).
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00C ----
  METHOD PREPARE_DATA.

    CLEAR: ES_LIST, ET_DETAIL_EXP, ET_DETAIL_COM.
    MOVE-CORRESPONDING IS_FUND TO ES_LIST.

    "Get C/5 assignment
    READ TABLE MT_FUND_C5 INTO DATA(LS_FUND_C5) WITH KEY FIKRS = IS_FUND-FIKRS
                                                         FINCODE = IS_FUND-FINCODE.
    IF SY-SUBRC = 0.
      ES_LIST-C5_ID = LS_FUND_C5-C5_ID.
      ES_LIST-FM_OUTPUT = LS_FUND_C5-FM_OUTPUT.
      ES_LIST-ONAME = LS_FUND_C5-ONAME.
      ES_LIST-OTYPE = LS_FUND_C5-OTYPE.
      ES_LIST-C5_SEL = LS_FUND_C5-C5_SEL.
    ENDIF.

    "Determine budget amount
    ME->DETERMINE_BUDGET_AMOUNT( EXPORTING IV_FIKRS = IS_FUND-FIKRS
                                           IV_FINCODE = IS_FUND-FINCODE
                                 IMPORTING EV_AMOUNT = ES_LIST-BUDGET_UNORE ).
    "Determine expenses amount
    ME->DETERMINE_EXPENSES_AMOUNTS( EXPORTING IS_FUND = IS_FUND
                                              IV_C5_ID = ES_LIST-C5_ID
                                    IMPORTING EV_NPC_EXP_UNORE = ES_LIST-NPC_EXPENSES_UNORE
                                              EV_NPC_EXP_BR_IMPACT = ES_LIST-NPC_EXPENSES_BR_IMPACT
                                              EV_PC_EXP_UNORE = ES_LIST-PC_EXPENSES_UNORE
                                              EV_PC_EXP_BR_IMPACT = ES_LIST-PC_EXPENSES_BR_IMPACT
                                              ET_DETAIL = ET_DETAIL_EXP ).

    ME->DETERMINE_COMMITMENT_AMOUNTS( EXPORTING IS_FUND = IS_FUND
                                                IV_C5_ID = ES_LIST-C5_ID
                                      IMPORTING EV_PC_COM_UNORE = ES_LIST-PC_COMMIT_UNORE
                                                EV_NPC_COM_UNORE = ES_LIST-NPC_COMMIT_UNORE
                                                EV_PC_COM_BR_IMPACT = ES_LIST-PC_COMMIT_BR_IMPACT
                                                EV_NPC_COM_BR_IMPACT = ES_LIST-NPC_COMMIT_BR_IMPACT
                                                ET_DETAIL = ET_DETAIL_COM ).
    "Calculate totals
    ME->SET_TOTALS( CHANGING CS_LIST = ES_LIST ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00D ----
  METHOD SET_COLUMNS.

    DATA LO_COLUMNS TYPE REF TO CL_SALV_COLUMNS_TABLE.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.
    DATA LS_COLOR TYPE LVC_S_COLO.

    LO_COLUMNS = MO_SALV_TABLE->GET_COLUMNS( ).
    "Column width optimization
    LO_COLUMNS->SET_OPTIMIZE( ABAP_TRUE ).
    LO_COLUMNS->SET_KEY_FIXATION( ABAP_TRUE ).

    TRY.
        LO_COLUMNS->SET_COLOR_COLUMN( 'COLFIELD' ).
      CATCH CX_SALV_DATA_ERROR.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FIKRS' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FINCODE' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'TYPE' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'DATAB' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'DATBIS' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BESCHR' ).
        LO_COLUMN->SET_LONG_TEXT( 'Fund description' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BEZEICH' ).
        LO_COLUMN->SET_LONG_TEXT( 'Fund name' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FM_OUTPUT' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'C5_SEL' ).
        LO_COLUMN->SET_CELL_TYPE( IF_SALV_C_CELL_TYPE=>CHECKBOX ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'NPC_EXPENSES_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |NPC expenses (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'NPC_EXPENSES_BR_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( 'NPC expenses BR impact' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_EXPENSES_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |PC expenses (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_EXPENSES_BR_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( 'PC expenses BR impact' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_COMMIT_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |PC commitments (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'NPC_COMMIT_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |NPC commitments (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_COMMIT_BR_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( 'PC commitments BR impact' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'NPC_COMMIT_BR_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( 'NPC commitments BR impact' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    CASE MV_LIST_TYPE.

      WHEN 'M'.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BUDGET_UNORE' ).
            LO_COLUMN->SET_LONG_TEXT( |Budget (UNORE) in { MV_FM_WAERS }| ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'NPC_EXPENSES_TOTAL' ).
            LO_COLUMN->SET_LONG_TEXT( 'Total NPC expenses at BR' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_EXPENSES_TOTAL' ).
            LO_COLUMN->SET_LONG_TEXT( 'Total PC expenses at BR' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.


        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'COMMIT_TOTAL' ).
            LO_COLUMN->SET_LONG_TEXT( 'Total commitments at BR' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'AVAILABLE' ).
            LO_COLUMN->SET_LONG_TEXT( |Available in { MV_FM_WAERS }| ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EXPENSES_BR_IMPACT' ).
            LO_COLUMN->SET_LONG_TEXT( 'Impact BR expenses' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'COMMIT_BR_IMPACT' ).
            LO_COLUMN->SET_LONG_TEXT( 'Impact BR commitments' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'TOTAL_BR_IMPACT' ).
            LO_COLUMN->SET_LONG_TEXT( 'Total BR impact' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

      WHEN 'D'.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'VRGNG' ).
            LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'AWTYP' ).
            LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FM_AMOUNT_TYPE' ).
            LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FM_AMOUNT_TYPE_TEXT' ).
            LO_COLUMN->SET_LONG_TEXT( 'Actuals/Commitments' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'VRGNG_TXT' ).
            LO_COLUMN->SET_LONG_TEXT( 'Business transaction' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FM_DOC' ).
            LO_COLUMN->SET_LONG_TEXT( 'FM document n°' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

        TRY.
            LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'FM_POS' ).
            LO_COLUMN->SET_LONG_TEXT( 'FM doc position' ).
            LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
          CATCH CX_SALV_NOT_FOUND.
        ENDTRY.

    ENDCASE.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00E ----
  METHOD SET_DISPLAY_SETTINGS.

    DATA LO_DISPLAY_SETTINGS TYPE REF TO CL_SALV_DISPLAY_SETTINGS.

    LO_DISPLAY_SETTINGS = MO_SALV_TABLE->GET_DISPLAY_SETTINGS( ).
    LO_DISPLAY_SETTINGS->SET_STRIPED_PATTERN( ABAP_TRUE ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00F ----
  METHOD SET_FUNCTIONS.

    DATA LO_FUNCTIONS TYPE REF TO CL_SALV_FUNCTIONS_LIST.

    LO_FUNCTIONS = MO_SALV_TABLE->GET_FUNCTIONS( ).
    LO_FUNCTIONS->SET_ALL( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00G ----
  METHOD SET_LAYOUT.

    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.
    DATA LO_LAYOUT TYPE REF TO CL_SALV_LAYOUT.

    LO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = MV_REPID.
    LO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    LO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).
    "lo_layout->set_default( abap_true ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00H ----
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

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00I ----
  METHOD GET_BR_IMPACT.

    TYPES LTY_AMOUNT TYPE FM_FKBTRPY.
    DATA LV_DATE TYPE DATUM.

    CLEAR EV_BR_IMPACT.

    "Get fund type
    READ TABLE MT_FUND INTO DATA(LS_FUND) WITH KEY FIKRS = IS_FMIFI-FIKRS
                                                   FINCODE = IS_FMIFI-FINCODE.
    CHECK SY-SUBRC = 0.

    "Check conditions
    CHECK MO_BR_EXCHANGE_RATE_BL->CHECK_CONDITIONS( IV_BUKRS = IS_FMIFI-BUKRS
                                                    IV_FIKRS = IS_FMIFI-FIKRS
                                                    IV_GSBER = IS_FMIFI-BUS_AREA
                                                    IV_WAERS = IS_FMIFI-TWAER
                                                    IV_FIPEX = IS_FMIFI-FIPEX
                                                    IV_VRGNG = IS_FMIFI-VRGNG
                                                    IV_FTYPE = LS_FUND-TYPE ).

    "Get Fi line corresponding
    READ TABLE MT_BSEG INTO DATA(LS_BSEG) WITH KEY BUKRS = IS_FMIFI-BUKRS
                                                   BELNR = IS_FMIFI-KNBELNR
                                                   GJAHR = IS_FMIFI-KNGJAHR
                                                   BUZEI = IS_FMIFI-KNBUZEI.
    IF SY-SUBRC = 0.
      IF LS_BSEG-WWERT IS NOT INITIAL.
        LV_DATE = LS_BSEG-WWERT.
      ELSE.
        LV_DATE = LS_BSEG-BUDAT.
      ENDIF.
    ELSE.
      LV_DATE = IS_FMIFI-BUDAT.
    ENDIF.

    "Calculate BR impact
    MO_BR_EXCHANGE_RATE_BL->GET_BR_IMPACT( EXPORTING IV_BUKRS = IS_FMIFI-BUKRS
                                                     IV_GJAHR = IS_FMIFI-GJAHR
                                                     IV_FKBTRP = CONV LTY_AMOUNT( IS_FMIFI-FKBTR )
                                                     IV_TRBTRP = CONV LTY_AMOUNT( IS_FMIFI-TRBTR )
                                                     IV_TWAER = IS_FMIFI-TWAER
                                                     IV_WRTTP = IS_FMIFI-WRTTP
                                                     IV_VRGNG = IS_FMIFI-VRGNG
                                                     IV_BTART = IS_FMIFI-BTART
                                                     IV_BUDAT = LV_DATE
                                                     IV_BSEG_DMBTR = LS_BSEG-DMBTR
                                                     IV_BSEG_SHKZG = LS_BSEG-SHKZG
                                                     IV_FINCODE = IS_FMIFI-FINCODE
                                           IMPORTING EV_ZZAMOUNTBRDIFF = EV_BR_IMPACT ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00J ----
  METHOD DETERMINE_COMMITMENT_AMOUNTS.

    DATA LV_NPC_BR_IMPACT TYPE WERTV9.
    DATA LS_DETAIL TYPE TY_LIST_DET.

    CLEAR : EV_PC_COM_UNORE, EV_NPC_COM_UNORE, EV_PC_COM_BR_IMPACT, EV_NPC_COM_BR_IMPACT, ET_DETAIL.

    LOOP AT MT_FMIOI INTO DATA(LS_FMIOI) WHERE FIKRS = IS_FUND-FIKRS
                                         AND   FINCODE = IS_FUND-FINCODE.

      CHECK LS_FMIOI-TRBTR <> 0 OR LS_FMIOI-FKBTR <> 0.

      CLEAR LS_DETAIL.
      MOVE-CORRESPONDING IS_FUND TO LS_DETAIL.
      LS_DETAIL-C5_ID = IV_C5_ID.
      LS_DETAIL-GJAHR = LS_FMIOI-GJAHR.
      LS_DETAIL-FIPEX = LS_FMIOI-FIPEX.

      "inverse sign
      LS_FMIOI-TRBTR = LS_FMIOI-TRBTR * -1.
      LS_FMIOI-FKBTR = LS_FMIOI-FKBTR * -1.

      "Fill PC commitments in UNORE
      IF LS_FMIOI-FIPEX IN MT_FIPEX_PC.
        ADD LS_FMIOI-FKBTR TO EV_PC_COM_UNORE.
        LS_DETAIL-PC_COMMIT_UNORE = LS_FMIOI-FKBTR.
      ENDIF.

      "Fill NPC commitments in UNORE
      IF LS_FMIOI-FIPEX IN MT_FIPEX_NPC.
        ADD LS_FMIOI-FKBTR TO EV_NPC_COM_UNORE.
        LS_DETAIL-NPC_COMMIT_UNORE = LS_FMIOI-FKBTR.
      ENDIF.

      "Fill PC commitments BR impact
      IF LS_FMIOI-FIPEX IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIOI-FKBTR TO EV_PC_COM_BR_IMPACT.
        LS_DETAIL-PC_COMMIT_BR_IMPACT = LS_FMIOI-FKBTR.
      ENDIF.

      IF LS_FMIOI-TWAER = C_EUR.
        IF LS_FMIOI-FIPEX IN MT_FIPEX_NPC.
          LV_NPC_BR_IMPACT = ( LS_FMIOI-TRBTR / MV_CONST_RATE ) - LS_FMIOI-FKBTR.
          ADD LV_NPC_BR_IMPACT TO EV_NPC_COM_BR_IMPACT.
          LS_DETAIL-NPC_COMMIT_BR_IMPACT = LV_NPC_BR_IMPACT.
        ENDIF.
      ENDIF.

      IF MV_LIST_TYPE = 'D'.
        LS_DETAIL-FM_AMOUNT_TYPE = '2'.
        LS_DETAIL-FM_AMOUNT_TYPE_TEXT = ME->GET_AMOUNT_TYPE_TEXT( LS_DETAIL-FM_AMOUNT_TYPE ).
        "Get business transaction text.
        LS_DETAIL-VRGNG = LS_FMIOI-VRGNG.
        LS_DETAIL-VRGNG_TXT = ME->GET_BUSINESS_TRANSACTION_TEXT( IV_VRGNG =  LS_DETAIL-VRGNG ).
        "Get object type text
        LS_DETAIL-AWTYP = LS_FMIOI-RFTYP.
        LS_DETAIL-AWTYP_TXT = ME->GET_OBJECT_TYPE_TEXT( IV_AWTYP = LS_DETAIL-AWTYP ).
        LS_DETAIL-AWREF = LS_FMIOI-REFBN.
        LS_DETAIL-AWORG = LS_FMIOI-RFPOS.
        LS_DETAIL-FM_DOC = LS_FMIOI-REFBN.
        LS_DETAIL-FM_POS = LS_FMIOI-RFPOS.
        APPEND LS_DETAIL TO ET_DETAIL.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00K ----
  METHOD SET_COLOR.

    CLEAR RS_COLOR.
    RS_COLOR-FNAME = IV_FNAME.
    RS_COLOR-COLOR-COL = IV_COL.
    RS_COLOR-COLOR-INT = IV_INT.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00L ----
  METHOD DISPLAY_MESSAGE.

    MV_REPID = IV_REPID.

    TRY.
        CL_SALV_TABLE=>FACTORY( IMPORTING R_SALV_TABLE = MO_SALV_TABLE
                                CHANGING  T_TABLE      = MT_MESSAGE ).
      CATCH CX_SALV_MSG .
    ENDTRY.

    "ALV functions activation
    ME->SET_FUNCTIONS( ).

    "ALV layout
    ME->SET_LAYOUT( ).

    "ALV display settings
    ME->SET_DISPLAY_SETTINGS( ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00M ----
  METHOD GET_AMOUNT_TYPE_TEXT.

    CLEAR RV_TEXT.
    CASE IV_AMOUNT_TYPE.
      WHEN '1'.
        RV_TEXT = 'Actuals'.
      WHEN '2'.
        RV_TEXT = 'Commitments'.
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00N ----
  METHOD GET_BUSINESS_TRANSACTION_TEXT.

    CLEAR RV_TEXT.
    READ TABLE MT_TJ01T INTO DATA(LS_TJ01T) WITH KEY VRGNG = IV_VRGNG.
    IF SY-SUBRC = 0.
      RV_TEXT = LS_TJ01T-TXT.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00O ----
  METHOD GET_DATA_FROM_HIST.

    "Initialize data
    ME->INITIALIZE( ).
    "Get fund
    ME->GET_FUND_FROM_DB( ).
    CHECK MT_FUND IS NOT INITIAL.
    "Read history tables
    ME->GET_HISTORY_FROM_DB( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00P ----
  METHOD GET_HISTORY_FROM_DB.

    SELECT * FROM YTFM_BR_REP_H FOR ALL ENTRIES IN @MT_FUND
                                WHERE REF_DATE = @MP_CDATE
                                AND   FIKRS = @MT_FUND-FIKRS
                                AND   FINCODE = @MT_FUND-FINCODE
             INTO TABLE @MT_HIST_HEAD.

    SELECT * FROM YTFM_BR_REP_D FOR ALL ENTRIES IN @MT_FUND
                                WHERE REF_DATE = @MP_CDATE
                                AND   FIKRS = @MT_FUND-FIKRS
                                AND   FINCODE = @MT_FUND-FINCODE
             INTO TABLE @MT_HIST_DETAIL.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00Q ----
  METHOD GET_LIST_OF_STORED_DATES.

    CLEAR ET_STORED_DATES.
    SELECT DISTINCT REF_DATE, AEDAT, AETIM FROM YTFM_BR_REP_H INTO TABLE @ET_STORED_DATES.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00R ----
  METHOD GET_OBJECT_TYPE_TEXT.

    CLEAR RV_TEXT.
    READ TABLE MT_TTYPT INTO DATA(LS_TTYPT) WITH KEY AWTYP = IV_AWTYP.
    IF SY-SUBRC = 0.
      RV_TEXT = LS_TTYPT-OTEXT.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00S ----
  METHOD INSERT_INTO_DATABASE.

    DATA LS_LIST TYPE TY_LIST.
    DATA LT_DETAIL_EXP TYPE TTY_LIST_DET.
    DATA LT_DETAIL_COM TYPE TTY_LIST_DET.
    DATA LS_DB_HEAD TYPE YTFM_BR_REP_H.
    DATA LV_AEDAT TYPE DATUM.
    DATA LV_AETIM TYPE UZEIT.
    DATA LS_MESSAGE TYPE TY_MESSAGE.

    LV_AEDAT = SY-DATUM.
    LV_AETIM = SY-UZEIT.

    CLEAR: MV_ROW_H, MV_ROW_D.

    MV_LIST_TYPE = 'D'.

    LOOP AT MT_FUND INTO DATA(LS_FUND).

      ME->PREPARE_DATA( EXPORTING IS_FUND = LS_FUND
                        IMPORTING ES_LIST = LS_LIST
                                  ET_DETAIL_EXP = LT_DETAIL_EXP
                                  ET_DETAIL_COM = LT_DETAIL_COM ).

      CHECK LS_LIST-BUDGET_UNORE <> 0 OR LS_LIST-NPC_EXPENSES_UNORE <> 0 OR LS_LIST-PC_EXPENSES_UNORE <> 0.

      "Insert line in YTFM_BR_REP_H
      CLEAR LS_DB_HEAD.
      LS_DB_HEAD-REF_DATE = MP_CDATE.
      LS_DB_HEAD-AEDAT = LV_AEDAT.
      LS_DB_HEAD-AETIM = LV_AETIM.
      MOVE-CORRESPONDING LS_LIST TO LS_DB_HEAD.
      INSERT YTFM_BR_REP_H FROM LS_DB_HEAD.
      IF SY-SUBRC <> 0.
        WRITE ICON_LED_RED TO LS_MESSAGE-STATUS AS ICON.
        LS_MESSAGE-MESSAGE = |Unable to insert in YTFM_BR_REP_H with key { LS_DB_HEAD-REF_DATE } { LS_DB_HEAD-FIKRS } { LS_DB_HEAD-FINCODE }|.
        APPEND LS_MESSAGE TO MT_MESSAGE.
      ELSE.
        ADD 1 TO MV_ROW_H.
      ENDIF.
      "Insert lines in YTFM_BR_REP_D
      CLEAR MV_SEQUENCE.
      ME->INSERT_INTO_DETAIL_TABLE( IT_DETAIL = LT_DETAIL_EXP ).
      ME->INSERT_INTO_DETAIL_TABLE( IT_DETAIL = LT_DETAIL_COM ).

    ENDLOOP.

    CLEAR LS_MESSAGE.
    IF MV_ROW_H IS INITIAL.
      WRITE ICON_LED_YELLOW TO LS_MESSAGE-STATUS AS ICON.
    ELSE.
      WRITE ICON_LED_GREEN TO LS_MESSAGE-STATUS AS ICON.
    ENDIF.
    LS_MESSAGE-MESSAGE = |{ MV_ROW_H } row(s) inserted in YTFM_BR_REP_H|.
    APPEND LS_MESSAGE TO MT_MESSAGE.

    CLEAR LS_MESSAGE.
    IF MV_ROW_D IS INITIAL.
      WRITE ICON_LED_YELLOW TO LS_MESSAGE-STATUS AS ICON.
    ELSE.
      WRITE ICON_LED_GREEN TO LS_MESSAGE-STATUS AS ICON.
    ENDIF.
    LS_MESSAGE-MESSAGE = |{ MV_ROW_D } row(s) inserted in YTFM_BR_REP_D|.
    APPEND LS_MESSAGE TO MT_MESSAGE.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00T ----
  METHOD INSERT_INTO_DETAIL_TABLE.

    DATA LS_DB_DETAIL TYPE YTFM_BR_REP_D.
    DATA LS_MESSAGE TYPE TY_MESSAGE.

    LOOP AT IT_DETAIL INTO DATA(LS_DETAIL).
      CLEAR LS_DB_DETAIL.
      MOVE-CORRESPONDING LS_DETAIL TO LS_DB_DETAIL.
      LS_DB_DETAIL-REF_DATE = MP_CDATE.
      ADD 1 TO MV_SEQUENCE.
      LS_DB_DETAIL-SEQID = MV_SEQUENCE.
      CASE LS_DETAIL-FM_AMOUNT_TYPE.
        WHEN '1'.  "Actuals
          LS_DB_DETAIL-NPC_UNORE = LS_DETAIL-NPC_EXPENSES_UNORE .
          LS_DB_DETAIL-NPC_BR_IMPACT = LS_DETAIL-NPC_EXPENSES_BR_IMPACT.
          LS_DB_DETAIL-PC_UNORE = LS_DETAIL-PC_EXPENSES_UNORE.
          LS_DB_DETAIL-PC_BR_IMPACT = LS_DETAIL-PC_EXPENSES_BR_IMPACT.
        WHEN '2'.  "Commitments
          LS_DB_DETAIL-NPC_UNORE = LS_DETAIL-NPC_COMMIT_UNORE .
          LS_DB_DETAIL-NPC_BR_IMPACT = LS_DETAIL-NPC_COMMIT_BR_IMPACT.
          LS_DB_DETAIL-PC_UNORE = LS_DETAIL-PC_COMMIT_UNORE.
          LS_DB_DETAIL-PC_BR_IMPACT = LS_DETAIL-PC_COMMIT_BR_IMPACT.
      ENDCASE.
      INSERT YTFM_BR_REP_D FROM LS_DB_DETAIL.
      IF SY-SUBRC <> 0.
        WRITE ICON_LED_RED TO LS_MESSAGE-STATUS AS ICON.
        LS_MESSAGE-MESSAGE = |Unable to insert in YTFM_BR_REP_D with key { LS_DB_DETAIL-REF_DATE } { LS_DB_DETAIL-FIKRS } { LS_DB_DETAIL-FINCODE } { LS_DB_DETAIL-SEQID }|.
        APPEND LS_MESSAGE TO MT_MESSAGE.
      ELSE.
        ADD 1 TO MV_ROW_D.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00U ----
  METHOD PREPARE_DATA_FOR_ALV_HIST.

    DATA LS_LIST TYPE TY_LIST.
    DATA LT_DETAIL TYPE TTY_LIST_DET.
    DATA LS_DETAIL TYPE TY_LIST_DET.
    DATA LS_FUND TYPE TY_FUND.
    DATA LS_FUND_C5 TYPE TY_FUND_C5.

    MV_LIST_TYPE = IV_LIST_TYPE.

    LOOP AT MT_HIST_HEAD INTO DATA(LS_HIST_HEAD).
      CLEAR: LS_LIST, LS_FUND, LS_FUND_C5.
      MOVE-CORRESPONDING LS_HIST_HEAD TO LS_LIST.
      "Set calculated amounts
      ME->SET_TOTALS( CHANGING CS_LIST = LS_LIST ).

      "Complete fund data
      READ TABLE MT_FUND INTO LS_FUND WITH KEY FIKRS = LS_HIST_HEAD-FIKRS
                                               FINCODE = LS_HIST_HEAD-FINCODE.
      IF SY-SUBRC = 0.
        MOVE-CORRESPONDING LS_FUND TO LS_LIST.
        "Get C/5 assignment
        READ TABLE MT_FUND_C5 INTO LS_FUND_C5 WITH KEY FIKRS = LS_HIST_HEAD-FIKRS
                                                       FINCODE = LS_HIST_HEAD-FINCODE.
        IF SY-SUBRC = 0.
          LS_LIST-C5_ID = LS_FUND_C5-C5_ID.
          LS_LIST-FM_OUTPUT = LS_FUND_C5-FM_OUTPUT.
          LS_LIST-ONAME = LS_FUND_C5-ONAME.
          LS_LIST-OTYPE = LS_FUND_C5-OTYPE.
          LS_LIST-C5_SEL = LS_FUND_C5-C5_SEL.
        ENDIF.
      ENDIF.

      IF IV_LIST_TYPE = 'D'.
        CLEAR LT_DETAIL.
        LOOP AT MT_HIST_DETAIL INTO DATA(LS_HIST_DETAIL) WHERE REF_DATE = LS_HIST_HEAD-REF_DATE
                                                         AND   FIKRS = LS_HIST_HEAD-FIKRS
                                                         AND   FINCODE = LS_HIST_HEAD-FINCODE.
          CLEAR LS_DETAIL.
          MOVE-CORRESPONDING LS_HIST_DETAIL TO LS_DETAIL.
          MOVE-CORRESPONDING LS_FUND TO LS_DETAIL.
          "Get amount type text
          LS_DETAIL-FM_AMOUNT_TYPE_TEXT = ME->GET_AMOUNT_TYPE_TEXT( LS_HIST_DETAIL-FM_AMOUNT_TYPE ).
          "Get business transaction text.
          LS_DETAIL-VRGNG_TXT = ME->GET_BUSINESS_TRANSACTION_TEXT( IV_VRGNG =  LS_DETAIL-VRGNG ).
          "Get object type text
          LS_DETAIL-AWTYP_TXT = ME->GET_OBJECT_TYPE_TEXT( IV_AWTYP = LS_DETAIL-AWTYP ).
          "set amounts
          CASE LS_HIST_DETAIL-FM_AMOUNT_TYPE.
            WHEN '1'. "Actuals
              LS_DETAIL-NPC_EXPENSES_UNORE = LS_HIST_DETAIL-NPC_UNORE.
              LS_DETAIL-NPC_EXPENSES_BR_IMPACT = LS_HIST_DETAIL-NPC_BR_IMPACT.
              LS_DETAIL-PC_EXPENSES_UNORE = LS_HIST_DETAIL-PC_UNORE.
              LS_DETAIL-PC_EXPENSES_BR_IMPACT = LS_HIST_DETAIL-PC_BR_IMPACT.
            WHEN '2'.  "Commitments
              LS_DETAIL-NPC_COMMIT_UNORE = LS_HIST_DETAIL-NPC_UNORE.
              LS_DETAIL-NPC_COMMIT_BR_IMPACT = LS_HIST_DETAIL-NPC_BR_IMPACT.
              LS_DETAIL-PC_COMMIT_UNORE = LS_HIST_DETAIL-PC_UNORE.
              LS_DETAIL-PC_COMMIT_BR_IMPACT = LS_HIST_DETAIL-PC_BR_IMPACT.
          ENDCASE.
          APPEND LS_DETAIL TO LT_DETAIL.
        ENDLOOP.
      ENDIF.

      "Put data in ALV list
      ME->SET_DATA_TO_ALV_LIST_TABLES( IS_LIST = LS_LIST
                                       IT_DETAIL_1 = LT_DETAIL ).

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00V ----
  METHOD PREPARE_DATA_FOR_ALV_LIST.

    DATA LS_LIST TYPE TY_LIST.
    DATA LV_MINIMUM_BUDGET TYPE WERTV9.
    DATA LV_INT TYPE LVC_INT VALUE 1.
    DATA LT_DETAIL_EXP TYPE TTY_LIST_DET.
    DATA LT_DETAIL_COM TYPE TTY_LIST_DET.

    MV_LIST_TYPE = IV_LIST_TYPE.

    LOOP AT MT_FUND INTO DATA(LS_FUND).

      ME->PREPARE_DATA( EXPORTING IS_FUND = LS_FUND
                        IMPORTING ES_LIST = LS_LIST
                                  ET_DETAIL_EXP = LT_DETAIL_EXP
                                  ET_DETAIL_COM = LT_DETAIL_COM ).

      "Put data in ALV list
      ME->SET_DATA_TO_ALV_LIST_TABLES( IS_LIST = LS_LIST
                                       IT_DETAIL_1 = LT_DETAIL_EXP
                                       IT_DETAIL_2 = LT_DETAIL_COM ).

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00W ----
  METHOD SET_DATA_TO_ALV_LIST_TABLES.

    DATA LV_MINIMUM_BUDGET TYPE WERTV9.
    DATA LV_INT TYPE LVC_INT VALUE 1.

    "Don't keep funds without EUR expenses if asked
    IF MP_EUREXP = ABAP_TRUE.
      CHECK IS_LIST-NPC_EXPENSES_BR_IMPACT <> 0 OR IS_LIST-PC_EXPENSES_BR_IMPACT <> 0
         OR IS_LIST-PC_COMMIT_BR_IMPACT <> 0 OR IS_LIST-NPC_COMMIT_BR_IMPACT <> 0.
    ENDIF.

    IF IS_LIST-BUDGET_UNORE <> 0 OR IS_LIST-NPC_EXPENSES_UNORE <> 0 OR IS_LIST-PC_EXPENSES_UNORE <> 0.
      "Calculate minimum budget to check from percentage indicated in selection screen
      LV_MINIMUM_BUDGET = IS_LIST-BUDGET_UNORE * MP_PCT / 100.
      IF MP_FILTER = ABAP_TRUE.
        CHECK IS_LIST-AVAILABLE <= LV_MINIMUM_BUDGET.
      ENDIF.
      "Set colors
      CLEAR IS_LIST-COLFIELD.
      APPEND ME->SET_COLOR( IV_FNAME = 'C5_ID' IV_COL = COL_HEADING IV_INT = 1 ) TO IS_LIST-COLFIELD.
      APPEND ME->SET_COLOR( IV_FNAME = 'ONAME' IV_COL = COL_HEADING IV_INT = 1 ) TO IS_LIST-COLFIELD.
      APPEND ME->SET_COLOR( IV_FNAME = 'OTYPE' IV_COL = COL_HEADING IV_INT = 1 ) TO IS_LIST-COLFIELD.
      APPEND ME->SET_COLOR( IV_FNAME = 'C5_SEL' IV_COL = COL_HEADING IV_INT = 1 ) TO IS_LIST-COLFIELD.
      CASE MV_LIST_TYPE.
        WHEN 'M'.
          IF IS_LIST-AVAILABLE <= LV_MINIMUM_BUDGET.
            APPEND ME->SET_COLOR( IV_FNAME = 'AVAILABLE' IV_COL = COL_NEGATIVE IV_INT = 1 ) TO IS_LIST-COLFIELD.
          ENDIF.
          "Set color to TOTAL columns
          IF LV_INT = 1.
            LV_INT = 0.
          ELSE.
            LV_INT = 1.
          ENDIF.
          APPEND ME->SET_COLOR( IV_FNAME = 'NPC_EXPENSES_TOTAL' IV_COL = COL_GROUP IV_INT = LV_INT ) TO IS_LIST-COLFIELD.
          APPEND ME->SET_COLOR( IV_FNAME = 'PC_EXPENSES_TOTAL' IV_COL = COL_GROUP IV_INT = LV_INT ) TO IS_LIST-COLFIELD.
          APPEND ME->SET_COLOR( IV_FNAME = 'COMMIT_TOTAL' IV_COL = COL_GROUP IV_INT = LV_INT ) TO IS_LIST-COLFIELD.
          APPEND ME->SET_COLOR( IV_FNAME = 'TOTAL_BR_IMPACT' IV_COL = COL_GROUP IV_INT = LV_INT ) TO IS_LIST-COLFIELD.
          APPEND IS_LIST TO MT_LIST.
        WHEN 'D'.
          APPEND LINES OF IT_DETAIL_1 TO MT_LIST_DET.
          APPEND LINES OF IT_DETAIL_2 TO MT_LIST_DET.
      ENDCASE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CM00X ----
  METHOD SET_TOTALS.

    "Calculate total amounts for expenses
    CS_LIST-NPC_EXPENSES_TOTAL = CS_LIST-NPC_EXPENSES_UNORE + CS_LIST-NPC_EXPENSES_BR_IMPACT.
    CS_LIST-PC_EXPENSES_TOTAL = CS_LIST-PC_EXPENSES_UNORE + CS_LIST-PC_EXPENSES_BR_IMPACT.
    CS_LIST-EXPENSES_BR_IMPACT = CS_LIST-NPC_EXPENSES_BR_IMPACT + CS_LIST-PC_EXPENSES_BR_IMPACT.

    "Calculate total amounts for commitments
    CS_LIST-COMMIT_TOTAL = CS_LIST-PC_COMMIT_UNORE + CS_LIST-NPC_COMMIT_UNORE + CS_LIST-PC_COMMIT_BR_IMPACT + CS_LIST-NPC_COMMIT_BR_IMPACT.
    CS_LIST-COMMIT_BR_IMPACT = CS_LIST-PC_COMMIT_BR_IMPACT + CS_LIST-NPC_COMMIT_BR_IMPACT.

    "Calculate available amount
    CS_LIST-AVAILABLE = CS_LIST-BUDGET_UNORE - CS_LIST-NPC_EXPENSES_TOTAL - CS_LIST-PC_EXPENSES_TOTAL - CS_LIST-COMMIT_TOTAL.
    CS_LIST-TOTAL_BR_IMPACT = CS_LIST-EXPENSES_BR_IMPACT + CS_LIST-COMMIT_BR_IMPACT.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CO ----
PROTECTED SECTION.

* ---- YCL_FM_CONSTANT_DOLLAR_BL_V2==CU ----
CLASS YCL_FM_CONSTANT_DOLLAR_BL_V2 DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  TYPES:
    BEGIN OF TY_STORED_LIST,
             REF_DATE TYPE YE_DATE_REFERENCE,
             AEDAT    TYPE AEDAT,
             AETIM    TYPE AS4TIME,
           END OF TY_STORED_LIST .
  TYPES:
    TTY_STORED_LIST TYPE TABLE OF TY_STORED_LIST .

  METHODS PREPARE_DATA_FOR_ALV_HIST
    IMPORTING
      !IV_LIST_TYPE TYPE CHAR1 .
  METHODS GET_DATA_FROM_HIST .
  CLASS-METHODS PRELIMINARY_CHECKS
    IMPORTING
      !IV_FIKRS TYPE FIKRS
      !IV_BEGFY TYPE GJAHR
      !IV_ENDFY TYPE GJAHR
    RETURNING
      VALUE(ES_RETURN) TYPE BAPIRETURN1 .
  METHODS INSERT_INTO_DATABASE .
  CLASS-METHODS GET_LIST_OF_STORED_DATES
    EXPORTING
      !ET_STORED_DATES TYPE TTY_STORED_LIST .
  METHODS GET_DATA .
  METHODS DISPLAY_MESSAGE
    IMPORTING
      !IV_REPID TYPE SY-REPID .
  METHODS DISPLAY_ALV
    IMPORTING
      !IV_REPID TYPE SY-REPID .
  METHODS SET_SELECTION_VALUES
    IMPORTING
      !IV_SELNAME TYPE RSSCR_NAME
      !IV_KIND TYPE RSSCR_KIND
      !IV_VALUE TYPE ANY OPTIONAL
      !IT_VALUE TYPE ANY TABLE OPTIONAL .
  METHODS PREPARE_DATA_FOR_ALV_LIST
    IMPORTING
      !IV_LIST_TYPE TYPE CHAR1 .