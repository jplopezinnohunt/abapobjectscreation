*&---------------------------------------------------------------------*
*&  Include           YFM_ACCTCHK                                      *
*&---------------------------------------------------------------------*
*report yfm_acctchk.

TABLES: BPGE,
        BPJA,
        FMBDT,
        FMFCTR,
        FMFINCODE,
        FMCI, FMHISV, "fmfpo, fmhictr - tables changed from FM to PSM
        PRPS, TBP1C, TJ01, USR05, YFMXCHK, YFMXCHKP, YGLCHK, YXUSER, YXTCODE.

DATA: W_HLEVEL LIKE FMHICTR-HILEVEL,
      W_OBJNR LIKE BPJA-OBJNR,
      W_LEVCNT TYPE I,
      W_FLAG,
      W_FCTR(100),
      W_DATE TYPE D,
      W_PROFIL LIKE TBP1C-PROFIL.



**********
**********---Forms---
**********

**
**---initial check
**
FORM INIT_CHECK USING FP_FIKRS LIKE COBL-FIKRS
                      FP_GEBER LIKE COBL-GEBER
                      FP_FIPOS LIKE COBL-FIPOS
                      FP_VORGN LIKE COBL-VORGN
                      FP_BLART LIKE COBL-BLART
                      FP_SCOPE LIKE COBL-SCOPE
                      FP_PRVRG_SV LIKE COBL-PRVRG_SV
                      FP_BUDAT LIKE COBL-BUDAT
                      FP_GJAHR LIKE COBL-GJAHR
                      FP_GSBER LIKE COBL-GSBER
                      FP_THEAD TYPE PTRV_HEAD
                      FP_TVCHK      "if 'X' - travel user-exit
                CHANGING FP_STATUS. "ret status(if 'X' -exit from check)

DATA: R_SKIPDOC LIKE RANGE OF COBL-BLART.
DATA: BEGIN OF W_SKIPDOC,
        SIGN(1),
        OPTION(2),
        LOW LIKE COBL-BLART,
        HIGH LIKE COBL-BLART,
      END OF W_SKIPDOC.

DATA: W_MONAT LIKE COBL-MONAT,
      W_GJAHR LIKE COBL-GJAHR,
      W_MSGTX(25),
      W_NEWTRIP,
      W_THEAD TYPE PTRV_HEAD.

IF FP_VORGN = 'TRVL'.
  FP_STATUS = 'X'.
  RETURN.
ENDIF. "fp_vorgn

**check for batch transations of 'WF-BATCH' user
IF SY-TCODE = 'FMW1' OR
   SY-TCODE = 'FMW2' OR
   SY-TCODE = 'FMW3'.
  FP_STATUS = 'X'.
  RETURN.
ENDIF. "sy-tcode


CLEAR FMFINCODE.
SELECT SINGLE *
      FROM FMFINCODE
      WHERE FIKRS = FP_FIKRS
        AND FINCODE = FP_GEBER.

CLEAR W_NEWTRIP.
SELECT SINGLE * INTO W_THEAD FROM PTRV_HEAD
      WHERE PERNR = FP_THEAD-PERNR
        AND REINR = FP_THEAD-REINR.
IF SY-SUBRC <> 0.
  W_NEWTRIP = 1.
ENDIF.


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
IF SY-SUBRC = 0.
  FP_STATUS = 'X'.
  RETURN.
ENDIF. "sy-subrc
***

***11.10.2010 - do not post new trips with 149* funds - request from L.Chabeau
IF W_NEWTRIP = 1 AND FP_GEBER(3) = '149'.
  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'Impossible to use fund ' FP_GEBER.
ENDIF.
***

***11/2025 - block next years postings for certain funds (DBM request related to CF simulation in Prod)
CLEAR YFMXCHK.
IF FP_BUDAT(4) > SY-DATUM(4).
  SELECT SINGLE * FROM YFMXCHK
        WHERE FIKRS = FP_FIKRS
          AND GEBER = FP_GEBER
          AND XCHECK = 'Y'.

  IF SY-SUBRC IS INITIAL.
    CLEAR W_MSGTX.
    CONCATENATE FP_GEBER ' in the year ' FP_BUDAT(4) INTO W_MSGTX SEPARATED BY SPACE.
    MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
           WITH 'Impossible to use fund ' W_MSGTX.
  ENDIF.
ENDIF. "i_cobl-gjahr
***


***posting period blockage
CLEAR YFMXCHKP.
SELECT SINGLE * FROM YFMXCHKP WHERE BUKRS = FP_FIKRS AND CHTYP = 'FY' AND ACTIV = 'X'.
IF SY-SUBRC IS INITIAL. "and sy-sysid = 'P01'.
  W_MONAT = FP_BUDAT+4(2).
  W_GJAHR = FP_BUDAT(4).
  IF W_GJAHR = YFMXCHKP-GJAHR AND W_MONAT <= YFMXCHKP-MONAT.
CALL FUNCTION 'AUTHORITY_CHECK'
  EXPORTING
*   USER                      = SY-UNAME
    OBJECT                    = 'Y_FMUECLO'
    FIELD1                    = 'YFLAG'
*   VALUE1                    = ' '
*   FIELD2                    = ' '
*   VALUE2                    = ' '
*   FIELD3                    = ' '
*   VALUE3                    = ' '
*   FIELD4                    = ' '
*   VALUE4                    = ' '
*   FIELD5                    = ' '
*   VALUE5                    = ' '
*   FIELD6                    = ' '
*   VALUE6                    = ' '
*   FIELD7                    = ' '
*   VALUE7                    = ' '
*   FIELD8                    = ' '
*   VALUE8                    = ' '
*   FIELD9                    = ' '
*   VALUE9                    = ' '
*   FIELD10                   = ' '
*   VALUE10                   = ' '
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

IF SY-SUBRC = 2.
  FP_STATUS = ' '.
*  return.
 ELSE. "if ( fmfincode-type = '001' or fmfincode-type = '002' or
*        ( fmfincode-type between '004' and '009' ) ) and "'if' is added temporary by req. from BB.
*        fp_fikrs = 'UNES' and
*        ( sy-tcode = 'ME21' or
*          sy-tcode = 'ME21N' or
*          sy-tcode = 'ME23N' or
*          sy-tcode = 'ME51N' or
*          sy-tcode = 'FMX1'  or
*          sy-tcode = 'PR05' ) and w_newtrip = 1.
      CLEAR W_MSGTX.
      CONCATENATE W_GJAHR ', period ' W_MONAT INTO W_MSGTX.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed in the Fiscal Year ' W_MSGTX.
ENDIF. "sy-subrc authority check
**
  ENDIF. "w_gjahr
ENDIF. "sy-subrc yfmxchkp
***!!!

***BB blockage
CLEAR YFMXCHKP.
SELECT SINGLE * FROM YFMXCHKP WHERE BUKRS = FP_FIKRS AND CHTYP = 'BB' AND ACTIV = 'X'.
IF SY-SUBRC IS INITIAL.
  W_MONAT = FP_BUDAT+4(2).
  W_GJAHR = FP_BUDAT(4).
  IF W_GJAHR = YFMXCHKP-GJAHR AND W_MONAT <= YFMXCHKP-MONAT.
CALL FUNCTION 'AUTHORITY_CHECK'
  EXPORTING
*   USER                      = SY-UNAME
    OBJECT                    = 'Y_FMUECLO'
    FIELD1                    = 'YFLAG'
*   VALUE1                    = ' '
*   FIELD2                    = ' '
*   VALUE2                    = ' '
*   FIELD3                    = ' '
*   VALUE3                    = ' '
*   FIELD4                    = ' '
*   VALUE4                    = ' '
*   FIELD5                    = ' '
*   VALUE5                    = ' '
*   FIELD6                    = ' '
*   VALUE6                    = ' '
*   FIELD7                    = ' '
*   VALUE7                    = ' '
*   FIELD8                    = ' '
*   VALUE8                    = ' '
*   FIELD9                    = ' '
*   VALUE9                    = ' '
*   FIELD10                   = ' '
*   VALUE10                   = ' '
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

IF SY-SUBRC = 2.
  FP_STATUS = ' '.
*  return.
 ELSEIF FP_FIKRS = 'UNES'.
*    and w_newtrip = 1.
*      select single * from yxtcode
*                      where xtype = 'FM'
*                        and tcode = sy-tcode.
*      if sy-subrc = 0.
      CLEAR W_MSGTX.
      CONCATENATE FP_GJAHR ', period ' W_MONAT INTO W_MSGTX.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Postings are not allowed in the Fiscal Year ' W_MSGTX.
*      endif.
ENDIF. "sy-subrc authority check
**
  ENDIF. "fp_gjahr
ENDIF. "sy-subrc yfmxchkp
***BB

**



**check for Asset Management
IF ( FP_BLART = 'AA' ) OR ( FP_BLART = 'AF' ).
  FP_STATUS = 'X'.
  RETURN.
ENDIF. "fp_blart
**end of AM check


***02/02/2010 - special funds exclusion - request from D.Tal
CLEAR YFMXCHK.
SELECT SINGLE *
      FROM YFMXCHK
      WHERE FIKRS = FP_FIKRS
        AND GEBER = FP_GEBER
        AND XCHECK = 'F'.
IF SY-SUBRC IS INITIAL.
  FP_STATUS = 'X'.
  RETURN.
ENDIF.
***



**get position attributes
CLEAR FMCI.
SELECT SINGLE *
      FROM FMCI
      WHERE FIKRS = FP_FIKRS
        AND FIPEX = FP_FIPOS.

   CLEAR W_FLAG.
   IF FMCI-FIVOR <> '30' AND SY-SUBRC = 0.
     FP_STATUS = 'X'.
     RETURN.
   ENDIF. "fmci-fivor
   IF SY-SUBRC <> 0 AND
      ( FP_VORGN = 'RMWE' OR FP_VORGN = 'TRVL' ) AND
      FP_SCOPE = 'OC'.
     W_FLAG = 1.
   ENDIF. "sy-subrc
   IF FP_VORGN = 'RMWE' AND FP_SCOPE IS INITIAL.
     FP_STATUS = 'X'.
     RETURN.
   ENDIF. "fp_vorgn

  IF SY-SUBRC <> 0 AND FP_TVCHK <> SPACE.
    W_FLAG = 1.
  ENDIF.
IF FMCI-FIVOR <> '30' AND W_FLAG <> 1.
  FP_STATUS = 'X'.
  RETURN.
ENDIF. "fmci-fivor and w_flag

*check for business transaction - ?
IF FP_TVCHK = SPACE.
 CLEAR TJ01.
 SELECT SINGLE *
       FROM TJ01
       WHERE VRGNG = FP_PRVRG_SV.

 IF TJ01-VRGSV <> 'X'.
   FP_STATUS = 'X'.
   RETURN.
 ENDIF. "tj01-vrgsv
ENDIF. "fp_tvchk
*end of check

ENDFORM. "init_check

*
*
*


**
**---Fund Center hierarchy check
**
FORM FUND_CENTRE_HIER USING FP_FIKRS LIKE COBL-FIKRS
                            FP_GEBER LIKE COBL-GEBER
                            FP_FISTL LIKE COBL-FISTL
                            FP_GJAHR LIKE COBL-GJAHR.

*hierarchy levels table
DATA: BEGIN OF T_LEVCNT OCCURS 0,
        HILEVEL(4),
        OBJNR LIKE BPJA-OBJNR,
        CNTR TYPE I,
      END OF T_LEVCNT.

*table to calculate budget distribution by Fund Centers
DATA: BEGIN OF T_BDGDSTR OCCURS 0,
        OBJNR LIKE BPJA-OBJNR, "fund center
        HILEV(4),              "hierarchy level
        RDSUM LIKE BPJA-WTJHR, "distributable amount
      END OF T_BDGDSTR.

DATA: W_FISTL LIKE FMHISV-FISTL.

CLEAR FMFINCODE.
SELECT SINGLE * FROM FMFINCODE
                WHERE FIKRS = FP_FIKRS
                  AND FINCODE = FP_GEBER.

  IF ( FMFINCODE-TYPE = '001' ) OR
     ( FMFINCODE-TYPE = '002' ) OR
     ( FMFINCODE-TYPE BETWEEN '004' AND '008' ) OR
     ( FMFINCODE-TYPE BETWEEN '101' AND '114' ) OR
**added 25.08.2004 by request from S.Shekhar
     ( FMFINCODE-TYPE = '003' ).
* not ( fmfincode-type between '301' and '399' ).

    CLEAR YFMXCHK.
    SELECT SINGLE *
          FROM YFMXCHK
          WHERE FIKRS = FP_FIKRS
            AND GEBER = FP_GEBER
            AND XCHECK = 'H'.
    IF SY-SUBRC <> 0.
***new Funds Centre check for BCS
    SELECT SINGLE *
                 FROM FMBDT
                 WHERE RLDNR = '9F'
                   AND RVERS = '000'
                   AND RFIKRS = FP_FIKRS
                   AND RFUND = FP_GEBER
                   AND RFUNDSCTR = FP_FISTL
                   AND BUDTYPE_9 = '3000'.

    IF SY-SUBRC <> 0. "no budget on FCtr
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'Please, use correct funds center!'.
    ENDIF. "sy-subrc - no budget on FCtr
 ENDIF. "sy-subrc for select from yxfmchk
ENDIF. "fmfincode-type

ENDFORM. "fund_centre_hier

*
*
*


**
**---check if WBS-element corresponds to Fund
**
FORM COMPARE_FUND_WBS USING FP_PSPNR LIKE COBL-PS_PSP_PNR
                            FP_GEBER LIKE COBL-GEBER
                            FP_HKONT LIKE COBL-HKONT.
  IF FP_PSPNR <> SPACE.
   IF ( FMFINCODE-TYPE BETWEEN '101' AND '112' ) AND
      ( FP_HKONT <> '0006046011' ).
    CLEAR PRPS.
    SELECT SINGLE *
          FROM PRPS
          WHERE PSPNR = FP_PSPNR.
    IF PRPS-POSID(10) <> FP_GEBER.
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
    ENDIF. "prps-posid(10)
   ENDIF. "fmfincode-type
  ENDIF. "fp_pspnr
ENDFORM. "compare_fund_wbs

*
*
*


**
**---checks for Fund, Business Area, WBS-element, CostCentre
**
FORM FUND_BA_WBS_CC USING FP_GEBER LIKE COBL-GEBER
                          FP_EKOPI LIKE COBL-EKOPI
                          FP_AWPOS LIKE COBL-AWPOS
                          FP_PRVRG LIKE COBL-PRVRG_SV
                          FP_KOSTL LIKE COBL-KOSTL
                          FP_PSPNR LIKE COBL-PS_PSP_PNR
                          FP_GSBER LIKE COBL-GSBER
                          FP_TVCHK.

IF FP_GEBER = SPACE.
 IF ( FP_TVCHK = 'X' ) OR
    ( FP_EKOPI = 'X' ) OR
    ( ( FP_AWPOS <> SPACE ) AND
      ( FP_PRVRG(3) = 'RMB' ) ).
  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'No fund indicated!' 'Please specify the fund.'.
 ENDIF. "i_cobl-ekopi

 ELSE. "fp_geber

***check for PFF fund - request from Y.Kassim of 04.11.2010
   IF FP_GEBER = 'PFF' AND
      FP_PSPNR <> SPACE.
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'WBS-element is not allowed for this fund!'.
   ENDIF.
***

   CASE FMFINCODE-TYPE.
     WHEN '099' OR '299' OR '399'.
           "" or '199' - excluded 21.05.04 by request of S.Shekhar
       IF FP_KOSTL = SPACE.
         MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                WITH 'Please specify Cost Center!'
                     'WBS-element is not allowed for this fund type!'.
       ENDIF. "fp_kostl
       IF FP_PSPNR <> SPACE.
         MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                WITH 'Please specify Cost Center!'
                     'WBS-element is not allowed for this fund type!'.
       ENDIF. "fp_pspnr

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
       IF ( FMFINCODE-TYPE = '005' ) OR
          ( FMFINCODE-TYPE BETWEEN '101' AND '112' ).
         IF FP_PSPNR = SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Please specify the WBS-element!'
                       'Cost Center is not allowed for this fund type!'.
         ENDIF. "fp_pspnr
         IF FP_KOSTL <> SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                  WITH 'Please specify the WBS-element!'
                       'Cost Center is not allowed for this fund type!'.
         ENDIF. "fp_kostl
       ENDIF. "fmfincode-type
   ENDCASE. "fmfincode-type


   IF ( FMFINCODE-TYPE BETWEEN '001' AND '099' ) AND
      ( FP_GSBER <> 'GEF' ).
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
            WITH 'Business area should be GEF! Fund type'
                 FMFINCODE-TYPE
                 'belongs to business area GEF.'.
    ELSEIF ( FMFINCODE-TYPE BETWEEN '100' AND '199' ) AND
           ( FP_GSBER <> 'PFF' ).
      MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
             WITH 'Business area should be PFF! Fund type'
                  FMFINCODE-TYPE
                  'belongs to business area PFF.'.
     ELSEIF ( FMFINCODE-TYPE BETWEEN '200' AND '299' ) AND
            ( FP_GSBER <> 'MBF' ).
       MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
              WITH 'Business area should be MBF! Fund type'
                   FMFINCODE-TYPE
                   'belongs to business area MBF.'.
      ELSEIF ( FMFINCODE-TYPE BETWEEN '300' AND '399' ) AND
             ( FP_GSBER <> 'OPF' ).
        MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
               WITH 'Business area should be OPF! Fund type'
                    FMFINCODE-TYPE
                    'belongs to business area OPF.'.
   ENDIF. "fmfincode-type


ENDIF. "fp_geber

ENDFORM. "fund_ba_wbs_cc
**********



**
**---checks for Fund, Business Area, WBS-element, CostCentre
** for Institutes
**
FORM INST_FUND_BA_WBS_CC USING FP_FIKRS LIKE COBL-FIKRS
                               FP_GEBER LIKE COBL-GEBER
                               FP_EKOPI LIKE COBL-EKOPI
                               FP_AWPOS LIKE COBL-AWPOS
                               FP_PRVRG LIKE COBL-PRVRG_SV
                               FP_KOSTL LIKE COBL-KOSTL
                               FP_PSPNR LIKE COBL-PS_PSP_PNR
                               FP_GSBER LIKE COBL-GSBER
                               FP_TVCHK.

IF FP_GEBER = SPACE.
 IF ( FP_TVCHK = 'X' ) OR
    ( FP_EKOPI = 'X' ) OR
    ( ( FP_AWPOS <> SPACE ) AND
      ( FP_PRVRG(3) = 'RMB' ) ).
  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'No fund indicated!' 'Please specify the fund.'.
 ENDIF. "i_cobl-ekopi

 ELSE. "fp_geber
      CLEAR FMFINCODE.
      SELECT SINGLE *
            FROM FMFINCODE
            WHERE FIKRS = FP_FIKRS
              AND FINCODE = FP_GEBER.

      CASE FP_FIKRS.
        WHEN 'IBE'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200'.
              IF FP_KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_kostl
              IF FP_PSPNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_pspnr

            WHEN '300'.
              IF FP_PSPNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_pspnr
              IF FP_KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_kostl

            WHEN OTHERS.
          ENDCASE.

        WHEN 'IIEP'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200'.
              IF FP_KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_kostl
              IF FP_PSPNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_pspnr

            WHEN '300' OR '400' OR '500'.
              IF FP_PSPNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_pspnr
              IF FP_KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_kostl

            WHEN OTHERS.
          ENDCASE. "fund type

        WHEN 'UIS'.
          CASE FMFINCODE-TYPE.
            WHEN '100' OR '200'.
              IF FP_KOSTL = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_kostl
              IF FP_PSPNR <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                   WITH 'Please specify Cost Center!'
                        'WBS-element is not allowed for this fund type!'.
              ENDIF. "fp_pspnr

            WHEN '300'.
              IF FP_PSPNR = SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_pspnr
              IF FP_KOSTL <> SPACE.
                MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                       WITH 'Please specify the WBS-element!'
                            'Cost Center is not allowed for this fund type!'.
              ENDIF. "fp_kostl

            WHEN OTHERS.
          ENDCASE. "fund type

        WHEN OTHERS.
      ENDCASE.
ENDIF. "fp_geber

ENDFORM. "inst_fund...
***********