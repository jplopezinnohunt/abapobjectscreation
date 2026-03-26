*&---------------------------------------------------------------------*
*&  Include           ZXFMYU33                                         *
*&---------------------------------------------------------------------*
  DATA:
    L_KOKRS LIKE IONRA-KOKRS,
    L_LSTAR LIKE IONRA-LSTAR,
    L_KOSTL LIKE IONRA-KOSTL.

  IF I_COEP-OBJNR(2) = 'KL'.

    CLEAR C_ROBJNRZ.

    CALL FUNCTION 'OBJECT_KEY_GET_KL'
      EXPORTING
        OBJNR       = I_COEP-OBJNR
      IMPORTING
        KOKRS       = L_KOKRS
        KOSTL       = L_KOSTL
        LSTAR       = L_LSTAR
      EXCEPTIONS
        NOT_FOUND   = 1
        WRONG_OBART = 2
        OTHERS      = 3.

    C_ROBJNRZ   = 'KS'.
    C_ROBJNRZ+2 = L_KOKRS.
    C_ROBJNRZ+6 = L_KOSTL.

 ENDIF.

*{   DELETE         HRFK900002                                        1
*\*>>>> START OF INSERTION <<<<
*\  DATA:
*\    l_kokrs LIKE ionra-kokrs,
*\    l_lstar LIKE ionra-lstar,
*\    l_kostl LIKE ionra-kostl.
*\
*\  IF i_coep-objnr(2) = 'KL'.
*\
*\    CLEAR C_ROBJNRZ.
*\
*\    CALL FUNCTION 'OBJECT_KEY_GET_KL'
*\      EXPORTING
*\        objnr       = i_coep-objnr
*\      IMPORTING
*\        kokrs       = l_kokrs
*\        kostl       = l_kostl
*\        lstar       = l_lstar
*\      EXCEPTIONS
*\        not_found   = 1
*\        wrong_obart = 2
*\        OTHERS      = 3.
*\
*\    C_ROBJNRZ   = 'KS'.
*\    C_ROBJNRZ+2 = l_kokrs.
*\    C_ROBJNRZ+6 = l_kostl.
*\
*\ ENDIF.
*\*>>>> END OF INSERTION <<<<<<
*\
*}   DELETE