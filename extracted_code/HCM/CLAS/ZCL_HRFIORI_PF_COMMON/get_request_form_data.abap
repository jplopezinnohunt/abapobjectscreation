  METHOD get_request_form_data.

    DATA: lv_step_guid       TYPE asr_guid,
          lv_xstring         TYPE xstring,
          lo_data_container  TYPE REF TO cl_hrasr00_data_container,
          lo_process         TYPE REF TO if_hrasr00_proc_obj_handler,
          lo_object          TYPE REF TO cl_hrasr00_proc_obj_handler,
          lo_message_handler TYPE REF TO cl_hrasr00_dt_message_list.

*   Get step from process guid
    get_last_step_for_a_request(
      EXPORTING
        iv_process_guid = iv_process_guid
      IMPORTING
        ov_step_guid = lv_step_guid ).

*   Get associated step object
    CREATE OBJECT lo_object
      EXPORTING
        step_guid = lv_step_guid.

    CALL METHOD lo_object->set_attributes_internal
      EXPORTING
        step_guid = lv_step_guid
        pobj_guid = iv_process_guid.

    lo_process ?= lo_object.

    CREATE OBJECT lo_message_handler.
*    cl_hrasr00_proc_obj_handler=>get_instance(
*      EXPORTING message_handler = lo_message_handler
*          step_guid = lv_step_guid
*          process_name = iv_process
*          activity     = 'R'
*      IMPORTING
*          instance = lo_process ).

*   Get data container
    lo_process->get_data_container(
      EXPORTING
        message_handler = lo_message_handler
      IMPORTING
        data_container = lv_xstring ).

    CREATE OBJECT lo_data_container
      EXPORTING
        xml = lv_xstring.

*   Get form data values
    lo_data_container->get_values_of_fields(
      IMPORTING values_of_fields = ot_fields_value ).

  ENDMETHOD.
