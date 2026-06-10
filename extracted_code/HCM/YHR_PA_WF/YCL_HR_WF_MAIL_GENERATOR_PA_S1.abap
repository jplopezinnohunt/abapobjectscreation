class YCL_HR_WF_MAIL_GENERATOR_PA_S1 definition
  public
  inheriting from YCL_HR_WF_MAIL_GENERATOR
  create public .

public section.
  type-pools YPAWF .
protected section.

  data MV_WF_STEP_TXT type TEXT30 .
  data MV_MASSG_TXT_EN type MGTXT .
  data MV_ENAME_FR type EMNAM .
  data MV_MASSN_TXT_EN type MNTXT .
  data MV_MASSN_TXT_FR type MNTXT .
  data MO_WF_FACTORY type ref to YCL_HRWF_FACTORY .
  data MV_SHORT_S type SHORT_D .
  data MV_STEXT_O_EN type STEXT .
  data MV_STEXT_S_EN type STEXT .
  data MV_STEXT_O_FR type STEXT .
  data MV_STEXT_S_FR type STEXT .
  data MV_ENAME_EN type EMNAM .
  data MV_MASSG_TXT_FR type MGTXT .

  methods GET_DATA
    redefinition .
  methods INITIALIZE_DATA
    redefinition .
  methods REPLACE_IN_HEADER
    redefinition .
  methods FILTER_AUTHORIZED_EMAIL
    redefinition .
private section.
ENDCLASS.



CLASS YCL_HR_WF_MAIL_GENERATOR_PA_S1 IMPLEMENTATION.


  method FILTER_AUTHORIZED_EMAIL.

    DATA lt_mail_auth TYPE TABLE OF ytbc_mail_auth.

    SELECT * INTO TABLE lt_mail_auth FROM ytbc_mail_auth WHERE yappl = 'PA_WF'.

    LOOP AT ct_email ASSIGNING FIELD-SYMBOL(<lv_email>).
      READ TABLE lt_mail_auth TRANSPORTING NO FIELDS WITH KEY ymail = <lv_email>.
      IF sy-subrc <> 0.
        CONCATENATE <lv_email> 'TEST' INTO <lv_email>.
      ENDIF.
    ENDLOOP.

  endmethod.


  METHOD get_data.

    DATA lv_date_c(10) TYPE c.
    DATA lv_atx TYPE anstx.

    me->put_to_container( iv_field = '<PERNR>' iv_value = mv_objid ).
    WRITE mv_date_ref TO lv_date_c DD/MM/YYYY.
    me->put_to_container( iv_field = '<DATE>' iv_value = lv_date_c ).
    me->put_to_container( iv_field = '<ENAME_EN>' iv_value = mv_ename_en ).
    me->put_to_container( iv_field = '<ENAME_FR>' iv_value = mv_ename_fr ).
    me->put_to_container( iv_field = '<MASSN_EN>' iv_value = mv_massn_txt_en ).
    me->put_to_container( iv_field = '<MASSN_FR>' iv_value = mv_massn_txt_fr ).
    me->put_to_container( iv_field = '<MASSG_EN>' iv_value = mv_massg_txt_en ).
    me->put_to_container( iv_field = '<MASSG_FR>' iv_value = mv_massg_txt_fr ).
    me->put_to_container( iv_field = '<SHORT_S>' iv_value = mv_short_s ).
    me->put_to_container( iv_field = '<STEXT_S_EN>' iv_value = mv_stext_s_en ).
    me->put_to_container( iv_field = '<STEXT_S_FR>' iv_value = mv_stext_s_fr ).
    me->put_to_container( iv_field = '<STEXT_O_EN>' iv_value = mv_stext_o_en ).
    me->put_to_container( iv_field = '<STEXT_O_FR>' iv_value = mv_stext_o_fr ).
    me->put_to_container( iv_field = '<WI_FATHER>' iv_value = mv_wi_father ).
    me->put_to_container( iv_field = '<GRADE>' iv_value = mo_wf_factory->mo_main_class->ms_employee_data-trfgr ).
    IF mv_current_actor-otype = 'US'.
      me->put_to_container( iv_field = '<UNAME_TXT>' iv_value = ycl_wf_utilities=>get_username( mv_current_actor-objid ) ).
    ENDIF.

    WRITE sy-datum TO lv_date_c DD/MM/YYYY.
    me->put_to_container( iv_field = '<SYSTDATE>' iv_value = lv_date_c ).

    "Work contract text
    SELECT SINGLE atx INTO lv_atx FROM t542t WHERE spras = 'E'
                                             AND   molga = 'UN'
                                             AND   ansvh = mo_wf_factory->mo_main_class->ms_employee_data-p0001-ansvh.
    me->put_to_container( iv_field = '<CONTRACT>' iv_value = lv_atx ).

    IF mt_reason IS NOT INITIAL.
      me->put_to_container( iv_field = '<REASON>' iv_value = me->convert_reason_to_string( ) ).
    ENDIF.

    "Get duty station
    ycl_hr_wf_get_data=>get_ds_from_werks_brtrl( EXPORTING iv_werks = mo_wf_factory->mo_main_class->ms_employee_data-p0001-werks
                                                           iv_btrtl = mo_wf_factory->mo_main_class->ms_employee_data-p0001-btrtl
                                                 IMPORTING ev_dstxt = DATA(lv_dstxt) ).
    me->put_to_container( iv_field = '<DUTY>' iv_value = lv_dstxt ).

    "org unit root
    READ TABLE mo_wf_factory->mo_main_class->ms_employee_data-orgunit_up INTO DATA(ls_orgunit_root)
              WITH KEY otype = 'O'
                       objid = mo_wf_factory->mo_main_class->ms_employee_data-orgunit_root.
    IF sy-subrc IS INITIAL.
      me->put_to_container( iv_field = '<ORGUNIT_ROOT>' iv_value = ls_orgunit_root-stext ).
    ENDIF.

  ENDMETHOD.


  METHOD initialize_data.

    DATA lt_p1000 TYPE TABLE OF p1000.
    DATA ls_p1000 TYPE p1000.

    "Initialisation of WF business class
    mo_wf_factory = ycl_hrwf_factory=>get_instance( ypawf_c_wftype_s1 ).

    "Get employee data
    mo_wf_factory->mo_main_class->get_employee_data( iv_pernr = mv_objid
                                                     iv_action_date = mv_date_ref ).
    "Build formatted name
    CONCATENATE mo_wf_factory->mo_main_class->ms_employee_data-atext_en
                mo_wf_factory->mo_main_class->ms_employee_data-nachn
                mo_wf_factory->mo_main_class->ms_employee_data-vorna
                INTO mv_ename_en SEPARATED BY space.
    CONCATENATE mo_wf_factory->mo_main_class->ms_employee_data-atext_fr
                mo_wf_factory->mo_main_class->ms_employee_data-nachn
                mo_wf_factory->mo_main_class->ms_employee_data-vorna
                INTO mv_ename_fr SEPARATED BY space.

    "Get employee position text
    mo_wf_factory->mo_read_infty_pd->read_infotype( EXPORTING iv_otype = 'S'
                                                              iv_objid = mo_wf_factory->mo_main_class->ms_employee_data-p0001-plans
                                                              iv_infty = '1000'
                                                              iv_istat = '1'
                                                              iv_begda = mv_date_ref
                                                              iv_endda = mv_date_ref
                                                    IMPORTING et_pnnnn = lt_p1000 ).
    READ TABLE lt_p1000 INTO ls_p1000 WITH KEY langu = 'EN'.
    IF sy-subrc = 0.
      mv_short_s = ls_p1000-short.
      mv_stext_s_en = ls_p1000-stext.
    ENDIF.

    READ TABLE lt_p1000 INTO ls_p1000 WITH KEY langu = 'FR'.
    IF sy-subrc = 0.
      mv_stext_s_fr = ls_p1000-stext.
    ELSE.
      mv_stext_s_fr = mv_stext_s_en.
    ENDIF.

    "Get employee org unit text
    CLEAR lt_p1000.
    mo_wf_factory->mo_read_infty_pd->read_infotype( EXPORTING iv_otype = 'O'
                                                              iv_objid = mo_wf_factory->mo_main_class->ms_employee_data-p0001-orgeh
                                                              iv_infty = '1000'
                                                              iv_istat = '1'
                                                              iv_begda = mv_date_ref
                                                              iv_endda = mv_date_ref
                                                    IMPORTING et_pnnnn = lt_p1000 ).
    READ TABLE lt_p1000 INTO ls_p1000 WITH KEY langu = 'EN'.
    IF sy-subrc = 0.
      mv_stext_o_en = ls_p1000-stext.
    ENDIF.

    READ TABLE lt_p1000 INTO ls_p1000 WITH KEY langu = 'FR'.
    IF sy-subrc = 0.
      mv_stext_o_fr = ls_p1000-stext.
    ELSE.
      mv_stext_o_fr = mv_stext_o_en.
    ENDIF.

    "Get Action type and reason for action text
    SELECT SINGLE mntxt INTO mv_massn_txt_en FROM t529t WHERE sprsl = 'E'
                                                        AND   massn = mv_massn.
    SELECT SINGLE mntxt INTO mv_massn_txt_fr FROM t529t WHERE sprsl = 'F'
                                                        AND   massn = mv_massn.
    SELECT SINGLE mgtxt INTO mv_massg_txt_en FROM t530t WHERE sprsl = 'E'
                                                        AND   massn = mv_massn
                                                        AND   massg = mv_massg.
    SELECT SINGLE mgtxt INTO mv_massg_txt_fr FROM t530t WHERE sprsl = 'F'
                                                        AND   massn = mv_massn
                                                        AND   massg = mv_massg.
    "Get WF step designation
    DATA(lt_steps) = mo_wf_factory->mo_main_class->get_wf_steps( iv_pernr = mv_objid
                                                                 iv_action_date = mv_date_ref ).
    READ TABLE lt_steps INTO DATA(ls_step) WITH KEY wfstep = mv_wf_step.
    IF sy-subrc = 0.
      mv_wf_step_txt = ls_step-wfstept.
    ENDIF.

  ENDMETHOD.


  METHOD replace_in_header.

    DATA lv_date_c(10) TYPE c.

    REPLACE '<ENAME_EN>' WITH mv_ename_en INTO cv_string.
    REPLACE '<MASSN_EN>' WITH mv_massn_txt_en INTO cv_string.
    REPLACE '<SHORT_S>' WITH mv_short_s INTO cv_string.
    REPLACE '<MASSG_EN>' WITH mv_massg_txt_en INTO cv_string.

    WRITE mv_date_ref TO lv_date_c.
    REPLACE '<DATE>' WITH lv_date_c INTO cv_string.

    CONDENSE cv_string.

  ENDMETHOD.
ENDCLASS.