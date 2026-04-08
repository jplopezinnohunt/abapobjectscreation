*----------------------------------------------------------------------*
* Data declarations for RPR_TRAVEL  reports                            *
*----------------------------------------------------------------------*
* 1.10
* YEKP1HK000676 07/17/2002 - field ANZAHL (note 538048)
* 4.6C
* YEKL9CK061635 07/24/2001 - Authority check (note 423136)
* YEKL9CK049417 04/10/2001 - Mileage sumations (note 396171)
* YEKL9CK031621 11/27/2000 - Employee name in ALV list (note 361865)
* YEKL9CK024129 09/21/2000 - XCIPH0K008979 backed out (note 334898)
* YEKL9CK023161 09/13/2000 - Service Provider Info (note 332921)
* XCIPH0K008979 04022000 create a special internal table for ALV
*               because the length of a field is too small for ALV
* YEKAHRK056800 09/10/1999 - Not all trips selected
*----------------------------------------------------------------------*
tables:    pa0001,                     "Org.assignment data
           ptrv_head,                  "Trip frame data
           ptrv_shdr,                  "Trip sums
           ptrv_perio,                 "Trip periods
           sscrfields,                 "Selection Screen Stuff
           v_ptrv_head,                "View of trip header & sums
           v_ptrv_srec.                "View of trip recipts & add info

type-pools: rsds.

types:     begin of ipernr_tmp,
             pernr  like p0001-pernr,
             bukrs  like p0001-bukrs,
             werks  like p0001-werks,
             kostl  like p0001-kostl,
             persg  like p0001-persg,
             persk  like p0001-persk,
             ename  like p0001-ename, "..................YEKL9CK031621
             sname  like p0001-sname, "..................YEKL9CK031621
             vdsk1  like p0001-vdsk1, "..................YEKL9CK061635
           end of ipernr_tmp.

types:     begin of isrec.
include      type  v_ptrv_srec.
types:       sptxt like t706c-sptxt,
*            Begin YEKL9CK023161
             ctg_text type txt30,
             prv_text type provider_name,
*            End YEKL9CK023161
*            Begin YEKL9CK031621
             ename    type emnam,
             sname    type smnam,
*            End YEKL9CK031621
             multipli_lrg type i, "......................YEKP1HK000676
           end of isrec,

           begin of isrec_tmp,
             mandt     like v_ptrv_srec-mandt,
             pernr     like v_ptrv_srec-pernr,
             reinr     like v_ptrv_srec-reinr,
             perio     like v_ptrv_srec-perio,
           end of isrec_tmp.

data:      col_pos        type i,
           count_pernr    type i,
           count_reject   type i,
           delta          like sy-uzeit,
*K031621   ihead          like v_ptrv_head   occurs 0 with header line,
           ip0001         type ptrv_stats_p0001_itab  with header line,
           ipernr         type ptrv_pernr_so occurs 0 with header line,
           ipernr_tmp     type hashed table of ipernr_tmp
                                      with unique key pernr
                                      with header line,
*          iscos          like ptrv_scos     occurs 0 with header line,
           iscos_tmp      type isrec_tmp     occurs 0 with header line,
           isrec          type isrec         occurs 0 with header line,
           isrec_tmp      type isrec_tmp     occurs 0 with header line,
           subrc          like sy-subrc,
           where_tab      type rsds_where occurs 0,
           where_tab_ln   like line of where_tab,
           xwhere_tab     like rsdswhere occurs 50 with header line.

* Begin YEKL9CK031621
data:       begin of ihead occurs 0.
              include structure v_ptrv_head.
data:         ename         type emnam,
              sname         type smnam,
              mileage_total type i,  "...................YEKL9CK049417
            end of ihead.

data:       begin of ihead2 occurs 0.
              include structure v_ptrv_head.
data:         ename         type emnam,
              sname         type smnam,

            end of ihead2.

data:       begin of ihead3 occurs 0.
              include structure v_ptrv_head.
data:         ename         type emnam,
              sname         type smnam,

            end of ihead3.

data:       begin of iscos occurs 0.
              include structure ptrv_scos.
data:         ename   type emnam,
              sname   type smnam,
            end of iscos.
* End YEKL9CK031621

data:       begin of iscos2 occurs 0.
              include structure ptrv_scos.
data:         ename   type emnam,
              sname   type smnam,
            end of iscos2.

data wa_iscos like line of iscos.
data wa_ihead like line of ihead.


ranges:    rg_tabnames for rsdstabs-prim_tab.

field-symbols: <f1>,
               <isrec> type isrec.

* Constant definitions
include:   rpr_travel_stats_constants.

constants: ldb_where(30) value '(SAPDBPTRVP)DYN_SEL-CLAUSES',
           sfae_limit    type i value '200'.             "YEKAHRK056800

* Data declarations for ABAP list viewer
include rpr_alv_data.

* Macros
define append_rg_tabnames.
  rg_tabnames-sign   = 'I'.
  rg_tabnames-option = 'EQ'.
  rg_tabnames-low    = '&1'.
  append rg_tabnames.
end-of-definition.
