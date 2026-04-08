*----------------------------------------------------------------------*
*  Report  RPR_TRIP_HEADER_DATA
*  Display trip header, status & trip sums
*----------------------------------------------------------------------*
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
report  rpr_trip_header_data message-id 56.

INCLUDE ZZPR_TRIP_DATA_TOP.
*include rpr_trip_data_top.

define fc.
  add 1 to col_pos.
  fieldcat_ln-col_pos      =  col_pos.
* fieldcat_ln-ref_tabname  = 'V_PTRV_HEAD'. "............YEKL9CK031621
  fieldcat_ln-fieldname    = '&1'.
* Begin YEKL9CK031621
  case fieldcat_ln-fieldname.
    when 'ENAME' or 'SNAME'.
      fieldcat_ln-ref_tabname  = 'PA0001'.
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
end-of-definition.

selection-screen: begin of block a10 with frame title a10.
parameters:       variant  like disvariant-variant,
                  rb_grid  radiobutton group r10,        "YEKAHRK039877
                  rb_alv   radiobutton group r10.        "YEKAHRK039877
selection-screen: end of block a10,
                  begin of block a20 with frame title a20.
parameters:       optimize type ptrv_optimize default 'X'.
selection-screen: end of block a20.

initialization.
  a10 = 'Listaufbereitung'(a10).
  a20 = 'Laufzeit'(a20).

at selection-screen on variant.
  check not variant is initial.
  perform check_variant_existence using variant variant_save.

at selection-screen on value-request for variant.
  perform f4_display_variant using variant variant_save.

start-of-selection.
  pgm = disvariant-report = sy-repid.
  disvariant-variant      = variant.
  perform: build_fieldcat.

  ipernr-sign   = 'I'.
  ipernr-option = 'EQ'.

get pa0001 fields pernr bukrs werks kostl persg persk
                  ename sname. ".........................YEKL9CK031621

  ipernr-low = pa0001-pernr.
  collect ipernr.

  move-corresponding pa0001 to ipernr_tmp.
  insert table ipernr_tmp.

end-of-selection.
  if ipernr[] is initial.
    message s007.
*   No trip data found for specified selection criteria
    exit.
  endif.

  perform: compress_ipernr,
           get_header_data.

*----------------------------------------------------------------------*
*       Form routine declarations
*----------------------------------------------------------------------*
INCLUDE ZZPR_TRIP_DATA_FORM_ROUTINES.
*  include: rpr_trip_data_form_routines.

*----------------------------------------------------------------------*
*       Form  GET_HEADER_DATA
*----------------------------------------------------------------------*
*       Select trip header data & sums via v_ptrv_head
*----------------------------------------------------------------------*
form get_header_data.
  if not optimize is initial.
    perform get_active_columns using 'IHEAD'.
*   Version numbers always need to be selected because of the
*   subsequent delete adjacent duplicates.
*   ANTRG and ABREC are required for the authorization checks
    append: 'HDVRS' to coltab,
            'PDVRS' to coltab,
            'SEQNO' to coltab,
            'ANTRG' to coltab,
            'ABREC' to coltab,
*   Begin YEKL9CK031621
            'PERNR' to coltab.

*   Begin YEKL9CK099733
*   delete coltab
*     where fieldname = 'ENAME'
*     or    fieldname = 'SNAME'
*     or    fieldname = 'MILEAGE_TOTAL'. "...............YEKL9CK049417
    delete coltab
      where fieldname = 'ENAME'
      or    fieldname = 'SNAME'.

    delete coltab
      where fieldname = 'MILEAGE_TOTAL'.

    if sy-subrc is initial.
      append 'M_TOTAL' to coltab.
    endif.

*   End YEKL9CK031621
*   End YEKL9CK099733
  endif.

* Get dynamic selection criteria from logical DB
  append_rg_tabnames: ptrv_head,
                      ptrv_perio,
                      ptrv_shdr.

  perform get_dynamic_selections tables rg_tabnames.

  perform compress_coltab. ".............................YEKL9CK0693731

* if count_pernr <= 200. "...............................YEKAHRK056800
  if count_pernr <= sfae_limit. "........................YEKAHRK056800
*   Regular select statement
    select (coltab) from v_ptrv_head
      into corresponding fields of table ihead2
      where  pernr       in ipernr
      and    reinr       in ldbtrip
      and    zort1       in ldbzort1
      and    zland       in ldbzland
      and    datv1       in ldbfrom
      and    datb1       in ldbto
      and    sum_reimbu  in ldbreimb
      and    trip_total  in ldbtotal
      and    sum_paidco  in ldbpdc1   "..................YEKPH9K009401
      and    currency    in ldbcur1
      and    abrec       in ldbabrec
      and    uebrf       in ldbuebrf
      and    kunde       in ldbkunde   ".................YEKAHRK033171
      and    antrg       in ldbantrg   ".................YEKAHRK033171
      and    ueblg       in ldbueblg   ".................YEKAHRK033171
      and    uebdt       in ldbuebdt   ".................YEKAHRK033171
      and    sum_advanc  in ldbadvc    ".................YEKAHRK033171
      and    sum_payout  in ldbpay     ".................YEKAHRK033171
*     Begin YEKL9CK045160
      and    pdvrs = ( select min( pdvrs ) from ptrv_perio
                         where pernr = v_ptrv_head~pernr
                         and   reinr = v_ptrv_head~reinr
                         and   perio = v_ptrv_head~perio )
*     End YEKL9CK045160
      and    (xwhere_tab).
  else.
*   Select for all entries
    select (coltab) from v_ptrv_head
      into corresponding fields of table ihead2
      for all entries in ipernr
      where  pernr       =  ipernr-low
      and    reinr       in ldbtrip
      and    zort1       in ldbzort1
      and    zland       in ldbzland
      and    datv1       in ldbfrom
      and    datb1       in ldbto
      and    sum_reimbu  in ldbreimb
      and    trip_total  in ldbtotal
      and    sum_paidco  in ldbpdc1   "..................YEKPH9K009401
      and    currency    in ldbcur1
      and    abrec       in ldbabrec
      and    uebrf       in ldbuebrf
      and    kunde       in ldbkunde   ".................YEKAHRK033171
      and    antrg       in ldbantrg   ".................YEKAHRK033171
      and    ueblg       in ldbueblg   ".................YEKAHRK033171
      and    uebdt       in ldbuebdt   ".................YEKAHRK033171
      and    sum_advanc  in ldbadvc    ".................YEKAHRK033171
      and    sum_payout  in ldbpay     ".................YEKAHRK033171
*     Begin YEKL9CK045160
      and   pdvrs = ( select min( pdvrs ) from ptrv_perio
                        where pernr = v_ptrv_head~pernr
                        and   reinr = v_ptrv_head~reinr
                        and   perio = v_ptrv_head~perio )
*     End YEKL9CK045160
      and    (xwhere_tab).
  endif.

  if sy-subrc <> 0.
    message s007.
    exit.
*   No trip data found for specified selection criteria
  endif.



**AHOUNOU121003
LOOP AT  ihead2 into wa_ihead.
IF wa_ihead-antrg eq 4 and wa_ihead-uebrf eq 1 .

ELSE.
   append wa_ihead to ihead.
  clear wa_ihead.
endif.
ENDLOOP.

**AHOUNOU121003


* Eliminate duplicate versions of a trip/period
  sort ihead by pernr reinr perio hdvrs pdvrs seqno.
* Begin YEKAHRK047461
* delete adjacent duplicates from ihead:
*                            comparing pernr reinr hdvrs seqno,
*                            comparing pernr reinr perio pdvrs seqno.
* Begin YEKL9CK045160
* delete adjacent duplicates from ihead:
*                            comparing pernr reinr perio seqno.
* End YEKL9CK045160
* End YEKAHRK047461

*AHOUNOU31102003
  perform authority_check_item using 'NONE'.
  if ihead[] is initial.
    message s520.
*   Display authorizations missing or no value
    exit.
  endif.
*AHOUNOU31102003
  perform display_data.
endform.                               " GET_HEADER_DATA

*----------------------------------------------------------------------*
*       Form  DISPLAY_DATA
*----------------------------------------------------------------------*
*       Display selected data
*----------------------------------------------------------------------*
form display_data.
  perform: build_sortcat,
           set_layout_options using 'IHEAD',
           call_list_viewer.
endform.                               " DISPLAY_DATA

*----------------------------------------------------------------------*
*       Form  BUILD_FIELDCAT
*----------------------------------------------------------------------*
*       Build field catalog for the list viewer
*----------------------------------------------------------------------*
form build_fieldcat.
  fieldcat_ln-tabname = 'IHEAD'.

*    Fieldname         hotspot       do_sum
*                key           no_out        cfieldname
  fc pernr       xfield xfield space  space  space.
  fc reinr       xfield xfield space  space  space.
  fc perio       space  space  xfield space  space.
  fc tripdur     space  space  space  space  space.
  fc datv1       space  space  space  space  space.
  fc uhrv1       space  space  xfield space  space.
  fc datb1       space  space  space  space  space.
  fc uhrb1       space  space  xfield space  space.
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
* Begin YEKL9CK031621
  fc ename       space  xfield xfield space  space.
  fc sname       space  xfield xfield space  space.
* End YEKL9CK031621

* Begin YEKL9CK024129
* M_TOTAL needs to point to a differnt reffield because of overflows
  clear: fieldcat_ln.

  add 1 to col_pos.

  fieldcat_ln-tabname       = 'IHEAD'.
  fieldcat_ln-fieldname     = 'M_TOTAL'.
  fieldcat_ln-col_pos       =  col_pos.
  fieldcat_ln-ref_tabname   = 'PTK10'.
  fieldcat_ln-ref_fieldname = 'INLKM'.

  append fieldcat_ln to fieldcat.
* End YEKL9CK024129

* Begin YEKL9CK049417
  fieldcat_ln-tabname       = 'IHEAD'.
  fieldcat_ln-fieldname     = 'MILEAGE_TOTAL'.
  fieldcat_ln-col_pos       =  col_pos.
  fieldcat_ln-ref_tabname   = 'PTK10'.
  fieldcat_ln-ref_fieldname = 'INLKM'.

  append fieldcat_ln to fieldcat.
* End YEKL9CK049417

* Begin YEKL9CK039726
  if variant         is initial
    and not rb_grid  is initial.
*   Check if a default variant exists - Grid control only
    perform get_default_variant using disvariant variant.
  endif.
* End YEKL9CK039726

  if not variant is initial and not optimize is initial.
    perform get_fieldcat_from_variant using disvariant 'IHEAD' space.
  endif.

endform.                               " BUILD_FIELDCAT

*----------------------------------------------------------------------*
*       Form  BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Build sort catalog for the list viewer
*----------------------------------------------------------------------*
form build_sortcat.
*    Sortpos    Up            Subtot
*      Sortfield       Down          Group
  sc 1 pernr    xfield space  xfield 'UL'.
  sc 2 datv1    space  xfield space  space.
  sc 2 seqno    xfield space  space  space.
endform.                               " BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Form  CALL_LIST_VIEWER
*----------------------------------------------------------------------*
*       Start list viewer
*----------------------------------------------------------------------*
form call_list_viewer.
  if not count_reject is initial.
    message s268 with count_reject.
*   Display is incomplete because of missing authorizations
  endif.

* Begin YEKL9BK025794
  data: lf_save.

  authority-check object 'S_ALV_LAYO'
     id 'ACTVT' field '23'.

  if sy-subrc is initial.
*   user is authorized to maintain system wide variants
    lf_save = 'A'.
  else.
*   user can only save variants for him/herself
    lf_save = 'U'.
  endif.
* End YEKL9BK025794

* Begin YEKL9CK049417
  delete fieldcat
    where fieldname = 'M_TOTAL'.
* End YEKL9CK049417

* Begin YEKAHRK039877
  if rb_alv is initial.
    call function 'REUSE_ALV_GRID_DISPLAY'
         exporting
              i_buffer_active         =  xfield "........YEKL9CK016665
              i_callback_program      =  pgm
              is_layout               =  layout
              it_fieldcat             =  fieldcat
              it_sort                 =  sortcat
              it_events               =  eventcat
*             i_save                   = variant_save    YEKL9BK025794
              i_save                   = lf_save ".......YEKL9BK025794
              is_variant              =  disvariant
              i_callback_user_command = 'USER_COMMAND'
         tables
              t_outtab                = ihead
         exceptions
              program_error           = 1
              others                  = 2.
  else.
*   End YEKAHRK039877
    call function 'REUSE_ALV_LIST_DISPLAY'
         exporting
              i_buffer_active         =  xfield "........YEKL9CK016665
              i_callback_program      =  pgm
              is_layout               =  layout
              it_fieldcat             =  fieldcat
              it_sort                 =  sortcat
              it_events               =  eventcat
*             i_save                   = variant_save    YEKL9BK025794
              i_save                   = lf_save ".......YEKL9BK025794
              is_variant              =  disvariant
              i_callback_user_command = 'USER_COMMAND'
         tables
               t_outtab                = ihead          "XCIK008979
         exceptions
              program_error           = 1
              others                  = 2.
  endif.                                                 "YEKAHRK039877
endform.                               " CALL_LIST_VIEWER
*---------------------------------------------------------------------*
*       FORM USER_COMMAND
*---------------------------------------------------------------------*
*       Callback routine for function REUSE_ALV_LIST_DISPLAY
*       Execute commands
*---------------------------------------------------------------------*
form user_command using    ucomm like sy-ucomm
                  selfield type slis_selfield.

  read table ihead index selfield-tabindex.
  if sy-subrc <> 0.
    exit.
  endif.

  case ucomm.
    when '&IC1'.
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
      if selfield-sel_tab_field cs 'REINR'.
        perform interactive_display using 'XXXX'
                                            ihead-pernr
                                            ihead-reinr.
      elseif selfield-sel_tab_field cs 'PERNR' or
             selfield-sel_tab_field cs 'ENAME' or "......YEKL9CK031621
             selfield-sel_tab_field cs 'SNAME'. "........YEKL9CK031621

        perform get_name using ihead-pernr ihead-datb1.
      endif.
*     End YEKAHRK039877
  endcase.
endform.
