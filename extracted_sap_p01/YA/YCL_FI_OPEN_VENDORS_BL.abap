* ==== CLASS POOL YCL_FI_OPEN_VENDORS_BL ====
CLASS-POOL .
*"* class pool for class YCL_FI_OPEN_VENDORS_BL

*"* local type definitions
INCLUDE YCL_FI_OPEN_VENDORS_BL========CCDEF.

*"* class YCL_FI_OPEN_VENDORS_BL definition
*"* public declarations
  INCLUDE YCL_FI_OPEN_VENDORS_BL========CU.
*"* protected declarations
  INCLUDE YCL_FI_OPEN_VENDORS_BL========CO.
*"* private declarations
  INCLUDE YCL_FI_OPEN_VENDORS_BL========CI.
ENDCLASS. "YCL_FI_OPEN_VENDORS_BL definition

*"* macro definitions
INCLUDE YCL_FI_OPEN_VENDORS_BL========CCMAC.
*"* local class implementation
INCLUDE YCL_FI_OPEN_VENDORS_BL========CCIMP.

CLASS YCL_FI_OPEN_VENDORS_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_OPEN_VENDORS_BL implementation


* ---- YCL_FI_OPEN_VENDORS_BL========CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_BSIK,
      BUKRS      TYPE BSIK-BUKRS,
      LIFNR      TYPE BSIK-LIFNR,
      UMSKS      TYPE BSIK-UMSKS,
      AUGDT      TYPE BSIK-AUGDT,
      AUGBL      TYPE BSIK-AUGBL,
      ZUONR      TYPE BSIK-ZUONR,
      NAME1      TYPE LFA1-NAME1,
      NAME2      TYPE LFA1-NAME2,
      NAME3      TYPE LFA1-NAME3,
      NAME4      TYPE LFA1-NAME4,
      UMSKZ      TYPE BSIK-UMSKZ,
      GJAHR      TYPE BSIK-GJAHR,
      BELNR      TYPE BSIK-BELNR,
      BUZEI      TYPE BSIK-BUZEI,
      BUDAT      TYPE BSIK-BUDAT,
      BLDAT      TYPE BSIK-BLDAT,
      CPUDT      TYPE BSIK-CPUDT,
      XBLNR      TYPE BSIK-XBLNR,
      BLART      TYPE BSIK-BLART,
      SHKZG      TYPE BSIK-SHKZG,
      GSBER      TYPE BSIK-GSBER,
      DMBTR      TYPE BSIK-DMBTR,
      DWAER      TYPE T001-WAERS,
      WRBTR      TYPE BSIK-WRBTR,
      WWAER      TYPE BSIK-WAERS,
      SGTXT      TYPE BSIK-SGTXT,
      HKONT      TYPE BSIK-HKONT,
      HKONT_TEXT TYPE SKAT-TXT50,
      ZFBDT      TYPE BSIK-ZFBDT,
      XREF1      TYPE BSIK-XREF1,
      XREF2      TYPE BSIK-XREF2,
      ZBD1T      TYPE BSIK-ZBD1T,
      ZBD2T      TYPE BSIK-ZBD2T,
      ZBD3T      TYPE BSIK-ZBD3T,
      ZLSCH      TYPE BSIK-ZLSCH,
      ZLSCH_TEXT TYPE T042Z-TEXT1,
      REBZG      TYPE BSIK-REBZG,
      REBZT      TYPE BSIK-REBZT,
      USNAM      TYPE BKPF-USNAM,
      BEGRU      TYPE LFB1-BEGRU,
      LAND1      TYPE T001-LAND1,
      BDIFF      TYPE BSIK-BDIFF,
      BDIF2      TYPE BSIK-BDIF2,
      BDIF3      TYPE BSIK-BDIF3,
      BSTAT      TYPE BSIK-BSTAT,
      MWSKZ      TYPE BSIK-MWSKZ,
      MCTXT      TYPE FMFCTRT-MCTXT,
    END OF TY_BSIK .
  TYPES:
    BEGIN OF TY_T003,
      BLART            TYPE T003-BLART,
      XMREF            TYPE T003-XMREF,
      YYBLART_GRP      TYPE T003-YYBLART_GRP,
      YYBLART_GRP_TEXT TYPE TEXT40,
      LTEXT            TYPE T003T-LTEXT,
      YYNAME           TYPE T003T-YYNAME,
    END OF TY_T003 .
  TYPES:
    BEGIN OF TY_T074,
      UMSKZ TYPE T074T-SHBKZ,
      LTEXT TYPE T074T-LTEXT,
    END OF TY_T074 .
  TYPES:
    BEGIN OF TY_BSEG,
      BUKRS  TYPE BSEG-BUKRS,
      BELNR  TYPE BSEG-BELNR,
      GJAHR  TYPE BSEG-GJAHR,
      BUZEI  TYPE BSEG-BUZEI,
      SHKZG  TYPE BSEG-SHKZG,
      FISTL  TYPE BSEG-FISTL,
      GEBER  TYPE BSEG-GEBER,
      DATBIS TYPE FMFINCODE-DATBIS,
      XOPVW  TYPE BSEG-XOPVW,
    END OF TY_BSEG .

  DATA MT_USER_ASSIGNMENT TYPE YCL_HR_USER_ASSIGNMENT=>TTY_USER_ASSIGNMENT .
  DATA MV_OLDEST_USER_BEGDA TYPE BEGDA .
  DATA MS_T001 TYPE T001 .
  DATA MV_DO_TOTAL TYPE XFELD .
  DATA MV_AMOUNT_FILTER TYPE CHAR1 .
  DATA MV_REPID TYPE SY-REPID .
  DATA:
    MT_BSIK TYPE TABLE OF TY_BSIK .
  DATA:
    MT_T003 TYPE SORTED TABLE OF TY_T003 WITH UNIQUE KEY BLART .
  DATA:
    MT_T074 TYPE SORTED TABLE OF TY_T074 WITH UNIQUE KEY UMSKZ .
  DATA:
    MT_BSEG TYPE SORTED TABLE OF TY_BSEG WITH UNIQUE KEY BUKRS BELNR GJAHR BUZEI .
  DATA MV_DATE_REF TYPE DATUM .
  DATA MP_BUKRS TYPE BUKRS .
  DATA:
    MR_LIFNR TYPE RANGE OF LIFNR .
  DATA MO_DISPLAY_SETTINGS TYPE REF TO CL_SALV_DISPLAY_SETTINGS .
  DATA MO_SALV_TABLE TYPE REF TO CL_SALV_TABLE .
  DATA MO_LAYOUT TYPE REF TO CL_SALV_LAYOUT .

  METHODS PREPARE_FOR_LOCATION_SECTOR .
  METHODS SET_TOTALS .
  METHODS SET_COLUMNS .
  METHODS GET_PAYMENT_DATE
    IMPORTING
      !IS_BSIK TYPE TY_BSIK
    RETURNING
      VALUE(RV_PAYMENT_DATE) TYPE DATUM .
  METHODS PREPARE_DATA .
  METHODS GET_CLOPE
    IMPORTING
      !IS_BSIK TYPE TY_BSIK
    EXPORTING
      !EV_CLOPE TYPE ICO_AUGP
      !EV_ISTAT TYPE YE_FI_ITEM_STATUS .
  METHODS READ_DATA_FROM_DATABASE .
  METHODS GET_AGING
    IMPORTING
      !IV_PAYMENT_DATE TYPE DATUM
      !IV_REFERENCE_DATE TYPE DATUM
    EXPORTING
      !EV_AGING TYPE YE_CA_AGING
      !EV_NBMONTH TYPE YE_NBMONTH
      !ES_CELL_COLOR TYPE LVC_S_SCOL .
  METHODS HANDLE_LINK_CLICK
    FOR EVENT LINK_CLICK OF CL_SALV_EVENTS_TABLE
    IMPORTING
      !ROW
      !COLUMN .

* ---- YCL_FI_OPEN_VENDORS_BL========CM001 ----
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

* ---- YCL_FI_OPEN_VENDORS_BL========CM002 ----
  METHOD GET_DATA.

    MV_DATE_REF = IV_DATE.
    MV_AMOUNT_FILTER = IV_AMOUNT_FILTER.
    MV_DO_TOTAL = IV_DO_TOTAL.
    "Read data from database
    ME->READ_DATA_FROM_DATABASE( ).
    "Prepare data for list
    ME->PREPARE_DATA( ).

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM003 ----
  METHOD READ_DATA_FROM_DATABASE.

    TYPES: BEGIN OF LTY_DOC,
             BUKRS TYPE BSEG-BUKRS,
             BELNR TYPE BSEG-BELNR,
             GJAHR TYPE BSEG-GJAHR,
           END OF LTY_DOC.

    DATA LT_DOC TYPE TABLE OF LTY_DOC.
    DATA LS_DOC TYPE LTY_DOC.
    DATA LT_BLART TYPE RANGE OF BLART.

    LT_BLART = VALUE #( ( SIGN = 'E' OPTION = 'EQ' LOW = 'MF' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'MA' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'PP' )
                        ( SIGN = 'E' OPTION = 'EQ' LOW = 'AP' ) ).

    SELECT I~BUKRS,
           I~LIFNR,
           I~UMSKS,
           I~AUGDT,
           I~AUGBL,
           I~ZUONR,
           L~NAME1,
           L~NAME2,
           L~NAME3,
           L~NAME4,
           I~UMSKZ,
           I~GJAHR,
           I~BELNR,
           I~BUZEI,
           I~BUDAT,
           I~BLDAT,
           I~CPUDT,
           I~XBLNR,
           I~BLART,
           I~SHKZG,
           I~GSBER,
           I~DMBTR,
           B~WAERS AS DWAER,
           I~WRBTR,
           I~WAERS AS WWAER,
           I~SGTXT,
           I~HKONT,
           A~TXT50 AS HKONT_TEXT,
           I~ZFBDT,
           I~XREF1,
           I~XREF2,
           I~ZBD1T,
           I~ZBD2T,
           I~ZBD3T,
           I~ZLSCH,
           P~TEXT1 AS ZLSCH_TEXT,
           I~REBZG,
           I~REBZT,
           F~USNAM,
           C~BEGRU,
           B~LAND1,
           I~BDIFF,
           I~BDIF2,
           I~BDIF3,
           I~BSTAT,
           I~MWSKZ,
           M~MCTXT
           FROM BSIK AS I
           LEFT OUTER JOIN T001 AS B ON B~BUKRS = I~BUKRS
           LEFT OUTER JOIN LFA1 AS L ON L~LIFNR = I~LIFNR
           LEFT OUTER JOIN LFB1 AS C ON  C~LIFNR = I~LIFNR
                                     AND C~BUKRS = I~BUKRS
           LEFT OUTER JOIN BKPF AS F ON  F~BUKRS = I~BUKRS
                                     AND F~BELNR = I~BELNR
                                     AND F~GJAHR = I~GJAHR
           LEFT OUTER JOIN T042Z AS P ON  P~LAND1 = B~LAND1
                                      AND P~ZLSCH = I~ZLSCH
           LEFT OUTER JOIN SKAT AS A ON  A~SPRAS = @SY-LANGU
                                     AND A~KTOPL = 'UNES'
                                     AND A~SAKNR = I~HKONT
           LEFT OUTER JOIN FMFCTRT AS M ON  M~SPRAS = @SY-LANGU
                                        AND M~FIKRS = B~FIKRS
                                        AND M~FICTR = I~XREF1
                                        AND M~DATBIS >= I~CPUDT
                                        AND M~DATAB <= I~CPUDT
           WHERE I~BUKRS = @MP_BUKRS
           AND   I~LIFNR IN @MR_LIFNR
           AND   I~BLART IN @LT_BLART
           AND   I~BUDAT <= @MV_DATE_REF
           INTO TABLE @MT_BSIK.

    "Check authority access
    CLEAR MV_NO_AUTH.
    LOOP AT MT_BSIK INTO DATA(LS_BSIK) WHERE BEGRU IS NOT INITIAL.
      AUTHORITY-CHECK OBJECT 'F_BKPF_BEK'
               ID 'BRGRU' FIELD LS_BSIK-BEGRU
               ID 'ACTVT' FIELD '03'.
      IF SY-SUBRC <> 0.
        ADD 1 TO MV_NO_AUTH.
        DELETE MT_BSIK.
        CONTINUE.
      ELSE.
        AUTHORITY-CHECK OBJECT 'F_LFA1_BEK'
                    ID 'BRGRU' FIELD LS_BSIK-BEGRU
                    ID 'ACTVT' FIELD '03'.
        IF SY-SUBRC <> 0.
          ADD 1 TO MV_NO_AUTH.
          DELETE MT_BSIK.
          CONTINUE.
        ENDIF.
      ENDIF.
      MOVE-CORRESPONDING LS_BSIK TO LS_DOC.
      APPEND LS_DOC TO LT_DOC.
    ENDLOOP.

    CHECK LT_DOC IS NOT INITIAL.

    SORT LT_DOC.
    DELETE ADJACENT DUPLICATES FROM LT_DOC.

    "Get BSEG lines for accounting documents to get fund / fund center
    SELECT S~BUKRS,
           S~BELNR,
           S~GJAHR,
           S~BUZEI,
           S~SHKZG,
           S~FISTL,
           S~GEBER,
           F~DATBIS,
           S~XOPVW
           FROM BSEG AS S
           LEFT OUTER JOIN BKPF AS K ON  K~BUKRS = S~BUKRS
                                     AND K~BELNR = S~BELNR
                                     AND K~GJAHR = S~GJAHR
           LEFT OUTER JOIN FMFINCODE AS F ON  F~FIKRS = K~FIKRS
                                          AND F~FINCODE = S~GEBER
           FOR ALL ENTRIES IN @LT_DOC
           WHERE S~BUKRS = @LT_DOC-BUKRS
           AND   S~BELNR = @LT_DOC-BELNR
           AND   S~GJAHR = @LT_DOC-GJAHR
           INTO TABLE @MT_BSEG.

    "Get data for Document type (BLART)
    SELECT A~BLART,
           A~XMREF,
           A~YYBLART_GRP,
           D~DDTEXT AS YYBLART_GRP_TEXT,
           T~LTEXT,
           T~YYNAME
           FROM T003 AS A
           LEFT OUTER JOIN T003T AS T ON  T~SPRAS = @SY-LANGU
                                      AND T~BLART = A~BLART
           LEFT OUTER JOIN DD07V AS D ON  D~DOMNAME = 'YD_FI_DOC_TYPE_GROUP'
                                      AND D~DDLANGUAGE = @SY-LANGU
                                      AND D~DOMVALUE_L = A~YYBLART_GRP
           WHERE A~BLART IN @LT_BLART
           INTO TABLE @MT_T003.

    "Get data for special G/L indicator
    SELECT SHBKZ AS UMSKZ, LTEXT FROM T074T WHERE SPRAS = @SY-LANGU
                                            AND   KOART = 'K'   "Vendor
                                 INTO TABLE @MT_T074.

    "Get T001
    SELECT SINGLE * FROM T001 WHERE BUKRS = @MP_BUKRS INTO @MS_T001.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM004 ----
  METHOD PREPARE_DATA.

    TYPES: BEGIN OF LTY_WRBTR,
             WWAER TYPE WAERS,
             WRBTR TYPE WERTV12,
           END OF LTY_WRBTR.

    DATA LS_LIST TYPE TY_LIST.
    DATA LS_CELL_COLOR TYPE LVC_S_SCOL.
    DATA LT_AGING_TEXT TYPE YCL_CA_UTILITIES=>TTY_DOMAIN_VALUE.
    DATA LT_LIST TYPE TTY_LIST.
    DATA LS_WRBTR TYPE LTY_WRBTR.
    DATA LT_WRBTR TYPE SORTED TABLE OF LTY_WRBTR WITH UNIQUE KEY WWAER.
    DATA LV_DMBTR TYPE DMBTRV.
    DATA LO_ORG_ASSIGNMENT TYPE REF TO YCL_HR_ORG_ASSIGNMENT.
    DATA LS_ORG_ASSIGN TYPE YCL_HR_ORG_ASSIGNMENT=>TY_ORG_ASSIGNMENT.
    DATA LO_LOCATION_DETERMINATION TYPE REF TO YCL_FI_LOCATION_DETERMINATION.

    "Get aging text
    LT_AGING_TEXT = YCL_CA_UTILITIES=>GET_DOMAIN_VALUES( 'YD_CA_AGING' ).

    "Get user's assignment
    ME->PREPARE_FOR_LOCATION_SECTOR( ).

    "Get Org structure
    LO_ORG_ASSIGNMENT = NEW YCL_HR_ORG_ASSIGNMENT( IV_AUTHORITY_CHECK = ABAP_FALSE
                                                   IV_BEGDA = MV_OLDEST_USER_BEGDA
                                                   IV_ENDDA = '99991231' ).

    "Get assignment from fund center
    LO_LOCATION_DETERMINATION = NEW YCL_FI_LOCATION_DETERMINATION( ).

    SORT MT_BSIK BY BUKRS LIFNR ZUONR BELNR.

    LOOP AT MT_BSIK INTO DATA(LS_BSIK).
      AT NEW ZUONR.
        CLEAR: LT_LIST, LT_WRBTR, LV_DMBTR.
      ENDAT.
      CLEAR LS_LIST.
      MOVE-CORRESPONDING LS_BSIK TO LS_LIST.
      IF LS_BSIK-SHKZG = 'H'.
        MULTIPLY LS_LIST-WRBTR BY -1.
        MULTIPLY LS_LIST-DMBTR BY -1.
      ENDIF.
      "Concatenate vendor names
      LS_LIST-NAME = |{ LS_BSIK-NAME1 } { LS_BSIK-NAME2 } { LS_BSIK-NAME3 } { LS_BSIK-NAME4 }|.
      "Get document type data
      READ TABLE MT_T003 INTO DATA(LS_T003) WITH KEY BLART = LS_LIST-BLART.
      IF SY-SUBRC = 0.
        LS_LIST-BLART_TEXT = LS_T003-LTEXT.
        LS_LIST-XMREF = LS_T003-XMREF.
        LS_LIST-YYBLART_GRP = LS_T003-YYBLART_GRP.
        LS_LIST-YYBLART_GRP_TEXT = LS_T003-YYBLART_GRP_TEXT.
        LS_LIST-YYNAME = LS_T003-YYNAME.
      ENDIF.
      "Get payment date
      LS_LIST-ZALDT = ME->GET_PAYMENT_DATE( IS_BSIK = LS_BSIK ).
      "Get special G/L indicator data
      READ TABLE MT_T074 INTO DATA(LS_T074) WITH KEY UMSKZ = LS_LIST-UMSKZ.
      IF SY-SUBRC = 0.
        LS_LIST-UMSKZ_TEXT = LS_T074-LTEXT.
      ENDIF.
      "Get aging
      ME->GET_AGING( EXPORTING IV_PAYMENT_DATE = LS_LIST-ZALDT
                               IV_REFERENCE_DATE = MV_DATE_REF
                     IMPORTING EV_AGING = LS_LIST-AGING
                               ES_CELL_COLOR = LS_CELL_COLOR ).
      APPEND LS_CELL_COLOR TO LS_LIST-COLFIELD.
      READ TABLE LT_AGING_TEXT INTO DATA(LS_AGING_TEXT) WITH KEY DOMNAME = 'YD_CA_AGING'
                                                                 VALUE = LS_LIST-AGING.
      IF SY-SUBRC = 0.
        LS_LIST-AGING_TEXT = LS_AGING_TEXT-DDTEXT.
      ENDIF.
      "Get fund / fund center
      LOOP AT MT_BSEG INTO DATA(LS_BSEG) WHERE BUKRS = LS_BSIK-BUKRS
                                         AND   BELNR = LS_BSIK-BELNR
                                         AND   GJAHR = LS_BSIK-GJAHR
                                         AND   SHKZG <> LS_BSIK-SHKZG.
        IF LS_BSEG-GEBER IS NOT INITIAL.
          LS_LIST-FISTL = LS_BSEG-FISTL.
          LS_LIST-GEBER = LS_BSEG-GEBER.
          LS_LIST-DATBIS = LS_BSEG-DATBIS.
          EXIT.
        ENDIF.
      ENDLOOP.
      "Get clear item / open status icon
      ME->GET_CLOPE( EXPORTING IS_BSIK = LS_BSIK
                     IMPORTING EV_CLOPE = LS_LIST-CLOPE
                               EV_ISTAT = LS_LIST-ISTAT ).

      "Get location and FO/sector
      IF LS_BSIK-XREF1 IS NOT INITIAL.
        LO_LOCATION_DETERMINATION->GET_LOCATION_FROM_FUND_CENTER( EXPORTING IV_FISTL = LS_BSIK-XREF1
                                                                  IMPORTING EV_LOCATION = LS_LIST-LOCATION
                                                                            EV_TEXT = LS_LIST-FO_SECT ).
      ENDIF.
      IF LS_LIST-LOCATION <> 'I' AND LS_LIST-LOCATION <> 'F'.
        LOOP AT MT_USER_ASSIGNMENT INTO DATA(LS_USER_ASSIGNMENT) WHERE UNAME = LS_BSIK-USNAM
                                                                 AND   IT0001_DATA-ENDDA >= LS_BSIK-CPUDT.
          EXIT.
        ENDLOOP.
        IF SY-SUBRC = 0.
          MOVE-CORRESPONDING LS_USER_ASSIGNMENT-IT0001_DATA TO LS_ORG_ASSIGN.
          LO_ORG_ASSIGNMENT->GET_LOC_AND_FO_SECTOR_FROM_PA( EXPORTING IS_ORG_ASSIGN = LS_ORG_ASSIGN
                                                                      IV_DATE = LS_LIST-CPUDT
                                                            IMPORTING EV_LOCATION = LS_LIST-LOCATION
                                                                      EV_FO_SECT = LS_LIST-FO_SECT ).
        ENDIF.
      ENDIF.
      IF LS_LIST-LOCATION IS INITIAL.
        "Try to get if through company code (if different from UNES ...)
        LO_LOCATION_DETERMINATION->GET_LOCATION_FROM_COMP_CODE( EXPORTING IV_BUKRS = LS_BSIK-BUKRS
                                                                IMPORTING EV_LOCATION = LS_LIST-LOCATION
                                                                          EV_TEXT = LS_LIST-FO_SECT ).
      ENDIF.
      TRANSLATE LS_LIST-FO_SECT TO UPPER CASE.

      "Set to temporary table
      APPEND LS_LIST TO LT_LIST.

      IF MV_AMOUNT_FILTER <> 'A'.
        ADD LS_LIST-DMBTR TO LV_DMBTR.
        LS_WRBTR-WWAER = LS_LIST-WWAER.
        LS_WRBTR-WRBTR = LS_LIST-WRBTR.
        COLLECT LS_WRBTR INTO LT_WRBTR.
      ENDIF.

      AT END OF ZUONR.
        CASE MV_AMOUNT_FILTER.
          WHEN 'A'.   "All lines
            APPEND LINES OF LT_LIST TO MT_LIST.
          WHEN 'Z'.   "Only lines where sum on vendor / assignment = 0
            LOOP AT LT_WRBTR TRANSPORTING NO FIELDS WHERE WRBTR <> 0.
              EXIT.
            ENDLOOP.
            IF SY-SUBRC <> 0 AND LV_DMBTR = 0.
              APPEND LINES OF LT_LIST TO MT_LIST.
            ENDIF.
          WHEN 'N'.   "Only lines where sum on vendor / assignment <> 0
            LOOP AT LT_WRBTR TRANSPORTING NO FIELDS WHERE WRBTR <> 0.
              EXIT.
            ENDLOOP.
            IF SY-SUBRC = 0 OR LV_DMBTR <> 0.
              APPEND LINES OF LT_LIST TO MT_LIST.
            ENDIF.
        ENDCASE.
      ENDAT.

    ENDLOOP.

    SORT MT_LIST BY BUKRS LIFNR ZUONR BELNR.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM005 ----
  METHOD GET_PAYMENT_DATE.

    DATA LS_FAEDE TYPE FAEDE.

    MOVE-CORRESPONDING IS_BSIK TO LS_FAEDE.
    LS_FAEDE-KOART = 'K'.

    CALL FUNCTION 'DETERMINE_DUE_DATE'
      EXPORTING
        I_FAEDE                    = LS_FAEDE
        I_GL_FAEDE                 = ABAP_TRUE
      IMPORTING
        E_FAEDE                    = LS_FAEDE
      EXCEPTIONS
        ACCOUNT_TYPE_NOT_SUPPORTED = 1
        OTHERS                     = 2.
    IF SY-SUBRC = 0.
      RV_PAYMENT_DATE = LS_FAEDE-SK1DT.
    ELSE.
      CLEAR RV_PAYMENT_DATE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM006 ----
  METHOD GET_AGING.

    CLEAR: EV_AGING, EV_NBMONTH, ES_CELL_COLOR.

    "Set color for cell depending aging
    ES_CELL_COLOR-FNAME = 'AGING_TEXT'.

    IF IV_PAYMENT_DATE IS INITIAL.
      EV_AGING = 'ZZ'.
      ES_CELL_COLOR-COLOR-COL = COL_TOTAL.
      ES_CELL_COLOR-COLOR-INT = 1.
    ELSEIF IV_PAYMENT_DATE > IV_REFERENCE_DATE.
      EV_AGING = 'FU'.
      ES_CELL_COLOR-COLOR-COL = COL_POSITIVE.
      ES_CELL_COLOR-COLOR-INT = 1.
    ELSE.
      CALL FUNCTION 'HR_99S_MONTHS_BETWEEN_DATES'
        EXPORTING
          P_BEGDA  = IV_PAYMENT_DATE
          P_ENDDA  = IV_REFERENCE_DATE
*         P_COMPL  = ' '
        IMPORTING
          P_MONTHS = EV_NBMONTH.
      IF EV_NBMONTH <= 2.
        EV_AGING = 'L2'.
        ES_CELL_COLOR-COLOR-COL = COL_POSITIVE.
        ES_CELL_COLOR-COLOR-INT = 0.
      ELSEIF EV_NBMONTH <= 6.
        EV_AGING = '26'.
        ES_CELL_COLOR-COLOR-COL = COL_GROUP.
        ES_CELL_COLOR-COLOR-INT = 1.
      ELSE.
        EV_AGING = 'M6'.
        ES_CELL_COLOR-COLOR-COL = COL_NEGATIVE.
        ES_CELL_COLOR-COLOR-INT = 1.
      ENDIF.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM007 ----
  METHOD CHECK_GLOBAL_AUTHORITY.

    "Check access authorization for accounting documents type vendor
    AUTHORITY-CHECK OBJECT 'F_BKPF_KOA'
                ID 'KOART' FIELD 'K'
                ID 'ACTVT' FIELD '03'.
    IF SY-SUBRC <> 0.
      MESSAGE S001(YFI1) WITH 'vendors' RAISING NO_AUTHORIZATION.
    ENDIF.

    "Check access authorization for vendors
    AUTHORITY-CHECK OBJECT 'F_LFA1_BUK'
                ID 'BUKRS' FIELD IV_BUKRS
                ID 'ACTVT' FIELD '03'.
    IF SY-SUBRC <> 0.
      MESSAGE S002(YFI1) WITH 'vendors' IV_BUKRS RAISING NO_AUTHORIZATION.
    ENDIF.

    "Check access authorization for accounting documents for company code
    AUTHORITY-CHECK OBJECT 'F_BKPF_BUK'
                ID 'BUKRS' FIELD IV_BUKRS
                ID 'ACTVT' FIELD '03'.
    IF SY-SUBRC <> 0.
      MESSAGE S003(YFI1) WITH IV_BUKRS RAISING NO_AUTHORIZATION.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM008 ----
  METHOD DISPLAY_ALV.

    DATA LO_EVENTS TYPE REF TO CL_SALV_EVENTS_TABLE.

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

    MO_SALV_TABLE->SET_SCREEN_STATUS( PFSTATUS = 'SALV_TABLE_1'
                                      REPORT   = 'YCA_ALV_GUI_STATUS'
                                      SET_FUNCTIONS = MO_SALV_TABLE->C_FUNCTIONS_ALL ).

    LO_EVENTS = MO_SALV_TABLE->GET_EVENT( ).
*    SET HANDLER me->handle_user_command FOR lo_events.
    SET HANDLER ME->HANDLE_LINK_CLICK FOR LO_EVENTS.

    "ALV columns
    ME->SET_COLUMNS( ).

    "Set totals and subtotals
    IF MV_DO_TOTAL = ABAP_TRUE.
      ME->SET_TOTALS( ).
    ENDIF.

    "Set line selections
*    mo_selections = mo_salv_table->get_selections( ).
*    mo_selections->set_selection_mode( if_salv_c_selection_mode=>row_column ).

    "ALV layout
    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.

    MO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = MV_REPID.
    MO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    MO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).

    "ALV display settings
    MO_DISPLAY_SETTINGS = MO_SALV_TABLE->GET_DISPLAY_SETTINGS( ).
    MO_DISPLAY_SETTINGS->SET_STRIPED_PATTERN( ABAP_TRUE ).
    MO_DISPLAY_SETTINGS->SET_NO_MERGING( ABAP_TRUE ).

*    "Set header
*    me->set_header( ).

    IF MV_NO_AUTH IS NOT INITIAL.
      MESSAGE I006(YFI1) WITH MV_NO_AUTH.
    ENDIF.

    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM009 ----
  METHOD SET_COLUMNS.

    DATA LO_COLUMNS TYPE REF TO CL_SALV_COLUMNS_TABLE.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.

    LO_COLUMNS = MO_SALV_TABLE->GET_COLUMNS( ).
    "Column width optimization
    LO_COLUMNS->SET_OPTIMIZE( ABAP_TRUE ).

    TRY.
        LO_COLUMNS->SET_COLOR_COLUMN( 'COLFIELD' ).
      CATCH CX_SALV_DATA_ERROR.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'ISTAT' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'CLOPE' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
        LO_COLUMN->SET_ALIGNMENT( IF_SALV_C_ALIGNMENT=>CENTERED ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'YYBLART_GRP' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'YYBLART_GRP_TEXT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Group' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Group' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BELNR' ).
        LO_COLUMN->SET_CELL_TYPE( IF_SALV_C_CELL_TYPE=>HOTSPOT ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'AGING' ).
        LO_COLUMN->SET_TECHNICAL( ABAP_TRUE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'AGING_TEXT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Aging' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Aging' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BLART_TEXT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Document type text' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Document type text' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'DATBIS' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'M' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'WRBTR' ).
        LO_COLUMN->SET_LONG_TEXT( 'Amount in doc. currency' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Amount in doc. curr.' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'WWAER' ).
        LO_COLUMN->SET_LONG_TEXT( 'Document currency' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Document currency' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'DMBTR' ).
        LO_COLUMN->SET_LONG_TEXT( 'Amount in local currency' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Amount in local curr' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'DWAER' ).
        LO_COLUMN->SET_LONG_TEXT( 'Local currency' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Local currency' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'UMSKZ_TEXT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Special G/L ind. text' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Spec G/L ind. text' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'XMREF' ).
        LO_COLUMN->SET_CELL_TYPE( IF_SALV_C_CELL_TYPE=>CHECKBOX ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'BUZEI' ).
        LO_COLUMN->SET_VISIBLE( ABAP_FALSE ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'ZLSCH_TEXT' ).
        LO_COLUMN->SET_LONG_TEXT( 'Payment method text' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Payment method text' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= LO_COLUMNS->GET_COLUMN( 'LOCATION' ).
        LO_COLUMN->SET_LONG_TEXT( 'Location' ).
        LO_COLUMN->SET_MEDIUM_TEXT( 'Location' ).
        LO_COLUMN->SET_FIXED_HEADER_TEXT( 'L' ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM00A ----
  METHOD HANDLE_LINK_CLICK.

    CHECK ROW IS NOT INITIAL.
    READ TABLE MT_LIST INTO DATA(LS_LIST) INDEX ROW.
    CHECK SY-SUBRC = 0.

    CASE COLUMN.
      WHEN 'BELNR'.
        SUBMIT YFI_DISPLAY_DOCUMENT WITH P_BUKRS = LS_LIST-BUKRS
                                    WITH P_BELNR = LS_LIST-BELNR
                                    WITH P_GJAHR = LS_LIST-GJAHR
                                    WITH P_BUZEI = LS_LIST-BUZEI
                                    AND RETURN.
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM00B ----
  METHOD SET_TOTALS.

    DATA LO_AGGREGATIONS TYPE REF TO CL_SALV_AGGREGATIONS.
    DATA LO_SORTS TYPE REF TO CL_SALV_SORTS.
    DATA LO_SORT TYPE REF TO CL_SALV_SORT.

    LO_AGGREGATIONS = MO_SALV_TABLE->GET_AGGREGATIONS( ).
    TRY.
        LO_AGGREGATIONS->ADD_AGGREGATION( COLUMNNAME = 'DMBTR'
                                          AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
        LO_AGGREGATIONS->ADD_AGGREGATION( COLUMNNAME = 'WRBTR'
                                          AGGREGATION = IF_SALV_C_AGGREGATION=>TOTAL ).
      CATCH CX_SALV_ERROR.
    ENDTRY.

    LO_SORTS = MO_SALV_TABLE->GET_SORTS( ).
    TRY.
        LO_SORT = LO_SORTS->ADD_SORT( COLUMNNAME = 'LIFNR' ).
        LO_SORT = LO_SORTS->ADD_SORT( COLUMNNAME = 'NAME' ).
        LO_SORT = LO_SORTS->ADD_SORT( COLUMNNAME = 'ZUONR' ).
        LO_SORT->SET_SUBTOTAL( ABAP_TRUE ).
      CATCH CX_SALV_ERROR.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM00C ----
  METHOD GET_CLOPE.

    DATA LS_BSEGP TYPE BSEGP.
    DATA LS_ITEM TYPE RFPOSXEXT.
    DATA LV_XOPVW TYPE BSEG-XOPVW.

    CLEAR: EV_CLOPE, EV_ISTAT.

    MOVE-CORRESPONDING IS_BSIK TO LS_BSEGP.
    MOVE-CORRESPONDING IS_BSIK TO LS_ITEM.
    LS_ITEM-KOART = 'K'.  "Vendor

    "Get XOPVW
    READ TABLE MT_BSEG INTO DATA(LS_BSEG) WITH KEY BUKRS = IS_BSIK-BUKRS
                                                   BELNR = IS_BSIK-BELNR
                                                   GJAHR = IS_BSIK-GJAHR
                                                   BUZEI = IS_BSIK-BUZEI.
    IF SY-SUBRC = 0.
      LV_XOPVW = LS_BSEG-XOPVW.
    ENDIF.

    CALL FUNCTION 'ITEM_DERIVE_FIELDS'
      EXPORTING
        S_T001       = MS_T001
        S_BSEGP      = LS_BSEGP
        KEY_DATE     = MV_DATE_REF
        XOPVW        = LV_XOPVW
        X_ICONS_ONLY = ABAP_TRUE
*       I_KALSM      =
      CHANGING
        S_ITEM       = LS_ITEM
      EXCEPTIONS
        BAD_INPUT    = 1
        OTHERS       = 2.

    IF SY-SUBRC = 0.
      EV_CLOPE = LS_ITEM-ICO_AUGP.
      CASE LS_ITEM-ICO_AUGP(3).
        WHEN ICON_LED_RED(3).   "Open item
          EV_ISTAT = 'O'.
        WHEN ICON_LED_YELLOW(3).  "Parked item
          EV_ISTAT = 'K'.
        WHEN ICON_LED_GREEN(3).  "Cleared item
          EV_ISTAT = 'C'.
        WHEN ICON_CHECKED(3).  "Posted item
          EV_ISTAT = 'P'.
      ENDCASE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CM00E ----
  METHOD PREPARE_FOR_LOCATION_SECTOR.

    TYPES: BEGIN OF LTY_CREATOR,
             UNAME TYPE UNAME,
             AEDAT TYPE AEDAT,
           END OF LTY_CREATOR.

    DATA LT_CREATOR TYPE TABLE OF LTY_CREATOR.
    DATA LS_CREATOR TYPE LTY_CREATOR.
    DATA LV_NEW TYPE XFELD.
    DATA LV_END TYPE XFELD.
    DATA LT_USER_PERIOD TYPE YCL_HR_USER_ASSIGNMENT=>TTY_USER_PERIOD.
    DATA LS_USER_PERIOD TYPE YCL_HR_USER_ASSIGNMENT=>TY_USER_PERIOD.
    DATA LO_USER_ASSIGNMENT TYPE REF TO YCL_HR_USER_ASSIGNMENT.

    "Extract users for location / field office
    LOOP AT MT_BSIK INTO DATA(LS_BSIK).
      LS_CREATOR-UNAME = LS_BSIK-USNAM.
      LS_CREATOR-AEDAT = LS_BSIK-CPUDT.
      APPEND LS_CREATOR TO LT_CREATOR.
    ENDLOOP.

    SORT LT_CREATOR.
    DELETE ADJACENT DUPLICATES FROM LT_CREATOR.

    LOOP AT LT_CREATOR INTO LS_CREATOR.
      LV_NEW = LV_END = ABAP_FALSE.
      AT NEW UNAME.
        LV_NEW = ABAP_TRUE.
      ENDAT.
      IF LV_NEW = ABAP_TRUE.
        CLEAR LS_USER_PERIOD.
        LS_USER_PERIOD-UNAME = LS_CREATOR-UNAME.
        LS_USER_PERIOD-BEGDA = LS_CREATOR-AEDAT.
        IF LS_USER_PERIOD-BEGDA < MV_OLDEST_USER_BEGDA AND LS_USER_PERIOD-BEGDA IS NOT INITIAL.
          MV_OLDEST_USER_BEGDA = LS_USER_PERIOD-BEGDA.
        ENDIF.
      ENDIF.
      AT END OF UNAME.
        LV_END = ABAP_TRUE.
      ENDAT.
      IF LV_END = ABAP_TRUE.
        "ls_user_period-endda = ls_creator-aedat.
        LS_USER_PERIOD-ENDDA = '99991231'.
        INSERT LS_USER_PERIOD INTO TABLE LT_USER_PERIOD.
      ENDIF.
    ENDLOOP.

    "Get User assignment
    LO_USER_ASSIGNMENT = NEW YCL_HR_USER_ASSIGNMENT( ).
    LO_USER_ASSIGNMENT->GET_USER_PERNR_ORG_ASSIGN( EXPORTING IT_USER_PERIOD = LT_USER_PERIOD
                                                   IMPORTING ET_USER_ASSIGNMENT = MT_USER_ASSIGNMENT ).

  ENDMETHOD.

* ---- YCL_FI_OPEN_VENDORS_BL========CO ----
PROTECTED SECTION.

* ---- YCL_FI_OPEN_VENDORS_BL========CU ----
CLASS YCL_FI_OPEN_VENDORS_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  TYPES:
    BEGIN OF TY_LIST.
             INCLUDE TYPE YSFI_OPEN_VENDORS_DATA.
             TYPES: COLFIELD TYPE LVC_T_SCOL,
           END OF TY_LIST .
  TYPES:
    TTY_LIST TYPE TABLE OF TY_LIST .

  DATA MT_LIST TYPE TTY_LIST .
  DATA MV_NO_AUTH TYPE INT4 .

  METHODS CHECK_GLOBAL_AUTHORITY
    IMPORTING
      !IV_BUKRS TYPE BUKRS
    EXCEPTIONS
      NO_AUTHORIZATION .
  METHODS GET_DATA
    IMPORTING
      !IV_DATE TYPE DATUM
      !IV_AMOUNT_FILTER TYPE CHAR1 DEFAULT 'A'
      !IV_DO_TOTAL TYPE XFELD DEFAULT ABAP_FALSE .
  METHODS SET_SELECTION_VALUES
    IMPORTING
      !IV_SELNAME TYPE RSSCR_NAME
      !IV_KIND TYPE RSSCR_KIND
      !IV_VALUE TYPE ANY OPTIONAL
      !IT_VALUE TYPE ANY TABLE OPTIONAL .
  METHODS DISPLAY_ALV
    IMPORTING
      !IV_REPID TYPE SY-REPID DEFAULT SY-REPID .