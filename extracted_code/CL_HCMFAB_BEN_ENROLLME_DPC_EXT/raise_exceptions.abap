METHOD raise_exceptions.

  DATA: lt_message_bapi        TYPE bapirettab,
        ls_message_bapi        TYPE bapiret2,
        ls_messages            TYPE rpbenerr,
        lo_message_container  TYPE REF TO /iwbep/if_message_container,
        lx_busi_exception     TYPE REF TO /iwbep/cx_mgw_busi_exception.
  IF it_messages IS NOT INITIAL.
    LOOP AT it_messages INTO ls_messages.
      ls_message_bapi-id = ls_messages-class.
      ls_message_bapi-number = ls_messages-msgno.
      ls_message_bapi-message_v1 = ls_messages-msgv1.
      ls_message_bapi-message_v2 = ls_messages-msgv2.
      ls_message_bapi-message_v3 = ls_messages-msgv3.
      ls_message_bapi-message_v4 = ls_messages-msgv4.
      ls_message_bapi-type = ls_messages-sever.
      APPEND ls_message_bapi TO lt_message_bapi.
      CLEAR:ls_message_bapi,ls_messages.
    ENDLOOP.

    DELETE lt_message_bapi WHERE type EQ 'I' OR type EQ 'S' OR type EQ 'W'.
    lo_message_container = me->mo_context->get_message_container( ).

    IF lt_message_bapi IS NOT INITIAL.
      lo_message_container->add_messages_from_bapi(
            it_bapi_messages         = lt_message_bapi
            iv_determine_leading_msg = /iwbep/if_message_container=>gcs_leading_msg_search_option-first
            iv_add_to_response_header = abap_true
            iv_entity_type           = iv_entity_name ).

      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          message_container = lo_message_container.
    ENDIF.
  ENDIF.
ENDMETHOD.
