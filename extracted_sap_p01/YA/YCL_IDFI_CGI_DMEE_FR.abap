* ==== CLASS POOL YCL_IDFI_CGI_DMEE_FR ====
CLASS-POOL .
*"* class pool for class YCL_IDFI_CGI_DMEE_FR

*"* local type definitions
INCLUDE YCL_IDFI_CGI_DMEE_FR==========CCDEF.

*"* class YCL_IDFI_CGI_DMEE_FR definition
*"* public declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FR==========CU.
*"* protected declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FR==========CO.
*"* private declarations
  INCLUDE YCL_IDFI_CGI_DMEE_FR==========CI.
ENDCLASS. "YCL_IDFI_CGI_DMEE_FR definition

*"* macro definitions
INCLUDE YCL_IDFI_CGI_DMEE_FR==========CCMAC.
*"* local class implementation
INCLUDE YCL_IDFI_CGI_DMEE_FR==========CCIMP.

CLASS YCL_IDFI_CGI_DMEE_FR IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IDFI_CGI_DMEE_FR implementation


* ---- YCL_IDFI_CGI_DMEE_FR==========CI ----
PRIVATE SECTION.

* ---- YCL_IDFI_CGI_DMEE_FR==========CM002 ----
  METHOD IF_IDFI_CGI_DMEE_COUNTRIES~GET_VALUE.

    DATA LO_CGI_UTIL TYPE REF TO YCL_IDFI_CGI_DMEE_UTIL.
    DATA LV_SUBRC TYPE SY-SUBRC.

    "Check if tag is redefined with PPC customizing
    LO_CGI_UTIL = NEW YCL_IDFI_CGI_DMEE_UTIL( ).
    LO_CGI_UTIL->GET_TAG_VALUE_FROM_CUSTO( EXPORTING IV_LAND1 = I_FPAYH-ZBNKS
                                                     IV_DEB_CRE = FLT_VAL_DEBIT_OR_CREDIT
                                                     IV_TAG_FULL = I_NODE_PATH
                                                     IS_FPAYH = I_FPAYH
                                                     IS_FPAYHX = I_FPAYHX
                                                     IS_FPAYP = I_FPAYP
                                           IMPORTING EV_SUBRC = LV_SUBRC
                                           CHANGING  CV_VALUE_C = O_VALUE ).

  ENDMETHOD.

* ---- YCL_IDFI_CGI_DMEE_FR==========CO ----
PROTECTED SECTION.

* ---- YCL_IDFI_CGI_DMEE_FR==========CU ----
CLASS YCL_IDFI_CGI_DMEE_FR DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES IF_BADI_INTERFACE .
  INTERFACES IF_IDFI_CGI_DMEE_COUNTRIES .