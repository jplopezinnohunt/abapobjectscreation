*----------------------------------------------------------------------
*
*   INCLUDE ZXFMYU22
*
*----------------------------------------------------------------------
*
TABLES: BPGE,
        BPJA,
        FMFCTR,
        FMFINCODE,
        FMCI, FMHISV, "fmfpo, fmhictr - tables changed from FM to PSM
        PRPS, TBP1C, TJ01, USR05, YFMXCHK.

DATA: W_HLEVEL LIKE FMHICTR-HILEVEL,
      W_OBJNR LIKE BPJA-OBJNR,
      W_LEVCNT TYPE I,
      W_FLAG,
      W_FCTR(100),
      W_DATE TYPE D,
      W_PROFIL LIKE TBP1C-PROFIL.


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



*test branch
DATA: W_TSTUNAME(12) VALUE 'I_KONAKOV'.
IF SY-UNAME = W_TSTUNAME.
*  break-point.
ENDIF.

***!!!!!temporary exclusion of TRAVEL
CHECK I_COBL-VORGN <> 'TRVL'.
***!!!!!

**check for batch transations of 'WF-BATCH' user
CHECK SY-TCODE <> 'FMW1'.
CHECK SY-TCODE <> 'FMW2'.
CHECK SY-TCODE <> 'FMW3'.


**check for user parameter allowing to avoid further checks
CLEAR USR05.
SELECT SINGLE *
      FROM USR05
      WHERE BNAME = SY-UNAME
        AND PARID = 'ZFMUCHK'.
CHECK ( SY-SUBRC <> 0 ) OR ( USR05-PARVA = SPACE ).
**end of user parameter check


**check for Asset Management
CHECK ( I_COBL-BLART <> 'AA' ) AND ( I_COBL-BLART <> 'AF' ).
**end of AM check


***check for 2004 postings in 2005 - exceptions list
*refresh r_skipdoc.
*clear w_skipdoc.
*w_skipdoc-option = 'EQ'.
*w_skipdoc-sign = 'I'.
*w_skipdoc-low = 'AB'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'AC'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'AF'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'AP'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'CO'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'ER'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'FO'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'IM'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'IO'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'JV'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'MF'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'P3'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'SC'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'SR'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'VC'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = '12'.
*append w_skipdoc to r_skipdoc.
*w_skipdoc-low = 'Z2'.
*append w_skipdoc to r_skipdoc.
**w_skipdoc-low = 'TV'.
**append w_skipdoc to r_skipdoc.

**w_date = '20050115'.
*if i_cobl-budat < '20050101'.
** if ( not ( i_cobl-blart in r_skipdoc ) ) or
**    ( i_cobl-blart = 'FO' and sy-datum > '20050112' ).
**  if ( ( i_cobl-awtyp <> space ) and ( i_cobl-awtyp <> 'TRAVL' ) and
**       ( i_cobl-awpos <> space ) ) or
**     ( i_cobl-blart = 'FO' ).
*    message id 'ZFI' type 'E' number '009'
*              with 'Postings are not allowed in the year 2004!'.
**  endif. "i_cobl-awtyp
** endif. "i_cobl-blart
*endif. "i_cobl-budat
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
      I_COBL-VORGN = 'RMWE' AND
      I_COBL-SCOPE = 'OC'.
     W_FLAG = 1.
   ENDIF. "sy-subrc
   IF I_COBL-VORGN = 'RMWE' AND I_COBL-SCOPE IS INITIAL.
     EXIT.
   ENDIF. "i_cobl-vorgn

**additional check for budget hierarchy
   CLEAR FMFINCODE.
   SELECT SINGLE *
         FROM FMFINCODE
         WHERE FIKRS = I_COBL-FIKRS
           AND FINCODE = I_COBL-GEBER.
  IF ( FMFINCODE-TYPE = '001' ) OR
     ( FMFINCODE-TYPE = '002' ) OR
     ( FMFINCODE-TYPE BETWEEN '004' AND '008' ) OR
     ( FMFINCODE-TYPE BETWEEN '101' AND '113' ) OR
**added 25.08.2004 by request from S.Shekhar
     ( FMFINCODE-TYPE = '003' ).
* not ( fmfincode-type between '301' and '399' ).

*   if i_cobl-geber <> '23111904' and
*      i_cobl-geber <> '23112704' and
*      i_cobl-geber <> '23211704' and
*      i_cobl-geber <> '23212404' and
*      i_cobl-geber <> '23213604' and
*      i_cobl-geber <> '23311404' and
*      i_cobl-geber <> '23312404' and
*      i_cobl-geber <> '23313804' and
*      i_cobl-geber <> '23411404' and
*      i_cobl-geber <> '23412404' and
*      i_cobl-geber <> '23413504' and
***temporary exclusion of the fund 29313201 - 22/07/2004
*      i_cobl-geber <> '29313201' and
***added 11.10.2004 by request from S.Shekhar
*      i_cobl-geber <> '149GEF0000'.

   CLEAR YFMXCHK.
   SELECT SINGLE *
         FROM YFMXCHK
         WHERE FIKRS = I_COBL-FIKRS
           AND GEBER = I_COBL-GEBER
           AND XCHECK = 'H'.
   IF SY-SUBRC <> 0.
*    CALL FUNCTION 'FM4C_READ_HIERARCHY'
*      EXPORTING
*       I_FIKRS               = i_cobl-fikrs
*       I_FIPOS               = i_cobl-fipos
*       I_FISTL               = i_cobl-fistl
*       I_GEBER               = i_cobl-geber
*       I_GJAHR               = i_cobl-gjahr
*     IMPORTING
*       E_PROFIL              = w_profil.

   CLEAR: TBP1C, W_OBJNR, W_HLEVEL.
   REFRESH: T_LEVCNT, T_BDGDSTR.
   SELECT SINGLE *
         FROM TBP1C
         WHERE PROFIL = FMFINCODE-PROFIL "w_profil
           AND APPLIK = 'M'
           AND WRTTP  = '43'.

  IF TBP1C-BPJA = 'X'.
   CLEAR BPJA.
   SELECT *
         FROM BPJA
         WHERE WRTTP = 43
           AND GJAHR = I_COBL-GJAHR
           AND GEBER = I_COBL-GEBER.
     CLEAR FMHISV.
     SELECT SINGLE *
           FROM FMHISV
           WHERE HIVARNT = '0000'
             AND FISTL = I_COBL-FISTL.
     CLEAR T_LEVCNT.
     T_LEVCNT-HILEVEL = FMHISV-HILEVEL.
     T_LEVCNT-OBJNR = BPJA-OBJNR.
     T_LEVCNT-CNTR = 1.
     COLLECT T_LEVCNT.
     CLEAR T_BDGDSTR.
     T_BDGDSTR-OBJNR = BPJA-OBJNR.
     T_BDGDSTR-HILEV = FMHISV-HILEVEL.
     T_BDGDSTR-RDSUM = BPJA-WLJHR - BPJA-WLJHV.
     COLLECT T_BDGDSTR.
     IF FMHISV-HILEVEL > W_HLEVEL.
       W_HLEVEL = FMHISV-HILEVEL.
       W_OBJNR = BPJA-OBJNR.
     ENDIF. "fmhictr-hilevel
   ENDSELECT. "bpja
  ELSE. "tbp1c-bpja
    CLEAR BPGE.
    SELECT *
          FROM BPGE
          WHERE WRTTP = 43
            AND GEBER = I_COBL-GEBER.
      CLEAR FMHISV.
      SELECT SINGLE *
            FROM FMHISV
            WHERE HIVARNT = '0000'
              AND FISTL = I_COBL-FISTL.
      CLEAR T_LEVCNT.
      T_LEVCNT-HILEVEL = FMHISV-HILEVEL.
      T_LEVCNT-OBJNR = BPGE-OBJNR.
      T_LEVCNT-CNTR = 1.
      COLLECT T_LEVCNT.
      CLEAR T_BDGDSTR.
      T_BDGDSTR-OBJNR = BPGE-OBJNR.
      T_BDGDSTR-HILEV = FMHISV-HILEVEL.
      T_BDGDSTR-RDSUM = BPGE-WLGES - BPGE-WLGEV.
      COLLECT T_BDGDSTR.
      IF FMHISV-HILEVEL > W_HLEVEL.
        W_HLEVEL = FMHISV-HILEVEL.
        W_OBJNR = BPGE-OBJNR.
      ENDIF. "fmhictr-hilevel
    ENDSELECT. "bpge
  ENDIF. "tbp1c-bpja

****mod 07.10.2004  delete t_levcnt where hilevel <> w_hlevel.
  DELETE T_BDGDSTR WHERE RDSUM = 0.

****mod 07.10.2004 START ****
  SORT T_BDGDSTR BY HILEV DESCENDING.
  CLEAR T_BDGDSTR.
  READ TABLE T_BDGDSTR INDEX 1.
  IF SY-SUBRC = 0.
*****mod 03.03.2005    w_hlevel = t_bdgdstr-hilev.
*****mod 03.03.2005    delete t_bdgdstr where hilev <> w_hlevel.
****mod 07.10.2004 END ****

****mod 07.10.2004  loop at t_bdgdstr.
****mod 07.10.2004    clear t_levcnt.
****mod 07.10.2004    read table t_levcnt
****mod 07.10.2004    with key objnr = t_bdgdstr-objnr.
****mod 07.10.2004    if sy-subrc <> 0.
****mod 07.10.2004      delete t_bdgdstr.
****mod 07.10.2004    endif. "sy-subrc
****mod 07.10.2004  endloop. "t_bddstr
****mod 07.10.2004  clear w_levcnt.
****mod 07.10.2004  describe table t_levcnt lines w_levcnt.
****mod 07.10.2004  if w_levcnt = 1.
****mod 07.10.2004     clear fmfctr.
****mod 07.10.2004     select *
****mod 07.10.2004           from fmfctr
****mod 07.10.2004           where fikrs = i_cobl-fikrs
****mod 07.10.2004             and ctr_objnr = w_objnr.
****mod 07.10.2004     endselect. "fmfctr
****mod 07.10.2004     if ( fmfctr-fictr <> i_cobl-fistl )
****mod 07.10.2004 and (sy-subrc = 0 ).
****mod 07.10.2004       message id 'ZFI' type 'E' number '009'
****mod 07.10.2004 with 'Please, use correct fund center - '
****mod 07.10.2004 fmfctr-fictr.
****mod 07.10.2004     endif. "fmfctr-fictr

****mod 07.10.2004   elseif w_levcnt > 1. "w_levcnt
     CLEAR FMFCTR.
     SELECT SINGLE *
           FROM FMFCTR
           WHERE FIKRS = I_COBL-FIKRS
             AND FICTR = I_COBL-FISTL.
     IF SY-SUBRC = 0.
       READ TABLE T_BDGDSTR WITH KEY OBJNR = FMFCTR-CTR_OBJNR.
       IF SY-SUBRC <> 0.
         CLEAR W_FCTR.
         SORT T_BDGDSTR.
         LOOP AT T_BDGDSTR.
           AT NEW OBJNR.
             CLEAR FMFCTR.
             SELECT *
                   FROM FMFCTR
                   WHERE FIKRS = I_COBL-FIKRS
                     AND CTR_OBJNR = T_BDGDSTR-OBJNR.
             ENDSELECT. "fmfctr
             IF W_FCTR = SPACE.
               W_FCTR = FMFCTR-FICTR.
              ELSE. "w_fctr
                CONCATENATE W_FCTR FMFCTR-FICTR INTO W_FCTR
                           SEPARATED BY ', '.
             ENDIF. "w_fctr
           ENDAT. "new objnr
         ENDLOOP. "t_bdgdstr
         MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
                WITH 'Please, use correct fund center: ' W_FCTR.
       ENDIF. "sy-subrc <> 0
     ENDIF. "sy-subrc = 0
****mod 07.10.2004 START ****
   ENDIF. "sy-subrc for read table t_bdgdstr
****mod 07.10.2004 END ****
****mod 07.10.2004  endif. "w_levcnt
  ENDIF. "i_cobl-geber <> '23......' and
  ENDIF. "fmfinode-type
**

CHECK FMCI-FIVOR = '30' OR W_FLAG = 1." or sy-subrc <> 0.

*check for business transaction - ?
 CLEAR TJ01.
 SELECT SINGLE *
       FROM TJ01
       WHERE VRGNG = I_COBL-PRVRG_SV.

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


IF I_COBL-GEBER = SPACE.
 IF ( I_COBL-EKOPI = 'X' ) OR
    ( ( I_COBL-AWPOS <> SPACE ) AND
      ( I_COBL-PRVRG_SV(3) = 'RMB' ) ).
  MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
         WITH 'No fund indicated!' 'Please specify the fund.'.
 ENDIF. "i_cobl-ekopi

 ELSE. "i_cobl-geber
   CASE FMFINCODE-TYPE.
     WHEN '099' OR '299' OR '399'.
           "" or '199' - excluded 21.05.04 by request of S.Shekhar
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


ENDIF. "i_cobl-geber