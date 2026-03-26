METHOD update_effective_date_reason.

  DATA: lt_req              TYPE STANDARD TABLE OF zv_hrfiori_req,
        ls_req              TYPE zv_hrfiori_req,
        lv_effective_date   TYPE datum,
        lv_end_date         TYPE datum,
        lv_reason_to_update TYPE ze_hrfiori_reason.

  "------------------------------------------------------------
  " Déterminer le reason à mettre à jour
  "------------------------------------------------------------
  IF iv_reason_new IS NOT INITIAL.
    lv_reason_to_update = iv_reason_new.
  ELSE.
    lv_reason_to_update = iv_reason.
  ENDIF.

  "------------------------------------------------------------
  " 1. Déterminer le GUID
  "------------------------------------------------------------
  IF cv_guid IS NOT INITIAL.
    SELECT *
      INTO TABLE lt_req
      FROM zv_hrfiori_req
      WHERE guid = cv_guid.
  ELSE.
    SELECT *
      INTO TABLE lt_req
      FROM zv_hrfiori_req
      WHERE creator_pernr = iv_pernr
        AND reason        = iv_reason
        AND closed       <> abap_true
        AND cancelled    <> abap_true.
  ENDIF.

  "------------------------------------------------------------
  " 2. Aucune request trouvée
  "------------------------------------------------------------
  IF lt_req IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER 125
      INTO rs_return-message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 3. Dernière version (seqno max)
  "------------------------------------------------------------
  SORT lt_req BY effective_date DESCENDING seqno DESCENDING.
  READ TABLE lt_req INTO ls_req INDEX 1.

  "------------------------------------------------------------
  " 4. Vérifier les statuts bloquants
  "------------------------------------------------------------
  IF ls_req-closed = abap_true
     OR ls_req-cancelled = abap_true.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER 126
      INTO rs_return-message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 5. Mise à jour autorisée
  "------------------------------------------------------------
  cv_guid = ls_req-guid.

  IF iv_effective_date IS INITIAL.
    lv_effective_date =  ls_req-effective_date.
  ELSE.
    lv_effective_date = iv_effective_date.
  ENDIF.

  " Mise à jour avec date de fin (pour LWOP)
  IF iv_end_date IS INITIAL.
    lv_end_date = ls_req-endda.
  ELSE.
    lv_end_date = iv_end_date.
  ENDIF.

  UPDATE zthrfiori_hreq
     SET effective_date = lv_effective_date
         endda          = lv_end_date
         reason         = lv_reason_to_update
   WHERE guid = cv_guid.

  IF sy-subrc <> 0.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER 127
      INTO rs_return-message.
  ELSE.
    MESSAGE ID 'ZHRFIORI' TYPE 'S' NUMBER 128
      INTO rs_return-message.
  ENDIF.

ENDMETHOD.
