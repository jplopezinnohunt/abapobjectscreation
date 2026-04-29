METHOD is_dmeex_tree.
* In this method check whether the DMEE tree was changed in DMEE(x)
* transaction or not. Must be called dynamically because of downport
* to lower releases.

  DATA:
    lo_any_object         TYPE REF TO object.

  IF mv_tree_type EQ iv_tree_type AND mv_tree_id EQ iv_tree_id.
    rv_is_dmeex_tree = mv_is_dmeex_tree.
  ELSE.
    mv_tree_type = iv_tree_type.
    mv_tree_id   = iv_tree_id.

    TRY .
        CREATE OBJECT lo_any_object TYPE (con_cl_dmee_runtime)
          EXPORTING
            iv_tree_type       = mv_tree_type
            iv_tree_id         = mv_tree_id.

        CALL METHOD lo_any_object->(con_method_dmeex)
          RECEIVING
            ev_dmeex = rv_is_dmeex_tree.

      CATCH cx_sy_create_object_error.
        CLEAR rv_is_dmeex_tree.
      CATCH cx_sy_dyn_call_illegal_method.
        CLEAR rv_is_dmeex_tree.
    ENDTRY.

  ENDIF. "IF mv_tree_type EQ iv_tree_type AND mv_tree_id EQ iv_tree_id.

ENDMETHOD.