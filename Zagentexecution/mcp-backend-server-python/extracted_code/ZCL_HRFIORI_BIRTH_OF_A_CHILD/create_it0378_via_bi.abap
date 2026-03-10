  METHOD create_it0378_via_bi.

    DATA: lv_fval       TYPE bdc_fval,
          lv_timestamp1 TYPE syst_uzeit,
          lv_timestamp2 TYPE syst_uzeit,
          ls_apqi       TYPE apqi,
          lt_bdcdata    TYPE tt_bdcdata,
          lt_apqi       TYPE STANDARD TABLE OF apqi.

*   Open session
    CALL FUNCTION 'BDC_OPEN_GROUP'
      EXPORTING
        client = sy-mandt
        group  = 'IT0378_CREAT'
        keep   = 'X'
        user   = sy-uname
      EXCEPTIONS
        OTHERS = 11.

*   Prepare BDC data
*   First screen
    bdc_dynpro( EXPORTING iv_program = 'SAPMP50A'
                          iv_dynpro  = '1000'
                          iv_dynbegin = 'X'
                CHANGING  ct_bdcdata = lt_bdcdata ).

    CLEAR: lv_fval.
    MOVE iv_pernr TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'RP50G-PERNR'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).
    bdc_field( EXPORTING iv_fnam = 'BDC_OKCODE'
                         iv_fval = '/00'
                CHANGING ct_bdcdata = lt_bdcdata ).

    bdc_field( EXPORTING iv_fnam = 'RP50G-TIMR6'
                         iv_fval = 'X'
                CHANGING ct_bdcdata = lt_bdcdata ).
    bdc_field( EXPORTING iv_fnam = 'BDC_OKCODE'
                         iv_fval = '/00'
                CHANGING ct_bdcdata = lt_bdcdata ).

    CLEAR: lv_fval.
    WRITE iv_begda TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'RP50G-BEGDA'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).
    CLEAR: lv_fval.
    WRITE iv_endda TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'RP50G-ENDDA'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).

    bdc_field( EXPORTING iv_fnam = 'RP50G-CHOIC'
                         iv_fval = '378'
                CHANGING ct_bdcdata = lt_bdcdata ).
    bdc_field( EXPORTING iv_fnam = 'RP50G-SUBTY'
                         iv_fval = 'CHIL'
                CHANGING ct_bdcdata = lt_bdcdata ).
    bdc_field( EXPORTING iv_fnam = 'BDC_OKCODE'
                         iv_fval = '=INS'
                CHANGING ct_bdcdata = lt_bdcdata ).

*   Second screen
    bdc_dynpro( EXPORTING iv_program = 'MP037800'
                          iv_dynpro  = '2000'
                          iv_dynbegin = 'X'
                CHANGING  ct_bdcdata = lt_bdcdata ).

    CLEAR: lv_fval.
    WRITE iv_begda TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'P0378-BEGDA'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).
    CLEAR: lv_fval.
    WRITE iv_endda TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'P0378-ENDDA'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).

    CLEAR: lv_fval.
    MOVE iv_event TO lv_fval.
    bdc_field( EXPORTING iv_fnam = 'P0378-EVENT'
                         iv_fval = lv_fval
                CHANGING ct_bdcdata = lt_bdcdata ).
    bdc_field( EXPORTING iv_fnam = 'BDC_OKCODE'
                         iv_fval = '=UPD'
                CHANGING ct_bdcdata = lt_bdcdata ).

*   Create batch input folder
    CALL FUNCTION 'BDC_INSERT'
      EXPORTING
        tcode     = 'PA30'
      TABLES
        dynprotab = lt_bdcdata
      EXCEPTIONS
        OTHERS    = 7.

*   Close folder
    CALL FUNCTION 'BDC_CLOSE_GROUP'.

**   We submit the batch input
    lv_timestamp1 = sy-uzeit.
    lv_timestamp2 = lv_timestamp1 + 3.
    SUBMIT rsbdcsub
      WITH mappe EQ 'IT0378_CREAT'
      WITH von EQ sy-datum
      WITH bis EQ sy-datum
      WITH fehler EQ ' '
      WITH z_verarb = 'X'
      EXPORTING LIST TO MEMORY
      AND RETURN.
*
**   We get batch input status.
*    CALL FUNCTION 'BDC_OBJECT_SELECT'
*      EXPORTING
*        name      = 'IT0378_CREAT'
*        datatype  = 'BDC'
*        client    = sy-mandt
*        date_from = sy-datum
*        date_to   = sy-datum
*        time_from = lv_timestamp1
*        time_to   = lv_timestamp2
**       QSTATE    = '*'
**       SESSION_CREATOR        = '*'
**       UP_TO_N_ROWS           = 0
*      TABLES
*        apqitab   = lt_apqi
**       GROUPSEL  =
**     EXCEPTIONS
**       INVALID_DATATYPE       = 1
**       OTHERS    = 2
*      .
*
*    READ TABLE lt_apqi INTO ls_apqi INDEX 1.
*    IF ls_apqi-qstate = 'F'.
*      ov_subrc = 0.
*    ELSE.
*      ov_subrc = 4.
*      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '019'
*        INTO ov_message.
*    ENDIF.


  ENDMETHOD.
