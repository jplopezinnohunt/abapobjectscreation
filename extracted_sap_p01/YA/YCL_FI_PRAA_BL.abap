* ==== CLASS POOL YCL_FI_PRAA_BL ====
CLASS-POOL .
*"* class pool for class YCL_FI_PRAA_BL

*"* local type definitions
INCLUDE YCL_FI_PRAA_BL================CCDEF.

*"* class YCL_FI_PRAA_BL definition
*"* public declarations
  INCLUDE YCL_FI_PRAA_BL================CU.
*"* protected declarations
  INCLUDE YCL_FI_PRAA_BL================CO.
*"* private declarations
  INCLUDE YCL_FI_PRAA_BL================CI.
ENDCLASS. "YCL_FI_PRAA_BL definition

*"* macro definitions
INCLUDE YCL_FI_PRAA_BL================CCMAC.
*"* local class implementation
INCLUDE YCL_FI_PRAA_BL================CCIMP.

CLASS YCL_FI_PRAA_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_PRAA_BL implementation


* ---- YCL_FI_PRAA_BL================CI ----
PRIVATE SECTION.

  TYPES:
    TTY_PSKEY TYPE TABLE OF PSKEY .
  TYPES:
    BEGIN OF TY_MESSAGE,
      STATUS  TYPE P_99S_STATU,
      PERNR   TYPE P_PERNR,
      MESSAGE TYPE TEXT132,
    END OF TY_MESSAGE .
  TYPES:
    TTY_MESSAGE TYPE TABLE OF TY_MESSAGE .
  TYPES:
    TTY_RANGE_WAERS TYPE RANGE OF PAD_WAERS .
  TYPES:
    TTY_RANGE_ZLSCH TYPE RANGE OF PCODE .
  TYPES:
    BEGIN OF TY_LIFNR_PERNR,
      LIFNR TYPE LIFNR,
      NAME1 TYPE NAME1_GP,
      PERNR TYPE P_PERNR,
    END OF TY_LIFNR_PERNR .
  TYPES:
    TTY_LIFNR_PERNR TYPE TABLE OF TY_LIFNR_PERNR .
  TYPES:
    BEGIN OF TY_BANK_DATA,
      BANKS    TYPE BANKS,
      BANKL    TYPE BANKL,
      BANKN    TYPE BANKN,
      BKONT    TYPE BKONT,
      BVTYP    TYPE BVTYP,
      BKREF    TYPE BKREF,
      KOINH    TYPE KOINH_FI,
      YYTRAVEL TYPE YE_TV_BANK_FOR_TRAVEL,
    END OF TY_BANK_DATA .
  TYPES:
    TTY_BANK_DATA TYPE TABLE OF TY_BANK_DATA .
  TYPES:
    BEGIN OF TY_BANK_CURRENCY,
      BANKS TYPE BANKS,
      BANKL TYPE BANKL,
      BANKN TYPE BANKN,
      BKONT TYPE BKONT,
      BVTYP TYPE BVTYP,
      CURRE TYPE BVTYP,
    END OF TY_BANK_CURRENCY .
  TYPES:
    TTY_BANK_CURRENCY TYPE TABLE OF TY_BANK_CURRENCY .
  TYPES:
    TTY_CURRENCY TYPE TABLE OF BVTYP .
  TYPES:
    TTY_PERNR_EXCLUDED TYPE TABLE OF YTHR_PRAA_EXC .

  DATA MT_PERNR_EXCLUDED TYPE TTY_PERNR_EXCLUDED .
  DATA MS_PA0001 TYPE PA0001 .
  DATA MT_STRING TYPE STRING_TABLE .
  DATA MT_LIFNR_PERNR TYPE TTY_LIFNR_PERNR .
  CONSTANTS C_NODATA TYPE NODATA_BI VALUE '/' ##NO_TEXT.
  DATA MT_WAERS TYPE TTY_RANGE_WAERS .
  DATA MT_ZLSCH TYPE TTY_RANGE_ZLSCH .
  DATA MT_PERNR_MSG TYPE TTY_MESSAGE .
  DATA MT_PSKEY TYPE TTY_PSKEY .
  CLASS-DATA MO_INSTANCE TYPE REF TO YCL_FI_PRAA_BL .
  DATA MO_MESSAGE_HANDLER TYPE REF TO CL_HRPA_MESSAGE_LIST .
  DATA MO_PLAIN_INFOTYPE_ACCESS TYPE REF TO CL_HRPA_PLAIN_INFOTYPE_ACCESS .
  DATA:
    MT_PAYMENT_LIST TYPE TABLE OF T042Z_L_BF .
  DATA:
    MT_COUNTRY_PROP TYPE TABLE OF YTFI_PRAA_CTRY .

  METHODS GET_PAYMENT_METHOD_LIST
    IMPORTING
      !IV_COUNTRY TYPE LAND1 .
  METHODS SET_BGR00
    IMPORTING
      !IV_GROUP TYPE APQ_GRPN
    RETURNING
      VALUE(RS_BGR00) TYPE BGR00 .
  METHODS SET_BLF00
    IMPORTING
      !IV_LIFNR TYPE LIFNR
      !IV_BUKRS TYPE BUKRS OPTIONAL
    RETURNING
      VALUE(RS_BLF00) TYPE BLF00 .
  METHODS SET_BLFBK
    IMPORTING
      !IS_BANK TYPE TY_BANK_DATA
      !IV_DELETE TYPE BOOLEAN OPTIONAL
    RETURNING
      VALUE(RS_BLFBK) TYPE BLFBK .
  METHODS GET_EMPLOYEE_BANKS
    IMPORTING
      !IT_STATUS TYPE YTTHR_SUBTY_TRAVEL
    EXPORTING
      !ET_BANK TYPE TTY_BANK_DATA .
  METHODS GET_VENDOR_BANKS
    IMPORTING
      !IV_LIFNR TYPE LIFNR
    EXPORTING
      !ET_BANK TYPE TTY_BANK_DATA
      !ET_BANK_CURRENCY TYPE TTY_BANK_CURRENCY
      !ET_CURRENCY TYPE TTY_CURRENCY .
  METHODS CHECK_SUBTY
    IMPORTING
      !IV_WAERS TYPE WAERS
      !IV_ZLSCH TYPE PCODE
    RETURNING
      VALUE(RV_IS_OK) TYPE BOOLEAN .
  METHODS SET_MESSAGE
    IMPORTING
      !IV_PERNR TYPE P_PERNR
      !IT_MESSAGES TYPE HRPAD_MESSAGE_TAB .

* ---- YCL_FI_PRAA_BL================CM001 ----
  METHOD GET_INSTANCE.

    IF MO_INSTANCE IS INITIAL.
      CREATE OBJECT MO_INSTANCE TYPE (IV_CLASSNAME).
     ENDIF.

     RO_INSTANCE = MO_INSTANCE.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM002 ----
  METHOD CONSTRUCTOR.

    DATA LO_MASTERDATA_BUFFER TYPE REF TO IF_HRPA_MASTERDATA_BUFFER.
    DATA LO_MASTERDATA_BL TYPE REF TO IF_HRPA_MASTERDATA_BL.

    TRY.
        CALL METHOD CL_HRPA_MASTERDATA_BUFFER=>GET_INSTANCE
          IMPORTING
            MASTERDATA_BUFFER = LO_MASTERDATA_BUFFER.
      CATCH CX_HRPA_VIOLATED_ASSERTION .
    ENDTRY.

    TRY.
        CALL METHOD CL_HRPA_MASTERDATA_BL=>GET_INSTANCE
          EXPORTING
            MASTERDATA_BUFFER = LO_MASTERDATA_BUFFER
          IMPORTING
            MASTERDATA_BL     = LO_MASTERDATA_BL.
      CATCH CX_HRPA_VIOLATED_ASSERTION .
    ENDTRY.

    CREATE OBJECT MO_PLAIN_INFOTYPE_ACCESS TYPE CL_HRPA_PLAIN_INFOTYPE_ACCESS
      EXPORTING
        MASTERDATA_BL = LO_MASTERDATA_BL.

    "Currency to filter
    MT_WAERS = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'EUR' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'USD' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'GBP' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'CHF' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'CAD' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'NOK' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'DDK' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'JPY' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'MGA' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'TND' ) ).

    "Payment mode to filter
    MT_ZLSCH = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = 'C' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'J' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'L' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'N' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'S' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = 'X' ) ).

    "Get excluded PERNR
    SELECT * INTO TABLE MT_PERNR_EXCLUDED FROM YTHR_PRAA_EXC.

    "Get country properties
    SELECT * INTO TABLE MT_COUNTRY_PROP FROM YTFI_PRAA_CTRY.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM003 ----
  METHOD DELIMIT_BANK_DATA.

    DATA LT_PA0009 TYPE TABLE OF PA0009.
    DATA LS_PA0009 TYPE PA0009.
    DATA LS_P0009 TYPE P0009.
    DATA LS_PSKEY TYPE PSKEY.
    DATA LT_MESSAGES TYPE HRPAD_MESSAGE_TAB.
    DATA LS_PERNR_MSG TYPE TY_MESSAGE.
    DATA LV_MODE TYPE HRPAD_UPDATE_MODE.
    DATA LO_EXC TYPE REF TO CX_HRPA_VIOLATED_ASSERTION.
    DATA LV_ERROR_SHORT TYPE STRING.
    DATA LV_IS_OK TYPE BOOLEAN.

    CLEAR MT_PSKEY.

    ME->GET_PAYMENT_METHOD_LIST( 'FR' ).

    "Get data
    SELECT * FROM PA0009 AS P9
             FOR ALL ENTRIES IN @IT_PERNR
             WHERE P9~PERNR = @IT_PERNR-TABLE_LINE
             AND   P9~SUBTY = @IV_SUBTY
             AND   P9~SPRPS = @SPACE
             AND   P9~ENDDA > @IV_ENDDA
          INTO TABLE @LT_PA0009.

    "Delete buffers
    CALL METHOD MO_PLAIN_INFOTYPE_ACCESS->IF_HRPA_BUFFER_CONTROL~INITIALIZE.

    LV_MODE-NO_RETROACTIVITY = ABAP_TRUE.

    LOOP AT LT_PA0009 INTO LS_PA0009.
      IF LS_PA0009-BEGDA > IV_ENDDA.
        LS_PERNR_MSG-PERNR = LS_PA0009-PERNR.
        LS_PERNR_MSG-MESSAGE = |No delimation possible for record starting at { LS_PA0009-BEGDA }|.
        WRITE ICON_LED_RED TO LS_PERNR_MSG-STATUS AS ICON.
        APPEND LS_PERNR_MSG TO MT_PERNR_MSG.
      ELSE.
        CREATE OBJECT MO_MESSAGE_HANDLER.

        MOVE-CORRESPONDING LS_PA0009 TO LS_P0009.
        LS_P0009-INFTY = '0009'.
        MOVE-CORRESPONDING LS_P0009 TO LS_PSKEY.

        "Delimit infotype
        LS_P0009-ENDDA = IV_ENDDA.

        "Check payment method
        IF LS_P0009-ZLSCH IS NOT INITIAL.
          READ TABLE MT_PAYMENT_LIST TRANSPORTING NO FIELDS WITH KEY ZLSCH = LS_P0009-ZLSCH.
          IF SY-SUBRC <> 0.
            LS_P0009-ZLSCH = 'Z'.
          ENDIF.
        ENDIF.

        CLEAR LV_IS_OK.

        TRY.
            CALL METHOD MO_PLAIN_INFOTYPE_ACCESS->IF_HRPA_PLAIN_INFOTYPE_ACCESS~MODIFY
              EXPORTING
                TCLAS           = 'A'
                OLD_PSKEY       = LS_PSKEY
*               massn           =
*               massg           =
                UPDATE_MODE     = LV_MODE
*               no_auth_check   =
                MESSAGE_HANDLER = MO_MESSAGE_HANDLER
              IMPORTING
                IS_OK           = LV_IS_OK
              CHANGING
                PNNNN           = LS_P0009
*               pnnnn2          =
*               pref            =
*               text_tab        =
              .
          CATCH CX_HRPA_VIOLATED_ASSERTION INTO LO_EXC.
            CLEAR LS_PERNR_MSG.
            LS_PERNR_MSG-MESSAGE = LO_EXC->GET_TEXT( ).
            LS_PERNR_MSG-PERNR = LS_PSKEY-PERNR.
            WRITE ICON_ALERT TO LS_PERNR_MSG-STATUS AS ICON.
            APPEND LS_PERNR_MSG TO MT_PERNR_MSG.
        ENDTRY.

        MO_MESSAGE_HANDLER->GET_MESSAGE_LIST( IMPORTING MESSAGES = LT_MESSAGES ).
        ME->SET_MESSAGE( EXPORTING IV_PERNR = LS_PSKEY-PERNR
                                   IT_MESSAGES = LT_MESSAGES ).
        FREE MO_MESSAGE_HANDLER.
        CLEAR LT_MESSAGES.

        IF LV_IS_OK = ABAP_TRUE.
          LS_PERNR_MSG-MESSAGE = |Infotype 0009 subtype { IV_SUBTY } delimited|.
          LS_PERNR_MSG-PERNR = LS_PSKEY-PERNR.
          WRITE ICON_LED_GREEN TO LS_PERNR_MSG-STATUS AS ICON.
          APPEND LS_PERNR_MSG TO MT_PERNR_MSG.
        ENDIF.
      ENDIF.

    ENDLOOP.

    IF MV_UPDATE = ABAP_TRUE.
      TRY.
          CALL METHOD MO_PLAIN_INFOTYPE_ACCESS->IF_HRPA_BUFFER_CONTROL~FLUSH
            EXPORTING
              NO_COMMIT = SPACE.
        CATCH CX_HRPA_VIOLATED_ASSERTION .
      ENDTRY.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM004 ----
  METHOD SET_MESSAGE.

    DATA LS_PERNR_MSG TYPE TY_MESSAGE.

    LOOP AT IT_MESSAGES INTO DATA(LS_MESSAGE).
      CLEAR LS_PERNR_MSG.
      LS_PERNR_MSG-PERNR = IV_PERNR.
      MESSAGE ID LS_MESSAGE-MSGID TYPE LS_MESSAGE-MSGTY NUMBER LS_MESSAGE-MSGNO
              WITH LS_MESSAGE-MSGV1 LS_MESSAGE-MSGV2 LS_MESSAGE-MSGV3 LS_MESSAGE-MSGV4 INTO LS_PERNR_MSG-MESSAGE.
      CASE LS_MESSAGE-MSGTY.
        WHEN 'E'.
          WRITE ICON_LED_RED TO LS_PERNR_MSG-STATUS AS ICON.
        WHEN 'W'.
          WRITE ICON_LED_YELLOW TO LS_PERNR_MSG-STATUS AS ICON.
        WHEN 'I'.
          WRITE ICON_LED_GREEN TO LS_PERNR_MSG-STATUS AS ICON.
        WHEN 'S'.
          WRITE ICON_LED_INACTIVE TO LS_PERNR_MSG-STATUS AS ICON.
        WHEN OTHERS.
          WRITE ICON_ALERT TO LS_PERNR_MSG-STATUS AS ICON.
      ENDCASE.
      APPEND LS_PERNR_MSG TO MT_PERNR_MSG.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM005 ----
  METHOD DISPLAY_ALV.

    DATA LO_ALV TYPE REF TO YIF_ALV_DISPLAY.
    DATA LT_COLUMNS TYPE SALV_T_COLUMN.

    FIELD-SYMBOLS <TAB> TYPE ANY TABLE.
    ASSIGN (IV_TABNAME) TO <TAB>.
    CHECK SY-SUBRC = 0.

    LO_ALV = YCL_ALV_FACTORY=>GET_INSTANCE( ).
    LO_ALV->INIT_ALV( EXPORTING IV_HEADER = 1
                      CHANGING IT_TABLE = <TAB> ).
    LO_ALV->SET_MAIN_FUNCTIONS( EXPORTING IV_REPORT = MV_REPID
                                          IV_TITLE = IV_TITLE ).

    IF IV_SORT_FIELD IS NOT INITIAL.
      APPEND IV_SORT_FIELD TO LT_COLUMNS.
      LO_ALV->SET_SORTED_COLUMS( LT_COLUMNS ).
    ENDIF.

    IF MV_UPDATE = ABAP_TRUE.
      LO_ALV->SET_HEADER( IV_TYPE = 'T'
                          IV_ROW = 1
                          IV_COLUMN = 1
                          IV_TEXT = IV_LABEL_UPD ).
    ELSE.
      LO_ALV->SET_HEADER( IV_TYPE = 'T'
                    IV_ROW = 1
                    IV_COLUMN = 1
                    IV_TEXT = IV_LABEL_TEST ).
    ENDIF.
    LO_ALV->DISPLAY_ALV( ).

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM006 ----
  METHOD GET_IT0009_SUBTY_STATUS.

    DATA LS_P0009 TYPE P0009.
    DATA LS_P0009_2 TYPE P0009.
    DATA LT_SUBTY TYPE RANGE OF SUBTY.
    DATA LS_STATUS TYPE LINE OF YTTHR_SUBTY_TRAVEL.
    DATA LV_TRAVEL TYPE I.
    DATA LV_SUBTY TYPE SUBTY.
    DATA LT_P0009 TYPE TABLE OF P0009.
    FIELD-SYMBOLS <STATUS> TYPE LINE OF YTTHR_SUBTY_TRAVEL.

    "Extract subty 0, 1, 2 from infotype 0009
    LT_SUBTY = VALUE #( ( SIGN = 'I' OPTION = 'EQ' LOW = '0' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = '1' )
                        ( SIGN = 'I' OPTION = 'EQ' LOW = '2' ) ).

    "Get infotype 0009
    CLEAR MT_P0009.
    SELECT * INTO CORRESPONDING FIELDS OF TABLE LT_P0009 FROM PA0009
                                              WHERE PERNR = IV_PERNR
                                              AND   SUBTY IN LT_SUBTY
                                              AND   SPRPS = SPACE
                                              AND   ENDDA >= IV_DATE
                                              AND   BEGDA <= '99991231'
                                              AND   ZLSCH IN MT_ZLSCH
                                              ORDER BY SUBTY.

    "At date for main bank to be aligned with PRAA standard
    LOOP AT LT_P0009 INTO LS_P0009 WHERE SUBTY = '0'
                                   AND   BEGDA <= IV_DATE
                                   AND   ENDDA >= IV_DATE.
      APPEND LS_P0009 TO MT_P0009.
      EXIT.
    ENDLOOP.

    "The last for other bank
    SORT LT_P0009 BY SUBTY ENDDA DESCENDING.
    LOOP AT LT_P0009 INTO LS_P0009 WHERE SUBTY = '1'.
      APPEND LS_P0009 TO MT_P0009.
      EXIT.
    ENDLOOP.

    "Get the last subtype 2
    LOOP AT LT_P0009 INTO LS_P0009_2 WHERE SUBTY = '2'.
      EXIT.
    ENDLOOP.

    LOOP AT MT_P0009 INTO LS_P0009.
      CLEAR LS_STATUS.
      LS_STATUS-SUBTY = LS_P0009-SUBTY.
      IF ME->CHECK_SUBTY( EXPORTING IV_WAERS = LS_P0009-WAERS
                                    IV_ZLSCH = LS_P0009-ZLSCH ) = ABAP_TRUE.
        LS_STATUS-YYTRAVEL = ABAP_TRUE.
        ADD 1 TO LV_TRAVEL.
      ENDIF.
      APPEND LS_STATUS TO RT_STATUS.
    ENDLOOP.

    IF LV_TRAVEL = 2.
      LOOP AT RT_STATUS ASSIGNING <STATUS>.
        CLEAR <STATUS>-YYTRAVEL.
      ENDLOOP.
      UNASSIGN <STATUS>.
    ENDIF.

    CASE LV_TRAVEL.
      WHEN 0 OR 2.
        "No TRAVEL found:
        "  - check if subtype 2 is filled with travel bank and find corresponding
        "    bank in subtype 0 or 1
        "  - else, if a travel bank exixts, take it
        "  - else, put 0 as default travel bank
        "  - else put 1 as default travel bank
        IF LS_P0009_2 IS NOT INITIAL.
          READ TABLE MT_P0009 INTO LS_P0009 WITH KEY BANKS = LS_P0009_2-BANKS
                                                     BANKL = LS_P0009_2-BANKL
                                                     BANKN = LS_P0009_2-BANKN
                                                     BKONT = LS_P0009_2-BKONT.
          IF SY-SUBRC = 0.
            LV_SUBTY = LS_P0009-SUBTY.
          ELSE.
            LV_SUBTY = LS_P0009_2-SUBTY.
            CLEAR LS_STATUS.
            LS_STATUS-SUBTY = LV_SUBTY.
            APPEND LS_STATUS TO RT_STATUS.
            "Set travel bank to Bank table
            APPEND LS_P0009_2 TO MT_P0009.
          ENDIF.
        ENDIF.
        IF LV_SUBTY IS INITIAL.
          READ TABLE MT_P0009 TRANSPORTING NO FIELDS WITH KEY SUBTY = '0'.
          IF SY-SUBRC = 0.
            LV_SUBTY = '0'.
          ELSE.
            LV_SUBTY = '1'.
          ENDIF.
        ENDIF.
        READ TABLE RT_STATUS ASSIGNING <STATUS> WITH KEY SUBTY = LV_SUBTY.
        IF <STATUS> IS ASSIGNED.
          <STATUS>-YYTRAVEL = ABAP_TRUE.
        ENDIF.
      WHEN 1.
        "Nothing to do
    ENDCASE.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM007 ----
  METHOD CHECK_SUBTY.

    RV_IS_OK = ABAP_FALSE.
    CHECK IV_WAERS IN MT_WAERS.
    CHECK IV_ZLSCH IN MT_ZLSCH.
    RV_IS_OK = ABAP_TRUE.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM008 ----
  METHOD GET_ASSIGNMENT.

    IF MS_PA0001-PERNR <> IV_PERNR.
      CLEAR MS_PA0001.
      SELECT SINGLE * INTO MS_PA0001 FROM PA0001 WHERE PERNR = IV_PERNR
                                                 AND   SPRPS = SPACE
                                                 AND   ENDDA >= IV_DATE
                                                 AND   BEGDA <= IV_DATE.
    ENDIF.

    EV_ENAME = MS_PA0001-ENAME.
    EV_PERSG = MS_PA0001-PERSG.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM009 ----
  METHOD SET_BGR00.

    RS_BGR00-STYPE = '0'.
    RS_BGR00-GROUP = IV_GROUP.
    RS_BGR00-MANDT = SY-MANDT.
    RS_BGR00-USNAM = SY-UNAME.
    RS_BGR00-NODATA = C_NODATA.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00A ----
  METHOD SET_BLF00.

    RS_BLF00-STYPE = '1'.
    RS_BLF00-TCODE = 'XK02'.
    RS_BLF00-LIFNR = IV_LIFNR.
    IF IV_BUKRS IS NOT INITIAL.
      RS_BLF00-BUKRS = IV_BUKRS.
    ELSE.
      RS_BLF00-BUKRS = C_NODATA.
    ENDIF.
    RS_BLF00-EKORG = C_NODATA.
    RS_BLF00-KTOKK = C_NODATA.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00C ----
  METHOD GET_VENDOR_BANKS.

    DATA LS_BANK_CURRENCY TYPE TY_BANK_CURRENCY.

    SELECT * INTO CORRESPONDING FIELDS OF TABLE ET_BANK FROM LFBK WHERE LIFNR = IV_LIFNR.

    SORT ET_BANK.

    LOOP AT ET_BANK ASSIGNING FIELD-SYMBOL(<LS_BANK>).
      MOVE-CORRESPONDING <LS_BANK> TO LS_BANK_CURRENCY.
      LS_BANK_CURRENCY-CURRE = <LS_BANK>-BVTYP(3).
      APPEND LS_BANK_CURRENCY TO ET_BANK_CURRENCY.
      APPEND <LS_BANK>-BVTYP TO ET_CURRENCY.
      <LS_BANK>-BVTYP = LS_BANK_CURRENCY-CURRE.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00D ----
  METHOD GET_EMPLOYEE_BANKS.

    DATA LS_BANK_DATA TYPE TY_BANK_DATA.
    DATA LV_ENAME TYPE EMNAM.

    LOOP AT MT_P0009 INTO DATA(LS_P0009) WHERE BANKN IS NOT INITIAL.
      MOVE-CORRESPONDING LS_P0009 TO LS_BANK_DATA.
      LS_BANK_DATA-BVTYP = LS_P0009-WAERS.
      IF LS_P0009-EMFTX IS NOT INITIAL.
        LS_BANK_DATA-KOINH = LS_P0009-EMFTX.
      ELSE.
        ME->GET_ASSIGNMENT( EXPORTING IV_PERNR = LS_P0009-PERNR
                            IMPORTING EV_ENAME = LV_ENAME ).
        LS_BANK_DATA-KOINH = LV_ENAME.
      ENDIF.
      READ TABLE IT_STATUS INTO DATA(LS_STATUS) WITH KEY SUBTY = LS_P0009-SUBTY.
      IF SY-SUBRC = 0.
        LS_BANK_DATA-YYTRAVEL = LS_STATUS-YYTRAVEL.
      ENDIF.
      "For some countries (CN, TJ, TN) reference field containes additional informations
      "this information is set to bank control key in vendor
*      IF ls_p0009-bkont IS INITIAL AND ls_p0009-bkref IS NOT INITIAL.
*        ls_bank_data-bkont = me->set_reference_to_control_key( ls_p0009 ).
*      ENDIF.

      APPEND LS_BANK_DATA TO ET_BANK.
    ENDLOOP.

    SORT ET_BANK.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00E ----
  METHOD SET_BLFBK.

    "Set data
    RS_BLFBK-STYPE = '2'.
    RS_BLFBK-TBNAM = 'BLFBK'.
    RS_BLFBK-XDELE = IV_DELETE.
    MOVE-CORRESPONDING IS_BANK TO RS_BLFBK.

    "Set '/' to empty fields
    DO.
      ASSIGN COMPONENT SY-INDEX OF STRUCTURE RS_BLFBK TO FIELD-SYMBOL(<FIELD>).
      IF SY-SUBRC <> 0.
        EXIT.
      ENDIF.
      IF <FIELD> IS ASSIGNED AND <FIELD> = SPACE.
        <FIELD> = C_NODATA.
      ENDIF.
    ENDDO.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00H ----
  METHOD GET_PAYMENT_METHOD_LIST.

    CALL FUNCTION 'HRCA_PAYMENTMETH_GETLIST'
      EXPORTING
        COUNTRY    = IV_COUNTRY
      TABLES
        T042Z_LIST = MT_PAYMENT_LIST
      EXCEPTIONS
        NOT_FOUND  = 1
        OTHERS     = 2.
    IF SY-SUBRC <> 0.
      CLEAR MT_PAYMENT_LIST.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00J ----
  METHOD IS_EXCLUDED_PERNR.

    READ TABLE MT_PERNR_EXCLUDED TRANSPORTING NO FIELDS WITH KEY PERNR = IV_PERNR.
    IF SY-SUBRC = 0.
      RV_EXCLUDED = ABAP_TRUE.
    ELSE.
      RV_EXCLUDED = ABAP_FALSE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00K ----
  METHOD GET_COUNTRY_PROPERTIES.

    READ TABLE MT_COUNTRY_PROP INTO RS_PROP WITH KEY LAND1 = IV_LAND1.
    IF SY-SUBRC <> 0.
      CLEAR RS_PROP.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00P ----
  METHOD GET_VENDOR_TO_EXTEND_COMP_CODE.

    DATA LT_LFB1 TYPE SORTED TABLE OF LFB1 WITH UNIQUE KEY LIFNR BUKRS.

    CHECK MT_PERNR IS NOT INITIAL.

    IF MV_NO_MODIF_SCAN = ABAP_FALSE.
      "Get vendor modified from modified date
      SELECT DISTINCT A~LIFNR, A~NAME1, B~PERNR FROM LFA1 AS A
                     INNER JOIN LFB1 AS B ON B~LIFNR = A~LIFNR
                     INNER JOIN CDHDR AS C
                     ON   C~OBJECTCLAS = 'KRED'
                     AND  C~OBJECTID = B~LIFNR
                     AND  C~UDATE >= @IV_DATE_FROM
                     AND  ( C~TCODE = 'XK01' OR C~TCODE = 'XK02' )
                     FOR ALL ENTRIES IN @MT_PERNR
                     WHERE B~PERNR = @MT_PERNR-TABLE_LINE
                     AND   B~BUKRS IN @IT_BUKRS_RANGE
             INTO TABLE @MT_LIFNR_PERNR.
    ELSE.
      "Get all vendor corresponding to personnel number from selection screen
      SELECT DISTINCT A~LIFNR, A~NAME1, B~PERNR FROM LFA1 AS A
                      INNER JOIN LFB1 AS B ON B~LIFNR = A~LIFNR
                      FOR ALL ENTRIES IN @MT_PERNR
                      WHERE B~PERNR = @MT_PERNR-TABLE_LINE
                      AND   B~BUKRS IN @IT_BUKRS_RANGE
             APPENDING TABLE @MT_LIFNR_PERNR.
    ENDIF.

    SORT MT_LIFNR_PERNR.
    DELETE ADJACENT DUPLICATES FROM MT_LIFNR_PERNR.

    CHECK MT_LIFNR_PERNR IS NOT INITIAL.

    "Get all data for vendor / company code
    SELECT * FROM LFB1 FOR ALL ENTRIES IN @MT_LIFNR_PERNR
                       WHERE LIFNR = @MT_LIFNR_PERNR-LIFNR
                       AND   ( BUKRS IN @IT_BUKRS_RANGE OR BUKRS = @IV_BUKRS_TARGET )
                       INTO TABLE @LT_LFB1.

    LOOP AT MT_LIFNR_PERNR INTO DATA(LS_LIFNR_PERNR).

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00Q ----
  METHOD GET_VENDOR_TO_MODIFY_BANK.

    DATA LT_PERNR TYPE TABLE OF P_PERNR.
    DATA LT_LFBK_BANK TYPE TTY_BANK_DATA.
    DATA LT_0009_BANK TYPE TTY_BANK_DATA.
    DATA LS_BANK TYPE TY_BANK_DATA.
    DATA LT_BANK_CURRENCY TYPE TTY_BANK_CURRENCY.
    DATA LS_BANK_CURRENCY TYPE TY_BANK_CURRENCY.
    DATA LT_CURRENCY TYPE TTY_CURRENCY.
    DATA LV_BVTYP TYPE BVTYP.
    DATA LV_NUMBER(1) TYPE N.
* EVO IBAN
    DATA : LV_BANKN35 TYPE BANKN35,
           LV_IBAN    TYPE IBAN,
           LS_RETURN  TYPE BAPIRET2,
           LV_SUBRC   TYPE SYSUBRC.
* Fin EVO IBAN

    CHECK MT_PERNR IS NOT INITIAL.

    IF MV_NO_MODIF_SCAN = ABAP_FALSE.

      "Get vendor modified from modified date
      SELECT DISTINCT A~LIFNR, A~NAME1, B~PERNR FROM LFA1 AS A
                     INNER JOIN LFB1 AS B ON B~LIFNR = A~LIFNR
                     INNER JOIN CDHDR AS C
                     ON   C~OBJECTCLAS = 'KRED'
                     AND  C~OBJECTID = B~LIFNR
                     AND  C~UDATE >= @IV_DATE_FROM
                     AND  ( C~TCODE = 'XK01' OR C~TCODE = 'XK02' )
                     FOR ALL ENTRIES IN @MT_PERNR
                     WHERE B~PERNR = @MT_PERNR-TABLE_LINE
                     AND   B~BUKRS IN @IT_BUKRS_RANGE
             INTO TABLE @MT_LIFNR_PERNR.

      "Get infotype 0009 with date starting from modification date to today
      SELECT DISTINCT A~LIFNR, A~NAME1, P~PERNR FROM PA0009 AS P
                      INNER JOIN LFB1 AS B ON B~PERNR = P~PERNR
                      INNER JOIN LFA1 AS A ON A~LIFNR = B~LIFNR
                      FOR ALL ENTRIES IN @MT_PERNR
                      WHERE P~PERNR = @MT_PERNR-TABLE_LINE
                      AND   B~BUKRS IN @IT_BUKRS_RANGE
                      AND   BEGDA >= @IV_DATE_FROM
                      AND   BEGDA <= @SY-DATUM
             APPENDING TABLE @MT_LIFNR_PERNR.

      "Get infotype 0009 modified from date
      SELECT DISTINCT CAST( SUBSTRING( P4~SRTFD,2,8 ) AS NUMC( 8 ) ) AS PERNR FROM PCL4 AS P4
                 WHERE P4~RELID = 'LA'
                 AND   P4~AEDTM >= @IV_DATE_FROM
                 AND   SUBSTRING( P4~SRTFD,10,4 ) = '0009'
                 INTO TABLE @LT_PERNR.
      "Filter LT_PERNR with PERNR from selection-screen
      LOOP AT LT_PERNR INTO DATA(LV_PERNR).
        READ TABLE MT_PERNR TRANSPORTING NO FIELDS WITH KEY TABLE_LINE = LV_PERNR.
        IF SY-SUBRC <> 0.
          DELETE LT_PERNR.
        ENDIF.
      ENDLOOP.

    ELSE.
      LT_PERNR = MT_PERNR.
    ENDIF.

    "add to table MT_LIFNR_PERNR
    IF LT_PERNR IS NOT INITIAL.
      SELECT DISTINCT A~LIFNR, A~NAME1, B~PERNR FROM LFA1 AS A
                      INNER JOIN LFB1 AS B ON B~LIFNR = A~LIFNR
                      FOR ALL ENTRIES IN @LT_PERNR
                      WHERE B~PERNR = @LT_PERNR-TABLE_LINE
                      AND   B~BUKRS IN @IT_BUKRS_RANGE
             APPENDING TABLE @MT_LIFNR_PERNR.
    ENDIF.

    SORT MT_LIFNR_PERNR.
    DELETE ADJACENT DUPLICATES FROM MT_LIFNR_PERNR.

    "Align bank from infotype 0009
    LOOP AT MT_LIFNR_PERNR INTO DATA(LS_LIFNR_PERNR).
      CLEAR: LT_LFBK_BANK, LT_0009_BANK, LT_BANK_CURRENCY, LT_CURRENCY.
      DATA(LT_STATUS) = GET_IT0009_SUBTY_STATUS( IV_PERNR = LS_LIFNR_PERNR-PERNR
                                                 IV_DATE  = IV_DATE_REF ).
      "Get vendor banks
      ME->GET_VENDOR_BANKS( EXPORTING IV_LIFNR = LS_LIFNR_PERNR-LIFNR
                            IMPORTING ET_BANK = LT_LFBK_BANK
                                      ET_BANK_CURRENCY = LT_BANK_CURRENCY
                                      ET_CURRENCY = LT_CURRENCY ).
      ME->GET_EMPLOYEE_BANKS( EXPORTING IT_STATUS = LT_STATUS
                              IMPORTING ET_BANK = LT_0009_BANK ).
      IF LT_LFBK_BANK <> LT_0009_BANK.
        "Set vendor header to file data
        APPEND ME->SET_BLF00( IV_LIFNR = LS_LIFNR_PERNR-LIFNR ) TO MT_STRING.
        "Delete vendor bank
        LOOP AT LT_LFBK_BANK INTO LS_BANK.
          APPEND ME->SET_BLFBK( IS_BANK = LS_BANK IV_DELETE = ABAP_TRUE ) TO MT_STRING.
        ENDLOOP.
        "Create bank from IT0009
        LOOP AT LT_0009_BANK INTO LS_BANK.
          "Get BVTYP if already exists in vendor bank
          READ TABLE LT_BANK_CURRENCY INTO LS_BANK_CURRENCY WITH KEY BANKS = LS_BANK-BANKS
                                                                     BANKL = LS_BANK-BANKL
                                                                     BANKN = LS_BANK-BANKN
                                                                     BKONT = LS_BANK-BKONT
                                                                     CURRE = LS_BANK-BVTYP.
          IF SY-SUBRC = 0.
            LS_BANK-BVTYP = LS_BANK_CURRENCY-BVTYP.
          ELSE.
            LV_BVTYP = LS_BANK-BVTYP.
            DO.
              "Currency already used ?
              READ TABLE LT_CURRENCY TRANSPORTING NO FIELDS WITH KEY TABLE_LINE = LV_BVTYP.
              IF SY-SUBRC = 0.
                IF LV_BVTYP+3(1) = SPACE.
                  LV_BVTYP+3(1) = LV_NUMBER = 1.
                ELSE.
                  LV_NUMBER = LV_BVTYP+3(1).
                  IF LV_NUMBER = 9.
                    EXIT.
                  ENDIF.
                  ADD 1 TO LV_NUMBER.
                  LV_BVTYP+3(1) = LV_NUMBER.
                ENDIF.
              ELSE.
                APPEND LV_BVTYP TO LT_CURRENCY.
                LS_BANK-BVTYP = LV_BVTYP.
                EXIT.
              ENDIF.
            ENDDO.
          ENDIF.
          APPEND ME->SET_BLFBK( IS_BANK = LS_BANK ) TO MT_STRING.
* EVO BKREF Relevant => check IBAN exists, else to create
*          IF ls_bank-bkref = 'TRAVEL'.
*            DATA(lv_bkref_relevant) = me->check_bkref_relevant_country( iv_banks = ls_bank-banks  ).
*            IF lv_bkref_relevant = abap_true.
*
*              lv_bankn35  = ls_bank-bankn .
*
*              me->get_iban(
*                EXPORTING
*                  iv_banks  = ls_bank-banks     " Bank Country Key
*                  iv_bankl  = ls_bank-bankl     " Bank Number
*                  iv_bankn  = lv_bankn35         " Bank account number
*                  iv_bkont  = ls_bank-bkont      " Bank Control Key
*                  iv_bkref  = ''            " blank
*                  iv_travel = 'X'
*                IMPORTING
*                  ev_subrc  = lv_subrc           " ABAP System Field: Return Code of ABAP Statements
*                  ev_iban   = lv_iban            " IBAN (International Bank Account Number)
*              ).
*
**     create IBAN with reference field
*              IF lv_subrc NE 0 AND lv_iban IS NOT INITIAL.
*                CONCATENATE ls_bank-bankn 'TRAVEL' INTO lv_bankn35.
*                IF me->mv_update = abap_true.
*                  me->bapi_iban_create(
*                    EXPORTING
*                      iv_banks   =  ls_bank-banks    " Bank Country Key
*                      iv_bankl   =  ls_bank-bankl    " Bank Number
*                      iv_bankn   =  lv_bankn35        " Bank account number
*                      iv_bkont   =  ls_bank-bkont    " Bank Control Key
*                      iv_iban    =  lv_iban           " IBAN (International Bank Account Number)
**               iv_tabname = 'LFBK'             " Table name, 16 characters
*                      iv_pernr   =  ls_lifnr_pernr-pernr   " Personnel number
*                      iv_begda   =  sy-datum    " Start Date
*                    IMPORTING
*                      rs_return  =  ls_return
*                  ).
*                ENDIF.
*              ENDIF.
*            ENDIF.
*          ENDIF.
* END EVO BKREF Relevant => check IBAN exists, else to create
        ENDLOOP.
      ELSE.   "No bank Update
        DELETE MT_LIFNR_PERNR.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CM00R ----
  METHOD UPDATE_VENDOR.

    DATA LV_STRING TYPE STRING.
    DATA LV_MESSAGE TYPE STRING.
    DATA LT_ABAP_LIST TYPE TABLE OF ABAPLIST.

    CHECK MT_STRING IS NOT INITIAL.

    OPEN DATASET IV_FILE IN TEXT MODE FOR OUTPUT
                         ENCODING DEFAULT
                         MESSAGE LV_MESSAGE.
    IF SY-SUBRC <> 0.
      MESSAGE LV_MESSAGE TYPE 'E'.
    ELSE.
      "set file header
      LV_STRING = ME->SET_BGR00( IV_GROUP = IV_GROUP ).
      TRANSFER LV_STRING TO IV_FILE.
      "set vendor to update
      LOOP AT MT_STRING INTO LV_STRING.
        TRANSFER LV_STRING TO IV_FILE.
      ENDLOOP.
      "Close file
      CLOSE DATASET IV_FILE.
    ENDIF.

    IF MV_UPDATE = ABAP_FALSE.    "Test mode
      SUBMIT RFBIKR00 AND RETURN
                      WITH DS_NAME = IV_FILE
                      WITH FL_CHECK = ABAP_TRUE
                      WITH XLOG = ABAP_TRUE EXPORTING LIST TO MEMORY.
    ELSE. "Update mode
      SUBMIT RFBIKR00 AND RETURN
                      WITH DS_NAME = IV_FILE
                      WITH FL_CHECK = ABAP_FALSE
                      WITH XINF = ABAP_TRUE EXPORTING LIST TO MEMORY.
    ENDIF.

    CALL FUNCTION 'LIST_FROM_MEMORY'
      TABLES
        LISTOBJECT = LT_ABAP_LIST
      EXCEPTIONS
        NOT_FOUND  = 1
        OTHERS     = 2.

    CHECK SY-SUBRC = 0.

    CALL FUNCTION 'WRITE_LIST'
      TABLES
        LISTOBJECT = LT_ABAP_LIST
      EXCEPTIONS
        EMPTY_LIST = 1
        OTHERS     = 2.

  ENDMETHOD.

* ---- YCL_FI_PRAA_BL================CO ----
PROTECTED SECTION.

* ---- YCL_FI_PRAA_BL================CU ----
CLASS YCL_FI_PRAA_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  DATA MV_NO_MODIF_SCAN TYPE BOOLEAN .
  DATA MT_P0009 TYPE P0009_TAB .
  DATA MT_PERNR TYPE PERNR_TAB .
  DATA MV_REPID TYPE SY-REPID .
  DATA MV_UPDATE TYPE BOOLEAN .

  METHODS UPDATE_VENDOR
    IMPORTING
      !IV_GROUP TYPE APQ_GRPN
      !IV_FILE TYPE RFBIFILE .
  METHODS IS_EXCLUDED_PERNR
    IMPORTING
      !IV_PERNR TYPE P_PERNR
    RETURNING
      VALUE(RV_EXCLUDED) TYPE BOOLEAN .
  METHODS GET_VENDOR_TO_EXTEND_COMP_CODE
    IMPORTING
      !IT_BUKRS_RANGE TYPE YTT_BUKRS_RANGE OPTIONAL
      !IV_DATE_REF TYPE DATUM DEFAULT SY-DATUM
      !IV_DATE_FROM TYPE DATUM
      !IV_BUKRS_TARGET TYPE BUKRS .
  METHODS GET_VENDOR_TO_MODIFY_BANK
    IMPORTING
      !IT_BUKRS_RANGE TYPE YTT_BUKRS_RANGE OPTIONAL
      !IV_DATE_REF TYPE DATUM DEFAULT SY-DATUM
      !IV_DATE_FROM TYPE DATUM .
  METHODS GET_IT0009_SUBTY_STATUS
    IMPORTING
      !IV_PERNR TYPE P_PERNR
      !IV_DATE TYPE DATUM DEFAULT SY-DATUM
    RETURNING
      VALUE(RT_STATUS) TYPE YTTHR_SUBTY_TRAVEL .
  METHODS GET_COUNTRY_PROPERTIES
    IMPORTING
      !IV_LAND1 TYPE LAND1
    RETURNING
      VALUE(RS_PROP) TYPE YTFI_PRAA_CTRY .
  METHODS GET_ASSIGNMENT
    IMPORTING
      !IV_PERNR TYPE P_PERNR
      !IV_DATE TYPE DATUM DEFAULT SY-DATUM
    EXPORTING
      !EV_ENAME TYPE EMNAM
      !EV_PERSG TYPE PERSG .
  METHODS DISPLAY_ALV
    IMPORTING
      !IV_TABNAME TYPE LVC_FNAME
      !IV_TITLE TYPE LVC_TITLE
      !IV_LABEL_TEST TYPE LVC_TITLE
      !IV_LABEL_UPD TYPE LVC_TITLE
      !IV_SORT_FIELD TYPE LVC_FNAME OPTIONAL .
  METHODS DELIMIT_BANK_DATA
    IMPORTING
      !IT_PERNR TYPE PERNR_TAB
      !IV_SUBTY TYPE SUBTY
      !IV_ENDDA TYPE ENDDA .
  METHODS CONSTRUCTOR .
  CLASS-METHODS GET_INSTANCE
    IMPORTING
      !IV_CLASSNAME TYPE CLASSNAME DEFAULT 'YCL_FI_PRAA_BL'
    RETURNING
      VALUE(RO_INSTANCE) TYPE REF TO YCL_FI_PRAA_BL .