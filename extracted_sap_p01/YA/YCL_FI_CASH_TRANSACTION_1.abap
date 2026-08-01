* ==== CLASS POOL YCL_FI_CASH_TRANSACTION_1 ====
CLASS-POOL .
*"* class pool for class YCL_FI_CASH_TRANSACTION_1

*"* local type definitions
INCLUDE YCL_FI_CASH_TRANSACTION_1=====CCDEF.

*"* class YCL_FI_CASH_TRANSACTION_1 definition
*"* public declarations
  INCLUDE YCL_FI_CASH_TRANSACTION_1=====CU.
*"* protected declarations
  INCLUDE YCL_FI_CASH_TRANSACTION_1=====CO.
*"* private declarations
  INCLUDE YCL_FI_CASH_TRANSACTION_1=====CI.
ENDCLASS. "YCL_FI_CASH_TRANSACTION_1 definition

*"* macro definitions
INCLUDE YCL_FI_CASH_TRANSACTION_1=====CCMAC.
*"* local class implementation
INCLUDE YCL_FI_CASH_TRANSACTION_1=====CCIMP.

CLASS YCL_FI_CASH_TRANSACTION_1 IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_CASH_TRANSACTION_1 implementation


* ---- YCL_FI_CASH_TRANSACTION_1=====CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_BSEG,
      BUKRS TYPE BSEG-BUKRS,
      BELNR TYPE BSEG-BELNR,
      GJAHR TYPE BSEG-GJAHR,
      BUZEI TYPE BSEG-BUZEI,
      BSCHL TYPE BSEG-BSCHL,
      HKONT TYPE BSEG-HKONT,
      TXT20 TYPE SKAT-TXT20,
      BUDAT TYPE BKPF-BUDAT,
      GSBER TYPE BSEG-GSBER,
      SHKZG TYPE BSEG-SHKZG,
      WRBTR TYPE BSEG-WRBTR,
      WAERS TYPE BKPF-WAERS,
      DMBTR TYPE BSEG-DMBTR,
      HWAER TYPE BKPF-HWAER,
    END OF TY_BSEG .

  DATA MV_REPID TYPE SY-REPID .
  DATA:
    MT_BSEG TYPE TABLE OF TY_BSEG .
  DATA MO_COLUMNS TYPE REF TO CL_SALV_COLUMNS_TABLE .
  DATA MO_FUNCTIONS TYPE REF TO CL_SALV_FUNCTIONS_LIST .
  DATA MO_SALV_TABLE TYPE REF TO CL_SALV_TABLE .
  DATA MO_LAYOUT TYPE REF TO CL_SALV_LAYOUT .

* ---- YCL_FI_CASH_TRANSACTION_1=====CM001 ----
  METHOD EXTRACT_DATA.

    TYPES: BEGIN OF LTY_BELNR,
             BUKRS TYPE BKPF-BUKRS,
             BELNR TYPE BKPF-BELNR,
             GJAHR TYPE BKPF-GJAHR,
           END OF LTY_BELNR.

    DATA LT_BELNR TYPE TABLE OF LTY_BELNR.

    "Extract all documents from selection criterias
    SELECT DISTINCT H~BUKRS,
                    H~BELNR,
                    H~GJAHR
               FROM BKPF AS H
               INNER JOIN BSEG AS I ON  I~BUKRS = H~BUKRS
                                    AND I~BELNR = H~BELNR
                                    AND I~GJAHR = H~GJAHR
               WHERE H~BUKRS = @IV_BUKRS
               AND   H~BUDAT IN @IT_BUDAT_RANGE
               AND   H~WAERS IN @IT_WAERS_RANGE
               AND   I~HKONT IN @IT_HKONT_RANGE
               INTO TABLE @LT_BELNR.

    SORT LT_BELNR.
    CHECK LT_BELNR IS NOT INITIAL.

    "extract all items document which are out of g/L account selection
    SELECT DISTINCT H~BUKRS,
                    H~BELNR,
                    H~GJAHR,
                    I~BUZEI,
                    I~BSCHL,
                    I~HKONT,
                    T~TXT20,
                    H~BUDAT,
                    I~GSBER,
                    I~SHKZG,
                    I~WRBTR,
                    H~WAERS,
                    I~DMBTR,
                    H~HWAER
           FROM BKPF AS H
           INNER JOIN BSEG AS I ON  I~BUKRS = H~BUKRS
                                AND I~BELNR = H~BELNR
                                AND I~GJAHR = H~GJAHR
           LEFT OUTER JOIN T001 AS B ON B~BUKRS = H~BUKRS
           LEFT OUTER JOIN SKAT AS T ON  T~SPRAS = @SY-LANGU
                                     AND T~KTOPL = B~KTOPL
                                     AND T~SAKNR = I~HKONT
           FOR ALL ENTRIES IN @LT_BELNR
           WHERE H~BUKRS = @LT_BELNR-BUKRS
           AND   H~BELNR = @LT_BELNR-BELNR
           AND   H~GJAHR = @LT_BELNR-GJAHR
           AND   H~BUDAT IN @IT_BUDAT_RANGE
           AND   H~WAERS IN @IT_WAERS_RANGE
           AND   I~HKONT NOT IN @IT_HKONT_RANGE
           INTO TABLE @MT_BSEG.

    "Set debit / credit
    LOOP AT MT_BSEG ASSIGNING FIELD-SYMBOL(<LS_BSEG>) WHERE SHKZG = 'H'.
      <LS_BSEG>-WRBTR = <LS_BSEG>-WRBTR * -1.
      <LS_BSEG>-DMBTR = <LS_BSEG>-DMBTR * -1.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_CASH_TRANSACTION_1=====CM002 ----
  METHOD DISPLAY_ALV.

*    DATA lo_alv TYPE REF TO yif_alv_display.
*
*    lo_alv = ycl_alv_factory=>get_instance( ).
*    lo_alv->init_alv( CHANGING it_table = mt_bseg ).
*    lo_alv->set_main_functions( EXPORTING iv_report = iv_repid
*                                          iv_title = 'Offsetting entries' ).
*
*    lo_alv->display_alv( ).

    DATA LS_LAYOUT_KEY TYPE SALV_S_LAYOUT_KEY.

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
            T_TABLE      = MT_BSEG.
      CATCH CX_SALV_MSG .
    ENDTRY.

    "ALV functions activation
    MO_FUNCTIONS = MO_SALV_TABLE->GET_FUNCTIONS( ).
    MO_FUNCTIONS->SET_ALL( ).

    "ALV layout
    MO_LAYOUT = MO_SALV_TABLE->GET_LAYOUT( ).
    LS_LAYOUT_KEY-REPORT = MV_REPID.
    MO_LAYOUT->SET_KEY( LS_LAYOUT_KEY ).
    MO_LAYOUT->SET_SAVE_RESTRICTION( IF_SALV_C_LAYOUT=>RESTRICT_NONE ).
    MO_LAYOUT->SET_INITIAL_LAYOUT( '/STANDARD' ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.

* ---- YCL_FI_CASH_TRANSACTION_1=====CO ----
PROTECTED SECTION.

* ---- YCL_FI_CASH_TRANSACTION_1=====CU ----
CLASS YCL_FI_CASH_TRANSACTION_1 DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  METHODS DISPLAY_ALV
    IMPORTING
      !IV_REPID TYPE SY-REPID .
  METHODS EXTRACT_DATA
    IMPORTING
      !IV_BUKRS TYPE BUKRS
      !IT_HKONT_RANGE TYPE YTTFI_HKONT_RANGE
      !IT_BUDAT_RANGE TYPE RANGES_BUDAT_TT
      !IT_WAERS_RANGE TYPE BUKU_T_RTCURR .