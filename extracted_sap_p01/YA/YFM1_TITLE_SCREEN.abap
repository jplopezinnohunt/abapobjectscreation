
REPORT YFM1_TITLE_SCREEN.

********************************************************************
* PROGRAM        YBBUR001                                          *
* TITLE          Extended Daily - Yearly detail by budget code     *
* AUTHOR         A. AHOUNOU                                        *
* DATE WRITTEN   30/05/2005                                        *
* R/3 RELEASE    4.7                                               *
********************************************************************
* COPIED FROM    XXX                                               *
* TITLE          XXX                                               *
********************************************************************
* PROGRAM TYPE   Report                                            *
* DEV.CLASS      YB : Regular Budget                               *
* LOGICAL DB     F1M                                               *
********************************************************************
* CHANGE HISTORY                                                   *
* Date         By                   Correction Number              *
*                                                                  *
* 1. 17/10/2005 - Illya Konakov   IKON171005                       *
*    Addition of the node FMTOX instead of module                  *
*    FM_TOTALS_READ_WITH_RANGES (advised from SAP OSS)             *
* 2. 31/10/2006 - Tal Deborah   DTAL311006                         *
*    Improve performance by using FMFINT-Fund texts to get fund title*
* 3. 22/01/2007 - Tal Deborah   DTAL220107                         *
*    set default biennium values for budget fiscal year            *
* 4. 09/01/2008 - Illya Konakov   IKON090108                       *
*    Addition of the field fmfint-bezeich                          *
* 5. 22/09/2008 - Illya Konakov IKON220908                         *
*    Take the full title for fund
* 6. 10/05/2009 - Sara Rocha                                       *
*    Changed RE_USE_ALV parameter i_save to 'U' to allow only user *
*    specific layouts.                                             *                                *
********************************************************************
*                      TYPE-POOLS                                  *
********************************************************************
TYPE-POOLS: FMFI,  " Find management updating FI
            SLIS,  " Global types for generic cunning building blocks
            RSDS.  " Types for free memoranda

*******************************************************************
*                      NODES                                      *
*******************************************************************
NODES:  FKRS,           " Financial Management Areas
        FFND,
        FCTR,
        FPOS,
        FMAA,
        FMTOX,
        BPBYX,          " Totals records: annual budget
        EPBY.           " Annual budget line items


*******************************************************************
*                     TABLES                                      *
*******************************************************************
TABLES: FMHICTR,        " FIFB: DB Table for Hierarchy Relations
                        " in a  center
        FMFMIT2,        " FIFM: Internal Structure in Reporting
        FMFCTR,         " FIFM: Funds Center Master Record
        BPBK,           " Doc.Header Controlling Obj
        FMFINCODE,
*DTAL311006
        FMFINT,         " Fund texts
        FMHISV,
         BPVJ.

*******************************************************************
* Definition of internal tables                                   *
*******************************************************************
DATA: BEGIN OF G_T_ITEM OCCURS 100,
        BUCODE(30) TYPE  C,              " Budget Code
        SGTEXT     LIKE  BPBK-SGTEXT,    " Budget Code Title
        BEZEICH    LIKE  FMFINT-BEZEICH, "Fund name - IKON090108
        FIKRS      LIKE  FKRS-FIKRS,     " Financial management area
        FONDS      LIKE  FMAA-FONDS,   " Fund
        FICTR LIKE  FMAA-FICTR,  " Fund Center
        CTR_OBJNR  LIKE  FMAA-CTR_OBJNR, " Object number
        FWAER      LIKE  BPBYX-FWAER,     " Currency
        WLJHR      LIKE  EPBY-WLJHR,     " Allocation
        WLJHK      LIKE BPBYX-WLJHK,      " Distibuted allocation
        BTR005     LIKE  FMSU1-BTR001,   " Allotment year 1
        BTR001     LIKE  FMSU1-BTR001,   " Expenditures year 1
        BTR002     LIKE  FMSU1-BTR001,   " Undelivered Orders 1
        FKBTR      LIKE  FMFMIT2-FKBTR,  " Total expenses
        BTR003     LIKE  FMSU1-BTR001,   " Available Funds onAllotment1
        BTR004     LIKE  FMSU1-BTR001,   " Exécution Rate
        BTR006     LIKE  FMSU1-BTR001,   " Funds Blocked
        ERFDAT     LIKE FMFINCODE-ERFDAT,
        TYPE       LIKE FMFINCODE-TYPE,        "type of fund
        BTR007     LIKE  FMSU1-BTR001,   " Available Funds onAllocation
        BTR008     LIKE  FMSU1-BTR001,   " Allotment year 2
        BTR009     LIKE  FMSU1-BTR001,   " Expenditures year 2
        BTR010     LIKE  FMSU1-BTR001,   " Undelivered Orders year 2
        BTR011     LIKE  FMSU1-BTR001,   " Available Funds onAllotment2
*        fname      like   fmaa-fname, " Fund name
        STITLE(250) TYPE C, "Fund title - IKON220908
      END OF G_T_ITEM.

*******************************************************************
*                      DATA                                       *
*******************************************************************
DATA: BEGIN OF G_T_ITEM2 OCCURS 0.
        INCLUDE STRUCTURE G_T_ITEM.
DATA: END OF G_T_ITEM2.

DATA: BEGIN OF G_T_ITEM3 OCCURS 0.
        INCLUDE STRUCTURE G_T_ITEM.
DATA: END OF G_T_ITEM3.

DATA: BEGIN OF G_T_ITEM4 OCCURS 0.
        INCLUDE STRUCTURE G_T_ITEM.
DATA: END OF G_T_ITEM4.

* table pour lecture du budget du parent
DATA: BEGIN OF G_T_ITEM_TEMP OCCURS 0.
        INCLUDE STRUCTURE G_T_ITEM.
DATA: END OF G_T_ITEM_TEMP.

DATA: BEGIN OF T_PARENTS OCCURS 0,
        FONDS   LIKE FMAA-FONDS,       " AEM181201+
        N         TYPE I,                  " AEM181201+
        CTR_OBJNR LIKE FMAA-CTR_OBJNR,
        PARENT_ST LIKE FMHISV-PARENT_ST,
      END OF T_PARENTS.


* Table to count number of fund center per fund
DATA: BEGIN OF T_N_FUNDCENTER OCCURS 0,
        FONDS   LIKE FMAA-FONDS,
        N         TYPE I,
      END OF T_N_FUNDCENTER.


DATA: BEGIN OF T_COLLECT OCCURS 0,
        FONDS   LIKE FMAA-FONDS,  " Fund
        FIKRS     LIKE FKRS-FIKRS,    " Financial management area
        FICTR     LIKE FMAA-FICTR,    " Funds center
        FISTL     LIKE FMAA-FICTR,
        FKBTR_BL  LIKE FMFMIT2-FKBTR, " Funds Blocked
        FKBTR_EX_1  LIKE FMFMIT2-FKBTR, " Expenditure
        FKBTR_UN_1  LIKE FMFMIT2-FKBTR, " Undelivered orders
        FKBTR_EX_2  LIKE FMFMIT2-FKBTR, " Expenditure
        FKBTR_UN_2  LIKE FMFMIT2-FKBTR, " Undelivered orders
        CTR_OBJNR LIKE FMAA-CTR_OBJNR,
        ERFDAT LIKE FMFINCODE-ERFDAT, "creation date
        TYPE LIKE FMFINCODE-TYPE,        "type of fund
      END OF   T_COLLECT.


DATA: BEGIN OF T_FOND OCCURS 0.
        INCLUDE STRUCTURE RANGE_C10.
DATA: END OF T_FOND.

DATA: BEGIN OF T_FISTL OCCURS 0.
        INCLUDE STRUCTURE RANGE_C16.
DATA: END OF T_FISTL.

DATA: BEGIN OF T_FICTR OCCURS 0.
        INCLUDE STRUCTURE RANGE_C16.
DATA: END OF T_FICTR.

DATA: BEGIN OF T_FMIT OCCURS 0.
        INCLUDE STRUCTURE FMFMIT2.
DATA: END OF T_FMIT.

DATA: BEGIN OF G_T_FKRS OCCURS 10,
         FIKRS LIKE FKRS-FIKRS,
      END OF G_T_FKRS.

DATA: G_T_MASTER_DATA LIKE FMAA OCCURS 300 WITH HEADER LINE.

DATA: G_T_FIELDCAT TYPE SLIS_T_FIELDCAT_ALV,
      G_T_SORT     TYPE SLIS_T_SORTINFO_ALV,
      G_F_LAYOUT   TYPE SLIS_LAYOUT_ALV,
      G_T_EVENTS   TYPE SLIS_T_EVENT.

" Document number from budget allocation & structure planning
DATA: WA_BELNR LIKE EPBY-BELNR.

DATA DYN_SEL    TYPE RSDS_TYPE.

DATA WA_TRANGE  TYPE RSDS_TRANGE.


DATA: WA_BUCODE(27) TYPE C,
      WA_TITLE LIKE BPBK-SGTEXT,
      WA_ITEM  LIKE G_T_ITEM,
      WA_ITEM2  LIKE G_T_ITEM,
      WA_ITEM3  LIKE G_T_ITEM,
      WA_FICTR LIKE FMAA-FICTR,
      WA_BTR005 LIKE FMSU1-BTR001,
      WA_PARENTS LIKE T_PARENTS,
      WA_BPVJ LIKE BPVJ.


* For edition of % Execution rate
DATA: W_SUM_EXP         LIKE   FMFMIT2-FKBTR.   " Sum Total Expenses
DATA: W_SUM_ALL         LIKE   EPBY-WLJHR.      " Sum Total Alloc.
DATA: W_PCT_EX_RATE     LIKE   FMFMIT2-FKBTR.   " % Execution Rate

* DTAL16012003
DATA: W_BIEN_YEAR       TYPE I.        " indicator for biennium year

*IKON09062005
DATA: BEGIN OF T_FUND_MD OCCURS 0,
        BUCODE(30) TYPE  C,              " Budget Code
        SGTEXT     LIKE  BPBK-SGTEXT,    " Budget Code Title
        FIKRS      LIKE  FKRS-FIKRS,     " Financial management area
        FONDS      LIKE  FMAA-FONDS,     " Fund
        FICTR      LIKE  FMAA-FICTR,     " Fund Center
        CTR_OBJNR  LIKE  FMAA-CTR_OBJNR, " Object number
        FUND_TYPE  LIKE  FMAA-FUND_TYPE, " Fund Type
        ERFDAT     LIKE  FMFINCODE-ERFDAT,
*        fname      like   fmaa-fname, " Fund name
      END OF T_FUND_MD.

*IKON220908
DATA: W_ONAME LIKE THEAD-TDNAME,
      W_STITLE(400),
      W_SLEN TYPE I,
      W_TLEN TYPE I.
DATA: T_TLINES TYPE TABLE OF TLINE WITH HEADER LINE.

*******************************************************************
*                      SELECTION SCREEN                           *
*******************************************************************
SELECTION-SCREEN SKIP.
SELECTION-SCREEN BEGIN OF BLOCK FUND_TYPE WITH FRAME.

SELECT-OPTIONS S_FTYPE FOR FMAA-FUND_TYPE.

***IKON030609 - add selection on FMFINT-BEZEICH
SELECT-OPTIONS S_RPERS FOR FMFINT-BEZEICH.
SELECTION-SCREEN END OF BLOCK FUND_TYPE.



***IKON171005 - start of block
INITIALIZATION.
    W_BIEN_YEAR = SY-DATUM(4) MOD 2.
    IF W_BIEN_YEAR = 1.
       P_FYR_FR = SY-DATUM(4) - 1.
       P_FYR_TO = SY-DATUM(4).
*DTAL220107
       S_GJ_BUD-SIGN = 'I'.
       S_GJ_BUD-OPTION = 'BT'.
       S_GJ_BUD-LOW = SY-DATUM(4) - 1.
       S_GJ_BUD-HIGH = SY-DATUM(4).
       APPEND S_GJ_BUD.
    ELSE.
       P_FYR_FR = SY-DATUM(4).
       P_FYR_TO = SY-DATUM(4) + 1.
*DTAL220107
       S_GJ_BUD-SIGN = 'I'.
       S_GJ_BUD-OPTION = 'BT'.
       S_GJ_BUD-LOW = SY-DATUM(4).
       S_GJ_BUD-HIGH = SY-DATUM(4) + 1.
       APPEND S_GJ_BUD.
    ENDIF. "w_bien_year.
***IKON171005 - end of block

***IKON220908
    S_FTYPE-LOW = '001'.
    S_FTYPE-HIGH = '999'.
    S_FTYPE-SIGN = 'I'.
    S_FTYPE-OPTION = 'BT'.
    APPEND S_FTYPE.


*at selection-screen on s_fikrs.
* loop at s_fikrs.
*   if s_fikrs-low = ' ' or s_fikrs-high = ' '.
*      s_ftype-low = ' '.
*      s_ftype-high = ' '.
*      append s_ftype.
*   endif.
*     s_ftype-sign = 'I'.
*     s_ftype-option = 'BT'.
*     append s_ftype.
*    else.
*      s_ftype-low = '100'.
*      s_ftype-high = '200'.
*      s_ftype-sign = 'I'.
*      s_ftype-option = 'BT'.
*      append s_ftype.
*   endif.
* endloop. "s_fikrs
***

*{   INSERT         DUPK900005                                        1
*IKON110408 - Hide some selection parameters
AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF SCREEN-NAME = 'P_FU_GRP' OR
       SCREEN-NAME = 'P_FC_GRP' OR
       SCREEN-NAME = 'P_CI_GRP' OR
       SCREEN-NAME = '%F019045_1000' OR
       SCREEN-NAME = '%F019056_1000' OR
       SCREEN-NAME = '%F019076_1000'.
      SCREEN-ACTIVE = '0'.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP. "screen
*}   INSERT

*******************************************************************
*                     START-OF-SELECTION                          *
*******************************************************************
*start-of-selection.

*******************************************************************
*                     START-OF-SELECTION                          *
*******************************************************************

START-OF-SELECTION.

*******************
*IF s_fikrs-low = ' ' and s_fikrs-high = ' '.
*
*    s_ftype-low = '001'.
*    s_ftype-high = '999'.
*    s_ftype-sign = 'I'.
*    s_ftype-option = 'BT'.
*
*elseif s_fikrs-low <> 'UNES'.
*
*    s_ftype-low = '100'.
*    s_ftype-high = '999'.
*    s_ftype-sign = 'I'.
*    s_ftype-option = 'BT'.
*
*elseif s_fikrs-low = 'UNES'.
*
*    s_ftype-low = '001'.
*    s_ftype-high = '099'.
*    s_ftype-sign = 'I'.
*    s_ftype-option = 'BT'.
*
*
*    append s_ftype.
*
*endif.
********************
GET FKRS FIELDS FIKRS.

GET FMAA FIELDS FONDS FUND_TYPE DATAB_FONDS
                FICTR FIPEX .

  CHECK FMAA-FUND_TYPE IN S_FTYPE.

***IKON171005 - form's call commented
*  perform 00_get_expenditures.

  PERFORM 01_GET_FCTR_INFO.

***IKON171005 - start of block - instead of 00_get_expenditures
  GET FMTOX.
    IF ( FMTOX-WRTTP = '54' OR
         FMTOX-WRTTP = '50' OR
         FMTOX-WRTTP = '51' OR
         FMTOX-WRTTP = '52' OR
         FMTOX-WRTTP = '80' OR
         FMTOX-WRTTP = '81' OR
         FMTOX-WRTTP = '60' OR
         FMTOX-WRTTP = '58' OR
         FMTOX-WRTTP = '57' OR
         FMTOX-WRTTP = '61' OR
         FMTOX-WRTTP = '66' ) AND
       FMTOX-STATS <> 'X' .

      CLEAR: T_COLLECT, T_FUND_MD.
      READ TABLE T_FUND_MD WITH KEY FIKRS = FKRS-FIKRS FONDS = FMTOX-FONDS.
      T_COLLECT-FONDS = FMTOX-FONDS. "fmaa-fonds.
      T_COLLECT-FIKRS = T_FUND_MD-FIKRS. "fkrs-fikrs.
      T_COLLECT-FICTR = FMTOX-FICTR. "fmaa-fictr.
      T_COLLECT-ERFDAT = T_FUND_MD-ERFDAT. "fmaa-erfdat_fonds.
      T_COLLECT-TYPE = T_FUND_MD-FUND_TYPE. "fmaa-fund_type.

      W_BIEN_YEAR = FMTOX-GJAHR MOD 2.

      IF FMTOX-WRTTP = '80'.
        T_COLLECT-FKBTR_BL = ( FMTOX-FKBTRP +
                               FMTOX-FKBTRC +
                               FMTOX-FKBTRW ) * -1. "Funds Blocked
       ELSEIF FMTOX-WRTTP = '54' OR
              FMTOX-WRTTP = '57' OR
              FMTOX-WRTTP = '61' OR
              FMTOX-WRTTP = '66'.
         IF W_BIEN_YEAR = 0.
           T_COLLECT-FKBTR_EX_1 = ( FMTOX-FKBTRP +
                                    FMTOX-FKBTRC +
                                    FMTOX-FKBTRW ).    "Expenditures
           T_COLLECT-FKBTR_EX_2 = 0.
          ELSE.
            T_COLLECT-FKBTR_EX_2 = ( FMTOX-FKBTRP +
                                     FMTOX-FKBTRC +
                                     FMTOX-FKBTRW ).    "Expenditures
            T_COLLECT-FKBTR_EX_1 = 0.
         ENDIF. "w_bien_year
       ELSE. "fmtox-wrttp
         IF W_BIEN_YEAR = 0.
           T_COLLECT-FKBTR_UN_1 = ( FMTOX-FKBTRP +
                                    FMTOX-FKBTRC +
                                    FMTOX-FKBTRW ).    "Undelivered
           T_COLLECT-FKBTR_UN_2 = 0.
          ELSE.
            T_COLLECT-FKBTR_UN_2 = ( FMTOX-FKBTRP +
                                     FMTOX-FKBTRC +
                                     FMTOX-FKBTRW ).    "Undelivered
            T_COLLECT-FKBTR_UN_1 = 0.
         ENDIF. "w_bien_year
      ENDIF. "fmtox-wrttp = '80'

      IF FMTOX-FIPEX = 'REVENUE' OR
         FMTOX-FIPEX = 'GAINS'.
       ELSE.
        COLLECT T_COLLECT.
      ENDIF. "fmtox-fipex

    ENDIF. "fmtox-wrttp... and fmtox-stats
***IKON171005 - end of block

GET BPBYX.

  CHECK BPBYX-WRTTP = '43'.
  READ TABLE T_FUND_MD WITH KEY FONDS = BPBYX-FONDS
                                FICTR = BPBYX-FICTR.
  CHECK SY-SUBRC IS INITIAL.

  PERFORM 02_COLLECT_ALLOTMENT.


*******************************************************************
*                     END-OF-SELECTION                            *
*******************************************************************
END-OF-SELECTION.

  PERFORM 03_ASSOCIATE_EXPEN.

  PERFORM 07_RESTRICT_HIERARCHY.

  PERFORM 09_EDITION.

***********************************************************************
*
*                    FORM 00_GET_EXPENDITURES
*
***********************************************************************
*
* --> input
*
* <-- output
*
***********************************************************************

FORM 00_GET_EXPENDITURES.

  CLEAR T_FOND.
  REFRESH T_FOND.
  T_FOND-SIGN = 'I'.
  T_FOND-OPTION = 'EQ'.
  T_FOND-LOW = FMAA-FONDS.
  APPEND T_FOND.

  CLEAR T_FISTL.
  REFRESH T_FISTL.
  T_FISTL-SIGN = 'I'.
  T_FISTL-OPTION = 'EQ'.
  T_FISTL-LOW = FMAA-FICTR.
  APPEND T_FISTL.

  REFRESH T_FMIT.

*******************   CALL FUNCTION  ********************
***********  FM_TOTALS_READ_WITH_RANGES  ****************
  CALL FUNCTION 'FM_TOTALS_READ_WITH_RANGES'
    EXPORTING
      I_FIKRS   = FKRS-FIKRS
    TABLES
      T_RFISTL  = T_FISTL
      T_RFONDS  = T_FOND
      T_FMITTAB = T_FMIT.

*DT22102002 - ADD CONTROL to exclude all statistical commitments

  LOOP AT T_FMIT WHERE   ( RWRTTP = '54'
                        OR RWRTTP = '50'
                        OR RWRTTP = '51'
                        OR RWRTTP = '52'
                        OR RWRTTP = '80'
                        OR RWRTTP = '81'
                        OR RWRTTP = '60'
                        OR RWRTTP = '58'
                        OR RWRTTP = '57'
                        OR RWRTTP = '61'
                        OR RWRTTP = '66' )
                        AND  RSTATS NE 'X' .

    CLEAR T_COLLECT.
    T_COLLECT-FONDS   = FMAA-FONDS.
    T_COLLECT-FIKRS     =  FKRS-FIKRS.
    T_COLLECT-FICTR     = FMAA-FICTR.


    SELECT SINGLE * FROM FMFINCODE
    WHERE FINCODE EQ  FMAA-FONDS AND TYPE IN S_FTYPE.

    IF SY-SUBRC EQ 0.
      T_COLLECT-ERFDAT = FMFINCODE-ERFDAT.
      T_COLLECT-TYPE = FMFINCODE-TYPE.
    ENDIF.

*    t_collect-ctr_objnr = fmaa-ctr_objnr.

    W_BIEN_YEAR = T_FMIT-RYEAR+0(4) MOD 2.

* ARK18102001-1 Begin
    IF T_FMIT-RWRTTP = '80'.
*     the sign is changed because of a difference between
*     table data and stadards reports in SAP
      T_COLLECT-FKBTR_BL = T_FMIT-FKBTR * -1. "Funds Blocked
    ELSEIF   T_FMIT-RWRTTP = '54'
       OR T_FMIT-RWRTTP = '57'          " FV14122001-3
       OR T_FMIT-RWRTTP = '61'          " FV14122001-3
       OR T_FMIT-RWRTTP = '66'.         " FV14122001-3
      IF W_BIEN_YEAR = 0.
        T_COLLECT-FKBTR_EX_1 = T_FMIT-FKBTR.    "Expenditures
        T_COLLECT-FKBTR_EX_2 = 0.
      ELSE.
        T_COLLECT-FKBTR_EX_2 = T_FMIT-FKBTR.    "Expenditures
        T_COLLECT-FKBTR_EX_1 = 0.
      ENDIF.
    ELSE.
      IF W_BIEN_YEAR = 0.
        T_COLLECT-FKBTR_UN_1 = T_FMIT-FKBTR.    "Undelivered
        T_COLLECT-FKBTR_UN_2 = 0.
      ELSE.
        T_COLLECT-FKBTR_UN_2 = T_FMIT-FKBTR.    "Undelivered
        T_COLLECT-FKBTR_UN_1 = 0.
      ENDIF.
    ENDIF.
* ARK18102001-1 End


* FV14122001-3
    IF   T_FMIT-RFIPEX = 'REVENUE'          " FV14122001-3
     OR  T_FMIT-RFIPEX = 'GAINS'.           " FV14122001-3
    ELSE.
      COLLECT T_COLLECT.
    ENDIF.
* FV14122001-3
  ENDLOOP.
ENDFORM.                               " 00_get_expenditures



***********************************************************************
*
*                     FORM   01_get_fctr_info
*
***********************************************************************
*
* --> input
*
* <-- g_t_event
*
***********************************************************************
FORM   01_GET_FCTR_INFO.

*IKON09062005
  CLEAR T_FUND_MD.
  T_FUND_MD-FIKRS = FKRS-FIKRS.
  MOVE-CORRESPONDING FMAA TO T_FUND_MD.
  CONCATENATE FMAA-FONDS FMAA-FICTR
             INTO T_FUND_MD-BUCODE SEPARATED BY SPACE.
***IKON130509 - take ERFDAT from FMFINCODE, not from FMAA
  SELECT SINGLE ERFDAT
        INTO T_FUND_MD-ERFDAT
        FROM FMFINCODE
        WHERE FIKRS = FKRS-FIKRS
          AND FINCODE = FMAA-FONDS.
***  t_fund_md-erfdat = fmaa-erfdat_fonds.
  COLLECT T_FUND_MD.
ENDFORM.                                             " 01_get_fctr_info

***********************************************************************
*
*                     FORM  02_COLLECT_ALLOTMENT                      *
***********************************************************************
*
* --> input
*
* <-- output
*
***********************************************************************
FORM 02_COLLECT_ALLOTMENT.

* Allocation
  G_T_ITEM-WLJHR = BPBYX-WLJHR.
*AHOUNOU  30/07/2004
  G_T_ITEM-WLJHK = BPBYX-WLJHK.
*AHOUNOU  30/07/2004
* Allotment depending on the biennium
* DTAL16012003
  W_BIEN_YEAR = BPBYX-GJAHR+0(4) MOD 2.
*  if sy-datum+0(4) < bpbyx-gjahr+0(4).
  IF W_BIEN_YEAR = 0.
*AHOUNOU  30/07/2004
    G_T_ITEM-BTR005 = BPBYX-WLJHK.
*AHOUNOU  30/07/2004
    G_T_ITEM-BTR008 = 0.
  ELSE.
*AHOUNOU  30/07/2004
    G_T_ITEM-BTR008 = BPBYX-WLJHK.
*AHOUNOU  30/07/2004
    G_T_ITEM-BTR005 = 0.
  ENDIF.

*IKON09062005
  MOVE-CORRESPONDING T_FUND_MD TO G_T_ITEM.
  G_T_ITEM-TYPE = T_FUND_MD-FUND_TYPE.
  G_T_ITEM-SGTEXT = T_FUND_MD-SGTEXT.

  COLLECT G_T_ITEM.
ENDFORM.                                         " 02_COLLECT_ALLOTMENT


***********************************************************************
*
*                     FORM  03_ASSOCIATE_EXPEN
*
***********************************************************************
*
* --> input
*
* <-- output
*
***********************************************************************
*
*
*
*
*
***********************************************************************
*
FORM 03_ASSOCIATE_EXPEN.

*** Associate expenditures to budget code for edition
  LOOP AT T_COLLECT.

* Check If there is budget
    READ TABLE G_T_ITEM
    WITH KEY
      FONDS     = T_COLLECT-FONDS
      FIKRS     = T_COLLECT-FIKRS
      FICTR     = T_COLLECT-FICTR.
*      ctr_objnr = t_collect-ctr_objnr.

* If exists set alloc/allot to zero
* DTAL16012003
    IF SY-SUBRC = 0.
      CLEAR: G_T_ITEM-WLJHR,
*AHOUNOU  30/07/2004
             G_T_ITEM-WLJHK,
*AHOUNOU  30/07/2004
             G_T_ITEM-BTR005,
             G_T_ITEM-BTR008.
* Else initialize g_t_item
    ELSE.
      CLEAR G_T_ITEM.
      G_T_ITEM-FONDS   = T_COLLECT-FONDS.
      G_T_ITEM-FIKRS     = T_COLLECT-FIKRS.
      G_T_ITEM-FICTR     = T_COLLECT-FICTR.
*      g_t_item-ctr_objnr = t_collect-ctr_objnr.
      G_T_ITEM-TYPE = T_COLLECT-TYPE.
      G_T_ITEM-ERFDAT = T_COLLECT-ERFDAT.
      CONCATENATE T_COLLECT-FONDS T_COLLECT-FICTR
             INTO G_T_ITEM-BUCODE SEPARATED BY SPACE.
    ENDIF.

    G_T_ITEM-BTR006    = T_COLLECT-FKBTR_BL.

* To obtain positive number for display
    G_T_ITEM-BTR001 =  T_COLLECT-FKBTR_EX_1 * -1.
    G_T_ITEM-BTR009 =  T_COLLECT-FKBTR_EX_2 * -1.
* To obtain positive number for display
    G_T_ITEM-BTR002 =  T_COLLECT-FKBTR_UN_1 * -1.
    G_T_ITEM-BTR010 =  T_COLLECT-FKBTR_UN_2 * -1.
* To obtain total
    G_T_ITEM-FKBTR    =  G_T_ITEM-BTR001 + G_T_ITEM-BTR002
                       + G_T_ITEM-BTR009 + G_T_ITEM-BTR010.

    COLLECT G_T_ITEM.

  ENDLOOP.

  LOOP AT G_T_ITEM.
* To obtain Avalaible amount on Allotment
* DTAL16012003
    G_T_ITEM-BTR003  =   G_T_ITEM-BTR005 -
                           ( G_T_ITEM-BTR001 + G_T_ITEM-BTR002 ).
    G_T_ITEM-BTR011  =   G_T_ITEM-BTR008 -
                           ( G_T_ITEM-BTR009 + G_T_ITEM-BTR010 ).

* To obtain Avalaible amount on Allocation
*AHOUNOU  30/07/2004
    G_T_ITEM-BTR007   =  G_T_ITEM-WLJHK - G_T_ITEM-FKBTR .
*AHOUNOU  30/07/2004
* To obtain Percentage
* DTAL16012003
    IF G_T_ITEM-WLJHK NE 0.
*AHOUNOU  30/07/2004
      G_T_ITEM-BTR004   = ( G_T_ITEM-FKBTR / G_T_ITEM-WLJHK ) * 100.
*AHOUNOU  30/07/2004
    ELSE.
      G_T_ITEM-BTR004  = 0.
    ENDIF.

    MODIFY G_T_ITEM.

  ENDLOOP.

ENDFORM.                                          " 03_ASSOCIATE_EXPEN



***********************************************************************
*
*                  FORM 07_RESTRICT_HIERARCHY
*
***********************************************************************
*
* --> g_t_item
*
* <-- g_t_item2
*
***********************************************************************
*
*
*
*
*
***********************************************************************
*
FORM 07_RESTRICT_HIERARCHY.

  REFRESH T_N_FUNDCENTER.
  REFRESH T_PARENTS.
  CLEAR T_PARENTS.
* EMAR25062002 table temporaire pour lecture
* du budget de la ligne parent
* critères de tri :
* fond
* fund center
* budget (pour recherche du budget du parent)
  SORT G_T_ITEM BY FONDS
                   FICTR
                   WLJHK DESCENDING .
  REFRESH G_T_ITEM_TEMP.
  APPEND LINES OF G_T_ITEM TO G_T_ITEM_TEMP.

* Get all parents
  LOOP AT G_T_ITEM.

* Count number of fund center per fund
    AT NEW FICTR.
      T_N_FUNDCENTER-FONDS = G_T_ITEM-FONDS.
      T_N_FUNDCENTER-N = 1.
      COLLECT T_N_FUNDCENTER.
    ENDAT.
* Recherche du fund center parent
    SELECT SINGLE CTR_OBJNR FROM FMFCTR INTO T_PARENTS-CTR_OBJNR
      WHERE CTR_OBJNR = G_T_ITEM-CTR_OBJNR
            AND FICTR = G_T_ITEM-CTR_OBJNR.

* Aucun parent
    CHECK SY-SUBRC EQ 0.

* Check not t_parents-ctr_objnr is initial.
    IF T_PARENTS-CTR_OBJNR EQ SPACE.  " top of hierarchy
      T_PARENTS-CTR_OBJNR = G_T_ITEM-CTR_OBJNR.
    ENDIF.

* Recherche du parent si le parent a un budget nul
* ou si la ligne en cours a du budget
    READ TABLE G_T_ITEM_TEMP
      WITH KEY
        CTR_OBJNR = T_PARENTS-CTR_OBJNR
        FONDS     = G_T_ITEM-FONDS.

    IF G_T_ITEM_TEMP-WLJHK EQ 0
    OR G_T_ITEM-WLJHK NE 0.

      T_PARENTS-FONDS = G_T_ITEM-FONDS.
      T_PARENTS-N     = 1.
      COLLECT T_PARENTS.

*    APPEND t_parents.

    ENDIF.

  ENDLOOP.

* Table temporaire pour lecture du budget de la ligne parent
  REFRESH G_T_ITEM_TEMP.
  APPEND LINES OF G_T_ITEM TO G_T_ITEM_TEMP.

* Tri pour avoir les dépenses en 1er
  SORT G_T_ITEM_TEMP BY FONDS
                        FICTR
                        FKBTR DESCENDING .

  CLEAR G_T_ITEM.
  LOOP AT G_T_ITEM.

    READ TABLE T_N_FUNDCENTER
      WITH KEY FONDS = G_T_ITEM-FONDS.
* If Only one fund center then edit
    IF T_N_FUNDCENTER-N EQ 1.
      MOVE-CORRESPONDING G_T_ITEM TO G_T_ITEM2.
      APPEND G_T_ITEM2.
    ELSE.
* Si la ligne en cours est une ligne de dépense,pas de test d'existence
* de parent. Cas ligne en cours n'est pas une ligne de dépense :
      IF G_T_ITEM-FKBTR EQ 0.

* Recherche de dépenses
        CLEAR G_T_ITEM_TEMP.
        READ TABLE G_T_ITEM_TEMP
        WITH KEY CTR_OBJNR = G_T_ITEM-CTR_OBJNR
                 FONDS     = G_T_ITEM-FONDS.

* Si la ligne a des dépenses elle est à éditer
* Si la ligne n'a pas de dépense ==> check du parent
        IF G_T_ITEM_TEMP-FKBTR EQ 0.
* for this fund :
* if parents exists : do not edit
          READ TABLE T_PARENTS
          WITH KEY CTR_OBJNR = G_T_ITEM-CTR_OBJNR
                   FONDS     = G_T_ITEM-FONDS.
* Edit que si pas de parent
          CHECK SY-SUBRC NE 0.

        ENDIF.
      ENDIF.

      MOVE-CORRESPONDING G_T_ITEM TO G_T_ITEM2.
      APPEND G_T_ITEM2.

    ENDIF.
  ENDLOOP.

*****************************************************
  CLEAR G_T_ITEM3.
  REFRESH G_T_ITEM3.
  CLEAR WA_ITEM2.

  LOOP AT  G_T_ITEM2 INTO  WA_ITEM2.

    IF
    ( WA_ITEM2-WLJHK  EQ 0
       AND WA_ITEM2-BTR005 EQ 0
       AND WA_ITEM2-BTR001 EQ 0
       AND WA_ITEM2-BTR002 EQ 0
       AND WA_ITEM2-FKBTR  EQ 0
       AND WA_ITEM2-BTR003 EQ 0
       AND WA_ITEM2-BTR004 EQ 0
       AND WA_ITEM2-BTR006 EQ 0
       AND WA_ITEM2-BTR007 EQ 0
       AND WA_ITEM2-BTR008 EQ 0
       AND WA_ITEM2-BTR009 EQ 0
      AND WA_ITEM2-BTR010 EQ 0
       AND WA_ITEM2-BTR011 EQ 0 ).

    ELSE.

      READ TABLE G_T_ITEM3 WITH KEY FONDS = WA_ITEM2-FONDS
                                    FICTR = WA_ITEM2-FICTR
                     INTO WA_ITEM3.
      IF SY-SUBRC  = 0.

        WA_ITEM3-WLJHR  = WA_ITEM3-WLJHR  + WA_ITEM2-WLJHR.
        WA_ITEM3-WLJHK  = WA_ITEM3-WLJHK  + WA_ITEM2-WLJHK.
        WA_ITEM3-BTR005 = WA_ITEM3-BTR005 + WA_ITEM2-BTR005.
        WA_ITEM3-BTR001 = WA_ITEM3-BTR001 + WA_ITEM2-BTR001.
        WA_ITEM3-BTR002 = WA_ITEM3-BTR002 + WA_ITEM2-BTR002.
        WA_ITEM3-FKBTR  = WA_ITEM3-FKBTR  + WA_ITEM2-FKBTR.
        WA_ITEM3-BTR003 = WA_ITEM3-BTR003 + WA_ITEM2-BTR003.
        WA_ITEM3-BTR006 = WA_ITEM3-BTR006 + WA_ITEM2-BTR006.
        WA_ITEM3-BTR007 = WA_ITEM3-BTR007 + WA_ITEM2-BTR007.
        WA_ITEM3-BTR008 = WA_ITEM3-BTR008 + WA_ITEM2-BTR008.
        WA_ITEM3-BTR009 = WA_ITEM3-BTR009 + WA_ITEM2-BTR009.
        WA_ITEM3-BTR010 = WA_ITEM3-BTR010 + WA_ITEM2-BTR010.
        WA_ITEM3-BTR011 = WA_ITEM3-BTR011 + WA_ITEM2-BTR011.

        IF WA_ITEM3-WLJHK NE 0.
          WA_ITEM3-BTR004   = ( WA_ITEM3-FKBTR / WA_ITEM3-WLJHK ) * 100.

        ELSE.
          WA_ITEM3-BTR004  = 0.
        ENDIF.

        MODIFY TABLE G_T_ITEM3 FROM WA_ITEM3.
        CLEAR WA_ITEM3.
        CLEAR WA_ITEM2.

      ELSE.
        IF WA_ITEM3-WLJHK NE 0.
          WA_ITEM3-BTR004   = ( WA_ITEM3-FKBTR / WA_ITEM3-WLJHK ) * 100.

        ELSE.
          WA_ITEM3-BTR004  = 0.
        ENDIF.

        APPEND  WA_ITEM2 TO G_T_ITEM3.

        CLEAR WA_ITEM2.
      ENDIF.
    ENDIF.
  ENDLOOP.

*DTAL311006
* Max value for wa_belnr
*  wa_belnr = 9999999999.
  CLEAR  WA_ITEM3.
  LOOP AT G_T_ITEM3 INTO WA_ITEM3.

*    SELECT sgtext belnr FROM BPVJ INTO corresponding fields of WA_BPVJ
*      WHERE GEBER   = wa_item3-fonds .
*      if sy-subrc eq 0 and WA_BPVJ-belnr <= wa_belnr.
*        wa_belnr = WA_BPVJ-belnr.
*        wa_item3-sgtext = WA_BPVJ-sgtext.
*      endif.
*    ENDSELECT.
    SELECT SINGLE * FROM FMFINT
                  WHERE FINCODE = WA_ITEM3-FONDS
                    AND FIKRS   = WA_ITEM3-FIKRS.
*IKON090108 - start
*      if sy-subrc eq 0.
*         IF FMFINT-BESCHR <> ''.
*            wa_item3-sgtext = FMFINT-BESCHR.
*         else.
*            wa_item3-sgtext = FMFINT-BEZEICH.
*         endif.
*      endif.
            WA_ITEM3-SGTEXT = FMFINT-BESCHR.
            WA_ITEM3-BEZEICH = FMFINT-BEZEICH.
*IKON090108 - end

***IKON030609 - check for responsible person
    IF NOT ( FMFINT-BEZEICH IN S_RPERS ).
      CLEAR WA_ITEM3.
      CONTINUE.
    ENDIF.
***

*IKON220908 - start
    CONCATENATE WA_ITEM3-FIKRS WA_ITEM3-FONDS INTO W_ONAME.
    REFRESH T_TLINES.
    CALL FUNCTION 'READ_TEXT'
      EXPORTING
*       CLIENT                        = SY-MANDT
        ID                            = 'FD01'
        LANGUAGE                      = SY-LANGU
        NAME                          = W_ONAME
        OBJECT                        = 'FMMD'
*       ARCHIVE_HANDLE                = 0
*       LOCAL_CAT                     = ' '
*     IMPORTING
*       HEADER                        =
      TABLES
        LINES                         = T_TLINES
     EXCEPTIONS
       ID                            = 1
       LANGUAGE                      = 2
       NAME                          = 3
       NOT_FOUND                     = 4
       OBJECT                        = 5
       REFERENCE_CHECK               = 6
       WRONG_ACCESS_TO_ARCHIVE       = 7
       OTHERS                        = 8
              .
    IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    ENDIF.
    CLEAR W_STITLE.
    LOOP AT T_TLINES.
      W_SLEN = STRLEN( T_TLINES-TDLINE ).
      IF SY-TABIX = 1.
        W_STITLE = T_TLINES-TDLINE(W_SLEN).
        W_TLEN = W_SLEN.
       ELSEIF W_TLEN < 250.
         CONCATENATE W_STITLE T_TLINES-TDLINE(W_SLEN) INTO W_STITLE SEPARATED BY SPACE.
         W_TLEN = STRLEN( W_STITLE ).
      ENDIF.
    ENDLOOP. "t_tlines
    WA_ITEM3-STITLE = W_STITLE(250).
*IKON220908 - end
    APPEND WA_ITEM3 TO G_T_ITEM4.
    CLEAR WA_ITEM3.
*    wa_belnr = 9999999999.

  ENDLOOP.

ENDFORM.                                       " 07_RESTRICT_HIERARCHY

***********************************************************************
*
*                         FORM 09_EDITION
*
***********************************************************************
*
* --> g_i_tem
*
* <-- EDITION
*
***********************************************************************
***********************************************************************
*
FORM 09_EDITION.
* Provide Meta-Datas
  PERFORM 091_FILL_FIELDCAT CHANGING G_T_FIELDCAT.
  PERFORM 093_FILL_LAYOUT   CHANGING G_F_LAYOUT.
  PERFORM 095_FILL_SORT     CHANGING G_T_SORT.
  PERFORM 097_FILL_EVENTS   CHANGING G_T_EVENTS.

* Call of the presentation toolset
  CALL FUNCTION 'REUSE_ALV_LIST_DISPLAY'
    EXPORTING
      I_CALLBACK_PROGRAM      = 'YFM1_TITLE'
      I_CALLBACK_USER_COMMAND = 'USER_COMMAND'
      I_STRUCTURE_NAME        = 'G_T_ITEM4'
      IS_LAYOUT               = G_F_LAYOUT
      IT_FIELDCAT             = G_T_FIELDCAT
      IT_SORT                 = G_T_SORT
      I_DEFAULT               = 'X'
      I_SAVE                  = 'U'
      IT_EVENTS               = G_T_EVENTS
    TABLES
      T_OUTTAB                = G_T_ITEM4
    EXCEPTIONS
      PROGRAM_ERROR           = 1
      OTHERS                  = 2.

ENDFORM.                                                    "09_EDITION


***********************************************************************
*
*                      FORM 091_FILL_FIELDCAT
*
***********************************************************************
*
* --> input
*
* <-- g_t_fielcat
*
***********************************************************************
***********************************************************************
*
FORM 091_FILL_FIELDCAT
  CHANGING C_T_FIELDCAT TYPE SLIS_T_FIELDCAT_ALV.

  DATA: L_F_FIELDCAT LIKE LINE OF C_T_FIELDCAT.

* Budget Code
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BUCODE'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 1.
  L_F_FIELDCAT-KEY            = 'X'.
  L_F_FIELDCAT-NO_SUM         = 'X'.
  L_F_FIELDCAT-SELTEXT_L      = 'Budget Code'.
  L_F_FIELDCAT-SELTEXT_M      = 'Budget Code'.
  L_F_FIELDCAT-SELTEXT_S      = 'Budget Code'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Budget Code'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 15.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Title
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'SGTEXT'.
  L_F_FIELDCAT-REF_TABNAME    = 'BPBK'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 2.
  L_F_FIELDCAT-SELTEXT_L      = 'Title'.
  L_F_FIELDCAT-SELTEXT_M      = 'Title'.
  L_F_FIELDCAT-SELTEXT_S      = 'Title'.
  L_F_FIELDCAT-DDICTXT        = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 39.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

*IKON090108
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BEZEICH'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMFINT'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 2.
  L_F_FIELDCAT-SELTEXT_L      = 'Responsible person'.
  L_F_FIELDCAT-SELTEXT_M      = 'Responsible person'.
  L_F_FIELDCAT-SELTEXT_S      = 'Resp.person'.
  L_F_FIELDCAT-DDICTXT        = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 20.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Allocation
  CLEAR L_F_FIELDCAT.
*AHOUNOU  30/07/2004
  L_F_FIELDCAT-FIELDNAME      = 'WLJHK'.
*AHOUNOU  30/07/2004
  L_F_FIELDCAT-REF_TABNAME    = 'bpbyx'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 3.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_L      = 'Allocation'.
  L_F_FIELDCAT-SELTEXT_M      = 'Allocation'.
  L_F_FIELDCAT-SELTEXT_S      = 'Allocation'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Allocation'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Allotment year 1
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR005'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 4.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_M      = 'Allotment Y1'.
  L_F_FIELDCAT-SELTEXT_S      = 'Allotment Y1'.
  L_F_FIELDCAT-SELTEXT_L      = 'Allotment Year 1'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Allotment Year 1'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Allotment year 2
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR008'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 5.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_M      = 'Allotment Y2'.
  L_F_FIELDCAT-SELTEXT_S      = 'Allotment Y2'.
  L_F_FIELDCAT-SELTEXT_L      = 'Allotment Year 2'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Allotment Year 2'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.


* Undelivered orders year 1
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR002'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 6.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_M      = 'Und.OrdersY1'.
  L_F_FIELDCAT-SELTEXT_L      = 'Undelivered orders year 1'.
  L_F_FIELDCAT-SELTEXT_S      = 'Und.OrdersY1'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Und. orders 1'.
  L_F_FIELDCAT-DDICTXT        = 'M'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Undelivered orders year 2
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR010'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 7.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_S      = 'Und.OrdersY2'.
  L_F_FIELDCAT-SELTEXT_M      = 'Und.OrdersY2'.
  L_F_FIELDCAT-SELTEXT_L      = 'Undelivered orders year 2'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Und. orders 2'.
  L_F_FIELDCAT-DDICTXT        = 'M'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 17.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Expenditures year 1
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR001'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 8.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_S      = 'Expendit.Y1'.
  L_F_FIELDCAT-SELTEXT_M      = 'Expendit. Y1'.
  L_F_FIELDCAT-SELTEXT_L      = 'Expenditures year 1'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Expenditures year 1'.
  L_F_FIELDCAT-DDICTXT        = 'M'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Expenditures year 2
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR009'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 9.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_S      = 'Expendit.Y2'.
  L_F_FIELDCAT-SELTEXT_M      = 'Expendit. Y2'.
  L_F_FIELDCAT-SELTEXT_L      = 'Expenditures year 2'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Expenditures year 2'.
  L_F_FIELDCAT-DDICTXT        = 'M'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Total
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'FKBTR'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMFMIT2'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 10.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_L      = 'Total expenses'.
  L_F_FIELDCAT-SELTEXT_M      = 'Total expenses'.
  L_F_FIELDCAT-SELTEXT_S      = 'Total expenses'.
  L_F_FIELDCAT-REPTEXT_DDIC   = 'Total expenses'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.


* Available Funds on Allotment year 1
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME     = 'BTR003'.
  L_F_FIELDCAT-REF_TABNAME   = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS       = 1.
  L_F_FIELDCAT-COL_POS       = 11.
  L_F_FIELDCAT-DO_SUM        = 'X'.
  L_F_FIELDCAT-CFIELDNAME    = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_M     = 'Avail.Allot.y1'.
  L_F_FIELDCAT-SELTEXT_S     = 'Avail.Allot.y1'.
  L_F_FIELDCAT-SELTEXT_L     = 'Avail. Allot. y1'.
  L_F_FIELDCAT-JUST          = 'L' .
  L_F_FIELDCAT-OUTPUTLEN     = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Available Funds on Allotment year 2
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME     = 'BTR011'.
  L_F_FIELDCAT-REF_TABNAME   = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS       = 1.
  L_F_FIELDCAT-COL_POS       = 12.
  L_F_FIELDCAT-DO_SUM        = 'X'.
  L_F_FIELDCAT-CFIELDNAME    = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_M     = 'Avail.Allot.y2'.
  L_F_FIELDCAT-SELTEXT_S     = 'Avail.Allot.y2'.
  L_F_FIELDCAT-SELTEXT_L     = 'Avail. Allot. y2'.
  L_F_FIELDCAT-JUST          = 'L' .
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* DTAL16012003
* Available Funds on Allocation
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME     = 'BTR007'.
  L_F_FIELDCAT-REF_TABNAME   = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS       = 1.
  L_F_FIELDCAT-COL_POS       = 13.
  L_F_FIELDCAT-DO_SUM        = 'X'.
  L_F_FIELDCAT-CFIELDNAME    = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_L     = 'Avail Allocation'.
  L_F_FIELDCAT-SELTEXT_M     = 'Avail.Alloc'.
  L_F_FIELDCAT-SELTEXT_S     = 'Avail.Alloc'.
  L_F_FIELDCAT-JUST          = 'L' .
  L_F_FIELDCAT-OUTPUTLEN     = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Execution Rate
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME   = 'BTR004'.
  L_F_FIELDCAT-REF_TABNAME = 'FMSU1'.
  L_F_FIELDCAT-COL_POS     = 14.
  L_F_FIELDCAT-CFIELDNAME  = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_L   = 'Exec. Rate'.
  L_F_FIELDCAT-SELTEXT_M   = 'Exec. Rate'.
  L_F_FIELDCAT-SELTEXT_S   = 'Exec. Rate'.
  L_F_FIELDCAT-REPTEXT_DDIC = 'Exec. Rate'.
*  l_f_fieldcat-do_sum      = 'X'.
  L_F_FIELDCAT-JUST        = 'L' .
  L_F_FIELDCAT-OUTPUTLEN   = 10.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

* Funds Blocked
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'BTR006'.
*  l_f_fieldcat-ref_tabname    = 'FMSU1'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 15.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'FWAER'.
  L_F_FIELDCAT-SELTEXT_L      = 'Blocked amount'.
  L_F_FIELDCAT-SELTEXT_M      = 'Blocked amount'.
  L_F_FIELDCAT-SELTEXT_S      = 'Blocked amnt'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 16.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.


* Fund type
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'TYPE'.
  L_F_FIELDCAT-REF_TABNAME    = 'fmfincode'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 16.
  L_F_FIELDCAT-DO_SUM         = 'X'.
  L_F_FIELDCAT-CFIELDNAME     = 'TYPE'.
  L_F_FIELDCAT-SELTEXT_L      = 'TYPE'.
  L_F_FIELDCAT-JUST           = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 8.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.



* Creation date
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'ERFDAT'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMFINCODE'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 17.
  L_F_FIELDCAT-SELTEXT_L      = 'Cr. date'.
  L_F_FIELDCAT-SELTEXT_M      = 'Cr. date'.
  L_F_FIELDCAT-SELTEXT_S      = 'Cr. date'.
  L_F_FIELDCAT-DDICTXT        = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 15.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

*IKON220908 - Fund title
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'STITLE'.
  L_F_FIELDCAT-ROW_POS        = 2.
  L_F_FIELDCAT-COL_POS        = 1.
  L_F_FIELDCAT-SELTEXT_L      = 'Fund title'.
  L_F_FIELDCAT-SELTEXT_M      = 'Fund title'.
  L_F_FIELDCAT-SELTEXT_S      = 'Fund title'.
  L_F_FIELDCAT-DDICTXT        = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 250.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.

*IKON020609 - Fund centre
  CLEAR L_F_FIELDCAT.
  L_F_FIELDCAT-FIELDNAME      = 'FICTR'.
  L_F_FIELDCAT-REF_TABNAME    = 'FMFCTR'.
  L_F_FIELDCAT-ROW_POS        = 1.
  L_F_FIELDCAT-COL_POS        = 18.
  L_F_FIELDCAT-SELTEXT_L      = 'Fund Centre'.
  L_F_FIELDCAT-SELTEXT_M      = 'FundCentre'.
  L_F_FIELDCAT-SELTEXT_S      = 'FCentre'.
  L_F_FIELDCAT-DDICTXT        = 'L'.
  L_F_FIELDCAT-OUTPUTLEN      = 17.
  APPEND L_F_FIELDCAT TO C_T_FIELDCAT.


ENDFORM.                                             "091_FILL_FIELDCAT


***********************************************************************
*
*                      Form  093_FILL_LAYOUT
*
***********************************************************************
*
* --> input
*
* <-- g_t_sort
*
***********************************************************************

FORM 093_FILL_LAYOUT
CHANGING C_F_LAYOUT TYPE SLIS_LAYOUT_ALV.

  CALL FUNCTION 'FM_ALV_LAYOUT'
    CHANGING
      C_F_LAYOUT = C_F_LAYOUT.

  C_F_LAYOUT-NO_TOTALLINE      = ' '.
* To maintain options chose in fieldcat
  C_F_LAYOUT-COLWIDTH_OPTIMIZE = ' '.
  C_F_LAYOUT-NO_MIN_LINESIZE = ' '.
*  c_f_layout-min_linesize      = '255'.
*  c_f_layout-max_linesize      = '255'.


ENDFORM.                                               "093_FILL_LAYOUT


***********************************************************************
*
*                      FORM 095_FILL_SORT
*
***********************************************************************
*
* --> input
*
* <-- g_t_sort
*
***********************************************************************

FORM 095_FILL_SORT
CHANGING C_T_SORT TYPE SLIS_T_SORTINFO_ALV.

*  "/ Workarea
  DATA: L_F_SORT LIKE LINE OF C_T_SORT.

  CLEAR L_F_SORT.
  L_F_SORT-SPOS = 1.
  L_F_SORT-FIELDNAME = 'BUCODE'.
  L_F_SORT-UP = 'X'.
  L_F_SORT-SUBTOT = ' '.
  APPEND L_F_SORT TO C_T_SORT.

ENDFORM.                                                 "095_FILL_SORT


***********************************************************************
*
*                      FORM 097_FILL_EVENT
*
***********************************************************************
*
* --> input
*
* <-- g_t_event
*
***********************************************************************

FORM 097_FILL_EVENTS CHANGING C_T_EVENTS TYPE SLIS_T_EVENT.

  DATA: L_F_EVENTS LIKE LINE OF C_T_EVENTS.

  L_F_EVENTS-NAME = 'TOP_OF_PAGE'.
  L_F_EVENTS-FORM = 'TOP_OF_PAGE'.
  APPEND L_F_EVENTS TO C_T_EVENTS.

ENDFORM.                                               "097_FILL_EVENTS

***********************************************************************
*
*                      FORM TOP-OF-PAGE
*
***********************************************************************
*
* --> input
*
* <-- output
*
***********************************************************************

FORM TOP_OF_PAGE.

*jb.fv 26/11/2001
  CLEAR: W_SUM_EXP.              " Sum Total Expenses
  CLEAR: W_SUM_ALL.              " Sum Total Alloc.
  CLEAR: W_PCT_EX_RATE.          " % Execution Rate

  LOOP AT G_T_ITEM4.
    W_SUM_EXP = W_SUM_EXP + G_T_ITEM4-FKBTR.
*AHOUNOU  30/07/2004
    W_SUM_ALL = W_SUM_ALL + G_T_ITEM4-WLJHK.
*AHOUNOU  30/07/2004
  ENDLOOP.

  IF W_SUM_ALL NE 0.
    W_PCT_EX_RATE = ( W_SUM_EXP / W_SUM_ALL ) * 100.
  ENDIF.

*jb.fv 26/11/2001

  WRITE: /01  SY-REPID,
          110 SY-TITLE.
* EMAR25062002 : affichage date et user sur 2 lignes
* Date :
  WRITE : /01
  TEXT-002,
    SY-DATUM.

*          231 text-002,
*          237 sy-datum.
  WRITE: /01  SY-UNAME,
* Page :
          231 TEXT-003,
          237 SY-PAGNO.

  SKIP 1.

*jb.fv 26/11/2001
  WRITE: 01  'Total Execution Rate %'.
  WRITE: 26  W_PCT_EX_RATE LEFT-JUSTIFIED.
*jb.fv 26/11/2001

ENDFORM.                                                  " TOP-OF-PAGE


***********************************************************************
*
*                      FORM USER_COMMAND
*
***********************************************************************
*
* --> input
*
* <-- g_t_event
*
***********************************************************************

FORM USER_COMMAND USING U_UCOMM  LIKE SY-UCOMM
                      SELFIELD TYPE SLIS_SELFIELD.
  CASE U_UCOMM.
    WHEN 'PIC1'.
      READ TABLE G_T_ITEM4 INDEX SELFIELD-TABINDEX.
      CHECK SY-SUBRC = 0.

      DATA TEXPR TYPE RSDS_TEXPR.
      DATA: FIELDS     TYPE TABLE OF RSDSFIELDS WITH HEADER LINE,
            TABLES     LIKE  RSDSTABS OCCURS 0  WITH HEADER LINE.
      DATA: SELID   LIKE RSDYNSEL-SELID.
      DATA WA_YEAR LIKE BPEJ-GJAHR.

      WA_YEAR = SY-DATUM+0(4).


      SUBMIT RFFMEPGAX WITH S_FIKRS EQ G_T_ITEM4-FIKRS   SIGN 'I'
                      WITH S_FONDS EQ G_T_ITEM4-FONDS SIGN 'I'
                      WITH S_FICTR  EQ G_T_ITEM4-FICTR   SIGN 'I'
                      WITH P_FYR_FR EQ '2001' SIGN 'I'
                      WITH P_FYR_TO EQ WA_YEAR SIGN 'I'
                      WITH P_PER_FR EQ '1' SIGN 'I'
                      WITH P_PER_TO EQ '16' SIGN 'I'
                      WITH P_MAXSEL EQ '999999999' SIGN 'I'
                          AND RETURN.


  ENDCASE.
ENDFORM.                                              " USER_COMMAND