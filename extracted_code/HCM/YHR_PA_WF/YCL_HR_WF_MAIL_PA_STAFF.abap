class YCL_HR_WF_MAIL_PA_STAFF definition
  public
  inheriting from YCL_HR_WF_MAIL_GENERATOR
  create public .

public section.

  methods YIF_HR_WF_MAIL~SEND_WI_NOTIFICATION_PA
    redefinition .
protected section.

  data MV_MASSN_TXT_EN type TEXT60 .
  data MV_MASSN_TXT_FR type TEXT60 .
  data MV_DEAR type CHAR05 .
  data MV_FIRSTNAME type PAD_VORNA .
  data MO_WF_FACTORY type ref to YCL_HRWF_FACTORY .

  methods FILTER_AUTHORIZED_EMAIL
    redefinition .
  methods GET_DATA
    redefinition .
  methods INITIALIZE_DATA
    redefinition .
  methods REPLACE_IN_HEADER
    redefinition .
  methods SET_ATTACHMENT
    redefinition .
private section.
ENDCLASS.



CLASS YCL_HR_WF_MAIL_PA_STAFF IMPLEMENTATION.


  METHOD filter_authorized_email.
    DATA lt_mail_auth TYPE TABLE OF ytbc_mail_auth.

    SELECT * INTO TABLE lt_mail_auth FROM ytbc_mail_auth WHERE yappl = 'PA_WF'.

    LOOP AT ct_email ASSIGNING FIELD-SYMBOL(<lv_email>).
      READ TABLE lt_mail_auth TRANSPORTING NO FIELDS WITH KEY ymail = <lv_email>.
      IF sy-subrc <> 0.
        CONCATENATE <lv_email> 'TEST' INTO <lv_email>.
      ENDIF.
    ENDLOOP.
  ENDMETHOD.


  METHOD get_data.
    CALL METHOD super->get_data.
    me->put_to_container( iv_field = '<MASSN_EN>' iv_value = mv_massn_txt_en   ).
    me->put_to_container( iv_field = '<MASSN_FR>' iv_value = mv_massn_txt_fr   )."EVO241124
    me->put_to_container( iv_field = '<DEAR>'      iv_value = mv_dear   ). "Dear Cher or Chère
    me->put_to_container( iv_field = '<FIRSTNAME>' iv_value = mv_firstname   ).


  ENDMETHOD.


  METHOD initialize_data.
    DATA : lv_wftype TYPE ye_hrwf_type,
           lv_gesch  TYPE hrpad_gender.


    "Initialisation of WF business class
    lv_wftype = mv_add_param_1."WF type Param 1
    mo_wf_factory = ycl_hrwf_factory=>get_instance( lv_wftype ).

    "Get employee data
    mo_wf_factory->mo_main_class->get_employee_data( iv_pernr = mv_objid
                                                     iv_action_date = mv_date_ref ).

    "Get Action type and reason for action text
    SELECT SINGLE yymntxt_long INTO mv_massn_txt_en FROM t529t WHERE sprsl = 'E'
                                                                 AND massn = mv_massn.

    SELECT SINGLE yymntxt_long INTO mv_massn_txt_fr FROM t529t WHERE sprsl = 'F' "EVO241124
                                                                 AND massn = mv_massn. "EVO241124

    SELECT SINGLE gesch vorna INTO ( lv_gesch, mv_firstname ) FROM pa0002 WHERE pernr =  mv_objid
                                                                        AND begda LE mv_date_ref
                                                                        AND endda GE mv_date_ref.
    CASE lv_gesch.
      WHEN '1'.
        mv_dear = 'Cher'.
      WHEN '2'.
        mv_dear = 'Chère'.
    ENDCASE.
  ENDMETHOD.


  METHOD replace_in_header.
    CALL METHOD super->replace_in_header
      CHANGING
        cv_string = cv_string.

    REPLACE '<MASSN_EN>' WITH mv_massn_txt_en INTO cv_string.
    REPLACE '<MASSN_FR>' WITH mv_massn_txt_fr INTO cv_string."EVO241124

    CONDENSE cv_string.

  ENDMETHOD.


  METHOD set_attachment.

    CLEAR ms_document_data.
    DATA lv_size TYPE sofolenti1-doc_size.

    SELECT SINGLE * INTO @DATA(ls_attach) FROM ythrpawf_attach WHERE wftype = @mv_add_param_1 "Workflow Type
                                                                 AND pernr  = @mv_objid
                                                                 AND attty  = @mv_add_param_2. "Attachment type examples : PA for PAF / AD for Amnistrative Details

    CHECK sy-subrc = 0.

    "ms_document_data-obj_type = 'PDF'.
    ms_document_data-obj_descr = ls_attach-filename.
    ms_document_data-doc_size  = xstrlen( ls_attach-contents ).

    "Convert Xstring to XTAB
    mt_att_content_hex = cl_bcs_convert=>xstring_to_solix( iv_xstring = ls_attach-contents ).

  ENDMETHOD.


   METHOD yif_hr_wf_mail~send_wi_notification_pa.

     DATA lt_body  TYPE soli_tab.
     DATA lt_mail TYPE ytthr_wf_actors.
     DATA lt_mail_copy TYPE ytthr_wf_actors.
     DATA ls_mail TYPE LINE OF ytthr_wf_actors.
     DATA : lv_langu TYPE syst_langu.                       "EVO241124
     mv_objid = iv_pernr.
     mv_date_ref = iv_date_action.
     mt_reason = it_reason.
     mv_wi_father = iv_wi_father.
     mv_massn = iv_massn.
     mv_massg = iv_massg.
     mv_wf_step = iv_wf_step.
     mv_current_actor-otype = 'US'.
     mv_current_actor-objid = iv_current_uname.
     mv_add_param_1 = iv_add_param_1.
     mv_add_param_2 = iv_add_param_2.
     mv_add_param_3 = iv_add_param_3.
     mv_add_param_4 = iv_add_param_4.

     lv_langu = mv_add_param_3.

     "Initialize data
     me->initialize_data( ).

     "get subject
     CLEAR: mt_lines, mt_stream, ms_stream, mt_body.
     mt_lines = me->get_template( iv_name  = mv_notif_header
                                  iv_langu = lv_langu      ). "evo241124

     me->convert_to_table_string( ).

     READ TABLE mt_stream INTO ms_stream INDEX 1.
     me->replace_in_header( CHANGING cv_string  = ms_stream ).
     mv_subject = ms_stream.

     CLEAR mt_lines.
     "get body
     mt_lines = me->get_template( iv_name  = mv_notif_body
                                  iv_langu = lv_langu      ). "evo241124

     me->convert_to_table_string( ).
     "Manage attachments
     CLEAR: ms_document_data, mt_att_content, mt_att_content_hex.
     me->set_attachment( ).
     "Generate body
     me->replace_in_body( ).
     LOOP AT mt_stream INTO ms_stream .
       CONCATENATE ms_stream '<br>' INTO ms_stream.
       REPLACE ALL OCCURRENCES OF cl_abap_char_utilities=>newline IN ms_stream WITH '<br>'.
       CLEAR lt_body.
       CALL FUNCTION 'SO_STRING_TO_TAB'
         EXPORTING
           content_str = ms_stream
         TABLES
           content_tab = lt_body.

       APPEND LINES OF lt_body TO mt_body.
     ENDLOOP.

     "Extract e-mails
     LOOP AT it_actors INTO DATA(ls_actors) WHERE email IS NOT INITIAL.
       MOVE-CORRESPONDING ls_actors TO ls_mail.
       APPEND ls_mail TO lt_mail.
     ENDLOOP.

     LOOP AT it_actors_copy INTO ls_actors WHERE email IS NOT INITIAL.
       MOVE-CORRESPONDING ls_actors TO ls_mail.
       APPEND ls_mail TO lt_mail_copy.
     ENDLOOP.

     IF lt_mail IS NOT INITIAL.
       me->send_mail( it_mail      = lt_mail
                      it_mail_copy = lt_mail_copy
                      iv_sender    = iv_sender   ).
     ENDIF.

   ENDMETHOD.
ENDCLASS.