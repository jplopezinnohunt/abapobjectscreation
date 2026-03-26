ENHANCEMENT 1  .
*&---------------------------------------------------------------------*
*&      Form  set_default_currency_un
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  --> date     (this should be begin of loan p0045-begda)
*  <-- def_curr (this should be p0045-dbtcu, because p0045-dbtcu
*                is used as default for the other currencies in IT0045)
*----------------------------------------------------------------------*
* Commented in Note 2883615
FORM set_default_currency_un
  USING    value(date)     TYPE d
  CHANGING value(def_curr) TYPE waers.
  DATA l_is_ok TYPE boole_d.
  DATA tds_p TYPE t7unpad_ds.     "#EC ..,
  DATA icurc TYPE tcurc.
  DATA lt_land1 TYPE STANDARD TABLE OF land1.
  DATA proposal_land1 TYPE land1.

  CONSTANTS: un_land1 TYPE land1 VALUE 'UN '.        "#EC ..,

  CALL FUNCTION 'POPUP_DISPLAY_MESSAGE'
    EXPORTING
      titel = text-m01
      msgid = 'HRPADUN_GEN'
      msgty = 'I'
      msgno = '720'.


  CALL FUNCTION 'HELP_VALUES_GET'
    EXPORTING
      fieldname    = 'WAERS'
      tabname      = 'T500W'
    IMPORTING
      select_value = def_curr
    EXCEPTIONS
      OTHERS       = 1.

  CHECK sy-subrc EQ 0.

  CHECK def_curr NE space.

  IF date CO ' 0'. date = sy-datum. ENDIF.                  "GWY486043

  CALL METHOD cl_hr_t7unpad_ds=>read         "#EC ..,
    EXPORTING
      molga = t001p-molga
      dstat = psyst-btrtl
    RECEIVING
      ds    = tds_p.

  SELECT land1 FROM t500w INTO TABLE lt_land1
    WHERE waers  = def_curr
      AND begda <= date
      AND endda >= date.

  IF sy-subrc <> 0.
    CLEAR proposal_land1.
  ELSE.
*   "try if default_currency is valid
    READ TABLE lt_land1 INTO proposal_land1
      WITH TABLE KEY table_line = tds_p-land1.

    IF sy-subrc <> 0.  "default_curr is not valid
*     "try if EURO is valid
      READ TABLE lt_land1 INTO proposal_land1
        WITH TABLE KEY table_line = un_land1.

      IF sy-subrc <> 0.
*       "take first valid currency
        READ TABLE lt_land1 INTO proposal_land1
          INDEX 1.
      ENDIF.
    ENDIF.
  ENDIF.

  psyst-land = proposal_land1.

*##--Begin--##
  PERFORM re500c(sapfp50m) USING tds_p-land1 date.

  IF def_curr IS INITIAL.
    def_curr = t500c-waers.
  ENDIF.


ENDFORM.                    " set_default_currency_un

**&---------------------------------------------------------------------*
**&      Form  read_feature_un
**&---------------------------------------------------------------------*
**       text
**----------------------------------------------------------------------*
**  -->  p1        text
**  <--  p2        text
**----------------------------------------------------------------------*
FORM read_feature_un USING    value(datein)     TYPE d
                     CHANGING value(dateout)    TYPE d
                              value(datelut)    TYPE d.
  DATA  pme97   TYPE pun_pad_pme97_f4.       "#EC ..,
  DATA  l_begda TYPE d.
  DATA  l_endda TYPE d.
  DATA  l_term  TYPE anzhl.
  data  l_logrp type logrp.

  "CLEAR: gs_yloan-insert, gs_yloan-check.
  l_begda = datein.
  l_begda+6(02) = '01'.                             "corr_jli 20041111


  MOVE-CORRESPONDING pme04 TO pme97.

  pme97-dlart = p0045-dlart.

  CALL FUNCTION 'HR_FEATURE_BACKFIELD'
    EXPORTING
      feature       = 'UNLON'
      struc_content = pme97
    IMPORTING
      back          = l_logrp
    EXCEPTIONS
      OTHERS        = 0.

  CHECK NOT l_logrp IS INITIAL.

  l_term = l_logrp.

  CALL FUNCTION 'HR_UN_CALC_DATE'       "#EC ..,
    EXPORTING
      i_start_date = l_begda
      i_term       = l_term
      i_periodunit = '012'
    IMPORTING
      e_end_date   = l_endda.

  IF sy-subrc = 0.               "#EC *
    dateout = l_endda - 1.
    datelut = l_endda - 1.
  ENDIF.

ENDFORM.                    " read_feature_un
*&---------------------------------------------------------------------*
*&      Form  SWITCH_VISIBILITY_2200_UN
*&---------------------------------------------------------------------*
*  activate push button 'PB_CARTE...' (calculate rate), if it is not
*    the last record.
*  activate push button 'PB_CAEDA...' (calculate endda), if it is not
*    the last record.
*&---------------------------------------------------------------------*
FORM switch_visibility_2200_un .
* activate if not in last record
  IF q0045-enddal <> p0045-endda.
    LOOP AT SCREEN.
      IF   screen-name CS 'PB_CARTE'
        OR screen-name CS 'PB_CAEDA'.

        screen-input     = '1'  .
        MODIFY SCREEN.
      ENDIF.
    ENDLOOP.
  ENDIF.

ENDFORM.                    " switch_visibility_2200_un
ENDENHANCEMENT.
