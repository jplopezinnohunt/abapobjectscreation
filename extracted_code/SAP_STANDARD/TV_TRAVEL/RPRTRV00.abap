*----------------------------------------------------------------------*
*   INCLUDE RPRTRV00                                                   *
*----------------------------------------------------------------------*
* 6.00
* MAWAENK017862 20041130 Performance-Verbesserung für WEB-Transaktion
*                        [note 789716]
* 5.00
* MAWPLNK071524 27012004 Initialwerte in der Tabelle V_T702N_A
*                        (note 701158)
* 4.6C
* XFUAHRK056058 010999 enable simple value return for feature TRVCT
* 4.0C
* XVYAHRK017129 060498 redesign of reading morei / trvct
*                      routines read_morei / read_t702n
* XVYAHRK007941 170498 read trvct without variation
* XVYAHRK007941 240398 read trvct after redesign

*&---------------------------------------------------------------------*
*&      Form  READ_MOREI
*&
*&      Ermittlung der Reiseregelungsvariante (MOREI)
*&---------------------------------------------------------------------*
*      <--P_MOREI  text
*      -->P_KIND_OF_ERROR
*      <--P_STATUS
*----------------------------------------------------------------------*

FORM read_morei USING p_morei
                      p_kind_of_error
                      p_status.

  DATA:  p_funct LIKE t549d-funct.

  SELECT SINGLE funct FROM  t549d INTO p_funct
                      WHERE namen = 'TRVCT'.
  IF sy-subrc NE 0.
    MESSAGE e732(56).
  ELSE.
*   if p_funct+14(1) = '1'.                              "VLDPH4K014073
    IF p_funct+20(1) = '1'.                              "VLDPH4K014073
      PERFORM re549d USING 'TRVCT' p_kind_of_error p_morei p_status.
    ELSEIF p_funct+20(1) = ' '.                             "XFUK056058
*     einfache Wertrueckgabe                             "XFUK056058
      p_status = 0.                                         "XFUK056058
      p_morei  = p_funct+0(2).                              "XFUK056058
    ELSE.
* TRVCT wurde noch nicht umgesetzt.
      MESSAGE e696(56).
    ENDIF.
  ENDIF.
ENDFORM.                               " READ_MOREI

*&---------------------------------------------------------------------*
*&      Form  READ_T702N
*&
*&      Lesen des Merkmals TRVCT mit dem aktuellen MOREI
*&      Gibt das Merkmal TRVCT direkt in der aufbereiteten Form
*&      zurück, z.B. varia_b = 'B...'
*&---------------------------------------------------------------------*
*      -->P_MOREI
*      <--P_VARIA_B
*      <--P_VARIA_V
*      <--P_VARIA_U
*      <--P_VARIA_F
*      <--P_VARIA_R
*      <--P_VARIA_P
*      <--P_SUBRC
*----------------------------------------------------------------------*

FORM read_t702n USING p_morei
                      p_varia_b
                      p_varia_v
                      p_varia_u
                      p_varia_f
                      p_varia_r
                      p_varia_p
                      p_subrc.

  DATA: *t702n LIKE t702n.
  DATA: varia_trvct_b LIKE ptrv_trvct_b,
        varia_trvct_v LIKE ptrv_trvct_v,
        varia_trvct_u LIKE ptrv_trvct_u,
        varia_trvct_f LIKE ptrv_trvct_f,
        varia_trvct_r LIKE ptrv_trvct_r,
        varia_trvct_p LIKE ptrv_trvct_p.

  p_subrc = 0.

  IF NOT t702n-morei = p_morei.                             "MAWK071524

    SELECT SINGLE * FROM t702n WHERE morei = p_morei.

    IF sy-subrc NE 0.
      p_subrc = sy-subrc.
      CLEAR p_varia_b.
      CLEAR p_varia_u.
      CLEAR p_varia_v.
      CLEAR p_varia_f.
      CLEAR p_varia_r.
      CLEAR p_varia_p.
      MESSAGE e860(56) WITH p_morei.
    ENDIF.                                                  "MAWK071524
                                                            "MAWK071524
* Im der Tabelle T702N dürfen keine Initialwerte vorkommen! "MAWK071524
    PERFORM check_t702n USING    t702n                      "MAWK071524
                                 p_morei                    "MAWK071524
                        CHANGING p_subrc.                   "MAWK071524
*  ELSE.                                                    "MAWK071524
  ENDIF.                                                    "MAWK071524
  MOVE-CORRESPONDING t702n TO varia_trvct_b.
  MOVE-CORRESPONDING t702n TO varia_trvct_v.
  MOVE-CORRESPONDING t702n TO varia_trvct_u.
  MOVE-CORRESPONDING t702n TO varia_trvct_f.
  MOVE-CORRESPONDING t702n TO varia_trvct_r.
  MOVE-CORRESPONDING t702n TO varia_trvct_p.

  p_varia_b+1(30) = varia_trvct_b.
  p_varia_b+0(1) = 'B'.
  p_varia_v+1(30) = varia_trvct_v.
  p_varia_v+0(1) = 'V'.
  p_varia_u+1(30) = varia_trvct_u.
  p_varia_u+0(1) = 'U'.
  p_varia_f+1(30) = varia_trvct_f.
  p_varia_f+0(1) = 'F'.
  p_varia_r+1(30) = varia_trvct_r.
  p_varia_r+0(1) = 'R'.
  p_varia_p+1(30) = varia_trvct_p.
  p_varia_p+0(1) = 'P'.
*  ENDIF.                                                   "MAWK071524

ENDFORM.                               " READ_T702N



**&--------------------------------------------------------------------*
**&      Form  RE702N_TAB
**&
**&      Lesen des Merkmals TRVCT mit dem aktuellen MOREI
**&      Gibt das Merkmal TRVCT direkt in der aufbereiteten Form
**&      zurück, z.B. varia_b = 'B...'
**&--------------------------------------------------------------------*
*FORM RE702N_TAB USING P_MOREI
*                      P_VARIA_B
*                      P_VARIA_V
*                      P_VARIA_U
*                      P_VARIA_F
*                      P_VARIA_R
*                      P_VARIA_P
*                      P_SUBRC.
*
*  DATA: *T702N LIKE T702N.
*  DATA: VARIA_TRVCT_B LIKE PTRV_TRVCT_B,
*        VARIA_TRVCT_V LIKE PTRV_TRVCT_V,
*        VARIA_TRVCT_U LIKE PTRV_TRVCT_U,
*        VARIA_TRVCT_F LIKE PTRV_TRVCT_F,
*        VARIA_TRVCT_R LIKE PTRV_TRVCT_R,
*        VARIA_TRVCT_P LIKE PTRV_TRVCT_P.
*
*  P_SUBRC = 0.
*
*  SELECT SINGLE * FROM T702N WHERE MOREI = P_MOREI.
*
*  IF SY-SUBRC NE 0.
*    P_SUBRC = SY-SUBRC.
*    CLEAR P_VARIA_B.
*    CLEAR P_VARIA_U.
*    CLEAR P_VARIA_V.
*    CLEAR P_VARIA_F.
*    CLEAR P_VARIA_R.
*    CLEAR P_VARIA_P.
*    MESSAGE E860(56) WITH P_MOREI.
*  ELSE.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_B.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_V.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_U.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_F.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_R.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_P.
*
*    P_VARIA_B+1(30) = VARIA_TRVCT_B.
*    P_VARIA_B+0(1) = 'B'.
*    P_VARIA_V+1(30) = VARIA_TRVCT_V.
*    P_VARIA_V+0(1) = 'V'.
*    P_VARIA_U+1(30) = VARIA_TRVCT_U.
*    P_VARIA_U+0(1) = 'U'.
*    P_VARIA_F+1(30) = VARIA_TRVCT_F.
*    P_VARIA_F+0(1) = 'F'.
*    P_VARIA_R+1(30) = VARIA_TRVCT_R.
*    P_VARIA_R+0(1) = 'R'.
*    P_VARIA_P+1(30) = VARIA_TRVCT_P.
*    P_VARIA_P+0(1) = 'P'.
*  ENDIF.
*
*ENDFORM.                               " RE702N_TAB
*
**&--------------------------------------------------------------------*
**&      Form  CHECK_TRVCT_T702N
**&
**&      Ermittlung der Reiseregelungsvariante (MOREI) und Lesen des
**&      Mekmals TRVCT mit dem aktuellen MOREI
**&--------------------------------------------------------------------*
*FORM CHECK_TRVCT_T702N USING P_MOREI
*                             P_KIND_OF_ERROR
*                             P_STATUS
*                             P_VARIA_B
*                             P_VARIA_V
*                             P_VARIA_U
*                             P_VARIA_F
*                             P_VARIA_R
*                             P_VARIA_P.
*
*  DATA: *T702N LIKE T702N.
*  DATA: VARIA_TRVCT_B LIKE PTRV_TRVCT_B,
*        VARIA_TRVCT_V LIKE PTRV_TRVCT_V,
*        VARIA_TRVCT_U LIKE PTRV_TRVCT_U,
*        VARIA_TRVCT_F LIKE PTRV_TRVCT_F,
*        VARIA_TRVCT_R LIKE PTRV_TRVCT_R,
*        VARIA_TRVCT_P LIKE PTRV_TRVCT_P,
*        P_FUNCT LIKE T549D-FUNCT,
*        ANZ_LINES TYPE I.
*
*  SELECT SINGLE FUNCT FROM  T549D INTO P_FUNCT
*                      WHERE NAMEN = 'TRVCT'.
*
* IF P_FUNCT+14(1) = '1'.
*    PERFORM RE549D USING 'TRVCT' P_KIND_OF_ERROR P_MOREI P_STATUS.
*  ELSE.
**    perform re549d_tab tables variation
**                   using 'TRVCT' p_kind_of_error p_status.
**    describe table variation lines anz_lines.
**    if anz_lines > 1.
*      MESSAGE E696(56).
**    else.
**      loop at variation.
**        move variation-varia(2) to p_morei.
**      endloop.
**    endif.
*  ENDIF.
*
*  SELECT SINGLE * FROM T702N WHERE MOREI = P_MOREI.
*
*  IF SY-SUBRC NE 0.
*    CLEAR P_VARIA_B.
*    CLEAR P_VARIA_U.
*    CLEAR P_VARIA_V.
*    CLEAR P_VARIA_F.
*    CLEAR P_VARIA_R.
*    CLEAR P_VARIA_P.
*  ELSE.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_B.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_V.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_U.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_F.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_R.
*    MOVE-CORRESPONDING T702N TO VARIA_TRVCT_P.
*
*    P_VARIA_B+1(30) = VARIA_TRVCT_B.
*    P_VARIA_B+0(1) = 'B'.
*    P_VARIA_V+1(30) = VARIA_TRVCT_V.
*    P_VARIA_V+0(1) = 'V'.
*    P_VARIA_U+1(30) = VARIA_TRVCT_U.
*    P_VARIA_U+0(1) = 'U'.
*    P_VARIA_F+1(30) = VARIA_TRVCT_F.
*    P_VARIA_F+0(1) = 'F'.
*    P_VARIA_R+1(30) = VARIA_TRVCT_R.
*    P_VARIA_R+0(1) = 'R'.
*    P_VARIA_P+1(30) = VARIA_TRVCT_P.
*    P_VARIA_P+0(1) = 'P'.
*  ENDIF.
*
*ENDFORM.                               " CHECK_TRVCT_T702N
*

*&---------------------------------------------------------------------*
*&      Form  check_t702n
*&---------------------------------------------------------------------*
*       FORM neu zu MAWK071524
*----------------------------------------------------------------------*
*      -->P_T702N  text
*      <--P_P_SUBRC  text
*----------------------------------------------------------------------*
FORM check_t702n USING    p_t702n
                          p_morei
                 CHANGING p_subrc.

  DATA: l_tabname TYPE ddobjname,
        lt_tablestructure TYPE TABLE OF dfies,
        lwa_tablestructure LIKE dfies,
        lwa_t702n LIKE t702n,
        lf_table_field TYPE c LENGTH 61.

  FIELD-SYMBOLS <field> TYPE c.

  l_tabname = 'T702N'.

* Begin of MAWK017862
*  CALL FUNCTION 'DDIF_FIELDINFO_GET'
*    EXPORTING
*      tabname        = l_tabname
*    TABLES
*      dfies_tab      = lt_tablestructure
*    EXCEPTIONS
*      not_found      = 1
*      internal_error = 2
*      OTHERS         = 3.
CALL FUNCTION 'DDIF_NAMETAB_GET'
  EXPORTING
    tabname           = l_tabname
 TABLES
   DFIES_TAB         = lt_tablestructure
 EXCEPTIONS
   NOT_FOUND         = 1
   OTHERS            = 2.
* End of MAWK017862
  IF sy-subrc <> 0.
    p_subrc = sy-subrc.
*     Fehler im FB &1. Bitte benachrichtigen Sie ihren
*     Systemadministrator.
    MESSAGE ID '56' TYPE 'E' NUMBER '895' WITH 'DDIF_FIELDINFO_GET'.
  ENDIF.
  CLEAR l_tabname.
  DELETE lt_tablestructure WHERE fieldname = 'MANDT' OR
                                 fieldname = 'MOREI'.
  LOOP AT lt_tablestructure INTO lwa_tablestructure.
    CONCATENATE 'P_T702N' lwa_tablestructure-fieldname
           INTO lf_table_field
      SEPARATED BY '-'.
    ASSIGN (lf_table_field) TO <field>.
    IF <field> EQ ' '.
      p_subrc = sy-subrc.
      lwa_tablestructure-tabname = 'V_T702N_A'.
      IF <field> IS ASSIGNED.
        UNASSIGN <field>.
      ENDIF.
*     Die Tabelle &1, Argument &2 ist nicht vollständig gepflegt.
      MESSAGE ID '56' TYPE 'E' NUMBER '896'
                      WITH lwa_tablestructure-tabname
                           p_morei.
    ENDIF.
    IF <field> IS ASSIGNED.
      UNASSIGN <field>.
    ENDIF.
  ENDLOOP.

ENDFORM.                    " check_t702n