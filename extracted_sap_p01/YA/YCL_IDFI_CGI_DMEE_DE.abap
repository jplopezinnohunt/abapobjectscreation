* ==== CLASS POOL YCL_IDFI_CGI_DMEE_DE ====
CLASS-POOL .
*"* class pool for class YCL_IDFI_CGI_DMEE_DE

*"* local type definitions
INCLUDE YCL_IDFI_CGI_DMEE_DE==========CCDEF.

*"* class YCL_IDFI_CGI_DMEE_DE definition
*"* public declarations
  INCLUDE YCL_IDFI_CGI_DMEE_DE==========CU.
*"* protected declarations
  INCLUDE YCL_IDFI_CGI_DMEE_DE==========CO.
*"* private declarations
  INCLUDE YCL_IDFI_CGI_DMEE_DE==========CI.
ENDCLASS. "YCL_IDFI_CGI_DMEE_DE definition

*"* macro definitions
INCLUDE YCL_IDFI_CGI_DMEE_DE==========CCMAC.
*"* local class implementation
INCLUDE YCL_IDFI_CGI_DMEE_DE==========CCIMP.

CLASS YCL_IDFI_CGI_DMEE_DE IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IDFI_CGI_DMEE_DE implementation


* ---- YCL_IDFI_CGI_DMEE_DE==========CI ----
PRIVATE SECTION.

* ---- YCL_IDFI_CGI_DMEE_DE==========CM001 ----
  METHOD GET_CREDIT.

    CASE I_NODE_PATH.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
*       this node holds the value of the Clearing system member ID
        IF I_FPAYH-ZBNKL IS NOT INITIAL.
          C_VALUE = I_FPAYH-ZBNKL.
        ELSE.
          "c_value = i_fpayh-zbnky.
          CLEAR C_VALUE.
        ENDIF.

      WHEN OTHERS.
*       call the generic functionality
        SUPER->GET_CREDIT(
          EXPORTING
            FLT_VAL_DEBIT_OR_CREDIT =  FLT_VAL_DEBIT_OR_CREDIT
            FLT_VAL_COUNTRY         =  FLT_VAL_COUNTRY            " Country ISO code
            I_TREE_ID               =  I_TREE_ID                  " DMEE:  ID for a DMEE format tree
            I_TREE_TYPE             =  I_TREE_TYPE                " DMEE: tree type
            I_PARAM                 =  I_PARAM
            I_UPARAM                =  I_UPARAM
            I_EXTENSION             =  I_EXTENSION                " DMEE: Extended Interface for Exit Module
            I_FPAYH                 =  I_FPAYH                    " Payment medium: Payment data
            I_FPAYHX                =  I_FPAYHX                   " Payment Medium: Prepared Data for Payment
            I_FPAYP                 =  I_FPAYP                    " Payment medium: Data on paid items
            I_ROOT_NODES            =  I_ROOT_NODES
            I_NODE_PATH             =  I_NODE_PATH
          CHANGING
            C_VALUE                 =  C_VALUE
            O_VALUE                 =  O_VALUE
            N_VALUE                 =  N_VALUE
            P_VALUE                 =  P_VALUE
        ).
    ENDCASE.

  ENDMETHOD.

* ---- YCL_IDFI_CGI_DMEE_DE==========CO ----
PROTECTED SECTION.

  METHODS GET_CREDIT
    REDEFINITION .

* ---- YCL_IDFI_CGI_DMEE_DE==========CU ----
CLASS YCL_IDFI_CGI_DMEE_DE DEFINITION
  PUBLIC
  INHERITING FROM CL_IDFI_CGI_DMEE_DE
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.