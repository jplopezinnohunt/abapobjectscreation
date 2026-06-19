FUNCTION BNK_API_GET_REL_ACTORS
  IMPORTING
    VALUE(I_REL_PROCEDURE) TYPE BCA_DTE_REL_PROC
    VALUE(I_STEPNUMBER) TYPE BCA_DTE_STEPNUMBER
    I_STRUCTURE TYPE ANY ##ADT_PARAMETER_UNTYPED
    VALUE(I_REL_OBJ_CAT) TYPE BCA_DTE_OBJECT_CAT DEFAULT 'BNK_COM'
  EXPORTING
    E_TAB_ACTORS TYPE TSWHACTOR
    E_TAB_RC TYPE BAPIRET2_T.





  CALL FUNCTION 'BCA_API_REL_GET_ACTORS'
    EXPORTING
      i_object_cat    = I_REL_OBJ_CAT
      i_rel_procedure = i_rel_procedure
      i_stepnumber    = i_stepnumber
      i_structure     = i_structure
    TABLES
      actor_tab       = e_tab_actors
    EXCEPTIONS
      not_customized  = 1
      nobody_found    = 2
      OTHERS          = 3.
  IF sy-subrc <> 0.

    PERFORM  return_code_fill
           USING     sy-msgid
                     sy-msgty
                     sy-msgno sy-msgv1
                     sy-msgv2  sy-msgv3  sy-msgv4
           CHANGING  e_tab_rc.

  ENDIF.



ENDFUNCTION.