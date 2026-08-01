* ==== CLASS POOL YCL_IDFI_CGI_DMEE_IT ====
CLASS-POOL .
*"* class pool for class YCL_IDFI_CGI_DMEE_IT

*"* local type definitions
INCLUDE YCL_IDFI_CGI_DMEE_IT==========CCDEF.

*"* class YCL_IDFI_CGI_DMEE_IT definition
*"* public declarations
  INCLUDE YCL_IDFI_CGI_DMEE_IT==========CU.
*"* protected declarations
  INCLUDE YCL_IDFI_CGI_DMEE_IT==========CO.
*"* private declarations
  INCLUDE YCL_IDFI_CGI_DMEE_IT==========CI.
ENDCLASS. "YCL_IDFI_CGI_DMEE_IT definition

*"* macro definitions
INCLUDE YCL_IDFI_CGI_DMEE_IT==========CCMAC.
*"* local class implementation
INCLUDE YCL_IDFI_CGI_DMEE_IT==========CCIMP.

CLASS YCL_IDFI_CGI_DMEE_IT IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IDFI_CGI_DMEE_IT implementation


* ---- YCL_IDFI_CGI_DMEE_IT==========CI ----
PRIVATE SECTION.

* ---- YCL_IDFI_CGI_DMEE_IT==========CM001 ----
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

* ---- YCL_IDFI_CGI_DMEE_IT==========CO ----
PROTECTED SECTION.

  METHODS GET_CREDIT
    REDEFINITION .

* ---- YCL_IDFI_CGI_DMEE_IT==========CU ----
CLASS YCL_IDFI_CGI_DMEE_IT DEFINITION
  PUBLIC
  INHERITING FROM CL_IDFI_CGI_DMEE_IT
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.