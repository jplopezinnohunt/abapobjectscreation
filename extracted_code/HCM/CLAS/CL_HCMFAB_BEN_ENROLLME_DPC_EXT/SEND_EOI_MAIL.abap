METHOD SEND_EOI_MAIL.

  DATA :
      lt_itf                   TYPE tline_tab,
      lv_text                  TYPE string,
      ls_sapscript_header      TYPE thead,
      lo_formatted_text        TYPE REF TO cl_wd_formatted_text,
      lv_formatted_text_type   TYPE cl_wd_formatted_text=>t_type,
      lv_date(10)              TYPE c,
      lv_text_changed          TYPE abap_bool,
      lv_date_grp              TYPE string,
      lv_rec_name              TYPE string,
      lv_name                  TYPE emnam,
      lv_plan                  TYPE string,
      lv_rec_email             TYPE ad_smtpadr,
      lv_subject               TYPE so_obj_des.

  read_receiver_detail(
    EXPORTING
      iv_pernr = iv_pernr
    IMPORTING
      ev_email = lv_rec_email
      ev_name  = lv_name
  ).

  CHECK lv_rec_email IS NOT INITIAL AND
        lv_name IS NOT INITIAL.

  CALL FUNCTION 'DOCU_GET'
    EXPORTING
      extend_except          = ' '
      id                     = 'TX'
      langu                  = sy-langu
      object                 = c_eoi_mail_object
      typ                    = 'E'
      version                = 0
      version_active_or_last = 'L'
      print_param_get        = 'X'
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

    lv_rec_name = lv_name.
    lv_text_changed = lo_formatted_text->replace_placeholder(
     name           = 'NAME'
     text           =  lv_rec_name
     ).

    WRITE iv_grp_date  TO lv_date.
    lv_date_grp = lv_date.
    lv_text_changed = lo_formatted_text->replace_placeholder(
     name           = 'GRP'
     text           =  lv_date_grp
    ).

    lv_plan = iv_plan_name.
    lv_text_changed = lo_formatted_text->replace_placeholder(
     name           = 'PLAN'
     text           =  lv_plan
    ).

    lv_text = lo_formatted_text->m_xml_text.

  ENDIF.

  lv_subject = text-t10.

  send_mail(
    EXPORTING
      iv_body      = lv_text
      iv_subject   = lv_subject
      iv_rec_email = lv_rec_email
  ).

ENDMETHOD.
