*----------------------------------------------------------------------*
*  Report  RPR_TRIP_HEADER_DATA
*  Display trip header, status & trip sums
*----------------------------------------------------------------------*
* 6.04
* GLWEH4K002181 28012008     no authorization for auditor(1136355)
* 6.03
* MAHE34K002031 06072007 GDPdU: company code switches not took into
*                        account [n.1072465]
* 6.0
* MAHP7HK009704 13/07/2006 - gdpdu tax auditor checks (note 955629)
* 2.0
* MZCELNK001201 31052004 Possib.choose trip or sep.alow. in sel. screen
* 4.6C
* YEKL9CK099733 06/17/2002 - mileage and optimizatin (note 528233)
* YEKL9CK069373 10/04/2001 - wrong reporting results (note 440712)
* YEKL9CK049417 04/10/2001 - Mileage sumations (note 396171)
* YEKL9CK045160 03/06/2001 - Incorrect DB selection (note 387631)
* YEKL9CK039726 01/29/2001 - Default variants (note 377704)
* YEKL9CK031621 11/27/2000 - Employee name in ALV list (note 361865)
* YEKL9CK024129 09/21/2000 - XCIPH0K008979 backed out (note 334898)
* YEKL9BK025794 08/03/2000 - systemwide list variants (note 322854)
* YEKL9CK016665 07/17/2000 - ALV performance (note 318150)
* XCIPH0K008979 04/02/2000 - create a special internal table for ALV
*               because the length of a field is too small for ALV
* YEKAHRK056800 09/10/1999 - Not all trips selected
* 4.6B
* YEKPH9K009401 06/11/1999 - Paid company missing in DB select
* 4.6A
* YEKAHRK047461 03/29/1999 - Delete adjacent duplicates incorrect
* YEKAHRK039877 03/08/1999 - Extensions for stats manager
* YEKAHRK033171 01/11/1999 - New parameters for call of get_name
*----------------------------------------------------------------------*
REPORT  yrpr_trip_header_data MESSAGE-ID 56.

TABLES PRPS.
INCLUDE YRPR_TRIP_DATA_TOP.
*INCLUDE rpr_trip_data_top.


DEFINE fc.
  add 1 to col_pos.
  fieldcat_ln-col_pos      =  col_pos.
* fieldcat_ln-ref_tabname  = 'V_PTRV_HEAD'. "............YEKL9CK031621
  fieldcat_ln-fieldname    = '&1'.
* Begin YEKL9CK031621
  case fieldcat_ln-fieldname.
*AAHOUNOU29102013
*    when 'ENAME' or 'SNAME'.
    when 'ENAME' or 'SNAME' or 'ZZSECTOR'.
**AAHOUNOU29102013
      fieldcat_ln-ref_tabname  = 'PA0001'.
    when 'RETXT'.
      fieldcat_ln-ref_tabname  = 'T706G'.
    when others.
      fieldcat_ln-ref_tabname  = 'V_PTRV_HEAD'.
  endcase.
* End YEKL9CK031621
  fieldcat_ln-key          =  &2.
  fieldcat_ln-hotspot      =  &3.
  fieldcat_ln-no_out       =  &4.
  fieldcat_ln-do_sum       =  &5.
  fieldcat_ln-cfieldname   =  &6.
  translate: fieldcat_ln-fieldname  to upper case.
  append fieldcat_ln to fieldcat.
END-OF-DEFINITION.

*AAHOUNOU29102013
select-options: S_SECTOR FOR PRPS-USR02 .
*AAHOUNOU29102013

SELECTION-SCREEN: BEGIN OF BLOCK a10 WITH FRAME TITLE a10.

PARAMETERS:       variant  LIKE disvariant-variant,
                  rb_grid  RADIOBUTTON GROUP r10,        "YEKAHRK039877
                  rb_alv   RADIOBUTTON GROUP r10.        "YEKAHRK039877
SELECTION-SCREEN: END OF BLOCK a10,
                  BEGIN OF BLOCK a20 WITH FRAME TITLE a20.
PARAMETERS:       optimize TYPE ptrv_optimize DEFAULT 'X'.
SELECTION-SCREEN: END OF BLOCK a20.

INITIALIZATION.
*Begin of MAHK009704
* check, if user is auditor
  CALL FUNCTION 'CA_USER_EXISTS'
    EXPORTING
      i_user       = sy-uname
    EXCEPTIONS
      user_missing = 1
      OTHERS       = 2.

  IF sy-subrc = 0.  "user found as auditor
    user_is_auditor = 1.

*  check if user is allowed to use program
    CALL FUNCTION 'CA_CHECK_DATE'
      EXPORTING
        i_applk           = 'EA-TRV'
        i_orgunit         = ''
        i_user            = sy-uname
        i_program         = sy-cprog
      EXCEPTIONS
        no_authority_prog = 2.

    IF sy-subrc <> 0.
*   user is not allowed to use program
      MESSAGE s650 DISPLAY LIKE 'E' WITH sy-cprog.
      LEAVE PROGRAM.
    ENDIF.
  ENDIF.
*End of MAHK009704

  a10 = 'Listaufbereitung'(a10).
  a20 = 'Laufzeit'(a20).

AT SELECTION-SCREEN ON variant.
  CHECK NOT variant IS INITIAL.
  PERFORM check_variant_existence USING variant variant_save.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR variant.
  PERFORM f4_display_variant USING variant variant_save.

* begin of MAHN1072465
**begin of MAHK209257
** no multiple selctions allowed
*AT SELECTION-SCREEN ON ldbpernr.
*  IF user_is_auditor = 1.
*    DESCRIBE TABLE ldbpernr LINES table_length.
*    CHECK table_length > 0.
*    IF table_length > 1.
*      MESSAGE e651.
*    ELSE.
*      READ TABLE ldbpernr INDEX 1.
*      IF ldbpernr-option <> 'EQ' OR
*         ldbpernr-sign   <> 'I'.
*        MESSAGE e651.
*      ENDIF.
*    ENDIF.
*  ENDIF.
*
*AT SELECTION-SCREEN ON ldbbukrs.
*  IF user_is_auditor = 1.
*    DESCRIBE TABLE ldbbukrs LINES table_length.
*    CHECK table_length > 0.
*    IF table_length > 1.
*      MESSAGE e651.
*    ELSE.
*      READ TABLE ldbbukrs INDEX 1.
*      IF ldbbukrs-option <> 'EQ' OR
*         ldbbukrs-sign   <> 'I'.
*        MESSAGE e651.
*      ENDIF.
*    ENDIF.
*  ENDIF.
*
*AT SELECTION-SCREEN ON ldbfrom.
*  IF user_is_auditor = 1.
*    DESCRIBE TABLE ldbfrom LINES table_length.
*    CHECK table_length > 0.
*    IF table_length > 1.
*      MESSAGE e651.
*    ELSE.
*      READ TABLE ldbfrom INDEX 1.
*      IF ldbfrom-sign  <> 'I'.
*        MESSAGE e651.
*      ENDIF.
*    ENDIF.
*  ENDIF.
*
*AT SELECTION-SCREEN ON ldbto.
*  IF user_is_auditor = 1.
*    DESCRIBE TABLE ldbto LINES table_length.
*    CHECK table_length > 0.
*    IF table_length > 1.
*      MESSAGE e651.
*    ELSE.
*      READ TABLE ldbto INDEX 1.
*      IF ldbto-sign  <> 'I'.
*        MESSAGE e651.
*      ENDIF.
*    ENDIF.
*  ENDIF.
**end of MAHK209257
* end of MAHN1072465


START-OF-SELECTION.

* begin of MAHN1072465
**begin of MAHK209257
*  IF user_is_auditor = 1.
*    PERFORM check_auditor_autho USING sy-subrc.
*    IF sy-subrc <> 0.
*      EXIT.
*    ENDIF.
*  ENDIF.
**end of MAHK209257
* end of MAHN1072465
  LOOP AT S_SECTOR  .
    IF S_SECTOR-LOW  is not initial.
      TRANSLATE S_SECTOR-LOW TO UPPER CASE.
        modify S_SECTOR  .
    ENDIF.
    IF S_SECTOR-HIGH is not initial.
      TRANSLATE S_SECTOR-HIGH TO UPPER CASE.
         modify S_SECTOR  .
    ENDIF.
  ENDLOOP.

  pgm = disvariant-report = sy-repid.
  disvariant-variant      = variant.
  PERFORM: build_fieldcat.

  ipernr-sign   = 'I'.
  ipernr-option = 'EQ'.

*GET pa0001 FIELDS pernr bukrs werks kostl persg persk
*                  ename sname. ".........................YEKL9CK031621

GET pa0001 FIELDS pernr bukrs werks kostl persg persk
                  ename sname zzsector.

  check pa0001-zzsector in s_sector.

  ipernr-low = pa0001-pernr.
  COLLECT ipernr.

  MOVE-CORRESPONDING pa0001 TO ipernr_tmp.

  INSERT table ipernr_tmp.

END-OF-SELECTION.
  IF ipernr[] IS INITIAL.
    MESSAGE s007.
*   No trip data found for specified selection criteria
    EXIT.
  ENDIF.

  PERFORM: compress_ipernr,
           get_header_data.

*----------------------------------------------------------------------*
*       Form routine declarations
*----------------------------------------------------------------------*
  INCLUDE YRPR_TRIP_DATA_FORM_ROUTINES.
*  INCLUDE: rpr_trip_data_form_routines.

*----------------------------------------------------------------------*
*       Form  GET_HEADER_DATA
*----------------------------------------------------------------------*
*       Select trip header data & sums via v_ptrv_head
*----------------------------------------------------------------------*
FORM get_header_data.
  IF NOT optimize IS INITIAL.
    PERFORM get_active_columns USING 'IHEAD'.
*   Version numbers always need to be selected because of the
*   subsequent delete adjacent duplicates.
*   ANTRG and ABREC are required for the authorization checks
    APPEND: 'HDVRS' TO coltab,
            'PDVRS' TO coltab,
            'SEQNO' TO coltab,
            'ANTRG' TO coltab,
            'ABREC' TO coltab,
            'PERIO' TO coltab,                              "MZCK001201
*   Begin YEKL9CK031621
            'PERNR' TO coltab.

*   Begin YEKL9CK099733
*   delete coltab
*     where fieldname = 'ENAME'
*     or    fieldname = 'SNAME'
*     or    fieldname = 'MILEAGE_TOTAL'. "...............YEKL9CK049417
*    DELETE coltab
*      WHERE fieldname = 'ENAME'
*      OR    fieldname = 'SNAME'.

*AAHOUNOU04112013
    DELETE coltab
      WHERE fieldname = 'ENAME'
      OR    fieldname = 'SNAME'
      OR    fieldname = 'ZZSECTOR'
      OR    fieldname =  'RETXT'.
*AAHOUNOU04112013

    DELETE coltab
      WHERE fieldname = 'MILEAGE_TOTAL'.

    IF sy-subrc IS INITIAL.
      APPEND 'M_TOTAL' TO coltab.
    ENDIF.

*   End YEKL9CK031621
*   End YEKL9CK099733
  ENDIF.

* Get dynamic selection criteria from logical DB
  append_rg_tabnames: ptrv_head,
                      ptrv_perio,
                      ptrv_shdr.

  PERFORM get_dynamic_selections TABLES rg_tabnames.

  PERFORM compress_coltab. ".............................YEKL9CK0693731

* if count_pernr <= 200. "...............................YEKAHRK056800
  IF count_pernr <= sfae_limit. "........................YEKAHRK056800
*   Regular select statement
    SELECT (coltab) FROM v_ptrv_head
      INTO CORRESPONDING FIELDS OF TABLE ihead
      WHERE  pernr       IN ipernr
      AND    reinr       IN ldbtrip
      AND    zort1       IN ldbzort1
      AND    zland       IN ldbzland
      AND    datv1       IN ldbfrom
      AND    datb1       IN ldbto
      AND    sum_reimbu  IN ldbreimb
      AND    trip_total  IN ldbtotal
      AND    sum_paidco  IN ldbpdc1   "..................YEKPH9K009401
      AND    currency    IN ldbcur1
      AND    abrec       IN ldbabrec
      AND    uebrf       IN ldbuebrf
      AND    kunde       IN ldbkunde   ".................YEKAHRK033171
      AND    antrg       IN ldbantrg   ".................YEKAHRK033171
      AND    ueblg       IN ldbueblg   ".................YEKAHRK033171
      AND    uebdt       IN ldbuebdt   ".................YEKAHRK033171
      AND    sum_advanc  IN ldbadvc    ".................YEKAHRK033171
      AND    sum_payout  IN ldbpay     ".................YEKAHRK033171
*     Begin YEKL9CK045160
      AND    pdvrs = ( SELECT MIN( pdvrs ) FROM ptrv_perio
                         WHERE pernr = v_ptrv_head~pernr
                         AND   reinr = v_ptrv_head~reinr
                         AND   perio = v_ptrv_head~perio )
*     End YEKL9CK045160
      AND    (xwhere_tab).
  ELSE.
*   Select for all entries
    SELECT (coltab) FROM v_ptrv_head
      INTO CORRESPONDING FIELDS OF TABLE ihead
      FOR ALL ENTRIES IN ipernr
      WHERE  pernr       =  ipernr-low
      AND    reinr       IN ldbtrip
      AND    zort1       IN ldbzort1
      AND    zland       IN ldbzland
      AND    datv1       IN ldbfrom
      AND    datb1       IN ldbto
      AND    sum_reimbu  IN ldbreimb
      AND    trip_total  IN ldbtotal
      AND    sum_paidco  IN ldbpdc1   "..................YEKPH9K009401
      AND    currency    IN ldbcur1
      AND    abrec       IN ldbabrec
      AND    uebrf       IN ldbuebrf
      AND    kunde       IN ldbkunde   ".................YEKAHRK033171
      AND    antrg       IN ldbantrg   ".................YEKAHRK033171
      AND    ueblg       IN ldbueblg   ".................YEKAHRK033171
      AND    uebdt       IN ldbuebdt   ".................YEKAHRK033171
      AND    sum_advanc  IN ldbadvc    ".................YEKAHRK033171
      AND    sum_payout  IN ldbpay     ".................YEKAHRK033171
*     Begin YEKL9CK045160
      AND   pdvrs = ( SELECT MIN( pdvrs ) FROM ptrv_perio
                        WHERE pernr = v_ptrv_head~pernr
                        AND   reinr = v_ptrv_head~reinr
                        AND   perio = v_ptrv_head~perio )
*     End YEKL9CK045160
      AND    (xwhere_tab).
  ENDIF.

  IF sy-subrc <> 0.
    MESSAGE s007.
    EXIT.
*   No trip data found for specified selection criteria
  ENDIF.

* Eliminate duplicate versions of a trip/period
  SORT ihead BY pernr reinr perio hdvrs pdvrs seqno.
* Begin YEKAHRK047461
* delete adjacent duplicates from ihead:
*                            comparing pernr reinr hdvrs seqno,
*                            comparing pernr reinr perio pdvrs seqno.
* Begin YEKL9CK045160
* delete adjacent duplicates from ihead:
*                            comparing pernr reinr perio seqno.
* End YEKL9CK045160
* End YEKAHRK047461

  PERFORM authority_check_item USING 'NONE'.
  IF ihead[] IS INITIAL.
    MESSAGE s267.
*   Display not possible because of missing authorizations
    EXIT.
  ENDIF.

  PERFORM filter_trips_sa_ihead.                            "MZCK001201

*AAHOUNOU29102013
*ALAIN


  Tables t706g.
  data: wa_kztkt like ptrv_head-kztkt, " work area for Main activity
        wa_kzrea like ptrv_head-kzrea, " work area for Type
        w_ttype like t706g-retxt.

  LOOP AT ihead.
    clear  wa_kzrea.
    select single uname from  ptrv_head
             into   ihead-uname
             where pernr = ihead-pernr
               and reinr = ihead-reinr
               and hdvrs = ihead-hdvrs . " Veux-t-on récupérer la personne qui a changé le TRIP ou la personne qui l'a créé? " Séquential number 97 / 98 / 99????


    select single kzrea from  ptrv_head
             into   wa_kzrea
             where pernr = ihead-pernr
               and reinr = ihead-reinr
               and hdvrs = ihead-hdvrs .

    select   * from  t706g
     where  spras  = sy-langu
     and    morei  = '06'
     and    kzrea  = wa_kzrea.
    endselect.


    move t706g-retxt to ihead-retxt.
    modify  ihead.
  ENDLOOP.




*AAHOUNOU29102013

* begin of MAHN1072465
  IF user_is_auditor = 1.
    PERFORM check_trips_for_auditor.
    IF list_shortened = 'X'.                                "GLWK002181
      MESSAGE s656.
    ENDIF.
  ENDIF.
* end of   MAHN1072465

  PERFORM display_data.
ENDFORM.                               " GET_HEADER_DATA

*----------------------------------------------------------------------*
*       Form  DISPLAY_DATA
*----------------------------------------------------------------------*
*       Display selected data
*----------------------------------------------------------------------*
FORM display_data.
  PERFORM: build_sortcat,
           set_layout_options USING 'IHEAD',
           call_list_viewer.
ENDFORM.                               " DISPLAY_DATA

*----------------------------------------------------------------------*
*       Form  BUILD_FIELDCAT
*----------------------------------------------------------------------*
*       Build field catalog for the list viewer
*----------------------------------------------------------------------*
FORM build_fieldcat.
  fieldcat_ln-tabname = 'IHEAD'.
*    Fieldname         hotspot       do_sum
*                key           no_out        cfieldname
  fc pernr       xfield xfield space  space  space.
  fc reinr       xfield xfield space  space  space.
*  fc perio      space  space  xfield space  space.       ">>MZCK001201
  fc perio       space  space  sa_excl space  space.      "<<MZCK001201
  fc tripdur     space  space  space  space  space.
*  fc datv1       space  space  space  space  space.      ">>MZCK001201
*  fc uhrv1       space  space  xfield space  space.      ">>MZCK001201
  fc pdatv       space  space  space  space  space.       "<<MZCK001201
  fc puhrv       space  space  xfield space  space.       "<<MZCK001201
*  fc datb1       space  space  space  space  space.      ">>MZCK001201
*  fc uhrb1       space  space  xfield space  space.      ">>MZCK001201
  fc pdatb       space  space  space  space  space.       "<<MZCK001201
  fc puhrb       space  space  xfield space  space.       "<<MZCK001201
  fc molga       space  space  xfield space  space.
  fc morei       space  space  xfield space  space.
  fc schem       space  space  xfield space  space.
  fc kzrea       space  space  xfield space  space.
  fc berei       space  space  xfield space  space.
  fc kztkt       space  space  xfield space  space.
  fc zort1       space  space  space  space  space.
  fc zland       space  space  space  space  space.
  fc hrgio       space  space  space  space  space.
  fc ndnst       space  space  xfield space  space.
  fc kunde       space  space  space  space  space.
  fc dath1       space  space  xfield space  space.
  fc uhrh1       space  space  xfield space  space.
  fc datr1       space  space  xfield space  space.
  fc uhrr1       space  space  xfield space  space.
  fc agrz1       space  space  xfield space  space.
  fc grgio       space  space  xfield space  space.
  fc grber       space  space  xfield space  space.
  fc uzkvg       space  space  xfield space  space.
  fc zusag       space  space  xfield space  space.
  fc endrg       space  space  xfield space  space.
  fc depar       space  space  xfield space  space.
  fc arrvl       space  space  xfield space  space.
  fc retrn       space  space  xfield space  space.
  fc dates       space  space  xfield space  space.
  fc times       space  space  xfield space  space.
  fc uname       space  space  xfield space  space.
  fc repid       space  space  xfield space  space.
  fc dantn       space  space  xfield space  space.
  fc fintn       space  space  xfield space  space.
  fc addit_amnt  space  space  xfield xfield 'CURRENCY'.
  fc sum_reimbu  space  space  space  xfield 'CURRENCY'.
  fc sum_advanc  space  space  xfield xfield 'CURRENCY'.
  fc sum_payout  space  space  xfield xfield 'CURRENCY'.
  fc sum_paidco  space  space  space  xfield 'CURRENCY'.
  fc trip_total  space  space  space  xfield 'CURRENCY'.
  fc pd_food     space  space  xfield xfield 'CURRENCY'.
  fc pd_housing  space  space  xfield xfield 'CURRENCY'.
  fc pd_mileage  space  space  xfield xfield 'CURRENCY'.
  fc currency    space  space  space  space  space.
* fc m_total     space  space  space  space  space. "....YEKL9CK024129
  fc abrec       space  space  space  space  space.
  fc uebrf       space  space  space  space  space.
  fc antrg       space  space  xfield space  space.
  fc ueblg       space  space  xfield space  space.
  fc uebdt       space  space  xfield space  space.
  fc tlock       space  space  xfield space  space.
  fc seqno       space  space  xfield space  space.      "YEKAHRK039877


  if cl_fitv_switch_check=>ptrm_sfws_03( ) = abap_true.    "GVJ_CEE_CZ_SK
    fc exchange_date  space  space  space  space  space.   "GVJ_CEE_CZ_SK
    fc rounding       space  space  xfield space  space.   "GVJ_CEE_CZ_SK
  endif.                                                   "GVJ_CEE_CZ_SK

* Begin YEKL9CK031621
  fc ename       space  xfield xfield space  space.
  fc sname       space  xfield xfield space  space.
*AAHOUNOU29102013
  fc zzsector     space  xfield xfield space  space.
  fc retxt     space  xfield xfield space  space.
*AAHOUNOU29102013
* End YEKL9CK031621

* Begin YEKL9CK024129
* M_TOTAL needs to point to a differnt reffield because of overflows
  CLEAR: fieldcat_ln.

  ADD 1 TO col_pos.

  fieldcat_ln-tabname       = 'IHEAD'.
  fieldcat_ln-fieldname     = 'M_TOTAL'.
  fieldcat_ln-col_pos       =  col_pos.
  fieldcat_ln-ref_tabname   = 'PTK10'.
  fieldcat_ln-ref_fieldname = 'INLKM'.

  APPEND fieldcat_ln TO fieldcat.
* End YEKL9CK024129

* Begin YEKL9CK049417
  fieldcat_ln-tabname       = 'IHEAD'.
  fieldcat_ln-fieldname     = 'MILEAGE_TOTAL'.
  fieldcat_ln-col_pos       =  col_pos.
  fieldcat_ln-ref_tabname   = 'PTK10'.
  fieldcat_ln-ref_fieldname = 'INLKM'.

  APPEND fieldcat_ln TO fieldcat.
* End YEKL9CK049417

* Begin YEKL9CK039726
  IF variant         IS INITIAL
    AND NOT rb_grid  IS INITIAL.
*   Check if a default variant exists - Grid control only
    PERFORM get_default_variant USING disvariant variant.
  ENDIF.
* End YEKL9CK039726

  IF NOT variant IS INITIAL AND NOT optimize IS INITIAL.
    PERFORM get_fieldcat_from_variant USING disvariant 'IHEAD' space.
  ENDIF.

ENDFORM.                               " BUILD_FIELDCAT

*----------------------------------------------------------------------*
*       Form  BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Build sort catalog for the list viewer
*----------------------------------------------------------------------*
FORM build_sortcat.
*    Sortpos    Up            Subtot
*      Sortfield       Down          Group
  sc 1 pernr    xfield space  xfield 'UL'.
*  sc 2 datv1    space  xfield space  space.               ">>MZCK001201
  sc 2 pdatv    space  xfield space  space.              "<<MZCK001201
  sc 2 seqno    xfield space  space  space.
ENDFORM.                               " BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Form  CALL_LIST_VIEWER
*----------------------------------------------------------------------*
*       Start list viewer
*----------------------------------------------------------------------*
FORM call_list_viewer.
  IF NOT count_reject IS INITIAL.
    MESSAGE s268 WITH count_reject.
*   Display is incomplete because of missing authorizations
  ENDIF.

* Begin YEKL9BK025794
  DATA: lf_save.

  AUTHORITY-CHECK OBJECT 'S_ALV_LAYO'
     ID 'ACTVT' FIELD '23'.

  IF sy-subrc IS INITIAL.
*   user is authorized to maintain system wide variants
    lf_save = 'A'.
  ELSE.
*   user can only save variants for him/herself
    lf_save = 'U'.
  ENDIF.
* End YEKL9BK025794

* Begin YEKL9CK049417
  DELETE fieldcat
    WHERE fieldname = 'M_TOTAL'.
* End YEKL9CK049417

* Begin YEKAHRK039877
  IF rb_alv IS INITIAL.
    CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
      EXPORTING
*       i_buffer_active         =  xfield "........YEKL9CK016665
        i_callback_program      = pgm
        is_layout               = layout
        it_fieldcat             = fieldcat
        it_sort                 = sortcat
        it_events               = eventcat
*       i_save                  = variant_save    YEKL9BK025794
        i_save                  = lf_save ".......YEKL9BK025794
        is_variant              = disvariant
        i_callback_user_command = 'USER_COMMAND'
      TABLES
        t_outtab                = ihead
      EXCEPTIONS
        program_error           = 1
        OTHERS                  = 2.
  ELSE.
*   End YEKAHRK039877
    CALL FUNCTION 'REUSE_ALV_LIST_DISPLAY'
      EXPORTING
*       i_buffer_active         =  xfield "........YEKL9CK016665
        i_callback_program      = pgm
        is_layout               = layout
        it_fieldcat             = fieldcat
        it_sort                 = sortcat
        it_events               = eventcat
*       i_save                  = variant_save    YEKL9BK025794
        i_save                  = lf_save ".......YEKL9BK025794
        is_variant              = disvariant
        i_callback_user_command = 'USER_COMMAND'
      TABLES
        t_outtab                = ihead                     "XCIK008979
      EXCEPTIONS
        program_error           = 1
        OTHERS                  = 2.
  ENDIF.                                                 "YEKAHRK039877
ENDFORM.                               " CALL_LIST_VIEWER
*---------------------------------------------------------------------*
*       FORM USER_COMMAND
*---------------------------------------------------------------------*
*       Callback routine for function REUSE_ALV_LIST_DISPLAY
*       Execute commands
*---------------------------------------------------------------------*
FORM user_command USING    ucomm LIKE sy-ucomm
                  selfield TYPE slis_selfield.

  READ TABLE ihead INDEX selfield-tabindex.
  IF sy-subrc <> 0.
    EXIT.
  ENDIF.

  CASE ucomm.
    WHEN '&IC1'.
*     Begin YEKAHRK039877
*     case selfield-sel_tab_field.
*       when 'IHEAD-REINR'.
*         perform interactive_display using 'XXXX'
*                                           ihead-pernr
*                                           ihead-reinr.
*       when 'IHEAD-PERNR'.
**        PERFORM get_name.                              "YEKAHRK033171
*         perform get_name using ihead-pernr ihead-datb1."YEKAHRK033171
**
*     endcase.
      IF selfield-sel_tab_field CS 'REINR'.
        PERFORM interactive_display USING 'XXXX'
                                            ihead-pernr
                                            ihead-reinr
                                            ihead-perio.    "MZCK001201
      ELSEIF selfield-sel_tab_field CS 'PERNR' OR
             selfield-sel_tab_field CS 'ENAME' OR "......YEKL9CK031621
             selfield-sel_tab_field CS 'SNAME'. "........YEKL9CK031621

        PERFORM get_name USING ihead-pernr ihead-datb1.
      ENDIF.
*     End YEKAHRK039877
  ENDCASE.
ENDFORM.                    "user_command
*---------------------------------------------------------------------*
*       FORM check_trips_for_auditor                                  *
*---------------------------------------------------------------------*
*       new with MAHN1072465                                          *
*---------------------------------------------------------------------*
FORM check_trips_for_auditor.
  DATA ls_pa0001 TYPE          pa0001.
  DATA ls_head LIKE LINE OF    ihead.

  CLEAR list_shortened.                                     "GLWK002181
* loop at all trips and delete if no authority for auditor
  LOOP AT ihead INTO ls_head.

* get company code of pernr to which it was assigned during trip
    READ TABLE gt_pa0001      " read from buffer first
      WITH KEY pernr = ls_head-pernr
      TRANSPORTING NO FIELDS.

    IF sy-subrc <> 0.
      SELECT *            " not in buffer -> get it from database
      FROM pa0001
      APPENDING TABLE gt_pa0001
      WHERE pernr = ls_head-pernr.
    ENDIF.

    LOOP AT gt_pa0001
      INTO ls_pa0001
      WHERE pernr  = ls_head-pernr
*        AND begda <= ls_head-datv1
*        AND endda >= ls_head-datb1.
         AND begda <= ls_head-pdatv
         AND endda >= ls_head-pdatb.                        "GLWK002181
      EXIT.
    ENDLOOP.
    IF sy-subrc <> 0.
      list_shortened = 'X'.                                 "GLWK002181
      DELETE TABLE ihead FROM ls_head.   "unknown error
      CONTINUE.
    ENDIF.

* check date and compcode for auditor
    CALL FUNCTION 'CA_CHECK_DATE'
      EXPORTING
        i_applk           = 'EA-TRV'
        i_orgunit         = ls_pa0001-bukrs
        i_user            = sy-uname
        i_program         = sy-cprog
*       i_from_date       = ls_head-datv1
*       i_to_date         = ls_head-datb1
        i_from_date       = ls_head-pdatv                   "GLWK002181
        i_to_date         = ls_head-pdatb
      EXCEPTIONS
        no_authority_date = 1.
    .
    IF sy-subrc <> 0.
      list_shortened = 'X'.                                 "GLWK002181
      DELETE TABLE ihead FROM ls_head.
      CONTINUE.
    ENDIF.
  ENDLOOP.
ENDFORM.                    "check_trips_for_auditor
**&---------------------------------------------------------------------*
**&      Form  check_auditor_autho
**&---------------------------------------------------------------------*
**       new with MAHK009704
*       not used anymore with MAHN1072465
**----------------------------------------------------------------------*
*FORM check_auditor_autho CHANGING sy-subrc.
*
*  DATA: begdate_to_use TYPE rebed VALUE '99999999',
*        enddate_to_use TYPE reend VALUE '00000000',
*        compcode_to_use TYPE bukrs.
*
*  IF  ( NOT ldbpernr[] IS INITIAL AND NOT ldbbukrs[] IS INITIAL )
*       OR ( ldbpernr[] IS INITIAL AND ldbbukrs[] IS INITIAL )
*       OR ( ldbfrom[] IS INITIAL AND ldbto[] IS INITIAL ).
*    MESSAGE s653 DISPLAY LIKE 'E'. "Personalnr. oder Buchungskreis in Verbindung mit Datum eingeben
*    sy-subrc = 1.
*    EXIT.
*  ENDIF.
*
**get lowest begindate an highest enddate
*
*  READ TABLE ldbfrom INDEX 1.
*  IF ldbfrom-low > '00000000'.
*    begdate_to_use = ldbfrom-low.
*  ENDIF.
*  IF ldbfrom-high > '00000000'.
*    enddate_to_use = ldbfrom-high.
*  ENDIF.
*
*  READ TABLE ldbto INDEX 1.
*  IF ldbto-low < begdate_to_use AND ldbto-low > '00000000'.
*    begdate_to_use = ldbto-low.
*  ENDIF.
*  IF ldbto-high > enddate_to_use AND ldbto-high > '00000000'.
*    enddate_to_use = ldbto-high.
*  ENDIF.
*
*  IF  begdate_to_use = '99999999'
*   OR enddate_to_use = '00000000'.  "initial value!
*    MESSAGE s655 DISPLAY LIKE 'E'.
**   Mind. ein Von- u. ein Bisdatum bei Beginn- oder Enddatum eingeben.
*    sy-subrc = 1.
*    EXIT.
*  ENDIF.
*
**get bukrs either direct or by persnr
*  IF NOT ldbbukrs[] IS INITIAL.
*    READ TABLE ldbbukrs INDEX 1.
*    MOVE ldbbukrs-low TO compcode_to_use.
*  ELSE.
*    READ TABLE ldbpernr INDEX 1.
*    SELECT SINGLE bukrs
*      FROM pa0001
*      INTO compcode_to_use
*      WHERE pernr = ldbpernr-low.
*  ENDIF.
*
**check
*  CALL FUNCTION 'CA_CHECK_DATE'
*    EXPORTING
*      i_applk           = 'EA-TRV'
*      i_orgunit         = compcode_to_use
*      i_user            = sy-uname
*      i_program         = sy-cprog
*      i_from_date       = begdate_to_use
*      i_to_date         = enddate_to_use
*    EXCEPTIONS
*      no_authority_date = 1.
*
*  IF sy-subrc <> 0.
*    MESSAGE s654 DISPLAY LIKE 'E'.
*    sy-subrc = 1.
*    EXIT.
**   Keine Berechtigungen im ausgewählten Zeitraum.
*
*  ENDIF.
*ENDFORM.                    "auditor_checks
