  METHOD if_idfi_cgi_dmee_countries~get_value.

    DATA lo_cgi_util TYPE REF TO ycl_idfi_cgi_dmee_util.
    DATA lv_subrc TYPE sy-subrc.

    "Check if tag is redefined with PPC customizing
    lo_cgi_util = NEW ycl_idfi_cgi_dmee_util( ).
    lo_cgi_util->get_tag_value_from_custo( EXPORTING iv_land1 = i_fpayh-zbnks
                                                     iv_deb_cre = flt_val_debit_or_credit
                                                     iv_tag_full = i_node_path
                                                     is_fpayh = i_fpayh
                                                     is_fpayhx = i_fpayhx
                                                     is_fpayp = i_fpayp
                                           IMPORTING ev_subrc = lv_subrc
                                           CHANGING  cv_value_c = o_value ).

  ENDMETHOD.