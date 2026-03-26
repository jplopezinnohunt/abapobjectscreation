  METHOD get_computed_value_lgart.

    DATA: ls_rsdr TYPE t7unpad_rsdr.

    CALL METHOD cl_hr_t7unpad_rsdr=>read
      EXPORTING
        molga = c_molga_un
        rsdrt = iv_rsdrt
      RECEIVING
        rsdr  = ls_rsdr.

    ov_lgart = ls_rsdr-lgart.

  ENDMETHOD.
