FUNCTION BCA_OBJ_REL_GET_ACTORS
  IMPORTING
    I_OBJECT_CAT TYPE BCA_DTE_OBJECT_CAT
    I_REL_PROCEDURE TYPE BCA_DTE_REL_PROC
    I_STEPNUMBER TYPE BCA_DTE_STEPNUMBER
    I_STRUCTURE TYPE ANY ##ADT_PARAMETER_UNTYPED
  TABLES
    ACTOR_TAB LIKE SWHACTOR
  EXCEPTIONS
    NOT_CUSTOMIZED
    NOBODY_FOUND.



* local data declaration
  DATA: l_rule_key             TYPE bca_str_rel_rule_key,
        l_rule                 TYPE bca_str_rel_rule_data,
        l_rule_object          TYPE swhactor,
        l_rule_obj             TYPE rhobjects-object,
        l_contdef              TYPE STANDARD TABLE OF swcontdef,
        wa_contdef             TYPE swcontdef,
        l_container            TYPE STANDARD TABLE OF swcont,
        l_object_cat_key       TYPE bca_str_rel_obj_cat_key,
        l_str_rel_obj_cat_data TYPE bca_str_rel_obj_cat_data,
        dref                   TYPE REF TO data.

  FIELD-SYMBOLS: <fs_struct> TYPE any,
                 <fs_comp>   TYPE any.

* set local variables
  l_rule_key-object_cat = i_object_cat.
  l_rule_key-rel_procedure = i_rel_procedure.
  l_rule_key-stepnumber = i_stepnumber.

* get rule from customizing table
  CALL FUNCTION 'BCA_DB_REL_RULE_SEL_SINGLE'
    EXPORTING
      i_str_rel_rule_key = l_rule_key
    IMPORTING
      e_str_el_rule_data = l_rule
    EXCEPTIONS
      not_found          = 1
      OTHERS             = 2.
  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
      WITH sy-msgv1 sy-msgv2 sy-msgv4 sy-msgv4
      RAISING not_customized.
  ENDIF.

  l_rule_object-otype = c_wf_rule_type.
  l_rule_object-objid = l_rule.
  l_rule_obj = l_rule_object.

* get list of used attributes for  role resolution
  CALL FUNCTION 'RH_GET_ACTOR_ATTRIBUTES'
    EXPORTING
      act_object_ext   = l_rule_obj
      read_container   = 'X'
      authority_check  = 'X'
      bypassing_buffer = 'X'
      act_langu        = sy-langu
    TABLES
      act_cont_def     = l_contdef
    EXCEPTIONS
      object_not_found = 1
      OTHERS           = 2.
  IF sy-subrc <> 0.
    MESSAGE e229(bca_release_wf) WITH i_object_cat i_rel_procedure
      i_stepnumber RAISING not_customized.
  ENDIF.

* get the name of the structure with application data
  l_object_cat_key-object_cat = i_object_cat.

  CALL FUNCTION 'BCA_DB_REL_OBJ_CAT_SEL_SINGLE'
    EXPORTING
      i_str_rel_obj_cat_key  = l_object_cat_key
    IMPORTING
      e_str_rel_obj_cat_data = l_str_rel_obj_cat_data
    EXCEPTIONS
      not_found              = 1
      OTHERS                 = 2.
  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.

* create structure with the type of application data
  CATCH SYSTEM-EXCEPTIONS  create_data_unknown_type     = 1
                           create_data_not_allowed_type = 2
                           OTHERS                       = 3.
    CREATE DATA dref TYPE (l_str_rel_obj_cat_data-structurename).
  ENDCATCH.
  IF sy-subrc NE 0.
    MESSAGE x229(bca_release_wf) WITH i_object_cat i_rel_procedure
     i_stepnumber RAISING not_customized.
  ENDIF.

  ASSIGN dref->* TO <fs_struct>.

  <fs_struct> = i_structure.

* fill container with data
  LOOP AT l_contdef INTO wa_contdef.

    ASSIGN COMPONENT wa_contdef-element OF STRUCTURE <fs_struct>
                                        TO <fs_comp>.

    swc_set_element l_container wa_contdef-element <fs_comp>.

  ENDLOOP.

** refresh organizational environment
*  CALL FUNCTION 'RH_INBOX_VIEW_BUFFER_REFRESH'.

* call rule for actors
  CALL FUNCTION 'RH_GET_ACTORS'
    EXPORTING
      act_object                = l_rule_obj
    TABLES
      actor_container           = l_container
      actor_tab                 = actor_tab
    EXCEPTIONS
      no_active_plvar           = 1
      no_actor_found            = 2
      exception_of_role_raised  = 3
      no_valid_agent_determined = 4
      OTHERS                    = 5.
  IF sy-subrc <> 0.
    MESSAGE e230(bca_release_wf) WITH l_rule  RAISING nobody_found.
  ENDIF.

ENDFUNCTION.