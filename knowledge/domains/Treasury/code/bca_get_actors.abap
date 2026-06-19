FUNCTION BCA_API_REL_GET_ACTORS
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




CALL FUNCTION 'BCA_OBJ_REL_GET_ACTORS'
  EXPORTING
    i_object_cat          = i_object_cat
    i_rel_procedure       = i_rel_procedure
    i_stepnumber          = i_stepnumber
    i_structure           = i_structure
  tables
    actor_tab             = actor_tab
 EXCEPTIONS
   NOT_CUSTOMIZED        = 1
   NOBODY_FOUND          = 2
          .
case sy-subrc.
when '1'.
 MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
        WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4 raising not_customized.
when '2'.
 MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
        WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4 raising nobody_found.
endcase.

ENDFUNCTION.