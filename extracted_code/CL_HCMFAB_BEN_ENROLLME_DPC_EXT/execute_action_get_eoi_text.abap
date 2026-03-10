METHOD execute_action_get_eoi_text.

  DATA: ls_param                 LIKE LINE OF it_parameter,
        ls_sapscript_header      TYPE thead,
        ls_eoi_txt               TYPE hcmfab_s_enro_eoi_text,
        lv_eogrp                 TYPE datum,
        lv_text                  TYPE string,
        lv_formatted_text_type   TYPE cl_wd_formatted_text=>t_type,
        lv_date(10)              TYPE c,
        lv_text_changed          TYPE abap_bool,
        lv_date_grp              TYPE string,
        lv_doc_obj               TYPE doku_obj,
        lt_itf                   TYPE tline_tab,
        lt_error                 TYPE TABLE OF rpbenerr,
        lo_formatted_text        TYPE REF TO cl_wd_formatted_text,
        lo_ex     TYPE REF TO cx_root.

  CLEAR: lv_eogrp.
  TRY .
      LOOP AT it_parameter INTO ls_param.
        CASE ls_param-name.
          WHEN 'GracePeriodEnd'.
            lv_eogrp = ls_param-value.
          WHEN OTHERS.
        ENDCASE.
      ENDLOOP.
    CATCH cx_root INTO lo_ex.

  ENDTRY.

  lv_doc_obj = c_eoi_object.

  CLEAR:lt_itf,ls_sapscript_header.
  CALL FUNCTION 'DOCU_GET'
    EXPORTING
      extend_except          = ' '
      id                     = 'TX'
      langu                  = sy-langu
      object                 = lv_doc_obj
      typ                    = 'E'
      version                = 0
      version_active_or_last = 'L'
      print_param_get        = c_true
    IMPORTING
      head                   = ls_sapscript_header
    TABLES
      line                   = lt_itf
    EXCEPTIONS
      no_docu_on_screen      = 1
      no_docu_self_def       = 2
      no_docu_temp           = 3
      ret_code               = 4
      OTHERS                 = 5.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  lv_formatted_text_type = cl_wd_formatted_text=>e_type-formatted_text.

  lo_formatted_text = cl_wd_formatted_text=>create_from_sapscript(
       sapscript_head  = ls_sapscript_header
       sapscript_lines = lt_itf
       type            = lv_formatted_text_type
   ).

  IF lo_formatted_text IS NOT INITIAL.
    CLEAR:lv_date_grp,lv_text,ls_eoi_txt-eoi_text.
    WRITE lv_eogrp  TO lv_date.
    lv_date_grp = lv_date.

    lv_text_changed = lo_formatted_text->replace_placeholder(
     name           = 'GRP'
     text           =  lv_date_grp
    ).

    lv_text = lo_formatted_text->m_xml_text.
    REPLACE FIRST OCCURRENCE OF '<p>' in lv_text with ''.
    REPLACE ALL OCCURRENCES OF '<p>'
        IN lv_text WITH cl_abap_char_utilities=>NEWLINE."RAJUG3090204
     REPLACE ALL OCCURRENCES OF '</p>'
        IN lv_text WITH ''.
    REPLACE all OCCURRENCES OF '&#x20;' in lv_text with cl_abap_char_utilities=>horizontal_tab.
    REPLACE all OCCURRENCES OF '&#x2f;' in lv_text with '/'. "Note 2820848

    ls_eoi_txt-eoi_text = lv_text.

    copy_data_to_ref(
      EXPORTING
        is_data = ls_eoi_txt
      CHANGING
        cr_data = er_data
    ).
  ENDIF.

ENDMETHOD.
