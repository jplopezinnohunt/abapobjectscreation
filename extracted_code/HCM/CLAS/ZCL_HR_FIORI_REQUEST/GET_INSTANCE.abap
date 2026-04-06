 METHOD get_instance.
   IF mo_instance IS INITIAL.
     CREATE OBJECT mo_instance.
   ENDIF.

   ro_instance = mo_instance.
 ENDMETHOD.
