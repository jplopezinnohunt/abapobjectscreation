  METHOD compare_structures.
* Compare structures Character by Character, if any character in
* Generic structure is replaced by Country-Specific character, raise
* an error

    CONSTANTS:
      lc_refname       TYPE string VALUE 'REF'.             "#EC NOTEXT

    DATA:
      lv_refname_digit TYPE n LENGTH 2,
      lv_refname       TYPE string,
      lv_change_found  TYPE abap_bool.

    FIELD-SYMBOLS:
      <fs_ref_generic> TYPE any,
      <fs_ref_cntrspc> TYPE any.

* Prepare error value
    CLEAR lv_change_found.

* First compare FPAHX structures
    DO 99 TIMES.
      UNASSIGN: <fs_ref_generic>, <fs_ref_cntrspc>.
      lv_refname_digit = sy-index.
      CONCATENATE lc_refname lv_refname_digit INTO lv_refname.
      ASSIGN COMPONENT lv_refname OF STRUCTURE is_generic
          TO <fs_ref_generic>.
      ASSIGN COMPONENT lv_refname OF STRUCTURE is_cntry_spec
          TO <fs_ref_cntrspc>.
      IF <fs_ref_generic> IS NOT ASSIGNED OR
         <fs_ref_cntrspc> IS NOT ASSIGNED.
*     We are at the end of structure, there are no more REFxx fields
        EXIT.
      ENDIF.

      CALL METHOD compare_by_chars
        EXPORTING
          iv_generic    = <fs_ref_generic>
          iv_cntry_spec = <fs_ref_cntrspc>
        EXCEPTIONS
          change_found  = 1
          OTHERS        = 2.
      IF sy-subrc NE 0.
*     There is difference in Generic and Country-Specific structure
*     found in character mode - trigger an error and write to FBPM
*     log warning message
        CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
          EXPORTING
            i_msgid = 'IDFIPAYM_MSG'
            i_msgty = 'W'
            i_msgno = '011'
            i_msgv1 = iv_struc_name
            i_msgv2 = lv_refname
            i_msgv3 = mv_country_key.                       "#EC NOTEXT

        IF 1 = 0. "Crossreference
          MESSAGE w011(idfipaym_msg)
             WITH iv_struc_name lv_refname mv_country_key.
        ENDIF.

        lv_change_found = abap_true.
      ENDIF.
    ENDDO.

* Difference in Country-Specific Call has been found
    IF lv_change_found EQ abap_true.
      RAISE change_found.
    ENDIF.
  ENDMETHOD.