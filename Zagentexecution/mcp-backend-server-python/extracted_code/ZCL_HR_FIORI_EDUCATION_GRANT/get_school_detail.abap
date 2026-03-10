  METHOD get_school_detail.

    DATA : lv_datum         TYPE datum,
           ls_school_detail TYPE t7unpad_egsn..

    lv_datum = COND datum( WHEN iv_datum IS NOT INITIAL THEN iv_datum ELSE sy-datum ).

    CALL METHOD cl_hr_t7unpad_egsn=>read_at_date
      EXPORTING
        molga = c_molga_un
        egssl = iv_egssl
        date  = lv_datum
      RECEIVING
        egsn  = ls_school_detail.

    rs_school_details = CORRESPONDING #( ls_school_detail ).

  ENDMETHOD.
