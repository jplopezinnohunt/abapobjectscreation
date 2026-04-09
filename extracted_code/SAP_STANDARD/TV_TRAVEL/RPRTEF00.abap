* 6.06
* HOJ_CEE_PL    23072010 Polish Country Version Localization
* 6.0
* INSERTVJM14 / VJMKATVP   Retrofit RAPS
* AKAK011844    15122004 cproject integration
* 5.0
* MZCELNK001775 30082004 Long waiting time for program start
* SLGROSSVERGL  16082004 Einrichten Vergleichsrechnung
* MZCELNK001103 31032004 Possib.choose trip or sep.alow. in sel. screen
* QKWPLNK073352 02022004 Add'l fields f. header;400731 corr. incomplete
* 2.0
* HASP1HK006053          New BAdi FITV_REP_TRAVEL_EXP
* WKUALNK044326 20012003 country version for Italy
* QKWALNK040210 04122002 New user exit for form
* 1.10
* QKWALNK002031 07082001 Add'l fields for form header/minor errors
*                        Ref. Note 400731
* 4.6C
* WKUL9CK040045 05022001 select-option for trip number (FIN/TEC/DTA)
* WBGL9CK018580 03082000 Kopfzeilenaufbereitung see QIZ Note 322126;
* WBGL9CK015266 06072000 Kompaktformular - Prog.abbruch bei überlangen
*                        Namen; Kopfzeilenaufbereitung; Note 315533;

* 4.6A
* XOWPH9K004741 10051999 taxable benefit receipts
* YEKAHRK049955 03291999 New enqueue logic
* QJSAHRK047747 30031999 Korrektur Parameterfelder im RPRTEF00
* 4.5B
* WKUPH4K031118 Berechtigungsprüfung hinter das Infotypenlesen verlegt
*               Berechtigungsprüfung mit zum Systemdatum gelesenen ITs

*KI4
*4.5B
* KI4K035321/XFUKI4PSKM05  Bergeundungstext fuer KM mit privat KFZ
* KI4K034793/VJMKI4PSME01  Branchenkennzeichen setzen
* VJMKI4PSHWMY HinzWerb über Memory bei Simulation
*
*------ Travel Expenses standard form ---------------------------------*

REPORT rprtef00 MESSAGE-ID pn LINE-SIZE 78 LINE-COUNT 65
                                           NO STANDARD PAGE HEADING.
*{   INSERT         D01K999803                                        1
DATA zexit_UNESCO  TYPE REF TO ZIF_EX_TRIP_UNESCO.
*}   INSERT

TABLES: pernr, pcl1, pme14, ptp42.

DATA:   BEGIN OF COMMON PART buffer.

INCLUDE rpppxd10.
DATA:   END OF COMMON PART.

DATA: BEGIN OF COMMON PART infotypes.
INFOTYPES: 0001 OCCURS 2,              "Org. Zuordnung......
           0017 OCCURS 2.              "Daten zur Person....
DATA: END   OF COMMON PART.

Data begin of p0032_help occurs 2.                         "QKWK073352
  include structure p0032.                                 "QKWK073352
data end of p0032_help.                                    "QKWK073352

INFOTYPES: 0002 OCCURS 2,              "Daten zur Person....
           0006 OCCURS 2,              "Anschriften.........
* SLGROSSVERGL begin
*           0009 OCCURS 2.              "Bankverbindung     "QKWK002031
           0009 OCCURS 2,              "Bankverbindung     "QKWK002031
           0008 OCCURS 2.              "Basisbezüge
* SLGROSSVERGL end
*          0032 OCCURS 2.   "QKWK073352 Beriebsint. Daten  "QKWK002031

INCLUDE rprdeftt.                      "TE-Transparent Tables

DATA: BEGIN OF COMMON PART cluster_definition.
INCLUDE rprstr00.       " Internal structures for TE-Transparent-Tables
INCLUDE rpc1te00.       " PCL1-Data  Travel Exp. DDIC Cluster TE
INCLUDE mp56tt99.                      " PCL1-Data  User-Table USER
DATA: END OF COMMON PART.

DATA: p0001_sydat LIKE p0001,                               "WKUK031118
      p0017_sydat LIKE p0017.                               "WKUK031118

TABLES rprxxxxx.                                            "WKUK040045
DATA: frame_title_4(132).                                "MZCELNK001103

* block 1
SELECTION-SCREEN BEGIN OF BLOCK 1 WITH FRAME TITLE text-y01.
SELECT-OPTIONS:
* S_REISEN FOR PTP42-REINR.                                 "WKUK040045
  s_reisen FOR rprxxxxx-reinr.                              "WKUK040045
SELECTION-SCREEN END OF BLOCK 1.

* block 2
SELECTION-SCREEN BEGIN OF BLOCK 2 WITH FRAME TITLE text-y02.
PARAMETERS:
  hinz_dru LIKE rprxxxxx-hinz_dru RADIOBUTTON GROUP amnt,
  hinz_weg LIKE rprxxxxx-hinz_weg RADIOBUTTON GROUP amnt,
  hinz_dyn LIKE rprxxxxx-hinz_dyn RADIOBUTTON GROUP amnt DEFAULT 'X'.
SELECTION-SCREEN END OF BLOCK 2.

* block 4
* >> delete begin MZCELNK001103
*SELECTION-SCREEN BEGIN OF BLOCK 4 WITH FRAME TITLE text-y04.
*PARAMETERS:
*  wr_incl LIKE rprxxxxx-wr_incl RADIOBUTTON GROUP wr DEFAULT 'X',
*  wr_excl LIKE rprxxxxx-wr_excl RADIOBUTTON GROUP wr,
*  wr_only LIKE rprxxxxx-wr_only RADIOBUTTON GROUP wr.
* >> delete end MZCELNK001103
* << insert begin MZCELNK001103
*SELECTION-SCREEN BEGIN OF BLOCK 4 WITH FRAME TITLE frame_4."MZCK001775
SELECTION-SCREEN BEGIN OF BLOCK 4 WITH FRAME TITLE text-y05."MZCK001775
PARAMETERS:
  wr_excl LIKE rprxxxxx-wr_excl                             "MZCK001775
                  RADIOBUTTON GROUP wr, "MODIF ID mwr,      "MZCK001775
  wr_only LIKE rprxxxxx-wr_only
                  RADIOBUTTON GROUP wr,
  sa_only LIKE rprxxxxx-radio0                              "MZCK001775
                     RADIOBUTTON GROUP wr,                  "MZCK001775
  wr_incl LIKE rprxxxxx-wr_incl                             "MZCK001775
                  RADIOBUTTON GROUP wr DEFAULT 'X'.         "MZCK001775
* sa_incl LIKE rprxxxxx-radio0                              "MZCK001775
*                     RADIOBUTTON GROUP wr, MODIF ID msa,   "MZCK001775
* sa_excl LIKE rprxxxxx-radio1                              "MZCK001775
*                     RADIOBUTTON GROUP wr MODIF ID msa,    "MZCK001775
* sa_all LIKE rprxxxxx-radio2 DEFAULT 'X'                   "MZCK001775
*                     RADIOBUTTON GROUP wr MODIF ID msa.    "MZCK001775
* << insert end MZCELNK001103
SELECTION-SCREEN END OF BLOCK 4.

* block 3
SELECTION-SCREEN BEGIN OF BLOCK 3 WITH FRAME TITLE text-y03.
PARAMETERS:
  allesdru LIKE rprxxxxx-kr_feld1 DEFAULT ' ',
  reisepro LIKE rprxxxxx-kr_feld2 DEFAULT 'X',
  reisetxt LIKE rprxxxxx-kr_feld3 DEFAULT 'X' NO-DISPLAY,   "QJSK047747
  sw_antrg LIKE rprxxxxx-kr_feld5 DEFAULT ' ',
  addinfo  LIKE rprxxxxx-kr_feld4 DEFAULT 'X' NO-DISPLAY,   "QJSK047747
  kostzuor LIKE rprxxxxx-kr_feld6 DEFAULT 'X',
  einkopf  LIKE rprxxxxx-kr_feld7 DEFAULT ' ' NO-DISPLAY,
  simulate LIKE rprxxxxx-kr_feld2 NO-DISPLAY,
  extperio LIKE ptp42-perio       DEFAULT '000' NO-DISPLAY, "XCIPSDETRG
  sortline(50) NO-DISPLAY.

SELECTION-SCREEN SKIP 1.
SELECTION-SCREEN PUSHBUTTON /3(20) name USER-COMMAND sort.
SELECTION-SCREEN END OF BLOCK 3.

FIELD-GROUPS: header.                  "Datenextrakt

FIELD-SYMBOLS: <option_s>.             "Übergabefeld für Sortierung

*---------------------------------------------------------------------
*  Data - Definition
*---------------------------------------------------------------------
DATA: varia_trvct_b LIKE ptrv_trvct_b, "VJMTODO: nur
        varia_trvct_v LIKE ptrv_trvct_v,         "temporär hier dekla-
        varia_trvct_u LIKE ptrv_trvct_u,         "riert (19.3.98)
        varia_trvct_f LIKE ptrv_trvct_f,
        varia_trvct_r LIKE ptrv_trvct_r,
        varia_trvct_p LIKE ptrv_trvct_p,
        anz_lines TYPE i.
*data testmode.                         "WBGK015266;        "WBGK018580

INCLUDE rpr_trip_enqueue_dequeue.                        "YEKAHRK049955
INCLUDE rprdt000.                "Tables Travel Expenses T706*, *T706*
INCLUDE rprdt100.                      " Tables   general (T001,P...)
"T001 über HRCA_COMPANYCODE_GETDETAIL
DATA: BEGIN OF COMMON PART compact.
INCLUDE rprfd000.                      " Data-Pool Formular general
INCLUDE rprfd001.                      " Data-Pool Kompaktf.
INCLUDE rprde100.                      " Data-Pool Trav.Exp.
INCLUDE rprde100_ps_at.       "Data definition for PS AT "MZCELNK001103
INCLUDE rprde200.                      " Data-Pool Trav.Exp.
DATA: END OF COMMON PART.

INCLUDE rprde400.                      " Data-Pool  Verpflegung
INCLUDE rprdatps.                      " Data P.S.          "VJMK063330
*INSERTVJM14 BEG
INCLUDE rprdatps_at.          "P.S. Austria   INSERTVJM14/ VJMKATVP
*INSERTVJM14 END

INCLUDE rprdatps_ki4.                  "                 "VJMKI4PSAP01
INCLUDE rpc1te00_ps_ki4.               "Makros P.S.      "VJMKI4PSHWMY
*
INCLUDE <icon>.                        " Pushbutton-Icons

* HASK006053
* BAdi FITV_REP_TRAVEL_EXP
CLASS: cl_exithandler DEFINITION LOAD.
DATA: exit TYPE REF TO if_ex_fitv_rep_travel_exp.
*

*---------------------------------------------------------------------*
*  Main routines                                                      *
*---------------------------------------------------------------------*
* Lesen des Verwaltungssatzes
INCLUDE rprpnppd.

INCLUDE rpracctt.                      " routines'fill T_perio / T_head'
INCLUDE rprcust3.
INCLUDE rprcust0.                      "mk customizing routines
INCLUDE rprcust1.                      "mk customizing headlines
INCLUDE rprcust2.                      "mk customizing headlines

INCLUDE rprfmr00.                      " Mainroutine

*---------------------------------------------------------------------*
*  help routines                                                      *
*---------------------------------------------------------------------*
INCLUDE rprfs000.                      " Allgemein
INCLUDE rprfs100.                      " Fahrtkosten
* HOJ_CEE_PL - Municipal Transport, Approaching Destination
INCLUDE glo_rprfs100.
* HOJ_CEE_PL
INCLUDE rprfs200.                      " Belege
INCLUDE rprfs300.                      " Unterkunft
*{   REPLACE        D01K9A0004                                        2
*\INCLUDE rprfs400.                      " Verpflegung
INCLUDE rprfs400.                      " Verpflegung
*INCLUDE zrprfs400.                      " Verpflegung "test
*}   REPLACE
INCLUDE rprfs4es.                      " Verpfl. + Unterkunft Spanien
Include RPRFS400_CZ_SK. "QKW_CEE_CK_SK Meals accounting for Czech Rep.
INCLUDE glo_rprfs4pl.   " Subroutines Meals Poland          HOJ_CEE_PL
INCLUDE rprauth0.       " Berechtigungsprüfungen            "WKUK031118
INCLUDE rprgenfo_ps_ki4.     "general Routines P.S.      "VJMKI4PSME01
INCLUDE RPRGENFO_AT.         "common routines AT TEC/TEF  "INSERTVJM14
INCLUDE rprtef00_forms_ps_de_ki4. "TEF-routines for PS  "XFUKI4PSKM05
INCLUDE rprtectef_ps_ki4.   "common routines TEC/TEF    "VJMKI4PSVP02
INCLUDE rprtectef_ps_tg.                                    "VJMPSTRG00

INCLUDE MP56TF_T702G.           "Read properties of RAG "WKUK044326

*---------------------------------------------------------------------*
*  READ TABLE T549B - Company specifications for Travel Expenses      *
*---------------------------------------------------------------------*
INCLUDE rpumkc00.                      " Read table 549B/D
INCLUDE rprtrv00.                      "Lesen Merkmale

*---------------------------------------------------------------------*
*  USER-EXITS: Benutzerspez. Zusätze am Formularende                  *
*---------------------------------------------------------------------*
INCLUDE rprfex00.                      " Userexit
INCLUDE rprfex00_extension.                                 "QKWK040210
INCLUDE rprfs400_ps_de_ki4.
*

INCLUDE rprfs400_ps_fr_ki4.

INCLUDE rprfmr00_ps.

INCLUDE rprfs4it.                                           "WKUK044326

*INSERTVJM14 BEG
INCLUDE RPRFS400_PS_AT.                                       "VJMKATVP
*INSERTVJM14 END