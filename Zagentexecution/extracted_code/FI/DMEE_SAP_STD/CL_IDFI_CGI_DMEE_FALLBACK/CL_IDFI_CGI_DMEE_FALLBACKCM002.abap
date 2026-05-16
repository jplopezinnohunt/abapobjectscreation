  METHOD INITIALIZE.
*   Logic of this FM is called at the first run of the BAdI call
*   AND for each new payment (after FPAYH/HX changes) shotrcuts will be filled. \
    CONSTANTS:                                                 "n2699168
      LC_FIELD_UETR_SWITCH TYPE FIELDNAME VALUE 'UETR_SWITCH', "n2699168
      LC_FIELD_UETR        TYPE FIELDNAME VALUE 'UETR'.        "n2699168

    FIELD-SYMBOLS:                                             "n2699168
      <FS_UETR_SWITCH>     TYPE ANY,                           "n2699168
      <FS_UETR>            TYPE ANY.                           "n2699168

*   initialize shortcuts parameters
    IF MV_IS_INITIALIZED IS INITIAL.
*     Content of this IF statement holds the selects which will be done only once.

*     Initialize CGI values. they are used in conditions and as values in some nodes
      CL_IDFI_CGI_DMEE_UTILS=>GET_CGI_XML_VALUES(
        EXPORTING
          IV_BUKRS  = I_FPAYP-BUKRS
          IV_ZBUKR  = I_FPAYH-ZBUKR
        IMPORTING
          EV_CGIID  = MV_CGIID
          EV_CGIIR  = MV_CGIIR
          EV_CGIPRT = MV_CGIPRT
          EV_CGICD = MV_CGICD                               "n2893975
      ).
*     don't forget to set the mv_is_initialized to abap_true :)
      MV_IS_INITIALIZED = ABAP_TRUE.

*     Usage measurement not on SAP systems - n2330563
      IF CL_IDFI_CGI_DMEE_UTILS=>IS_SAP_SYSTEM( ) EQ ABAP_FALSE.
        DATA LR_CGI_USAGE TYPE REF TO CL_IDFI_CGI_DMEE_USAGE.
        LR_CGI_USAGE = CL_IDFI_CGI_DMEE_USAGE=>GET_INSTANCE( ).
        IF LR_CGI_USAGE IS BOUND.
          CALL METHOD LR_CGI_USAGE->CALL_USAGE_INSERT.
        ENDIF.
      ENDIF. "Usage measurement not on SAP systems - n2330563
    ENDIF.

    CLEAR:
      MV_IS_SEPA_PAYMENT,
      MV_IS_HR_PAYMENT,
      MV_IS_CHECK_PAYMENT,
      MV_IS_BANK2BANK_TRANSFER,                           "n2283292
      MV_UETR,                                            "n2699168
      MV_IS_UETR_SWITCHED.                                "n2699168

*   Fill Shortcuts for the current payment
    IF I_FPAYHX-REF03+0(1) EQ GC_SEPA_FLG.                "n2533796
      MV_IS_SEPA_PAYMENT = ABAP_TRUE.
    ENDIF.

    IF I_FPAYH-DORIGIN EQ GC_HR_PY.
      MV_IS_HR_PAYMENT = ABAP_TRUE.
    ENDIF.

    IF I_FPAYHX-XSCHK EQ ABAP_TRUE.
      MV_IS_CHECK_PAYMENT = ABAP_TRUE.
    ENDIF.

    IF I_FPAYH-DORIGIN EQ GC_TR_CM_BT.                  "n2283292
      MV_IS_BANK2BANK_TRANSFER = ABAP_TRUE.             "n2283292
    ENDIF.                                              "n2283292

*   Get format parameters
    MS_FORMAT_PARAMS = CL_IDFI_CGI_DMEE_UTILS=>GET_FORMAT_PARAMETERS( ).

*   <<< Beginig of Note 2699168
*   Check for SWIFT gpi UETR - Unique End-to-End Transaction Reference
    ASSIGN COMPONENT LC_FIELD_UETR_SWITCH OF STRUCTURE MS_FORMAT_PARAMS
        TO <FS_UETR_SWITCH>.
    IF SY-SUBRC EQ 0.
      MV_IS_UETR_SWITCHED = <FS_UETR_SWITCH>.
      IF MV_IS_UETR_SWITCHED EQ ABAP_TRUE.
        ASSIGN COMPONENT LC_FIELD_UETR OF STRUCTURE I_FPAYH
            TO <FS_UETR>.
        IF SY-SUBRC EQ 0 AND <FS_UETR> IS NOT INITIAL.
          MV_UETR = <FS_UETR>.
        ELSE.
*         UETR is on only when it is in all structures and has value
          CLEAR MV_IS_UETR_SWITCHED.
        ENDIF. "IF sy-subrc EQ 0.
      ENDIF. "IF mv_is_uetr_switched EQ abap_true.
    ENDIF. "IF sy-subrc EQ 0.
*   >>> End of Note 2699168

*   Retrieves payment area
    CL_IDFI_CGI_DMEE_UTILS=>GET_AREA(
      EXPORTING
        IS_FPAYH     = I_FPAYH
      IMPORTING
        EV_AREA      = MV_AREA
        ).
  ENDMETHOD.