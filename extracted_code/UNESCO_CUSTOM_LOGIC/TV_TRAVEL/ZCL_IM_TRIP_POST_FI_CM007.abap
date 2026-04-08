METHOD if_ex_trip_post_fi~exb706k .
  DATA l_trvus TYPE trvus.
  DATA lt_p0001 TYPE TABLE OF p0001.
  DATA ls_p0001 TYPE p0001.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr                =  t_head-pernr
      infty                = '0001'
     begda                 =  t_head-datv1
     endda                 =  t_head-datv1
    TABLES
      infty_tab            = lt_p0001
* EXCEPTIONS
*   INFTY_NOT_FOUND       = 1
*   OTHERS                = 2
            .
  IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDIF.

  READ TABLE lt_p0001 INTO ls_p0001 INDEX 1 .

  CHECK sy-subrc EQ  0.

  clear l_trvus.
  CALL METHOD zcl_tv_t9tvacc=>read
    EXPORTING
      persg = ls_p0001-persg
      morei = morei
      kzrea = t_head-kzrea
      kztkt = t_head-kztkt
    RECEIVING
      trvus = l_trvus.

  IF NOT l_trvus IS INITIAL.
    users = l_trvus.
  ENDIF.

  if ( ls_p0001-bukrs = 'UNES' or
       ls_p0001-bukrs = 'UBO'  or
       ls_p0001-bukrs = 'UIL'  or
       ls_p0001-bukrs = 'IIEP' or
       ls_p0001-bukrs = 'UIS' ) and
     ls_p0001-werks <> 'FR00'.
    if lgart = 'MJ63' or lgart = 'MJ64'.
      select single focod into users
                          from yfo_parea
                          where parea = ls_p0001-werks
                            and sarea = ls_p0001-btrtl.
      if sy-subrc is initial.
        concatenate users l_trvus into users.
       else.
         users = 'FO'.
      endif. "sy-subrc
     else. "lgart
       clear l_trvus.
       CALL METHOD zcl_tv_t9tvacc=>read
         EXPORTING
           persg = ls_p0001-persg
           morei = morei
           kzrea = t_head-kzrea
           kztkt = t_head-kztkt
         RECEIVING
           trvus = l_trvus.

         users = l_trvus.
    endif. "lgart
  endif. "ls_p0001-bukrs

ENDMETHOD.
