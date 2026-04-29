  METHOD get_batch_number.
    DATA:
      ls_fpayhx TYPE fpayhx,
      lt_payp   TYPE TABLE OF FPAYP.

*   Only for DMEE eXtended Transactions
    CHECK mv_is_dmeex_tree IS NOT INITIAL.

*   Clear the placeholder
    CLEAR rv_renum.
    ls_fpayhx = is_fpayhx.
    lt_payp = it_fpayp_fref.
    TRY .
      CALL METHOD cl_idfi_utils=>('GET_DMEE_BATCHES')
        EXPORTING
          is_fpayh            = is_fpayh                 " Datensatz (Typ: DMEE_TREE_TYPE-IF_TYPE)
          iv_paymedium        = iv_paymedium             " Checkbox
          iv_level            = 002                      " DMEE: level of a format object
        IMPORTING
          rv_batch_id         = rv_renum
        CHANGING
          cs_fpayhx           = ls_fpayhx                 " Payment Medium: Prepared Data for Payment
          ct_fpayp            = lt_payp                 " Table type FPAYP

        .

    CATCH cx_sy_dyn_call_illegal_method.
      CLEAR rv_renum.
    ENDTRY.
  ENDMETHOD.