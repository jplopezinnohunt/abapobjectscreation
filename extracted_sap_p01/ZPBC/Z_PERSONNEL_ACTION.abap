*&---------------------------------------------------------------------*
*& Report  Z_PERSONNEL_ACTION                                          *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  Z_PERSONNEL_ACTION LINE-SIZE 200.

*
* selection screen
*
SELECTION-SCREEN COMMENT 1(50) TEXT-001.
SELECTION-SCREEN SKIP.
SELECTION-SCREEN COMMENT 1(50) TEXT-002.
*selection-screen skip.

*
* Block main
SELECTION-SCREEN BEGIN OF BLOCK MAINPAR WITH FRAME TITLE TEXT-003.

* personnel number
*selection-screen begin of line.
*selection-screen comment 1(23) tpernr.
PARAMETERS:
  PPERNR  TYPE PA0003-PERNR MODIF ID CTI MATCHCODE OBJECT PREM.
*selection-screen end of line.

SELECTION-SCREEN SKIP.

* choose 'Action'
*selection-screen begin of line.
*selection-screen comment 1(23) tdoact.
PARAMETERS:
  PDOACT    RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) tact.
*parameters:
*  pact      type p0000-massn.
*selection-screen end of line.

* choose 'Action type'
*selection-screen begin of line.
*selection-screen comment 1(23) tdoactt.
PARAMETERS:
  PDOACTT   RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) tactt.
PARAMETERS:
  PACTT     TYPE P0000-MASSN.
*selection-screen comment 50(8) tactr.
PARAMETERS:
  PACTR     TYPE P0000-MASSG.
*selection-screen end of line.

* choose 'Mobility and hardship'
*selection-screen begin of line.
*selection-screen comment 1(23) tdomah.
PARAMETERS:
  PDOMAH    RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) tmah.
*parameters:
*  pmah      type p0000-massn.
*selection-screen end of line.

* choose 'Education grant'
*selection-screen begin of line.
*selection-screen comment 1(23) tdoedgr.
*parameters:
*  pdoedgr   radiobutton group rtyp.
*selection-screen comment 32(10) tedgr.
*parameters:
*  pedgr     type p0000-massn.
*selection-screen end of line.

* choose 'Rental subsity'
*selection-screen begin of line.
*selection-screen comment 1(23) tdoresu.
PARAMETERS:
  PDORESU   RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) tresu.
*parameters:
*  presu     type p0000-massn.
*selection-screen end of line.

* choose 'Health insurance'
*selection-screen begin of line.
*selection-screen comment 1(23) tdohein.
PARAMETERS:
  PDOHEIN   RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) thein.
*parameters:
*  phein     type p0000-massn.
*selection-screen end of line.

* choose 'Personal data'
*selection-screen begin of line.
*selection-screen comment 1(23) tdopeda.
PARAMETERS:
  PDOPEDA   RADIOBUTTON GROUP RTYP.
*selection-screen comment 32(10) tpeda.
*parameters:
*  ppeda     type p0000-massn.
*selection-screen end of line.

PARAMETERS:
  PDOCTTY   RADIOBUTTON GROUP RTYP.

* insert 24.08.2006
PARAMETERS:
  PDOEXTN   RADIOBUTTON GROUP RTYP.
* end insert 24.08.2006

SELECTION-SCREEN SKIP.

* selection date
*selection-screen begin of line.
*selection-screen comment 1(23) tsdate.
PARAMETERS:
  PSDATE  LIKE SY-DATUM DEFAULT SY-DATUM.
*selection-screen end of line.

SELECTION-SCREEN END OF BLOCK MAINPAR.



*
* Block output
SELECTION-SCREEN BEGIN OF BLOCK OUTPPAR WITH FRAME TITLE TEXT-004.

* file name and type
*selection-screen begin of line.
*selection-screen comment 1(23) tfname.
PARAMETERS:
  PFNAME  TYPE C  LENGTH 200 DEFAULT '\\hqfs\dfs\dit\mis\steps\paf\paf_t.dot' "'\\hqfs\dfs\dit\Public\Templates\Steps\pa_form.doc'
          VISIBLE LENGTH 50 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) tfpath1.
PARAMETERS:
  PFPATH  TYPE C LENGTH 200 DEFAULT 'C:\'
          VISIBLE LENGTH 50 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) tfpath2.
PARAMETERS:
  PFPATHA TYPE C LENGTH 200 DEFAULT ''
          VISIBLE LENGTH 50 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) tfprint.
PARAMETERS:
  PFPRINT AS CHECKBOX DEFAULT ' '.
*selection-screen end of line.

SELECTION-SCREEN END OF BLOCK OUTPPAR.


*
* Block remarks
SELECTION-SCREEN BEGIN OF BLOCK REMPAR WITH FRAME TITLE TEXT-005.

* remarks
*selection-screen begin of line.
*selection-screen comment 1(23) trem01.
PARAMETERS:
  PREM01  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem02.
PARAMETERS:
  PREM02  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem03.
PARAMETERS:
  PREM03  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem04.
PARAMETERS:
  PREM04  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem05.
PARAMETERS:
  PREM05  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem06.
PARAMETERS:
  PREM06  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) trem07.
PARAMETERS:
  PREM07  TYPE C  LENGTH 80 DEFAULT ''
          VISIBLE LENGTH 80 LOWER CASE.
*selection-screen end of line.

*selection-screen begin of line.
*selection-screen comment 1(23) tid.
PARAMETERS:
* changed 23.08.2006
*  pid     type c  length 30 default ''
  PID     TYPE C  LENGTH 30 DEFAULT SY-UNAME NO-DISPLAY "'D. Andros'
* end changed
          VISIBLE LENGTH 30 LOWER CASE.
*selection-screen end of line.

SELECTION-SCREEN END OF BLOCK REMPAR.

*
* Block utilities
SELECTION-SCREEN BEGIN OF BLOCK UTIPAR WITH FRAME TITLE TEXT-006.

* message level
*selection-screen begin of line.
*selection-screen comment 1(23) tmlevel.
PARAMETERS:
  PMLEVEL(1)  TYPE N DEFAULT 0. "4.
*selection-screen end of line.

SELECTION-SCREEN END OF BLOCK UTIPAR.




* called before selection screen is shown
INITIALIZATION.
* Definition tof texts move to text tabel because otherwise report
* transactions would not display the texts...
*  tpname    = '"Personnel Action"'.
*  tpvers    = 'release 1.xx'.
*  tmainpar  = 'Selection'.
*  tdoact    = 'By action'.
*  tdoactt   = 'By action type'.
*  tactt     = 'Type'.
*  tactr     = 'Reason'.
*  tdomah    = 'By mobility & hardship'.
*  tdoedgr   = 'By education grant'.
*  tdoresu   = 'By rental subsidy'.
*  tdohein   = 'By health insurance'.
*  tdopeda   = 'By personal data'.
*  tpernr    = 'Personal number'.
*  tsdate    = 'Selection date'.

*  toutppar  = 'Output'.
*  tfname    = 'Filename'.
*  tfpath1   = 'Path (data file)'.
*  tfpath2   = 'Path (server, for form)'.
*  tfprint   = 'Show values and print'.

*  trempar   = 'Remarks'.
*  trem01    = 'Line 1'.
*  trem02    = 'Line 2'.
*  trem03    = 'Line 3'.
*  trem04    = 'Line 4'.
*  trem05    = 'Line 5'.
*  trem06    = 'Line 6'.
*  trem07    = 'Line 7'.
*  tid       = 'Id.'.

*  tutipar   = 'Utilities'.
*  tmlevel   = 'Message level'.



AT SELECTION-SCREEN ON VALUE-REQUEST FOR PFNAME.
  DATA:
    F4_PATH  TYPE IBIPPARMS-PATH.

  CALL FUNCTION 'F4_FILENAME'
    EXPORTING
      PROGRAM_NAME  = SYST-REPID
      DYNPRO_NUMBER = SYST-DYNNR
      FIELD_NAME    = 'pfname'
    IMPORTING
      FILE_NAME     = F4_PATH.
  IF SY-SUBRC NE 0.
    WRITE: / 'Error during F4 for local file'.
  ELSE.
    PFNAME = F4_PATH.
  ENDIF.



* at execution of selection screen
START-OF-SELECTION.

  CONSTANTS:
    LC_HTAB TYPE STRING
            VALUE CL_ABAP_CHAR_UTILITIES=>HORIZONTAL_TAB,
    LC_VTAB TYPE STRING
            VALUE CL_ABAP_CHAR_UTILITIES=>VERTICAL_TAB,
    LC_NEWL TYPE STRING
            VALUE CL_ABAP_CHAR_UTILITIES=>NEWLINE,
    LC_CRLF TYPE STRING
            VALUE CL_ABAP_CHAR_UTILITIES=>CR_LF.

  TYPES:
    BEGIN OF DATALINE,
      F1      TYPE CHAR80,
      F2      TYPE CHAR80,
      F3      TYPE CHAR80,
      F4      TYPE CHAR80,
      F5      TYPE CHAR80,
      F6      TYPE CHAR80,
****I_KONAKOV - insert new field ROA - reason of action
      ROA     TYPE CHAR80,
      F7      TYPE CHAR80,
      F1F     TYPE CHAR50,
      F1T     TYPE CHAR50,
      F2F     TYPE CHAR50,
****I_KONAKOV - insert of a new field CDF - contract expiry date
      CDF     TYPE CHAR10,
      F2T     TYPE CHAR50,
****I_KONAKOV - insert of a new field CDT - contract expiry date
      CDT     TYPE CHAR10,
      F3F     TYPE CHAR50,
      F3T     TYPE CHAR50,
      F4F     TYPE CHAR30,
      F4T     TYPE CHAR30,
* insert 03.10.2006
*   WPF     type char30,
*   WPT     type char30,
* end insert 03.10.2006
* changed 23.08.2006
*   F5F     type char30,
*   F5T     type char30,
      F5F     TYPE CHAR50,
      F5T     TYPE CHAR50,
****I_KONAKOV - insert field
      F5P     TYPE CHAR5,  "string for 'P.M.'
*      bsl     type char200,
      F6F     TYPE CHAR30,
      F6T     TYPE CHAR30,
*   F7F     type char30,
*   F7T     type char30,
      F7F     TYPE CHAR50,
      F7T     TYPE CHAR50,
****I_KONAKOV - insert field
      F7P     TYPE CHAR5,  "string for 'P.M.'
* end changed 23.08.2006
      F8F     TYPE CHAR30,
      F8T     TYPE CHAR30,
****I_KONAKOV - insert field
      F8P     TYPE CHAR5,  "string for 'P.M.'
      F9F     TYPE CHAR30,
      F9T     TYPE CHAR30,
      TF      TYPE CHAR30,
      TT      TYPE CHAR30,
* insert 03.10.2006
      WPF     TYPE CHAR30,
      WPT     TYPE CHAR30,
      SAF     TYPE CHAR50,
      SAT     TYPE CHAR50,
      RSF     TYPE CHAR50,
      RST     TYPE CHAR50,
      EGF     TYPE CHAR50,
      EGT     TYPE CHAR50,
      IAF     TYPE CHAR50,
      IAT     TYPE CHAR50,
      LAF     TYPE CHAR50,
      LAT     TYPE CHAR50,
      SDF     TYPE CHAR50,
      SDT     TYPE CHAR50,
****I_KONAKOV - insert field
      SDP     TYPE CHAR5,  "string for 'P.M.'
* end insert 03.10.2006
      UF      TYPE CHAR40,
      UT      TYPE CHAR40,
* changed 23.08.2006
*   VF      type char40,
*   VT      type char40,
      VF      TYPE CHAR70,
      VT      TYPE CHAR70,
* end changed 23.08.2006
      WF      TYPE CHAR40,
      WT      TYPE CHAR40,
      XF      TYPE CHAR50,
      XT      TYPE CHAR50,
      YF      TYPE CHAR50,
      YT      TYPE CHAR50,
      ZF      TYPE CHAR50,
      ZT      TYPE CHAR50,
****I_KONAKOV - insert field R0 for string "Remarks:"
      R0      TYPE CHAR100,
      R1      TYPE CHAR100,
      R2      TYPE CHAR100,
      R3      TYPE CHAR100,
      R4      TYPE CHAR100,
      R5      TYPE CHAR100,
      R6      TYPE CHAR100,
      R7      TYPE CHAR100,
      FD      TYPE CHAR30,
      FI      TYPE CHAR30,
      P1F     TYPE CHAR100,
      Q1F     TYPE CHAR100,
      P1T     TYPE CHAR100,
      Q1T     TYPE CHAR100,
****I_KONAKOV - insert of a new fields
      PFN     TYPE CHAR20, "UNPF no
      GSF     TYPE CHAR50, "Gross base salary "From"
      GST     TYPE CHAR50, "Gross base salary "To"
      GSP     TYPE CHAR5,  "string for 'P.M.'
*      gsl     type char200,  "string for GBAS
      CAF     TYPE CHAR50, "Family allowance - children "From"
      CAT     TYPE CHAR50, "Family allowance - children "To"
      CAP     TYPE CHAR5,  "string for 'P.M.'
      RNF     TYPE CHAR50, "Rental subsidy "From"
      RNT     TYPE CHAR50, "Rental subsidy "To"
      RNP     TYPE CHAR5,  "string for 'P.M.'
      SPF     TYPE CHAR50, "Family allowance - spouse "From"
      SPT     TYPE CHAR50, "Family allowance - spouse "To"
      SPP     TYPE CHAR5,  "string for 'P.M.'
      PCF     TYPE CHAR50, "Pension contribution "From"
      PCT     TYPE CHAR50, "Pension contribution "To"
      PCP     TYPE CHAR5,  "string for 'P.M.'
      MFF     TYPE CHAR50, "MBF contribution "From"
      MFT     TYPE CHAR50, "MBF contribution "To"
      MFP     TYPE CHAR5,  "string for 'P.M.'
      OSF     TYPE CHAR50, "Other source allowance "From"
      OST     TYPE CHAR50, "Other source allowance "To"
      OSP     TYPE CHAR5,  "string for 'P.M.'
      NRF     TYPE CHAR50, "Not resident's allowance "From"
      NRT     TYPE CHAR50, "Not resident's allowance "To"
      NRP     TYPE CHAR5,  "string for 'P.M.'
      SLF     TYPE CHAR50, "Second lang. allowance "From"
      SLT     TYPE CHAR50, "Second lang. allowance "To"
      SLP     TYPE CHAR5,  "string for 'P.M.'
      SEF     TYPE CHAR50, "Service allowance "From"
      SET     TYPE CHAR50, "Service allowance "To"
      SEP     TYPE CHAR5,  "string for 'P.M.'
      FMF     TYPE CHAR50, "Family allowance "From"
      FMT     TYPE CHAR50, "Family allowance "To"
      FMP     TYPE CHAR5,  "string for 'P.M.'
      RPF     TYPE CHAR50, "Representation allowance "From"
      RPT     TYPE CHAR50, "Representation allowance "To"
      RPP     TYPE CHAR5,  "string for 'P.M.'
      TRF     TYPE CHAR50, "Transportation allowance "From"
      TRT     TYPE CHAR50, "Transportation allowance "To"
      TRP     TYPE CHAR5,  "string for 'P.M.'
      SNF     TYPE CHAR50, "Spec. non-pens. allowance "From"
      SNT     TYPE CHAR50, "Spec. non-pens. allowance "To"
      SNP     TYPE CHAR5,  "string for 'P.M.'
      PTF     TYPE CHAR50, "Personal transitional allowance "From"
      PTT     TYPE CHAR50, "Personal transitional allowance "To"
      PTP     TYPE CHAR5,  "string for 'P.M.'
      AGF     TYPE CHAR50, "Assignment grant (DSA) "From"
      AGT     TYPE CHAR50, "Assignment grant (DSA) "To"
      AGP     TYPE CHAR5,  "string for 'P.M.'
      ALF     TYPE CHAR50, "Assignment grant (lump sum) "From"
      ALT     TYPE CHAR50, "Assignment grant (lump sum) "To"
      ALP     TYPE CHAR5,  "string for 'P.M.'
      RGF     TYPE CHAR50, "Repatriation grant "From"
      RGT     TYPE CHAR50, "Repatriation grant "To"
      RGP     TYPE CHAR5,  "string for 'P.M.'
      TMF     TYPE CHAR50, "Termination indemnity "From"
      TMT     TYPE CHAR50, "Termination indemnity "To"
      TMP     TYPE CHAR5,  "string for 'P.M.'
      DGF     TYPE CHAR50, "Death grant "From"
      DGT     TYPE CHAR50, "Death grant "To"
      DGP     TYPE CHAR5,  "string for 'P.M.'
      ILF     TYPE CHAR50, "In lieu of notice "From"
      ILT     TYPE CHAR50, "In lieu of notice "To"
      ILP     TYPE CHAR5,  "string for 'P.M.'
      ANF     TYPE CHAR50, "Annual leave statement "From"
      ANT     TYPE CHAR50, "Annual leave statment "To"
      ANP     TYPE CHAR5,  "string for 'P.M.'
      HDF     TYPE CHAR50, "Hairdressing indemnity "From"
      HDT     TYPE CHAR50, "Hairdressing indemnity "To"
      HDP     TYPE CHAR5,  "string for 'P.M.'
      CLF     TYPE CHAR50, "Closing allowance "From"
      CLT     TYPE CHAR50, "Closing allowance "To"
      CLP     TYPE CHAR5,  "string for 'P.M.'
      PAF     TYPE CHAR50, "Spec. post allowance "From"
      PAT     TYPE CHAR50, "Spec. post allowance "To"
      PAP     TYPE CHAR5,  "string for 'P.M.'
      DHF     TYPE CHAR50, "Deduction for housing provided "From"
      DHT     TYPE CHAR50, "Deduction for housing provided "To"
      DHP     TYPE CHAR5,  "string for 'P.M.'
      SSF     TYPE CHAR50, "Social security "From"
      SST     TYPE CHAR50, "Social security "To"
      SSP     TYPE CHAR5,  "string for 'P.M.'
      LLF     TYPE CHAR50, "Lloyd insurance "From"
      LLT     TYPE CHAR50, "Lloyd insurance "To"
      LLP     TYPE CHAR5,  "string for 'P.M.'
      BDA     TYPE CHAR10, "Birthdate
      IMA     TYPE CHAR80, "internal mailing address
      UDF     TYPE CHAR10, "UNESCO entry date "From"
      UDT     TYPE CHAR10, "UNESCO entry date "To"
      UNF     TYPE CHAR10, "UN entry date "From"
      UNT     TYPE CHAR10, "UN entry date "To"
      DSF     TYPE CHAR50, "Duty station "From"
      DST     TYPE CHAR50, "Duty station "To"
      ADF     TYPE CHAR50, "Adm. duty station "From"
      ADT     TYPE CHAR50, "Adm. duty station "To"
      OUF     TYPE CHAR50, "Org. unit "From"
      OUT     TYPE CHAR50, "Org. unit "To"
      PNF     TYPE CHAR25, "Post number "From"
      PNT     TYPE CHAR25, "Post number "To"
      AT1     TYPE CHAR200,"Automatic text
      AT2     TYPE CHAR200,"Automatic text
      AT3     TYPE CHAR200,"Automatic text
      AT4     TYPE CHAR200,"Automatic text
      PDN     TYPE CHAR25, "PAF document number
      PDR     TYPE CHAR10, "PAF document revision
****I_KONAKOV - end of insert
    END OF DATALINE.

* HR data
  DATA:
    PA0000        TYPE PA0000,
    PA0001        TYPE PA0001,
    PA0002        TYPE PA0002,
    PA0003        TYPE PA0003,
    PA0006        TYPE PA0006,
    PA0007        TYPE PA0007,
    PA0008        TYPE PA0008,
    PA0009        TYPE PA0009,
    PA0011        TYPE PA0011,
    PA0012        TYPE PA0012,
    PA0013        TYPE PA0013,
    PA0014        TYPE PA0014,
    PA0015        TYPE PA0015,
    PA0016        TYPE PA0016,
    PA0017        TYPE PA0017,
    PA0019        TYPE PA0019,
    PA0021        TYPE PA0021,
    PA0022        TYPE PA0022,
    PA0023        TYPE PA0023,
    PA0024        TYPE PA0024,
    PA0025        TYPE PA0025,
    PA0027        TYPE PA0027,
    PA0028        TYPE PA0028,
    PA0030        TYPE PA0030,
    PA0031        TYPE PA0031,
    PA0032        TYPE PA0032,
    PA0033        TYPE PA0033,
    PA0034        TYPE PA0034,
    PA0035        TYPE PA0035,
    PA0037        TYPE PA0037,
    PA0040        TYPE PA0040,
    PA0041        TYPE PA0041,
    PA0045        TYPE PA0045,
    PA0050        TYPE PA0050,
    PA0054        TYPE PA0054,
    PA0057        TYPE PA0057,
    PA0077        TYPE PA0077,
    PA0078        TYPE PA0078,
    PA0080        TYPE PA0080,
    PA0081        TYPE PA0081,
    PA0082        TYPE PA0082,
    PA0083        TYPE PA0083,
    PA0094        TYPE PA0094,
    PA0105        TYPE PA0105,
    PA0165        TYPE PA0165,
    PA0167        TYPE PA0167,
    PA0168        TYPE PA0168,
    PA0169        TYPE PA0169,
    PA0171        TYPE PA0171,
    PA0185        TYPE PA0185,
    PA0262        TYPE PA0262,
    PA0278        TYPE PA0278,
    PA0279        TYPE PA0279,
    PA0302        TYPE PA0302,
    PA0304        TYPE PA0304,
    PA0351        TYPE PA0351,
    PA0374        TYPE PA0374,
    PA0376        TYPE PA0376,
    PA0377        TYPE PA0377,
    PA0378        TYPE PA0378,
    PA0416        TYPE PA0416,
    PA0487        TYPE PA0487,
    PA0509        TYPE PA0509,
    PA0703        TYPE PA0703,
    PA0704        TYPE PA0704,
    PA0710        TYPE PA0710,
    PA0712        TYPE PA0712,
    PA0715        TYPE PA0715,
    PA0959        TYPE PA0959,
    PA0960        TYPE PA0960,
****I_KONAKOV - insert for IT0961
    PA0961        TYPE PA0961,
    PA0962        TYPE PA0962,
    PA2001        TYPE PA2001,
    PA2003        TYPE PA2003,
    PA2006        TYPE PA2006,
    PA2010        TYPE PA2010,
    PA2013        TYPE PA2013.
***  pa9001        type pa9001,
****  pa9002        type pa9002,
***  pa9278        type pa9278,
***  pa9600        type pa9600,
***  pa9601        type pa9601,
***  pa9602        type pa9602,
****  pa9605        type pa9605,
***  pa9620        type pa9620,
***  pa9685        type pa9685.


  TYPES:
    BEGIN OF TBENTRY,
      ID   TYPE STRING,
      WT   TYPE LGART,
      BTB  TYPE MAXBT,
      BTA  TYPE MAXBT,
      CUB  TYPE WAERS,
      CUA  TYPE WAERS,
    END OF TBENTRY.

  FIELD-SYMBOLS:
    <GTHISINFTY>       TYPE  ANY,
    <GPREVINFTY>       TYPE  ANY.

  DATA:
    DEBUGLEVEL(1)      TYPE  N       VALUE 0,
    TMPS               TYPE  STRING,
    TMPS2              TYPE  STRING,
    CPISINIT(1)        TYPE  C VALUE SPACE,
    TABNAME            TYPE  STRING,
    TABNAMES           TYPE  TABLE OF STRING,
    TABNAMESA          TYPE  TABLE OF STRING,
    CUSTTABLE          TYPE  STRING  VALUE 'ZUNES_ATTR',
    OVRPERNR           TYPE  PERNR-PERNR VALUE 0,
    DELETEPERSON(1)    TYPE  C       VALUE 'X',
    DISPPRLOG(1)       TYPE  C       VALUE ' ',
    DOPERMANENT(1)     TYPE  C       VALUE ' ',
    SALPERIODB         TYPE  I       VALUE 12,
    SALPERIODA         TYPE  I       VALUE 12,
    MOLGA              TYPE  MOLGA   VALUE 'UN',
    PLVAR              TYPE  P1000-PLVAR    VALUE '01',
    TRFKZ              TYPE  T503-TRFKZ,
    THISPERIOD         TYPE  FAPER,
    PREVPERIOD         TYPE  FAPER,
    BENTRIES           TYPE  TABLE OF TBENTRY,
    BENTRY             TYPE  TBENTRY,
    CONTPHOME          TYPE  STRING  VALUE 'HOME', "I_KONAKOV - value changed from '0001',
    GENAFROM(1)        TYPE  C VALUE 'X',
    GENATO(1)          TYPE  C VALUE 'X',
    DISPBLINES         TYPE  TABLE OF STRING,
    FROMDATE           TYPE  D,
    EFFECTIVEDATE      TYPE  D,
    FIRE_DATE          TYPE  D,
    HIRE_DATE          TYPE  D,

* insert 14.09.2006
    EMPCTA     TYPE EMPCT,
    EMPCTB     TYPE EMPCT,
    L_SBMOD    TYPE SBMOD,
    PA_ADMIN   TYPE SACHN,
* end insert 14.09.2006
* insert 24.08.2006
    RATEA      TYPE STRING,
    RATEB      TYPE STRING,
    HIDCSHAREA TYPE P,
    HIDCSHAREB TYPE P,
    HIDCFULLA  TYPE P,
    HIDCFULLB  TYPE P,
    HIDSSHAREA TYPE P,
    HIDSSHAREB TYPE P,
    HIDSFULLA  TYPE P,
    HIDSFULLB  TYPE P,
* end insert 24.08.2006
    PLANSB TYPE PLANS,
    PLANSA TYPE PLANS,
    ORGEHB TYPE ORGEH,
    ORGEHA TYPE ORGEH,
    WERKSB TYPE PERSA,
    WERKSA TYPE PERSA,
    BTRTLB TYPE BTRTL,
    BTRTLA TYPE BTRTL,
    NATIOB TYPE NATIO,
    NATIOA TYPE NATIO,
    CTTYPB TYPE CTTYP,
    CTTYPA TYPE CTTYP,
***  zzpyfb type zzpyfreq,
***  zzpyfa type zzpyfreq,
    DEPCVB TYPE BEN_DEPCOV,
    DEPCVA TYPE BEN_DEPCOV,
    BOPTIB TYPE BEN_OPTION,
    BOPTIA TYPE BEN_OPTION,
    BEGDAB TYPE BEGDA,
    BEGDAA TYPE BEGDA,
    CTEDTB TYPE CTEDT,
    CTEDTA TYPE CTEDT,
    TRFGRB TYPE TRFGR,
    TRFGRA TYPE TRFGR,
    TRFSTB TYPE TRFST,
    TRFSTA TYPE TRFST,
    STVORB TYPE STVOR,
    STVORA TYPE STVOR,
    KOSTLB TYPE KOSTL,
    KOSTLA TYPE KOSTL,
    PERSGB TYPE PERSG,
    PERSGA TYPE PERSG,
    PERSKB TYPE PERSK,
    PERSKA TYPE PERSK,
    HOMESTATION TYPE STRING,
****I_KONAKOV - variable for 'P.M.' string in a separate field
    W_PMPA(4),
    W_LINE(200).

* insert 14.09.2006
  TABLES: PME17.
* end insert 14.09.2006


*
* Start of processing
*

* Init
  IF PMLEVEL = 9.
    PMLEVEL = 0.
    CLEAR DELETEPERSON.
    WRITE: / 'Temporary persons will not be deleted!'.
  ENDIF.
  IF PMLEVEL = 8.
    PMLEVEL = 0.
    DISPPRLOG = 'X'.
    WRITE: / 'Displaying Payroll Logs!'.
  ENDIF.
  IF PMLEVEL >  0.
    DEBUGLEVEL = PMLEVEL.
  ENDIF.

  CLASS CL_ABAP_CHAR_UTILITIES DEFINITION LOAD.

* set country (controlling date and numeric formats
  DATA:
    CURRCOUNTRY(3)  TYPE C.
  PERFORM GETATTRIBUTE USING 'COUNTRY' 'GB ' CHANGING TMPS.
  CURRCOUNTRY = TMPS.

*
* Special processing for online customizing changes
*
****I_KONAKOV - block commented
***  if prem01 is initial and prem02 is initial and not prem03 is initial.
***    if strlen( prem03 ) > 2.
***      if prem03(3) = '***'.
***        data:
***          custline  type string,
***          attr      type zunes_attr,
***          tsize     type i.
***
***        write: / 'Special mode: Customizing settings'.
***        split prem03+3 at ':' into attr-aname attr-avalue.
***        modify (custtable) from attr.
***        write: / 'Set/changed attribute', attr-aname no-gap,
***          'to', attr-avalue no-gap,
***          'Result:', sy-subrc, '/', sy-dbcnt.
***        return.
***      endif.
***      if prem03(3) = '**D'.
***        write: / 'Special mode: Customizing delete'.
***        move prem03+3 to attr-aname.
***        delete from (custtable)
***          where aname = attr-aname.
***        write: / sy-subrc, sy-dbcnt.
***        commit work.
***        return.
***      endif.
***      if prem03(3) = '**L'.
***        write: / 'Special mode: Customizing list'.
***        select * from (custtable) into attr.
***          write: / attr-aname, attr-avalue.
***        endselect.
***        return.
***      endif.
***      if prem03(3) = '**I'.
***        write: / 'Special mode: wage types init'.
***        perform initwagetypes.
***        return.
***      endif.
***      if prem03(3) = '**W'.
***        write: / 'Special mode: wage types list'.
***        perform getwagetypeattributes using 1.
***        return.
***      endif.
***      if prem03(3) = '*DD'.
***        write: / 'Special mode: Customizing delete all'.
***        delete from (custtable).
***        commit work.
***        return.
***      endif.
***      if prem03(3) = '**A'.
***        data: dspa type t7unpad_dspa.
***        write: / 'Special mode: Customizing DSPA'.
***        select single * from t7unpad_dspa into dspa
***          where molga = 'UN'
***            and dstat = '0060'
***            and trfkz = '3'
***            and eentl = '99991231'
***            and endda = '99991231'.
***        write: / sy-subrc, sy-dbcnt.
***        dspa-begda = '20050101'.
***        modify t7unpad_dspa from dspa.
***        write: / sy-subrc, sy-dbcnt.
***        return.
***      endif.
***      if prem03(3) = '**R'.
***        data:  removepernr  type  pernr-pernr.
***        perform getattribute using 'TP_FROM' '99990000' changing tmps.
***        removepernr = tmps.
***        write: / 'Special mode: Removing temporary person:',
***          removepernr.
***        debuglevel = 1.
***        if not removepernr is initial.
***          perform deleteperson
***            using removepernr 'X' 'X'.
***        endif.
***        return.
***      endif.
***      if prem03(3) = '**S'.
***        perform initcp.
***        try.
***            tabname = prem03+3.
***            if ppernr is initial.
***              select count(*) from (tabname) into tsize.
***              write: / 'Size of table', tabname, ':', tsize,
***                'records'.
***            else.
***              select count(*) from (tabname) into tsize
***                where pernr = ppernr.
***              write: / 'Size of table', tabname, 'for', ppernr, ':', tsize,
***                'records'.
***            endif.
***          catch cx_root.
***            write: / 'Exception'.
***        endtry.
***        return.
***      endif.
***
***      if   prem03(3) = '*SS'
***        or prem03(3) = '*SP'.
***        data:
***          wa_tadir  like tadir.
***
***        perform initcp.
***        tabname = prem03+3.
***        select * from tadir into wa_tadir
***          where object = 'TABL'
***            and obj_name like tabname.
***          try.
***              if ppernr is initial.
***                select count(*) from (wa_tadir-obj_name) into tsize.
***                write: / 'Size of table', wa_tadir-obj_name,
***                  ':', tsize, 'records'.
***              else.
***                select count(*) from (wa_tadir-obj_name) into tsize
***                  where pernr = ppernr.
***                write: / 'Size of table', wa_tadir-obj_name,
***                  'for', ppernr, ':', tsize, 'records'.
***              endif.
***            catch cx_root.
***              write: / 'Exception:', wa_tadir-obj_name.
***          endtry.
***          if ( tsize > 0 ) and ( prem03(3) = '*SP' ).
***            read table tabnames transporting no fields
***              with key table_line = wa_tadir-obj_name.
***            if sy-subrc <> 0.
***              write: / 'Not in tabnames:', wa_tadir-obj_name, '!'.
***            endif.
***          endif.
***        endselect.
***        return.
***      endif.
***      if prem03(3) = '**-'.
***        data:
***          cmd(100)  type c.
***
***        cmd = prem03+3.
***        if cmd(9) = 'PERMANENT'.
***          write: / 'Temporary person left unchanged and permanent'.
***          dopermanent = 'X'.
***          ovrpernr = cmd+9(8).
***          if not ovrpernr is initial.
***            if ovrpernr > '99990000'.
***              write: / 'Temporary pernr set to ', ovrpernr.
***            endif.
***          endif.
***        endif.
***      endif.
***    endif.
***  endif.
****I_KONAKOV - end of commented block

  FORMAT COLOR COL_HEADING.
  WRITE: / 'Personnel Action report'.
  IF PPERNR IS INITIAL.
    FORMAT COLOR COL_NEGATIVE.
    WRITE: / 'Personnel number not specified!'.
    FORMAT COLOR COL_NORMAL.
    RETURN.
  ENDIF.
  ULINE.
  SKIP.
  FORMAT COLOR COL_NORMAL.

  PERFORM GETCUSTOMIZING.
  PERFORM DOPROCESSING USING PPERNR.

*
* End of main program
*



*
* get customizing from table
*
FORM GETCUSTOMIZING.
  DATA:
    ANAME  TYPE STRING,
    AVALUE TYPE STRING.

  LOOP AT BENTRIES INTO BENTRY.
    CONCATENATE 'WT_' BENTRY-ID INTO ANAME.
    AVALUE = BENTRY-WT.
    PERFORM GETATTRIBUTE USING ANAME AVALUE CHANGING TMPS.
    BENTRY-WT = TMPS.
    IF DEBUGLEVEL > 2.
      WRITE: / 'WT:', BENTRY-ID, BENTRY-WT, '*'.
    ENDIF.
    MODIFY BENTRIES FROM BENTRY.
  ENDLOOP.
  PERFORM GETWAGETYPEATTRIBUTES USING 0.

  PERFORM GETATTRIBUTE USING 'CONTPHOME' '0001'
    CHANGING CONTPHOME.
ENDFORM.                    "getCustomizing



*
* Get a named attribute from storage
*
FORM GETATTRIBUTE
  USING
    VALUE(ANAME)   TYPE STRING
    VALUE(DEFVAL)  TYPE STRING
  CHANGING
    AVALUE  TYPE STRING.

  CLEAR AVALUE.
  SELECT SINGLE AVALUE FROM (CUSTTABLE) INTO AVALUE
    WHERE ANAME = ANAME.
  IF SY-SUBRC <> 0.
    AVALUE = DEFVAL.
    IF 1 = 0.
      DATA:
        ATTR   TYPE ZUNES_ATTR.

      ATTR-ANAME  = ANAME.
      ATTR-AVALUE = DEFVAL.
      INSERT (CUSTTABLE) FROM ATTR.
    ENDIF.
  ENDIF.
ENDFORM.                    "getAttribute



*
* Init wage types into customizing
*
FORM INITWAGETYPES.
  REFRESH BENTRIES.

  DATA:
    ANAME     TYPE STRING,
    AVALUE    TYPE STRING,
    BENTRY    TYPE TBENTRY.

  BENTRY-ID = 'BASE'.
  BENTRY-WT = '0032'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'BASE2'.
  BENTRY-WT = '1490'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'BASE3'.
  BENTRY-WT = '0132'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'BASE4'.
  BENTRY-WT = '0133'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'BASE5'.
  BENTRY-WT = '0134'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'BASE6'.
  BENTRY-WT = '0036'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'SNET'.
  BENTRY-WT = '0032'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'POST'.
  BENTRY-WT = '0050'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'POST2'.
  BENTRY-WT = '0152'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'POST3'.
  BENTRY-WT = '0153'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'POST4'.
  BENTRY-WT = '0154'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'POST5'.
  BENTRY-WT = '0151'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'PENS'.
  BENTRY-WT = '0080'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'PENS2'.
  BENTRY-WT = '0182'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'PENS3'.
  BENTRY-WT = '0183'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'PENS4'.
  BENTRY-WT = '0184'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'MHAL'.
  BENTRY-WT = '0300'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'MHAL2'.
  BENTRY-WT = '0310'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'MHAL3'.
  BENTRY-WT = '0320'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'CHAL'.
  BENTRY-WT = '0230'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'SPAL'.
  BENTRY-WT = '0210'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'DPAL'.
  BENTRY-WT = '0250'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'DPAL2'.
  BENTRY-WT = '0260'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'LAAL'.
  BENTRY-WT = '0270'.
  APPEND BENTRY TO BENTRIES.
* insert 14.09.2006
  BENTRY-ID = 'LAAL2'.
  BENTRY-WT = '0280'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'HDAL'.
  BENTRY-WT = '0106'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'EDUC'.
  BENTRY-WT = '1250'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'RSAL'.
  BENTRY-WT = '0410'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'SALW'.
  BENTRY-WT = '0370'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'SALW2'.
  BENTRY-WT = '0375'.
  APPEND BENTRY TO BENTRIES.
* end insert 14.09.2006
  BENTRY-ID = 'PRFU'.
  BENTRY-WT = '5650'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'PRFU2'.
  BENTRY-WT = '5651'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'ACIL'.
  BENTRY-WT = '1900'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'HISE'.
  BENTRY-WT = '1800'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'HISE2'.
  BENTRY-WT = '1820'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'HIDE'.
  BENTRY-WT = '1810'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'HIDE2'.
  BENTRY-WT = '1830'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'AGLS'.
  BENTRY-WT = '1260'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'AGLS2'.
  BENTRY-WT = '1265'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'AGLS3'.
  BENTRY-WT = '1270'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'AGLS4'.
  BENTRY-WT = '1275'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'RESU'.
  BENTRY-WT = 'M410'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'DSCP'.
  BENTRY-WT = '1918'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'DMSP'.
  BENTRY-WT = '1828'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'DMSP2'.
  BENTRY-WT = '1838'.
  APPEND BENTRY TO BENTRIES.
  BENTRY-ID = 'ANLP'.
  BENTRY-WT = '1600'.
  APPEND BENTRY TO BENTRIES.

  LOOP AT BENTRIES INTO BENTRY.
    ANAME  = BENTRY-ID.
    AVALUE = BENTRY-WT.
    CONCATENATE 'WT_' ANAME INTO ANAME.
    PERFORM GETATTRIBUTE
      USING ANAME AVALUE
      CHANGING AVALUE.
    WRITE: / 'Setting', ANAME, 'to', AVALUE.
  ENDLOOP.
  REFRESH BENTRIES.
ENDFORM.                    "initWageTypes



*
* Get a additional wage types from storage
*
FORM GETWAGETYPEATTRIBUTES
  USING MODE TYPE I.
  DATA:
    ANAME   TYPE STRING,
    AVALUE  TYPE STRING,
    BENTRY  TYPE TBENTRY.

  SELECT ANAME AVALUE INTO (ANAME, AVALUE )
      FROM (CUSTTABLE)
      WHERE ANAME LIKE 'WT_%'.
    READ TABLE BENTRIES INTO BENTRY WITH KEY ID = ANAME+3.
    IF SY-SUBRC > 2.
      IF DEBUGLEVEL > 2.
        WRITE: / 'Reading wage type:', ANAME, AVALUE.
      ENDIF.
      BENTRY-ID = ANAME+3.
      BENTRY-WT = AVALUE.
      APPEND BENTRY TO BENTRIES.
    ENDIF.
  ENDSELECT.
  IF SY-SUBRC <> 0.
    WRITE: / 'Error reading wage type attributes'.
  ENDIF.
ENDFORM.                    "getWageTypeAttributes



*
* Get the concatenated text of action and reason
*
FORM GETMASSNTEXT
  USING
    MASSN TYPE MASSN
    MASSG TYPE MASSG
  CHANGING
    TEXT
****I_KONAKOV - insert parameter for reason of action
    TEXT2.

  DATA:
    MASSNT  TYPE T529T-MNTXT,
    MASSGT  TYPE T530T-MGTXT.

  CALL FUNCTION 'HRWPC_RFC_MASSN_TEXT_GET'
    EXPORTING
      MASSN      = MASSN
      LANGU      = SY-LANGU
    IMPORTING
      MASSN_TEXT = MASSNT.
  CALL FUNCTION 'HRWPC_RFC_MASSG_TEXT_GET'
    EXPORTING
      MASSN      = MASSN
      MASSG      = MASSG
      LANGU      = SY-LANGU
    IMPORTING
      MASSG_TEXT = MASSGT.
****I_KONAKOV - change to separate nature and reason of action
***  concatenate massnt '/' massgt
***    into text separated by space.
  TEXT = MASSNT.
  TEXT2 = MASSGT.
****I_KONAKOV - end of change
ENDFORM.                    "getMassnText



*
FORM GETHOMESTATION
  USING
    PERNR  TYPE PERNR-PERNR
    BEGDA  TYPE BEGDA
  CHANGING
    HOMEST TYPE NATIO
****I_KONAKOV - insert parameter for Home city
    HOMECITY.

  CLEAR HOMEST.
  DATA:
    T_P0351    TYPE TABLE OF P0351,
    WA_P0351   TYPE P0351.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0351'
      BEGDA           = BEGDA
      ENDDA           = BEGDA
    TABLES
      INFTY_TAB       = T_P0351
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0351 INTO WA_P0351.
      IF WA_P0351-CONTP = CONTPHOME.
        HOMEST = WA_P0351-LAND1.
****I_KONAKOV - insert line for Home city
        HOMECITY = WA_P0351-ORT01.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                    "getHomeStation



*
FORM GETORGEHTEXT
  USING
    ORGEH TYPE ORGEH
  CHANGING
    ORGTX TYPE STRING.

  CLEAR ORGTX.
  SELECT SINGLE ORGTX FROM T527X INTO ORGTX
    WHERE SPRSL = SY-LANGU
      AND ORGEH = ORGEH.
ENDFORM.                    "getOrgehText


*
FORM GETBTRTLTEXT
  USING
    WERKS TYPE PERSA
    BTRTL TYPE BTRTL
  CHANGING
    BTEXT TYPE STRING.

  CLEAR BTEXT.
  SELECT SINGLE BTEXT FROM T001P INTO BTEXT
    WHERE
*      werks = werks and
      BTRTL = BTRTL.
ENDFORM.                    "getBtrtlText


*
FORM GETPERSGTEXT
  USING
    PERSG TYPE PERSG
  CHANGING
    PTEXT TYPE STRING.

  CLEAR PTEXT.
  SELECT SINGLE PTEXT FROM T501T INTO PTEXT
    WHERE SPRSL = SY-LANGU
      AND PERSG = PERSG.
ENDFORM.                    "getPersgText


*
FORM GETCCTEXT
  USING
    KOKRS  TYPE KOKRS
    KOSTL  TYPE KOSTL
  CHANGING
    KTEXT TYPE STRING.

  DATA:
    SCC_CODE  TYPE STRING.

  CLEAR KTEXT.

  PERFORM GETATTRIBUTE USING 'CC_CODE' 'X' CHANGING SCC_CODE.
  IF SCC_CODE IS INITIAL.
    SELECT SINGLE KTEXT FROM CSKT INTO KTEXT
      WHERE SPRAS = SY-LANGU
        AND KOKRS = KOKRS
        AND KOSTL = KOSTL.
  ENDIF.
  IF KTEXT IS INITIAL.
    KTEXT = KOSTL.
  ENDIF.
ENDFORM.                    "getCCText


*
FORM GETNATIOTEXT
  USING
    NATIO TYPE NATIO
  CHANGING
    NATIOTEXT TYPE STRING.
  SELECT SINGLE NATIO FROM T005T INTO NATIOTEXT
    WHERE SPRAS = SY-LANGU
      AND LAND1 = NATIO.
ENDFORM.                    "getNatioText

*
FORM GETNATIOTEXTLANDX
  USING
    NATIO TYPE NATIO
  CHANGING
    NATIOTEXT TYPE STRING.
  SELECT SINGLE LANDX FROM T005T INTO NATIOTEXT
    WHERE SPRAS = SY-LANGU
      AND LAND1 = NATIO.
ENDFORM.                    "getNatioTextLandx



*
FORM GETPOSITIONTEXT
  USING
    PLANS TYPE PLANS
    DATUM TYPE D
  CHANGING
    PLANSTEXT TYPE STRING.
  PLANSTEXT = PLANS.
  IF 1 = 1.
    DATA:
      IT1000_TAB   TYPE TABLE OF P1000 INITIAL SIZE 10,
      IT1000_WA    LIKE LINE OF IT1000_TAB.
    CALL FUNCTION 'RH_PM_READ_INFTY'
      EXPORTING
        ACT_PLVAR        = PLVAR
        ACT_OTYPE        = 'S '
        ACT_OBJID        = PLANS
        ACT_BEGDA        = DATUM
        ACT_ENDDA        = DATUM
        ACT_ISTAT        = '1'
        ACT_INFTY        = '1000'
      TABLES
        INNNN            = IT1000_TAB
      EXCEPTIONS
        NO_ACTIVE_PLVAR  = 1
        OBJECT_NOT_FOUND = 2
        NOTHING_FOUND    = 3
        OTHERS           = 4.
    LOOP AT IT1000_TAB INTO IT1000_WA.
      PLANSTEXT = IT1000_WA-STEXT.
    ENDLOOP.
  ELSE.
    SELECT SINGLE PLSTX FROM T528T INTO PLANSTEXT
      WHERE SPRSL = SY-LANGU
        AND OTYPE = 'S '
        AND PLANS = PLANS
        AND BEGDA <= DATUM
        AND ENDDA >= DATUM.
  ENDIF.
ENDFORM.                    "getPositionText


* insert 14.09.2006
FORM RE549D USING
            MERKMAL      TYPE C
            KIND_OF_ERROR
            BACK
            STATUS.
  DATA          STRUC(5).
  DATA          FEATURE LIKE T549B-NAMEN.
  FIELD-SYMBOLS <STRUC_CONTENT>.
  FEATURE = MERKMAL.
  SELECT SINGLE STRUC FROM  T549D INTO STRUC
         WHERE  NAMEN       = MERKMAL.
  IF SY-SUBRC NE 0.
    STATUS = 4.
  ELSE.
    ASSIGN (STRUC) TO <STRUC_CONTENT>.
    IF SY-SUBRC NE 0 AND ( KIND_OF_ERROR = SPACE OR
                           KIND_OF_ERROR = 1 ).
      STATUS = 8.
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 2.
      MESSAGE I568(P0).
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 3.
      MESSAGE S568(P0).
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 4.
      MESSAGE E568(P0).
    ELSE.
      CLEAR BACK.
      CALL FUNCTION 'HR_FEATURE_BACKFIELD'
        EXPORTING
          FEATURE       = FEATURE
          STRUC_CONTENT = <STRUC_CONTENT>
          KIND_OF_ERROR = KIND_OF_ERROR
        IMPORTING
          BACK          = BACK
        CHANGING
          STATUS        = STATUS
        EXCEPTIONS
          OTHERS        = 1.    "VLDAL0K095544 (Checkman)
      IF SY-SUBRC <> 0.
      ENDIF.
    ENDIF.
  ENDIF.
ENDFORM.                                                    "RE549D
* end insert 14.09.2006

*
* Get position, department & location
*
FORM GETP0001
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0001    TYPE TABLE OF P0001,
    WA_P0001   TYPE P0001.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0001'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0001
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0001 INTO WA_P0001.
      IF    WA_P0001-BEGDA <= FROMD
        AND WA_P0001-ENDDA >= FROMD.
        PLANSB = WA_P0001-PLANS.
        ORGEHB = WA_P0001-ORGEH.
        WERKSB = WA_P0001-WERKS.
        BTRTLB = WA_P0001-BTRTL.
        PERSGB = WA_P0001-PERSG.
        PERSKB = WA_P0001-PERSK.
        KOSTLB = WA_P0001-KOSTL.
      ENDIF.
      IF    WA_P0001-BEGDA <= TOD
        AND WA_P0001-ENDDA >= TOD.
        PLANSA = WA_P0001-PLANS.
        ORGEHA = WA_P0001-ORGEH.
        WERKSA = WA_P0001-WERKS.
        BTRTLA = WA_P0001-BTRTL.
        PERSGA = WA_P0001-PERSG.
        PERSKA = WA_P0001-PERSK.
        KOSTLA = WA_P0001-KOSTL.
        EXIT.
      ENDIF.
    ENDLOOP.
* insert 14.09.2006
* get Name of HR Administrator
    MOVE-CORRESPONDING WA_P0001 TO PME17.
    PME17-MOLGA = 'UN'.
    PME17-TCLAS = 'A'.
    PERFORM RE549D USING 'PINCH'
                         '4'
                         L_SBMOD
                         SY-SUBRC.
    IF SY-SUBRC NE 0.
      CLEAR PA_ADMIN.
    ELSE.
      SELECT SINGLE SACHN FROM T526 INTO PA_ADMIN
       WHERE WERKS = L_SBMOD
         AND SACHX = WA_P0001-SACHP.

      IF SY-SUBRC = 0.
        PA_ADMIN = PA_ADMIN(2).
      ENDIF.
    ENDIF.
* end insert 14.09.2006
  ENDIF.
ENDFORM.                                                    "getP0001



*
* Get Natio etc.
*
FORM GETP0002
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0002    TYPE TABLE OF P0002,
    WA_P0002   TYPE P0002.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0002'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0002
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0002 INTO WA_P0002.
      IF    WA_P0002-BEGDA <= FROMD
        AND WA_P0002-ENDDA >= FROMD.
        NATIOB = WA_P0002-NATIO.
      ENDIF.
      IF    WA_P0002-BEGDA <= TOD
        AND WA_P0002-ENDDA >= TOD.
        NATIOA = WA_P0002-NATIO.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                                                    "getP0002



*
* Get PA0008
*
FORM GETP0008
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0008    TYPE TABLE OF P0008,
* insert 27.09.2006
    WA_P0008A  TYPE TABLE OF P0008,
    WA_P0008B  TYPE TABLE OF P0008,
* end insert 27.09.2006
    WA_P0008   TYPE P0008.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0008'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0008
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0008 INTO WA_P0008.
      IF    WA_P0008-BEGDA <= FROMD
        AND WA_P0008-ENDDA >= FROMD.
        TRFGRB = WA_P0008-TRFGR.
        TRFSTB = WA_P0008-TRFST.
        STVORB = WA_P0008-STVOR.
* insert 27.09.2006
        APPEND WA_P0008 TO WA_P0008B.
* end insert 27.09.2006
      ENDIF.
      IF    WA_P0008-BEGDA <= TOD
        AND WA_P0008-ENDDA >= TOD.
        TRFGRA = WA_P0008-TRFGR.
        TRFSTA = WA_P0008-TRFST.
        STVORA = WA_P0008-STVOR.
* insert 27.09.2006
        APPEND WA_P0008 TO WA_P0008A.
* end insert 27.09.2006
        EXIT.
      ENDIF.
    ENDLOOP.

* Getting the computed STVOR
    DATA: TMPS TYPE STRING.
    PERFORM GETATTRIBUTE USING 'NEXTINCR'  'N' CHANGING TMPS.
    IF TMPS = 'Y'.
* insert 14.09.2006
* only go to this routine if Next Incr date is blank
      IF STVORB IS INITIAL.
* end insert 14.09.2006
* changed 27.09.2006
*     CALL FUNCTION '/TAR/UN_RECLASS_NEXT_INCR_DATE'
        CALL FUNCTION 'HR_UN_RECLASS_NEXT_INCR_DATE'
* end changed 27.09.2006
         EXPORTING
            PERNR           = PERNR
*         RECL_DATE       =
            BEGDA           = FROMD
            ENDDA           = FROMD
          IMPORTING
            STVOR           = STVORB
          TABLES
* changed 27.09.2006
*         P0008           = t_p0008.
            P0008           = WA_P0008B.
* changed 27.09.2006
* insert 14.09.2006
      ENDIF.
* end insert 14.09.2006

* insert 14.09.2006
* only go to this routine if Next Incr date is blank
      IF STVORA IS INITIAL.
* end insert 14.09.2006
* changed 27.09.2006
*     CALL FUNCTION '/TAR/UN_RECLASS_NEXT_INCR_DATE'
        CALL FUNCTION 'HR_UN_RECLASS_NEXT_INCR_DATE'
* end changed 27.09.2006
          EXPORTING
            PERNR           = PERNR
*         RECL_DATE       =
            BEGDA           = TOD
            ENDDA           = TOD
          IMPORTING
            STVOR           = STVORA
          TABLES
* changed 27.09.2006
*         P0008           = t_p0008.
            P0008           = WA_P0008A.
* changed 27.09.2006
* insert 14.09.2006
      ENDIF.
* end insert 14.09.2006
    ENDIF.

  ENDIF.
ENDFORM.                                                    "getP0008



*
* Get contract
*
FORM GETCONTRACT
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0016    TYPE TABLE OF P0016,
    WA_P0016   TYPE P0016.

  CLEAR: CTTYPB, CTTYPA, BEGDAB, BEGDAA, CTEDTB, CTEDTA.
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0016'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0016
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0016 INTO WA_P0016.
      IF 1 = 1.
        IF     WA_P0016-BEGDA <= FROMD
           AND WA_P0016-ENDDA >= FROMD.
          CTTYPB = WA_P0016-CTTYP.
          BEGDAB = WA_P0016-BEGDA.
          CTEDTB = WA_P0016-CTEDT.
***          zzpyfb = wa_p0016-zzpyfreq.
        ENDIF.
        IF     WA_P0016-BEGDA <= TOD
           AND WA_P0016-ENDDA >= TOD.
          BEGDAA = WA_P0016-BEGDA.
          CTEDTA = WA_P0016-CTEDT.
          CTTYPA = WA_P0016-CTTYP.
***          zzpyfa = wa_p0016-zzpyfreq.
          EXIT.
        ENDIF.
      ELSE.
        IF     WA_P0016-BEGDA < TOD
           AND WA_P0016-ENDDA > TOD.
          CTTYPB = WA_P0016-CTTYP.
          CTTYPA = WA_P0016-CTTYP.
          BEGDAB = WA_P0016-BEGDA.
          BEGDAA = WA_P0016-BEGDA.
          CTEDTB = WA_P0016-CTEDT.
          CTEDTA = WA_P0016-CTEDT.
        ENDIF.
        IF WA_P0016-BEGDA = TOD.
          BEGDAA = WA_P0016-BEGDA.
          CTEDTA = WA_P0016-CTEDT.
          CTTYPA = WA_P0016-CTTYP.
          EXIT.
        ENDIF.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                    "getContract


*&---------------------------------------------------------------------*
*&      Form  getContractText
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->CTTYP      text
*      -->CTTYPTEXT  text
*----------------------------------------------------------------------*
FORM GETCONTRACTTEXT
  USING
    CTTYP TYPE CTTYP
  CHANGING
    CTTYPTEXT TYPE STRING.

  CLEAR CTTYPTEXT.
  SELECT SINGLE CTTXT FROM T547S INTO CTTYPTEXT
    WHERE SPRSL = SY-LANGU
      AND CTTYP = CTTYP.
ENDFORM.                    "getContractText

* insert 24.08.2006
FORM GETP0021
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0021  TYPE TABLE OF P0021,
* insert 06.10.2006
    L_INTKY  TYPE T577-INTKY,
* end insert 06.10.2006
    WA_P0021 TYPE P0021.

  RATEA = 'S-rate'.
  RATEB = 'S-rate'.


  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0021'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0021
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0021 INTO WA_P0021.
      IF    WA_P0021-BEGDA <= FROMD
        AND WA_P0021-ENDDA >= FROMD.

* changed 06.10.2006
*       if wa_p0021-kdgbr = 'X'.
*          ratea = 'D-rate'.
        IF WA_P0021-KDGBR = 'X' AND WA_P0021-SPRPS IS INITIAL.
          SELECT SINGLE INTKY FROM T577 INTO L_INTKY
            WHERE MOLGA = 'UN' AND AUSPR = WA_P0021-FAMSA.
          IF SY-SUBRC = 0.
            CASE L_INTKY.
              WHEN '1'.
                RATEA = 'D-rate'.
              WHEN '2'.
                RATEA = 'D-rate'.
              WHEN OTHERS.
            ENDCASE.
          ENDIF.
        ENDIF.
* end changed 06.10.2006

**** changed 06.10.2006 / 20.10.2006
**** check table T577 for all valid child
****       if wa_p0021-un_zz_midep = 'X' and wa_p0021-famsa = '2'.
***        if wa_p0021-un_zz_midep = 'X' and wa_p0021-sprps is initial.
**** end changed 06.10.2006
***           select single intky from T577 into l_intky
***             where molga = 'UN' and auspr = wa_p0021-famsa.
***           if sy-subrc = 0.
***              if l_intky = '1'.
***                 case wa_p0021-zzbenc.
***                  when 'S'.
***                    add 1 to hidcsharea.
***                  when 'F'.
***                    add 1 to hidcfulla.
***                  when others.
***                 endcase.
***              endif.
***           endif.
**** end changed 20.10.2006
***         endif.

**** changed 06.10.2006 / 20.10.2006
**** check table T577 for all valid spouse
****       if wa_p0021-un_zz_midep = 'X' and wa_p0021-famsa = '1'.
***        if wa_p0021-un_zz_midep = 'X' and wa_p0021-sprps is initial.
**** end changed 06.10.2006
***           select single intky from T577 into l_intky
***             where molga = 'UN' and auspr = wa_p0021-famsa.
***           if sy-subrc = 0.
***              if l_intky = '2'.
***                 case wa_p0021-zzbenc.
***                  when 'S'.
***                    add 1 to hidssharea.
***                  when 'F'.
***                    add 1 to hidsfulla.
***                  when others.
***                 endcase.
***              endif.
***           endif.
***         endif.
**** end changed 20.10.2006
      ENDIF.

      IF    WA_P0021-BEGDA <= TOD
        AND WA_P0021-ENDDA >= TOD.

* changed 06.10.2006
*       if wa_p0021-kdgbr = 'X'.
*          rateb = 'D-rate'.
*       endif.
        IF WA_P0021-KDGBR = 'X' AND WA_P0021-SPRPS IS INITIAL.
          SELECT SINGLE INTKY FROM T577 INTO L_INTKY
            WHERE MOLGA = 'UN' AND AUSPR = WA_P0021-FAMSA.
          IF SY-SUBRC = 0.
            CASE L_INTKY.
              WHEN '1'.
                RATEB = 'D-rate'.
              WHEN '2'.
                RATEB = 'D-rate'.
              WHEN OTHERS.
            ENDCASE.
          ENDIF.
        ENDIF.
* end changed 06.10.2006

**** changed 06.10.2006 /20.10.2006
**** check table T577 for all valid child
****       if wa_p0021-un_zz_midep = 'X' and wa_p0021-famsa = '2'.
***        if wa_p0021-un_zz_midep = 'X' and wa_p0021-sprps is initial.
**** end changed 06.10.2006
***           select single intky from T577 into l_intky
***             where molga = 'UN' and auspr = wa_p0021-famsa.
***           if sy-subrc = 0.
***              if l_intky = '1'.
***                 case wa_p0021-zzbenc.
***                  when 'S'.
***                    add 1 to hidcshareb.
***                  when 'F'.
***                    add 1 to hidcfullb.
***                  when others.
***                 endcase.
***              endif.
***           endif.
***         endif.
**** end changed 20.10.2006

**** changed 06.10.2006
**** check table T577 for all valid spouse
****       if wa_p0021-un_zz_midep = 'X' and wa_p0021-famsa = '1'.
***        if wa_p0021-un_zz_midep = 'X' and wa_p0021-famsa = '1'
***           and wa_p0021-sprps is initial.
**** end changed 06.10.2006
***           select single intky from T577 into l_intky
***             where molga = 'UN' and auspr = wa_p0021-famsa.
***           if sy-subrc = 0.
***              if l_intky = '2'.
***                 case wa_p0021-zzbenc.
***                  when 'S'.
***                    add 1 to hidsshareb.
***                  when 'F'.
***                    add 1 to hidsfullb.
***                  when others.
***                 endcase.
***              endif.
***           endif.
***         endif.
**** end changed 20.10.2006

      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                                                    "getP0021
* end insert 24.08.2006


*
* Get health insurance plan
*
FORM GETP0167
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0167    TYPE TABLE OF P0167,
    WA_P0167   TYPE P0167.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0167'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0167
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0167 INTO WA_P0167.
      IF    WA_P0167-BEGDA <= FROMD
        AND WA_P0167-ENDDA >= FROMD.
        DEPCVB = WA_P0167-DEPCV.
        BOPTIB = WA_P0167-BOPTI.
      ENDIF.
      IF    WA_P0167-BEGDA <= TOD
        AND WA_P0167-ENDDA >= TOD.
        DEPCVA = WA_P0167-DEPCV.
        BOPTIA = WA_P0167-BOPTI.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                                                    "getP0167


* insert 14.09.2006
* get record in IT0007
FORM GETP0007
  USING
    PERNR    TYPE PERNR-PERNR
    FROMD    TYPE BEGDA
    TOD      TYPE BEGDA.

  DATA:
    T_P0007    TYPE TABLE OF P0007,
    WA_P0007   TYPE P0007.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0007'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0007
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0007 INTO WA_P0007.
      IF    WA_P0007-BEGDA <= FROMD
        AND WA_P0007-ENDDA >= FROMD.
        EMPCTB = WA_P0007-EMPCT.
      ENDIF.
      IF    WA_P0007-BEGDA <= TOD
        AND WA_P0007-ENDDA >= TOD.
        EMPCTA = WA_P0007-EMPCT.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                                                    "getP0007
* end insert 14.09.2006


*
* Get cost distribution
*
FORM GETCOSTDISTR
  TABLES
    LINES
  USING
    PERNR    TYPE PERNR-PERNR
    BEGDA    TYPE BEGDA
  CHANGING
    TEXTB1   TYPE STRING
    TEXTB2   TYPE STRING
    TEXTA1   TYPE STRING
    TEXTA2   TYPE STRING.

  DATA:
    TMPS                 TYPE STRING,
    TMPS2                TYPE STRING,
    COUNT                TYPE I,
    DIST_COSTCENTERS     TYPE TABLE OF HRI1001_COST,
    DIST_COSTCENTERS_WA  TYPE HRI1001_COST,
    INIT_TAB             TYPE TABLE OF HRI1001,
    GIVEN_P0001_TAB      TYPE TABLE OF P0001,
    FIELDCD(28)          TYPE C,
    FIELDSB1             TYPE TABLE OF STRING,
    FIELDSB2             TYPE TABLE OF STRING,
    FIELDSA1             TYPE TABLE OF STRING,
    FIELDSA2             TYPE TABLE OF STRING,
    FIELDPRZ(6)          TYPE C,
    LINE(80)             TYPE C,
    SEPC(1)              TYPE C VALUE ',',
    T_P0001              TYPE TABLE OF P0001,
    T_P0027              TYPE TABLE OF P0027,
    WA_P0027             LIKE LINE OF T_P0027.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0001'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0001
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0027'
      BEGDA           = BEGDA
      ENDDA           = BEGDA
    TABLES
      INFTY_TAB       = T_P0027
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.

  CLEAR: TEXTB1, TEXTB2, TEXTA1, TEXTA2.

  DATA:
    KBU    LIKE WA_P0027-KBU01,
    KST    LIKE WA_P0027-KST01,
    KPR    LIKE WA_P0027-KPR01.
  DATA:
    POSFT  TYPE I,
    FTEXTB1(400),
    FTEXTB2(400),
    FTEXTA1(400),
    FTEXTA2(400).

*  sepc = lc_vtab.
  DESCRIBE TABLE T_P0027 LINES COUNT.
  POSFT = 0.
  IF COUNT > 0.
    LOOP AT T_P0027 INTO WA_P0027.
      IF 1 = 1.
        DO 20 TIMES VARYING KST FROM WA_P0027-KST01 NEXT WA_P0027-KST02
                   VARYING KBU FROM WA_P0027-KBU01 NEXT WA_P0027-KBU02
                   VARYING KPR FROM WA_P0027-KPR01 NEXT WA_P0027-KPR02.
          IF KST IS INITIAL. EXIT. ENDIF.
          PERFORM GETCCTEXT
            USING    KBU KST
            CHANGING TMPS.
          IF TEXTB1 IS INITIAL.
            TEXTB1  = TMPS.
            FTEXTB1 = TMPS.
          ELSE.
            CONCATENATE TEXTB1 TMPS INTO TEXTB1 SEPARATED BY SEPC.
            FTEXTB1+POSFT = TMPS.
          ENDIF.
          TMPS = WA_P0027-KPR01.
          CONCATENATE TMPS '%' INTO TMPS.
          IF TEXTB2 IS INITIAL.
            TEXTB2  = TMPS.
            FTEXTB2 = TMPS.
          ELSE.
            CONCATENATE TEXTB2 TMPS INTO TEXTB2 SEPARATED BY SEPC.
            FTEXTB2+POSFT = TMPS.
          ENDIF.
          ADD 21 TO POSFT.
        ENDDO.
      ENDIF.
    ENDLOOP.
  ELSE.
    CLEAR: TEXTB1, TEXTB2, TEXTA1, TEXTA2.
    CALL FUNCTION 'RH_COST_DISTRIBUTION_OF_OBJECT'
      EXPORTING
        PLVAR            = '01'
        BEGDA            = '18000101'
        ENDDA            = '99991231'
        PERNR            = PERNR
        USE_OM_BUFFER    = SPACE
      TABLES
        DIST_COSTCENTERS = DIST_COSTCENTERS
        INIT_TAB         = INIT_TAB
        GIVEN_P0001_TAB  = T_P0001. "given_p0001_tab.

    LOOP AT DIST_COSTCENTERS INTO DIST_COSTCENTERS_WA.
      WRITE DIST_COSTCENTERS_WA-PROZT TO FIELDPRZ.
      TMPS = FIELDPRZ.
      CLEAR FIELDCD.
      PERFORM GETCCTEXT
        USING
          DIST_COSTCENTERS_WA-KOKRS
          DIST_COSTCENTERS_WA-KOSTL
        CHANGING
          TMPS2.
      IF DIST_COSTCENTERS_WA-BEGDA <= BEGDA
         AND DIST_COSTCENTERS_WA-ENDDA >= BEGDA.
        APPEND TMPS2    TO FIELDSB1.
        APPEND FIELDPRZ TO FIELDSB2.
      ENDIF.
*      if dist_costcenters_wa-endda > begda.
*        append tmpS2    to fieldsa1.
*        append fieldPrz to fieldsa2.
*      endif.
      CLEAR LINE.
    ENDLOOP.

    POSFT = 0.
    LOOP AT FIELDSB1 INTO TMPS.
      IF TEXTB1 IS INITIAL.
        TEXTB1  = TMPS.
        FTEXTB1 = TMPS.
      ELSE.
        CONCATENATE TEXTB1 TMPS INTO TEXTB1 SEPARATED BY SEPC.
        FTEXTB1+POSFT = TMPS.
      ENDIF.
      ADD 21 TO POSFT.
    ENDLOOP.
    POSFT = 0.
    LOOP AT FIELDSB2 INTO TMPS.
      IF TEXTB2 IS INITIAL.
        TEXTB2  = TMPS.
        FTEXTB2 = TMPS.
      ELSE.
        CONCATENATE TEXTB2 TMPS INTO TEXTB2 SEPARATED BY SEPC.
        FTEXTB2+POSFT = TMPS.
      ENDIF.
      ADD 21 TO POSFT.
    ENDLOOP.
    POSFT = 0.
    LOOP AT FIELDSA1 INTO TMPS.
      IF TEXTA1 IS INITIAL.
        TEXTA1  = TMPS.
        FTEXTA1 = TMPS.
      ELSE.
        CONCATENATE TEXTA1 TMPS INTO TEXTA1 SEPARATED BY SEPC.
        FTEXTA1+POSFT = TMPS.
      ENDIF.
      ADD 21 TO POSFT.
    ENDLOOP.
    POSFT = 0.
    LOOP AT FIELDSA2 INTO TMPS.
      IF TEXTA2 IS INITIAL.
        TEXTA2  = TMPS.
        FTEXTA2 = TMPS.
      ELSE.
        CONCATENATE TEXTA2 TMPS INTO TEXTA2 SEPARATED BY SEPC.
        FTEXTA2+POSFT = TMPS.
      ENDIF.
      ADD 21 TO POSFT.
    ENDLOOP.
  ENDIF.
  TEXTB1 = FTEXTB1.
  TEXTB2 = FTEXTB2.
  TEXTA1 = TEXTB1.
  TEXTA2 = TEXTB2.
ENDFORM.                    "getCostDistr



*
* Get assignment grant
*
FORM GETASSIGNMENTGRANT
  USING
    PERNR    TYPE PERNR-PERNR
    BEGDA    TYPE BEGDA
  CHANGING
    ASSGRB   TYPE MAXBT
    ASSGRA   TYPE MAXBT.

***    clear: assgrb, assgra.
***  data:
***    t_p9600    type table of p9600,
***    wa_p9600   type p9600.
***
***  CALL FUNCTION 'HR_READ_INFOTYPE'
***    EXPORTING
***      PERNR                 = pernr
***      INFTY                 = '9600'
***      BEGDA                 = '18000101'
***      ENDDA                 = '99991231'
***    TABLES
***      INFTY_TAB             = t_p9600
***    EXCEPTIONS
***      INFTY_NOT_FOUND       = 1
***      OTHERS                = 2.
***  if sy-subrc = 0.
***    loop at t_p9600 into wa_p9600.
***      if wa_p9600-begda < begda.
***      endif.
***    endloop.
***  endif.
***
***  perform getWT using 'AGLS' changing assgrb assgra.
***
**** insert 14.09.2006
**** assignment grant is a one-time payment
*** if salPeriodb > 1.
***    divide assgrb by salPeriodb.
***  endif.
***  if salPerioda > 1.
***    divide assgra by salPerioda.
***  endif.
**** end insert 14.09.2006

ENDFORM.                    "getAssignmentGrant



*
* Get provident fund
*
FORM GETPROVIDENTFUND
  USING
    PERNR    TYPE PERNR-PERNR
    BEGDA    TYPE BEGDA
  CHANGING
    PROFUB   TYPE MAXBT
    PROFUA   TYPE MAXBT.

***    clear: profub, profua.
***  data:
***    t_p9600    type table of p9600,
***    wa_p9600   type p9600.
***
***  CALL FUNCTION 'HR_READ_INFOTYPE'
***    EXPORTING
***      PERNR                 = pernr
***      INFTY                 = '9600'
***      BEGDA                 = '18000101'
***      ENDDA                 = '99991231'
***    TABLES
***      INFTY_TAB             = t_p9600
***    EXCEPTIONS
***      INFTY_NOT_FOUND       = 1
***      OTHERS                = 2.
***  if sy-subrc = 0.
***    loop at t_p9600 into wa_p9600.
***      if wa_p9600-begda < begda.
***      endif.
***    endloop.
***  endif.
***
***  perform getWT using 'PRFU' changing profub profua.
ENDFORM.                    "getProvidentFund


*
* Get duty station
*
FORM GETDSTAT
  USING
    PERNR   TYPE PERNR-PERNR
    BEGDA   TYPE BEGDA
  CHANGING
    DSTAT   TYPE PUN_DSTAT.

  DATA:
    T_P0001    TYPE TABLE OF P0001,
    WA_P0001   TYPE P0001.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERNR
      INFTY           = '0001'
      BEGDA           = BEGDA
      ENDDA           = BEGDA
    TABLES
      INFTY_TAB       = T_P0001
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0001 INTO WA_P0001.
      SELECT SINGLE DSTAT FROM T7UNPAD_DS0P INTO DSTAT
        WHERE WERKS = WA_P0001-WERKS
          AND BTRTL = WA_P0001-BTRTL.
      IF SY-SUBRC = 0.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.
  IF DSTAT IS INITIAL.
    WRITE: / 'Cannot determine Duty station!'.
  ENDIF.
ENDFORM.                    "getDstat



*
* Get duty station name
*
FORM GETDSTXT
  USING
    DSTAT TYPE PUN_DSTAT
  CHANGING
    DSTXT   TYPE STRING.

  SELECT SINGLE DSTXT FROM T7UNPAD_DS_T INTO DSTXT
    WHERE SPRSL = SY-LANGU
      AND MOLGA = MOLGA
      AND DSTAT = DSTAT.
ENDFORM.                    "getDstxt


*
* Get duty station country
*
FORM GETDSCOUNTRY
  USING
    DSTAT        TYPE PUN_DSTAT
  CHANGING
    COUNTRYTXT   TYPE STRING.

  DATA:
    COUNTRY  TYPE LAND1.

  SELECT SINGLE LAND1 FROM T7UNPAD_DS INTO COUNTRY
    WHERE MOLGA = MOLGA
      AND DSTAT = DSTAT.
  IF SY-SUBRC = 0.
    SELECT SINGLE LANDX FROM T005T INTO COUNTRYTXT
      WHERE SPRAS = SY-LANGU
        AND LAND1 = COUNTRY.
  ELSE.
    CONCATENATE 'country' COUNTRY INTO COUNTRYTXT
      SEPARATED BY SPACE.
  ENDIF.
ENDFORM.                    "getDsCountry



*
* Formatting
*

DATA:
  LINES        TYPE  TABLE OF STRING,
  SLINE        TYPE  STRING,
  IDHEAD1      TYPE  STRING  VALUE '1',
  IDHEAD2      TYPE  STRING  VALUE '2',
  IDNORMAL     TYPE  STRING  VALUE '3',
  IDFROMTO     TYPE  STRING  VALUE '4',
  SEPCOLUMNS   TYPE  STRING  VALUE ';',
  SEPITEMS     TYPE  STRING  VALUE ';',
  COL1         TYPE  STRING,
  COL2         TYPE  STRING,
  COL3         TYPE  STRING,
  COL4         TYPE  STRING,
  LRUWAERSB    TYPE STRING,
  LRUWAERSA    TYPE STRING.


*
* format a value.
*
FORM FMTBETRG
  USING
    BETRG TYPE MAXBT
  CHANGING
    COL   TYPE STRING.

  DATA:
    TMPCOL(14) TYPE C.

  WRITE BETRG TO TMPCOL RIGHT-JUSTIFIED CURRENCY '2'.
  COL = TMPCOL.
ENDFORM.                    "fmtBetrg


*&---------------------------------------------------------------------*
*&      Form  fmtBetrgP
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->BETRG      text
*      -->BA         text
*      -->COL        text
*----------------------------------------------------------------------*
FORM FMTBETRGP
  USING
    BETRG TYPE MAXBT
    BA    TYPE C
  CHANGING
    COL   TYPE STRING.

  DATA:
    TMPBETRG   TYPE MAXBT,
    TMPCOL(14) TYPE C.

  TMPBETRG = BETRG.
  WRITE TMPBETRG TO TMPCOL RIGHT-JUSTIFIED CURRENCY '2'.
  COL = TMPCOL.
****I_KONAKOV - line inserted for separate variable for 'P.M.' field
  CLEAR W_PMPA.
  IF   ( BA = 'b' AND SALPERIODB = 12 )
    OR ( BA = 'a' AND SALPERIODA = 12 ).
****I_KONAKOV - line commented to get rid of 'P.A.' due to requirements of STEPS team
***    concatenate col 'P.A.' into col separated by space.
  ENDIF.
  IF   ( BA = 'b' AND SALPERIODB = 1 )
    OR ( BA = 'a' AND SALPERIODA = 1 ).
****I_KONAKOV - line commented to separate 'P.M.' as other field
***    concatenate col 'P.M.' into col separated by space.
****I_KONAKOV - line inserted for separate variable for 'P.M.' field
    W_PMPA = 'P.M.'.
  ENDIF.
ENDFORM.                    "fmtBetrgP


*
* format a date.
*
FORM FMTDATE
  USING
    DATE  LIKE SY-DATUM
  CHANGING
    COL   TYPE STRING.

  DATA:
    TMPCOL(10) TYPE C.

  WRITE DATE TO TMPCOL RIGHT-JUSTIFIED.
  COL = TMPCOL.
ENDFORM.                    "fmtDate


*
* format one output line
*
FORM LINE
  USING
    ID TEXT PCOL1 PCOL2.

  CONCATENATE ID TEXT SEPITEMS PCOL1 SEPITEMS PCOL2
    INTO SLINE.
  CLEAR: COL1, COL2.
  APPEND SLINE TO LINES.
ENDFORM.                    "line


*
* getPeriod
*
FORM GETPERIOD
  USING
    ID
  CHANGING
    PERIOD TYPE I.

  DATA:
    SID TYPE STRING.

  CONCATENATE 'MU_' ID INTO SID.
  PERFORM GETATTRIBUTE USING SID '12' CHANGING TMPS.
  PERIOD = TMPS.
ENDFORM.                    "getPeriod


*
* Get wt content
*
FORM GETWT
  USING
    ID
  CHANGING
    BETRGB TYPE MAXBT
    BETRGA TYPE MAXBT.

  CLEAR: BETRGB, BETRGA.
  LOOP AT BENTRIES INTO BENTRY.
    IF BENTRY-ID(4) = ID.
      ADD BENTRY-BTB TO BETRGB.
      IF NOT BENTRY-CUB IS INITIAL.
        LRUWAERSB = BENTRY-CUB.
      ENDIF.
      ADD BENTRY-BTA TO BETRGA.
      IF NOT BENTRY-CUA IS INITIAL.
        LRUWAERSA = BENTRY-CUA.
      ENDIF.
      IF DEBUGLEVEL > 0.
        WRITE: / BENTRY-ID, AT 10 BENTRY-WT,
          BENTRY-BTB CURRENCY '2',
          BETRGB CURRENCY '2',
          BENTRY-BTA CURRENCY '2',
          BETRGA CURRENCY '2'.
      ENDIF.
    ENDIF.
  ENDLOOP.
  IF BETRGB < 0.
    BETRGB = 0 - BETRGB.
  ENDIF.
  IF BETRGA < 0.
    BETRGA = 0 - BETRGA.
  ENDIF.


* retrieve an optional multiplier
*  perform getPeriod using id     changing salPeriod.

  IF SALPERIODB > 1.
    MULTIPLY BETRGB BY SALPERIODB.
  ENDIF.
  IF SALPERIODA > 1.
    MULTIPLY BETRGA BY SALPERIODA.
  ENDIF.
ENDFORM.                    "getWT


*
* Get wage type content as formatted text
*
FORM GETWTS
  USING
    ID
  CHANGING
    SBETRGB
    SBETRGA.

  DATA:
    BETRGB  TYPE MAXBT,
    BETRGA  TYPE MAXBT.

  PERFORM GETWT     USING ID     CHANGING BETRGB BETRGA.
  PERFORM FMTBETRG  USING BETRGB CHANGING SBETRGB.
  PERFORM FMTBETRG  USING BETRGA CHANGING SBETRGA.
  IF 1 = 1.
    CONCATENATE LRUWAERSB SBETRGB INTO SBETRGB SEPARATED BY SPACE.
    CONCATENATE LRUWAERSA SBETRGA INTO SBETRGA SEPARATED BY SPACE.
  ENDIF.
ENDFORM.                    "getWTS


*
* Get wage type content as formatted text for the correct period
*
FORM GETWTSP
  USING
    ID
  CHANGING
    SBETRGB
    SBETRGA.

  DATA:
    BETRGB  TYPE MAXBT,
    BETRGA  TYPE MAXBT.

  PERFORM GETWT     USING ID     CHANGING BETRGB BETRGA.
  PERFORM FMTBETRGP USING BETRGB 'b' CHANGING SBETRGB.
  PERFORM FMTBETRGP USING BETRGA 'a' CHANGING SBETRGA.
  IF 1 = 1.
    CONCATENATE LRUWAERSB SBETRGB INTO SBETRGB SEPARATED BY SPACE.
    CONCATENATE LRUWAERSA SBETRGA INTO SBETRGA SEPARATED BY SPACE.
  ENDIF.
ENDFORM.                    "getWTSP


*
* Check whether a wage type is filled
*
FORM ISWTFILLED
  USING
    WTID
  CHANGING
    FILLEDB
    FILLEDA.

  CLEAR: FILLEDB, FILLEDA.
  READ TABLE BENTRIES INTO BENTRY
    WITH KEY ID = WTID.
  IF SY-SUBRC = 0.
    IF NOT BENTRY-BTB IS INITIAL.
      FILLEDB = 'X'.
    ENDIF.
    IF NOT BENTRY-BTA IS INITIAL.
      FILLEDA = 'X'.
    ENDIF.
  ENDIF.
ENDFORM.                    "isWtFilled

* insert 23.08.2006
FORM GETPRCPOST
  USING
    DSTAT   TYPE PUN_DSTAT
    TRFKZ   TYPE TRFKZ
    SELDATE TYPE D
  CHANGING
    PAMUL   TYPE PUN_PAMUL.

  DATA:
    DSPA TYPE T7UNPAD_DSPA.

  SELECT * FROM T7UNPAD_DSPA INTO DSPA
    WHERE MOLGA  = MOLGA
      AND DSTAT  = DSTAT
      AND TRFKZ  = TRFKZ
      AND BEGDA <= SELDATE
      AND ENDDA >= SELDATE.
    PAMUL = DSPA-PAMUL.
    IF DSPA-TRFKZ = TRFKZ.
      EXIT.
    ENDIF.
  ENDSELECT.
ENDFORM.                    "getPrcPost

*&---------------------------------------------------------------------*
*&      Form  fmtPrz
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->PRZ        text
*      -->COL        text
*----------------------------------------------------------------------*
FORM FMTPRZ
  USING
    PRZ   TYPE P
  CHANGING
    COL   TYPE STRING.

  DATA:
    PRZ2(5)   TYPE P DECIMALS 2,
    TMPCOL(7) TYPE C.

  PRZ2 = PRZ.
  WRITE PRZ2 TO TMPCOL RIGHT-JUSTIFIED CURRENCY '2'.
  COL = TMPCOL.
* concatenate col '%' into col.
ENDFORM.                    "fmtPrz

*&---------------------------------------------------------------------*
*&      Form  fmtPrz2
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->PRZ        text
*      -->COL        text
*----------------------------------------------------------------------*
FORM FMTPRZ2
  USING
    PRZ   TYPE P
  CHANGING
    COL   TYPE STRING.

  DATA:
    PRZ2(5)   TYPE P,
    TMPCOL(7) TYPE C.

  PRZ2 = PRZ.
  WRITE PRZ2 TO TMPCOL LEFT-JUSTIFIED.
  COL = TMPCOL.
* concatenate col '%' into col.
ENDFORM.                                                    "fmtPrz2

* end insert 23.08.2006

*
* Construct an entry for the MS Word data file
* taking care for several modes to blank out fields
*
FORM MKENTRY
  USING
    FIELD
    VALUE.

  DATA:
    ENAFROM(1)   TYPE C VALUE 'X',
    ENATO(1)     TYPE C VALUE 'X'.

  IF <GPREVINFTY> IS INITIAL.
    CLEAR ENAFROM.
  ELSE.
    IF GENAFROM IS INITIAL.
      CLEAR ENAFROM.
      READ TABLE DISPBLINES TRANSPORTING NO FIELDS
        WITH KEY TABLE_LINE = FIELD.
      IF SY-SUBRC = 0.
        ENAFROM = 'X'.
      ENDIF.
    ENDIF.
  ENDIF.
  IF <GTHISINFTY> IS INITIAL.
    CLEAR ENATO.
  ELSE.
    IF GENATO IS INITIAL.
      CLEAR ENATO.
      READ TABLE DISPBLINES TRANSPORTING NO FIELDS
        WITH KEY TABLE_LINE = FIELD.
      IF SY-SUBRC = 0.
        ENATO = 'X'.
      ENDIF.
    ENDIF.
  ENDIF.

  IF STRLEN( FIELD ) = 2.
    IF FIELD+1(1) = 'F'.
      IF ENAFROM IS INITIAL.
        CLEAR VALUE.
      ENDIF.
    ENDIF.
    IF FIELD+1(1) = 'T'.
      IF ENATO IS INITIAL.
        CLEAR VALUE.
      ENDIF.
    ENDIF.
  ENDIF.
  IF STRLEN( FIELD ) = 3.
    IF FIELD+2(1) = 'F'.
      IF ENAFROM IS INITIAL.
        CLEAR VALUE.
      ENDIF.
    ENDIF.
    IF FIELD+2(1) = 'T'.
      IF ENATO IS INITIAL.
        CLEAR VALUE.
      ENDIF.
    ENDIF.
  ENDIF.

  CONCATENATE FIELD SEPCOLUMNS VALUE
    INTO SLINE. " separated by space.
  APPEND SLINE TO LINES.
ENDFORM.                    "mkEntry


* * * * * * * * * * * * * * * * * * * *
*
*
* Process one person
*
*
* * * * * * * * * * * * * * * * * * * *
FORM DOPROCESSING
  USING
    PERNR    TYPE PERNR-PERNR.

  DATA:
    TAB        TYPE  X       VALUE '09',
    TABC       TYPE  C,
    LF         TYPE  X       VALUE '0A',
    CR         TYPE  X       VALUE '0D',
    NATOFACT   TYPE  STRING  VALUE 'undefined',
****I_KONAKOV - insert line for reason of action
    REASOFACT  TYPE  STRING  VALUE 'undefined',
    CURRPERNR  TYPE  PERNR-PERNR,
    BETB       TYPE  MAXBT,
    BETA       TYPE  MAXBT,
    FILLEDB(1) TYPE  C,
    FILLEDA(1) TYPE  C.

  TABC        = TAB.

  PERFORM GETATTRIBUTE USING 'TP_FROM' '99990000' CHANGING TMPS.
  IF TMPS IS INITIAL.
    WRITE: /
      'Number range for temporary persons not defined ("TP_FROM").',
      'Terminating'.
    RETURN.
  ENDIF.
  CURRPERNR = TMPS.
****I_KONAKOV - insert to avoid blockage when using the same pernr
  DATA: W_CURRPN(20),
        W_NEWPN(8) TYPE N,
        W_WACT TYPE ZUNES_ATTR.

  CLEAR W_CURRPN.
  SELECT ANAME
        FROM (CUSTTABLE)
        INTO W_CURRPN
        WHERE ANAME LIKE 'CPN9999%'
        ORDER BY ANAME.
  ENDSELECT. "(custtable)
  IF SY-SUBRC <> 0.
    W_NEWPN = '99990000'.
   ELSE.
     W_NEWPN = W_CURRPN+3(8) + 1.
  ENDIF. "sy-subrc
  CLEAR W_CURRPN.
  CONCATENATE 'CPN' W_NEWPN INTO W_CURRPN.
  CLEAR W_WACT.
  W_WACT-ANAME = W_CURRPN.
  INSERT INTO (CUSTTABLE) VALUES W_WACT.
  IF SY-SUBRC <> 0.
    WRITE: / 'Unable to generate new temp. PERNR!'.
   ELSE.
     OVRPERNR = W_NEWPN.
  ENDIF.
****I_KONAKOV - end of insert
  IF NOT OVRPERNR IS INITIAL.
    IF OVRPERNR > '99990000'.
      CURRPERNR = OVRPERNR.
      WRITE: / 'Temporary pernr overwritten by', CURRPERNR.
    ENDIF.
  ENDIF.
  IF CURRPERNR IS INITIAL.
    WRITE: /
      'Temporary person is initial !',
      'Terminating'.
    RETURN.
  ENDIF.
  IF CURRPERNR < '9000000'.
    WRITE: /
      'Temporary person is below 90000000 !',
      'Terminating'.
    RETURN.
  ENDIF.

  PERFORM DELETEPERSON
    USING CURRPERNR 'X' 'X'.

  PERFORM COPYPERSON
    USING PERNR CURRPERNR.

  FORMAT COLOR COL_NORMAL.
  WRITE: / 'Person', PPERNR,
    '   ( copied to temporary person:', CURRPERNR, ')'.
  FORMAT COLOR OFF.
  SKIP.
  IF 1 = 2.
    PERFORM CREATEDUMMYPERSON
      USING CURRPERNR.
  ENDIF.

  IF DEBUGLEVEL > 99.
    PERFORM DISPLAYPERSON
      USING CURRPERNR.
  ENDIF.

*
* Process according to the selected information
*

* Action
  IF NOT PDOACT IS INITIAL.
    DATA:
      THISPA0000  TYPE PA0000,
      PREVPA0000  TYPE PA0000.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0000' PSDATE 'X'
      CHANGING THISPA0000 PREVPA0000.
    PERFORM GETMASSNTEXT
      USING THISPA0000-MASSN THISPA0000-MASSG
      CHANGING NATOFACT REASOFACT.
  ENDIF.

* Last action
  IF NOT PDOACTT IS INITIAL.
    PERFORM FETCHACTIONINFOTYPE
      USING    CURRPERNR PACTT PACTR PSDATE 'X'
      CHANGING THISPA0000 PREVPA0000.
    PERFORM GETMASSNTEXT
      USING THISPA0000-MASSN THISPA0000-MASSG
      CHANGING NATOFACT REASOFACT.
  ENDIF.

* Mobility and hardship allowance (0960)
  IF NOT PDOMAH IS INITIAL.
    DATA:
      THISPA0960  TYPE PA0960,
      PREVPA0960  TYPE PA0960.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0960' PSDATE 'X'
      CHANGING THISPA0960 PREVPA0960.
    NATOFACT = 'Change in mobility range'.
  ENDIF.

* Education grant (9605)
*  if not pdoEDGR is initial.
*data:
*  thisPA9605  type pa9605,
*  prevPA9605  type pa9605.
*
*    perform fetchInfotype
*      using    currPernr '9605' psdate 'X'
*      changing thisPA9605 prevPA9605.
*    NatOfAct = 'Grant/Change of education Grant'.
*  endif.

* Rental subsidy (0962)
  IF NOT PDORESU IS INITIAL.
    DATA:
      THISPA0962  TYPE PA0962,
      PREVPA0962  TYPE PA0962.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0962' PSDATE 'X'
      CHANGING THISPA0962 PREVPA0962.
    NATOFACT = 'Grant/Change of rental subsidy'.
  ENDIF.

* Health insurance
  IF NOT PDOHEIN IS INITIAL.
    DATA:
*  thisPA0037  type pa0037,
*  prevPA0037  type pa0037.
      THISPA0167  TYPE PA0167,
      PREVPA0167  TYPE PA0167.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0167' PSDATE 'X'
      CHANGING THISPA0167 PREVPA0167.
    NATOFACT = 'Change in DEP/SM Health Insurances'.
  ENDIF.

* Personal data
  IF NOT PDOPEDA IS INITIAL.
    DATA:
      THISPA0002  TYPE PA0002,
      PREVPA0002  TYPE PA0002.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0002' PSDATE 'X'
      CHANGING THISPA0002 PREVPA0002.
    NATOFACT = 'Change in Personal data'.
  ENDIF.

* Contract
  IF NOT PDOCTTY IS INITIAL.
    DATA:
      THISPA0016  TYPE PA0016,
      PREVPA0016  TYPE PA0016.

    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0016' PSDATE 'X'
      CHANGING THISPA0016 PREVPA0016.
    NATOFACT = 'Change in Contract'.
  ENDIF.

* insert 24.08.2006
* Extension
  IF NOT PDOEXTN IS INITIAL.
    PERFORM FETCHINFOTYPE
      USING    CURRPERNR '0016' PSDATE 'X'
      CHANGING THISPA0016 PREVPA0016.
    NATOFACT = 'Extension of Appointment'.
  ENDIF.
* end insert 24.08.2006


*
* assure that the date is not before the hire date
*
  DATA:
    PHIFI      TYPE TABLE OF PHIFI,
    T_HFP0000  TYPE TABLE OF P0000,
    T_HFP0001  TYPE TABLE OF P0001,
    HFP0001    TYPE P0001.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = CURRPERNR
      INFTY           = '0000'
    TABLES
      INFTY_TAB       = T_HFP0000
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = CURRPERNR
      INFTY           = '0001'
    TABLES
      INFTY_TAB       = T_HFP0001
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.

  CALL FUNCTION 'RP_HIRE_FIRE'
    IMPORTING
      FIRE_DATE = FIRE_DATE
      HIRE_DATE = HIRE_DATE
    TABLES
      PPHIFI    = PHIFI
      PP0000    = T_HFP0000
      PP0001    = T_HFP0001.

  IF DEBUGLEVEL > 0.
    WRITE: / 'Hire date :', HIRE_DATE.
  ENDIF.
  IF NOT HIRE_DATE IS INITIAL.
    IF EFFECTIVEDATE < HIRE_DATE.
      WRITE: / 'Effective date (', EFFECTIVEDATE,
               ') set to hire date (', HIRE_DATE, ')'.
      EFFECTIVEDATE = HIRE_DATE.
    ENDIF.
  ENDIF.
  IF 1 = 1.
    DATA:
      ABKRS TYPE ABKRS.

    PERFORM GETATTRIBUTE USING 'PR_AREA' '01' CHANGING TMPS.
    ABKRS      = TMPS.
    SORT T_HFP0001 ASCENDING BY BEGDA.
    LOOP AT T_HFP0001 INTO HFP0001.
****I_KONAKOV - changed to include PArea '99' into dates
***      if hfp0001-abkrs = abkrs.
      IF HFP0001-ABKRS = ABKRS OR HFP0001-ABKRS = '99'.
****I_KONAKOV - end of change
        IF HFP0001-BEGDA > EFFECTIVEDATE.
          WRITE: / 'Effective date (', EFFECTIVEDATE,
                   ') set to IT0001 record (', HFP0001-BEGDA, ')'.
          EFFECTIVEDATE = HFP0001-BEGDA.
        ENDIF.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.


*
* Check whether it makes sense to calc and print
*
  IF <GTHISINFTY> IS INITIAL.
    FORMAT COLOR COL_NEGATIVE.
    IF NOT PDOACTT IS INITIAL.
      WRITE: / 'No actions for', PACTT, '/', PACTR, 'found!'.
    ELSE.
      WRITE: / 'No infotype', 'found at', PSDATE.
    ENDIF.
    FORMAT COLOR OFF.
  ELSE.
    THISPERIOD = EFFECTIVEDATE(6).
    PREVPERIOD = THISPERIOD - 1.
    IF PREVPERIOD+4(2) = '00'.
      PREVPERIOD(4) = PREVPERIOD(4) - 1.
      PREVPERIOD+4(2) = '12'.
    ENDIF.

*
* Some information
*
    SKIP.
    IF <GTHISINFTY> IS INITIAL.
      WRITE: / 'No current infotype was found.'.
    ELSE.
      WRITE: / 'A current infotype was found (', THISPERIOD, ').'.
    ENDIF.
    IF <GPREVINFTY> IS INITIAL.
      WRITE: / 'No previous infotype was found.'.
    ELSE.
      WRITE: / 'A previous infotype was found (', PREVPERIOD, ').'.
    ENDIF.
    WRITE: / 'The effective date is:', EFFECTIVEDATE.
    WRITE: / 'The from      date is:', FROMDATE.
    SKIP.

*
* List of fileds to be shown during column blank out
*
    PERFORM GETATTRIBUTE
      USING 'DISPBLINES' 'F1F,F1T,F2F,F2T,F3F,F3T'
      CHANGING TMPS.
    SPLIT TMPS AT ',' INTO TABLE DISPBLINES.

*
* Determine 'off' phases
*
    PERFORM GETATTRIBUTE USING 'PR_OFFMASSN' '09' CHANGING TMPS.
    IF NOT TMPS IS INITIAL.
      PERFORM DETERMINEOFFPHASES
        USING CURRPERNR FROMDATE EFFECTIVEDATE.
    ENDIF.

*
* Run payroll
*
    PERFORM RUNRPCALC USING CURRPERNR THISPERIOD.
    SKIP.


* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
*
*
* Output
*
*
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    IF DEBUGLEVEL = 0.
* get master data
      PERFORM GETP0001
        USING    PERNR FROMDATE EFFECTIVEDATE.
      PERFORM GETP0002
        USING    PERNR FROMDATE EFFECTIVEDATE.
      PERFORM GETP0008
        USING    PERNR FROMDATE EFFECTIVEDATE.
      PERFORM GETCONTRACT
        USING    PERNR FROMDATE EFFECTIVEDATE.
      PERFORM GETP0167
        USING    PERNR FROMDATE EFFECTIVEDATE.
* insert 24.08.2006
      PERFORM GETP0021
        USING    PERNR FROMDATE EFFECTIVEDATE.
* end insert 24.08.2006

* insert 14.09.2006
      PERFORM GETP0007
        USING    PERNR FROMDATE EFFECTIVEDATE.
* end insert 14.09.2006



* determine P.A. or P.M.
      DATA:
        PA_EMP TYPE STRING,
        PA_CON TYPE STRING.

****I_KONAKOV - 2 lines commented until future decision on the reason of assignment of '1'
***      salperiodb = 1.
***      salperioda = 1.
****I_KONAKOV - end of commented block
      PERFORM GETATTRIBUTE USING 'PANN_EMP' '*1SR*2SR' CHANGING PA_EMP.
      CONCATENATE '*' PERSGB PERSKB INTO TMPS.
      FIND TMPS IN PA_EMP.
      IF SY-SUBRC = 0.
        SALPERIODB = 12.
      ENDIF.
      CONCATENATE '*' PERSGA PERSKA INTO TMPS.
      FIND TMPS IN PA_EMP.
      IF SY-SUBRC = 0.
        SALPERIODA = 12.
      ENDIF.

      PERFORM GETATTRIBUTE USING 'PANN_CON' '*01*02*03*06'
        CHANGING PA_CON.
      CONCATENATE '*' CTTYPB INTO TMPS.
      FIND TMPS IN PA_CON.
      IF SY-SUBRC = 0.
        SALPERIODB = 12.
      ENDIF.
      CONCATENATE '*' CTTYPA INTO TMPS.
      FIND TMPS IN PA_CON.
      IF SY-SUBRC = 0.
        SALPERIODA = 12.
      ENDIF.

* Head
      PERFORM GETBTRTLTEXT USING WERKSA BTRTLA
        CHANGING COL1.
      PERFORM GETPERSGTEXT USING PA0001-PERSG
        CHANGING COL2.
      CONCATENATE COL1 COL2 INTO COL1 SEPARATED BY SPACE.
*    perform mkEntry using 'F1' col1.
      PERFORM MKENTRY USING 'F1' COL2.

*    concatenate pa0001-ename ' Number:' pernr
*      into col1 separated by space.
*    perform mkEntry using 'F2' col1.
      PERFORM MKENTRY USING 'F2' PA0001-ENAME.
      PERFORM MKENTRY USING 'F3' PERNR.

****I_KONAKOV - clear col1 before procedure
      CLEAR COL1.
****
      PERFORM GETNATIOTEXT USING NATIOA CHANGING COL1.
      PERFORM MKENTRY USING 'F4' COL1.

****I_KONAKOV - create variable for home city
      DATA: W_HCITY(25).
      PERFORM GETHOMESTATION
        USING CURRPERNR EFFECTIVEDATE
****I_KONAKOV - added parameter w_hcity
        CHANGING NATIOA W_HCITY.
      PERFORM GETNATIOTEXTLANDX USING NATIOA CHANGING HOMESTATION.
****I_KONAKOV - insert line to concatenate home city & country
      CONCATENATE W_HCITY '/' HOMESTATION INTO HOMESTATION.
      PERFORM MKENTRY USING 'F5' HOMESTATION.

      PERFORM MKENTRY USING 'F6' NATOFACT.
****I_KONAKOV - insert line for reason of action
      PERFORM MKENTRY USING 'ROA' REASOFACT.
      PERFORM FMTDATE USING EFFECTIVEDATE CHANGING COL2.
      PERFORM MKENTRY USING 'F7' COL2.


*** From/to columns

* position
      PERFORM GETPOSITIONTEXT
        USING PLANSB FROMDATE CHANGING COL1.
      PERFORM MKENTRY USING 'F1F' COL1.
      PERFORM GETPOSITIONTEXT
        USING PLANSA EFFECTIVEDATE CHANGING COL2.
      PERFORM MKENTRY USING 'F1T' COL2.

* contract
****I_KONAKOV - change to separate contract type and expiry date
****New fields - F2FD & F2TD
***      perform getcontracttext using cttypb changing col1.
***      perform fmtdate using begdab changing tmps.
***      perform fmtdate using ctedtb changing tmps2.
***      if ctedtb is initial.
***        concatenate col1 'From' tmps
***          into col1 separated by space.
***      else.
***        concatenate col1 'From' tmps 'to' tmps2
***          into col1 separated by space.
***      endif.
***      perform mkentry using 'F2F' col1.
***
***      perform getcontracttext using cttypa changing col2.
***      perform fmtdate using begdaa changing tmps.
***      perform fmtdate using ctedta changing tmps2.
***      if ctedta is initial.
***        concatenate col2 'From' tmps
***          into col2 separated by space.
***      else.
***        concatenate col2 'From' tmps 'to' tmps2
***          into col2 separated by space.
***      endif.
***      perform mkentry using 'F2T' col2.

      PERFORM GETCONTRACTTEXT USING CTTYPB CHANGING COL1.
      PERFORM FMTDATE USING CTEDTB CHANGING TMPS2.
      PERFORM MKENTRY USING 'F2F' COL1.
      PERFORM MKENTRY USING 'CDF' TMPS2.

      PERFORM GETCONTRACTTEXT USING CTTYPA CHANGING COL2.
      PERFORM FMTDATE USING CTEDTA CHANGING TMPS2.
      PERFORM MKENTRY USING 'F2T' COL2.
      PERFORM MKENTRY USING 'CDT' TMPS2.
****I_KONAKOV - end of change

* grade & step
      CONCATENATE TRFGRB '/' TRFSTB INTO COL1.
      PERFORM MKENTRY USING 'F3F' COL1.
      CONCATENATE TRFGRA '/' TRFSTA INTO COL2.
      PERFORM MKENTRY USING 'F3T' COL2.

* next adv.
      PERFORM FMTDATE USING STVORB CHANGING COL1.
      IF SALPERIODB <> 12.
        CLEAR COL1.
      ENDIF.
      PERFORM MKENTRY USING 'F4F' COL1.
      PERFORM FMTDATE USING STVORA CHANGING COL2.
      IF SALPERIODA <> 12.
        CLEAR COL2.
      ENDIF.
      PERFORM MKENTRY USING 'F4T' COL2.

* base salary
      PERFORM GETWTSP USING 'BASE' CHANGING COL1 COL2.
* insert 24.08.2006
      IF TRFGRB(1) = 'P' OR TRFGRB(1) = 'D'.
        CONCATENATE COL1 ' (' RATEA ')' INTO COL1.
      ENDIF.
      IF TRFGRA(1) = 'P' OR TRFGRA(1) = 'D'.
        CONCATENATE COL2 ' (' RATEB ')' INTO COL2.
      ENDIF.
* end insert 24.08.2006
      PERFORM MKENTRY USING 'F5F' COL1.
      PERFORM MKENTRY USING 'F5T' COL2.
****I_KONAKOV - insert a field for 'P.M.' string
      PERFORM MKENTRY USING 'F5P' W_PMPA.
*teststart
**      clear w_line.
**      w_line = 'Net base salary'.
**      w_line+57 = '|'.
**      w_line+80 = col1.
**      w_line+120 = col2.
**      perform mkentry using 'BSL' w_line.
*testend
* pensionale salary
      PERFORM GETWTSP USING 'PENS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'F6F' COL1.
      PERFORM MKENTRY USING 'F6T' COL2.

* post adjustment
      PERFORM GETWTSP USING 'POST' CHANGING COL1 COL2.
* insert 23.08.2006
      DATA: DSTAT TYPE PUN_DSTAT,
            PRZ   TYPE PUN_PAMUL,
            PRZ2  TYPE STRING.
      PERFORM GETDSTAT USING CURRPERNR FROMDATE CHANGING DSTAT.
      PERFORM GETPRCPOST USING DSTAT TRFKZ FROMDATE CHANGING PRZ.
      PERFORM FMTPRZ USING PRZ CHANGING PRZ2.
      CONCATENATE COL1 ' (mult. ' PRZ2 ')' INTO COL1.
* end insert 23.08.2006
      PERFORM MKENTRY USING 'F7F' COL1.
* insert 23.08.2006
      PERFORM GETDSTAT USING CURRPERNR EFFECTIVEDATE CHANGING DSTAT.
      PERFORM GETPRCPOST USING DSTAT TRFKZ EFFECTIVEDATE CHANGING PRZ.
      PERFORM FMTPRZ USING PRZ CHANGING PRZ2.
      CONCATENATE COL2 ' (mult. ' PRZ2 ')' INTO COL2.
* end insert 23.08.2006
      PERFORM MKENTRY USING 'F7T' COL2.
****I_KONAKOV - insert a field for 'P.M.' string
      PERFORM MKENTRY USING 'F7P' W_PMPA.

* mob. & hardship allowance
      PERFORM GETWTSP USING 'MHAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'F8F' COL1.
      PERFORM MKENTRY USING 'F8T' COL2.
****I_KONAKOV - insert a field for 'P.M.' string
      PERFORM MKENTRY USING 'F8P' W_PMPA.

* assignment grant
      PERFORM GETASSIGNMENTGRANT USING CURRPERNR EFFECTIVEDATE
        CHANGING BETB BETA.
      PERFORM FMTBETRGP USING BETB 'b' CHANGING COL1.
      PERFORM FMTBETRGP USING BETA 'a' CHANGING COL2.
      IF 1 = 1.
        CONCATENATE LRUWAERSB COL1 INTO COL1 SEPARATED BY SPACE.
        CONCATENATE LRUWAERSA COL2 INTO COL2 SEPARATED BY SPACE.
      ENDIF.
      PERFORM MKENTRY USING 'F9F' COL1.
      PERFORM MKENTRY USING 'F9T' COL2.

* family allowance
      DATA:
        SPALB  TYPE MAXBT,
        SPALA  TYPE MAXBT.
      PERFORM GETWT USING 'SPAL' CHANGING SPALB SPALA.
      PERFORM GETWT USING 'CHAL' CHANGING BETB BETA.
****I_KONAKOV - insert
      DATA: W_CHALF TYPE MAXBT,
            W_CHALT TYPE MAXBT,
            W_SPALF TYPE MAXBT,
            W_SPALT TYPE MAXBT.
      W_CHALF = BETB.
      W_CHALT = BETA.
      W_SPALF = SPALB.
      W_SPALT = SPALA.
****I_KONAKOV - end of insert
      ADD SPALB TO BETB.
      ADD SPALA TO BETA.
      PERFORM FMTBETRGP USING BETB 'b' CHANGING COL1.
      PERFORM FMTBETRGP USING BETA 'a' CHANGING COL2.
      IF 1 = 1.
        CONCATENATE LRUWAERSB COL1 INTO COL1 SEPARATED BY SPACE.
        CONCATENATE LRUWAERSA COL2 INTO COL2 SEPARATED BY SPACE.
      ENDIF.
      PERFORM MKENTRY USING 'TF' COL1.
      PERFORM MKENTRY USING 'TT' COL2.

* insert 03.10.2006
* work percentage
      PERFORM FMTPRZ USING EMPCTB CHANGING COL1.
      PERFORM FMTPRZ USING EMPCTA CHANGING COL2.
      PERFORM MKENTRY USING 'WPF' COL1.
      PERFORM MKENTRY USING 'WPT' COL2.

* special allowance
      PERFORM GETWTSP USING 'SALW' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SAF' COL1.
      PERFORM MKENTRY USING 'SAT' COL2.

* rental subsidy
      PERFORM GETWTSP USING 'RSAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'RSF' COL1.
      PERFORM MKENTRY USING 'RST' COL2.

* educational grant
      PERFORM GETWTSP USING 'EDUC' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'EGF' COL1.
      PERFORM MKENTRY USING 'EGT' COL2.

* interim allowance
      PERFORM GETWTSP USING 'HDAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'IAF' COL1.
      PERFORM MKENTRY USING 'IAT' COL2.

* language allowance
      PERFORM GETWTSP USING 'LAAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'LAF' COL1.
      PERFORM MKENTRY USING 'LAT' COL2.

* secondary dependent
      PERFORM GETWTSP USING 'DPAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SDF' COL1.
      PERFORM MKENTRY USING 'SDT' COL2.
****I_KONAKOV - insert a field for 'P.M.' string
      PERFORM MKENTRY USING 'SDP' W_PMPA.
* end insert 03.10.2006

* Contr. Staff member (SM) health ins.
      PERFORM GETWTSP USING 'HISE' CHANGING COL1 COL2.
      PERFORM ISWTFILLED
        USING 'HISE'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        CONCATENATE COL1 'HI' INTO COL1 SEPARATED BY SPACE.
        IF DEPCVB = 'SM  '.
          IF BOPTIB = 'OPT1' OR BOPTIB = 'OPT3' OR BOPTIB = 'OPT4'.
            CONCATENATE COL1 'SHARED' INTO COL1 SEPARATED BY SPACE.
          ENDIF.
          IF BOPTIB = 'OPT2' OR BOPTIB = 'OPT5'.
            CONCATENATE COL1 'FULL' INTO COL1 SEPARATED BY SPACE.
          ENDIF.
        ENDIF.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        CONCATENATE COL2 'HI' INTO COL2 SEPARATED BY SPACE.
        IF DEPCVA = 'SM  '.
          IF BOPTIA = 'OPT1' OR BOPTIA = 'OPT3' OR BOPTIA = 'OPT4'.
            CONCATENATE COL2 'SHARED' INTO COL2 SEPARATED BY SPACE.
          ENDIF.
          IF BOPTIA = 'OPT2' OR BOPTIA = 'OPT5'.
            CONCATENATE COL2 'FULL' INTO COL2 SEPARATED BY SPACE.
          ENDIF.
        ENDIF.
      ENDIF.
      PERFORM ISWTFILLED
        USING 'HISE2'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        CONCATENATE COL1 'MSP' INTO COL1 SEPARATED BY SPACE.
        IF DEPCVB = 'SM'.
          IF BOPTIB = 'OPT1' OR BOPTIB = 'OPT3' OR BOPTIB = 'OPT4'.
            CONCATENATE COL1 'SHARED' INTO COL1 SEPARATED BY SPACE.
          ENDIF.
          IF BOPTIB = 'OPT2' OR BOPTIB = 'OPT5'.
            CONCATENATE COL1 'FULL' INTO COL1 SEPARATED BY SPACE.
          ENDIF.
        ENDIF.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        CONCATENATE COL2 'MSP' INTO COL2 SEPARATED BY SPACE.
        IF DEPCVA = 'SM'.
          IF BOPTIA = 'OPT1' OR BOPTIA = 'OPT3' OR BOPTIA = 'OPT4'.
            CONCATENATE COL2 'SHARED' INTO COL2 SEPARATED BY SPACE.
          ENDIF.
          IF BOPTIA = 'OPT2' OR BOPTIA = 'OPT5'.
            CONCATENATE COL2 'FULL' INTO COL2 SEPARATED BY SPACE.
          ENDIF.
        ENDIF.
      ENDIF.
      PERFORM MKENTRY USING 'UF' COL1.
      PERFORM MKENTRY USING 'UT' COL2.

* Contr. Dep. health ins.
      PERFORM GETWTSP USING 'HIDE' CHANGING COL1 COL2.
      PERFORM ISWTFILLED
        USING 'HIDE'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        CONCATENATE COL1 'HI' INTO COL1 SEPARATED BY SPACE.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        CONCATENATE COL2 'HI' INTO COL2 SEPARATED BY SPACE.
      ENDIF.
      PERFORM ISWTFILLED
        USING 'HIDE2'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        CONCATENATE COL1 'MSP' INTO COL1 SEPARATED BY SPACE.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        CONCATENATE COL2 'MSP' INTO COL2 SEPARATED BY SPACE.
      ENDIF.

* insert 24.08.2006
      IF NOT HIDSSHAREA IS INITIAL OR NOT HIDCSHAREA IS INITIAL.
        CONCATENATE COL1 ' SHARED' INTO COL1.
        IF NOT HIDSSHAREA IS INITIAL.
          PERFORM FMTPRZ2 USING HIDSSHAREA CHANGING PRZ2.
          CONCATENATE COL1 ' (' PRZ2 '-Spouse)' INTO COL1.
        ENDIF.
        IF NOT HIDCSHAREA IS INITIAL.
          PERFORM FMTPRZ2 USING HIDCSHAREA CHANGING PRZ2.
          CONCATENATE COL1 ' (' PRZ2 '-child)' INTO COL1.
        ENDIF.
      ENDIF.
      IF NOT HIDSFULLA IS INITIAL OR NOT HIDCFULLA IS INITIAL.
        CONCATENATE COL1 ' FULL' INTO COL1.
        IF NOT HIDSFULLA IS INITIAL.
          PERFORM FMTPRZ2 USING HIDSFULLA CHANGING PRZ2.
          CONCATENATE COL1 ' (' PRZ2 '-Spouse)' INTO COL1.
        ENDIF.
        IF NOT HIDCFULLA IS INITIAL.
          PERFORM FMTPRZ2 USING HIDCFULLA CHANGING PRZ2.
          CONCATENATE COL1 ' (' PRZ2 '-child)' INTO COL1.
        ENDIF.
      ENDIF.
      IF NOT HIDSSHAREB IS INITIAL OR NOT HIDCSHAREB IS INITIAL.
        CONCATENATE COL2 ' SHARED' INTO COL2.
        IF NOT HIDSSHAREB IS INITIAL.
          PERFORM FMTPRZ2 USING HIDSSHAREB CHANGING PRZ2.
          CONCATENATE COL2 ' (' PRZ2 '-Spouse)' INTO COL2.
        ENDIF.
        IF NOT HIDCSHAREB IS INITIAL.
          PERFORM FMTPRZ2 USING HIDCSHAREB CHANGING PRZ2.
          CONCATENATE COL2 ' (' PRZ2 '-child)' INTO COL2.
        ENDIF.
      ENDIF.
      IF NOT HIDSFULLB IS INITIAL OR NOT HIDCFULLB IS INITIAL.
        CONCATENATE COL2 ' FULL' INTO COL2.
        IF NOT HIDSFULLB IS INITIAL.
          PERFORM FMTPRZ2 USING HIDSFULLB CHANGING PRZ2.
          CONCATENATE COL2 ' (' PRZ2 '-Spouse)' INTO COL2.
        ENDIF.
        IF NOT HIDCFULLB IS INITIAL.
          PERFORM FMTPRZ2 USING HIDCFULLB CHANGING PRZ2.
          CONCATENATE COL2 ' (' PRZ2 '-child)' INTO COL2.
        ENDIF.
      ENDIF.
* end insert 24.08.2006

      PERFORM MKENTRY USING 'VF' COL1.
      PERFORM MKENTRY USING 'VT' COL2.

* Contr. SM acc.ins.
      PERFORM GETWTSP USING 'ACIL' CHANGING COL1 COL2.
      PERFORM ISWTFILLED
        USING 'ACIL'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        CONCATENATE COL1 'AII' INTO COL1 SEPARATED BY SPACE.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        CONCATENATE COL2 'AII' INTO COL2 SEPARATED BY SPACE.
      ENDIF.
      PERFORM ISWTFILLED
        USING 'DSCP'
        CHANGING FILLEDB FILLEDA.
      IF NOT FILLEDB IS INITIAL.
        MOVE 'SCP' TO COL1.
      ENDIF.
      IF NOT FILLEDA IS INITIAL.
        MOVE 'SCP' TO COL2.
      ENDIF.
      PERFORM MKENTRY USING 'WF' COL1.
      PERFORM MKENTRY USING 'WT' COL2.

* provident fund
      PERFORM GETPROVIDENTFUND USING CURRPERNR EFFECTIVEDATE
        CHANGING BETB BETA.
      PERFORM FMTBETRGP USING BETB 'b' CHANGING COL1.
      PERFORM FMTBETRGP USING BETA 'a' CHANGING COL2.
      IF 1 = 1.
        CONCATENATE LRUWAERSB COL1 INTO COL1 SEPARATED BY SPACE.
        CONCATENATE LRUWAERSA COL2 INTO COL2 SEPARATED BY SPACE.
      ENDIF.
      PERFORM MKENTRY USING 'XF' COL1.
      PERFORM MKENTRY USING 'XT' COL2.

* department
* Isabelle
      PERFORM GETORGEHTEXT USING ORGEHB CHANGING COL1.
      PERFORM GETORGEHTEXT USING ORGEHA CHANGING COL2.
* Martine
* move : 23.08.2006
*data: dstat type pun_dstat.
* end move 23.08.2006
      PERFORM GETDSTAT USING CURRPERNR FROMDATE CHANGING DSTAT.
      PERFORM GETDSTXT USING DSTAT CHANGING COL1.
      PERFORM GETDSTAT USING CURRPERNR EFFECTIVEDATE CHANGING DSTAT.
      PERFORM GETDSTXT USING DSTAT CHANGING COL2.
      PERFORM MKENTRY USING 'YF' COL1.
      PERFORM MKENTRY USING 'YT' COL2.

* location
* Isabelle
      PERFORM GETBTRTLTEXT USING PA0001-WERKS BTRTLB
        CHANGING COL1.
      PERFORM GETBTRTLTEXT USING PA0001-WERKS BTRTLA
        CHANGING COL2.
* Martine
      PERFORM GETDSTAT USING CURRPERNR FROMDATE CHANGING DSTAT.
      PERFORM GETDSCOUNTRY USING DSTAT CHANGING COL1.
      PERFORM GETDSTAT USING CURRPERNR EFFECTIVEDATE CHANGING DSTAT.
      PERFORM GETDSCOUNTRY USING DSTAT CHANGING COL2.
      PERFORM MKENTRY USING 'ZF' COL1.
      PERFORM MKENTRY USING 'ZT' COL2.

* Remarks
*    concatenate prem01 prem02 prem03
*      prem04 prem05 prem06 prem07
*      into col1 separated by space.
*    perform mkEntry using 'FR1' col1.
****I_KONAKOV - print "Remarks:" as R0 remark
      DATA: W_PREM0(10).
      CLEAR W_PREM0.
      IF PREM01 <> SPACE OR
         PREM02 <> SPACE OR
         PREM03 <> SPACE OR
         PREM04 <> SPACE OR
         PREM05 <> SPACE OR
         PREM06 <> SPACE OR
         PREM07 <> SPACE.
        W_PREM0 = 'Remarks:'.
      ENDIF. "prem
      PERFORM MKENTRY USING 'R0' W_PREM0.
****I_KONAKOV
      PERFORM MKENTRY USING 'R1' PREM01.
      PERFORM MKENTRY USING 'R2' PREM02.
      PERFORM MKENTRY USING 'R3' PREM03.
      PERFORM MKENTRY USING 'R4' PREM04.
      PERFORM MKENTRY USING 'R5' PREM05.
      PERFORM MKENTRY USING 'R6' PREM06.
      PERFORM MKENTRY USING 'R7' PREM07.

* Date and Id
      PERFORM FMTDATE USING SY-DATUM CHANGING COL1.
*    concatenate col1 '                   ' pid
*      into col1 separated by space.
* insert 14.09.2006
****I_KONAKOV - line commented
***      concatenate col1 pa_admin into col1 separated by '/'.
* end insert 14.09.2006
      PERFORM MKENTRY USING 'FD' COL1.
****I_KONAKOV - change user id to user full name
***      perform mkentry using 'FI' pid.
TABLES: USR21, ADRP.
      CLEAR USR21.
      SELECT SINGLE * FROM USR21 WHERE BNAME = PID.
      CLEAR ADRP.
      SELECT SINGLE * FROM ADRP WHERE PERSNUMBER = USR21-PERSNUMBER.
      PERFORM MKENTRY USING 'FI' ADRP-NAME_TEXT.
****I_KONAKOV - end of insert

* Project/funding/Cost
      PERFORM GETCOSTDISTR
        TABLES   LINES
        USING    PERNR FROMDATE
        CHANGING COL1 COL2 COL3 COL4.
      PERFORM MKENTRY USING 'P1F' COL1.
      PERFORM MKENTRY USING 'Q1F' COL2.
      PERFORM GETCOSTDISTR
        TABLES   LINES
        USING    PERNR EFFECTIVEDATE
        CHANGING COL1 COL2 COL3 COL4.
      PERFORM MKENTRY USING 'P1T' COL3.
      PERFORM MKENTRY USING 'Q1T' COL4.

****I_KONAKOV - PF number
      DATA:
        W_PA0961  TYPE PA0961.

      CLEAR W_PA0961.
      SELECT *
        FROM PA0961
        INTO W_PA0961
        WHERE PERNR = CURRPERNR
          AND BEGDA <= EFFECTIVEDATE
          AND ENDDA >= EFFECTIVEDATE.
      ENDSELECT. "pa0961
      PERFORM MKENTRY USING 'PFN' W_PA0961-PFNUM.
****I_KONAKOV - end of insert

****I_KONAKOV - get Gross base salary
      PERFORM GETWTSP USING 'GBAS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'GSF' COL1.
      PERFORM MKENTRY USING 'GST' COL2.
      PERFORM MKENTRY USING 'GSP' W_PMPA.
*to test
**      clear w_line.
**      w_line = 'Gross base salary'.
**      w_line+57 = '|'.
**      w_line+80 = col1.
**      w_line+120 = col2.
**      perform mkentry using 'GSL' w_line.
*test end
****I_KONAKOV - end of insert

****I_KONAKOV - Child allowance
      PERFORM FMTBETRGP USING W_CHALF 'b' CHANGING COL1.
      PERFORM FMTBETRGP USING W_CHALT 'a' CHANGING COL2.
      CONCATENATE LRUWAERSB COL1 INTO COL1 SEPARATED BY SPACE.
      CONCATENATE LRUWAERSA COL2 INTO COL2 SEPARATED BY SPACE.
      PERFORM MKENTRY USING 'CAF' COL1.
      PERFORM MKENTRY USING 'CAT' COL2.
      PERFORM MKENTRY USING 'CAP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - get Rental subsidy
      PERFORM GETWTSP USING 'RNTS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'RNF' COL1.
      PERFORM MKENTRY USING 'RNT' COL2.
      PERFORM MKENTRY USING 'RNP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Spouse allowance
      PERFORM FMTBETRGP USING W_SPALF 'b' CHANGING COL1.
      PERFORM FMTBETRGP USING W_SPALT 'a' CHANGING COL2.
      CONCATENATE LRUWAERSB COL1 INTO COL1 SEPARATED BY SPACE.
      CONCATENATE LRUWAERSA COL2 INTO COL2 SEPARATED BY SPACE.
      PERFORM MKENTRY USING 'SPF' COL1.
      PERFORM MKENTRY USING 'SPT' COL2.
      PERFORM MKENTRY USING 'SPP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - get Pension contribution
      PERFORM GETWTSP USING 'PENC' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'PCF' COL1.
      PERFORM MKENTRY USING 'PCT' COL2.
      PERFORM MKENTRY USING 'PCP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - get MBF contribution
      PERFORM GETWTSP USING 'MBFC' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'MFF' COL1.
      PERFORM MKENTRY USING 'MFT' COL2.
      PERFORM MKENTRY USING 'MFP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Other sources allowance
      PERFORM GETWTSP USING 'OSAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'OSF' COL1.
      PERFORM MKENTRY USING 'OST' COL2.
      PERFORM MKENTRY USING 'OSP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Not resident's allowance
      PERFORM GETWTSP USING 'NRAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'NRF' COL1.
      PERFORM MKENTRY USING 'NRT' COL2.
      PERFORM MKENTRY USING 'NRP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Second language allowance
      PERFORM GETWTSP USING 'SLAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SLF' COL1.
      PERFORM MKENTRY USING 'SLT' COL2.
      PERFORM MKENTRY USING 'SLP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Service allowance
      PERFORM GETWTSP USING 'SEAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SEF' COL1.
      PERFORM MKENTRY USING 'SET' COL2.
      PERFORM MKENTRY USING 'SEP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Family allowance
      PERFORM GETWTSP USING 'FMAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'FMF' COL1.
      PERFORM MKENTRY USING 'FMT' COL2.
      PERFORM MKENTRY USING 'FMP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Representation allowance
      PERFORM GETWTSP USING 'RPAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'RPF' COL1.
      PERFORM MKENTRY USING 'RPT' COL2.
      PERFORM MKENTRY USING 'RPP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Transportation allowance
      PERFORM GETWTSP USING 'TRAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'TRF' COL1.
      PERFORM MKENTRY USING 'TRT' COL2.
      PERFORM MKENTRY USING 'TRP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Spec. pers. non-pensionable allowance
      PERFORM GETWTSP USING 'SNAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SNF' COL1.
      PERFORM MKENTRY USING 'SNT' COL2.
      PERFORM MKENTRY USING 'SNP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Pers. transitional allowance
      PERFORM GETWTSP USING 'PTAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'PTF' COL1.
      PERFORM MKENTRY USING 'PTT' COL2.
      PERFORM MKENTRY USING 'PTP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Assignment grant (DSA)
      PERFORM GETWTSP USING 'AGDS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'AGF' COL1.
      PERFORM MKENTRY USING 'AGT' COL2.
      PERFORM MKENTRY USING 'AGP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Assignment grant (lump sum)
      PERFORM GETWTSP USING 'AGLS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'ALF' COL1.
      PERFORM MKENTRY USING 'ALT' COL2.
      PERFORM MKENTRY USING 'ALP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Second language allowance
      PERFORM GETWTSP USING 'RPGR' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'RGF' COL1.
      PERFORM MKENTRY USING 'RGT' COL2.
      PERFORM MKENTRY USING 'RGP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Repatriation grant
      PERFORM GETWTSP USING 'TMID' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'TIF' COL1.
      PERFORM MKENTRY USING 'TIT' COL2.
      PERFORM MKENTRY USING 'TIP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Death grant
      PERFORM GETWTSP USING 'DEGR' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'DGF' COL1.
      PERFORM MKENTRY USING 'DGT' COL2.
      PERFORM MKENTRY USING 'DGP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - In lieu of notice
      PERFORM GETWTSP USING 'ILON' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'ILF' COL1.
      PERFORM MKENTRY USING 'ILT' COL2.
      PERFORM MKENTRY USING 'ILP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Annual leave settlement
      PERFORM GETWTSP USING 'ANLS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'ANF' COL1.
      PERFORM MKENTRY USING 'ANT' COL2.
      PERFORM MKENTRY USING 'ANP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Hairdressing indemnity
      PERFORM GETWTSP USING 'HDID' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'HDF' COL1.
      PERFORM MKENTRY USING 'HDT' COL2.
      PERFORM MKENTRY USING 'HDP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Closing allowance
      PERFORM GETWTSP USING 'CLAL' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'CLF' COL1.
      PERFORM MKENTRY USING 'CLT' COL2.
      PERFORM MKENTRY USING 'CLP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Spec. post allowance
      PERFORM GETWTSP USING 'SPPA' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'PAF' COL1.
      PERFORM MKENTRY USING 'PAT' COL2.
      PERFORM MKENTRY USING 'PAP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Deduction for housing provided
      PERFORM GETWTSP USING 'DDHP' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'DHF' COL1.
      PERFORM MKENTRY USING 'DHT' COL2.
      PERFORM MKENTRY USING 'DHP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Deduction - social security
      PERFORM GETWTSP USING 'DDSS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'SSF' COL1.
      PERFORM MKENTRY USING 'SST' COL2.
      PERFORM MKENTRY USING 'SSP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - Lloyd insurance
      PERFORM GETWTSP USING 'LLIS' CHANGING COL1 COL2.
      PERFORM MKENTRY USING 'LLF' COL1.
      PERFORM MKENTRY USING 'LLT' COL2.
      PERFORM MKENTRY USING 'LLP' W_PMPA.
****I_KONAKOV - end of insert

****I_KONAKOV - get birthdate
      DATA: W_BIRTHDATE(10),
            W_PA0002 TYPE PA0002.

      SELECT *
        FROM PA0002
        INTO W_PA0002
        WHERE PERNR = CURRPERNR
          AND ENDDA >= EFFECTIVEDATE
          AND BEGDA <= EFFECTIVEDATE.
      ENDSELECT. "pa0002
      WRITE W_PA0002-GBDAT TO W_BIRTHDATE.
      PERFORM MKENTRY USING 'BDA' W_BIRTHDATE.
****I_KONAKOV - end of insert

****I_KONAKOV - get internal mailing address
      DATA: W_PA0006 TYPE PA0006.

      CLEAR W_PA0006.
      SELECT *
            FROM PA0006
            INTO W_PA0006
            WHERE PERNR = CURRPERNR
              AND SUBTY = '6'
              AND ENDDA >= PSDATE
              AND BEGDA <= PSDATE.
        EXIT.
      ENDSELECT. "pa0006
      PERFORM MKENTRY USING 'IMA' W_PA0006-STRAS.
****I_KONAKOV - end of insert

****I_KONAKOV - get UNESCO and UN entry date
      DATA: W_PA0041 TYPE PA0041,
            W_DT(2) TYPE N,
            W_DTYPE41(15),
            W_DATE41(15),
            W_UNDATEF(10),
            W_UNDATET(10),
            W_UNESCODATEF(10),
            W_UNESCODATET(10).

      FIELD-SYMBOLS: <FS_DTYPE41>,
                     <FS_DATE41>.

      CLEAR W_PA0041.
      SELECT *
            FROM PA0041
            INTO W_PA0041
            WHERE PERNR = CURRPERNR.
        IF W_PA0041-BEGDA <= FROMDATE AND W_PA0041-ENDDA >= FROMDATE.
          W_DT = '01'.
          DO.
            CONCATENATE 'W_PA0041-DAR' W_DT INTO W_DTYPE41.
            ASSIGN (W_DTYPE41) TO <FS_DTYPE41>.
            CONCATENATE 'W_PA0041-DAT' W_DT INTO W_DATE41.
            ASSIGN (W_DATE41) TO <FS_DATE41>.
            CASE <FS_DTYPE41>.
              WHEN '01'.
                WRITE <FS_DATE41> TO W_UNDATEF.
              WHEN '06'.
                WRITE <FS_DATE41> TO W_UNESCODATEF.
              WHEN OTHERS.
            ENDCASE.
            IF W_DT = '12'.
              EXIT.
            ENDIF. "w_dt
            W_DT = W_DT + 1.
          ENDDO.
        ENDIF. "fromdate

        IF W_PA0041-BEGDA <= EFFECTIVEDATE AND W_PA0041-ENDDA >= EFFECTIVEDATE.
          W_DT = '01'.
          DO.
            CONCATENATE 'W_PA0041-DAR' W_DT INTO W_DTYPE41.
            ASSIGN (W_DTYPE41) TO <FS_DTYPE41>.
            CONCATENATE 'W_PA0041-DAT' W_DT INTO W_DATE41.
            ASSIGN (W_DATE41) TO <FS_DATE41>.
            CASE <FS_DTYPE41>.
              WHEN '01'.
                WRITE <FS_DATE41> TO W_UNDATET.
              WHEN '06'.
                WRITE <FS_DATE41> TO W_UNESCODATET.
              WHEN OTHERS.
            ENDCASE.
            IF W_DT = '12'.
              EXIT.
            ENDIF. "w_dt
            W_DT = W_DT + 1.
          ENDDO.
        ENDIF. "todate
      ENDSELECT. "pa0041

      PERFORM MKENTRY USING 'UDF' W_UNESCODATEF.
      PERFORM MKENTRY USING 'UDT' W_UNESCODATET.
      PERFORM MKENTRY USING 'UNF' W_UNDATEF.
      PERFORM MKENTRY USING 'UNT' W_UNDATET.
****I_KONAKOV - end of insert

****I_KONAKOV - Duty station
      DATA: W_PATXT LIKE T500P-NAME1,
            W_SATXT LIKE T001P-BTEXT,
            W_DUTYSTAT TYPE CHAR50.

      CLEAR: W_PATXT, W_SATXT, W_DUTYSTAT.
      SELECT SINGLE NAME1 INTO W_PATXT FROM T500P WHERE PERSA = WERKSB.
      SELECT SINGLE BTEXT INTO W_SATXT FROM T001P WHERE WERKS = WERKSB AND BTRTL = BTRTLB.
      CONCATENATE W_SATXT '/' W_PATXT INTO W_DUTYSTAT.
      PERFORM MKENTRY USING 'DSF' W_DUTYSTAT.

      CLEAR: W_PATXT, W_SATXT, W_DUTYSTAT.
      SELECT SINGLE NAME1 INTO W_PATXT FROM T500P WHERE PERSA = WERKSA.
      SELECT SINGLE BTEXT INTO W_SATXT FROM T001P WHERE WERKS = WERKSA AND BTRTL = BTRTLA.
      CONCATENATE W_SATXT '/' W_PATXT INTO W_DUTYSTAT.
      PERFORM MKENTRY USING 'DST' W_DUTYSTAT.
****I_KONAKOV - end of insert

****I_KONAKOV - Administrative duty station
      DATA: W_PA0395 TYPE PA0395.

      CLEAR: W_PA0395, W_PATXT, W_SATXT, W_DUTYSTAT.
      SELECT * FROM PA0395 INTO W_PA0395
            WHERE PERNR = CURRPERNR
              AND ENDDA >= FROMDATE
              AND BEGDA <= FROMDATE.
      ENDSELECT. "pa0395
      IF SY-SUBRC = 0.
        SELECT SINGLE NAME1 INTO W_PATXT FROM T500P WHERE PERSA = W_PA0395-WERKS.
        SELECT SINGLE BTEXT INTO W_SATXT FROM T001P WHERE WERKS = W_PA0395-WERKS AND BTRTL = W_PA0395-BTRTL.
        CONCATENATE W_SATXT '/' W_PATXT INTO W_DUTYSTAT.
      ENDIF. "sy-subrc
      PERFORM MKENTRY USING 'ADF' W_DUTYSTAT.

      CLEAR: W_PA0395, W_PATXT, W_SATXT, W_DUTYSTAT.
      SELECT * FROM PA0395 INTO W_PA0395
            WHERE PERNR = CURRPERNR
              AND ENDDA >= EFFECTIVEDATE
              AND BEGDA <= EFFECTIVEDATE.
      ENDSELECT. "pa0395
      IF SY-SUBRC = 0.
        SELECT SINGLE NAME1 INTO W_PATXT FROM T500P WHERE PERSA = W_PA0395-WERKS.
        SELECT SINGLE BTEXT INTO W_SATXT FROM T001P WHERE WERKS = W_PA0395-WERKS AND BTRTL = W_PA0395-BTRTL.
        CONCATENATE W_SATXT '/' W_PATXT INTO W_DUTYSTAT.
      ENDIF. "sy-subrc
      PERFORM MKENTRY USING 'ADT' W_DUTYSTAT.
****I_KONAKOV - end of insert

****I_KONAKOV - Org. unit
      PERFORM GETORGEHTEXT USING ORGEHB CHANGING COL1.
      PERFORM MKENTRY USING 'OUF' COL1.
      PERFORM GETORGEHTEXT USING ORGEHA CHANGING COL2.
      PERFORM MKENTRY USING 'OUT' COL2.
****I_KONAKOV - end of insert

****I_KONAKOV - Post number
      DATA: W_POSTNUM(12).

      CLEAR W_POSTNUM.
      CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
        EXPORTING
          OTYPE                         = 'S'
          OBJID                         = PLANSB
*         STATUS                        = '1'
          REFERENCE_DATE                = FROMDATE
*         LANGU                         = SY-LANGU
       IMPORTING
          SHORT_TEXT                    = W_POSTNUM
*         OBJECT_TEXT                   =
*         COSTCENTER_NAME               =
*         INTEGRATION_ACTIVE            =
*         RETURN                        =
       EXCEPTIONS
         NOTHING_FOUND                 = 1
         WRONG_OBJECTTYPE              = 2
         MISSING_COSTCENTER_DATA       = 3
         MISSING_OBJECT_ID             = 4
         OTHERS                        = 5
                .
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.
      PERFORM MKENTRY USING 'PNF' W_POSTNUM.

      CLEAR W_POSTNUM.
      CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
        EXPORTING
          OTYPE                         = 'S'
          OBJID                         = PLANSA
*         STATUS                        = '1'
          REFERENCE_DATE                = EFFECTIVEDATE
*         LANGU                         = SY-LANGU
       IMPORTING
          SHORT_TEXT                    = W_POSTNUM
*         OBJECT_TEXT                   =
*         COSTCENTER_NAME               =
*         INTEGRATION_ACTIVE            =
*         RETURN                        =
       EXCEPTIONS
         NOTHING_FOUND                 = 1
         WRONG_OBJECTTYPE              = 2
         MISSING_COSTCENTER_DATA       = 3
         MISSING_OBJECT_ID             = 4
         OTHERS                        = 5
                .
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.
      PERFORM MKENTRY USING 'PNT' W_POSTNUM.
****I_KONAKOV - end of insert

****I_KONAKOV - automatic texts
      DATA: W_ATEXT(200),
            W_RNTSF LIKE BETB,
            W_RNTST LIKE BETA.

      CLEAR W_ATEXT.
      IF NOT ( W_CHALT IS INITIAL ). "for Children allowance
        SELECT SINGLE ATEXT FROM YHR_PAFTXT INTO W_ATEXT
              WHERE TXKEY = 'WT_CHAL'.
      ENDIF.
      PERFORM MKENTRY USING 'AT1' W_ATEXT.

      CLEAR W_ATEXT.
      IF NOT ( W_SPALT IS INITIAL ). "for Spouse allowance
        SELECT SINGLE ATEXT FROM YHR_PAFTXT INTO W_ATEXT
              WHERE TXKEY = 'WT_SPAL'.
      ENDIF.
      PERFORM MKENTRY USING 'AT2' W_ATEXT.

      CLEAR: W_ATEXT, W_RNTSF, W_RNTST.
      PERFORM GETWT USING 'RNTS' CHANGING W_RNTSF W_RNTST.
      IF NOT ( W_RNTST IS INITIAL ). "for Rental subsidy
        SELECT SINGLE ATEXT FROM YHR_PAFTXT INTO W_ATEXT
              WHERE TXKEY = 'WT_RNTS'.
      ENDIF.
      PERFORM MKENTRY USING 'AT3' W_ATEXT.

      CLEAR W_ATEXT.
      PERFORM MKENTRY USING 'AT4' W_ATEXT.
****I_KONAKOV - end of insert

****I_KONAKOV - create PAF document number or modify revision if exist
      DATA: W_PAFNUM TYPE YHR_PAFNUM,
            W_PAFNO(25).
      CLEAR W_PAFNUM.
      SELECT *
            FROM YHR_PAFNUM
            INTO W_PAFNUM
            WHERE PERNR = CURRPERNR
              AND ADATE = EFFECTIVEDATE.
      ENDSELECT.
      IF SY-SUBRC <> 0.
        CLEAR W_PAFNUM.
        SELECT *
              FROM YHR_PAFNUM
              INTO W_PAFNUM
              ORDER BY PAFNUM.
        ENDSELECT.
        W_PAFNUM-PAFNUM = W_PAFNUM-PAFNUM + 1.
        W_PAFNUM-PERNR = CURRPERNR.
        W_PAFNUM-ADATE = EFFECTIVEDATE.
        CLEAR W_PAFNUM-PAFREV.
        INSERT YHR_PAFNUM FROM W_PAFNUM.
       ELSE.
         W_PAFNUM-PAFREV = W_PAFNUM-PAFREV + 1.
         MODIFY YHR_PAFNUM FROM W_PAFNUM.
      ENDIF. "sy-subrc
      CLEAR W_PAFNO.
      W_PAFNO = W_PAFNUM-PAFNUM.
      PERFORM MKENTRY USING 'PDN' W_PAFNO.
      CLEAR W_PAFNO.
      IF NOT W_PAFNUM-PAFREV IS INITIAL.
        CONCATENATE 'rev. ' W_PAFNUM-PAFREV INTO W_PAFNO.
      ENDIF. "pafrev
      PERFORM MKENTRY USING 'PDR' W_PAFNO.
****I_KONAKOV - end of insert

*
* Generating output document

      PERFORM CREATEWORDFORMDOC
         USING LINES.

    ENDIF. "debugLevel = 0

  ENDIF.


*
* clean up
*
* Delete the temporary person
  IF DOPERMANENT IS INITIAL.
    IF NOT DELETEPERSON IS INITIAL.
      PERFORM DELETEPERSON
        USING CURRPERNR 'X' 'X'.
    ENDIF.
  ENDIF.

****I_KONAKOV - delete used pernr from (custtable)
  IF NOT W_CURRPN IS INITIAL.
    DELETE FROM (CUSTTABLE) WHERE ANAME = W_CURRPN.
    IF SY-SUBRC <> 0.
    ENDIF.
  ENDIF. "not w_currpn
****I_KONAKOV - end of insert
ENDFORM. " end of doProcessing



DATA:
  BEGIN OF TPA,
    MANDT TYPE MANDT.
        INCLUDE STRUCTURE PAKEY.
DATA:
    END OF TPA.
*
* Read an infotype at date and previous
*
FORM FETCHINFOTYPE
  USING
    PERSON     TYPE PERNR-PERNR
    INFOTYPE   TYPE PRELP-INFTY
    SDATE      TYPE PRELP-BEGDA
    ANDPREV    TYPE C
  CHANGING
    THISINFTY
    PREVINFTY.

  FIELD-SYMBOLS:
    <PT>           TYPE ANY.

  DATA:
*  tpa      type tpk,
    BEGDA    LIKE PA0000-BEGDA,
    STRUNAME TYPE STRING.

  CONCATENATE 'PA' INFOTYPE INTO STRUNAME.
  ASSIGN (STRUNAME) TO <PT>.

  CLEAR: THISINFTY, PREVINFTY.

* cannot use HR_READ_INFTY cause of the variable infotypes returned.
  SELECT * FROM (STRUNAME) INTO <PT>
    WHERE PERNR = PERSON
      AND BEGDA <= SDATE
      AND ENDDA >= SDATE.
    THISINFTY = <PT>.
    EXIT.
  ENDSELECT.
  IF THISINFTY IS INITIAL.
    WRITE: / 'No infotype', INFOTYPE,
             'for', PERSON, 'at', SDATE.
  ELSE.
    TPA            = THISINFTY.
    EFFECTIVEDATE  = TPA-BEGDA.
    FROMDATE       = EFFECTIVEDATE.
    SUBTRACT 1 FROM FROMDATE.
    THISPERIOD     = TPA-BEGDA(6).
    WRITE: / 'Curr. infotype', TPA-BEGDA, 'to', TPA-ENDDA.
    IF NOT ANDPREV IS INITIAL.
      SELECT * FROM (STRUNAME) INTO <PT>
          WHERE PERNR = PERSON
        AND BEGDA < EFFECTIVEDATE.
        PREVINFTY = <PT>.
      ENDSELECT.
      IF PREVINFTY IS INITIAL.
        WRITE: / 'No prev infotype', INFOTYPE,
               'for', PERSON, 'before', BEGDA.
      ELSE.
        TPA            = PREVINFTY.
        PREVPERIOD     = TPA-BEGDA(6).
        WRITE: / 'Prev. infotype', TPA-BEGDA, 'to', TPA-ENDDA.
      ENDIF.
    ENDIF.
  ENDIF.

  ASSIGN PREVINFTY TO <GPREVINFTY>.
  ASSIGN THISINFTY TO <GTHISINFTY>.
ENDFORM.                    "fetchInfotype



*
* Read action infotype and previous
*
FORM FETCHACTIONINFOTYPE
  USING
    PERSON     TYPE PERNR-PERNR
    PMASSN     TYPE MASSN
    PMASSG     TYPE MASSG
    SDATE      TYPE PRELP-BEGDA
    ANDPREV    TYPE C
  CHANGING
    THISINFTY
    PREVINFTY.

  FIELD-SYMBOLS:
    <PT>           TYPE ANY.

  DATA:
    WA_PA0000  TYPE PA0000,
    BEGDA      LIKE PA0000-BEGDA,
    STRUNAME   TYPE STRING.

  CLEAR: THISINFTY, PREVINFTY.

  DATA:
    T_P0000    TYPE TABLE OF P0000,
    WA_P0000   TYPE P0000.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERSON
      INFTY           = '0000'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0000
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0000 INTO WA_P0000
        WHERE MASSN = PMASSN AND MASSG = PMASSG.
      EFFECTIVEDATE  = WA_P0000-BEGDA.
      FROMDATE       = EFFECTIVEDATE.
      SUBTRACT 1 FROM FROMDATE.
      MOVE-CORRESPONDING WA_P0000 TO WA_PA0000.
      PREVINFTY      = THISINFTY.
      THISINFTY      = WA_PA0000.
    ENDLOOP.
  ENDIF.

  ASSIGN PREVINFTY TO <GPREVINFTY>.
  ASSIGN THISINFTY TO <GTHISINFTY>.
ENDFORM.                    "fetchActionInfotype



*
* Read action infotype and previous
*
FORM DETERMINEOFFPHASES
  USING
    PERSON     TYPE PERNR-PERNR
    FROMDATE   TYPE D
    TODATE     TYPE D.

  FIELD-SYMBOLS:
    <PT>           TYPE ANY.

  DATA:
    T_P0000      TYPE TABLE OF P0000,
    WA_P0000     TYPE P0000,
    T_OFFMASSN   TYPE TABLE OF MASSN,
    WA_OFFMASSN  TYPE MASSN.

  PERFORM GETATTRIBUTE USING 'PR_OFFMASSN' '09' CHANGING TMPS.
  SPLIT TMPS AT ',' INTO TABLE T_OFFMASSN.

  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      PERNR           = PERSON
      INFTY           = '0000'
      BEGDA           = '18000101'
      ENDDA           = '99991231'
    TABLES
      INFTY_TAB       = T_P0000
    EXCEPTIONS
      INFTY_NOT_FOUND = 1
      OTHERS          = 2.
  IF SY-SUBRC = 0.
    LOOP AT T_P0000 INTO WA_P0000.
      READ TABLE T_OFFMASSN INTO WA_OFFMASSN
        WITH KEY TABLE_LINE = WA_P0000-MASSN.
      IF SY-SUBRC = 0.
        IF    WA_P0000-BEGDA <= TODATE
          AND WA_P0000-ENDDA >= TODATE.
          IF DEBUGLEVEL > 0.
            WRITE: / 'Ignoring To column because "off" phase.'.
            SKIP.
          ENDIF.
          CLEAR GENATO.
        ENDIF.
        IF    WA_P0000-BEGDA <= FROMDATE
          AND WA_P0000-ENDDA >= FROMDATE.
          IF DEBUGLEVEL > 0.
            WRITE: / 'Ignoring From column because "off" phase.'.
            SKIP.
          ENDIF.
          CLEAR GENAFROM.
        ENDIF.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDFORM.                    "determineOffPhases



*
* Copying and creating of temporary persons
*


*
* List of infotypes to copy
*
FORM INITCP.
  CPISINIT = 'X'.

  APPEND 'PA0000' TO TABNAMES.
  APPEND 'PA0001' TO TABNAMES.
  APPEND 'PA0002' TO TABNAMES.
  APPEND 'PA0003' TO TABNAMES.
  APPEND 'PA0006' TO TABNAMES.
  APPEND 'PA0007' TO TABNAMES.
  APPEND 'PA0008' TO TABNAMES.
  APPEND 'PA0009' TO TABNAMES.
  APPEND 'PA0011' TO TABNAMES.
  APPEND 'PA0012' TO TABNAMES.
  APPEND 'PA0013' TO TABNAMES.
  APPEND 'PA0014' TO TABNAMES.
  APPEND 'PA0015' TO TABNAMES.
  APPEND 'PA0016' TO TABNAMES.
  APPEND 'PA0017' TO TABNAMES.
  APPEND 'PA0019' TO TABNAMES.
  APPEND 'PA0021' TO TABNAMES.
  APPEND 'PA0022' TO TABNAMES.
  APPEND 'PA0023' TO TABNAMES.
  APPEND 'PA0024' TO TABNAMES.
  APPEND 'PA0025' TO TABNAMES.
  APPEND 'PA0027' TO TABNAMES.
  APPEND 'PA0028' TO TABNAMES.
  APPEND 'PA0030' TO TABNAMES.
  APPEND 'PA0031' TO TABNAMES.
  APPEND 'PA0032' TO TABNAMES.
  APPEND 'PA0033' TO TABNAMES.
  APPEND 'PA0034' TO TABNAMES.
  APPEND 'PA0035' TO TABNAMES.
  APPEND 'PA0037' TO TABNAMES.
  APPEND 'PA0040' TO TABNAMES.
  APPEND 'PA0041' TO TABNAMES.
  APPEND 'PA0045' TO TABNAMES.
  APPEND 'PA0050' TO TABNAMES.
  APPEND 'PA0054' TO TABNAMES.
  APPEND 'PA0057' TO TABNAMES.
  APPEND 'PA0077' TO TABNAMES.
  APPEND 'PA0078' TO TABNAMES.
  APPEND 'PA0080' TO TABNAMES.
  APPEND 'PA0081' TO TABNAMES.
  APPEND 'PA0082' TO TABNAMES.
  APPEND 'PA0083' TO TABNAMES.
  APPEND 'PA0094' TO TABNAMES.
  APPEND 'PA0105' TO TABNAMES.
  APPEND 'PA0165' TO TABNAMES.
  APPEND 'PA0167' TO TABNAMES.
  APPEND 'PA0168' TO TABNAMES.
  APPEND 'PA0169' TO TABNAMES.
  APPEND 'PA0171' TO TABNAMES.
  APPEND 'PA0185' TO TABNAMES.
  APPEND 'PA0262' TO TABNAMES.
  APPEND 'PA0278' TO TABNAMES.
  APPEND 'PA0279' TO TABNAMES.
  APPEND 'PA0302' TO TABNAMES.
  APPEND 'PA0304' TO TABNAMES.
  APPEND 'PA0351' TO TABNAMES.
  APPEND 'PA0374' TO TABNAMES.
  APPEND 'PA0376' TO TABNAMES.
  APPEND 'PA0377' TO TABNAMES.
  APPEND 'PA0378' TO TABNAMES.
  APPEND 'PA0416' TO TABNAMES.
  APPEND 'PA0487' TO TABNAMES.
  APPEND 'PA0509' TO TABNAMES.
  APPEND 'PA0703' TO TABNAMES.
  APPEND 'PA0704' TO TABNAMES.
  APPEND 'PA0710' TO TABNAMES.
  APPEND 'PA0712' TO TABNAMES.
  APPEND 'PA0715' TO TABNAMES.
  APPEND 'PA0959' TO TABNAMES.
  APPEND 'PA0960' TO TABNAMES.
****I_KONAKOV - insert line for IT0961
  APPEND 'PA0961' TO TABNAMES.
  APPEND 'PA0962' TO TABNAMES.
  APPEND 'PA2001' TO TABNAMES.
  APPEND 'PA2003' TO TABNAMES.
  APPEND 'PA2006' TO TABNAMES.
  APPEND 'PA2010' TO TABNAMES.
  APPEND 'PA2013' TO TABNAMES.
***  append 'PA9001' to tabnames.
****  append 'PA9002' to tabnames.
***  append 'PA9278' to tabnames.
***  append 'PA9600' to tabnames.
***  append 'PA9601' to tabnames.
***  append 'PA9602' to tabnames.
****  append 'PA9605' to tabnames.
***  append 'PA9620' to tabnames.
***  append 'PA9685' to tabnames.
ENDFORM.                    "initCP



*
* adjust copied person by removing the relevant infotypes
*
FORM ADJUSTCOPIEDPERSON
  USING
    PERSON      TYPE PERNR-PERNR
    SELDATE     TYPE D.

  DATA:
    DBCNT      TYPE I,
    DAYBEFORE  TYPE D.

  IF DEBUGLEVEL > 0.
    SKIP.
    WRITE: / 'Adjusting person', PERSON.
  ENDIF.
  LOOP AT TABNAMES INTO TABNAME.
    DELETE FROM (TABNAME)
      WHERE PERNR = PERSON
        AND BEGDA = SELDATE.
    IF SY-DBCNT > 0.
      IF DEBUGLEVEL > 0.
        WRITE: / 'Adjusted table', TABNAME, ':', SY-DBCNT, 'records'.
      ENDIF.
      DAYBEFORE = SELDATE.
      SUBTRACT 1 FROM DAYBEFORE.
      UPDATE (TABNAME)
        SET ENDDA = '99991231'
        WHERE PERNR = PERSON
          AND ENDDA = DAYBEFORE.
    ENDIF.
  ENDLOOP.
  COMMIT WORK.
ENDFORM.                    "adjustCopiedPerson



*
* create a temporary person from an existing person
*
FORM COPYPERSON
  USING
    FROMPERSON  TYPE PERNR-PERNR
    TOPERSON    TYPE PERNR-PERNR.

  FIELD-SYMBOLS:
    <PT>          TYPE ANY,
    <PTP>         TYPE ANY.

  DATA:
    DBCNT  TYPE I.

  IF CPISINIT IS INITIAL.
    PERFORM INITCP.
  ENDIF.

* copy infotypes
  LOOP AT TABNAMES INTO TABNAME.
    IF DEBUGLEVEL > 2.
      WRITE: / 'Copying table', TABNAME.
    ENDIF.
    ASSIGN (TABNAME) TO <PT>.
    CLEAR DBCNT.
    SELECT * FROM (TABNAME) INTO <PT>
        WHERE PERNR = FROMPERSON.
      ADD 1 TO DBCNT.
      <PT>+3(8) = TOPERSON.
      INSERT (TABNAME) FROM <PT>.
      IF SY-SUBRC <> 0.
        WRITE: / 'Copying person: Insert failed:', SY-SUBRC.
      ENDIF.
    ENDSELECT.
    IF DEBUGLEVEL > 1.
      IF DBCNT > 0.
        WRITE: / 'Copying table', TABNAME, ':', DBCNT, 'records'.
      ENDIF.
    ENDIF.
  ENDLOOP.

* copy several other tables
  DATA:
    T5BVV_WA TYPE T5BVV,
    T5BVV_T  TYPE T5BVV OCCURS 0 WITH HEADER LINE,
    T5CPB_WA TYPE T5CPB,
    T5CPB_T  TYPE T5CPB OCCURS 0 WITH HEADER LINE,
    T5CPZ_WA TYPE T5CPZ,
    T5CPZ_T  TYPE T5CPZ OCCURS 0 WITH HEADER LINE.

  CLEAR TABNAMESA.
  APPEND 'T5BVV' TO TABNAMESA.
  APPEND 'T5CPB' TO TABNAMESA.
  APPEND 'T5CPZ' TO TABNAMESA.

  LOOP AT TABNAMESA INTO TABNAME.
    IF DEBUGLEVEL > 2.
      WRITE: / 'Copying table', TABNAME.
    ENDIF.
    CLEAR DBCNT.
    DELETE FROM (TABNAME) WHERE PERNR = TOPERSON.
    IF 1 = 1.
      IF TABNAME = 'T5BVV'.
        SELECT * FROM T5BVV INTO TABLE T5BVV_T WHERE PERNR = FROMPERSON.
        LOOP AT T5BVV_T INTO T5BVV_WA.
          T5BVV_WA-PERNR = TOPERSON.
          INSERT T5BVV FROM T5BVV_WA.
          ADD 1 TO DBCNT.
        ENDLOOP.
      ENDIF.
      IF TABNAME = 'T5CPB'.
        SELECT * FROM T5CPB INTO TABLE T5CPB_T WHERE PERNR = FROMPERSON.
        LOOP AT T5CPB_T INTO T5CPB_WA.
          T5CPB_WA-PERNR = TOPERSON.
          INSERT T5CPB FROM T5CPB_WA.
          ADD 1 TO DBCNT.
        ENDLOOP.
      ENDIF.
      IF TABNAME = 'T5CPZ'.
        SELECT * FROM T5CPZ INTO TABLE T5CPZ_T WHERE PERNR = FROMPERSON.
        LOOP AT T5CPZ_T INTO T5CPZ_WA.
          T5CPZ_WA-PERNR = TOPERSON.
          INSERT T5CPZ FROM T5CPZ_WA.
          ADD 1 TO DBCNT.
        ENDLOOP.
      ENDIF.
    ELSE.
      DATA: F1 TYPE STRING VALUE '<pt>-PERNR'.
      SELECT * FROM (TABNAME) INTO <PT>
        WHERE PERNR = FROMPERSON.
        ADD 1 TO DBCNT.
*        assign component 'PERNR' of structure <pt> to <ptp>.
        ASSIGN (F1) TO <PTP>.
        IF SY-SUBRC <> 0.
          WRITE: / 'Assign failed:', SY-SUBRC.
        ELSE.
          <PTP> = TOPERSON.
          INSERT (TABNAME) FROM <PT>.
          IF SY-SUBRC <> 0.
            WRITE: / 'Copying', TABNAME, ': Insert failed:', SY-SUBRC.
          ENDIF.
        ENDIF.
      ENDSELECT.
    ENDIF.
    IF DEBUGLEVEL > 1.
      IF DBCNT > 0.
        WRITE: / 'Copying table', TABNAME, ':', DBCNT, 'records'.
      ENDIF.
    ENDIF.
  ENDLOOP.

* commit
  COMMIT WORK.
ENDFORM.                    "copyPerson



*
* delete an existing person
*
FORM DELETEPERSON
  USING
    PERSON    TYPE PERNR-PERNR
    MASTER    TYPE C
    CLUSTER   TYPE C.

  FIELD-SYMBOLS:
    <PT>          TYPE ANY.

  IF CPISINIT IS INITIAL.
    PERFORM INITCP.
  ENDIF.

* Deleting cluster
  IF NOT CLUSTER IS INITIAL.
    DATA:
      KEY LIKE PCL2-SRTFD.
    CONCATENATE PERSON '%' INTO KEY.
    DELETE FROM PCL2
      WHERE
        ( RELID = 'UN' OR RELID = 'CU' )  AND
        SRTFD LIKE KEY.
    IF DEBUGLEVEL > 0.
      WRITE: / 'Cluster delete  :', SY-SUBRC, SY-DBCNT.
    ENDIF.
    DELETE FROM HRPY_RGDIR     WHERE PERNR = PERSON.
    IF DEBUGLEVEL > 0.
      WRITE: / 'RGDIR delete    :', SY-SUBRC, SY-DBCNT.
    ENDIF.
    DELETE FROM HRPY_WPBP      WHERE PERNR = PERSON.
    IF DEBUGLEVEL > 0.
      WRITE: / 'WPBP delete     :', SY-SUBRC, SY-DBCNT.
    ENDIF.
    DELETE FROM HRPY_GROUPING  WHERE PERNR = PERSON.
    IF DEBUGLEVEL > 0.
      WRITE: / 'Grouping delete :', SY-SUBRC, SY-DBCNT.
    ENDIF.
    COMMIT WORK.
  ENDIF.


* Deleting pernr
  IF NOT MASTER IS INITIAL.
    IF 1 = 2.
*      submit RPUDELPN
*        with PNPPERNR-LOW = person
*        with PROTOCOL     = space
*        with TESTX        = space
*        and return
*        exporting list to memory.
    ELSE.
      LOOP AT TABNAMES INTO TABNAME.
        DELETE FROM (TABNAME)
            WHERE PERNR = PERSON.
*     write: / 'Deleting from table', tabname, ':', sy-subrc, sy-dbcnt.
      ENDLOOP.
      COMMIT WORK.
    ENDIF.
  ENDIF.
ENDFORM.                    "deletePerson
.



*
* display an existing person
*
FORM DISPLAYPERSON
  USING
    PERSON    TYPE PERNR-PERNR.

  FIELD-SYMBOLS:
    <PT>          TYPE ANY.

  DATA:
    TMPS(80)      TYPE C.

  IF CPISINIT IS INITIAL.
    PERFORM INITCP.
  ENDIF.

  SKIP.
  WRITE: / 'Person :', PERSON.
  LOOP AT TABNAMES INTO TABNAME.
    ASSIGN (TABNAME) TO <PT> CASTING TYPE (TABNAME).
    SELECT * FROM (TABNAME) INTO <PT>
        WHERE PERNR = PERSON.
      TMPS = <PT>.
      WRITE: / TABNAME+2, ':', TMPS.
    ENDSELECT.
  ENDLOOP.
  SKIP.
ENDFORM.                    "displayPerson



*
* create a temporary person from scratch
*
FORM CREATEDUMMYPERSON
  USING
    PERNR   TYPE PERNR-PERNR.

  DATA:
    COUNT(8)  TYPE N.

  IF CPISINIT IS INITIAL.
    PERFORM INITCP.
  ENDIF.

  DATA:
    BEGDA1  TYPE BEGDA  VALUE '20000101',
    BEGDA2  TYPE BEGDA  VALUE '99991231',
    ENDDA1  TYPE ENDDA  VALUE '20000101',
    ENDDA2  TYPE ENDDA  VALUE '99991231'.
  PA0000-PERNR   = PERNR.
  PA0000-BEGDA   = BEGDA1.
  PA0000-ENDDA   = '99991231'.
  PA0000-MASSN   = '00'.
  INSERT INTO PA0000 VALUES PA0000.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  MOVE-CORRESPONDING PA0000 TO PA0302.
  INSERT INTO PA0302 VALUES PA0302.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  DATA:
    BUKRS   TYPE BUKRS VALUE '',
    WERKS   TYPE PERSA VALUE '',
    PERSG   TYPE PERSG VALUE '',
    PERSK   TYPE PERSK VALUE ''.
  PA0001-PERNR   = PERNR.
  PA0001-BEGDA   = BEGDA1.
  PA0001-ENDDA   = ENDDA1.
  PA0001-BUKRS   = BUKRS.
  PA0001-WERKS   = WERKS.
  PA0001-PERSG   = PERSG.
  PA0001-PERSK   = PERSK.
  INSERT INTO PA0001 VALUES PA0001.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  PA0002-PERNR   = PERNR.
  PA0002-BEGDA   = BEGDA1.
  PA0002-ENDDA   = ENDDA1.
  PA0002-NACHN   = 'Dummy'.
  PA0002-VORNA   = 'Silly'.
  PA0002-CNAME   = 'Silly Dummy'.
  PA0002-ANRED   = 2.
  INSERT INTO PA0002 VALUES PA0002.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  DATA:
    ABRDT   TYPE LABRD VALUE '20050101',
    RRDAT   TYPE RRDAT VALUE '20050101',
    PRDAT   TYPE PRRDT VALUE '20050101'.

  PA0003-PERNR   = PERNR.
  PA0003-BEGDA   = BEGDA1.
  PA0003-ENDDA   = ENDDA1.
  PA0003-ABRDT   = '00'.
  PA0003-RRDAT   = '00'.
  PA0003-PRDAT   = '00'.
  INSERT INTO PA0003 VALUES PA0003.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  DATA:
    SCHKZ   TYPE SCHKN VALUE 'NORM    ',
    MOSTD   TYPE MOSTD VALUE '150',
    WOSTD   TYPE WOSTD VALUE '35'.

  PA0007-PERNR   = PERNR.
  PA0007-BEGDA   = BEGDA1.
  PA0007-ENDDA   = ENDDA1.
  PA0007-SCHKZ   = SCHKZ.
  PA0007-MOSTD   = MOSTD.
  PA0007-WOSTD   = WOSTD.
  INSERT INTO PA0007 VALUES PA0007.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.

  DATA:
    TRFAR   TYPE TRFAR VALUE '',
    TRFGB   TYPE TRFGB VALUE '',
    TRFGR   TYPE TRFGR VALUE '',
    TRFST   TYPE TRFST VALUE ''.
  PA0008-PERNR   = PERNR.
  PA0008-BEGDA   = BEGDA1.
  PA0008-ENDDA   = ENDDA1.
  PA0008-TRFAR   = TRFAR.
  PA0008-TRFGB   = TRFGB.
  PA0008-TRFGR   = TRFGR.
  PA0008-TRFST   = TRFST.
  INSERT INTO PA0008 VALUES PA0008.
  WRITE: / 'Insert:', SY-SUBRC, SY-DBCNT.


  COMMIT WORK.

  LOOP AT TABNAMES INTO TABNAME.
    SELECT COUNT(*) INTO COUNT FROM (TABNAME)
      WHERE PERNR = PERNR.
    WRITE: / 'Entries in', TABNAME, ':', COUNT,
      '(', SY-SUBRC, SY-DBCNT,')'.
  ENDLOOP.
ENDFORM.                    "createDummyPerson


*
* Display payroll log
*
FORM DISPLAYPAYROLLLOG.
  DATA:
    ABAPLIST         TYPE TABLE OF ABAPLIST,
    LISTLINE         TYPE CHAR200,
    LISTTXT          TYPE TABLE OF CHAR200.

  ULINE.
  CALL FUNCTION 'LIST_FROM_MEMORY'
    TABLES
      LISTOBJECT = ABAPLIST
    EXCEPTIONS
      NOT_FOUND  = 1
      OTHERS     = 2.
  IF SY-SUBRC <> 0.
    WRITE: / 'Cannot fetch list of payroll run:', SY-SUBRC.
  ELSE.
    CALL FUNCTION 'LIST_TO_ASCI'
      TABLES
        LISTASCI           = LISTTXT
        LISTOBJECT         = ABAPLIST
      EXCEPTIONS
        EMPTY_LIST         = 1
        LIST_INDEX_INVALID = 2
        OTHERS             = 3.
    IF SY-SUBRC <> 0.
      WRITE: / 'Error', SY-SUBRC, 'converting report!'.
    ELSE.
      LOOP AT LISTTXT INTO LISTLINE.
        WRITE: / LISTLINE(118).
      ENDLOOP.
    ENDIF.
  ENDIF.
  ULINE.
ENDFORM.                    "displayPayrollLog


*
* Run RPCALC
*
* Performs one RPCALC runs one with the current person, (1st run)
* one with the person with the 'newer' infotypes removed (2nd run).
* Both runs are in the same period.
*
* If splits are detected, the last two are used for the
* 'from' (here 'before', Suffix 'b') and 'to' (here 'after', Suffix 'a')
* columns. The values of the splits get multiplied to a full month.
* If splits are detected in the first run, no second run is necessary!
*
* If no splits are detected the complete month is taken 'as is'.
*

FORM RUNRPCALC
  USING
    PERNR       TYPE PERNR-PERNR
    THISPERIOD  TYPE FAPER.

  DATA:
    RPCALC(32)       TYPE C      VALUE 'HUNCALC0',
    SELPERIOD        LIKE THISPERIOD,
    ABKRS            TYPE ABKRS  VALUE '01',
    SCHEMA(4)        TYPE C      VALUE 'ZN00',
    RETRO_DATE       TYPE D,
    ADJUST1800(1)    TYPE C      VALUE SPACE,
    ADJUST1820(1)    TYPE C      VALUE SPACE,
    ADJUST1900(1)    TYPE C      VALUE SPACE,
    ADJUSTDELTA(1)   TYPE C      VALUE SPACE,
    ADJUSTPRORA(1)   TYPE C      VALUE SPACE,
    MODECLREAD(1)    TYPE C      VALUE '0',
    REMCLUSTER(1)    TYPE C      VALUE '0',
    DELTAWTS         TYPE TABLE OF LGART,
    ADJBEWTS         TYPE TABLE OF LGART,
    IS_BEFORE(1)     TYPE C      VALUE SPACE,
    SPLITS_FOUND     TYPE I      VALUE 0,
    SEQS_FOUND       TYPE I      VALUE 0.

  PERFORM GETATTRIBUTE USING 'RPCALC' 'HUNCALC0' CHANGING TMPS.
  RPCALC     = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_AREA' '01' CHANGING TMPS.
  ABKRS      = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_SCHEMA' 'ZN00' CHANGING TMPS.
  SCHEMA     = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_RETRO' '' CHANGING TMPS.
  RETRO_DATE = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_REMCLUSTER' '0' CHANGING TMPS.
  REMCLUSTER = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_ADJ1800' ' ' CHANGING TMPS.
  ADJUST1800 = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_ADJ1820' ' ' CHANGING TMPS.
  ADJUST1820 = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_ADJ1900' ' ' CHANGING TMPS.
  ADJUST1900 = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_ADJDELTA' ' ' CHANGING TMPS.
  ADJUSTDELTA = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_ADJPRORA' ' ' CHANGING TMPS.
  ADJUSTPRORA = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_MODECLREAD' '0' CHANGING TMPS.
  MODECLREAD = TMPS.
  PERFORM GETATTRIBUTE USING 'PR_DELTAWTS' '5650,5651' CHANGING TMPS.
  SPLIT TMPS AT ',' INTO TABLE DELTAWTS.
  PERFORM GETATTRIBUTE USING 'PR_ADJBEWTS' '1820' CHANGING TMPS.
  SPLIT TMPS AT ',' INTO TABLE ADJBEWTS.

  IF RETRO_DATE IS INITIAL.
    WRITE: / 'Retro is initial'.
  ELSE.
    IF HIRE_DATE > RETRO_DATE.
      RETRO_DATE = HIRE_DATE.
      WRITE: / 'Retro set to hire date :', RETRO_DATE.
    ELSE.
      WRITE: / 'Retro :', RETRO_DATE.
    ENDIF.
  ENDIF.
  SKIP.

  DO 2 TIMES.
    IF SY-INDEX = 1.
* First payroll run
      SELPERIOD = THISPERIOD.
    ELSE.
* Second payroll run. Will be cancelled if splits or multiple
* identical seqnrs had been detected during the first run.
      SELPERIOD = PREVPERIOD.
      IS_BEFORE = 'X'.
      IF SPLITS_FOUND > 1.
        IF DEBUGLEVEL > 0.
          SKIP.
          WRITE: /
            'No second payroll run necessary.',
            '(Because first run had enough splits)'.
        ENDIF.
        EXIT.
      ENDIF.
      IF SEQS_FOUND > 1.
        IF DEBUGLEVEL > 0.
          SKIP.
          WRITE: /
            'No second payroll run necessary.',
            '(Because first run had enough sequence numbers)'.
        ENDIF.
        EXIT.
      ENDIF.

* remove new infotype entries
* changed 14.09.2006
* do the routine if doPermanent = X
*     if doPermanent is initial.
      IF NOT DOPERMANENT IS INITIAL.
* end changed 14.09.2006
        PERFORM ADJUSTCOPIEDPERSON
          USING PERNR EFFECTIVEDATE.
      ENDIF.
* remove results of first payroll run
      IF REMCLUSTER = '1'.
        PERFORM DELETEPERSON
          USING PERNR SPACE 'X'.
      ENDIF.
    ENDIF.

    IF DEBUGLEVEL > 0.
      WRITE: / 'Running', RPCALC, 'for area', ABKRS,
        'with schema', SCHEMA, 'to', SELPERIOD.
    ENDIF.
    SUBMIT (RPCALC)
*      with pnpxabkr     = abkrs
*      with pnppernr-low = pernr
*      with pnptimra     = 'X'
*      with pnppabrp     = selperiod+4(2)
*      with pnppabrj     = selperiod(4)
*      with schema       = schema
*      with tst_on       = ' '
*      with prt_prot     = 'X'
*      with rueck-ab     = retro_date
      USING SELECTION-SET 'PAF'
      WITH PNPPERNR-LOW = PERNR
      WITH PNPPABRP     = SELPERIOD+4(2)
      WITH PNPPABRJ     = SELPERIOD(4)
      AND RETURN
      EXPORTING LIST TO MEMORY.

*   Reading the output list of RPCALC
    IF NOT DISPPRLOG IS INITIAL.
      PERFORM DISPLAYPAYROLLLOG.
    ENDIF. "end of reading RPCALC output list.


* read cluster
    DATA:
      BEGDA         TYPE BEGDA          VALUE '18000101',
      ENDDA         TYPE ENDDA          VALUE '99991231',
      WS_RGDIR      TYPE PC261,
      T_RGDIR       TYPE PC261 OCCURS 0,
      T_RGDIR_O     TYPE PC261 OCCURS 0,
      T_RESULTUNT   TYPE TABLE OF PAYUN_RESULT,
      T_RESULTUN    LIKE LINE OF T_RESULTUNT,
      T_RESULT99    TYPE PAY99_RESULT,
      W_WPBP        TYPE LINE OF HRPAY99_WPBP,
      W_BT          TYPE LINE OF HRPAY99_BT,
      W_RT          TYPE LINE OF HRPAY99_RT,
      SPLITB        TYPE APZNR,
      SPLITA        TYPE APZNR,
      SPLITDAYSB    TYPE I,
      SPLITDAYSA    TYPE I,
      SPLITDAYST    TYPE I,
      OUT_SEQNR     TYPE PC261-SEQNR,
      MSEHI         LIKE T538A-MSEHI.

    CLEAR: OUT_SEQNR.
    CALL FUNCTION 'RH_GET_PLVAR'
      IMPORTING
        PLVAR    = PLVAR
      EXCEPTIONS
        NO_PLVAR = 1
        OTHERS   = 2.
    IF SY-SUBRC <> 0.
      WRITE: / 'Cannot determine PLVAR!'.
    ENDIF.

    CALL FUNCTION 'RH_PM_GET_MOLGA_FROM_PERNR'
      EXPORTING
        PLVAR           = PLVAR
        PERNR           = PERNR
        BEGDA           = BEGDA
        ENDDA           = ENDDA
      IMPORTING
        MOLGA           = MOLGA
        TRFKZ           = TRFKZ
      EXCEPTIONS
        NOTHING_FOUND   = 1
        NO_ACTIVE_PLVAR = 2
        OTHERS          = 3.
    IF SY-SUBRC <> 0.
      WRITE: / 'Cannot determine MOLGA!'.
    ENDIF.

    CALL FUNCTION 'CU_READ_RGDIR'
      EXPORTING
        PERSNR             = PERNR
        NO_AUTHORITY_CHECK = 'X'
      IMPORTING
        MOLGA              = MOLGA
      TABLES
        IN_RGDIR           = T_RGDIR
      EXCEPTIONS
        NO_RECORD_FOUND    = 1
        OTHERS             = 2.
    IF SY-SUBRC <> 0.
      FORMAT COLOR COL_NEGATIVE.
      WRITE: / 'Error during cluster dir:', SY-SUBRC.
      FORMAT COLOR OFF.
      IF SY-SUBRC = 1.
        WRITE: / 'Probably the Payroll run was not succesfull.'.
        WRITE: / 'Inspect following payroll log:'.
        PERFORM DISPLAYPAYROLLLOG.
        WRITE: /
          'Maybe a program run with message level 9, and a',
          'subsequent manual payroll run for the temporary',
          'person will give more information.'.
        WRITE: / 'See documentation for details.'.
      ENDIF.
    ELSE.
      IF DEBUGLEVEL > 0.
        WRITE: / 'cluster dir (MOLGA):', MOLGA.
      ENDIF.

      CALL FUNCTION 'CD_READ_DATE_RANGE'
        EXPORTING
          BEGDA           = BEGDA
          ENDDA           = ENDDA
*         SEL_VOID        =
        TABLES
          RGDIR           = T_RGDIR
          OUT_RGDIR       = T_RGDIR_O
        EXCEPTIONS
          OTHERS          = 1.
      IF SY-SUBRC <> 0.
        WRITE: / 'error during cluster read date range:', SY-SUBRC.
      ELSE.
        DATA:
          LATEST_SEQNR      LIKE OUT_SEQNR,
          SCNDLATEST_SEQNR  LIKE OUT_SEQNR,
          FIRST_SEQ(1)      TYPE C,
          KEY_BENTRY        LIKE SY-TABIX,
          BETRG             LIKE W_RT-BETRG,
          DUMMY_WT          TYPE LGART,
          IS_DELTA(1)       TYPE C,
          FOR_B(1)          TYPE C,
          FOR_A(1)          TYPE C,
          SLGART            LIKE W_RT-LGART,
          SPECIALINS(1)     TYPE C,
          ADJUSTPRORAS(1)   TYPE C.

        CLEAR: LATEST_SEQNR, SCNDLATEST_SEQNR.
        LOOP AT T_RGDIR_O INTO WS_RGDIR.
          IF DEBUGLEVEL > 0.
            WRITE: / WS_RGDIR-SEQNR, WS_RGDIR-FPPER.
          ENDIF.
          IF WS_RGDIR-FPPER = SELPERIOD.
            ADD 1 TO SEQS_FOUND.
            SCNDLATEST_SEQNR = LATEST_SEQNR.
            LATEST_SEQNR     = WS_RGDIR-SEQNR.
          ENDIF.
        ENDLOOP.


        IF MODECLREAD = '1'.

* current mode of cluster read.
*(does work since using structure 'payun_result')
          DO 2 TIMES.
            IF SY-INDEX = 1.
              FIRST_SEQ = 'X'.
              OUT_SEQNR = LATEST_SEQNR.
            ELSE.
              CLEAR FIRST_SEQ.
              OUT_SEQNR = SCNDLATEST_SEQNR.
            ENDIF.
            WRITE: / 'Selected period:', SELPERIOD,
              ' ( seqnr', OUT_SEQNR, '), first:', FIRST_SEQ.

            DATA:
              PABRJ  TYPE PNPPABRJ,
              PABRP  TYPE PNPPABRP.

            PABRJ = SELPERIOD(4).
            PABRP = SELPERIOD+4(2).

            CLEAR T_RESULTUNT.


            CALL FUNCTION 'HR_GET_PAYROLL_RESULTS'
              EXPORTING
                PERNR                               = PERNR
*              PERMO                               =
                PABRJ                               = PABRJ
                PABRP                               = PABRP
*             PABRJ_END                           =
*             PABRP_END                           =
*             INPER_LST                           =
*             INPER_ACT                           =
*             ACTUAL                              =
*             WAERS                               =
*             ARCH_TOO                            =
              TABLES
                RESULT_TAB                          = T_RESULTUNT
             EXCEPTIONS
               NO_RESULTS                          = 1
               ERROR_IN_CURRENCY_CONVERSION        = 2
               T500L_ENTRY_NOT_FOUND               = 3
               PERIOD_MISMATCH_ERROR               = 4
               T549Q_ENTRY_NOT_FOUND               = 5
               INTERNAL_ERROR                      = 6
               WRONG_STRUCTURE_OF_RESULT_TAB       = 7
               OTHERS                              = 8.
            IF SY-SUBRC <> 0.
              WRITE: / 'HR_GET_PAYROLL_RESULTS:', SY-SUBRC.
            ELSE.
              DATA: PAYLINEUN TYPE PAYUN_RESULT.
              LOOP AT T_RESULTUNT INTO PAYLINEUN.

* skip non-used sequence numbers
                IF PAYLINEUN-EVP-SEQNR <> OUT_SEQNR.
                  CONTINUE.
                ENDIF.

*   WPBP (to get the splits)
*   splita will held the latest split, and splitb the second latest
*   split within the month.
                CLEAR: SPLITB, SPLITA, SPLITDAYSB, SPLITDAYSA, SPLITDAYST,
                       SPLITS_FOUND.
                IF DEBUGLEVEL > 1.
                  SKIP.
                  WRITE: / 'WPBP (Splits)  Pernr    seqnr begda      nr',
                           '  split_days    total_days'.
                ENDIF.
                LOOP AT PAYLINEUN-INTER-WPBP INTO W_WPBP.
                  ADD 1 TO SPLITS_FOUND.
                  SPLITB     = SPLITA.
                  SPLITDAYSB = SPLITDAYSA.
                  SPLITA     = W_WPBP-APZNR.
                  SPLITDAYSA = W_WPBP-ENDDA+6(2) - W_WPBP-BEGDA+6(2) + 1.
*              add splitdaysa to splitdayst.
                  SPLITDAYST = W_WPBP-ENDDA+6(2).
                  IF DEBUGLEVEL > 1.
                    WRITE: / 'WPBP (Splits):', PERNR, OUT_SEQNR,
                      W_WPBP-BEGDA, W_WPBP-APZNR, ':',
                      SPLITDAYSA, SPLITDAYST.
                  ENDIF.
                ENDLOOP.

* RT (to get the results)
                IF DEBUGLEVEL > 2.
                  SKIP.
                  WRITE: / 'RT : SeqNr Nr fromCol toCol wage T Nr',
                           '        single value          sum up value',
                           'curr zei cust_id'.
                ENDIF.
                LOOP AT PAYLINEUN-INTER-RT INTO W_RT.

                  SLGART = W_RT-LGART.

* Detect whether the value is for 'before' or 'after'.
                  CLEAR: FOR_B, FOR_A, ADJUSTPRORAS.
                  ADJUSTPRORAS = 'X'.
                  BETRG = W_RT-BETRG.
                  IF IS_BEFORE IS INITIAL. "first run
                    IF SPLITS_FOUND > 1.   "has splits
                      IF W_RT-APZNR = SPLITB.
                        FOR_B = 'X'.
                      ENDIF.
                      IF W_RT-APZNR = SPLITA.
                        FOR_A = 'X'.
                      ENDIF.
                    ELSE. "no splits
                      IF FIRST_SEQ IS INITIAL.
                        FOR_B = 'X'.
                      ELSE.
                        FOR_A = 'X'.
                      ENDIF.
                    ENDIF.
                  ELSE. "scnd payroll run
                    FOR_B = 'X'.
                    IF SPLITS_FOUND > 1.   "has splits -> take last split
                      SPLITDAYSB = SPLITDAYSA.
                    ENDIF.
                  ENDIF.
* Remove proration
                  IF NOT ADJUSTPRORAS IS INITIAL.
                    READ TABLE ADJBEWTS INTO DUMMY_WT
                      WITH KEY TABLE_LINE = SLGART.
                    IF SY-SUBRC = 0 OR ADJUSTPRORA = 'X'.
                      IF NOT FOR_B IS INITIAL.
                        IF      NOT SPLITDAYSB IS INITIAL
                            AND NOT SPLITDAYST IS INITIAL.
                          MULTIPLY BETRG BY SPLITDAYST.
                          DIVIDE   BETRG BY SPLITDAYSB.
                        ENDIF.
                      ENDIF.
                      IF NOT FOR_A IS INITIAL.
                        IF      NOT SPLITDAYSA IS INITIAL
                            AND NOT SPLITDAYST IS INITIAL.
                          MULTIPLY BETRG BY SPLITDAYST.
                          DIVIDE   BETRG BY SPLITDAYSA.
                        ENDIF.
                      ENDIF.
                    ENDIF.
                  ENDIF.
                  IF DEBUGLEVEL > 3.
                    WRITE: / 'RT :', OUT_SEQNR, W_RT-APZNR,
                      'from:', FOR_B, 'to:', FOR_A,
                      W_RT-LGART, W_RT-V0TYP, W_RT-V0ZNR,
                      W_RT-BETRG CURRENCY '2',
                      BETRG CURRENCY '2'.
                  ENDIF.

* Special treatment for selected wage types
                  CLEAR SPECIALINS.
                  IF NOT ADJUST1800 IS INITIAL.
                    IF SLGART = '1800'. CONTINUE. ENDIF.
                    IF SLGART = '1810'. CONTINUE. ENDIF.
                    IF SLGART = '1804' OR SLGART = '1808'.
                      SLGART = '1800'.
                      SPECIALINS = 'X'.
                    ENDIF.
                    IF SLGART = '1814' OR SLGART = '1818'.
                      SLGART = '1810'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.
                  IF NOT ADJUST1820 IS INITIAL.
                    IF SLGART = '1820'. CONTINUE. ENDIF.
                    IF SLGART = '1830'. CONTINUE. ENDIF.
                    IF SLGART = '1824' OR SLGART = '1828'.
                      SLGART = '1820'.
                      SPECIALINS = 'X'.
                    ENDIF.
                    IF SLGART = '1834' OR SLGART = '1838'.
                      SLGART = '1830'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.
                  IF NOT ADJUST1900 IS INITIAL.
                    IF SLGART = '1900'. CONTINUE. ENDIF.
                    IF SLGART = '1904' OR SLGART = '1908'.
                      SLGART = '1900'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.

* Detect whether the wage type is actually needed; in this
* case assign the value to the 'before' or 'after' field.

                  READ TABLE BENTRIES INTO BENTRY
                    WITH KEY WT = SLGART.
                  IF SY-SUBRC = 0.
                    KEY_BENTRY = SY-TABIX.

                    IF NOT ADJUSTDELTA IS INITIAL.
                      READ TABLE DELTAWTS INTO DUMMY_WT
                        WITH KEY TABLE_LINE = SLGART.
                      IF SY-SUBRC = 0.
                        IS_DELTA = 'X'.
                      ELSE.
                        IS_DELTA = SPACE.
                      ENDIF.
                    ENDIF.

                    SELECT SINGLE MSEHI INTO MSEHI FROM T538A
                      WHERE ZEINH = W_RT-ZEINH.

                    IF NOT FOR_B IS INITIAL.
                      IF NOT SPECIALINS IS INITIAL.
                        IF BENTRY-BTB IS INITIAL.
                          BENTRY-BTB = BETRG.
                        ELSE.
                          BENTRY-BTB = BENTRY-BTB - BETRG.
                        ENDIF.
                      ELSE.
                        IF IS_DELTA IS INITIAL.
                          BENTRY-BTB = BETRG.
                        ELSE.
                          BENTRY-BTB = BETRG - BENTRY-BTB.
                        ENDIF.
                      ENDIF.
                      BENTRY-CUB = W_RT-RTE_CURR.
                      IF BENTRY-CUB IS INITIAL.
                        BENTRY-CUB = W_RT-AMT_CURR.
                      ENDIF.
                      IF BENTRY-CUB IS INITIAL.
                        BENTRY-CUB = PAYLINEUN-INTER-VERSC-WAERS.
                      ENDIF.
                    ENDIF.
                    IF NOT FOR_A IS INITIAL.
                      IF NOT SPECIALINS IS INITIAL.
                        IF BENTRY-BTA IS INITIAL.
                          BENTRY-BTA = BETRG.
                        ELSE.
                          BENTRY-BTA = BENTRY-BTA - BETRG.
                        ENDIF.
                      ELSE.
                        IF IS_DELTA IS INITIAL.
                          BENTRY-BTA = BETRG.
                        ELSE.
                          BENTRY-BTA = BETRG - BENTRY-BTB.
                        ENDIF.
                      ENDIF.
                      BENTRY-CUA = W_RT-RTE_CURR.
                      IF BENTRY-CUA IS INITIAL.
                        BENTRY-CUA = W_RT-AMT_CURR.
                      ENDIF.
                      IF BENTRY-CUA IS INITIAL.
                        BENTRY-CUA = PAYLINEUN-INTER-VERSC-WAERS.
                      ENDIF.
                    ENDIF.
                    MODIFY BENTRIES FROM BENTRY INDEX KEY_BENTRY.
                    IF DEBUGLEVEL > 2.
                      WRITE: / 'RT*:', OUT_SEQNR, W_RT-APZNR,
                        'from:', FOR_B, 'to:', FOR_A,
                        W_RT-LGART, W_RT-V0TYP, W_RT-V0ZNR,
                        W_RT-BETRG CURRENCY '2',
                        BETRG CURRENCY '2',
                        W_RT-AMT_CURR, MSEHI, BENTRY-ID, IS_DELTA.
                    ENDIF.
                  ENDIF.

                ENDLOOP.
              ENDLOOP.
            ENDIF.

          ENDDO.




        ELSE.

*
*
* previous mode of cluster read.
* (does work, at least no dumps, but doubts whether the correct fuba...)
*
*
          DO 2 TIMES.
            IF SY-INDEX = 1.
              FIRST_SEQ = 'X'.
              OUT_SEQNR = LATEST_SEQNR.
            ELSE.
              CLEAR FIRST_SEQ.
              OUT_SEQNR = SCNDLATEST_SEQNR.
            ENDIF.
            WRITE: / 'Selected period:', SELPERIOD,
              ' ( seqnr', OUT_SEQNR, '), first:', FIRST_SEQ.

            IF NOT OUT_SEQNR IS INITIAL.
              CLEAR T_RESULT99.
              CALL FUNCTION 'PYXX_READ_PAYROLL_RESULT'
                EXPORTING
                  CLUSTERID                    = SPACE   "'UN'
                  EMPLOYEENUMBER               = PERNR
                  SEQUENCENUMBER               = OUT_SEQNR
                  READ_ONLY_INTERNATIONAL      = 'X'
                CHANGING
                  PAYROLL_RESULT               = T_RESULT99
                EXCEPTIONS
                  ILLEGAL_ISOCODE_OR_CLUSTERID = 1
                  ERROR_GENERATING_IMPORT      = 2
                  IMPORT_MISMATCH_ERROR        = 3
                  SUBPOOL_DIR_FULL             = 4
                  NO_READ_AUTHORITY            = 5
                  NO_RECORD_FOUND              = 6
                  VERSIONS_DO_NOT_MATCH        = 7
                  ERROR_READING_ARCHIVE        = 8
                  ERROR_READING_RELID          = 9
                  OTHERS                       = 10.
              IF SY-SUBRC <> 0.
                WRITE: / 'error reading payroll result:', SY-SUBRC.
              ELSE.

*   WPBP (to get the splits)
*   splita will held the latest split, and splitb the second latest
*   split within the month.
                CLEAR: SPLITB, SPLITA, SPLITDAYSB, SPLITDAYSA, SPLITDAYST,
                       SPLITS_FOUND.
                IF DEBUGLEVEL > 1.
                  SKIP.
                  WRITE: / 'WPBP (Splits)  Pernr    seqnr begda      nr',
                           '  split_days    total_days'.
                ENDIF.
                LOOP AT T_RESULT99-INTER-WPBP INTO W_WPBP.
                  ADD 1 TO SPLITS_FOUND.
                  SPLITB     = SPLITA.
                  SPLITDAYSB = SPLITDAYSA.
                  SPLITA     = W_WPBP-APZNR.
                  SPLITDAYSA = W_WPBP-ENDDA+6(2) - W_WPBP-BEGDA+6(2) + 1.
*              add splitdaysa to splitdayst.
                  SPLITDAYST = W_WPBP-ENDDA+6(2).
                  IF DEBUGLEVEL > 1.
                    WRITE: / 'WPBP (Splits):', PERNR, OUT_SEQNR,
                      W_WPBP-BEGDA, W_WPBP-APZNR, ':',
                      SPLITDAYSA, SPLITDAYST.
                  ENDIF.
                ENDLOOP.

* RT (to get the results)
                IF DEBUGLEVEL > 2.
                  SKIP.
                  WRITE: / 'RT : SeqNr Nr fromCol toCol wage T Nr',
                           '        single value          sum up value',
                           'curr zei cust_id'.
                ENDIF.
                LOOP AT T_RESULT99-INTER-RT INTO W_RT.

                  SLGART = W_RT-LGART.

* Detect whether the value is for 'before' or 'after'.
                  CLEAR: FOR_B, FOR_A, ADJUSTPRORAS.
                  ADJUSTPRORAS = 'X'.
                  BETRG = W_RT-BETRG.
                  IF IS_BEFORE IS INITIAL. "first run
                    IF SPLITS_FOUND > 1.   "has splits
                      IF W_RT-APZNR = SPLITB.
                        FOR_B = 'X'.
                      ENDIF.
                      IF W_RT-APZNR = SPLITA.
                        FOR_A = 'X'.
                      ENDIF.
                    ELSE. "no splits
                      IF FIRST_SEQ IS INITIAL.
                        FOR_B = 'X'.
                      ELSE.
                        FOR_A = 'X'.
                      ENDIF.
                    ENDIF.
                  ELSE. "scnd payroll run
                    FOR_B = 'X'.
                    IF SPLITS_FOUND > 1.   "has splits -> take last split
                      SPLITDAYSB = SPLITDAYSA.
                    ENDIF.
                  ENDIF.
* Remove proration
                  IF NOT ADJUSTPRORAS IS INITIAL.
                    READ TABLE ADJBEWTS INTO DUMMY_WT
                      WITH KEY TABLE_LINE = SLGART.
                    IF SY-SUBRC = 0 OR ADJUSTPRORA = 'X'.
                      IF NOT FOR_B IS INITIAL.
                        IF      NOT SPLITDAYSB IS INITIAL
                            AND NOT SPLITDAYST IS INITIAL.
                          MULTIPLY BETRG BY SPLITDAYST.
                          DIVIDE   BETRG BY SPLITDAYSB.
                        ENDIF.
                      ENDIF.
                      IF NOT FOR_A IS INITIAL.
                        IF      NOT SPLITDAYSA IS INITIAL
                            AND NOT SPLITDAYST IS INITIAL.
                          MULTIPLY BETRG BY SPLITDAYST.
                          DIVIDE   BETRG BY SPLITDAYSA.
                        ENDIF.
                      ENDIF.
                    ENDIF.
                  ENDIF.
                  IF DEBUGLEVEL > 3.
                    WRITE: / 'RT :', OUT_SEQNR, W_RT-APZNR,
                      'from:', FOR_B, 'to:', FOR_A,
                      W_RT-LGART, W_RT-V0TYP, W_RT-V0ZNR,
                      W_RT-BETRG CURRENCY '2',
                      BETRG CURRENCY '2'.
                  ENDIF.

* Special treatment for selected wage types
                  CLEAR SPECIALINS.
                  IF NOT ADJUST1800 IS INITIAL.
                    IF SLGART = '1800'. CONTINUE. ENDIF.
                    IF SLGART = '1810'. CONTINUE. ENDIF.
                    IF SLGART = '1804' OR SLGART = '1808'.
                      SLGART = '1800'.
                      SPECIALINS = 'X'.
                    ENDIF.
                    IF SLGART = '1814' OR SLGART = '1818'.
                      SLGART = '1810'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.
                  IF NOT ADJUST1820 IS INITIAL.
                    IF SLGART = '1820'. CONTINUE. ENDIF.
                    IF SLGART = '1830'. CONTINUE. ENDIF.
                    IF SLGART = '1824' OR SLGART = '1828'.
                      SLGART = '1820'.
                      SPECIALINS = 'X'.
                    ENDIF.
                    IF SLGART = '1834' OR SLGART = '1838'.
                      SLGART = '1830'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.
                  IF NOT ADJUST1900 IS INITIAL.
                    IF SLGART = '1900'. CONTINUE. ENDIF.
                    IF SLGART = '1904' OR SLGART = '1908'.
                      SLGART = '1900'.
                      SPECIALINS = 'X'.
                    ENDIF.
                  ENDIF.

* Detect whether the wage type is actually needed; in this
* case assign the value to the 'before' or 'after' field.
                  READ TABLE BENTRIES INTO BENTRY
                    WITH KEY WT = SLGART.
                  IF SY-SUBRC = 0.
                    KEY_BENTRY = SY-TABIX.

                    IF NOT ADJUSTDELTA IS INITIAL.
                      READ TABLE DELTAWTS INTO DUMMY_WT
                        WITH KEY TABLE_LINE = SLGART.
                      IF SY-SUBRC = 0.
                        IS_DELTA = 'X'.
                      ELSE.
                        IS_DELTA = SPACE.
                      ENDIF.
                    ENDIF.

                    SELECT SINGLE MSEHI INTO MSEHI FROM T538A
                      WHERE ZEINH = W_RT-ZEINH.

                    IF NOT FOR_B IS INITIAL.
                      IF NOT SPECIALINS IS INITIAL.
                        IF BENTRY-BTB IS INITIAL.
                          BENTRY-BTB = BETRG.
                        ELSE.
                          BENTRY-BTB = BENTRY-BTB - BETRG.
                        ENDIF.
                      ELSE.
                        IF IS_DELTA IS INITIAL.
                          BENTRY-BTB = BETRG.
                        ELSE.
                          BENTRY-BTB = BETRG - BENTRY-BTB.
                        ENDIF.
                      ENDIF.
                      BENTRY-CUB = W_RT-RTE_CURR.
                      IF BENTRY-CUB IS INITIAL.
                        BENTRY-CUB = W_RT-AMT_CURR.
                      ENDIF.
                      IF BENTRY-CUB IS INITIAL.
                        BENTRY-CUB = T_RESULT99-INTER-VERSC-WAERS.
                      ENDIF.
                    ENDIF.
                    IF NOT FOR_A IS INITIAL.
                      IF NOT SPECIALINS IS INITIAL.
                        IF BENTRY-BTA IS INITIAL.
                          BENTRY-BTA = BETRG.
                        ELSE.
                          BENTRY-BTA = BENTRY-BTA - BETRG.
                        ENDIF.
                      ELSE.
                        IF IS_DELTA IS INITIAL.
                          BENTRY-BTA = BETRG.
                        ELSE.
                          BENTRY-BTA = BETRG - BENTRY-BTB.
                        ENDIF.
                      ENDIF.
                      BENTRY-CUA = W_RT-RTE_CURR.
                      IF BENTRY-CUA IS INITIAL.
                        BENTRY-CUA = W_RT-AMT_CURR.
                      ENDIF.
                      IF BENTRY-CUA IS INITIAL.
                        BENTRY-CUA = T_RESULT99-INTER-VERSC-WAERS.
                      ENDIF.
                    ENDIF.
                    MODIFY BENTRIES FROM BENTRY INDEX KEY_BENTRY.
                    IF DEBUGLEVEL > 2.
                      WRITE: / 'RT*:', OUT_SEQNR, W_RT-APZNR,
                        'from:', FOR_B, 'to:', FOR_A,
                        W_RT-LGART, W_RT-V0TYP, W_RT-V0ZNR,
                        W_RT-BETRG CURRENCY '2',
                        BETRG CURRENCY '2',
                        W_RT-AMT_CURR, MSEHI, BENTRY-ID, IS_DELTA.
                    ENDIF.
                  ENDIF.

                ENDLOOP.
              ENDIF. " reading payroll result
            ENDIF.
          ENDDO.

        ENDIF. " mode of cluster read

      ENDIF. " CD_READ_LAST succesfull
    ENDIF. " CU_READ_RGDIR succesfull
  ENDDO.
ENDFORM. " end of runRPCALAC



*
* create a word document based on a form
*
FORM CREATEWORDFORMDOC
    USING LINES TYPE TABLE.

  DATA:
    LINE          TYPE STRING,
    LINEOUT(100)  TYPE C.

  SKIP.
  IF NOT PFNAME IS INITIAL.
    CALL FUNCTION 'RH_CHECK_WWORD_SUPPORT'
      EXCEPTIONS
        NO_BATCH                   = 1
        INTERNAL_ERROR             = 2
        WWORD_NOT_INSTALLED        = 3
        WRONG_FRONTEND_OS          = 4
        LANGUAGE_PROBLEMS_POSSIBLE = 5
        OTHERS                     = 6.
  ENDIF.
* MS Word not available
  IF ( PFNAME IS INITIAL ) OR ( SY-SUBRC <> 0 ).
    FORMAT COLOR COL_NEGATIVE.
    WRITE: / 'No support for MS Word on this PC.'.
    WRITE: / 'Error details:'.
    CASE SY-SUBRC.
      WHEN 1. WRITE: 'Not allowed in Batch mode (code 1)'.
      WHEN 2. WRITE: 'Internal error (code 2)'.
      WHEN 3. WRITE: 'Word not installed (code 3)'.
      WHEN 4. WRITE: 'Wrong frontend operating system (code 4)'.
      WHEN 5. WRITE: 'Language problems possible (code 5)'.
      WHEN 6. WRITE: 'Other problem (code 6)'.
    ENDCASE.
    SKIP.
    FORMAT COLOR COL_POSITIVE.
    WRITE: / 'The collected infomation will be shown below:'.
    SKIP.
    FORMAT COLOR COL_NORMAL.
    LOOP AT LINES INTO LINE.
      WRITE: / LINE+1.
    ENDLOOP.
* MS Word is available
  ELSE.
    DATA:
      FILENAME     TYPE STRING,
      DATA_TABLE   TYPE TABLE OF STRING.

    FILENAME  = PFNAME.

* copy the parameter data into the fubas table of data
    DATA:
      LINETYPE(1)  TYPE C,
      POS          TYPE I,
      ITEMS        TYPE TABLE OF STRING,
      FILEFORM     TYPE RLGRAP-FILENAME VALUE 'n:\pa_form.doc',
      FILEDATA     TYPE RLGRAP-FILENAME VALUE 'pa_data',
      FILEPATH     TYPE RLGRAP-FILENAME VALUE 'c:\',
      FIELDS       TYPE TABLE OF STRING,
      FDATALINE    TYPE DATALINE,
      FDATA        TYPE TABLE OF DATALINE,
      FNAME        TYPE STRING.
    FIELD-SYMBOLS:
      <FS>.

    IF NOT PFNAME IS INITIAL.
      FILEFORM = PFNAME.
    ENDIF.
    IF NOT PFPATH IS INITIAL.
      FILEPATH = PFPATH.
    ENDIF.
    LOOP AT LINES INTO LINE.
      IF NOT LINE IS INITIAL.
        SPLIT LINE AT SEPITEMS INTO TABLE ITEMS.
        LOOP AT ITEMS INTO LINE.
          CASE SY-TABIX.
            WHEN 1.
              FNAME = LINE.
              APPEND FNAME TO FIELDS.
            WHEN 2.
              ASSIGN COMPONENT FNAME OF STRUCTURE FDATALINE TO <FS>.
              <FS> = LINE.
            WHEN OTHERS.
              WRITE: 'format error:', LINE.
          ENDCASE.
        ENDLOOP.
      ENDIF.
    ENDLOOP.
    APPEND FDATALINE TO FDATA.

    CALL FUNCTION 'MS_WORD_OLE_FORMLETTER'
      EXPORTING
        WORD_DOCUMENT             = FILEFORM
*         HIDDEN                    = 0
*         WORD_PASSWORD             =
*         PASSWORD_OPTION           = 1
        FILE_NAME                 = FILEDATA
*         NEW_DOCUMENT              =
        DOWNLOAD_PATH             = FILEPATH
        PRINT                     = PFPRINT
      TABLES
        DATA_TAB                  = FDATA
        FIELDNAMES                = FIELDS
     EXCEPTIONS
       INVALID_FIELDNAMES        = 1
       USER_CANCELLED            = 2
       DOWNLOAD_PROBLEM          = 3
       COMMUNICATION_ERROR       = 4
       OTHERS                    = 5.
    IF SY-SUBRC <> 0.
      DATA:
        DESC    TYPE STRING VALUE 'unknown'.
      CASE SY-SUBRC.
        WHEN  1.  DESC = 'Invalid filenames'.
        WHEN  2.  DESC = 'User cancelled'.
        WHEN  3.  DESC = 'Download problem'.
        WHEN  4.  DESC = 'Communication error'.
        WHEN  5.  DESC = 'Others'.
      ENDCASE.
      WRITE: / 'Cannot launch MS Word! Reason:', DESC.
    ELSE.
      WRITE: / 'MS Word launched in a separate window'.
    ENDIF.

  ENDIF.
ENDFORM. "createWordFormDoc


*
* create a word document
*
FORM CREATEWORDDOC
    USING LINES TYPE TABLE.

  DATA:
    LINE          TYPE STRING,
    LINEOUT(100)  TYPE C.

  SKIP.
  CALL FUNCTION 'RH_CHECK_WWORD_SUPPORT'
    EXCEPTIONS
      NO_BATCH                   = 1
      INTERNAL_ERROR             = 2
      WWORD_NOT_INSTALLED        = 3
      WRONG_FRONTEND_OS          = 4
      LANGUAGE_PROBLEMS_POSSIBLE = 5
      OTHERS                     = 6.
* MS Word not available
  IF SY-SUBRC <> 0.
    FORMAT COLOR COL_NEGATIVE.
    WRITE: / 'No support for MS Word on this PC.'.
    WRITE: / 'Error details:'.
    CASE SY-SUBRC.
      WHEN 1. WRITE: 'Not allowed in Batch mode (code 1)'.
      WHEN 2. WRITE: 'Internal error (code 2)'.
      WHEN 3. WRITE: 'Word not installed (code 3)'.
      WHEN 4. WRITE: 'Wrong frontend operating system (code 4)'.
      WHEN 5. WRITE: 'Language problems possible (code 5)'.
      WHEN 6. WRITE: 'Other problem (code 6)'.
    ENDCASE.
    SKIP.
    FORMAT COLOR COL_POSITIVE.
    WRITE: / 'The collected infomation will be shown below:'.
    SKIP.
    FORMAT COLOR COL_NORMAL.
    LOOP AT LINES INTO LINE.
      WRITE: / LINE+1.
    ENDLOOP.
* MS Word is available
  ELSE.
    DATA:
      FILENAME     TYPE STRING,
      DATA_TABLE   TYPE TABLE OF STRING.

    FILENAME  = PFNAME.

* copy the parameter data into the fubas table of data
    DATA:
      LINETYPE(1)  TYPE C,
      POS          TYPE I,
      ITEMS        TYPE TABLE OF STRING.

    LOOP AT LINES INTO LINE.
      CLEAR LINEOUT.
      IF NOT LINE IS INITIAL.
        LINETYPE = LINE(1).
        SPLIT LINE+1 AT SEPITEMS INTO TABLE ITEMS.
        LOOP AT ITEMS INTO LINE.
          CASE SY-TABIX.
            WHEN 1.
              POS = 0.
            WHEN 2.
              IF LINETYPE = IDNORMAL.
                POS = 51.
              ELSE.
                POS = 26.
              ENDIF.
            WHEN 3.
              POS = 53.
            WHEN OTHERS.
              POS = ( SY-TABIX - 1 ) * 30.
          ENDCASE.
          LINEOUT+POS = LINE.
        ENDLOOP.
      ENDIF.
      APPEND LINEOUT TO DATA_TABLE.
    ENDLOOP.

    IF 1 = 1.
      CALL FUNCTION 'RH_START_WWORD_WITH_DATA'
        EXPORTING
          DATA_FILENAME             = FILENAME
*          DATA_FILETYPE             = pftype
*         DATA_FILELENGTH           =
*         DATA_PATH_FLAG            = 'W'
*         DATA_ENVIRONMENT          =
          DATA_TABLE                = DATA_TABLE
          WAIT                      = ' '
*          DELETE_FILE               = pfdelete
        EXCEPTIONS
          NO_BATCH                  = 1
          WWORD_NOT_INSTALLED       = 2
          INTERNAL_ERROR            = 3
          CANCELLED                 = 4
          DOWNLOAD_ERROR            = 5
          NO_AUTHORITY              = 6
          FILE_NOT_DELETED          = 7
          OTHERS                    = 8.
      IF SY-SUBRC <> 0.
        DATA:
          DESC    TYPE STRING VALUE 'unknown'.
        CASE SY-SUBRC.
          WHEN  1.  DESC = 'not in batch mode'.
          WHEN  2.  DESC = 'Word not installed'.
          WHEN  3.  DESC = 'Internal error'.
          WHEN  4.  DESC = 'Cancelled'.
          WHEN  5.  DESC = 'Download error'.
          WHEN  6.  DESC = 'No authority'.
          WHEN  7.  DESC = 'File not deleted'.
          WHEN  8.  DESC = 'Others'.
        ENDCASE.
        WRITE: / 'Cannot launch MS Word! Reason:', DESC.
      ELSE.
        WRITE: / 'MS Word launched in a separate window'.
      ENDIF.
    ENDIF.

  ENDIF.
ENDFORM. "createWordDoc