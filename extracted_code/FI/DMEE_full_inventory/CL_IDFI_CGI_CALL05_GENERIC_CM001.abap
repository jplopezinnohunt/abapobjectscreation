  METHOD check_changes.
* This method is used check changes done in Generic Call of this class
* and Country-Specific Call of ISO Country Key class (e.g.
* CL_IDFI_CGI_CALL05_DE).

* It is not possible to change any content of FPAYHX and FPAYP
* Reference fiels compared character by character
    CONSTANTS:
      lc_fpayhx TYPE string VALUE 'FPAYHX',                 "#EC NOTEXT
      lc_fpayp  TYPE string VALUE 'FPAYP[&]'.               "#EC NOTEXT

    DATA:
      lv_fpayp_gen_cnt    TYPE i,
      lv_fpayp_cntry_cnt  TYPE i,
      ls_fpayp_generic    LIKE LINE OF it_fpayp_fref_gen,
      ls_fpayp_cntry_spec LIKE LINE OF it_fpayp_fref_cntry,
      lv_change_found     TYPE abap_bool,
      lv_struc_name       TYPE string,
      lv_tabix_str        TYPE string.

* Prepare error trigger
    CLEAR lv_change_found.

* First compare FPAHX structures
    CALL METHOD compare_structures
      EXPORTING
        is_generic    = is_fpayhx_fref_gen
        is_cntry_spec = is_fpayhx_fref_cntry
        iv_struc_name = lc_fpayhx
      EXCEPTIONS
        change_found  = 1
        OTHERS        = 2.
    IF sy-subrc <> 0.
*     There is difference in Generic and Country-Specific structure
*     found in character mode - trigger an error and write to FBPM
*     log warning message
      lv_change_found = abap_true.
    ENDIF.

* Then compare FPAYP tables
    DESCRIBE TABLE:
      it_fpayp_fref_gen   LINES lv_fpayp_gen_cnt,
      it_fpayp_fref_cntry LINES lv_fpayp_cntry_cnt.

    IF lv_fpayp_gen_cnt NE lv_fpayp_cntry_cnt.
*   There is difference in Generic and Country-Specific items table
*   found by items count - trigger an error and write to FBPM
*   log warning message
      lv_change_found = abap_true.
    ELSE.
      LOOP AT it_fpayp_fref_gen INTO ls_fpayp_generic.
        READ TABLE it_fpayp_fref_cntry INTO ls_fpayp_cntry_spec
             INDEX sy-tabix.

        lv_struc_name = lc_fpayp.
        lv_tabix_str  = sy-tabix.
        REPLACE '&' WITH lv_tabix_str INTO lv_struc_name.
        CONDENSE lv_struc_name NO-GAPS.
        CALL METHOD compare_structures
          EXPORTING
            is_generic    = ls_fpayp_generic
            is_cntry_spec = ls_fpayp_cntry_spec
            iv_struc_name = lv_struc_name
          EXCEPTIONS
            change_found  = 1
            OTHERS        = 2.
        IF sy-subrc <> 0.
*         There is difference in Generic and Country-Specific structure
*         found in character mode - trigger an error and write to FBPM
*         log warning message
          lv_change_found = abap_true.
        ENDIF.
      ENDLOOP. "LOOP AT it_fpayp_fref_gen INTO ls_fpayp_generic.
    ENDIF. "IF lv_fpayp_gen_cnt NE lv_fpayp_cntry_cnt.


* Difference in Country-Specific Call has been found
    IF lv_change_found EQ abap_true.
      RAISE change_found.
    ENDIF.

  ENDMETHOD.