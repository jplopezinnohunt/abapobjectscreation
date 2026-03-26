  METHOD get_child_detail.

    "return fasexTxt, fanatTxt and Egage
    IF cs_child-fasex IS NOT INITIAL.
      cs_child-fasex_txt = cl_eain_get_text=>get_gender_text( ifd_gesch = cs_child-fasex ).
    ENDIF.
    IF cs_child-fanat IS NOT INITIAL.
      cs_child-fanat_txt = cl_eain_get_text=>get_nationality_text( ifd_natio = cs_child-fanat ).
    ENDIF.

    "Egage
    CALL METHOD cl_hrpa_infotype_0965=>get_age
      EXPORTING
        fgbdt    = cs_child-fgbdt
        scd_date = sy-datum
      IMPORTING
        l_age    = DATA(l_years).

    cs_child-egage = l_years.

  ENDMETHOD.
