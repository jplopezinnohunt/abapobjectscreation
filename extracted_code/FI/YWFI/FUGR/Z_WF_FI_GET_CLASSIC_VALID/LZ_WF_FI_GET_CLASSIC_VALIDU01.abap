FUNCTION z_wf_fi_pr_wf_actor1_det.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(WFVAR) LIKE  T001-WFVAR OPTIONAL
*"     VALUE(LEVEL) LIKE  VBWF15-STUFE OPTIONAL
*"     VALUE(DMBTR) LIKE  BSEG-DMBTR OPTIONAL
*"     VALUE(FRWEG) LIKE  VBWF15-FRWEG OPTIONAL
*"     VALUE(BELNR) LIKE  BSEG-BELNR OPTIONAL
*"     VALUE(BUKRS) LIKE  BSEG-BUKRS OPTIONAL
*"     VALUE(GJAHR) LIKE  BSEG-GJAHR OPTIONAL
*"     VALUE(BUZEI) LIKE  BSEG-BUZEI OPTIONAL
*"  TABLES
*"      ACTOR_TAB STRUCTURE  SWHACTOR
*"      AC_CONTAINER STRUCTURE  SWCONT
*"  EXCEPTIONS
*"      NOBODY_FOUND
*"      DOCUMENT_NOT_FOUND
*"      NOT_FOUND
*"----------------------------------------------------------------------
*---------------------------------------------------------------------*
*       ACTOR mit Hilfe Freigabegruppe Personenkonto ermitteln        *
*---------------------------------------------------------------------*
  INCLUDE <cntn01>.
  DATA:  i              LIKE sy-tabix.
*         i1             LIKE i,
*         i_max          LIKE i,
*         i_bzalt        LIKE i,
*         item_text_change(1) TYPE c,                        "N422072
*         dummy          TYPE i.
  DATA:    refe           LIKE rf05v-hwsol.
  DATA: actor_tab2 TYPE swhactor OCCURS 0 WITH HEADER LINE.
  DATA: result_tab LIKE swhactor OCCURS 0 WITH HEADER LINE.
  DATA: lt_emails TYPE TABLE OF zfi_payrel_email.
  FIELD-SYMBOLS: <user> TYPE zfi_payrel_email.
  TABLES: vbwf15.
  DATA:   BEGIN OF xvbwf15 OCCURS 1.
          INCLUDE STRUCTURE vbwf15.
  DATA:   END OF xvbwf15.
  DATA:   xobj_sap2         LIKE vbwforg-objid_sap.
  DATA:   BEGIN OF xobj_sap,
          wfvar             LIKE v_vbwf15-wfvar,
          frweg             LIKE v_vbwf15-frweg,
          stufe             LIKE v_vbwf15-stufe,
          hwbis             LIKE v_vbwf15-hwbis,
          END OF xobj_sap.
  DATA: xotype_sap LIKE vbwforg-otype_sap.
  DATA: xwfvar LIKE t001-wfvar.
  DATA: xlevel LIKE vbwf15-stufe.
  DATA: xdmbtr LIKE bseg-dmbtr.
  DATA: xfrweg LIKE vbwf15-frweg.
  xotype_sap = 'VBWF15'.
  REFRESH actor_tab.
  REFRESH xvbwf15.
  CLEAR xvbwf15.
  CLEAR i.                                          "note 940949
  IF wfvar IS INITIAL.
    CLEAR xwfvar.
    SET EXTENDED CHECK OFF.
    swc_get_element ac_container 'WFVar' xwfvar.     "WF-VARIANTE
    IF sy-subrc NE 0. MESSAGE s135(fp) WITH 'WFVar'. ENDIF.
    SET EXTENDED CHECK ON.
  ELSE.
    xwfvar = wfvar.
  ENDIF.
  IF level IS INITIAL.
    CLEAR xlevel.
    SET EXTENDED CHECK OFF.
    swc_get_element ac_container 'LEVEL' xlevel.     "Stufe
    IF sy-subrc NE 0. MESSAGE s135(fp) WITH 'LEVEL'. ENDIF.
    SET EXTENDED CHECK ON.
  ELSE.
    xlevel = level.
  ENDIF.
  IF dmbtr IS INITIAL.
    CLEAR xdmbtr.
    SET EXTENDED CHECK OFF.
    swc_get_element ac_container 'Amoun' xdmbtr.     "Betrag
    IF sy-subrc NE 0. MESSAGE s135(fp) WITH 'Amoun'. ENDIF.
    SET EXTENDED CHECK ON.
  ELSE.
    xdmbtr = dmbtr.
  ENDIF.
  IF frweg IS INITIAL.
    CLEAR xfrweg.
    SET EXTENDED CHECK OFF.
    swc_get_element ac_container 'RPath' xfrweg.     "Freigabeweg
    IF sy-subrc NE 0. MESSAGE s135(fp) WITH 'RPath'. ENDIF.
    SET EXTENDED CHECK ON.
  ELSE.
    xfrweg = frweg.
  ENDIF.
***  CALL CUSTOMER-FUNCTION '004'
***       EXPORTING
***            wfvar   = xwfvar
***            level   = xlevel
***            dmbtr   = xdmbtr
***            frweg   = xfrweg
***       TABLES
***            t_actor = actor_tab
***       EXCEPTIONS
***            nobody_found   = 1.
***  IF sy-subrc EQ 1.
***    RAISE nobody_found.
***  ENDIF.
  CALL FUNCTION 'OPEN_FI_PERFORM_00002220_P'
    EXPORTING
      wfvar   = xwfvar
      level   = xlevel
      dmbtr   = xdmbtr
      frweg   = xfrweg
    TABLES
      t_actor = actor_tab
    EXCEPTIONS
      OTHERS  = 0.
  READ TABLE actor_tab INDEX 1.
  CHECK sy-subrc NE 0.                 "Tabelle durch Userexit gefüllt?
* Tabelle für Freigabeberechtigte lesen
  SELECT * FROM vbwf15 INTO TABLE xvbwf15
                       WHERE wfvar EQ xwfvar ORDER BY PRIMARY KEY.
  IF sy-subrc NE 0.
***    EXIT.
  ENDIF.
*
  LOOP AT xvbwf15 WHERE frweg EQ xfrweg AND       "Qualifiziert mit
                        stufe EQ xlevel.          "Level und Gruppe
    refe  = xvbwf15-hwbis.
    IF refe GE xdmbtr.
      i = sy-tabix.
      EXIT.
    ENDIF.
  ENDLOOP.
  IF i IS INITIAL.
    LOOP AT xvbwf15 WHERE frweg EQ xfrweg AND       "Qualifiziert mit
                          stufe IS INITIAL.         "Gruppe
      refe  = xvbwf15-hwbis.
      IF refe GE xdmbtr.
        i = sy-tabix.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.
  IF i IS INITIAL.
    LOOP AT xvbwf15 WHERE frweg IS INITIAL AND   "Qualifiziert mit
                          stufe EQ xlevel.       "Level
      refe  = xvbwf15-hwbis.
      IF refe GE xdmbtr.
        i = sy-tabix.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.
  IF i IS INITIAL.
    LOOP AT xvbwf15 WHERE frweg IS INITIAL AND   "Unqualifiziert
                          stufe IS INITIAL.
      refe  = xvbwf15-hwbis.
      IF refe GE xdmbtr.
        i = sy-tabix.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.
  IF i IS INITIAL.
***    EXIT.
  ENDIF.
  xobj_sap-wfvar = xvbwf15-wfvar.
  xobj_sap-frweg = xvbwf15-frweg.
  xobj_sap-stufe = xvbwf15-stufe.
  xobj_sap-hwbis = xvbwf15-hwbis.
  CLEAR xobj_sap2.
  xobj_sap2 = xobj_sap.
  CALL FUNCTION 'RH_SAP_ORG_OBJEC_ACTORS_LIST'
    EXPORTING
      act_objtyp = xotype_sap
      act_objkey = xobj_sap2
    TABLES
      actor_tab  = actor_tab2
    EXCEPTIONS
      OTHERS     = 1.
  LOOP AT actor_tab2.
    CALL FUNCTION 'RH_STRUC_GET'
         EXPORTING
              act_otype       = 'S'
              act_objid       = actor_tab2-objid
              act_wegid       = 'WF_ORGUS'
              act_int_flag    = space
*             ACT_PLVAR       = ' '
*             ACT_BEGDA       = SY-DATUM
*             ACT_ENDDA       = SY-DATUM
*             ACT_TDEPTH      = 0
              authority_check = ''
*        IMPORTING
*           ACT_PLVAR       =
         TABLES
            result_tab      = result_tab
*           RESULT_OBJEC    =
*           RESULT_STRUC    =
         EXCEPTIONS
            no_plvar_found  = 1
            no_entry_found  = 2
            OTHERS          = 3.
    APPEND LINES OF result_tab TO actor_tab.
  ENDLOOP.
  DELETE actor_tab WHERE otype <> 'US'.
  DESCRIBE TABLE actor_tab.
  CHECK sy-tfill EQ 0.
*          RAISE nobody_found.
* Default User/emails for Workflow FI Payment Release notifications
  SELECT *
    FROM zfi_payrel_email
    INTO TABLE lt_emails.
  LOOP AT lt_emails ASSIGNING <user>.
    actor_tab-otype = 'US'.
    actor_tab-objid = <user>-bname.
    APPEND actor_tab.
  ENDLOOP.
ENDFUNCTION.