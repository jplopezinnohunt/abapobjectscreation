METHOD IF_EX_HCMFAB_PERSINFO_SETTINGS~GET_SETTINGS.

*  DATA: lv_ar_object TYPE saeobjart,
*        lv_subrc     TYPE sysubrc,
*        lv_gsval     TYPE gsval,
*        lv_doc_class TYPE saedoktyp,
*        lv_mime_type TYPE w3conttype.
*
*  "in SAP-standard, the employee picture can be changed from every PersInfo app
*  CLEAR: et_allowed_mimetypes, ev_disable_employee_pic_change.
*
*  IF et_allowed_mimetypes IS SUPPLIED.
** in the sap-standard fallback class,
** only the mime type defined in the OAC2 customizing is allowed
*
**.. get document type for employee photo
*    CALL METHOD cl_hr_t77s0=>read_gsval
*      EXPORTING
*        grpid       = 'ADMIN'
*        semid       = 'PHOTO'
*      IMPORTING
*        returnvalue = lv_gsval
*        subrc       = lv_subrc.
*    IF lv_subrc = 0.
*      lv_ar_object = lv_gsval.
*    ELSE.
*      lv_ar_object = 'HRICOLFOTO'.
*    ENDIF.
*
**.. get document class from archive link customizing
*    SELECT SINGLE doc_type FROM toadv INTO lv_doc_class
*                           WHERE ar_object = lv_ar_object.
*
*    IF sy-subrc = 0.
**.. get default mimetype
*      CALL METHOD cl_alink_services=>get_mimetype_from_doctype
*        EXPORTING
*          im_documentclass = lv_doc_class
*        IMPORTING
*          ex_mimetype      = lv_mime_type
*        EXCEPTIONS
*          not_found        = 1
*          OTHERS           = 2.
*      IF sy-subrc <> 0.
*        CALL FUNCTION 'SDOK_MIMETYPE_GET'
*          EXPORTING
*            extension = lv_doc_class
*          IMPORTING
*            mimetype  = lv_mime_type.
*      ENDIF.
*    ENDIF.
*
*    IF lv_mime_type IS INITIAL.
*      lv_mime_type = gc_mimetype-jpeg.
*    ENDIF.
*
*    APPEND lv_mime_type TO et_allowed_mimetypes.
*  ENDIF.

ENDMETHOD.
