METHOD validate_employee.

  " Initialisation
  CLEAR rs_return.

  " Vérification du paramètre d'entrée
  IF iv_persno IS INITIAL.
    rs_return-type    = 'E'.
*    rs_return-message = 'Personal number required'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '055'
      INTO rs_return-message.
    RETURN.
  ENDIF.

  " Variables locales
  DATA: lt_p0000 TYPE TABLE OF p0000,
        ls_p0000 TYPE p0000.

  " Lecture IT0000 (Actions)
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr         = iv_persno
      infty         = '0000'
      begda         = sy-datum
      endda         = sy-datum
    TABLES
      infty_tab     = lt_p0000
    EXCEPTIONS
      infty_not_found = 1
      others          = 2.

  IF sy-subrc = 0 AND lt_p0000 IS NOT INITIAL.
    READ TABLE lt_p0000 INTO ls_p0000 INDEX 1.
    IF sy-subrc = 0 AND ls_p0000-stat2 = '3'.  " Employé actif
      rs_return-type    = 'S'.
*      rs_return-message = |Employee { iv_persno } is active.|.
      MESSAGE ID 'ZHRFIORI' TYPE 'S' NUMBER '056'
        INTO rs_return-message WITH iv_persno.
      RETURN.
    ENDIF.
  ENDIF.

  " Si aucune donnée valide
  rs_return-type    = 'E'.
  MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '057'
        INTO rs_return-message WITH iv_persno.

ENDMETHOD.
