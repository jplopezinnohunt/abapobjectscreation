FUNCTION ptrv_ac_document_remote.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  IMPORTING
*"     VALUE(IV_AWREF) LIKE  HRAADOCHDRP-REFDOCNO
*"     REFERENCE(IV_COMPCODE) TYPE  PTRV_DOC_HD-BUKRS
*"     REFERENCE(IV_GLVOR) TYPE  PTRV_DOC_HD-INT_GLVOR
*"  EXPORTING
*"     REFERENCE(ES_RETURN) TYPE  BAPIRET2
*"  TABLES
*"      T_DOCUMENTS STRUCTURE  BAPIACDONR
*"  EXCEPTIONS
*"      ERROR_IN_FILTEROBJECTS
*"      ERROR_IN_ALE_CUSTOMIZING
*"      NOT_UNIQUE_RECEIVER
*"      NO_RFC_DESTINATION_MAINTAINED
*"      NO_OWN_LOGICAL_SYSTEM
*"      COMMUNICATION_FAILURE
*"      SYSTEM_FAILURE
*"      UNDEFINED_ERROR
*"----------------------------------------------------------------------

  DATA:   ls_unique_receiver LIKE bdbapidest,
          lt_filterobjects_values LIKE bdi_fobj OCCURS 10 WITH HEADER LINE,
          lv_own_log_sys TYPE tbdls-logsys,
          lv_obj_key TYPE bapiache01-obj_key,
          lv_obj_type TYPE bapiache01-obj_type,
          lv_bo TYPE bdi_bapi-object,
          lv_method TYPE bdi_bapi-method VALUE 'POST'.

  CLEAR lt_filterobjects_values. REFRESH lt_filterobjects_values.
  lt_filterobjects_values-objtype = 'COMP_CODE'.
  lt_filterobjects_values-objvalue = iv_compcode.
  APPEND lt_filterobjects_values.

  CASE iv_glvor.
    WHEN 'TRV1' OR 'TRV4'.  "GLW note 2379656
      lv_bo = 'BUS6004'.
    WHEN 'TRV2'.
      lv_bo = 'BUS6005'.
    WHEN 'TRV3'.
      lv_bo = 'BUS6006'.
*    WHEN 'TRV4'.
*      lv_bo = 'BUS6004'.
    WHEN OTHERS.
      RAISE undefined_error.
  ENDCASE.

  CALL FUNCTION 'ALE_BAPI_GET_UNIQUE_RECEIVER'
    EXPORTING
      object                        = lv_bo
      method                        = lv_method
    IMPORTING
      receiver                      = ls_unique_receiver
    TABLES
      filterobjects_values          = lt_filterobjects_values
    EXCEPTIONS
      error_in_filterobjects        = 1
      error_in_ale_customizing      = 2
      not_unique_receiver           = 3
      no_rfc_destination_maintained = 4
      OTHERS                        = 5.

  CASE sy-subrc.
    WHEN 1.
      RAISE error_in_filterobjects.
    WHEN 2.
      RAISE error_in_ale_customizing.
    WHEN 3.
      RAISE not_unique_receiver.
    WHEN 4.
      RAISE no_rfc_destination_maintained.
    WHEN 5.
      RAISE undefined_error.
  ENDCASE.

  CALL FUNCTION 'OWN_LOGICAL_SYSTEM_GET'
    IMPORTING
      own_logical_system             = lv_own_log_sys
    EXCEPTIONS
      own_logical_system_not_defined = 1
      OTHERS                         = 2.

  IF sy-subrc <> 0.
    RAISE no_own_logical_system.
  ENDIF.

  lv_obj_key = iv_awref.
  lv_obj_type = 'TRAVL'.

  IF ls_unique_receiver-rfc_dest IS INITIAL.

    CALL FUNCTION 'BAPI_ACC_DOCUMENT_RECORD'
      EXPORTING
        obj_type = lv_obj_type
        obj_key  = lv_obj_key
        obj_sys  = lv_own_log_sys
      IMPORTING
        return   = es_return
      TABLES
        receiver = t_documents.

  ELSE.

    CALL FUNCTION 'BAPI_ACC_DOCUMENT_RECORD'
      DESTINATION ls_unique_receiver-rfc_dest
      EXPORTING
        obj_type              = lv_obj_type
        obj_key               = lv_obj_key
        obj_sys               = lv_own_log_sys
      IMPORTING
        return                = es_return
      TABLES
        receiver              = t_documents
      EXCEPTIONS
        communication_failure = 1
        system_failure        = 2.

    IF sy-subrc = 1.
      RAISE communication_failure.
    ELSEIF sy-subrc = 2.
      RAISE system_failure.
    ENDIF.

  ENDIF.

ENDFUNCTION.