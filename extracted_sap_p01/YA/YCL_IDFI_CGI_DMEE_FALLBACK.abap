* ==== CLASS POOL YCL_IDFI_CGI_DMEE_FALLBACK ====
CLASS-POOL .
*"* class pool for class YCL_IDFI_CGI_DMEE_FALLBACK

*"* local type definitions
INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CCDEF.

*"* class YCL_IDFI_CGI_DMEE_FALLBACK definition
*"* public declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CU.
*"* protected declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CO.
*"* private declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CI.
ENDCLASS. "YCL_IDFI_CGI_DMEE_FALLBACK definition

*"* macro definitions
INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CCMAC.
*"* local class implementation
INCLUDE YCL_IDFI_CGI_DMEE_FALLBACK====CCIMP.

CLASS YCL_IDFI_CGI_DMEE_FALLBACK IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IDFI_CGI_DMEE_FALLBACK implementation


* ---- YCL_IDFI_CGI_DMEE_FALLBACK====CI ----
PRIVATE SECTION.

  CLASS-DATA MO_INSTANCE TYPE REF TO YCL_IDFI_CGI_DMEE_FALLBACK .
  DATA MV_CDTR_NAME TYPE TEXT100 .
  DATA MV_FPAYH TYPE FPAYH .

* ---- YCL_IDFI_CGI_DMEE_FALLBACK====CM001 ----
  METHOD GET_CREDIT.

******* Put here tag redefinition for FALLBACK class (general case)
******* For country specific redefinition tag, use DMEE VGI country BADI

    CASE I_NODE_PATH.

*      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
**       this node holds the value of the Clearing system member ID
*        IF i_fpayh-zbnkl IS NOT INITIAL.
*          c_value = i_fpayh-zbnkl.
*        ELSE.
**          c_value = i_fpayh-zbnky.
*          CLEAR c_value.
*        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
        "If payment origin is TR-CM-BT, then put item text to this tag
        IF I_FPAYP-ORIGIN = 'TR-CM-BT'.
          C_VALUE = I_FPAYP-SGTXT.
        ENDIF.
        "Only 35 first characters, remaining characters must be set in tag <StrtNm>
        MV_CDTR_NAME = C_VALUE.
        IF C_VALUE+35 IS NOT INITIAL.
          CLEAR C_VALUE+35.
        ENDIF.
        MV_FPAYH = I_FPAYH.   "Set to buffer for tag <StrtNm>

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
        IF I_FPAYH = MV_FPAYH AND MV_CDTR_NAME+35 IS NOT INITIAL.
          C_VALUE = |{ MV_CDTR_NAME+35 } { C_VALUE }|.
        ENDIF.
        IF C_VALUE+70 IS NOT INITIAL.
          CLEAR C_VALUE+70.
        ENDIF.

    ENDCASE.

  ENDMETHOD.

* ---- YCL_IDFI_CGI_DMEE_FALLBACK====CM002 ----
  METHOD GET_INSTANCE.

    IF MO_INSTANCE IS INITIAL.
      MO_INSTANCE = NEW YCL_IDFI_CGI_DMEE_FALLBACK( ).
    ENDIF.

    RO_INSTANCE = MO_INSTANCE.

  ENDMETHOD.

* ---- YCL_IDFI_CGI_DMEE_FALLBACK====CO ----
PROTECTED SECTION.

* ---- YCL_IDFI_CGI_DMEE_FALLBACK====CU ----
CLASS YCL_IDFI_CGI_DMEE_FALLBACK DEFINITION
  PUBLIC
  CREATE PUBLIC .

PUBLIC SECTION.

  CLASS-METHODS GET_INSTANCE
    RETURNING
      VALUE(RO_INSTANCE) TYPE REF TO YCL_IDFI_CGI_DMEE_FALLBACK .
  METHODS GET_CREDIT
    IMPORTING
      !FLT_VAL_DEBIT_OR_CREDIT TYPE ANY
      !FLT_VAL_COUNTRY TYPE INTCA
      !I_TREE_ID TYPE DMEE_TREEID_ABA
      !I_TREE_TYPE TYPE DMEE_TREETYPE_ABA
      !I_PARAM TYPE ANY
      !I_UPARAM TYPE ANY
      !I_EXTENSION TYPE DMEE_EXIT_INTERFACE_ABA
      !I_FPAYH TYPE FPAYH
      !I_FPAYHX TYPE FPAYHX
      !I_FPAYP TYPE FPAYP
      !I_ROOT_NODES TYPE STRING
      !I_NODE_PATH TYPE STRING
    CHANGING
      !C_VALUE TYPE ANY
      !O_VALUE TYPE ANY
      !N_VALUE TYPE ANY
      !P_VALUE TYPE ANY .