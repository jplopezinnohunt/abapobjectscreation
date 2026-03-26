  METHOD get_egsna_egsct_egsty_ort01.

    DATA: ls_egsn TYPE t7unpad_egsn.

    CALL METHOD cl_hr_t7unpad_egsn=>read_at_date
      EXPORTING
        molga = c_molga_un
        egssl = iv_egssl
        date  = iv_begda
      RECEIVING
        egsn  = ls_egsn.

    ov_egsna = ls_egsn-egsna.
    ov_ort01 = ls_egsn-ort01.
    ov_egsct = ls_egsn-egsct.
    ov_egsty = ls_egsn-egsty.

  ENDMETHOD.
