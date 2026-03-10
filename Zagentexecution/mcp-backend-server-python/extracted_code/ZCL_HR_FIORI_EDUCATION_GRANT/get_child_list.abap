  METHOD get_child_list.

    DATA  : gt_p0021 TYPE p0021_tab,
            lt_p0021 TYPE p0021_tab,
            lt_c0021 TYPE hrpadun_eg_child.

*    *read it0021 first all family members CODE TAKEN from mp00965
    CALL METHOD cl_hrpadun_eg_appl=>get_children
      EXPORTING
        pernr    = iv_pernr
        begda    = iv_begda
        endda    = iv_endda
        gt_p0021 = gt_p0021
      IMPORTING
        lt_p0021 = lt_p0021
        lt_c0021 = lt_c0021.

    ##TODO "Check why 2?
    DELETE ADJACENT DUPLICATES FROM lt_p0021 COMPARING objps subty.

    Rt_childs = CORRESPONDING #( lt_p0021 ).

    "get FanatTxt and FasexTxt

    LOOP AT Rt_childs ASSIGNING FIELD-SYMBOL(<lfs_child>).

      get_child_detail(
        CHANGING
          cs_child =  <lfs_child>            " Benefit App - Child structure
      ).

    ENDLOOP.
*          rt_childs = VALUE #(
*              FOR wa IN  lt_p0021
*              ( VALUE ZSHR_FIORI_CHILD( BASE wa
*                                 begda   = sy-datum
*                                 endda  = sy-datum
*                                 ) ) ).

  ENDMETHOD.
