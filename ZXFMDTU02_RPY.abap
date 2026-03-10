*&---------------------------------------------------------------------*
*&  Include           ZXFMDTU02                                        *
*&---------------------------------------------------------------------*
*& SROCHA26072010 Commented out code to replace with derivation rules
*&**********************************************************************

TABLES: BPGE,
        BPJA,
        EKKO,
        FMFCTR,
        FMFINCODE,
        FMCI, FMHISV, "fmfpo, fmhictr - tables changed from FM to PSM
        FMFUNDTYPE,
        FMBDT,
        PRPS, TBP1C, TJ01, USR05, YFMXCHK, YFMXCHKP, "yglchk,
        YXUSER, YXTCODE.

DATA: W_HLEVEL LIKE FMHICTR-HILEVEL,
      W_OBJNR LIKE BPJA-OBJNR,
      W_LEVCNT TYPE I,
      W_FISTL LIKE FMFCTR-FICTR,
      W_FLAG,
      W_FLAG2, "for 6045011 and 7045011
      W_FCTR(100),
      W_DATE TYPE D,
      W_PROFIL LIKE TBP1C-PROFIL,
      W_KBLNR LIKE COBL-KBLNR,
      W_EBELN LIKE COBL-EBELN,
      W_MSGTXT(25).


DATA: BEGIN OF T_LEVCNT OCCURS 0,
        HILEVEL(4),
        OBJNR LIKE BPJA-OBJNR,
        CNTR TYPE I,
      END OF T_LEVCNT.

DATA: R_SKIPDOC LIKE RANGE OF I_COBL-BLART.
DATA: BEGIN OF W_SKIPDOC,
        SIGN(1),
        OPTION(2),
        LOW LIKE I_COBL-BLART,
        HIGH LIKE I_COBL-BLART,
      END OF W_SKIPDOC.

*table to calculate budget distribution by Fund Centers
DATA: BEGIN OF T_BDGDSTR OCCURS 0,
        OBJNR LIKE BPJA-OBJNR, "fund center
        HILEV(4),              "hierarchy level
        RDSUM LIKE BPJA-WTJHR, "distributable amount
      END OF T_BDGDSTR.

DATA: BEGIN OF T_FCBUDGET OCCURS 0,
        RFIKRS    LIKE FMBDT-RFIKRS,
        RFUND     LIKE FMBDT-RFUND,
        RFUNDSCTR LIKE FMBDT-RFUNDSCTR,
      END OF T_FCBUDGET.


*test branch
DATA: W_TSTUNAME(12) VALUE 'I_KONAKOV'.
IF SY-UNAME = W_TSTUNAME.
*  break-point.
ENDIF.

CLEAR: W_FLAG, W_FLAG2.

***derivation for specific GL in UNES
*SROCHA26072010
*Replaced by Derivation Rule: "Derive Fund when fund empty for
*GL Accounts: 7042011 & 7045011
*SROCHA16112010
IF I_COBL-HKONT = '0007042011' AND I_COBL-FIKRS = 'UNES' AND
   I_COBL-GEBER = SPACE.
  C_FMDERIVE-FUND = '630PLF9000'.
  W_FLAG2 = 1.
ENDIF. "i_cobl-hkont

*SROCHA26072010
*Replaced by Derivation Rule: Derive Fund Center when fund Center
*empty for GL codes: 7042011 & 7045011
*SROCHA16112010
IF I_COBL-HKONT = '0007042011' AND I_COBL-FIKRS = 'UNES' AND
   I_COBL-FISTL = SPACE.
  C_FMDERIVE-FUND_CENTER = 'BOC'.
  W_FLAG2 = 1.
ENDIF. "i_cobl-hkont

*SROCHA26072010
*Replaced by Derivation Rule: Fund Center when FC empty for
*Specific GL Codes
*derivation for GL accts 6045011&7045011
*SROCHA16112010
IF ( I_COBL-HKONT = '0006045011' OR
     I_COBL-HKONT = '0007045011' OR
*     i_cobl-hkont = '0006044011' or "removed on 18/02/2021 on request from M.Spronk
     I_COBL-HKONT = '0006045014' )
    AND I_COBL-FISTL = SPACE AND I_COBL-FIKRS = 'UNES'.
  C_FMDERIVE-FUND_CENTER = 'UNESCO'.
  W_FLAG2 = 1.
ENDIF. "i_cobl-hkont

*SROCHA26072010
*Replace by Derivation Rule: Derive Fund when Fund empty
*for specific GL Accounts.
*SROCHA16112010

IF ( I_COBL-HKONT = '0006045011' OR
     I_COBL-HKONT = '0007045011' OR
*     i_cobl-hkont = '0006044011' or "removed on 18/02/2021 on request from M.Spronk
     I_COBL-HKONT = '0006045014' )
    AND I_COBL-GEBER = SPACE AND I_COBL-FIKRS = 'UNES'.
  C_FMDERIVE-FUND = 'GEF'.
  W_FLAG2 = 1.
ENDIF. "i_cobl-hkont


***I_KONAKOV 01/10/2025 - add derivation on request from B.Gazi
IF I_COBL-HKONT = '0007043011' OR
   I_COBL-HKONT = '0007043012' OR
   I_COBL-HKONT = '0007043013' OR
   I_COBL-HKONT = '0007043014'.
  CASE I_COBL-FIKRS.
    WHEN 'UNES'.
      C_FMDERIVE-FUND_CENTER = 'BFM'.
      C_FMDERIVE-FUND = '645ASH9000'.
      C_FMDERIVE-BUS_AREA = 'OPF'.
      W_FLAG2 = 1.

    WHEN OTHERS.
  ENDCASE. "i_cobl-fikrs
ENDIF. "i_cobl-hkont

IF I_COBL-HKONT = '0007043021'.
  CASE I_COBL-FIKRS.
    WHEN 'UNES'.
      C_FMDERIVE-FUND_CENTER = 'HED'.
      C_FMDERIVE-FUND = '401NHF1091'.
      C_FMDERIVE-WBS_ELEMENT = '401NHF1091'.
      C_FMDERIVE-BUS_AREA = 'PFF'.
      W_FLAG2 = 1.

    WHEN OTHERS.
  ENDCASE. "i_cobl-fikrs
ENDIF. "i_cobl-hkont
***


***I_KONAKOV 23/01/2015 - add derivation on request from M.Spronk
***Changed 11/02/2015 on request from M.Spronk
****6044011 removed on 18/02/2021 on request from M.Spronk
IF "( i_cobl-hkont = '0006044011' or
     I_COBL-HKONT = '0007044011' OR I_COBL-HKONT = '0007044014'. " ).
  CASE I_COBL-FIKRS.
    WHEN 'UNES'.
      CASE I_COBL-GSBER.
        WHEN 'GEF'.
          C_FMDERIVE-FUND_CENTER = 'UNESCO'.
          C_FMDERIVE-FUND = 'GEF'.
          W_FLAG2 = 1.
        WHEN 'MBF'.
          C_FMDERIVE-FUND_CENTER = 'UNESCO'.
          C_FMDERIVE-FUND = 'MBF'.
          W_FLAG2 = 1.
        WHEN OTHERS.
      ENDCASE. "i_cobl-gsber

    WHEN OTHERS.
  ENDCASE. "i_cobl-fikrs
ENDIF. "i_cobl-hkont
***

***I_KONAKOV 11/02/2015 - derivation on request from M.Spronk.
IF I_COBL-HKONT = '0007044012'.
  CASE I_COBL-FIKRS.
    WHEN 'UNES'.
      CASE I_COBL-GSBER.
        WHEN 'OPF'.
          C_FMDERIVE-FUND_CENTER = 'UNESCO'.
          C_FMDERIVE-FUND = 'OPF'.
          W_FLAG2 = 1.
        WHEN 'PFF'.
          C_FMDERIVE-FUND_CENTER = 'UNESCO'.
          C_FMDERIVE-FUND = 'PFF'.
          W_FLAG2 = 1.
        WHEN OTHERS.
      ENDCASE. "i_cobl-gsber

    WHEN OTHERS.
  ENDCASE. "i_cobl-fikrs
ENDIF. "i_cobl-hkont
***


***derivation for Fixed Assets balances transfer
IF SY-TCODE = 'OASV'.
  IF I_COBL-GEBER = SPACE.
    C_FMDERIVE-FUND = I_COBL-GSBER.
    W_FLAG2 = 1.
  ENDIF.
  IF I_COBL-FISTL = SPACE.
    CASE I_COBL-FIKRS.
      WHEN 'UNES'.
        C_FMDERIVE-FUND_CENTER = 'UNESCO'.
      WHEN 'UBO'.
        C_FMDERIVE-FUND_CENTER = 'BRZ'.
      WHEN 'IIEP'.
        C_FMDERIVE-FUND_CENTER = 'IEP'.
      WHEN 'IBE'.
        C_FMDERIVE-FUND_CENTER = 'IBE'.
      WHEN 'UIS'.
        C_FMDERIVE-FUND_CENTER = 'UIS'.
      WHEN 'UIL'.
        C_FMDERIVE-FUND_CENTER = 'UIL'.
      WHEN 'MGIE'.
        C_FMDERIVE-FUND_CENTER = 'MGI'.
      WHEN OTHERS.
    ENDCASE.
    W_FLAG2 = 1.
  ENDIF.
ENDIF.
***


***derive B/Area PFF for Fund Types 114 & 115 - request from S.Rocha 01/2022
IF I_COBL-FIKRS = 'UNES'.
  CLEAR FMFINCODE.
  SELECT SINGLE *
        FROM FMFINCODE
        WHERE FIKRS = I_COBL-FIKRS
          AND FINCODE = I_COBL-GEBER.
  IF ( FMFINCODE-TYPE = '114' ) OR ( FMFINCODE-TYPE = '115' ).
    C_FMDERIVE-BUS_AREA = 'PFF'.
  ENDIF. "fmfincode-type
ENDIF. "fikrs
***

****I_KONAKOV 03/2025 - substitute Commt Item for doc. types P1 & P2
*if i_cobl-blart = 'P2'.
*  select single * from yxuser
*                  where xtype = 'P2'
*                    and uname = sy-uname.
*  if sy-subrc <> 0.
*    c_fmderive-commit_item = 'CDSP'.
*  endif.
*endif. "i_cobl-blart
****


***To allow some users avoid the checks below
*clear yfmxchk.
*select single *
*      from yfmxchk
*      where fikrs = 'USER'
*        and geber = sy-uname
*        and xcheck = 'U'.
SELECT SINGLE * FROM YXUSER
                WHERE XTYPE = 'FM'
                  AND UNAME = SY-UNAME.
CHECK SY-SUBRC <> 0.
***

CHECK I_COBL-VORGN <> 'TRVL'.

***General checks

***08.10.2010 - block new postings on 149* funds - request from L.Chabeau
IF I_COBL-GEBER(3) = '149' AND
   ( SY-TCODE = 'ME21' OR
     SY-TCODE = 'ME51' OR
     SY-TCODE = 'ME21N' OR
     SY-TCODE = 'ME51N' OR
     SY-TCODE = 'FMX1' ).

  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'Impossible to use fund ' I_COBL-GEBER.
ENDIF. "i_cobl-geber(3)
***

***05.12.2011 - block new postings on specific fund types - request from L.Chabeau
*if ( ( sy-tcode(4) = 'ME21' or sy-tcode(4) = 'ME22' or sy-tcode(4) = 'ME23' ) and
*       i_cobl-awtyp = 'PORD' and i_cobl-awkey = space )
*    or
*   ( ( sy-tcode(4) = 'ME51' or sy-tcode(4) = 'ME52' or sy-tcode(4) = 'ME53' ) and
*       i_cobl-awtyp = 'PREQ' and i_cobl-awkey(1) = '#' )
*    or
*   ( sy-tcode = 'FMX1' ).
*
*  clear fmfincode.
*  select single * from fmfincode
*                  where fikrs = i_cobl-fikrs
*                    and fincode = i_cobl-geber.
*
*  if fmfincode-type <> '003' and
*     fmfincode-type between '001' and '009'.
*       message id 'ZFI' type 'E' number '009'
*              with 'Impossible to use specified fund in transaction '
*                   sy-tcode
*                   '. Please contact BFM'.
*  endif. "fmfincode-type
*endif. "sy-tcode
***


***specific tech fund block - call from BFM (Lionel&Yimiao) on 01/03/2024
CLEAR YFMXCHK.
SELECT SINGLE *
      FROM YFMXCHK
      WHERE FIKRS = I_COBL-FIKRS
        AND GEBER = I_COBL-GEBER
        AND XCHECK = 'Z'.
IF SY-SUBRC IS INITIAL.
  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'Impossible to use fund ' I_COBL-GEBER.
ENDIF.
***


***11/2025 - block next years postings for certain funds (DBM request related to CF simulation in Prod)
CLEAR YFMXCHK.
IF I_COBL-GJAHR > SY-DATUM(4).
  SELECT SINGLE * FROM YFMXCHK
        WHERE FIKRS = I_COBL-FIKRS
          AND GEBER = I_COBL-GEBER
          AND XCHECK = 'Y'.

  IF SY-SUBRC IS INITIAL.
    MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
           WITH 'Impossible to use fund ' I_COBL-GEBER ' in the year ' I_COBL-GJAHR.
  ENDIF.
ENDIF. "i_cobl-gjahr
***


***Posting period blockage
CLEAR YFMXCHKP.
SELECT SINGLE * FROM YFMXCHKP WHERE BUKRS = I_COBL-BUKRS AND CHTYP = 'FY' AND ACTIV = 'X'.
IF SY-SUBRC IS INITIAL.
  IF I_COBL-GJAHR = YFMXCHKP-GJAHR AND I_COBL-BUDAT+4(2) <= YFMXCHKP-MONAT.
CALL FUNCTION 'AUTHORITY_CHECK'
  EXPORTING
*   USER                      = SY-UNAME
    OBJECT                    = 'Y_FMUECLO'
    FIELD1                    = 'YFLAG'
 EXCEPTIONS
   USER_DONT_EXIST           = 1
   USER_IS_AUTHORIZED        = 2
   USER_NOT_AUTHORIZED       = 3
   USER_IS_LOCKED            = 4
   OTHERS                    = 5.
IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.

    IF SY-SUBRC <> 2.
      CLEAR W_MSGTXT.
      CONCATENATE I_COBL-GJAHR ', period ' I_COBL-BUDAT+4(2) INTO W_MSGTXT SEPARATED BY SPACE.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed in the Fiscal Year '
                  W_MSGTXT.
    ENDIF. "sy-subrc authority check
**
  ENDIF. "i_cobl-gjahr
ENDIF. "sy-subrc yfmxchkp
***!!!


***Check for BB
IF  I_COBL-FIKRS = 'UNES'.
CLEAR YFMXCHKP.
SELECT SINGLE * FROM YFMXCHKP WHERE BUKRS = I_COBL-BUKRS AND CHTYP = 'BB' AND ACTIV = 'X'.
IF SY-SUBRC IS INITIAL.
CALL FUNCTION 'AUTHORITY_CHECK'
  EXPORTING
*   USER                      = SY-UNAME
    OBJECT                    = 'Y_FMUECLO'
    FIELD1                    = 'YFLAG'
 EXCEPTIONS
   USER_DONT_EXIST           = 1
   USER_IS_AUTHORIZED        = 2
   USER_NOT_AUTHORIZED       = 3
   USER_IS_LOCKED            = 4
   OTHERS                    = 5.
IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.

    IF SY-SUBRC <> 2.
  IF I_COBL-BLDAT(4) = YFMXCHKP-GJAHR AND I_COBL-BLDAT+4(2) <= YFMXCHKP-MONAT.
*           and
*           ( sy-tcode = 'ME21' or
*             sy-tcode = 'ME21N' or
*             sy-tcode = 'ME23N' or
*             sy-tcode = 'ME29N' or
*             sy-tcode = 'ME51N' or
*             sy-tcode = 'ME52N' or
*             sy-tcode = 'FMX1' or
*             sy-tcode = 'FMX2' or
*             sy-tcode = 'FB01' or
*             sy-tcode = 'FB50' or
*             sy-tcode = 'FB60' or
*             sy-tcode = 'MIRO' or
*             sy-tcode = 'MIGO' or
*             sy-tcode = 'MIGO_GR' or
*             sy-tcode = 'Y_MIGO' or
*             sy-tcode = 'ML85' or
*             sy-tcode = 'ML81N' )
*           .
      CLEAR YXTCODE.
      SELECT SINGLE * FROM YXTCODE
                      WHERE XTYPE = 'FM'
                        AND TCODE = SY-TCODE.
      IF SY-SUBRC = 0.
        CLEAR W_MSGTXT.
        CONCATENATE I_COBL-BLDAT(4) ', period ' I_COBL-BLDAT+4(2) INTO W_MSGTXT SEPARATED BY SPACE.
        MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
               WITH 'Postings are not allowed in the Fiscal Year '
                    W_MSGTXT.
      ENDIF. "sy-subrc tcode
  ENDIF. "i_cobl-bldat
***check for FR/PO number from previous year
       CLEAR: YFMXCHK, W_KBLNR, W_EBELN.
       IF I_COBL-KBLNR <> SPACE.
         SELECT * FROM YFMXCHK
                WHERE FIKRS = 'FR'
                  AND XCHECK = 'D'.
           IF YFMXCHK-GEBER(3) = I_COBL-KBLNR(3).
             W_KBLNR = YFMXCHK-GEBER.
           ENDIF.
         ENDSELECT.
         IF I_COBL-KBLNR <= W_KBLNR.
           CLEAR W_MSGTXT.
           W_MSGTXT = I_COBL-KBLNR.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed for FR '
                  W_MSGTXT
                  ' (past year commitment)'.
         ENDIF.
       ENDIF. "i_cobl-kblnr
       IF I_COBL-EBELN <> SPACE.
       SELECT SINGLE GEBER FROM YFMXCHK INTO W_EBELN
              WHERE FIKRS = 'PO'
                AND XCHECK = 'D'.
         IF I_COBL-EBELN <= W_EBELN.
           CLEAR W_MSGTXT.
           W_MSGTXT = I_COBL-EBELN.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed for PO '
                  W_MSGTXT
                  ' (past year commitment)'.
         ENDIF.
       ENDIF. "i_cobl-ebeln
    ENDIF. "sy-subrc authority check
ENDIF. "sy-subrc yfmxchkp
ENDIF. "i_cobl-fikrs
***end of check for BB



***check for RP biennium post (added 01/2014)
CLEAR YFMXCHKP.
SELECT SINGLE * FROM YFMXCHKP WHERE BUKRS = I_COBL-BUKRS AND CHTYP = 'BE' AND ACTIV = 'X'.
IF SY-SUBRC IS INITIAL.
  CLEAR FMFINCODE.
  SELECT SINGLE *
        FROM FMFINCODE
        WHERE FIKRS = I_COBL-FIKRS
          AND FINCODE = I_COBL-GEBER.
  IF FMFINCODE-TYPE BETWEEN '001' AND '098'.
    IF ( I_COBL-GJAHR = '2023' AND I_COBL-GEBER(1) = '3' ) OR
       ( I_COBL-GJAHR = '2024' AND I_COBL-GEBER(1) = '2' ).
      CALL FUNCTION 'AUTHORITY_CHECK'
  EXPORTING
*   USER                      = SY-UNAME
    OBJECT                    = 'Y_FMUECLO'
    FIELD1                    = 'YFLAG'
 EXCEPTIONS
   USER_DONT_EXIST           = 1
   USER_IS_AUTHORIZED        = 2
   USER_NOT_AUTHORIZED       = 3
   USER_IS_LOCKED            = 4
   OTHERS                    = 5.
     IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
     ENDIF.

    IF SY-SUBRC <> 2.
      CLEAR W_MSGTXT.
      CONCATENATE I_COBL-GJAHR 'for fund' I_COBL-GEBER INTO W_MSGTXT SEPARATED BY SPACE.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed in the Fiscal Year '
                  W_MSGTXT.
    ENDIF. "sy-subrc authority check
**
    ENDIF. "i_cobl-gjahr and i_cobl-geber
  ENDIF. "fmfincode-type
ENDIF. "sy-subrc yfmxchkp
***



**check for Asset Management
CHECK ( I_COBL-BLART <> 'AA' ) AND ( I_COBL-BLART <> 'AF' ).
CHECK I_COBL-KOART <> 'A'.
CHECK I_COBL-HKONT <> '0004060000'.
**end of AM check

***02/02/2010 - special funds exclusion - request from D.Tal
CLEAR YFMXCHK.
SELECT SINGLE *
      FROM YFMXCHK
      WHERE FIKRS = I_COBL-FIKRS
        AND GEBER = I_COBL-GEBER
        AND XCHECK = 'F'.
CHECK SY-SUBRC <> 0.
***

**check for batch transations of 'WF-BATCH' user
CHECK SY-TCODE <> 'FMW1'.
CHECK SY-TCODE <> 'FMW2'.
CHECK SY-TCODE <> 'FMW3'.
**

***exclusion the pools - request from H.Assefa 15.02.06
*again include in checks - request from L.Chabeau 09.10.09
*check i_cobl-geber <> '149GEF0000'
*  and i_cobl-geber <> '150GEF0000'
*  and i_cobl-geber <> '633UDO9000'
*  and i_cobl-geber <> 'ICBPYUDO'
*  and i_cobl-geber <> 'IESPYUDO'
*  and i_cobl-geber <> 'ITEPYUDO'.
***


****derivation BArea PFF for some G/Ls (request from B.Grujic - 04/05/07)
*if i_cobl-hkont = '0005098011' or
*   i_cobl-hkont = '0005098012' or
*   i_cobl-hkont = '0005098013'.
*  c_fmderive-bus_area = 'PFF'.
*endif. "i_cobl-hkont

***I_KONAKOV 13/07/2016 - temp. switch off checks for HR operations
CHECK I_COBL-VORGN(2) <> 'HR'.
***

***I_KONAKOV 10/03/2017 - switch off for PBC log
CHECK SY-TCODE <> 'S_EH5_01000035'.
CHECK SY-TCODE <> 'HRFPM_START_AWB'.
CHECK SY-TCODE <> 'HRPBC_LOG'.
CHECK SY-CPROG <> 'RHRFPM_APPL_LOG_DISPLAY'.
***

CASE I_COBL-FIKRS.

  WHEN 'UNES'.

***check for Commitment Item in PO <> space - added 25/04/2024
*    if i_cobl-fipos is initial and i_cobl-vorgn = 'RMBE' and i_cobl-ekopi = 'X'.
*      concatenate 'Commitment Item is empty for position ' i_cobl-awpos into w_msgtxt.
*      message id 'ZFI' type 'E' number '009'
*              with w_msgtxt.
*    endif.
***

**get position attributes
CLEAR FMCI.
SELECT SINGLE *
      FROM FMCI
      WHERE FIKRS = I_COBL-FIKRS
        AND FIPEX = I_COBL-FIPOS.
**


   CLEAR W_FLAG.
   CHECK FMCI-FIVOR = '30' OR SY-SUBRC <> 0.
   IF SY-SUBRC <> 0 AND
      ( I_COBL-VORGN = 'RMWE' OR
        I_COBL-VORGN = 'TRVL' OR
        I_COBL-VORGN = 'HRBV' ) AND
      I_COBL-SCOPE = 'OC'.
     W_FLAG = 1.
   ENDIF. "sy-subrc
   IF I_COBL-VORGN = 'RMWE' AND I_COBL-SCOPE IS INITIAL.
     EXIT.
   ENDIF. "i_cobl-vorgn

***check for PFF fund - request from Y.Kassim of 04.11.2010
  IF I_COBL-GEBER = 'PFF'.
    IF I_COBL-PS_PSP_PNR <> SPACE.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'WBS-element is not allowed for this fund!'.
    ENDIF.
    IF I_COBL-KOSTL = SPACE.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'Please specify Cost Center!'.
    ENDIF.
  ENDIF.
***

***I_KONAKOV 03/2025 - remove FCtr check so standard AVC control will work instead
****additional check for budget hierarchy
*   clear fmfincode.
*   select single *
*         from fmfincode
*         where fikrs = i_cobl-fikrs
*           and fincode = i_cobl-geber.
*  if ( fmfincode-type = '001' ) or
*     ( fmfincode-type = '002' ) or
*     ( fmfincode-type between '004' and '008' ) or
*     ( fmfincode-type between '101' and '115' ) or
***added 25.08.2004 by request from S.Shekhar
*     ( fmfincode-type = '003' )
***added in 03/2018 on request from L.Chabeau
*      or
*     ( fmfincode-type between '301' and '398' ).
*
*   clear yfmxchk.
*   select single *
*         from yfmxchk
*         where fikrs = i_cobl-fikrs
*           and geber = i_cobl-geber
*           and xcheck = 'H'.
*   if sy-subrc <> 0 and w_flag2 is initial.
*
**   clear: tbp1c, w_objnr, w_hlevel.
**   refresh: t_levcnt, t_bdgdstr.
**   select single *
**         from tbp1c
**         where profil = fmfincode-profil "w_profil
**           and applik = 'M'
**           and wrttp  = '43'.
**
**  if tbp1c-bpja = 'X'.
**   clear bpja.
**   select *
**         from bpja
**         where wrttp = 43
**           and gjahr = i_cobl-gjahr
**           and geber = i_cobl-geber.
**     w_fistl = bpja-objnr+6(16).
**     clear fmhisv.
**     select single *
**           from fmhisv
**           where fikrs = i_cobl-fikrs
**             and hivarnt = '0000'
**             and fistl = w_fistl. "i_cobl-fistl.
**     clear t_levcnt.
**     t_levcnt-hilevel = fmhisv-hilevel.
**     t_levcnt-objnr = bpja-objnr.
**     t_levcnt-cntr = 1.
**     collect t_levcnt.
**     clear t_bdgdstr.
**     t_bdgdstr-objnr = bpja-objnr.
**     t_bdgdstr-hilev = fmhisv-hilevel.
**     t_bdgdstr-rdsum = bpja-wljhr - bpja-wljhv.
**     collect t_bdgdstr.
**     if fmhisv-hilevel > w_hlevel.
**       w_hlevel = fmhisv-hilevel.
**       w_objnr = bpja-objnr.
**     endif. "fmhictr-hilevel
**   endselect. "bpja
**  else. "tbp1c-bpja
**    clear bpge.
**    select *
**          from bpge
**          where wrttp = 43
**            and geber = i_cobl-geber.
**      w_fistl = bpge-objnr+6(16).
**      clear fmhisv.
**      select single *
**            from fmhisv
**            where fikrs = i_cobl-fikrs
**              and hivarnt = '0000'
**              and fistl = w_fistl. "i_cobl-fistl.
**      clear t_levcnt.
**      t_levcnt-hilevel = fmhisv-hilevel.
**      t_levcnt-objnr = bpge-objnr.
**      t_levcnt-cntr = 1.
**      collect t_levcnt.
**      clear t_bdgdstr.
**      t_bdgdstr-objnr = bpge-objnr.
**      t_bdgdstr-hilev = fmhisv-hilevel.
**      t_bdgdstr-rdsum = bpge-wlges - bpge-wlgev.
**      collect t_bdgdstr.
**      if fmhisv-hilevel > w_hlevel.
**        w_hlevel = fmhisv-hilevel.
**        w_objnr = bpge-objnr.
**      endif. "fmhictr-hilevel
**    endselect. "bpge
**  endif. "tbp1c-bpja
**
******mod 07.10.2004  delete t_levcnt where hilevel <> w_hlevel.
*****mod. 28.02.2011 - do not check budget on FCentre, check hlevel instead
*****  delete t_bdgdstr where rdsum = 0.
***additional mod 01.03.2011 - to allow all FCtrs from hierarchy
***  delete t_bdgdstr where hilev <> w_hlevel.
*******mod. 05.03.2012 - check budget and lowest level for ALEREMOTE
***     if sy-uname = 'ALEREMOTE'.
***       delete t_bdgdstr where hilev <> w_hlevel.
***       delete t_bdgdstr where rdsum = 0.
***     endif. "sy-name
*******mod. 05.03.2012 END
**
******mod 07.10.2004 START ****
**  sort t_bdgdstr by hilev descending.
**  clear t_bdgdstr.
**  read table t_bdgdstr index 1.
**  if sy-subrc = 0.
*******mod 03.03.2005    w_hlevel = t_bdgdstr-hilev.
*******mod 03.03.2005    delete t_bdgdstr where hilev <> w_hlevel.
******mod 07.10.2004 END ****
**
******mod 07.10.2004  loop at t_bdgdstr.
******mod 07.10.2004    clear t_levcnt.
******mod 07.10.2004    read table t_levcnt
******mod 07.10.2004    with key objnr = t_bdgdstr-objnr.
******mod 07.10.2004    if sy-subrc <> 0.
******mod 07.10.2004      delete t_bdgdstr.
******mod 07.10.2004    endif. "sy-subrc
******mod 07.10.2004  endloop. "t_bddstr
******mod 07.10.2004  clear w_levcnt.
******mod 07.10.2004  describe table t_levcnt lines w_levcnt.
******mod 07.10.2004  if w_levcnt = 1.
******mod 07.10.2004     clear fmfctr.
******mod 07.10.2004     select *
******mod 07.10.2004           from fmfctr
******mod 07.10.2004           where fikrs = i_cobl-fikrs
******mod 07.10.2004             and ctr_objnr = w_objnr.
******mod 07.10.2004     endselect. "fmfctr
******mod 07.10.2004     if ( fmfctr-fictr <> i_cobl-fistl )
******mod 07.10.2004 and (sy-subrc = 0 ).
******mod 07.10.2004       message id 'ZFI' type 'E' number '009'
******mod 07.10.2004 with 'Please, use correct fund center - '
******mod 07.10.2004 fmfctr-fictr.
******mod 07.10.2004     endif. "fmfctr-fictr
**
******mod 07.10.2004   elseif w_levcnt > 1. "w_levcnt
**     clear fmfctr.
**     select single *
**           from fmfctr
**           where fikrs = i_cobl-fikrs
**             and fictr = i_cobl-fistl.
**     if sy-subrc = 0.
**       read table t_bdgdstr with key objnr = fmfctr-ctr_objnr.
**       if sy-subrc <> 0.
**         clear w_fctr.
**         sort t_bdgdstr.
**         loop at t_bdgdstr.
**           at new objnr.
**             clear fmfctr.
**             select *
**                   from fmfctr
**                   where fikrs = i_cobl-fikrs
**                     and ctr_objnr = t_bdgdstr-objnr.
**             endselect. "fmfctr
**             if w_fctr = space.
**               w_fctr = fmfctr-fictr.
**              else. "w_fctr
**                concatenate w_fctr fmfctr-fictr into w_fctr
**                           separated by ', '.
**             endif. "w_fctr
**           endat. "new objnr
**         endloop. "t_bdgdstr
**         message id 'ZFI' type 'E' number '009'
**                with 'Please, use correct fund center!'. ": ' w_fctr.
**       endif. "sy-subrc <> 0
**     endif. "sy-subrc = 0
******mod 07.10.2004 START ****
**   endif. "sy-subrc for read table t_bdgdstr
******mod 07.10.2004 END ****
******mod 07.10.2004  endif. "w_levcnt
*
****new Funds Centre check for BCS
*    select single *
*                 from fmbdt
*                 where rldnr = '9F'
*                   and rvers = '000'
*                   and rfikrs = i_cobl-fikrs
*                   and rfund = i_cobl-geber
*                   and budtype_9 = '3000'.
*    if sy-subrc = 0. "budget exists for the fund
*    clear fmfundtype.
*    select single * from fmfundtype
*                    where fm_area = i_cobl-fikrs
*                      and fund_type = fmfincode-type.
*    refresh t_fcbudget.
*    if fmfundtype-budget_scope = 'O'. "Overall
*      select single *
*                   from fmbdt
*                   where rldnr = '9F'
*                     and rvers = '000'
*                     and rfikrs = i_cobl-fikrs
*                     and rfund = i_cobl-geber
*                     and rfundsctr = i_cobl-fistl
*                     and budtype_9 = '3000'.
*     else. "Annual
*       select single *
*                    from fmbdt
*                    where rldnr = '9F'
*                      and rvers = '000'
**                      and ryear = i_cobl-gjahr
*                      and rfikrs = i_cobl-fikrs
*                      and rfund = i_cobl-geber
*                      and rfundsctr = i_cobl-fistl
*                      and budtype_9 = '3000'.
*    endif. "budget scope
*    if sy-subrc <> 0. "no budget on FCtr
*      clear w_fctr.
**      concatenate 'Funds Center ' i_cobl-fistl ' is incorrect for fund ' i_cobl-geber.
*      message id 'ZFI' type 'E' number '009'
*              with 'Please, use correct funds center!'.
*    endif. "sy-subrc - no budget on FCtr
*    endif. "budget existance check.
****
*  endif. "fund not in yfmxchk
*  endif. "fmfincode-type
***I_KONAKOV 03/2025 - end of removed FCtr check block
***

CHECK FMCI-FIVOR = '30' OR W_FLAG = 1." or sy-subrc <> 0.

*check for business transaction - ?
 CLEAR TJ01.
 IF I_COBL-PRVRG_SV = SPACE AND I_COBL-VORGN = 'RMBE'.
   SELECT SINGLE *
         FROM TJ01
         WHERE VRGNG = I_COBL-VORGN.
  ELSE.
    SELECT SINGLE *
          FROM TJ01
          WHERE VRGNG = I_COBL-PRVRG_SV.
 ENDIF.
 CHECK TJ01-VRGSV = 'X'.
*end of check

****
****

CLEAR FMFINCODE.
SELECT SINGLE *
      FROM FMFINCODE
      WHERE FIKRS = I_COBL-FIKRS
        AND FINCODE = I_COBL-GEBER.

IF I_COBL-PS_PSP_PNR <> SPACE.
 IF ( FMFINCODE-TYPE BETWEEN '101' AND '112' ) AND
    ( I_COBL-HKONT <> '0006046011' ).
  CLEAR PRPS.
  SELECT SINGLE *
        FROM PRPS
        WHERE PSPNR = I_COBL-PS_PSP_PNR.
  IF PRPS-POSID(10) <> I_COBL-GEBER.
    MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
           WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
  ENDIF. "prps-posid(10)
 ENDIF. "fmfincode-type
ENDIF. "i_cobl-ps_psp_pnr


IF I_COBL-GEBER = SPACE AND W_FLAG2 IS INITIAL.
 IF ( I_COBL-EKOPI = 'X' ) OR
    ( ( I_COBL-AWPOS <> SPACE ) AND
      ( I_COBL-PRVRG_SV(3) = 'RMB' ) ).

* SROCHA26072010
*SROCHA16112010
 MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
 WITH 'No fund indicated!' 'Please specify the fund.'.
 ENDIF. "i_cobl-ekopi

 ELSE. "i_cobl-geber
   CASE FMFINCODE-TYPE.
* Lionel request from 10/10/2011 due to special accounts from cash flow deficit
*     when '099' or '299' or '399'.
*           "" or '199' - excluded 21.05.04 by request of S.Shekhar
*       if i_cobl-kostl = space.
*         message id 'ZFI' type 'E' number '009'
*                with 'Please specify Cost Center!'
*                     'WBS-element is not allowed for this fund type!'.
*       endif. "i_cobl-kostl
*       if i_cobl-ps_psp_pnr <> space.
*         message id 'ZFI' type 'E' number '009'
*                with 'Please specify Cost Center!'
*                     'WBS-element is not allowed for this fund type!'.
*       endif. "i_cobl-ps_psp_pnr

*commented 18.11.03     when '001'.
*       if i_cobl-ps_psp_pnr = space.
*         message id 'ZFI' type 'E' number '009'
*                with 'Please specify the WBS-element!'.
*       endif. "i_cobl-ps_psp_pnr
*       if i_cobl-kostl <> space.
*         message id 'ZFI' type 'E' number '009'
*                with 'No Cost Center is allowed for this fund type!'.
*end of comment of 18.11.03       endif. "i_cobl-kostl
*       clear prps.
*       select single *
*             from prps
*             where pspnr = i_cobl-ps_psp_pnr.
*       if prps-posid <> i_cobl-geber+1(1).
*         message id 'ZFI' type 'E' number '009'
*                with 'Incorrect WBS-element or Fund!' ' Please check.'
.
*       endif. "prps-posid(10)

     WHEN OTHERS.
       IF ( FMFINCODE-TYPE = '005' ) OR ( FMFINCODE-TYPE = '097' ) OR
          ( FMFINCODE-TYPE BETWEEN '101' AND '112' ).
         IF I_COBL-PS_PSP_PNR = SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Please specify the WBS-element!'
                       'Cost Center is not allowed for this fund type!'.
         ENDIF. "i_cobl-ps_psp_pnr
         IF I_COBL-KOSTL <> SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Please specify the WBS-element!'
                       'Cost Center is not allowed for this fund type!'.
         ENDIF. "i_cobl-kostl
       ENDIF. "fmfincode-type
   ENDCASE. "fmfincode-type

*SROCHA26072010 Replaced by derivation rule: Business Are from Fund Type
**test done by Tal Deborah for derivation rule
*SROCHA16112010

   IF ( FMFINCODE-TYPE BETWEEN '001' AND '099' ) AND
      ( I_COBL-GSBER <> 'GEF' ).
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
            WITH 'Business area should be GEF! Fund type'
                 FMFINCODE-TYPE
                 'belongs to business area GEF.'.
    ELSEIF ( FMFINCODE-TYPE BETWEEN '100' AND '199' ) AND
           ( I_COBL-GSBER <> 'PFF' ).
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Business area should be PFF! Fund type'
                  FMFINCODE-TYPE
                  'belongs to business area PFF.'.
     ELSEIF ( FMFINCODE-TYPE BETWEEN '200' AND '299' ) AND
            ( I_COBL-GSBER <> 'MBF' ).
       MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'Business area should be MBF! Fund type'
                   FMFINCODE-TYPE
                   'belongs to business area MBF.'.
      ELSEIF ( FMFINCODE-TYPE BETWEEN '300' AND '399' ) AND
             ( I_COBL-GSBER <> 'OPF' ).
        MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
               WITH 'Business area should be OPF! Fund type'
                    FMFINCODE-TYPE
                    'belongs to business area OPF.'.
   ENDIF. "fmfincode-type


   IF I_COBL-PS_PSP_PNR <> SPACE AND I_COBL-KOSTL <> SPACE.
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
            WITH 'Please specify either Cost Center or WBS-element,' ' not both!'.
   ENDIF.

ENDIF. "i_cobl-geber

***check on request from A.Coupez of 03/04/2009
**06/2009 - temporary removed until further request
*    if ( i_cobl-fistl = 'DAR' or i_cobl-fistl = 'DAK' or
*    i_cobl-fistl =	'ACR' or i_cobl-fistl = 'ADI' or i_cobl-fistl =
*'YAO' or i_cobl-fistl = 'BAG' or i_cobl-fistl = 'RAM' or  i_cobl-fistl
*=
* 'ISB' or i_cobl-fistl = ' POP' or i_cobl-fistl = 'IIS' ) and
*       ( i_cobl-hkont between '0006011501' and '0006011508' ) and
*       i_cobl-geber(2) = '45' and
*       ( sy-tcode = 'FMX1' or sy-tcode = 'FMX2' or sy-tcode = 'PR05' ).
*      message id 'ZFI' type 'E' number '009' with
*             'Your staff travel ceiling is exhausted for this Sector. '
*             'Contact the AO of the relevant Sector '
*             'for more information'.
*    endif.


****block for instiutes - since Nov-2006
  WHEN 'IIEP' OR 'UIS' OR 'IBE' OR 'UIL' OR 'MGIE'.

******get position attributes
    CLEAR FMCI.
    SELECT SINGLE *
          FROM FMCI
          WHERE FIKRS = I_COBL-FIKRS
            AND FIPEX = I_COBL-FIPOS.



    CLEAR W_FLAG.
    CHECK FMCI-FIVOR = '30' OR SY-SUBRC <> 0.
    IF SY-SUBRC <> 0 AND
       ( I_COBL-VORGN = 'RMWE' OR I_COBL-VORGN = 'TRVL' OR I_COBL-VORGN = 'HRBV' ) AND
       I_COBL-SCOPE = 'OC'.
      W_FLAG = 1.
    ENDIF. "sy-subrc
    IF I_COBL-VORGN = 'RMWE' AND I_COBL-SCOPE IS INITIAL.
      EXIT.
    ENDIF. "i_cobl-vorgn

    CHECK FMCI-FIVOR = '30' OR W_FLAG = 1.

*****check for business transaction - ?
    CLEAR TJ01.
    IF I_COBL-PRVRG_SV = SPACE AND I_COBL-VORGN = 'RMBE'.
      SELECT SINGLE *
            FROM TJ01
            WHERE VRGNG = I_COBL-VORGN.
     ELSE.
       SELECT SINGLE *
             FROM TJ01
             WHERE VRGNG = I_COBL-PRVRG_SV.
    ENDIF.
    CHECK TJ01-VRGSV = 'X'.
*****end of check

    IF I_COBL-GEBER = SPACE AND
       I_COBL-HKONT <> '0006045011' AND I_COBL-HKONT <> '0007045011'.
      "w_flag2 is initial.
     IF ( I_COBL-EKOPI = 'X' ) OR
        ( ( I_COBL-AWPOS <> SPACE ) AND
          ( I_COBL-PRVRG_SV(3) = 'RMB' ) ).
       MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'No fund indicated!' 'Please specify the fund.'.
     ENDIF. "i_cobl-ekopi

    ELSE. "added 15/04/2011 by reuqest from B.Grujic, extended in 12/2013
      CLEAR FMFINCODE.
      SELECT SINGLE *
            FROM FMFINCODE
            WHERE FIKRS = I_COBL-FIKRS
              AND FINCODE = I_COBL-GEBER.

      CASE I_COBL-FIKRS.
        WHEN 'IBE'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200'.
              IF I_COBL-KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
              IF I_COBL-PS_PSP_PNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr

            WHEN '300'.
              IF I_COBL-PS_PSP_PNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr
              IF I_COBL-KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl

            WHEN OTHERS.
          ENDCASE.


        WHEN 'IIEP'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200' OR '307' OR '600'.
              IF I_COBL-KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
              IF I_COBL-PS_PSP_PNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr

            WHEN '300' OR '306' OR '400' OR '500' OR '700'.
              IF I_COBL-PS_PSP_PNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr
              IF I_COBL-KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
***I_KONAKOV - added 03/2021 on request from IIEP to S.Rocha
              IF I_COBL-PS_PSP_PNR <> SPACE.
                CLEAR PRPS.
                SELECT SINGLE *
                      FROM PRPS
                      WHERE PSPNR = I_COBL-PS_PSP_PNR.
                IF PRPS-POSID(10) <> I_COBL-GEBER.
                  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                    WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
                ENDIF. "prps-posid(10)
              ENDIF. "i_cobl-ps_psp_pnr
***

            WHEN OTHERS.
          ENDCASE. "fund type


        WHEN 'MGIE'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200' OR '300' OR '301' OR
                 '302' OR '303' OR '304' OR '305'.
              IF I_COBL-KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
              IF I_COBL-PS_PSP_PNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr

            WHEN OTHERS.
          ENDCASE. "fund type


        WHEN 'UIL'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200'.
              IF I_COBL-KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
              IF I_COBL-PS_PSP_PNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr

            WHEN '300' OR '301'.
              IF I_COBL-PS_PSP_PNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr
              IF I_COBL-KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl

            WHEN OTHERS.
          ENDCASE. "fund type


        WHEN 'UIS'.
          CASE FMFINCODE-TYPE.
            WHEN 200. " '100' or '200'. modified on request Y.Kassim 25/01/2018
              IF I_COBL-KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl
              IF I_COBL-PS_PSP_PNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr

            WHEN '300'.
              IF I_COBL-PS_PSP_PNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-ps_psp_pnr
              IF I_COBL-KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "i_cobl-kostl

            WHEN OTHERS.
          ENDCASE. "fund type


        WHEN OTHERS.
      ENDCASE. "fikrs

   ENDIF. "i_cobl-geber

   IF I_COBL-PS_PSP_PNR <> SPACE AND I_COBL-KOSTL <> SPACE.
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
            WITH 'Please specify either Cost Center or WBS-element,' ' not both!'.
   ENDIF.


****UBO - since Apr-2009
  WHEN 'UBO'.
******get position attributes
    CLEAR FMCI.
    SELECT SINGLE *
          FROM FMCI
          WHERE FIKRS = I_COBL-FIKRS
            AND FIPEX = I_COBL-FIPOS.



    CLEAR W_FLAG.
    CHECK FMCI-FIVOR = '30' OR SY-SUBRC <> 0.
    IF SY-SUBRC <> 0 AND
       ( I_COBL-VORGN = 'RMWE' OR I_COBL-VORGN = 'TRVL' OR I_COBL-VORGN = 'HRBV' ) AND
       I_COBL-SCOPE = 'OC'.
      W_FLAG = 1.
    ENDIF. "sy-subrc
    IF I_COBL-VORGN = 'RMWE' AND I_COBL-SCOPE IS INITIAL.
      EXIT.
    ENDIF. "i_cobl-vorgn

    CHECK FMCI-FIVOR = '30' OR W_FLAG = 1.

*****check for business transaction - ?
    CLEAR TJ01.
    IF I_COBL-PRVRG_SV = SPACE AND I_COBL-VORGN = 'RMBE'.
      SELECT SINGLE *
            FROM TJ01
            WHERE VRGNG = I_COBL-VORGN.
     ELSE.
       SELECT SINGLE *
             FROM TJ01
             WHERE VRGNG = I_COBL-PRVRG_SV.
    ENDIF.
    CHECK TJ01-VRGSV = 'X'.
*****end of check

    IF I_COBL-GEBER = 'PFF' OR I_COBL-GEBER = 'OPF' OR
       I_COBL-GEBER = 'MBF' OR I_COBL-GEBER = 'GEF'.
       IF I_COBL-KOSTL = SPACE.
         MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                WITH 'Please specify Cost Center!'.
       ENDIF. "i_cobl-kostl
       IF I_COBL-PS_PSP_PNR <> SPACE.
         MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                WITH 'WBS-element is not allowed for this fund!'.
       ENDIF. "i_cobl-ps_psp_pnr
*    elseif i_cobl-geber = '633ULO9000'.
*       if i_cobl-kostl = space.
*         message id 'ZFI' type 'E' number '009'
*                with 'Please specify Cost Center!'.
**                     'WBS-element is not allowed for this fund!'.
*       endif. "i_cobl-kostl
*       if i_cobl-ps_psp_pnr <> space.
*         message id 'ZFI' type 'E' number '009'
*                with "'Please specify Cost Center!'
*                     'WBS-element is not allowed for this fund!'.
*       endif. "i_cobl-ps_psp_pnr
*
*       if i_cobl-gsber <> 'OPF'.
*         message id 'ZFI' type 'E' number '009'
*                with 'Business area should be OPF'.
*       endif.

     ELSE.
         IF I_COBL-GEBER = SPACE.
           IF ( I_COBL-EKOPI = 'X' ) OR
              ( ( I_COBL-AWPOS <> SPACE ) AND
              ( I_COBL-PRVRG_SV(3) = 'RMB' ) ).
             MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                    WITH 'No fund indicated!' 'Please specify the fund'.
           ENDIF.
         ENDIF.
         IF I_COBL-PS_PSP_PNR = SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Please specify the WBS-element!'.
*                       'Cost Center is not allowed for this fund!'.
         ENDIF. "i_cobl-ps_psp_pnr
         IF I_COBL-KOSTL <> SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH "'Please specify the WBS-element!'
                       'Cost Center is not allowed for this fund!'.
         ENDIF. "i_cobl-kostl

         IF I_COBL-GSBER <> 'OPF' AND I_COBL-GSBER <> 'PFF'.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Business area should be OPF or PFF'.
         ENDIF.

         IF I_COBL-PS_PSP_PNR <> SPACE.
           CLEAR FMFINCODE.
           SELECT SINGLE * FROM FMFINCODE
                           WHERE FIKRS = I_COBL-FIKRS
                             AND FINCODE = I_COBL-GEBER.
           IF ( FMFINCODE-TYPE BETWEEN '101' AND '112' ) AND
              ( I_COBL-HKONT <> '0006046011' ).
             CLEAR PRPS.
             SELECT SINGLE *
                   FROM PRPS
                   WHERE PSPNR = I_COBL-PS_PSP_PNR.
             IF PRPS-POSID(10) <> I_COBL-GEBER.
               MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                 WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
             ENDIF. "prps-posid(10)
           ENDIF. "fmfincode-type
         ENDIF. "i_cobl-ps_psp_pnr

    ENDIF.

   IF I_COBL-PS_PSP_PNR <> SPACE AND I_COBL-KOSTL <> SPACE.
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
            WITH 'Please specify either Cost Center or WBS-element,' ' not both!'.
   ENDIF.


  WHEN OTHERS. "case i_cobl-fikrs

ENDCASE. "i_cobl-fikrs