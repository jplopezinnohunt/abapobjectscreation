* ==== CLASS POOL YCL_FM_CONSTANT_DOLLAR_BL ====
CLASS-POOL .
*"* class pool for class YCL_FM_CONSTANT_DOLLAR_BL

*"* local type definitions
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CCDEF.

*"* class YCL_FM_CONSTANT_DOLLAR_BL definition
*"* public declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CU.
*"* protected declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CO.
*"* private declarations
  INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CI.
ENDCLASS. "YCL_FM_CONSTANT_DOLLAR_BL definition

*"* macro definitions
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CCMAC.
*"* local class implementation
INCLUDE YCL_FM_CONSTANT_DOLLAR_BL=====CCIMP.

CLASS YCL_FM_CONSTANT_DOLLAR_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_CONSTANT_DOLLAR_BL implementation


* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CI ----
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
    BEGIN OF TY_FMIT,
      FIKRS   TYPE FMIT-FIKRS,   "FM area
      FINCODE TYPE FMIT-RFONDS,  "Fund
      FISTL   TYPE FMIT-RFISTL,  "Fund center
      GJAHR   TYPE FMIT-RYEAR,   "Fiscal year
      "waers   TYPE waers,        "Currency
      WRTTP   TYPE FMIT-RWRTTP,  "Value type
      FIPEX   TYPE FMIT-RFIPEX,  "Commitment item
      TSLVT   TYPE FMIT-TSLVT,   "Carry forward
      TSL01   TYPE FMIT-TSL01,
      TSL02   TYPE FMIT-TSL02,
      TSL03   TYPE FMIT-TSL03,
      TSL04   TYPE FMIT-TSL04,
      TSL05   TYPE FMIT-TSL05,
      TSL06   TYPE FMIT-TSL06,
      TSL07   TYPE FMIT-TSL07,
      TSL08   TYPE FMIT-TSL08,
      TSL09   TYPE FMIT-TSL09,
      TSL10   TYPE FMIT-TSL10,
      TSL11   TYPE FMIT-TSL11,
      TSL12   TYPE FMIT-TSL12,
      TSL13   TYPE FMIT-TSL13,
      TSL14   TYPE FMIT-TSL14,
      TSL15   TYPE FMIT-TSL15,
      TSL16   TYPE FMIT-TSL16,
      HSLVT   TYPE FMIT-HSLVT,   "Carry forward
      HSL01   TYPE FMIT-HSL01,
      HSL02   TYPE FMIT-HSL02,
      HSL03   TYPE FMIT-HSL03,
      HSL04   TYPE FMIT-HSL04,
      HSL05   TYPE FMIT-HSL05,
      HSL06   TYPE FMIT-HSL06,
      HSL07   TYPE FMIT-HSL07,
      HSL08   TYPE FMIT-HSL08,
      HSL09   TYPE FMIT-HSL09,
      HSL10   TYPE FMIT-HSL10,
      HSL11   TYPE FMIT-HSL11,
      HSL12   TYPE FMIT-HSL12,
      HSL13   TYPE FMIT-HSL13,
      HSL14   TYPE FMIT-HSL14,
      HSL15   TYPE FMIT-HSL15,
      HSL16   TYPE FMIT-HSL16,
      RLDNR   TYPE FMIT-RLDNR,   "To avoid distinct with FOR ALL ENTRIES
      RRCTY   TYPE FMIT-RRCTY,   "To avoid distinct with FOR ALL ENTRIES
      RVERS   TYPE FMIT-RVERS,   "To avoid distinct with FOR ALL ENTRIES
      ROBJNR  TYPE FMIT-ROBJNR,  "To avoid distinct with FOR ALL ENTRIES
      COBJNR  TYPE FMIT-COBJNR,  "To avoid distinct with FOR ALL ENTRIES
      SOBJNR  TYPE FMIT-SOBJNR,  "To avoid distinct with FOR ALL ENTRIES
      RTCUR   TYPE FMIT-RTCUR,   "To avoid distinct with FOR ALL ENTRIES
      RPMAX   TYPE FMBDT-RPMAX,  "To avoid distinct with FOR ALL ENTRIES
    END OF TY_FMIT .
  TYPES:
    BEGIN OF TY_FMIFI,
      FIKRS   TYPE FMIFIIT-FIKRS,
      FINCODE TYPE FMIFIIT-FONDS,
      FISTL   TYPE FMIFIIT-FISTL,
      GJAHR   TYPE FMIFIIT-GJAHR,
      WRTTP   TYPE FMIFIIT-WRTTP,
      FIPEX   TYPE FMIFIIT-FIPEX,
      TRBTR   TYPE FMIFIIT-TRBTR,
      TWAER   TYPE FMIFIIT-TWAER,
      FKBTR   TYPE FMIFIIT-FKBTR,
      VRGNG   TYPE FMIFIIT-VRGNG,
      BLART   TYPE FMIFIHD-BLART,
      FMBELNR TYPE FMIFIIT-FMBELNR,  "To avoid distinct with FOR ALL ENTRIES
      FMBUZEI TYPE FMIFIIT-FMBUZEI,  "To avoid distinct with FOR ALL ENTRIES
      BTART   TYPE FMIFIIT-BTART,    "To avoid distinct with FOR ALL ENTRIES
      RLDNR   TYPE FMIFIIT-RLDNR,    "To avoid distinct with FOR ALL ENTRIES
      STUNR   TYPE FMIFIIT-STUNR,    "To avoid distinct with FOR ALL ENTRIES
    END OF TY_FMIFI .
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
      FIKRS                   TYPE FMIT-FIKRS,   "FM area
      FINCODE                 TYPE FMIT-RFONDS,  "Fund
      TYPE                    TYPE FMFINCODE-TYPE,
      DATAB                   TYPE FMFINCODE-DATAB,
      DATBIS                  TYPE FMFINCODE-DATBIS,
      BESCHR                  TYPE FMFINT-BESCHR,
      BEZEICH                 TYPE FMFINT-BEZEICH,
      BUDGET_UNORE            TYPE WERTV9,   "Budget in FM area currency (UNORE)
      EXPENSES_UNORE          TYPE WERTV9,   "Expenses in FM area currency (UNORE)
      EUR_NPC_EXP             TYPE WERTV9,   "EUR NPC expenses in EUR
      EUR_NPC_EXP_REA         TYPE WERTV9,   "EUR NPC expenses in EUR realized
      EUR_NPC_EXP_COM         TYPE WERTV9,   "EUR NPC expenses in EUR commiment
      EUR_NPC_EXP_UNORE       TYPE WERTV9,   "EUR NPC expenses in USD (UNORE)
      EUR_NPC_EXP_REA_UNORE   TYPE WERTV9,   "EUR NPC expenses in USD (UNORE) realized
      EUR_NPC_EXP_COM_UNORE   TYPE WERTV9,   "EUR NPC expenses in USD (UNORE) commitment
      EUR_NPC_EXP_CONSD       TYPE WERTV9,   "EUR NPC expenses in USD (constant $)
      EUR_NPC_EXP_REA_CONSD   TYPE WERTV9,   "EUR NPC expenses in USD (constant $) realized
      EUR_NPC_EXP_COM_CONSD   TYPE WERTV9,   "EUR NPC expenses in USD (constant $) commitment
      EUR_NPC_EXP_IMPACT      TYPE WERTV9,   "eur_npc_exp_unore - eur_npc_exp_consd
      EUR_NPC_EXP_REA_IMPACT  TYPE WERTV9,   "eur_npc_exp_rea_unore - eur_npc_exp_rea_consd
      EUR_NPC_EXP_COM_IMPACT  TYPE WERTV9,   "eur_npc_exp_com_unore - eur_npc_exp_com_consd
      PC_EXP_UNORE_IMPACT_REA TYPE WERTV9,   "PC expenses in USD (UNORE) realized - only impact with CI CDO, CDCE, CDSP
      PC_EXP_UNORE_IMPACT_COM TYPE WERTV9,   "PC expenses in USD (UNORE) commitment - only impact with CI CDO, CDCE, CDSP
      EXPENSES_CONSD          TYPE WERTV9,   "expenses_unore - eur_npc_exp_impact - pc_exp_unore_impact
      AVAILABLE               TYPE WERTV9,   "budget_unore - expenses_consd
      EUR_EXP_IMPACT          TYPE WERTV9,   "eur_npc_exp_impact + pc_exp_unore_impact
      COLFIELD                TYPE LVC_T_SCOL,  "Field color
    END OF TY_LIST .

  DATA MP_EUREXP TYPE XFELD .
  DATA MV_REPID TYPE SY-REPID .
  CONSTANTS C_EUR TYPE WAERS VALUE 'EUR' ##NO_TEXT.
  CONSTANTS C_USD TYPE WAERS VALUE 'USD' ##NO_TEXT.
  DATA MP_FILTER TYPE XFELD .
  DATA MP_PCT TYPE NUM2 .
  DATA MV_CONST_RATE TYPE TVRT_KKURS .
  DATA MV_FM_WAERS TYPE FM_WAERS .
  DATA MV_TR_WAERS TYPE WAERS .
  DATA:
    MT_FUND TYPE SORTED TABLE OF TY_FUND WITH UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMBDT TYPE SORTED TABLE OF TY_FMBDT WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMIT TYPE SORTED TABLE OF TY_FMIT WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMIFI TYPE SORTED TABLE OF TY_FMIFI WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_FMIOI TYPE SORTED TABLE OF TY_FMIOI WITH NON-UNIQUE KEY FIKRS FINCODE .
  DATA:
    MT_LIST TYPE TABLE OF TY_LIST .
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
    MT_VRGNG TYPE RANGE OF CO_VORGANG .

  METHODS DETERMINE_BUDGET_AMOUNT
    IMPORTING
      !IV_FIKRS   TYPE FIKRS
      !IV_FINCODE TYPE BP_GEBER
    EXPORTING
      !EV_AMOUNT  TYPE WERTV9 .
  METHODS DETERMINE_EXPENSES_AMOUNTS
    IMPORTING
      !IV_FIKRS               TYPE FIKRS
      !IV_FINCODE             TYPE BP_GEBER
    EXPORTING
      !EV_EXP_UNORE           TYPE WERTV9
      !EV_EUR_NPC_EXP_REA_EUR TYPE WERTV9
      !EV_EUR_NPC_EXP_COM_EUR TYPE WERTV9
      !EV_EUR_NPC_EXP_REA_USD TYPE WERTV9
      !EV_EUR_NPC_EXP_COM_USD TYPE WERTV9
      !EV_PC_IMPACT_USD_REA   TYPE WERTV9
      !EV_PC_IMPACT_USD_COM   TYPE WERTV9 .
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
  METHODS PREPARE_DATA .
  METHODS SET_COLUMNS .
  METHODS GET_EXPENSES_FROM_DB .
  METHODS GET_BUDGET_FROM_DB .
  METHODS INITIALIZE .
  METHODS GET_FUND_FROM_DB .
  METHODS SET_DISPLAY_SETTINGS .
  METHODS SET_FUNCTIONS .
  METHODS SET_LAYOUT .

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM001 ----
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

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM002 ----
  METHOD GET_DATA.

    "Get dates
    ME->INITIALIZE( ).
    "Get fund
    ME->GET_FUND_FROM_DB( ).
    CHECK MT_FUND IS NOT INITIAL.
    "Get budget
    ME->GET_BUDGET_FROM_DB( ).
    "Get expenses
    ME->GET_EXPENSES_FROM_DB( ).
    "Prepare data for list
    ME->PREPARE_DATA( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM003 ----
  METHOD GET_FUND_FROM_DB.

    SELECT A~FIKRS,
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
           WHERE A~FIKRS = @MP_FIKRS
           AND   A~FINCODE IN @MR_FUND
           AND   A~DATAB <= @MV_ENDDA
           AND   A~DATBIS >= @MV_BEGDA
           AND   A~TYPE IN @MR_TYPE
           INTO TABLE @MT_FUND.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM004 ----
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

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM005 ----
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
           H~BLART,
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

*    SELECT a~fikrs AS fikrs,
*           a~rfonds AS fincode,
*           a~rfistl AS fistl,
*           a~ryear AS gjahr,
*           a~rwrttp AS wrttp,
*           a~rfipex AS fipex,
*           a~tslvt,
*           a~tsl01,
*           a~tsl02,
*           a~tsl03,
*           a~tsl04,
*           a~tsl05,
*           a~tsl06,
*           a~tsl07,
*           a~tsl08,
*           a~tsl09,
*           a~tsl10,
*           a~tsl11,
*           a~tsl12,
*           a~tsl13,
*           a~tsl14,
*           a~tsl15,
*           a~tsl16,
*           a~hslvt,
*           a~hsl01,
*           a~hsl02,
*           a~hsl03,
*           a~hsl04,
*           a~hsl05,
*           a~hsl06,
*           a~hsl07,
*           a~hsl08,
*           a~hsl09,
*           a~hsl10,
*           a~hsl11,
*           a~hsl12,
*           a~hsl13,
*           a~hsl14,
*           a~hsl15,
*           a~hsl16,
*           a~rldnr,
*           a~rrcty,
*           a~rvers,
*           a~robjnr,
*           a~cobjnr,
*           a~sobjnr,
*           a~rtcur,
*           a~rpmax
*           FROM fmit AS a
*           FOR ALL ENTRIES IN @mt_fund
*           WHERE a~fikrs = @mt_fund-fikrs
*           AND   a~rfonds = @mt_fund-fincode
*           AND   a~rldnr = '9A'
*           AND   a~rvers = '000'
*           AND   a~ryear BETWEEN @mp_begfy AND @mp_endfy
*           AND   a~rstats = @abap_false
*           AND   a~rfistl IN @mr_fictr
*           AND   a~rfipex IN @lr_fipex
*           AND   a~rwrttp IN @lr_wrttp
*          INTO TABLE @mt_fmit.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM006 ----
  METHOD SET_COLUMNS.

    DATA LO_COLUMNS TYPE REF TO CL_SALV_COLUMNS_TABLE.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.

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
        LO_COLUMN->SET_KEY( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BEZEICH' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BUDGET_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |Budget (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EXPENSES_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |Expenses (UNORE) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC expenses in { MV_TR_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_REA' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC incurred expend. in { MV_TR_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_COM' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC commitments in { MV_TR_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC expenses in { MV_FM_WAERS } (UNORE)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_REA_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC incurred expend. in { MV_FM_WAERS } (UNORE)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_COM_UNORE' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC commitments in { MV_FM_WAERS } (UNORE)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_CONSD' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC expenses in { MV_FM_WAERS } (Const rate)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_REA_CONSD' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC incurred expend. in { MV_FM_WAERS } (Const rate)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_COM_CONSD' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC commitments in { MV_FM_WAERS } (Const rate)| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC expenses impact in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_REA_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC incurred expend. impact in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_NPC_EXP_COM_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( |{ MV_TR_WAERS } NPC commitments impact in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_EXP_UNORE_IMPACT_REA' ).
        LO_COLUMN->SET_LONG_TEXT( |PC expenses impact in { MV_FM_WAERS } - incurred| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'PC_EXP_UNORE_IMPACT_COM' ).
        LO_COLUMN->SET_LONG_TEXT( |PC expenses impact in { MV_FM_WAERS } - commitment| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EXPENSES_CONSD' ).
        LO_COLUMN->SET_LONG_TEXT( |Expenses (budget rate) in { MV_FM_WAERS }| ).
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
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'EUR_EXP_IMPACT' ).
        LO_COLUMN->SET_LONG_TEXT( |Impact (budget rate) in { MV_FM_WAERS }| ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM007 ----
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

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM008 ----
  METHOD INITIALIZE.

    "Get begin and end dates from selection period
    MV_BEGDA = |{ MP_BEGFY }0101|.
    MV_ENDDA = |{ MP_ENDFY }1231|.

    "Set transaction currency and FM area currency
    MV_TR_WAERS = C_EUR.
    MV_FM_WAERS = GET_FM_AREA_CURRENCY( MP_FIKRS ).

    "Get constant rate at first date of biennium
    MV_CONST_RATE = GET_CONSTANT_RATE( IV_DATE = MV_BEGDA ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM009 ----
  METHOD GET_FM_AREA_CURRENCY.

    SELECT SINGLE WAERS INTO @RV_WAERS FROM FM01 WHERE FIKRS = @IV_FIKRS.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00A ----
  METHOD GET_CONSTANT_RATE.

    CLEAR RV_RATE.

    "Get constant rate for USD to EUR
    SELECT SINGLE KWERT INTO @DATA(LV_KWERT) FROM T511K WHERE MOLGA = 'UN'
                                                        AND   KONST = 'ZCUSD'
                                                        AND   ENDDA >= @IV_DATE
                                                        AND   BEGDA <= @IV_DATE.
    IF SY-SUBRC = 0.
      RV_RATE = LV_KWERT / 100000.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00B ----
  METHOD PREPARE_DATA.

    DATA LS_LIST TYPE TY_LIST.
    DATA LS_COLOR TYPE LVC_S_SCOL.
    DATA LV_MINIMUM_BUDGET TYPE WERTV9.

    "Fill comitment item for personnel cost
    MT_FIPEX_PC = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = '10''' )
                           ( SIGN = 'I' OPTION = 'EQ' LOW = '11' )
                           ( SIGN = 'I' OPTION = 'EQ' LOW = '13' ) ).
    "Fill commitment item for personnel cost impact
    MT_FIPEX_PC_IMPACT = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDO' )
                                  ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDCE' )
                                  ( SIGN = 'I' OPTION = 'EQ' LOW = 'CDSP' ) ).

    "Business transaction HR
    MT_VRGNG = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRM1' )   "PBC pre-commitment
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRM2' )   "PBC commitment
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'HRP1' ) )."Payroll posting

    LOOP AT MT_FUND INTO DATA(LS_FUND).

      CLEAR LS_LIST.
      MOVE-CORRESPONDING LS_FUND TO LS_LIST.

      "Determine budget amount
      ME->DETERMINE_BUDGET_AMOUNT( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                             IV_FINCODE = LS_FUND-FINCODE
                                   IMPORTING EV_AMOUNT = LS_LIST-BUDGET_UNORE ).
      "Determine expenses amount
      ME->DETERMINE_EXPENSES_AMOUNTS( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                                IV_FINCODE = LS_FUND-FINCODE
                                      IMPORTING EV_EXP_UNORE = LS_LIST-EXPENSES_UNORE
                                                EV_EUR_NPC_EXP_REA_EUR = LS_LIST-EUR_NPC_EXP_REA
                                                EV_EUR_NPC_EXP_COM_EUR = LS_LIST-EUR_NPC_EXP_COM
                                                EV_EUR_NPC_EXP_REA_USD = LS_LIST-EUR_NPC_EXP_REA_UNORE
                                                EV_EUR_NPC_EXP_COM_USD = LS_LIST-EUR_NPC_EXP_COM_UNORE
                                                EV_PC_IMPACT_USD_REA = LS_LIST-PC_EXP_UNORE_IMPACT_REA
                                                EV_PC_IMPACT_USD_COM = LS_LIST-PC_EXP_UNORE_IMPACT_COM ).

      LS_LIST-EUR_NPC_EXP = LS_LIST-EUR_NPC_EXP_REA + LS_LIST-EUR_NPC_EXP_COM.
      LS_LIST-EUR_NPC_EXP_UNORE = LS_LIST-EUR_NPC_EXP_REA_UNORE + LS_LIST-EUR_NPC_EXP_COM_UNORE.

      "Don't keep funds without EUR expenses if asked
      IF MP_EUREXP = ABAP_TRUE.
        CHECK LS_LIST-EUR_NPC_EXP <> 0 OR LS_LIST-PC_EXP_UNORE_IMPACT_REA <> 0 OR LS_LIST-PC_EXP_UNORE_IMPACT_COM <> 0.
      ENDIF.

      "Set calculated amounts
      "ls_list-eur_npc_exp_consd = ls_list-eur_npc_exp / mv_const_rate.
      LS_LIST-EUR_NPC_EXP_REA_CONSD = LS_LIST-EUR_NPC_EXP_REA / MV_CONST_RATE.
      LS_LIST-EUR_NPC_EXP_COM_CONSD = LS_LIST-EUR_NPC_EXP_COM / MV_CONST_RATE.
      LS_LIST-EUR_NPC_EXP_CONSD = LS_LIST-EUR_NPC_EXP_REA_CONSD + LS_LIST-EUR_NPC_EXP_COM_CONSD.
      LS_LIST-EUR_NPC_EXP_IMPACT =  LS_LIST-EUR_NPC_EXP_CONSD - LS_LIST-EUR_NPC_EXP_UNORE.
      LS_LIST-EUR_NPC_EXP_REA_IMPACT =  LS_LIST-EUR_NPC_EXP_REA_CONSD - LS_LIST-EUR_NPC_EXP_REA_UNORE.
      LS_LIST-EUR_NPC_EXP_COM_IMPACT =  LS_LIST-EUR_NPC_EXP_COM_CONSD - LS_LIST-EUR_NPC_EXP_COM_UNORE.
      LS_LIST-EXPENSES_CONSD = LS_LIST-EXPENSES_UNORE + LS_LIST-EUR_NPC_EXP_IMPACT + LS_LIST-PC_EXP_UNORE_IMPACT_REA + LS_LIST-PC_EXP_UNORE_IMPACT_COM.
      LS_LIST-AVAILABLE = LS_LIST-BUDGET_UNORE - LS_LIST-EXPENSES_CONSD.
      LS_LIST-EUR_EXP_IMPACT = LS_LIST-EUR_NPC_EXP_IMPACT + LS_LIST-PC_EXP_UNORE_IMPACT_REA + LS_LIST-PC_EXP_UNORE_IMPACT_COM.

      "Set to list
      IF LS_LIST-BUDGET_UNORE IS NOT INITIAL OR LS_LIST-EXPENSES_UNORE IS NOT INITIAL.
        "Calculate minimum budget to check from percentage indicated in selection screen
        LV_MINIMUM_BUDGET = LS_LIST-BUDGET_UNORE * MP_PCT / 100.
        IF MP_FILTER = ABAP_TRUE.
          CHECK LS_LIST-AVAILABLE <= LV_MINIMUM_BUDGET.
        ENDIF.
        CLEAR: LS_LIST-COLFIELD, LS_COLOR.
        IF LS_LIST-AVAILABLE <= LV_MINIMUM_BUDGET.
          LS_COLOR-FNAME = 'AVAILABLE'.
          LS_COLOR-COLOR-COL = COL_NEGATIVE.
          LS_COLOR-COLOR-INT = 1.
          APPEND LS_COLOR TO LS_LIST-COLFIELD.
        ENDIF.
        APPEND LS_LIST TO MT_LIST.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00C ----
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

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00D ----
  METHOD DETERMINE_EXPENSES_AMOUNTS.

    DATA LV_FIELDNAME TYPE FIELDNAME.
    DATA LV_NUM(2) TYPE N.
    DATA LV_HSL_AMOUNT TYPE WERTV9.
    DATA LV_TSL_AMOUNT TYPE WERTV9.
    FIELD-SYMBOLS <FIELD> TYPE ANY.

    CLEAR: EV_EXP_UNORE,
           EV_EUR_NPC_EXP_REA_EUR, EV_EUR_NPC_EXP_COM_EUR,
           EV_EUR_NPC_EXP_REA_USD, EV_EUR_NPC_EXP_COM_USD,
           EV_PC_IMPACT_USD_REA, EV_PC_IMPACT_USD_COM.

    LOOP AT MT_FMIFI INTO DATA(LS_FMIFI) WHERE FIKRS = IV_FIKRS
                                         AND   FINCODE = IV_FINCODE.
      "inverse sign
      LS_FMIFI-TRBTR = LS_FMIFI-TRBTR * -1.
      LS_FMIFI-FKBTR = LS_FMIFI-FKBTR * -1.
      "Fill expenses amounts in USD (UNORE): all commitment items except CDO, CDCE, CDSP
      IF LS_FMIFI-FIPEX NOT IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIFI-FKBTR TO EV_EXP_UNORE.
      ENDIF.

      "Fill EUR expenses amounts in EUR and USD (UNORE): all commitment items except
      "    - 10', 11, 13 with document type PP
      "    - CDO, CDCE, CDSP
      IF LS_FMIFI-TWAER = C_EUR.
        IF NOT ( LS_FMIFI-FIPEX IN MT_FIPEX_PC_IMPACT OR ( LS_FMIFI-FIPEX IN MT_FIPEX_PC AND LS_FMIFI-VRGNG IN MT_VRGNG ) ).
          ADD LS_FMIFI-TRBTR TO EV_EUR_NPC_EXP_REA_EUR.
          ADD LS_FMIFI-FKBTR TO EV_EUR_NPC_EXP_REA_USD.
        ENDIF.
      ENDIF.

      "Fill PC expenses impact in constant dollar
      IF LS_FMIFI-FIPEX IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIFI-FKBTR TO EV_PC_IMPACT_USD_REA.
      ENDIF.

    ENDLOOP.

    LOOP AT MT_FMIOI INTO DATA(LS_FMIOI) WHERE FIKRS = IV_FIKRS
                                         AND   FINCODE = IV_FINCODE.

      "inverse sign
      LS_FMIOI-TRBTR = LS_FMIOI-TRBTR * -1.
      LS_FMIOI-FKBTR = LS_FMIOI-FKBTR * -1.

      "Fill expenses amounts in USD (UNORE): all commitment items except CDO, CDCE, CDSP
      IF LS_FMIOI-FIPEX NOT IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIOI-FKBTR TO EV_EXP_UNORE.
      ENDIF.

      "Fill EUR expenses amounts in EUR and USD (UNORE): all commitment items except
      "    - 10', 11, 13 with business transaction HRM1, HRM2, HRP1
      "    - CDO, CDCE, CDSP
      IF LS_FMIOI-TWAER = C_EUR.
        IF NOT ( LS_FMIOI-FIPEX IN MT_FIPEX_PC_IMPACT OR ( LS_FMIOI-FIPEX IN MT_FIPEX_PC AND LS_FMIOI-VRGNG IN MT_VRGNG ) ).
          ADD LS_FMIOI-TRBTR TO EV_EUR_NPC_EXP_COM_EUR.
          ADD LS_FMIOI-FKBTR TO EV_EUR_NPC_EXP_COM_USD.
        ENDIF.
      ENDIF.

      "Fill PC expenses impact in constant dollar
      IF LS_FMIOI-FIPEX IN MT_FIPEX_PC_IMPACT.
        ADD LS_FMIOI-FKBTR TO EV_PC_IMPACT_USD_COM.
      ENDIF.

    ENDLOOP.

*    LOOP AT mt_fmit INTO DATA(ls_fmit) WHERE fikrs = iv_fikrs
*                                       AND   fincode = iv_fincode.
*      "Extract amount in local currency and amount in transaction currency
*      CLEAR: lv_hsl_amount, lv_tsl_amount.
*      lv_hsl_amount = lv_hsl_amount - ls_fmit-hslvt.   "subtract to inverse sign
*      lv_tsl_amount = lv_tsl_amount - ls_fmit-tslvt.   "subtract to inverse sign
*      CLEAR lv_num.
*      DO 16 TIMES.
*        ADD 1 TO lv_num.
*        lv_fieldname = |LS_FMIT-HSL{ lv_num }|.
*        ASSIGN (lv_fieldname) TO <field>.
*        IF <field> IS ASSIGNED.
*          lv_hsl_amount = lv_hsl_amount - <field>.
*        ENDIF.
*        lv_fieldname = |LS_FMIT-TSL{ lv_num }|.
*        ASSIGN (lv_fieldname) TO <field>.
*        IF <field> IS ASSIGNED.
*          lv_tsl_amount = lv_tsl_amount - <field>.
*        ENDIF.
*      ENDDO.
*
*      "Fill expenses amounts in USD (UNORE): all commitment items except CDO, CDCE, CDSP
*      IF ls_fmit-fipex NOT IN mt_fipex_pc_impact.
*        ADD lv_hsl_amount TO ev_exp_unore.
*      ENDIF.
*
*      "Fill EUR expenses amounts in EUR and USD (UNORE): all commitment items except 10', 11, 13, CDO, CDCE, CDSP
*      IF ls_fmit-rtcur = c_eur AND ls_fmit-fipex NOT IN mt_fipex_pc.
*        ADD lv_tsl_amount TO ev_eur_npc_exp_eur.
*        ADD lv_hsl_amount TO ev_eur_npc_exp_usd.
*      ENDIF.
*
*      "Fill PC expenses impact in constant dollar
*      IF ls_fmit-fipex IN mt_fipex_pc_impact.
*        ADD lv_hsl_amount TO ev_pc_impact_usd.
*      ENDIF.
*
*    ENDLOOP.

    IF EV_EUR_NPC_EXP_REA_EUR = 0.
      CLEAR EV_EUR_NPC_EXP_REA_USD.
    ENDIF.

    IF EV_EUR_NPC_EXP_COM_EUR = 0.
      CLEAR EV_EUR_NPC_EXP_COM_USD.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00E ----
  METHOD DISPLAY_ALV.

    MV_REPID = IV_REPID.

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

    "ALV display settings
    ME->SET_DISPLAY_SETTINGS( ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).


  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00F ----
  METHOD SET_FUNCTIONS.

    DATA LO_FUNCTIONS TYPE REF TO CL_SALV_FUNCTIONS_LIST.

    LO_FUNCTIONS = MO_SALV_TABLE->GET_FUNCTIONS( ).
    LO_FUNCTIONS->SET_ALL( ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00G ----
  METHOD SET_LAYOUT.

    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.
    DATA LO_LAYOUT TYPE REF TO CL_SALV_LAYOUT.

    LO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = MV_REPID.
    LO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    LO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).
    "lo_layout->set_default( abap_true ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CM00H ----
  METHOD SET_DISPLAY_SETTINGS.

    DATA LO_DISPLAY_SETTINGS TYPE REF TO CL_SALV_DISPLAY_SETTINGS.

    LO_DISPLAY_SETTINGS = MO_SALV_TABLE->GET_DISPLAY_SETTINGS( ).
    LO_DISPLAY_SETTINGS->SET_STRIPED_PATTERN( ABAP_TRUE ).

  ENDMETHOD.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CO ----
PROTECTED SECTION.

* ---- YCL_FM_CONSTANT_DOLLAR_BL=====CU ----
CLASS YCL_FM_CONSTANT_DOLLAR_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  METHODS DISPLAY_ALV
    IMPORTING
      !IV_REPID TYPE SY-REPID .
  METHODS GET_DATA .
  CLASS-METHODS PRELIMINARY_CHECKS
    IMPORTING
      !IV_FIKRS TYPE FIKRS
      !IV_BEGFY TYPE GJAHR
      !IV_ENDFY TYPE GJAHR
    RETURNING
      VALUE(ES_RETURN) TYPE BAPIRETURN1 .
  METHODS SET_SELECTION_VALUES
    IMPORTING
      !IV_SELNAME TYPE RSSCR_NAME
      !IV_KIND TYPE RSSCR_KIND
      !IV_VALUE TYPE ANY OPTIONAL
      !IT_VALUE TYPE ANY TABLE OPTIONAL .