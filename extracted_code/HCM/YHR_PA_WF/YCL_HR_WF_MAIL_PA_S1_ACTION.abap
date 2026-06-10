class YCL_HR_WF_MAIL_PA_S1_ACTION definition
  public
  inheriting from YCL_HR_WF_MAIL_GENERATOR_PA_S1
  final
  create public .

public section.
protected section.

  methods REPLACE_IN_HEADER
    redefinition .
  methods GET_DATA
    redefinition .
private section.
ENDCLASS.



CLASS YCL_HR_WF_MAIL_PA_S1_ACTION IMPLEMENTATION.


  METHOD get_data.

    DATA lv_url TYPE string.

    super->get_data( ).

    CONCATENATE mv_protocol '://hq-sap-' sy-sysid '.hq.int.unesco.org/sap/bc/webdynpro/sap/ibo_wda_inbox?'
            'sap-system-login-basic_auth=X&sap-language=EN&sap-wd-configId=YUNESCO_WDAC_POWL_INBOX#' INTO lv_url.

    me->put_to_container( iv_field = '<URL>' iv_value = lv_url ).

  ENDMETHOD.


  METHOD replace_in_header.

    DATA lv_text TYPE text30.

    super->replace_in_header( CHANGING cv_string = cv_string ).

    IF mv_wf_step = 'D' OR
       mv_wf_step = 'E' OR
       mv_wf_step = 'F' OR
       mv_wf_step = 'G'.
      lv_text = |{ mv_wf_step_txt }/|.
      REPLACE '<WFSTEP>' WITH lv_text INTO cv_string.
    ELSE.
      REPLACE '<WFSTEP>' WITH space INTO cv_string.
    ENDIF.

    CONDENSE cv_string.

  ENDMETHOD.
ENDCLASS.