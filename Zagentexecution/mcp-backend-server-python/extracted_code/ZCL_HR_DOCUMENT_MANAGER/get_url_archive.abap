  METHOD get_url_archive.

    DATA : ls_toahr     TYPE toahr,
           lt_toahr     TYPE STANDARD TABLE OF toahr,
           lv_search    TYPE saeobjid,
*           ls_message   TYPE bapiret2,
*           lv_crepid    TYPE  saearchivi,
           lv_objectype TYPE saeanwdid,
           lv_objectid  TYPE saeobjid,
           lt_url       TYPE TABLE OF toauri,
           ls_url       TYPE  toauri.
*          lt_url type table of TOADURL_S.

    lv_search = im_pernr && '%'.
    SELECT *
      FROM toahr
      INTO TABLE lt_toahr
      WHERE sap_object = 'PREL'
        AND ar_object = im_doctype
        AND object_id LIKE lv_search
      ORDER BY ar_date DESCENDING.

    IF sy-subrc EQ 0.

      READ TABLE lt_toahr INTO ls_toahr INDEX 1.
      lv_objectid = ls_toahr-object_id.
      lv_objectype = ls_toahr-sap_object.

      CALL FUNCTION 'ARCHIVOBJECT_GET_URI'
        EXPORTING
          objecttype               = lv_objectype
          object_id                = lv_objectid
*         LOCATION                 = 'F'
*         HTTP_URL_ONLY            = ' '
        TABLES
          uri_table                = lt_url
        EXCEPTIONS
          error_archiv             = 1
          error_communicationtable = 2
          error_kernel             = 3
          error_http               = 4
          error_dp                 = 5
          OTHERS                   = 6.

      IF sy-subrc <> 0.
*         Implement suitable error handling here
        CLEAR ex_url.
        message id 'ZHRFIORI' type 'E' number '94'
        into ev_message.
        EXIT.
      ELSE.
        LOOP AT lt_url INTO ls_url.
          ex_url = ls_url-uri.
          EXIT.
        ENDLOOP.
      ENDIF.

   ELSE.
       CLEAR ex_url.
      message id 'ZHRFIORI' type 'E' number '94'
       into ev_message.
      EXIT.
    ENDIF.
*      lv_crepid = ls_toahr-archiv_id.
*CALL FUNCTION 'ALINK_RFC_DOCUMENlt_urlS_GET'
*  EXPORTING
*    IM_DOCID         = lv_objectid
*    IM_CREPID        = lv_crepid
* IMPORTING
*   EX_MESSAGE       = ls_message
* TABLES
*   EX_URLS          =  lt_url.
* Error during import of physical document (YH, 1010915520251231) from cluster table YTHR_CMS_1.

  ENDMETHOD.
