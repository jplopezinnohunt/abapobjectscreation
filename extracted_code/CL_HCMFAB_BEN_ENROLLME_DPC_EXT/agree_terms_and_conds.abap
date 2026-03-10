METHOD agree_terms_and_conds.

  DATA: lv_doc_object     TYPE DOKU_OBJ,
        lo_badi_tnc       TYPE REF TO hcmfab_b_terms_and_conditions,
        lo_exception      TYPE REF TO cx_static_check.

  SELECT SINGLE doc_object INTO lv_doc_object FROM hcmfab_ben_event
    WHERE barea = iv_barea
    AND   event = iv_event
    AND   enrty = iv_enrty.

  CHECK sy-subrc = 0 AND lv_doc_object IS NOT INITIAL.

  GET BADI lo_badi_tnc.

  IF lo_badi_tnc IS BOUND.

    CALL BADI lo_badi_tnc->process_user_selection
      EXPORTING
        iv_agreed = iv_agreed
        iv_pernr  = iv_pernr
        iv_event  = iv_event.

  ENDIF.

ENDMETHOD.
