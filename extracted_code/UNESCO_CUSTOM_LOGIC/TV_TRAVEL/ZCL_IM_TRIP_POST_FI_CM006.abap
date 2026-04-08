method IF_EX_TRIP_POST_FI~MODIFY_PTRV_DOC_HD .

data: w_pernr type ptrv_head-pernr,
      w_datv1 type ptrv_head-datv1.
DATA lt_p0001 TYPE TABLE OF p0001.
DATA ls_p0001 TYPE p0001.


clear: w_pernr, w_datv1.
select single pernr datv1
      into (w_pernr, w_datv1)
      from ptrv_head
      where reinr = ptrv_doc_hd-xblnr.

  refresh lt_p0001.
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr                =  w_pernr
      infty                = '0001'
     begda                 =  w_datv1
     endda                 =  w_datv1
    TABLES
      infty_tab            = lt_p0001
  EXCEPTIONS
    INFTY_NOT_FOUND       = 1
    OTHERS                = 2.

  IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDIF.

  READ TABLE lt_p0001 INTO ls_p0001 INDEX 1 .

  CHECK sy-subrc = 0.

  if ls_p0001-bukrs = 'UNES' and
     ls_p0001-werks <> 'FR00'.
    ptrv_doc_hd-blart = 'TF'.
   else.
     ptrv_doc_hd-blart = 'TV'.
  endif. "UNES

  if ls_p0001-bukrs = 'UIS'.
    if ls_p0001-werks = 'CA03'.
      ptrv_doc_hd-blart = 'TV'.
     else.
       ptrv_doc_hd-blart = 'TF'.
    endif.
  endif. "UIS

  if ls_p0001-bukrs = 'IIEP'.
***I_KONAKOV 30/09/2015 - changed on request from L.Caballe
***    if ls_p0001-werks = 'AR01'.
***      ptrv_doc_hd-blart = 'TF'.
***     else.
***       ptrv_doc_hd-blart = 'TV'.
***    endif.
    if ls_p0001-werks = 'FR01'.
      ptrv_doc_hd-blart = 'TV'.
     else.
       ptrv_doc_hd-blart = 'TF'.
    endif.
***
  endif. "IIEP

  if ls_p0001-bukrs = 'UIL'.
    if ls_p0001-werks = 'DE05'.
      ptrv_doc_hd-blart = 'TV'.
     else.
       ptrv_doc_hd-blart = 'TF'.
    endif.
  endif. "UIL

endmethod.
