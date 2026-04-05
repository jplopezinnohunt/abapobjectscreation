  METHOD get_tag_value_from_custo.
    DATA lv_pay_type TYPE ye_fi_pay_type.
    DATA ls_t015l TYPE t015l.
    DATA lv_dummy TYPE t015l-zwck1.
    DATA lv_value TYPE t015l-zwck1.
    DATA lv_field TYPE text80.
    DATA lv_first TYPE xfeld VALUE abap_true.
    DATA lv_deb_cre TYPE fin_drcrind.
    ev_subrc = 0.
    "Get pay type
    CASE is_fpayh-dorigin(2).
      WHEN 'HR'.
        lv_pay_type = 'P'.
      WHEN 'TR'.
        lv_pay_type = 'R'.
      WHEN OTHERS.
        lv_pay_type = 'O'.
    ENDCASE.
    CASE iv_deb_cre.
      WHEN 'DEBIT'.
        lv_deb_cre = 'D'.
      WHEN 'CREDIT'.
        lv_deb_cre = 'C'.
      WHEN OTHERS.
        ev_subrc = 8.
        EXIT.
    ENDCASE.
    LOOP AT mt_ppc_cus INTO DATA(ls_cus) WHERE land1 = iv_land1
                                         AND   deb_cre = lv_deb_cre
                                         AND   ( pay_type = lv_pay_type OR pay_type
                                         AND   tag_full = iv_tag_full.
      IF lv_first = abap_true.
        CLEAR cv_value_c.
        lv_first = abap_false.
      ENDIF.
      CASE ls_cus-ppc_code.
        WHEN 'SEPARATOR' OR 'FIXED_VAL'.
          me->build_value( EXPORTING iv_value_c = cv_value_c
                                     iv_value_to_add = ls_cus-ppc_value
                           IMPORTING ev_value_c = cv_value_c ).
        WHEN 'PPC_VAR'.
          READ TABLE mt_t015l INTO ls_t015l WITH KEY lzbkz = is_fpayp-lzbkz.
          IF sy-subrc = 0.
            SPLIT ls_t015l-zwck1 AT space INTO lv_value lv_dummy.
            me->build_value( EXPORTING iv_value_c = cv_value_c
                                       iv_value_to_add = lv_value
                             IMPORTING ev_value_c = cv_value_c ).
          ENDIF.
        WHEN 'PPC_DESCR'.
          READ TABLE mt_t015l INTO ls_t015l WITH KEY lzbkz = is_fpayp-lzbkz.
          IF sy-subrc = 0.
            SPLIT ls_t015l-zwck1 AT space INTO lv_dummy lv_value.
            me->build_value( EXPORTING iv_value_c = cv_value_c
                                       iv_value_to_add = lv_value
                             IMPORTING ev_value_c = cv_value_c ).
          ENDIF.
        WHEN 'PAY_FIELD'.
          lv_field = |IS_{ ls_cus-pay_struc }-{ ls_cus-pay_field }|.
          ASSIGN (lv_field) TO FIELD-SYMBOL(<field>).
          IF <field> IS ASSIGNED.
            me->build_value( EXPORTING iv_value_c = cv_value_c
                                     iv_value_to_add = <field>
                           IMPORTING ev_value_c = cv_value_c ).
          ELSE.
            ev_subrc = 8.
          ENDIF.
      ENDCASE.
    ENDLOOP.
    IF sy-subrc <> 0.
      ev_subrc = 4.
    ENDIF.
  ENDMETHOD.