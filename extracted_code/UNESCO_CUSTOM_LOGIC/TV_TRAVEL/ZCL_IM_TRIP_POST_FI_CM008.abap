method IF_EX_TRIP_POST_FI~EX_ZWEP .
  DATA lt_p0001 TYPE TABLE OF p0001.
  DATA ls_p0001 TYPE p0001.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr                =  zwep-pernr
      infty                = '0001'
     begda                 =  zwep-datv1
     endda                 =  zwep-datv1
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

  CHECK sy-subrc = 0.

  if ls_p0001-bukrs =  'UNES' and
     ls_p0001-werks <> 'FR00'.
    zwep-blart = 'TF'.
   else.
     zwep-blart = 'TV'.
  endif.

endmethod.
