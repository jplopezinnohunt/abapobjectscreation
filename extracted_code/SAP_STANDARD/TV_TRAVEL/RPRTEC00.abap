* 6.06
* QKZ_austria_timefields AT timefields for deductions
* HOJ_CEE_PL             CEE_PL country version retrofit PL
* VRD_CEE_RU             CEE_RU country version retrofit RU
* 6.05
* QKZ_CEE_CZ_SK 20072009 CEE_CZ_SK country vrsion retrofit CZ SK
* 6.0
* MAWP7HK005319 10022006 RPRTEC00: Runtime Errors RAISE_EXCEPTION
*                        [note 923106]
* INSERTVJM14 Retrofit RAPS
* (5.0?)
* QIZSLNK000348 24032004 performance problem PLOGI COSTD = 'X' [721336]
* MZCELNK001010 16082004 BADI for temporary changing values T702N (PS)
* MZCELNK001103 25032004 Possib.choose trip or sep.alow. in sel. screen
* 2.0
* WKUALNK044326 20012003 country version for Italy
* 1.10
* ABSALNK008357 09112001 Recurrent Destinations (ABSBKK008357)
* XOWALNK008259 05112001 Country version Finland
* VJMPSTRG  Anpassungen an Trennungsgeld
* 4.6C
* WKUL9CK040045 05022001 select-option for trip number (FIN/TEC/DTA)
* WKUL9CK027009 19102000 Falsche Fehlermeld.56 357 ersetzt u. verbessert

* 4.6B
* WTLPH9SPAIN99 090999 Jahreswechsel Spanien

* 4.6A
* YEKAHRK049955 03291999 New enqueue logic
* XOWAHRK033175 11011999 D-maximum amount for receipts
* WTLAHRK024036 28091998 Country version Sweden
* XBHAHRK900038 14071998 country ver. norway: ABSBKK900038, ABSFEK900038

* 4.5B
* WKUPH4K031118 Berechtigungsprüfung hinter das Infotypenlesen verlegt
*               Berechtigungsprüfung mit zum Systemdatum gelesenen ITs
* WTLPH4K026332 151298 Switch in Sel-Screen added for acc only requests

* 4.5A
* XCIAHRK000674          calc. of overnight lumpsums with daily ded.
* QKZAHRK007494 23031998 Konstantenlesen von T511k auf T706_const umgest
* QVTAHRK007236 20031998 Customizing for public transportation receipts
* XFUAHRK001931          Fahrtkostenabrechnung BRKG
* VJMALRK064954          Verpflegungsabrechnung P.S. Germany
* XFUALRK064764          Include for PS subroutines appended
* KI4
* 4.6C
* VJMKI4PSFRIJ01  I.J. Frankreich
* XCIKI4PSFROV01 Reduktion Unterkunftpauschalen für P.S. Frankreich

* 4.5B
* VJMKI4PSME01   Branchenkennzeichen setzen
* VJMKI4PSVP04   inkongruente Intervalle Steuer/Erst in Verpf.abrech
* VJMKI4PSHWMY   Makros P.S. (HinzWerb über Memory)
*

*-------Travel Expenses Calculation------------------------------------*
*----------------------------------------------------------------------*
* Change history of ALV Development
* Program description: Settlement of Trip Data
* Author             :  Someswara Rao.Bommidi -- C5056176
* Start Date         :  07/02/2005
* End   Date         :  21/02/2005
* Changed Function/flow of the program :
*               REUSE_ALV_LIST_DISPLAY          for Simple List
*               REUSE_ALV_HIERSEQ_LIST_DISPLAY  for Hierarchial List
*               HR_PAL_LOG_DISPLAY              for Application Log
*----------------------------------------------------------------------*

REPORT rprtec00 MESSAGE-ID 56 LINE-SIZE 79
                NO STANDARD PAGE HEADING.

TABLES: pernr, pcl1, pme14.

DATA:   BEGIN OF COMMON PART buffer.
INCLUDE rpppxd10.
DATA:   END OF COMMON PART.

DATA: BEGIN OF COMMON PART infotypes.

INFOTYPES: 0001 OCCURS 2,              "Org. Zuordnung......
           0017 OCCURS 2.              "Daten zur Person....
DATA: END   OF COMMON PART.

DATA abaplist LIKE abaplist OCCURS 10 WITH HEADER LINE.

INFOTYPES: 0000 OCCURS 2,              "Massnahmen..........
           0002 OCCURS 2,              "Daten zur Person....
           0003 OCCURS 1,              "Payroll status......
           0003 NAME old-p0003 OCCURS 1 MODE n,
* QIZK000348 begin...
*          0008 occurs 2,              "Basisbezuege........
*          0027 occurs 2.              "Kostenverteilung....
           0008 OCCURS 2.              "Basisbezuege........

DATA p0027 TYPE p0027 OCCURS 10 WITH HEADER LINE.
* QIZK000348 end...

DATA: p0001_sydat LIKE p0001,                               "WKUK031118
      p0017_sydat LIKE p0017.                               "WKUK031118

TABLES rprxxxxx.                                            "WKUK040045

**************Start of ALV coding on 7 Feb 2005 --- C5056176 **********
TYPE-POOLS: p99sb, slis.
**** Period Table and Structure
DATA: gs_period TYPE rprpay00_alv3,
      gt_period TYPE STANDARD TABLE OF rprpay00_alv3,

**** Header Table and Structure
      gs_header TYPE rprtec00_alv1,
      gt_header TYPE STANDARD TABLE OF rprtec00_alv1,

**** Item table and Structure
      gs_errtxt TYPE rprtec00_alv2,
      gt_errtxt TYPE STANDARD TABLE OF rprtec00_alv2,

****Start of changes after WDF reviw on 5 Mar 2005 --- C5056176
**** Status Messages Table and structure
      gs_stats TYPE hrpad_pal_stats,
      gt_stats TYPE STANDARD TABLE OF hrpad_pal_stats.
****End of changes after WDF reviw on 5 Mar 2005 --- C5056176

**** Internal Table to caputre the Viewnames
DATA: BEGIN OF gt_test OCCURS 0,
        viewname(20) TYPE c,
      END OF gt_test,
      gs_test LIKE LINE OF gt_test.

DATA: BEGIN OF gt_ver OCCURS 0,
        vermessage(101) TYPE c,
        reinr TYPE reinr,
        pernr           TYPE persno,
      END OF gt_ver,
      gs_ver LIKE LINE OF gt_ver.

**** Global Variables
DATA: gv_repid TYPE sy-repid,                     "Report name
      gv_counter TYPE i VALUE 1,                  "Counter
      gt_list_top_of_page TYPE slis_t_listheader, "top of page table
      gv_reinr TYPE reinr,                        "Trip Number
      gv_text(60) TYPE c,                         "Text
      gv_count TYPE i VALUE 1,                    "Counter
      gr_grid TYPE REF TO cl_salv_form_layout_grid,  "ref to Grid
      gv_pernr_node_flag TYPE sap_bool VALUE space, "boolean value
      gv_pernr_node_key TYPE p99sb_s_node-node_key,  "node key
      gv_title(50) TYPE c,                           "Title
      gv_topofpage(30) TYPE c,                       "Top of page text
      gv_keyvalue(25) TYPE c,                        "Text Value
      gv_error(60) TYPE c,
      gv_pageno TYPE i VALUE 0.

TYPE-POOLS abap.                                            "MAWH1436239

**** Constatnts
CONSTANTS: gc_true   TYPE sap_bool VALUE 'X',  "flag for true
           gc_save   TYPE c  VALUE  'A',       "save option
           gc_append TYPE c VALUE 'Y',         "List append value
           gc_num2(2) TYPE c VALUE '01',
           gc_header TYPE dd02l-tabname VALUE 'RPRTEC00_ALV1',
           gc_item TYPE dd02l-tabname VALUE 'RPRTEC00_ALV2',
           gc_period TYPE dd02l-tabname VALUE 'RPRPAY00_ALV3',
           gc_stats  TYPE dd02l-tabname VALUE 'HRPAD_PAL_STATS',
           gc_usercommand    TYPE slis_formname VALUE 'USER_COMMAND',
                                                       "usercommand form
       gc_set_pf_status TYPE slis_formname VALUE 'SET_PF_STATUS',
                                                       "pf-status form
       gc_tabname_header TYPE dd02l-tabname VALUE 'GT_HEADER',
                                                       "header tablename
       gc_tabname_item   TYPE dd02l-tabname VALUE 'GT_ERRTXT',
                                                       "Item tablename
       gc_before_line_output     TYPE  slis_formname VALUE
                          'BEFORE_LINE_OUTPUT', "before line output form
       gc_top_of_page_1 TYPE slis_formname VALUE
                                    'TOP_OF_PAGE_1', "top of page form
       gc_top_of_page_2 TYPE slis_formname VALUE
                                    'TOP_OF_PAGE_2', "top of page form
       gc_top_of_page_3 TYPE slis_formname VALUE
                                    'TOP_OF_PAGE_3', "top of page form
       gc_end_of_list1  TYPE slis_formname VALUE
                                       'END_OF_LIST1',"end of list1 form
       gc_end_of_list2  TYPE slis_formname VALUE
                                       'END_OF_LIST2'."end of list2 form
*******End  of ALV coding on 7 Feb 2005 --- C5056176************

SELECTION-SCREEN BEGIN OF BLOCK 1 WITH FRAME TITLE text-y01.
*PARAMETERS:                                                "WKUK040045
*  REINR LIKE RPRXXXXX-REINR.                               "WKUK040045
SELECT-OPTIONS:                                             "WKUK040045
  s_reisen FOR rprxxxxx-reinr.                              "WKUK040045
SELECTION-SCREEN END OF BLOCK 1.

SELECTION-SCREEN BEGIN OF BLOCK 2 WITH FRAME TITLE text-y02.
PARAMETERS:
  testx    LIKE rprxxxxx-kr_feld4 USER-COMMAND testx.
* GLW note 2239883 begin
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN COMMENT 1(3) text-z25.
PARAMETER only_acc TYPE xfeld MODIF ID os.
SELECTION-SCREEN COMMENT 6(70) text-z24 FOR FIELD only_acc.
SELECTION-SCREEN END OF LINE.
* GLW note 2239883 end
* ALLE     LIKE RPRXXXXX-KR_FELD1,                          "WKUK027009
PARAMETER  alle     LIKE rprxxxxx-kr_feld1.                 "WKUK027009
SELECTION-SCREEN BEGIN OF BLOCK 3.                          "WKUK027009
PARAMETERS:                                                 "WKUK027009
  request  LIKE rprxxxxx-kr_feld16 DEFAULT 'X',             "WTLK026332
* TRIP     LIKE RPRXXXXX-KR_FELD17 DEFAULT 'X', "WTLK026332 "WKUK027009
  trip     LIKE rprxxxxx-kr_feld17 DEFAULT 'X',             "WKUK027009
  sa_incl  LIKE rprxxxxx-kr_feld6 DEFAULT 'X'            "MZCELNK001103
                                  MODIF ID msa.          "MZCELNK001103
SELECTION-SCREEN END OF BLOCK 3.                            "WKUK027009
PARAMETERS:                                                 "WKUK027009
  liste    LIKE rprxxxxx-kr_feld3,
  simulate LIKE rprxxxxx-kr_feld2 NO-DISPLAY.
* das Feld SIMULATE bzw. SIMULATION (später: simulation = simulate)
* dient folgendermaßen zur Steuerung:
*   = 'X' : Simulation einer einzelnen Reise
*   = '2' : Simulation mehrerer Reisen aus dem Reisekalender (PR02)
*   = 'V' : Simulation als Vergleichsrechnung für Öffentl. Dienst DE
*   = 'T' : Simulation für Vergleichsrechunung Tagegeld P.S. DE
*   = 'P' : Simulation von parallelen D.R.                   "VJMPSTRG00

SELECTION-SCREEN END OF BLOCK 2.
PARAMETERS: nolock NO-DISPLAY,                              "VJMPSTRG00
            l_to_mem TYPE xfeld NO-DISPLAY,                 "MAWK005319
            periodnr LIKE rprxxxxx-perio NO-DISPLAY.        "VJMPSTRG00
** Automatisches Anstarten und Ausdrucken des RPRPAY00 abgeklemmt
*selection-screen begin of block 3 with frame title text-y03.
*parameters:
*  chck_pay like rprxxxxx-kr_feld3 default ' '.
*selection-screen end of block 3.

*---------------------------------------------------------------------
*  Data - Definition
*---------------------------------------------------------------------
INCLUDE rpr_trip_enqueue_dequeue.                        "YEKAHRK049955
INCLUDE rprdt000.       " Tables   Travel Expenses T706*, *T706*
INCLUDE rprdt100.       " Tables   general (T005, T549Q,...)

INCLUDE rprde000.       " Data  general   (Helpfields  Calculation)

INCLUDE rprdeftt.       " TE-Transparent-Tables

DATA: BEGIN OF COMMON PART cluster_definition.
INCLUDE rprstr00.       " internal structures for TE-Transparent-Tables
INCLUDE rpc1te00.       " PCL1-Data  Travel Exp. DDIC Cluster TE
INCLUDE mp56tt99.       " PCL1-Data  User-table USER
DATA: END OF COMMON PART.
INCLUDE rpc1te00_ps_ki4.                             "VJMKI4PSHWMY
*

INCLUDE rprde100.                      " Data-Pool  Travel Exp. general
INCLUDE rprde100_ps.          " Data-Pool TE Public Sector / VJMK064954
INCLUDE rprde400.                      " Data-Pool  Verpflegung
INCLUDE rprno400.                      " Data defin. Norway ABSBKK900038
INCLUDE rprtrv00.                      " Lesen Merkmale

INCLUDE rprrd_dat.                     "Data def. Rec Dest ABSBKK008357

*---------------------------------------------------------------------*
*  Main routines                                                      *
*---------------------------------------------------------------------*
* Lesen des Verwaltungssatzes
INCLUDE rprpnppd.

INCLUDE rpracctt.                      " routines'fill T_perio / T_head'

********Start of ALV commenting  on 7 Feb 2005 --- C5056176 *******
*INCLUDE rprinn00.                      " Initialization
*INCLUDE rprmr000.                      " Mainroutines
*INCLUDE rprmr100.                      " Routines of calculation
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********

**********Start of ALV coding on 7 Feb 2005 --- C5056176 *********
INCLUDE rprinn00_alv.                      " Initialization
INCLUDE rprmr000_alv.                      " Mainroutines
INCLUDE rprmr100_alv.                      " Routines of calculation
**********End of ALV coding on 7 Feb 2005 --- C5056176 *********

INCLUDE rprmr100_os_fr_ki4.            "allg. Routinen VJMKI4PSFRIJ02
* INCLUDE RPRMR100_PS_FR_KI4.           "Name im KI4   VJMKI4PSFRIJ02
INCLUDE rprmr100_ps.                                        "VJMPSTRG00
INCLUDE rprmr100_ps_at.              "MZCK001010 = INSERTVJM14

INCLUDE rprmr200.                      " Import/Export TS and TE Cluster
****Start of changes after WDF review on 3 Mar 2005 --- C5056176
*INCLUDE rprvat00.                      " Value Added Tax
INCLUDE rprvat00_alv.                      " Value Added Tax
* HOJ_CEE_PL - Municipal Transport, Approaching Destination
INCLUDE glo_rprvat00_alv_pl.
* HOJ_CEE_PL
****end of changes after WDF review on 3 Mar 2005 --- C5056176
INCLUDE rprvat03_ps.                   " Österreich P.S.    "INSERTVJM14
INCLUDE rprvat02.                      " D-maximum amount    XOWK033175
INCLUDE rprvatno.                      " Taxation Norway    ABSFEK900038

*---------------------------------------------------------------------*
*  Subroutines                                                        *
*---------------------------------------------------------------------*
********Start of ALV commenting  on 7 Feb 2005 --- C5056176 *******
*INCLUDE rprsr000.                      " Unterroutinen Allgemein
**********End of ALV commenting on 7 Feb 2005 --- C5056176 *********
********Start of ALV coding  on 7 Feb 2005 --- C5056176 *******
INCLUDE rprsr000_alv.                      " Unterroutinen Allgemein
**********End of ALV coding on 7 Feb 2005 --- C5056176 *********

INCLUDE rprsr100.                      " Unterroutinen Fahrtkosten
INCLUDE rprsr10a.                      " Kilometerkumulation
INCLUDE rprsr10b.                      " Kilometerkumulation XFUK001931
INCLUDE rprsr10c_tec.                  " Kilometerkumulation XFUK001931
INCLUDE rprsr200.                      " Unterroutinen Belege
INCLUDE rprsr200_ps_de_ki4. "Unterrourinen Belegabrechnung Ö.D. QKZ
*
INCLUDE rprsr300.                      " Unterroutinen Unterkunft
* Unterkunftsabrechnung mit tageweise gekürzten Übernachtungen
INCLUDE rprsr330.                                           "XCIK000674
INCLUDE rprsr330_ps_de.                                     "XCIK065629
INCLUDE rprsr300_ps_de. " Pub. Sector Unterrout. Unterkunft "XCIK065629
INCLUDE rprsr330_ps_fr. " Rout. Unterkunft PS Frankreich XCIKI4PSFROV01
INCLUDE rprsr400_ps_ki4.                            "VJMKI4PSVP04
*
INCLUDE rprsr3no.       " Unterroutinen Unterkunft Norway ABSBKK900038
INCLUDE rprsr3es.       " Unterroutinen Unterkunft Spanien  "WTLSPAIN99
INCLUDE rprsr400.       " Unterroutinen Verpflegung allgemein
INCLUDE rprsr4a0.       " Unterroutinen Verpflegung Austria
INCLUDE rprsr4a0_ps_at. " Include for AT PS  MZCELNK001080 = INSERTVJM14
INCLUDE rprsr4d0.       " Unterroutinen Verpflegung Germany
INCLUDE rprsr4d0_ps_de.  " Verpflegung Germany Pub.Sec. / VJMK064954
INCLUDE rprsr4d0_ps_de_ki4. " Verpflegung Germany Pub.Sec./ VJMKI4PSAP01
INCLUDE rprsr4fr_ps_ki4. "Verpflegung/I.J. Frankreich PS. VJMKI4PSFRIJ01
*
INCLUDE rprsr4dk.       " Unterroutinen Verpflegung Denmark
INCLUDE rprsr4es.       " Unterroutinen Verpflegung Spanien
INCLUDE rprsr4fr.       " Unterroutinen Verpflegung Frankreich
INCLUDE rprsr4no.       " Unterroutinen Verpflegung Norway ABSBKK900038
INCLUDE rprsr4se.       " Unterroutinen Verpflegung Schweden WTLK024036
INCLUDE rprsr4fi.       " Unterroutinen Verpflegung Finnland XOWK008259
INCLUDE rprsr4it.       " Unterroutinen Verpflegung Italien  WKUK044326
INCLUDE rprsr4cz.       " Unterroutinen Verpflegung Tschechien QKZ_CEE_CZ_SK
INCLUDE rprsr4sk.       " Unterroutinen Verpflegung Slowakia   QKZ_CEE_CZ_SK
INCLUDE rprsr4at.       " Unterroutinen Verpfpflegung AT  QKZ_austria_timefields
INCLUDE glo_rprsr4ru.   " Unterroutinen Verpflegung Russia     VRD_CEE_RU
INCLUDE glo_rprsr4pl.   " Subroutines Meals Poland             HOJ_CEE_PL
INCLUDE rprrueck.       " Unterroutinen für Setzen des Rückrechnungskz.
INCLUDE rprallfo_ps_de. " Unterroutinen für Public Sector    XFUK064764
INCLUDE rprgenfo_ps_ki4.    "general Routines P.S.      "VJMKI4PSME01
INCLUDE rprsrhw1_ps_ki4.    "routines for hinz/werb     "XFUKI4PSHW01
INCLUDE rprsrhw2_ps_ki4.    "routines for hinz/werb     "XFUKI4PSHW01
*
INCLUDE rprgen00.       " programmübergreif. Unterroutinen XCIK000674
INCLUDE rprauth0.       " Berechtigungsprüfungen            "WKUK031118

INCLUDE rprrd_forms.                   "FORMs Recur Destin ABSBKK008357
*---------------------------------------------------------------------*
*  Helpprograms                                                       *
*---------------------------------------------------------------------*
********Start of ALV commenting  on 7 Feb 2005 --- C5056176 *******
*INCLUDE rprtb000.                      " READ  TABLES
**********End of ALV commenting on 7 Feb 2005 --- C5056176 *********
********Start of ALV coding  on 7 Feb 2005 --- C5056176 *******
INCLUDE rprtb000_alv.                      " READ  TABLES
**********End of ALV coding on 7 Feb 2005 --- C5056176 *********

INCLUDE rprtb000_ps.                   " READ  TABLES    VJMPSTRG00
INCLUDE rprtectef_ps_tg.                                    "VJMPSTRG00
INCLUDE rprgenfo_at.             "VJMKATVP   INSERTVJM14
INCLUDE mp56tf_t702g.           "Read properties of RAG "WKUK044326

*---------------------------------------------------------------------
*  READ TABLE T549B - Company specifications for Travel Expenses
*---------------------------------------------------------------------
INCLUDE rpumkc00.                      " Read table 549B/D

*---------------------------------------------------------------------
*  USER-EXITS: Read Tables 706*
*---------------------------------------------------------------------
INCLUDE rprex000.

TOP-OF-PAGE.
********Start of ALV commenting  on 7 Feb 2005 --- C5056176 *******
*  FORMAT COLOR 1 INTENSIFIED.
*  WRITE text-ue1 TO zeile CENTERED.                         "#EC *
*  WRITE sy-pagno TO zeile+56.
*
*  WRITE:/ zeile.
*  ULINE.
*  FORMAT RESET.
**********End of ALV commenting on 7 Feb 2005 --- C5056176 *********