method IF_EX_TRIP_POST_FI~EX_ZWEP_ACCOUNT2 .

DATA lt_p0027 TYPE TABLE OF p0027.
DATA ls_p0027 TYPE p0027.
data: w_kpr00 like ls_p0027-kpr01,
      w_kprix(2) type n,
      w_kpndx(2) type n,
      w_kprnm(15).

field-symbols <fs_kprnm> type any.

if zwep-bukst is initial or zwep-gsbst is initial.

  clear ls_p0027.
  refresh lt_p0027.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr                =  zwep-pernr
      infty                = '0027'
     begda                 =  zwep-datv1
     endda                 =  zwep-datv1
    TABLES
      infty_tab            = lt_p0027
* EXCEPTIONS
*   INFTY_NOT_FOUND       = 1
*   OTHERS                = 2
            .
  IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDIF.

  loop at lt_p0027 into ls_p0027 where subty = '02'.
  endloop.

  check sy-subrc is initial.

  clear: w_kpr00, w_kpndx.
  do 25 times. "look for highest percentage
    clear: w_kprnm, w_kprix.
    w_kprix = sy-index.
    concatenate 'ls_p0027-kpr' w_kprix into w_kprnm.
    assign (w_kprnm) to <fs_kprnm>.
    if <fs_kprnm> > w_kpr00.
      w_kpr00 = <fs_kprnm>.
      w_kpndx = w_kprix.
    endif.
  enddo.

  clear w_kprnm.
  concatenate 'ls_p0027-kbu' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-bukst = <fs_kprnm>. "ls_p0027-kbu01. "CoCode

  clear w_kprnm.
  concatenate 'ls_p0027-kgb' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-gsbst = <fs_kprnm>. "ls_p0027-kgb01. "B/Area
  zwep-gsber = <fs_kprnm>. "ls_p0027-kgb01. "B/Area

  clear w_kprnm.
  concatenate 'ls_p0027-kst' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-kstst = <fs_kprnm>. "ls_p0027-kst01. "Cost Center

  clear w_kprnm.
  concatenate 'ls_p0027-fct' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-fistl = <fs_kprnm>. "ls_p0027-fct01. "Fund Center

  clear w_kprnm.
  concatenate 'ls_p0027-fcd' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-geber = <fs_kprnm>. "ls_p0027-fcd01. "Fund

  clear w_kprnm.
  concatenate 'ls_p0027-psp' w_kpndx into w_kprnm.
  assign (w_kprnm) to <fs_kprnm>.
  zwep-posnr = <fs_kprnm>. "ls_p0027-psp01. "WBS-element

endif.

endmethod.
