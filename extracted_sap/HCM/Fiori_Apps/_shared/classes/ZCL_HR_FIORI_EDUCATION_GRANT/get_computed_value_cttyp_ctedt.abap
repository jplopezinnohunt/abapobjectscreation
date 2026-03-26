  METHOD get_computed_value_cttyp_ctedt.

    DATA: lv_pernr         TYPE persno,
          lv_ctedt         TYPE ctedt,
          lv_fire_date     TYPE dats,
          ls_p0016         TYPE p0016,
          lt_p0000         TYPE STANDARD TABLE OF p0000,
          lt_p0001         TYPE STANDARD TABLE OF p0001,
          lt_p0000_large   TYPE STANDARD TABLE OF p0000,
          lt_p0001_large   TYPE STANDARD TABLE OF p0001,
          lt_p0016         TYPE STANDARD TABLE OF p0016,
          lt_phifi         TYPE STANDARD TABLE OF phifi,
          lo_read_infotype TYPE REF TO if_hrpa_read_infotype,
          lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits.

    IF iv_pernr IS INITIAL.
      CREATE OBJECT lo_benefits_util.
      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.

    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
      IMPORTING
        read_infotype = lo_read_infotype.

*   Get infotypes information
    CALL METHOD cl_hrpa_read_infty_un=>p0000_tab
      EXPORTING
        read_infotype = lo_read_infotype
        tclas         = c_tclas_a
        pernr         = lv_pernr
        begda         = iv_begda
        endda         = iv_endda
      RECEIVING
        p0000         = lt_p0000.
    CALL METHOD cl_hrpa_read_infty_un=>p0000_tab
      EXPORTING
        read_infotype = lo_read_infotype
        tclas         = c_tclas_a
        pernr         = lv_pernr
        begda         = c_low_date
        endda         = c_high_date
      RECEIVING
        p0000         = lt_p0000_large.

    CALL METHOD cl_hrpa_read_infty_un=>p0001_tab
      EXPORTING
        read_infotype = lo_read_infotype
        tclas         = c_tclas_a
        pernr         = lv_pernr
        begda         = iv_begda
        endda         = iv_endda
      RECEIVING
        p0001         = lt_p0001.
    CALL METHOD cl_hrpa_read_infty_un=>p0001_tab
      EXPORTING
        read_infotype = lo_read_infotype
        tclas         = c_tclas_a
        pernr         = lv_pernr
        begda         = c_low_date
        endda         = c_high_date
      RECEIVING
        p0001         = lt_p0001_large.

    CALL METHOD cl_hrpa_read_infty_un=>p0016_tab
      EXPORTING
        read_infotype = lo_read_infotype
        tclas         = c_tclas_a
        pernr         = lv_pernr
        begda         = c_low_date
        endda         = c_high_date
      RECEIVING
        p0016         = lt_p0016.

    LOOP AT lt_p0016 INTO ls_p0016
      WHERE begda <= iv_egyto
        AND endda >= iv_egyfr.
      EXIT.
    ENDLOOP.

*   Check fire date (if exists)
    CALL FUNCTION 'RP_HIRE_FIRE'
      EXPORTING
        beg       = c_low_date
        end       = c_high_date
      IMPORTING
        fire_date = lv_fire_date
      TABLES
        pphifi    = lt_phifi
        pp0000    = lt_p0000_large
        pp0001    = lt_p0001_large.

*   Get contract data
    CALL METHOD cl_hrpadun_eg_check=>check_contract
      EXPORTING
        begda = c_low_date
        endda = c_high_date
        p0000 = lt_p0000
        p0001 = lt_p0001
        p0016 = lt_p0016
      IMPORTING
        ctedt = lv_ctedt.

    IF lv_ctedt IS NOT INITIAL.
      IF lv_ctedt > lv_fire_date.
        lv_ctedt = lv_fire_date.
      ENDIF.

      ov_cttyp = ls_p0016-cttyp.
      ov_ctedt = lv_ctedt.
    ENDIF.

  ENDMETHOD.
