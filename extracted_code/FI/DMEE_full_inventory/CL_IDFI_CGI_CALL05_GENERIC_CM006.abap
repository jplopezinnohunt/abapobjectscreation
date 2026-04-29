METHOD if_idfi_cgi_call05~fill_fpay_fref.
* This method is used to return the changed Reference fields in
* structure FPAYHX and table FPAYP for DMEE(x) transaction in function
* module FI_PAYMEDIUM_DMEE_CGI_05.

* First is called Generic Functionality - to fill REF06 and others

* Then is called Country Specific Functionality - it is only allowed
* to change spaces, it is not allowed to replace existing fields,
* When there is not Country Specific class CL_IDFI_CGI_CALL05_xx (where
* xx stands for ISO Country Key), then empty method from this class is
* called

* At the end each structure is compared character by character and
* when any character from Generic Functionality is replaced, error
* message is triggered

    DATA:
      ls_fpayhx      TYPE fpayhx,
      ls_fpayhx_fref TYPE fpayhx_fref,
      lt_fpayp_fref   TYPE fpm_t_fpayp,
      lv_tree_id     TYPE dmee_treeid.
    FIELD-SYMBOLS:
      <fs_tree_id>   TYPE any.

* Used for warning message trigger
    IF is_fpayhx-ubiso IS NOT INITIAL.
      mv_country_key = is_fpayhx-ubiso.
    ELSE.
      mv_country_key = is_fpayhx-ubnks.
    ENDIF.

* Check the DMEE eXtended Transaction ------------------------- Step 0)
    ASSIGN COMPONENT 'TREE_ID' OF STRUCTURE is_fpayhx TO <fs_tree_id>.
    IF sy-subrc NE 0.
      ASSIGN COMPONENT 'FORMI' OF STRUCTURE is_fpayhx TO <fs_tree_id>.
    ENDIF.
    IF <fs_tree_id> IS ASSIGNED.
      lv_tree_id = <fs_tree_id>.
    ENDIF.
    mv_is_dmeex_tree = is_dmeex_tree( iv_tree_id = lv_tree_id ).

* Generic Functionality Call ---------------------------------- Step 1)
    CALL METHOD generic_call
      EXPORTING
        is_fpayh       = is_fpayh
        is_fpayhx      = is_fpayhx
        iv_paymedium   = iv_paymedium
      CHANGING
        cs_fpayhx_fref = cs_fpayhx_fref
        ct_fpayp_fref  = ct_fpayp_fref.

* Country-Specific Functionality Call ------------------------- Step 2)
    ls_fpayhx = is_fpayhx.                    "n2893975
    MOVE-CORRESPONDING cs_fpayhx_fref TO ls_fpayhx.     "Get the up to date data
    ls_fpayhx_fref  = cs_fpayhx_fref.
    lt_fpayp_fref[] = ct_fpayp_fref[].
    CALL METHOD country_specific_call
      EXPORTING
        is_fpayh       = is_fpayh
        is_fpayhx      = ls_fpayhx                "n2893975
        iv_paymedium   = iv_paymedium
      CHANGING
        cs_fpayhx_fref = ls_fpayhx_fref
        ct_fpayp_fref  = lt_fpayp_fref.

* Check that the Generic Ref.Fields has not been changed ------ Step 3)
    CALL METHOD check_changes
      EXPORTING
        is_fpayhx_fref_gen   = cs_fpayhx_fref
        it_fpayp_fref_gen    = ct_fpayp_fref
        is_fpayhx_fref_cntry = ls_fpayhx_fref
        it_fpayp_fref_cntry  = lt_fpayp_fref
      EXCEPTIONS
        change_found         = 1
        OTHERS               = 2.
    IF sy-subrc EQ 0.
      cs_fpayhx_fref  = ls_fpayhx_fref.
      ct_fpayp_fref[] = lt_fpayp_fref[].
    ENDIF.

*   Determinie the batch number -------------------------------- Step 999)
    IF iv_paymedium EQ abap_true.
*     Get the up to date data
      CLEAR ls_fpayhx.
      ls_fpayhx = is_fpayhx.
      MOVE-CORRESPONDING cs_fpayhx_fref TO ls_fpayhx.

      CALL METHOD get_batch_number
        EXPORTING
          is_fpayh      = is_fpayh
          is_fpayhx     = ls_fpayhx
          iv_paymedium  = iv_paymedium
          it_fpayp_fref = ct_fpayp_fref
        RECEIVING
          rv_renum      = cs_fpayhx_fref-ref06+40(35)."lv_renum.   " Reference Number
    ENDIF.


ENDMETHOD.