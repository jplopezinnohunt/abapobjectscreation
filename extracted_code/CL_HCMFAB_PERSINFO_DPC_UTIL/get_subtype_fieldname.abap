METHOD get_subtype_fieldname.

  DATA ls_t582a TYPE t582a.
  DATA ls_t777d TYPE t777d.
  DATA lv_dummy TYPE string.

  ls_t582a = cl_hr_t582a=>read( infty  = iv_infty ).
  IF ls_t582a-namst IS INITIAL.
*   Newer infotypes do not necessarily have namst maintained in T582A but always will in T777D.
    ls_t777d = cl_hr_t777d=>read( infty  = iv_infty ).
    rv_fieldname = ls_t777d-namst.
  ELSE.
    SPLIT ls_t582a-namst AT '-'  INTO lv_dummy rv_fieldname.
  ENDIF.

ENDMETHOD.
