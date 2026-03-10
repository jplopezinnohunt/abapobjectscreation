  METHOD get_computed_value_rsdep.

    DATA: lv_pernr         TYPE persno,
          lv_userid        TYPE sysid,
          lv_endda         TYPE endda,
          lv_eve_active    TYPE flag,
          lv_child         TYPE numc2,
          lv_depaw         TYPE numc2 ##NEEDED,
          ls_t596c         TYPE t596c,
          ls_dep_stat      TYPE pun_dep_stat,
          lt_p0021         TYPE STANDARD TABLE OF p0021,
          lt_p0962         TYPE STANDARD TABLE OF p0962,
          lt_dep_stat      TYPE hrpadun_dep_stat.
*          lo_read_infotype TYPE REF TO if_hrpa_read_infotype.

*   Get PERNR of connected user if needed
    IF iv_pernr IS INITIAL.
      MOVE sy-uname TO lv_userid.
      SELECT SINGLE pernr INTO lv_pernr
        FROM pa0105
          WHERE subty = '0001'
            AND endda >= sy-datum
            AND begda <= sy-datum
            AND usrid = lv_userid ##WARN_OK.
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.

    lv_endda = iv_endda.
    IF lv_endda IS INITIAL.
      lv_endda = c_31129999.
    ENDIF.

*   get childre data
*    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
*      IMPORTING
*        read_infotype = lo_read_infotype.
*
*    CALL METHOD cl_hrpa_read_infty_un=>p0021_tab
*      EXPORTING
*        read_infotype = lo_read_infotype
*        tclas         = if_hrpadun_const=>c_tclas
*        pernr         = lv_pernr
*        begda         = if_hrpadun_const=>c_low_date
*        endda         = if_hrpadun_const=>c_high_date
*      RECEIVING
*        p0021         = lt_p0021.

    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
*       TCLAS     = 'A'
        pernr     = lv_pernr
        infty     = '0021'
        begda     = sy-datum
        endda     = sy-datum
      TABLES
        infty_tab = lt_p0021.

*   Get customizing to determine how to set number of dependents
    CALL FUNCTION 'HR_APPL_T596C_READ'
      EXPORTING
        i_molga  = 'UN'
        i_appl   = 'EVE'
        i_date   = iv_begda
      IMPORTING
        es_t596c = ls_t596c.
    CALL METHOD cl_hrpadun_dp=>eve_depnd_active
      IMPORTING
        e_active = lv_eve_active.

    IF lv_eve_active IS NOT INITIAL AND ls_t596c IS NOT INITIAL.
      CALL METHOD cl_hrpa_infotype_0962=>bl_no_dependents
        EXPORTING
          begda = iv_begda
          endda = lv_endda
          p0021 = lt_p0021
          p0962 = lt_p0962
        IMPORTING
          depnr = lv_child
          depaw = lv_depaw.

      ov_rsdep = lv_child.
    ELSE.
      CALL METHOD cl_hrpa_infotype_0021_un=>bl_dep_stat_tab
        EXPORTING
          begda        = iv_begda
          endda        = iv_begda
          p0021        = lt_p0021
        IMPORTING
          dep_stat_tab = lt_dep_stat.

      LOOP AT lt_dep_stat INTO ls_dep_stat.
        ov_rsdep = ov_rsdep + ls_dep_stat-dcnt1.
      ENDLOOP.

    ENDIF.

  ENDMETHOD.
