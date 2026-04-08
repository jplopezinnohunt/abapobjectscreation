* 1.10
* YEKP1HK001358 08/29/2002 - incorrect authority check (note 549723)
* YEKP1HK001118 08/06/2002 - incorrect authority check (note 543662)
* 4.6C
* YEKL9CK069373 10/04/2001 - wrong reporting results (note 440712)
* YEKL9CK051858 05/03/2001 - Authority check (note 401170)
* YEKL9CK049417 04/10/2001 - Mileage sumations (note 396171)
* YEKL9CK039726 01/29/2001 - Default variants (note 377704)
* YEKL9CK031621 11/27/2000 - Employee name in ALV list (note 361865)
* YEKL9CK023161 09/13/2000 - Service Provider Info (note 332921)
* YEKAHRK056800 09/10/1999 - Not all trips selected
* 4.6A
* YEKAHRK047461 03/29/1999 - Delete adjacent duplicates incorrect
*----------------------------------------------------------------------*
* Subroutines for RPR_TRAVEL reports                                   *
*----------------------------------------------------------------------*

*----------------------------------------------------------------------*
*       Form  COMPRESS_IPERNR
*----------------------------------------------------------------------*
*       Compress I EQ entries in table ipernr into I BT entries
*       for better performance of the select statement
*----------------------------------------------------------------------*
form compress_ipernr.
* Begin YEKAHRK056800
  data: ipernr_tmp like ipernr occurs 0.

  ipernr_tmp[] = ipernr[].
* End of YEKAHRK056800

  call function 'PTRV_COMPRESS_SELECT_OPTIONS'
       tables
            pernr_so = ipernr
            bukrs_so = ldbbukrs
            kostl_so = ldbkost1.

  describe table: ipernr lines count_pernr.

* Begin YEKAHRK056800
  if count_pernr > sfae_limit.
    ipernr[] = ipernr_tmp[].
  endif.
* End YEKAHRK056800
endform.                               " COMPRESS_IPERNR
*----------------------------------------------------------------------*
*       Form  GET_NAME
*----------------------------------------------------------------------*
*       Display name for personnel number
*----------------------------------------------------------------------*
form get_name using pernr like p0001-pernr
                    date  like sy-datum.

  call function 'PTRV_GET_NAME_FOR_PERNR'
       exporting
            personnel_number = pernr
            validity_date    = date
            start_column     = 12
            start_row        = 4
       exceptions
            name_not_found   = 1
            others           = 2.
endform.                               " GET_NAME
*----------------------------------------------------------------------*
*       Form  INTERACTIVE_DISPLAY
*----------------------------------------------------------------------*
*       Interactive display according to selection pop-up
*----------------------------------------------------------------------*
*      --> SEL - Selection string
*                Pos1 = X -> Display Trip
*                Pos2 = X -> Display Trip Receipt Data
*                Pos2 = X -> Display Trip Cost Distribution
*----------------------------------------------------------------------*
form interactive_display using sel    type c
                               xpernr like ptrv_head-pernr
                               xreinr like ptrv_head-reinr.

  call function 'PTRV_SELECT_DISPLAY_OBJECT'
       exporting
            personnel_number = xpernr
            trip_number      = xreinr
            active_buttons   = sel
            start_row        = 10
            start_column     = 20
       exceptions
            no_buttons       = 1
            others           = 2.

endform.                               " INTERACTIVE_DISPLAY

*----------------------------------------------------------------------*
*       Form  SET_LAYOUT_OPTIONS
*----------------------------------------------------------------------*
*       Set list layout options for list viewer
*----------------------------------------------------------------------*
form set_layout_options using tname type c.
  data: lcount type i.

  clear: layout.

  layout-detail_initial_lines = xfield.
  layout-colwidth_optimize    = xfield.
  layout-cell_merge           = xfield. "................YEKL9CK031621
  layout-no_author            = xfield. "................YEKL9CK031621

  case tname.
    when 'IHEAD'.
      describe table ihead lines lcount.
      if lcount = 1.
*       Only one entry in table -> turn totals and subtotals off
        layout-no_subtotals = xfield.
        layout-no_totalline = xfield.
      elseif not ldbownpn is initial or count_pernr = 1.
*       More than one entry in table but only for one pernr
*       -> turn subtotals off
        layout-no_subtotals = xfield.
      endif.
    when 'ISREC'.
      describe table isrec lines lcount.
      if lcount = 1.
        layout-no_subtotals = xfield.
        layout-no_totalline = xfield.
      elseif not ldbownpn is initial or count_pernr = 1.
*       More than one entry in table but only for one pernr
*       Is it receipts for only one trip or more trips ?
        clear lcount.
        loop at isrec.
          on change of isrec-reinr.
            add 1 to lcount.
            if lcount = 2.
              exit.
            endif.
          endon.
        endloop.
        if lcount = 1.
*         Only one trip -> turn subtotals off
          layout-no_subtotals = xfield.
        endif.
      endif.


    when 'ISCOS'.
      describe table iscos lines lcount.
      if lcount = 1.
        layout-no_subtotals = xfield.
        layout-no_totalline = xfield.
      elseif not ldbownpn is initial or count_pernr = 1.
*       Is it cost for only one trip or more trips ?
        clear lcount.
        loop at iscos.
          on change of iscos-reinr.
            add 1 to lcount.
            if lcount = 2.
              exit.
            endif.
          endon.
        endloop.
        if lcount = 1.
*         Only one trip -> turn subtotals off
          layout-no_subtotals = xfield.
        endif.
      endif.
  endcase.
endform.                               " SET_LAYOUT_OPTIONS
*----------------------------------------------------------------------*
*       Form  AUTHORITY_CHECK_ITEM
*----------------------------------------------------------------------*
*       Check if user is authorized to display selected header items
*       Only for people you can look at more than their own stuff
*----------------------------------------------------------------------*
form authority_check_item using tname type c.

* Begin YEKP1HK001358
  data: lt_pa0017 type hashed table of pa0017
                    with unique key pernr,
        ls_pa0017 like line of lt_pa0017,
        lf_kostl  type pa0017-kostl.
* End YEKP1HK001358

  data: lf_authp type authp. "...........................YEKP1HK001118

  data: begin of authf,
          id     value 'S',
          antrg,
          abrec,
        end of authf.

  data: lf_ptzuo type ptzuo. "...........................YEKL9CK051858

  field-symbols: <ihead> like line of ihead. "...........YEKL9CK031621

* Begin YEKP1HK001358
  import ldb_pa0017_tab to lt_pa0017
           from memory id 'SAPDBPTRVP'.
* End YEKP1HK001358

* ldbownpn is set by the logical DB during its authorization check
* check ldbownpn is initial. "...........................YEKL9CK031621

  loop at ihead assigning <ihead>. ".....................YEKL9CK031621
    ihead = <ihead>. "...................................YEKL9CK031621

    at new pernr.
      read table ipernr_tmp with table key pernr = ihead-pernr.
      if sy-subrc <> 0.
*       Should never happen
        delete ihead
          where pernr = ihead-pernr.
*       Delete corresponding records in item tables
        case tname.
          when 'ISREC'.
            delete isrec
              where pernr = ihead-pernr.
          when 'ISCOS'.
            delete iscos
              where pernr = ihead-pernr.
        endcase.
        add 1 to count_reject.
        continue.
      endif.

*     Begin YEKP1HK001358
      clear:  ls_pa0017,
              lf_ptzuo,
              lf_kostl.

      read table lt_pa0017 with table key pernr = ihead-pernr
        into ls_pa0017.

      lf_ptzuo = ls_pa0017-ptzuo.

      lf_kostl = ipernr_tmp-kostl.

      if not ls_pa0017-kostl is initial.
        lf_kostl = ls_pa0017-kostl.
      endif.

*     Begin YEKL9CK051858
*      select ptzuo into lf_ptzuo
*        from pa0017 up to 1 rows
*        where pernr = ihead-pernr
*        and   begda <= sy-datum
*        and   endda >= sy-datum.
*      endselect.
*      if not sy-subrc is initial.
*        clear: lf_ptzuo.
*      endif.
*     End YEKL9CK051858
*     End YEKP1HK001358

*     Begin YEKP1HK001118
      call function 'PTRV_DETERMINE_AUTHP'
           exporting
                current_pernr = ihead-pernr
           importing
                authp         = lf_authp.
*     End YEKP1HK001118

    endat.

    authf-antrg = ihead-antrg.
    authf-abrec = ihead-abrec.

    <ihead>-mileage_total = <ihead>-m_total. "...........YEKL9CK049417

*   Begin YEKL9CK031621
    <ihead>-ename = ipernr_tmp-ename.
    <ihead>-sname = ipernr_tmp-sname.

    check ldbownpn is initial. " ........................YEKL9CK031621
*   End   YEKL9CK031621

    authority-check object 'P_TRAVL'
*     id 'AUTHP' dummy ".................................YEKP1HK001118
      id 'AUTHP' field lf_authp  ".......................YEKP1HK001118
      id 'BUKRS' field ipernr_tmp-bukrs
      id 'PERSA' field ipernr_tmp-werks
*     id 'KOSTL' field ipernr_tmp-kostl "................YEKP1HK001358
      id 'KOSTL' field lf_kostl "........................YEKP1HK001358
      id 'PERSG' field ipernr_tmp-persg
      id 'PERSK' field ipernr_tmp-persk
*     id 'VDSK1' dummy
      id 'VDSK1' field ipernr_tmp-vdsk1 "................YEKL9CK061635
*     id 'PTZUO' dummy ".................................YEKL9CK051858
      id 'PTZUO' field lf_ptzuo "........................YEKL9CK051858
      id 'AUTHF' field authf
      id 'AUTHS' dummy.

    if sy-subrc <> 0.
      delete ihead.

*     Delete corresponding records in item tables
      case tname.
        when 'ISREC'.
          delete isrec
            where pernr = ihead-pernr
            and   reinr = ihead-reinr.
        when 'ISCOS'.
          delete iscos
            where pernr = ihead-pernr
            and   reinr = ihead-reinr.
      endcase.

      add 1 to count_reject.
    endif.
  endloop.

  free ipernr_tmp.
endform.                               " AUTHORITY_CHECK_ITEM
*----------------------------------------------------------------------*
*       Form  GET_DYNAMIC_SELECTIONS
*----------------------------------------------------------------------*
*       Get dynamic selection criteria from logical database
*----------------------------------------------------------------------*
*      --> xtab - ranges table with table names
*----------------------------------------------------------------------*
form get_dynamic_selections tables xtab structure rg_tabnames.
  refresh: where_tab,
           xwhere_tab.

  assign (ldb_where) to <f1>.

  where_tab[] = <f1>.

  unassign <f1>.

  if not where_tab[] is initial.
    loop at where_tab into where_tab_ln
      where tablename in rg_tabnames.
      append lines of where_tab_ln-where_tab to xwhere_tab.
    endloop.

    loop at xwhere_tab from 2
      where line+0(3) = space.
      write 'AND' to xwhere_tab+0(3).
      modify xwhere_tab.
    endloop.
  endif.

endform.                               " GET_DYNAMIC_SELECTIONS
*----------------------------------------------------------------------*
*       Form  ELIMINATE_DUPLICATE_HEADERS
*----------------------------------------------------------------------*
*       Eliminate duplicate header records for trips with hard
*       currencies and multiple reimbursement amounts with
*       different currencies
*----------------------------------------------------------------------*
form eliminate_duplicate_headers.
  data:          ihead_ln like v_ptrv_head,
                 msg,
                 tabix    like sy-tabix.

* Begin YEKL9CK031621
* field-symbols: <ihead>     like v_ptrv_head,
*                <ihead_old> like v_ptrv_head.
  field-symbols: <ihead>     like line of ihead,
                 <ihead_old> like line of ihead.

* End YEKL9CK031621

  loop at ihead assigning <ihead>.
    if <ihead>-seqno = 2.
*     Multiple headers exist -> reset amount in record 1 and delete
*     the rest
      tabix = sy-tabix - 1.
      read table ihead assigning <ihead_old> index tabix.
      if sy-subrc = 0.
        clear: <ihead_old>-addit_amnt,
               <ihead_old>-sum_reimbu,
               <ihead_old>-sum_advanc,
               <ihead_old>-sum_payout,
               <ihead_old>-sum_paidco,
               <ihead_old>-trip_total,
               <ihead_old>-pd_food,
               <ihead_old>-pd_housing,
               <ihead_old>-pd_mileage,
               <ihead_old>-currency.
      endif.
      msg = xfield.
    endif.
    if <ihead>-seqno > 1.
      delete ihead.
    endif.
  endloop.

  if not msg is initial.
    message s352(56).
*   Anzeige enthält Reisen mit mehreren Erstattungsbeträgen. Langtxt be
  endif.
endform.                               " ELIMINATE_DUPLICATE_HEADERS
*----------------------------------------------------------------------*
*       Form  get_provider_info                  new with YEKL9CK023161
*----------------------------------------------------------------------*
*       get long texts for providers
*----------------------------------------------------------------------*
form get_provider_info using im_ctg type provider_category
                             im_prv type provider_code
                             ex_ctg_text type c
                             ex_prv_text type c.

  statics: lt_dd07v      type standard table of dd07v initial size 10,
           ls_dd07v      like line of lt_dd07v,
           lt_ta21p      type hashed table of ta21p
                              with unique key category provider,
           ls_ta21p      like line of lt_ta21p.

  if lt_dd07v is initial.
    call function 'DDIF_DOMA_GET'
         exporting
              name          = 'FTPD_PROVIDER_CATEGORY'
              langu         = sy-langu
         tables
              dd07v_tab     = lt_dd07v
         exceptions
              illegal_input = 1
              others        = 2.

    sort lt_dd07v by domvalue_l.
  endif.

  if ls_dd07v-domvalue_l <> im_ctg.
    read table lt_dd07v with key domvalue_l = im_ctg
                             into ls_dd07v
                             binary search.

    if not sy-subrc is initial.
      clear: ls_dd07v.
    endif.
  endif.

  ex_ctg_text = ls_dd07v-ddtext.

  if ls_ta21p-category <> im_ctg or
     ls_ta21p-provider <> im_prv.
    read table lt_ta21p with table key category = im_ctg
                                       provider = im_prv
                                       into ls_ta21p.

    if not sy-subrc is initial.
      select single * from ta21p into ls_ta21p
        where category = im_ctg
        and   provider = im_prv.

      if not sy-subrc is initial.
        clear: ls_ta21p.
        ls_ta21p-category = im_ctg.
        ls_ta21p-provider = im_prv.
      endif.

      insert ls_ta21p into table lt_ta21p.
    endif.
  endif.

  ex_prv_text = ls_ta21p-name.

endform.                    " get_provider_info
*----------------------------------------------------------------------*
*       Form  get_default_variant
*----------------------------------------------------------------------*
*       Determine default variant for ALV list - new with YEKL9CK039726
*----------------------------------------------------------------------*
form get_default_variant using value(im_disvar) type disvariant
                                     ex_variant like disvariant-variant.

  call function 'LVC_VARIANT_DEFAULT_GET'
       exporting
            i_save        = 'U'
       changing
            cs_variant    = im_disvar
       exceptions
            wrong_input   = 1
            not_found     = 2
            program_error = 3
            others        = 4.

  ex_variant = im_disvar-variant.

endform.                    " get_default_variant

*---------------------------------------------------------------------*
*       FORM compress_coltab - new with YEKL9CK069373
*---------------------------------------------------------------------*
*       Make sure fields in coltab are unique - otherwise
*       incorrect results with select for all entries
*---------------------------------------------------------------------*
form compress_coltab.

  sort coltab.
  delete adjacent duplicates from coltab.

endform.                    "compress_coltab
