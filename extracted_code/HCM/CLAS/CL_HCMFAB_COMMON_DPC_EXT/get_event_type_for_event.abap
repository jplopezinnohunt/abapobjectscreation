METHOD get_event_type_for_event.

  DATA: ls_event_type TYPE hcmfab_s_tcal_event_type.

  CLEAR rs_event_type.

* try to find entry for subcategory
  READ TABLE it_event_types INTO rs_event_type WITH KEY event_category = is_event-event_category event_subcategory = is_event-event_subcategory.
  IF sy-subrc = 0.
    RETURN.
  ENDIF.

* try to find entry for subcategory via wildcard '*'
  LOOP AT it_event_types INTO ls_event_type.
*    WHERE event_category = is_event-event_category AND event_subcategory CP is_event-event_subcategory.
    IF is_event-event_category = ls_event_type-event_category AND is_event-event_subcategory CP ls_event_type-event_subcategory.
      rs_event_type = ls_event_type.
      RETURN.
    ENDIF.
  ENDLOOP.

ENDMETHOD.
