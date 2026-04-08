*----------------------------------------------------------------------*
*  Report  RPR_TRIP_COST_ASSIGNMENT_DATA2
*  Display trip cost assignment without trip header data
*----------------------------------------------------------------------*
* 4.6C
* YEKL9CK069373 10/04/2001 - wrong reporting results (note 440712)
* YEKL9CK045160 03/06/2001 - Incorrect DB selection (note 387631)
* YEKL9CK039726 01/29/2001 - Default variants (note 377704)
* YEKL9CK031621 11/27/2000 - Employee name in ALV list (note 361865)
* YEKL9BK025794 08/03/2000 - systemwide list variants (note 322854)
* YEKL9CK016665 07/17/2000 - ALV performance (note 318150)
* YEKL9CK012611 06/12/2000 - WBS element not displayable
* YEKAHRK057750 09/23/1999 - Header data ignored for selection
* YEKAHRK056800 09/10/1999 - Not all trips selected
* YEKAHRK052310 07/15/1999 - Interactive displays called with wrong WA
* 4.6B
* YEKPH9K009401 06/11/1999 - Paid company missing in DB select
* 4.6A
* YEKAHRK033171 01/11/1999 - New parameters for call of get_name
*----------------------------------------------------------------------*


report   rpr_trip_cost_asignment_data2 message-id 56.

tables:  ptrv_scos.

INCLUDE YPR_TRIP_DATA_TOP.
*include: rpr_trip_data_top.

define fc.
  add 1 to col_pos.
  fieldcat_ln-col_pos      =  col_pos.
  fieldcat_ln-fieldname    = '&1'.
* Begin YEKL9CK031621
* fieldcat_ln-ref_tabname  = 'PTRV_SCOS'.
  case fieldcat_ln-fieldname.
    when 'ENAME' or 'SNAME'.
      fieldcat_ln-ref_tabname  = 'PA0001'.
    when others.
      fieldcat_ln-ref_tabname  = 'PTRV_SCOS'.
  endcase.
* End YEKL9CK031621
  fieldcat_ln-key          =  &2.
  fieldcat_ln-hotspot      =  &3.
  fieldcat_ln-no_out       =  &4.
  fieldcat_ln-do_sum       =  &5.
  fieldcat_ln-cfieldname   =  &6.
  translate: fieldcat_ln-fieldname to upper case.
  append fieldcat_ln to fieldcat.
end-of-definition.

selection-screen: begin of block a10 with frame title a10.
parameters:       variant  like disvariant-variant,
                  rb_grid  radiobutton group r10,
                  rb_alv   radiobutton group r10.
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
           get_cost_distrib_data using subrc.
  if subrc = 0.
    perform: get_header_data.
  endif.

*----------------------------------------------------------------------*
*       Form routine declarations
*----------------------------------------------------------------------*
INCLUDE YPR_TRIP_DATA_FORM_ROUTINES.
*  include: rpr_trip_data_form_routines.

*----------------------------------------------------------------------*
*       Form  GET_HEADER_DATA
*----------------------------------------------------------------------*
*       Select trip header data & sums via v_ptrv_head
*----------------------------------------------------------------------*
form get_header_data.
* Begin YEKAHRK057750
* data: iscos_save like line of iscos.
  data: del_rec.

  field-symbols: <iscos> like line of iscos.
* End YEKAHRK057750

  refresh coltab.

  if not optimize is initial.
*   Version numbers always need to be selected because of the
*   subsequent delete adjacent duplicates.
*   ANTRG and ABREC are required for the authorization checks
    append: 'PERNR' to coltab,
            'REINR' to coltab,                           "YEKAHRK057750
            'PERIO' to coltab,                           "YEKAHRK057750
            'HDVRS' to coltab,
            'PDVRS' to coltab,
            'ANTRG' to coltab,
            'ABREC' to coltab,
            'SEQNO' to coltab.
  endif.

* Get dynamic selection criteria from logical DB
  refresh rg_tabnames.

  append_rg_tabnames: ptrv_head,
                      ptrv_perio,
                      ptrv_shdr.

  perform get_dynamic_selections tables rg_tabnames.

  perform compress_coltab. ".............................YEKL9CK069373

* Select for all entries
  select (coltab) from v_ptrv_head
    into corresponding fields of table ihead
    for all entries in iscos_tmp
    where  pernr       =  iscos_tmp-pernr
    and    reinr       =  iscos_tmp-reinr
    and    perio       =  iscos_tmp-perio
    and    zort1       in ldbzort1
    and    zland       in ldbzland
    and    datv1       in ldbfrom
    and    datb1       in ldbto
    and    sum_reimbu  in ldbreimb
    and    trip_total  in ldbtotal
    and    sum_paidco  in ldbpdc1      "YEKPH9K009401
    and    currency    in ldbcur1
    and    abrec       in ldbabrec
    and    uebrf       in ldbuebrf
    and    kunde       in ldbkunde     "YEKAHRK033171
    and    antrg       in ldbantrg
    and    ueblg       in ldbueblg
    and    uebdt       in ldbuebdt
    and    sum_advanc  in ldbadvc
    and    sum_payout  in ldbpay
*   Begin YEKL9CK045160
    and    pdvrs = ( select min( pdvrs ) from ptrv_perio
                       where pernr = v_ptrv_head~pernr
                       and   reinr = v_ptrv_head~reinr
                       and   perio = v_ptrv_head~perio )
*   End YEKL9CK045160
    and    (xwhere_tab).

  if sy-subrc <> 0.
    message s007.
    exit.
*   No trip data found for specified selection criteria
  endif.





* Eliminate duplicate versions of a trip/period
  sort ihead by pernr reinr perio hdvrs pdvrs seqno.

* Begin YEKL9CK045160
* delete adjacent duplicates from ihead:
*                            comparing pernr reinr perio seqno.
* End YEKL9CK045160

  perform authority_check_item using 'ISCOS'.
  if ihead[] is initial.
*    message s267.
*   Display not possible because of missing authorizations
    exit.
  endif.

* Eliminate duplicate header entries with hard currency data
  perform eliminate_duplicate_headers.

  free iscos_tmp.
* Begin YEKAHRK057750
  loop at iscos assigning <iscos>.
    at new reinr.
      clear: del_rec.

      read table ihead
        with key pernr = <iscos>-pernr
                 reinr = <iscos>-reinr
                 binary search
                 transporting ename sname. "............YEKL9CK031621

      if sy-subrc <> 0.
        del_rec = xfield.
      endif.
    endat.

    if not del_rec is initial.
      delete iscos.
      continue. "........................................YEKL9CK031621
    endif.

*   Begin YEKL9CK031621
    <iscos>-ename = ihead-ename.
    <iscos>-sname = ihead-sname.
*   End YEKL9CK031621
  endloop.
* End YEKAHRK057750

  perform display_data.
endform.                               " GET_HEADER_DATA

*----------------------------------------------------------------------*
*       Form  DISPLAY_DATA
*----------------------------------------------------------------------*
*       Display selected data
*----------------------------------------------------------------------*
form display_data.
  perform: build_sortcat,
           set_layout_options using 'ISCOS',
           call_list_viewer.
endform.                               " DISPLAY_DATA

*----------------------------------------------------------------------*
*       Form  BUILD_FIELDCAT
*----------------------------------------------------------------------*
*       Build field catalog for the list viewer
*----------------------------------------------------------------------*
form build_fieldcat.
  fieldcat_ln-tabname  = 'ISCOS'.
  fieldcat_ln-ctabname = 'ISCOS'.

*    Fieldname          hotspot       do_sum
*                key           no_out        cfieldname
  fc pernr       xfield xfield space  space  space.
  fc reinr       xfield xfield space  space  space.
  fc perio       space  space  xfield space  space.

  fieldcat_ln-tabname  = 'ISCOS'.
  fieldcat_ln-ctabname = 'ISCOS'.
*    Fieldname             hotspot       do_sum
*                   key           no_out        cfieldname
  fieldcat_ln-emphasize = 'C500'.
  fc alloc_amount   space  space  space  xfield 'CURRENCY'.
  clear: fieldcat_ln-emphasize.
  fc currency       space  space  space  space  space.
  fc costcenter     space  space  space  space  space.
  fc co_area        space  space  space  space  space.
  fc internal_order space  space  space  space  space.
  fc sales_ord      space  space  space  space  space.
  fc s_ord_item     space  space  space  space  space.
  fc cost_obj       space  space  xfield space  space.
* Begin YEKL9CK012611
* fc wbs_elem       space  space  xfield space  space.
  fc wbs_elemt      space  space  xfield space  space.
* End YEKL9CK012611
  fc network        space  space  xfield space  space.
  fc activity       space  space  xfield space  space.
  fc co_busproc     space  space  xfield space  space.
  fc funds_ctr      space  space  xfield space  space.
  fc cmmt_item      space  space  xfield space  space.
  fc fund           space  space  xfield space  space.
  fc comp_code      space  space  xfield space  space.
  fc bus_area       space  space  xfield space  space.
* Begin YEKL9BK020306  - duplicate declaration
* fc pernr          space  space  xfield space  space.
* fc reinr          space  space  xfield space  space.
* fc perio          space  space  xfield space  space.
* End YEKL9BK020306
  fc costseqno      space  space  xfield space  space.
* Begin YEKL9CK031621
  fc ename          space  xfield xfield space  space.
  fc sname          space  xfield xfield space  space.
* End YEKL9CK031621

* Begin YEKL9CK039726
  if variant         is initial
    and not rb_grid  is initial.
*   Check if a default variant exists - Grid control only
    perform get_default_variant using disvariant variant.
  endif.
* End YEKL9CK039726

  if not variant is initial and not optimize is initial.
*   Begin YEKL9CK031621
*   perform get_fieldcat_from_variant using disvariant 'IHEAD' 'ISCOS'.
    perform get_fieldcat_from_variant using disvariant 'ISCOS' space.
*   End YEKL9CK031621
  endif.
endform.                               " BUILD_FIELDCAT

*----------------------------------------------------------------------*
*       Form  BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Build sort catalog for the list viewer
*----------------------------------------------------------------------*
form build_sortcat.
*    Sortpos        Up            Subtot
*      Sortfield           Down          Group
  sortcat_ln-tabname = 'ISCOS'.
  sc 1 pernr        xfield space  space  space.
  sc 2 reinr        space  xfield xfield space.
  sc 3 alloc_amount space  xfield space  space.
endform.                               " BUILD_SORTCAT
*----------------------------------------------------------------------*
*       Form  CALL_LIST_VIEWER
*----------------------------------------------------------------------*
*       Start list viewer
*----------------------------------------------------------------------*
form call_list_viewer.
  if not count_reject is initial.
    message s268.
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




SUBMIT YPR_TRIP_ROUT_1_4

          EXPORTING LIST TO MEMORY  AND RETURN.

          IMPORT IHEAD3 FROM MEMORY ID 'IHEADTABLE' .

          free memory id 'IHEADTABLE'.


*AHOUNOUALAIN

clear wa_iscos .
clear wa_ihead.


   loop at ihead3 into wa_ihead .

    if wa_ihead-TRIP_TOTAL ne 0.

       loop at iscos into wa_iscos where pernr = wa_ihead-pernr
                                  and reinr = wa_ihead-reinr.
*                                  and perio = wa_ihead-perio.


              append wa_iscos to iscos2.
              clear wa_iscos.
        endloop.

    endif.
    clear wa_ihead.

   endloop.



*AHOUNOUALAIN


  if rb_alv is initial.
    call function 'REUSE_ALV_GRID_DISPLAY'
         exporting
              i_buffer_active         =  xfield "........YEKL9CK016665
              i_callback_program      =  pgm
              i_callback_user_command = 'USER_COMMAND'
              is_layout               =  layout
              it_fieldcat             =  fieldcat
              it_sort                 =  sortcat
*             i_save                   = variant_save    YEKL9BK025794
              i_save                   = lf_save ".......YEKL9BK025794
              is_variant              =  disvariant
         tables
              t_outtab                = iscos2
         exceptions
              program_error           =  1
              others                  =  2.
  else.
    call function 'REUSE_ALV_LIST_DISPLAY'
         exporting
              i_buffer_active         =  xfield "........YEKL9CK016665
              i_callback_program      =  pgm
              i_callback_user_command = 'USER_COMMAND'
              is_layout               =  layout
              it_fieldcat             =  fieldcat
              it_sort                 =  sortcat
*             i_save                   = variant_save    YEKL9BK025794
              i_save                   = lf_save ".......YEKL9BK025794
              is_variant              =  disvariant
         tables
              t_outtab                =  iscos2
         exceptions
              program_error           =  1
              others                  =  2.
  endif.
endform.                               " CALL_LIST_VIEWER


*---------------------------------------------------------------------*
*       FORM USER_COMMAND
*---------------------------------------------------------------------*
*       Callback routine for function REUSE_ALV_LIST_DISPLAY
*       Execute commands
*---------------------------------------------------------------------*
form user_command using    ucomm like sy-ucomm
                  selfield type slis_selfield.

* read table ihead index selfield-tabindex.              "YEKAHRK052310
  read table iscos2 index selfield-tabindex.              "YEKAHRK052310
  if sy-subrc <> 0.
    exit.
  endif.

  case ucomm.
    when '&IC1'.
      if selfield-sel_tab_field cs 'REINR'.
        perform interactive_display using 'XX X'
*                                          ihead-pernr   "YEKAHRK052310
*                                          ihead-reinr.  "YEKAHRK052310
                                           iscos2-pernr   "YEKAHRK052310
                                           iscos2-reinr.  "YEKAHRK052310
      elseif selfield-sel_tab_field cs 'PERNR' or
             selfield-sel_tab_field cs 'ENAME' or "......YEKL9CK031621
             selfield-sel_tab_field cs 'SNAME'. "........YEKL9CK031621

*       perform get_name using ihead-pernr ihead-datb1.  "YEKAHRK052310
        perform get_name using iscos2-pernr sy-datum.     "YEKAHRK052310
      endif.
  endcase.
endform.
*----------------------------------------------------------------------*
*       Form  GET_COST_DISTRIB_DATA
*----------------------------------------------------------------------*
*       Read cost distribution data from PTRV_SCOS
*----------------------------------------------------------------------*
form get_cost_distrib_data using rc like sy-subrc.
  rc = 0.

  if optimize is initial.
    refresh coltab.
  else.
    perform get_active_columns using 'ISCOS'.
*   Personnel number, trip number and period are
*   necessary for subsequent select from v_ptrv_head
    append: 'PERNR' to coltab,
            'REINR' to coltab,
            'PERIO' to coltab.

*   Begin YEKL9CK031621
    delete coltab
      where fieldname = 'ENAME'
      or    fieldname = 'SNAME'.
*   End YEKL9CK031621
  endif.

* Get dynamic selection criteria from logical DB
  append_rg_tabnames: ptrv_scos.

  perform get_dynamic_selections tables rg_tabnames.

  perform manipulate_ldbkdwbs(sapdbptrvp).                  "QIZK048907

  perform compress_coltab. ".............................YEKL9CK069373

* if count_pernr <= 200.                                 "YEKAHRK056800
  if count_pernr <= sfae_limit.                          "YEKAHRK056800
*   Regular select statement
    select (coltab)
      into corresponding fields of table iscos
      from ptrv_scos
      where  pernr          in ipernr
      and    reinr          in ldbtrip
      and    costcenter     in ldbkost2
      and    co_area        in ldbkokrs
      and    internal_order in ldbaufnr
      and    sales_ord      in ldbkdauf
      and    s_ord_item     in ldbkdpos
      and    wbs_elemt      in ldbkdwbs                     "QIZK048907
      and    alloc_amount   in ldbalamt
      and    currency       in ldbcur3
      and    (xwhere_tab).
  else.
*   Select for all entries
    select (coltab)
      into corresponding fields of table iscos
      from ptrv_scos for all entries in ipernr
      where  pernr          =  ipernr-low
      and    reinr          in ldbtrip
      and    costcenter     in ldbkost2
      and    co_area        in ldbkokrs
      and    internal_order in ldbaufnr
      and    sales_ord      in ldbkdauf
      and    s_ord_item     in ldbkdpos
      and    wbs_elemt      in ldbkdwbs                     "QIZK048907
      and    alloc_amount   in ldbalamt
      and    currency       in ldbcur3
      and    (xwhere_tab).
  endif.

  if sy-subrc = 0.
* QIZK048907 begin...
    loop at iscos.
      call function 'CJPN_INTERN_TO_EXTERN_CONV'
           exporting
                int_num = iscos-wbs_elemt
           importing
                ext_num = iscos-wbs_elemt.
      modify iscos.
    endloop.
* QIZK048907 end...
    sort iscos by pernr reinr perio costseqno.
    iscos_tmp[] = iscos[].
    delete adjacent duplicates from iscos_tmp.
  else.
    message s007.
*   No trip data found for specified selection criteria
    rc = 4.
    exit.
  endif.

endform.                               " GET_RECEIPT_DATA



*----------------------------------------------------------------------*
*       Form  BUILD_RELATIONSHIP
*----------------------------------------------------------------------*
*       Build relationship between header and item table
*----------------------------------------------------------------------*
form build_relationship.
  keyinfo-header01 = 'PERNR'.
  keyinfo-item01   = 'PERNR'.
  keyinfo-header02 = 'REINR'.
  keyinfo-item02   = 'REINR'.
  keyinfo-header03 = 'PERIO'.
  keyinfo-item03   = 'PERIO'.
  keyinfo-header04 =  space.
  keyinfo-item04   = 'COSTSEQNO'.
endform.                               " BUILD_RELATIONSHIP
