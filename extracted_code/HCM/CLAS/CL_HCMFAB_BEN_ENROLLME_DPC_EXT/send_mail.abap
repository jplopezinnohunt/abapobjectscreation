METHOD send_mail.

  DATA: lv_x_text            TYPE xstring,
        lv_extension         TYPE soodk-objtp,
        ls_atta_hex          TYPE hcmfab_s_enro_attach,
        lt_att_hex           TYPE solix_tab,
        lt_hex               TYPE solix_tab,
        lo_ex                TYPE REF TO cx_root,
        lo_bcs               TYPE REF TO cl_bcs,
        lo_recipient         TYPE REF TO if_recipient_bcs,
        lo_sender            TYPE REF TO if_sender_bcs,
        lo_document          TYPE REF TO cl_document_bcs.

  TRY .

      CALL FUNCTION 'SCMS_STRING_TO_XSTRING'
        EXPORTING
          text   = iv_body
        IMPORTING
          buffer = lv_x_text.

      CALL FUNCTION 'SCMS_XSTRING_TO_BINARY'
        EXPORTING
          buffer     = lv_x_text
        TABLES
          binary_tab = lt_hex.

      lo_document = cl_document_bcs=>create_document(
                       i_type    = 'HTM'
                       i_hex     = lt_hex
                       i_subject = iv_subject ).

      IF it_attachment IS NOT INITIAL.

        LOOP AT it_attachment INTO ls_atta_hex.
          CLEAR : lv_extension, lt_att_hex .

          TRANSLATE ls_atta_hex-extension TO UPPER CASE.
          lv_extension = ls_atta_hex-extension.

          CALL FUNCTION 'SCMS_XSTRING_TO_BINARY'
            EXPORTING
              buffer     = ls_atta_hex-content
            TABLES
              binary_tab = lt_att_hex.

          CALL METHOD lo_document->add_attachment
            EXPORTING
              i_attachment_type    = lv_extension
              i_attachment_subject = ls_atta_hex-name
              i_att_content_hex    = lt_att_hex
            EXCEPTIONS
              OTHERS               = 1.

        ENDLOOP.

      ENDIF.

      lo_bcs = cl_bcs=>create_persistent( ).
      lo_sender = cl_cam_address_bcs=>create_internet_address( iv_rec_email ).
      lo_bcs->set_sender( lo_sender ).

      lo_recipient = cl_cam_address_bcs=>create_internet_address( iv_rec_email ).
      lo_bcs->add_recipient(
        EXPORTING
          i_recipient  = lo_recipient
          i_no_forward = abap_true ).

      lo_bcs->set_document( lo_document ).

      lo_bcs->set_status_attributes( 'E' ).

      lo_bcs->set_send_immediately( 'X' ).

      lo_bcs->send( ).

    CATCH cx_root INTO lo_ex.

  ENDTRY.

ENDMETHOD.
