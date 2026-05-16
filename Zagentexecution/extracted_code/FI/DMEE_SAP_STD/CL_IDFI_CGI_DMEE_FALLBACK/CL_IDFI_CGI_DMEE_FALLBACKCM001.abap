  METHOD IF_IDFI_CGI_DMEE_COUNTRIES~GET_VALUE.
*   This method handles all nodes which are defined in the CGI_XML_CT and CGI_XML_DD

    DATA:
      LS_WAERS     TYPE STRING,
      LS_EXTENSION  TYPE DMEE_EXIT_INTERFACE_ABA,
      LS_COMP       TYPE ABAP_COMPDESCR,
      LO_ELEMDESCR  TYPE REF TO CL_ABAP_ELEMDESCR,
      LO_STRUCDESCR TYPE REF TO CL_ABAP_STRUCTDESCR.

    FIELD-SYMBOLS:
      <FS_WAERS> TYPE ISOCD.

*   initialize general parameters
    INITIALIZE(
      EXPORTING
        I_FPAYH  = I_FPAYH
        I_FPAYHX = I_FPAYHX
        I_FPAYP  = I_FPAYP
    ).

    CASE FLT_VAL_DEBIT_OR_CREDIT.
      WHEN GC_CREDIT.
        GET_CREDIT(
          EXPORTING
            FLT_VAL_DEBIT_OR_CREDIT = FLT_VAL_DEBIT_OR_CREDIT
            FLT_VAL_COUNTRY         = FLT_VAL_COUNTRY             " Country ISO code
            I_TREE_ID               = I_TREE_ID                   " DMEE:  ID for a DMEE format tree
            I_TREE_TYPE             = I_TREE_TYPE                 " DMEE: tree type
            I_PARAM                 = I_PARAM
            I_UPARAM                = I_UPARAM
            I_EXTENSION             = I_EXTENSION                 " DMEE: Extended Interface for Exit Module
            I_FPAYH                 = I_FPAYH                     " Payment medium: Payment data
            I_FPAYHX                = I_FPAYHX                    " Payment Medium: Prepared Data for Payment
            I_FPAYP                 = I_FPAYP                     " Payment medium: Data on paid items
            I_ROOT_NODES            = I_ROOT_NODES
            I_NODE_PATH             = I_NODE_PATH
          CHANGING
            C_VALUE                 = C_VALUE
            O_VALUE                 = O_VALUE
            N_VALUE                 = N_VALUE
            P_VALUE                 = P_VALUE
        ).
      WHEN GC_DEBIT.
        GET_DEBIT(
          EXPORTING
            FLT_VAL_DEBIT_OR_CREDIT = FLT_VAL_DEBIT_OR_CREDIT
            FLT_VAL_COUNTRY         = FLT_VAL_COUNTRY             " Country ISO code
            I_TREE_ID               = I_TREE_ID                   " DMEE:  ID for a DMEE format tree
            I_TREE_TYPE             = I_TREE_TYPE                 " DMEE: tree type
            I_PARAM                 = I_PARAM
            I_UPARAM                = I_UPARAM
            I_EXTENSION             = I_EXTENSION                 " DMEE: Extended Interface for Exit Module
            I_FPAYH                 = I_FPAYH                     " Payment medium: Payment data
            I_FPAYHX                = I_FPAYHX                    " Payment Medium: Prepared Data for Payment
            I_FPAYP                 = I_FPAYP                     " Payment medium: Data on paid items
            I_ROOT_NODES            = I_ROOT_NODES
            I_NODE_PATH             = I_NODE_PATH
          CHANGING
            C_VALUE                 = C_VALUE
            O_VALUE                 = O_VALUE
            N_VALUE                 = N_VALUE
            P_VALUE                 = P_VALUE
        ).
    ENDCASE.

    IF I_EXTENSION-NODE-MP_SC_TAB IS NOT INITIAL
      AND I_EXTENSION-NODE-MP_SC_FLD IS NOT INITIAL AND
      ( P_VALUE IS NOT INITIAL OR I_EXTENSION-NODE-DATA_TYPE EQ 'P' ). "n2800089
*     The Currency in which is the amount must be entered in the node as
*     Mapping from structure field:
*       Structure & Field Name
*     First check whether type is compatible with ISOCD                "begin of n2960399
      LO_ELEMDESCR ?= CL_ABAP_ELEMDESCR=>DESCRIBE_BY_NAME( GC_ISOCD ).
      LO_STRUCDESCR ?= CL_ABAP_STRUCTDESCR=>DESCRIBE_BY_NAME( I_EXTENSION-NODE-MP_SC_TAB ).

      LOOP AT LO_STRUCDESCR->COMPONENTS INTO LS_COMP
          WHERE  NAME      = I_EXTENSION-NODE-MP_SC_FLD AND
                 TYPE_KIND = LO_ELEMDESCR->TYPE_KIND    AND
                 LENGTH    = LO_ELEMDESCR->LENGTH.

        IF SY-SUBRC = 0.
          CONCATENATE 'I_' I_EXTENSION-NODE-MP_SC_TAB '-' I_EXTENSION-NODE-MP_SC_FLD INTO LS_WAERS.
      ASSIGN (LS_WAERS) TO <FS_WAERS>.
      IF SY-SUBRC EQ 0.
*       Get Amount with Currency (Using Spell_Amount)
        CL_IDFI_CGI_DMEE_UTILS=>AMOUNT_WITH_CURR(             "n2508061
          EXPORTING
            IV_P_VALUE  = P_VALUE
            IV_CURRENCY = <FS_WAERS>
          IMPORTING
            EV_P_VALUE  = P_VALUE
        ).

        CL_IDFI_CGI_DMEE_UTILS=>CONVERT(
          EXPORTING
            IV_N_VALUE   = N_VALUE
            IV_C_VALUE   = C_VALUE
            IV_P_VALUE   = P_VALUE
            IV_CURRENCY  = <FS_WAERS>    " ISO currency code
            IS_EXTENSION = I_EXTENSION    " DMEE: Extended Interface for Exit Module
            IV_NATION    = MS_FORMAT_PARAMS-NATION
          CHANGING
            CV_O_VALUE   = O_VALUE
        ).
         ENDIF.

      ENDIF.
     ENDLOOP.                                                       "end of n2960399

    ELSE.
*     Conversion without currency defined in the DMEE tree
      CL_IDFI_CGI_DMEE_UTILS=>CONVERT(
       EXPORTING
         IV_N_VALUE   = N_VALUE
         IV_C_VALUE   = C_VALUE
         IV_P_VALUE   = P_VALUE
*         iv_currency  = <fs_waers>    " ISO currency code
         IS_EXTENSION = I_EXTENSION    " DMEE: Extended Interface for Exit Module
         IV_NATION    = MS_FORMAT_PARAMS-NATION
       CHANGING
         CV_O_VALUE   = O_VALUE
     ).
    ENDIF.

*   After the conversion the O_VALUE is filled.
*   customers which edit/change only O_VALUE so they clear the value
*   in the postprocessing content stored in N_VALUE, P_VALUE and C_VALUE overwrites this cleared value.
*   which cause unwanted behaviour or the node content
    CLEAR: C_VALUE, N_VALUE, P_VALUE.
*   DO NOT CLEAR THE O_VALUE HERE!!!

  ENDMETHOD.