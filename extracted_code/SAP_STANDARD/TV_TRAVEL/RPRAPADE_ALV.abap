* 6.06
* MAWH1492437   28072010 Erweiterte Programmprüfung im RPRAPA00: Warnung
*                        [note 1492437]

* 7.00
* MAWPR0K013477 03112006 RPRAPA00: Probleme bei Komponentennamen > 10
*                        Zeichen [note 995726]
* 4.70
* QIZPL0K032746 02052002 daily run of RPRAPA00...
* QIZPL0K023533 12042002 MOLGA replaced by COUNTRY...
* QIZAL0K101633 05022002 RPRAPA00 adapted to PS master data
* 4.6C Hot Package
* QIZP9CK082452 13102000 create company code segments
* QIZP9CK053440 wrong messages
* QIZP9CK047575 withholding tax data implemented
* 4.0C
* QIZAHRK003419 Mahndaten aufgenommen

* Data definition

TABLES:  pernr,                        " HR-master-data
         bgr00,                        " Mappenvorsatz
         blf00,                        " Kred. Batch-Input-Kopfsatz
         blfa1, lfa1, *lfa1,           " Kred. Allgemein Teil 1
         blfb1, lfb1, *lfb1,           " Kred. Buchungskreisdaten
         blfbk,                        " Kred. Bankverbindungen
         blfbk_iban,                   " Kred. Bankverbindungen IBAN          "ARIK142351 / Note 1555565
         lfbk, *lfbk,                  " Kred. Bankverbindung
         blfb5,                        " Kred. Mahndaten
         lfb5, *lfb5,                  " Kred. Mahndaten  "QIZK003419
* QIZK047575 begin...
         blfbw,                        " Kred. erwiterte Quellensteuer
         lfbw, *lfbw,                  " Kred. erwiterte Quellensteuer
* QIZK047575 end...
         blfm1,                        " Kred. Einkaufsdaten
         t001, *t001,                  " Buchungskreis Daten
         t500p, *t500p,                " HR-Ländergruppierung
         t522t,                        " HR-Anrede
         dd03l,                        " DDIC-Felder
         t001p,                        " Adressaufbereitung
         adrs,                         " Adressaufbereitung
         pme11.                        " Structure for feature TRVHB

TABLES  p0017.                                              "WKUK039334
DATA BEGIN OF p0017_help OCCURS 2.
                                                            "WKUK039334
        INCLUDE STRUCTURE p0017.                            "WKUK039334
DATA END OF p0017_help.
                                                            "WKUK039334

INFOTYPES: 0000 OCCURS 2,              " measure
           0001 OCCURS 2,              " Org. Assignment
           0002 OCCURS 2,              " Personal Data
           0006 OCCURS 2,              " Addresses
*          0017 OCCURS 2,              " Travel privileges  "WKUK039334
           0009 OCCURS 2.              " Bank Details

FIELD-SYMBOLS: <str_fields>.
FIELD-SYMBOLS: <templ_fields>.

DATA: jobcount   LIKE tbtco-jobcount.

FIELD-SYMBOLS: <old_vendor_fields>.
DATA: BEGIN OF old_vendor_lfa1.
        INCLUDE STRUCTURE lfa1.
DATA: END OF old_vendor_lfa1.
DATA: BEGIN OF old_vendor_lfb1.
        INCLUDE STRUCTURE lfb1.
DATA: END OF old_vendor_lfb1.
DATA: BEGIN OF old_vendor_lfb5.                             "QIZK003419
        INCLUDE STRUCTURE lfb5.                             "QIZK003419
DATA: END OF old_vendor_lfb5.                               "QIZK003419
DATA: BEGIN OF old_vendor_lfbw OCCURS 5.                    "QIZK047575
        INCLUDE STRUCTURE lfbw.                             "QIZK047575
DATA: END OF old_vendor_lfbw.                               "QIZK047575

DATA: BEGIN OF old_vendor_lfbk OCCURS 5,
      banks LIKE lfbk-banks,
      bankl LIKE lfbk-bankl,
      bankn LIKE lfbk-bankn,
      END OF old_vendor_lfbk.

DATA: repname LIKE sy-repid.
DATA: lin TYPE p.
DATA: t_code LIKE sy-tcode.
DATA: subrc LIKE sy-subrc.
DATA: pack TYPE p.
DATA: trvhb(11).
DATA  w_changes TYPE n.
DATA: h_line(80).
DATA: msg(100).                        "Message for OPEN DATASET
DATA: sw_stop(1).
DATA: first_process_global(1).
*DATA: fields(16).                                          "MAWK013477
*DATA: old_fields(26).                                      "MAWK013477
*DATA: fields_lfa_b1(16).                                   "MAWK013477
DATA: fields        TYPE c LENGTH 47.                       "MAWK013477
DATA: old_fields    TYPE c LENGTH 47.                       "MAWK013477
DATA: fields_lfa_b1 TYPE c LENGTH 47.                       "MAWK013477
* DATA: FILE_K(1000).                                       "QIZK053440
*DATA: file_k(1500).                            "QIZK053440 "MAWH1492437
*TYPES tv_file TYPE c LENGTH 1500.                           "MAWH1492437
TYPES: tv_file TYPE c LENGTH 2000. "GLW note 2055543
DATA  file_k  TYPE tv_file.                                 "MAWH1492437
DATA: vendor_no LIKE lfb1-lifnr.                            "QIZK082452

DATA: nodata VALUE '/'.
* Workarea zur Testausgabe des erstellten Files
DATA: BEGIN OF wa,
        char1(250)   TYPE c,
        char2(250)   TYPE c,
        char3(250)   TYPE c,
        char4(250)   TYPE c,
      END OF wa.
* Structure and internal table for error-handling
DATA: BEGIN OF error OCCURS 10.
        INCLUDE STRUCTURE hrerror.
DATA: END OF error.
DATA: BEGIN OF error_int OCCURS 20.
        INCLUDE STRUCTURE hrerror.
DATA: END OF error_int.
DATA: text LIKE t100-text,
      fcode(4),
      messtxt(300).

* errortable contains all rejected personnel numbers
DATA: BEGIN OF errortable OCCURS 500,
        pernr LIKE pernr-pernr,
        name(40),
        p0001(1),
        p0002(1),
        p0006(1),
        p0009(1),
        pxxxx(1),
      END OF errortable.

* logtable contains all personnel numbers on the output file.
DATA: BEGIN OF logtable OCCURS 500,
        pernr LIKE pernr-pernr,
        name(40),
      END OF logtable.
* table with locked pesonnel numbers
DATA: BEGIN OF lockedtable OCCURS 10,
        pernr LIKE pernr-pernr,
        name(40),
      END OF lockedtable.
* table with employees who already have vendor accounts
DATA: BEGIN OF apaccounttable OCCURS 50,
        pernr LIKE pernr-pernr,
        name(40),
      END OF apaccounttable.
* QIZK082452 begin...
* table contains all employees which have an vendor account and should
* get a new LFB1 segment. But this segment exists already without PERNR.
DATA: BEGIN OF apaccount_without_pernr OCCURS 50,
        pernr LIKE pernr-pernr,
        name(40),
        vendor_no LIKE lfb1-lifnr,
        bukrs LIKE lfb1-bukrs,
      END OF apaccount_without_pernr.
* QIZK082452 end...
* statistics
DATA: sel_pernr(6)      TYPE n.        "selected personnel numbers
DATA: sel_on_file(6)    TYPE n.        "personnel numbers on file
DATA: sel_rejected(6)   TYPE n.        "personnel numbers rejected
DATA: sel_locked(6)     TYPE n.        "personnel numbers locked
DATA: sel_ex_vendors(6) TYPE n.        "existing vendors
DATA: sel_no_changes(6) TYPE n.        "non-existing changes in HR
DATA: sel_no_changes_for_today(6) TYPE n.                   "QIZK032746
DATA: sel_no_vendors(6) TYPE n.        "non-existing vendors
DATA: sel_with_error(6) TYPE n. "personnel number with error message "GLW note 1989485

* Entkopplung T001
DATA: t001_bukrs LIKE hrca_company-comp_code,
      t001_butxt LIKE hrca_company-comp_name,
      t001_ort01 LIKE hrca_company-city,
      t001_land1 LIKE hrca_company-country,
      t001_waers LIKE hrca_company-currency,
      t001_ktopl LIKE hrca_company-chrt_accts,
      t001_periv LIKE hrca_company-fy_variant,
      t001_spras LIKE hrca_company-langu.

DATA: ps_master_data_active LIKE boole-boole.               "QIZK101633
* QIZK023533 begin...
DATA  molga LIKE t706d-molga.  "MOLGA according to country (P0006-LAND1)
* QIZK023533 end...

************* Start ALV Coding C5056168 28/02/2005*****************
TYPE-POOLS : slis.

CONSTANTS : gc_y(1) TYPE c VALUE 'Y',
            gc_x(1) TYPE c VALUE 'X',
            gc_struct_alv1 TYPE dd02l-tabname VALUE 'RPRAPA00_ALV1',
            gc_struct_alv2 TYPE dd02l-tabname VALUE 'RPRAPA00_ALV2',
            gc_struct_alv3 TYPE dd02l-tabname VALUE 'RPRAPA00_ALV3',
            gc_struct_stats TYPE dd02l-tabname VALUE 'HRPAD_PAL_STATS',
            gc_top_of_page_file TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_FILE',
            gc_top_of_page_log TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_LOG',
            gc_top_of_page_error TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_ERROR',
            gc_top_of_page_lock TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_LOCK',
            gc_top_of_page_apac TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_APAC',
            gc_top_of_page_apac_wo_pernr TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_APAC_WO_PERNR',
            gc_top_of_page_stats TYPE slis_alv_event-form
                           VALUE 'TOP_OF_PAGE_STATS'.

FIELD-SYMBOLS : <gf_outtab> TYPE STANDARD TABLE. "ALV Output table

*ALV Output strutures
TYPES : BEGIN OF ty_outtab_file.
        INCLUDE STRUCTURE rprapa00_alv1.
TYPES : color TYPE slis_t_specialcol_alv,
       END OF ty_outtab_file.     "File

DATA : gs_outtab_file TYPE ty_outtab_file,               "File
       gs_outtab_error TYPE rprapa00_alv2,                "Error
       gs_outtab_lock  TYPE rprapa00_alv3,                "Locked PERNRs
       gs_outtab_apaccount TYPE rprapa00_alv3,            "APAccount
       gs_outtab_apac_without_pernr TYPE rprapa00_alv3,   "W/O PERNRs
       gs_outtab_log TYPE rprapa00_alv3,                  "Log
       gs_outtab_stats TYPE hrpad_pal_stats.              "Statistics

*ALV Output Tables
DATA : gt_outtab_file TYPE STANDARD TABLE OF ty_outtab_file,    "File
       gt_outtab_error TYPE STANDARD TABLE OF rprapa00_alv2,    "Error
       gt_outtab_lock TYPE STANDARD TABLE OF rprapa00_alv3,     "Locked
       gt_outtab_apaccount TYPE STANDARD TABLE OF rprapa00_alv3,"APAcnt
       gt_outtab_apac_without_pernr
                     TYPE STANDARD TABLE OF rprapa00_alv3,  "W/O PERNRs
       gt_outtab_log TYPE STANDARD TABLE OF rprapa00_alv3,     "Log
       gt_outtab_stats TYPE STANDARD TABLE OF hrpad_pal_stats. "Stats

DATA : gv_repid TYPE syrepid,      "Program name
       gv_file_header_1(78) TYPE c,"Top of list header 1 for File output
       gv_log_fail_message(100) TYPE c,   "Message for no entries in Log
       gv_table_msg(100) TYPE c,       "Message for no entries in Table
       gv_last_pagno TYPE sy-pagno,       "Last page No. in the list
       gv_common_error_header_written(1) TYPE c,
       gt_fieldcat TYPE slis_t_fieldcat_alv,"Field catalogue
       gs_layout TYPE slis_layout_alv,      "Layout
       gt_events TYPE slis_t_event,         "Events
       gs_print TYPE slis_print_alv.        "Print

*************** End ALV Coding C5056168 28/02/2005*****************