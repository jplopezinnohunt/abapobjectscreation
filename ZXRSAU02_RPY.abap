*----------------------------------------------------------------------*
*   INCLUDE ZXRSAU02    for Enhancement of BW-Masterdata               *
*----------------------------------------------------------------------*
TABLES: PROJ,
        BPGE,
        BPJA,
        FMBDT,
        FMFINCODE,
        FMFPO,
        FMHISV,
        FMPOSIT,
        JCDS,
        TJ02T,
        TJ30T,
        TBP1C,
        YBW_PSCOUNTRY.

*Data: i_IFMBWFUND like IFMBWFUND. "Extract Structure for 0FUND_ATTR
DATA: I_IFMBWFUND LIKE IFMBWFUND_ISPS. "Extr.Struct 0FUND_PU_ATTR

RANGES: R_FONDS FOR I_IFMBWFUND-FINCODE,
        R_WRTTP FOR FMFMIT2-RWRTTP.

DATA: BEGIN OF T_FMIT OCCURS 0.
        INCLUDE STRUCTURE FMFMIT2.
      DATA: END OF T_FMIT.

DATA: W_PSPNR        LIKE PRPS-PSPNR,
      W_TDNAME       LIKE THEAD-TDNAME,
      W_TITLE        LIKE TLINE,
      W_LONGTXT(792),
      W_PSLEN        TYPE I,
      W_PROJ_STATUS  LIKE BSVX-STTXT,
      W_STCNT        TYPE I,
      W_STAT         LIKE JCDS-STAT,
      W_PSTAT        LIKE TJ02T-TXT04,
      W_PBDATE       TYPE D,
      W_PEDATE       TYPE D,
      W_YEAR(4),
      W_BI           TYPE I,
      W_BDATE        TYPE D,
      W_EDATE        TYPE D,
      W_UTIME        LIKE JCDS-UTIME,
      W_TOT_WLGES    LIKE BPGE-WLGES,
      W_OBJNR        LIKE BPGE-OBJNR,
      W_HILEVEL      LIKE FMHISV-HILEVEL,
      W_FISTL        LIKE FMHISV-FISTL,
      W_FICTR        LIKE FMHISV-FISTL.


DATA: T_TITLE LIKE TLINE OCCURS 0.

DATA: BEGIN OF T_STATUS OCCURS 0,
        ISTAT LIKE JCDS-STAT,
        PSTAT LIKE TJ02T-TXT04,
        BDATE TYPE D,
        UTIME LIKE JCDS-UTIME,
        EDATE TYPE D,
      END OF T_STATUS.

DATA: BEGIN OF T_STAT2 OCCURS 0,
        ISTAT LIKE JCDS-STAT,
        PSTAT LIKE TJ02T-TXT04,
        BDATE TYPE D,
        EDATE TYPE D,
      END OF T_STAT2.

DATA: BEGIN OF T_STDUP OCCURS 0,
        ISTAT LIKE T_STATUS-ISTAT,
        BDATE TYPE D,
        UTIME LIKE JCDS-UTIME,
        INDEX LIKE SY-TABIX,
      END OF T_STDUP.

DATA: BEGIN OF T_ALLOC OCCURS 0,
        FIPOS(1),
        WLGES    LIKE BPGE-WLGES,
      END OF T_ALLOC.

DATA: T_T_DATA LIKE IFMBWFUND_ISPS OCCURS 0 WITH HEADER LINE. "IFMBWFUND

DATA: W_VDATE TYPE D.



***for 0EMPLOYEE_ATTR:
DATA: I_HRMS_BIW_IO_OCCUPANCY LIKE HRMS_BIW_IO_OCCUPANCY.

DATA: W_T905 LIKE T905.
***



***for 0EMPLOYEE_0016_ATTR
DATA: W_COUNTER TYPE I.

DATA: I_HRMS_BW_ATTR_EMPLOYEE_0016 LIKE HRMS_BW_ATTR_EMPLOYEE_0016.

DATA: T_P0000 TYPE TABLE OF P0000,
      W_P0000 TYPE P0000,
      T_P0001 TYPE TABLE OF P0001,
      W_P0001 TYPE P0001,
      T_P0016 TYPE TABLE OF P0016,
      W_P0016 TYPE P0016,
      T_P2002 TYPE TABLE OF P2002,
      W_P2002 TYPE P2002.

DATA: T_T_DATA0016 LIKE HRMS_BW_ATTR_EMPLOYEE_0016 OCCURS 0 WITH HEADER LINE.
***


***for 0HR_PA_OS_1
DATA: I_HRMS_BW_IS_POSITION LIKE HRMS_BW_IS_POSITION.

DATA: T_P1018 TYPE TABLE OF HRP1018,
      W_P1018 TYPE HRP1018,
      T_T1018 TYPE TABLE OF HRT1018,
      W_T1018 TYPE HRT1018,
      W_PROZT LIKE HRT1018-PROZT.
***


***for 0HRPOSITION_ATTR
DATA: I_HRMS_BW_IO_POSITION LIKE HRMS_BW_IO_POSITION.

DATA: T_P1005 TYPE TABLE OF HRP1005,
      W_P1005 TYPE HRP1005.
***


***for 0PROJECT_ATTR
DATA: I_BIW_PROJ_ODP LIKE BIW_PROJ_ODP.

DATA: T_SEL_FUND    TYPE TABLE OF BAPI_0051_SELFUND,
      W_SEL_FUND    TYPE BAPI_0051_SELFUND,
      T_SEL_VERSION TYPE TABLE OF BAPI_0051_SELVERSION,
      W_SEL_VERSION TYPE BAPI_0051_SELVERSION,
      T_SEL_BUDCAT  TYPE TABLE OF BAPI_0051_SELBUDCAT,
      W_SEL_BUDCAT  TYPE BAPI_0051_SELBUDCAT,
      T_SEL_WFSTATE TYPE TABLE OF BAPI_0051_SELWFSTATE,
      W_SEL_WFSTATE TYPE BAPI_0051_SELWFSTATE,
      T_SEL_BUDTYPE TYPE TABLE OF BAPI_0051_SELBUDTYPE,
      W_SEL_BUDTYPE TYPE BAPI_0051_SELBUDTYPE,
      T_SEL_VALTYPE TYPE TABLE OF BAPI_0051_SELVALTYPE,
      W_SEL_VALTYPE TYPE BAPI_0051_SELVALTYPE,
      T_BUDGET      TYPE TABLE OF BAPI_0051_ITEM_GET,
      W_BUDGET      TYPE BAPI_0051_ITEM_GET,
      T_RETURN      TYPE TABLE OF BAPIRET2.

DATA: W_TOT_BUDGET LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR,
      W_BUDGET_10  LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR,
      W_BUDGET_20  LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR,
      W_BUDGET_30  LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR,
      W_BUDGET_40  LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR,
      W_BUDGET_50  LIKE BAPI_0051_ITEM_GET-TOTAL_AMOUNT_LCUR.


DATA: T_PROJ TYPE TABLE OF PROJ,
      W_PROJ TYPE PROJ.
***



CASE I_DATASOURCE.

  WHEN '0FUND_PU_ATTR'. "'0FUND_ATTR'.
    W_VDATE = SY-DATUM.
    W_VDATE(4) = W_VDATE(4) - 5.
    W_VDATE+4(4) = '0101'.
    CLEAR I_IFMBWFUND.
    LOOP AT I_T_DATA INTO I_IFMBWFUND.
      IF I_IFMBWFUND-DATETO < W_VDATE.
        DELETE I_T_DATA.
      ENDIF.
    ENDLOOP.

    REFRESH T_T_DATA.
    CLEAR I_IFMBWFUND.
    LOOP AT I_T_DATA INTO I_IFMBWFUND.
      REFRESH: T_TITLE, T_STATUS, T_STAT2, T_STDUP.
      CLEAR: T_TITLE, T_STATUS, T_STAT2, T_STDUP.
      CLEAR: W_PSPNR, W_TDNAME, W_TITLE, W_LONGTXT, W_PSLEN,
             W_PROJ_STATUS, W_STCNT, W_STAT, W_PSTAT,
             W_PBDATE, W_PEDATE.

      I_IFMBWFUND-YYSTART_DATE = I_IFMBWFUND-DATEFROM.
      I_IFMBWFUND-YYEND_DATE = I_IFMBWFUND-DATETO.

      I_IFMBWFUND-ZZDATAB = I_IFMBWFUND-DATEFROM.
      I_IFMBWFUND-ZZDATBIS = I_IFMBWFUND-DATETO.

*put budget profile in FDSUB2
*     clear fmfincode.
*     select single * from fmfincode
*                     where fikrs = i_IFMBWFUND-fikrs
*                       and fincode = i_IFMBWFUND-fincode.
*     i_IFMBWFUND-fdsub2 = fmfincode-profil.
*     i_IFMBWFUND-zzibf = fmfincode-zzibf.
*     i_IFMBWFUND-zzoutput = fmfincode-zzoutput.
      SELECT SINGLE PROFIL FROM FMFINCODE WHERE FIKRS = @I_IFMBWFUND-FIKRS
                                          AND FINCODE = @I_IFMBWFUND-FINCODE
                    INTO @I_IFMBWFUND-FDSUB2.
      IF SY-SUBRC <> 0.
        CLEAR I_IFMBWFUND-FDSUB2.
      ENDIF.

      REFRESH: R_FONDS, R_WRTTP, T_FMIT.
      CLEAR R_FONDS.
      R_FONDS-SIGN = 'I'.
      R_FONDS-OPTION = 'EQ'.
      R_FONDS-LOW = I_IFMBWFUND-FINCODE.
      APPEND R_FONDS.
      CLEAR R_WRTTP.
      R_WRTTP-SIGN = 'I'.
      R_WRTTP-OPTION = 'EQ'.
      R_WRTTP-LOW = '50'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '51'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '52'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '54'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '57'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '58'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '60'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '61'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '65'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '66'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '80'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '81'.
      APPEND R_WRTTP.
      R_WRTTP-LOW = '82'.
      APPEND R_WRTTP.
      CALL FUNCTION 'FM_TOTALS_READ_WITH_RANGES'
        EXPORTING
          I_FIKRS   = I_IFMBWFUND-FIKRS
        TABLES
          T_RFONDS  = R_FONDS
          T_RWRTTP  = R_WRTTP
          T_FMITTAB = T_FMIT.
      SORT T_FMIT BY RYEAR DESCENDING.
      CLEAR T_FMIT.
      READ TABLE T_FMIT INDEX 1.
      I_IFMBWFUND-YYACT_YEAR = T_FMIT-RYEAR.
      I_IFMBWFUND-FICTR = T_FMIT-RFISTL.
      IF I_IFMBWFUND-YYACT_YEAR IS INITIAL.
        I_IFMBWFUND-YYACT_YEAR = I_IFMBWFUND-DATEFROM.
      ENDIF. "yyact_year
*     if i_IFMBWFUND-fictr is initial.
*       clear: w_hilevel, w_fictr.
*       select single * from fmfincode
*                       where fikrs = i_IFMBWFUND-fikrs
*                         and fincode = i_IFMBWFUND-fincode.
*       select single * from tbp1c
*                       where profil = fmfincode-profil
*                         and applik = 'M'
*                         and wrttp = '43'.
*       if tbp1c-bpja = 'X'.
*         select * from bpja
*                  where wrttp = '43'
*                    and geber = i_IFMBWFUND-fincode.
*           w_fistl = bpja-objnr+6(16).
*           select * from fmhisv
*                    where fikrs = i_IFMBWFUND-fikrs
*                      and fistl = w_fistl.
*             if fmhisv-hilevel > w_hilevel.
*               w_hilevel = fmhisv-hilevel.
*               w_fictr = fmhisv-fistl.
*             endif.
*           endselect. "fmhisv
*         endselect. "bpja
*       endif. "tbp1c-bpja
*
*       if tbp1c-bpge = 'X'.
*         select * from bpge
*                  where wrttp = '43'
*                    and geber = i_IFMBWFUND-fincode.
*           w_fistl = bpge-objnr+6(16).
*           select * from fmhisv
*                    where fikrs = i_IFMBWFUND-fikrs
*                      and fistl = w_fistl.
*             if fmhisv-hilevel > w_hilevel.
*               w_hilevel = fmhisv-hilevel.
*               w_fictr = fmhisv-fistl.
*             endif.
*           endselect. "fmhisv
*         endselect. "bpge
*       endif. "tbp1c-bpge
*       i_IFMBWFUND-fictr = w_fictr.
*     endif. "fictr

***get Funds Center from budget table
      CLEAR: W_FICTR, FMBDT.
      W_HILEVEL = 9999.
      SELECT * FROM FMBDT
               WHERE RFIKRS = I_IFMBWFUND-FIKRS
                 AND RFUND = I_IFMBWFUND-FINCODE
                 AND VALTYPE_9 = 'B1'
                 AND WFSTATE_9 = 'P'.
        W_FISTL = FMBDT-RFUNDSCTR.
        CLEAR FMHISV.
        SELECT * FROM FMHISV
                 WHERE FIKRS = I_IFMBWFUND-FIKRS
                   AND FISTL = W_FISTL.
          IF FMHISV-HILEVEL < W_HILEVEL.
            W_HILEVEL = FMHISV-HILEVEL.
            W_FICTR = FMHISV-FISTL.
          ENDIF. "hilevel
        ENDSELECT. "fmhisv
      ENDSELECT. "fmbdt
      IF W_FICTR <> SPACE.
        I_IFMBWFUND-FICTR = W_FICTR.
      ENDIF. "w_fictr



****convert Fund name to Project code
      CLEAR W_PSPNR.
      CALL FUNCTION 'CONVERSION_EXIT_ABPSP_INPUT'
        EXPORTING
          INPUT     = I_IFMBWFUND-FINCODE
        IMPORTING
          OUTPUT    = W_PSPNR
        EXCEPTIONS
          NOT_FOUND = 1
          OTHERS    = 2.

      CLEAR PRPS.
      IF SY-SUBRC = 0.
****get data from Project System
        SELECT SINGLE *
              FROM PRPS
              WHERE PSPNR = W_PSPNR.
        I_IFMBWFUND-PRART = PRPS-PRART.
        I_IFMBWFUND-YYE_DONOR = PRPS-YYE_DONOR.
        I_IFMBWFUND-YYE_EXEC = PRPS-YYE_EXEC.
        I_IFMBWFUND-YYE_TYP_SOU = PRPS-YYE_TYP_SOU.
        I_IFMBWFUND-USR00 = PRPS-USR00.
        I_IFMBWFUND-USR01 = PRPS-USR01.
        I_IFMBWFUND-USR02 = PRPS-USR02.
        I_IFMBWFUND-USR03 = PRPS-USR03.
        I_IFMBWFUND-SCPERC = ( PRPS-YYE_POUR_10 +
                               PRPS-YYE_POUR_20 +
                               PRPS-YYE_POUR_30 +
                               PRPS-YYE_POUR_40 +
                               PRPS-YYE_POUR_50 ) / 5.
*check allocations to calculcate average SC perscentage
        IF I_IFMBWFUND-SCPERC <> PRPS-YYE_POUR_10 OR
           I_IFMBWFUND-SCPERC <> PRPS-YYE_POUR_20 OR
           I_IFMBWFUND-SCPERC <> PRPS-YYE_POUR_30 OR
           I_IFMBWFUND-SCPERC <> PRPS-YYE_POUR_40 OR
           I_IFMBWFUND-SCPERC <> PRPS-YYE_POUR_50.
          REFRESH T_ALLOC.
          CLEAR: FMFPO,
                 W_TOT_WLGES,
                 I_IFMBWFUND-SCPERC.

          SELECT *
                FROM FMFPO
                WHERE FIKRS = I_IFMBWFUND-FIKRS.

            CHECK "fmfpo-fipos(1) = '1' or
                  FMFPO-FIPOS = '20' OR
                  FMFPO-FIPOS = '30' OR
                  FMFPO-FIPOS = '40' OR
                  FMFPO-FIPOS = '50'.

            CLEAR BPGE.
            SELECT *
                  FROM BPGE
                  WHERE POSIT = FMFPO-POSIT
                    AND WRTTP = 43
                    AND GEBER = I_IFMBWFUND-FINCODE.

              CLEAR T_ALLOC.
              T_ALLOC-FIPOS = FMFPO-FIPOS(1).
              T_ALLOC-WLGES = BPGE-WLGES.
              COLLECT T_ALLOC.
*           w_tot_wlges = w_tot_wlges + bpge-wlges.
            ENDSELECT. "bpge
          ENDSELECT. "fmfpo

***use commitment item PC instead of 10', 11 and 13
          CLEAR FMPOSIT.
          SELECT SINGLE *
                       FROM FMPOSIT
                       WHERE FIKRS = I_IFMBWFUND-FIKRS
                         AND FIPEX = 'PC'.
          CLEAR BPGE.
          SELECT *
                FROM BPGE
                WHERE POSIT = FMPOSIT-POSIT                 "'FP000002'
                  AND WRTTP = 43
                  AND GEBER = I_IFMBWFUND-FINCODE.
            CLEAR T_ALLOC.
            T_ALLOC-FIPOS = 1.
            T_ALLOC-WLGES = BPGE-WLGES.
            COLLECT T_ALLOC.
          ENDSELECT. "bpge

***get total budget
          CLEAR FMPOSIT.
          SELECT SINGLE *
                       FROM FMPOSIT
                       WHERE FIKRS = I_IFMBWFUND-FIKRS
                         AND FIPEX = 'TC'.
          CLEAR FMHISV.
          SELECT *
                FROM FMHISV
                WHERE FIKRS = I_IFMBWFUND-FIKRS
                  AND HILEVEL = 1.
            CONCATENATE 'FS' I_IFMBWFUND-FIKRS FMHISV-FISTL INTO W_OBJNR.
            CLEAR BPGE.
            SELECT *
                  FROM BPGE
                  WHERE OBJNR = W_OBJNR
                    AND POSIT = FMPOSIT-POSIT               "'FP000001'
                    AND WRTTP = 43
                    AND GEBER = I_IFMBWFUND-FINCODE.
              W_TOT_WLGES = W_TOT_WLGES + BPGE-WLGES.
            ENDSELECT. "bpge
          ENDSELECT. "fmhisv

***subtract CI 80 (PSC) from total budget
          CLEAR FMPOSIT.
          SELECT SINGLE *
                       FROM FMPOSIT
                       WHERE FIKRS = I_IFMBWFUND-FIKRS
                         AND FIPEX = '80'.
          CLEAR BPGE.
          SELECT *
                FROM BPGE
                WHERE POSIT = FMPOSIT-POSIT
                  AND WRTTP = 43
                  AND GEBER = I_IFMBWFUND-FINCODE.
            W_TOT_WLGES = W_TOT_WLGES - BPGE-WLGES.
          ENDSELECT. "bpge


***calculate average percentage
          IF W_TOT_WLGES <> 0. "when total allocation <> 0
            CLEAR T_ALLOC.
            LOOP AT T_ALLOC.
              CASE T_ALLOC-FIPOS.
                WHEN '1'.
                  I_IFMBWFUND-SCPERC = I_IFMBWFUND-SCPERC +
                                       T_ALLOC-WLGES / W_TOT_WLGES *
                                       PRPS-YYE_POUR_10.
                WHEN '2'.
                  I_IFMBWFUND-SCPERC = I_IFMBWFUND-SCPERC +
                                       T_ALLOC-WLGES / W_TOT_WLGES *
                                       PRPS-YYE_POUR_20.
                WHEN '3'.
                  I_IFMBWFUND-SCPERC = I_IFMBWFUND-SCPERC +
                                       T_ALLOC-WLGES / W_TOT_WLGES *
                                       PRPS-YYE_POUR_30.
                WHEN '4'.
                  I_IFMBWFUND-SCPERC = I_IFMBWFUND-SCPERC +
                                       T_ALLOC-WLGES / W_TOT_WLGES *
                                       PRPS-YYE_POUR_40.
                WHEN '5'.
                  I_IFMBWFUND-SCPERC = I_IFMBWFUND-SCPERC +
                                       T_ALLOC-WLGES / W_TOT_WLGES *
                                       PRPS-YYE_POUR_50.
                WHEN OTHERS.
              ENDCASE. "t_alloc-fipos
            ENDLOOP. "t_alloc
*         i_IFMBWFUND-scperc = i_IFMBWFUND-scperc / 5.
          ENDIF. "w_tot_wlges
        ENDIF. "i_IFMBWFUND-scperc <>
      ENDIF. "sy-subrc (after fund->project conversion)


****convert Fund name to internal project code
      CLEAR: W_PSPNR, W_TDNAME.
      CALL FUNCTION 'CONVERSION_EXIT_KONPD_INPUT'
        EXPORTING
          INPUT     = I_IFMBWFUND-FINCODE
        IMPORTING
          OUTPUT    = W_PSPNR
*         PROJWA    =
        EXCEPTIONS
          NOT_FOUND = 1
          OTHERS    = 2.

      CLEAR PROJ.
      IF SY-SUBRC = 0.
        SELECT SINGLE *
              FROM PROJ
              WHERE PSPNR = W_PSPNR.

        W_TDNAME = PROJ-OBJNR+1.
***project officer
        I_IFMBWFUND-VERNR = PROJ-VERNR.

****get project status
        CLEAR W_PROJ_STATUS.
        CALL FUNCTION 'STATUS_TEXT_EDIT'
          EXPORTING
*           CLIENT           = SY-MANDT
            FLG_USER_STAT    = 'X'
            OBJNR            = PROJ-OBJNR
            ONLY_ACTIVE      = 'X'
            SPRAS            = SY-LANGU
            BYPASS_BUFFER    = 'X'
          IMPORTING
*           ANW_STAT_EXISTING       =
*           E_STSMA          =
            LINE             = W_PROJ_STATUS
*           USER_LINE        =
*           STONR            =
          EXCEPTIONS
            OBJECT_NOT_FOUND = 1
            OTHERS           = 2.

        IF SY-SUBRC = 0.
          CLEAR W_PSLEN.
          W_PSLEN = STRLEN( W_PROJ_STATUS ).
          IF W_PSLEN > 4.
            W_PSLEN = W_PSLEN - 4.
            W_PROJ_STATUS = W_PROJ_STATUS+W_PSLEN.
          ENDIF. "w_pslen
          CONDENSE W_PROJ_STATUS.
          I_IFMBWFUND-STTXT_INT = W_PROJ_STATUS.
        ENDIF. "sy-subrc=0 after 'status_text_edit'


****get all statuses for the project
        REFRESH: T_STATUS, T_STAT2.
        W_PBDATE = I_IFMBWFUND-DATEFROM.
        CLEAR T_STATUS.
***I_KONAKOV - 21/12/2016 - replace default status with REL on request from BFM
***       t_status-istat = 'I0001'.
***       t_status-pstat = 'CRTD'.
        T_STATUS-ISTAT = 'I0002'.
        T_STATUS-PSTAT = 'REL'.
***I_KONAKOV - 21/12/2016 - end of replacement
        T_STATUS-BDATE = I_IFMBWFUND-DATEFROM.
        APPEND T_STATUS.
        CLEAR: JCDS, W_STCNT.
        SELECT *
              FROM JCDS
              WHERE OBJNR = PROJ-OBJNR
              ORDER BY UDATE.
          CHECK JCDS-INACT = SPACE.
*         check jcds-stat(1) = 'I'.
***         check jcds-chind = 'I'. "???
          CHECK JCDS-STAT = 'I0002'  "REL
             OR JCDS-STAT = 'I0042'  "PREL
             OR JCDS-STAT = 'I0045'  "TECO
             OR JCDS-STAT = 'I0046'. "CLSD

******start date for current status - 1 is end date for previous one
*         w_stcnt = w_stcnt + 1.
*         clear t_status.
*         read table t_status index w_stcnt.
*         t_status-edate = jcds-udate - 1.
*         modify t_status index w_stcnt.
*****status PREL change to status REL
          IF JCDS-STAT = 'I0042'.
            JCDS-STAT = 'I0002'.
          ENDIF. "jcds-stat
          CLEAR TJ02T.
          SELECT SINGLE *
                FROM TJ02T
                WHERE ISTAT = JCDS-STAT
                  AND SPRAS = 'E'.

          CLEAR T_STATUS.
          T_STATUS-ISTAT = JCDS-STAT.
          T_STATUS-PSTAT = TJ02T-TXT04.
          T_STATUS-BDATE = JCDS-UDATE.
          T_STATUS-UTIME = JCDS-UTIME.
          APPEND T_STATUS.
        ENDSELECT. "jcds
*****!!!!! delete obsolete statuses
        CLEAR W_STAT.
        SORT T_STATUS DESCENDING BY BDATE UTIME.
        READ TABLE T_STATUS INDEX 1.
        W_STAT = T_STATUS-ISTAT.
        DELETE T_STATUS WHERE ISTAT > W_STAT.
*****!!!!!
*****delete duplicated statuses
        CLEAR: T_STATUS, W_STAT, W_STCNT, W_BDATE, W_UTIME.
        SORT T_STATUS BY ISTAT BDATE UTIME.
        REFRESH T_STDUP.
        LOOP AT T_STATUS.
          IF W_STAT = T_STATUS-ISTAT.
            CLEAR T_STDUP.
*****!!!!!
            IF T_STATUS-ISTAT <> 'I0046'.
*****!!!!!
              T_STDUP-ISTAT = T_STATUS-ISTAT.
*!!!!!           t_stdup-index = w_stcnt.
*****!!!!!
              T_STDUP-BDATE = T_STATUS-BDATE.
              T_STDUP-UTIME = T_STATUS-UTIME.
            ELSE. "for CLSD
              T_STDUP-ISTAT = W_STAT.
              T_STDUP-BDATE = W_BDATE.
              T_STDUP-UTIME = W_UTIME.
            ENDIF. "t_status-istat
*****!!!!!
            APPEND T_STDUP.
          ENDIF. "w_stat
          W_STAT = T_STATUS-ISTAT.
          W_BDATE = T_STATUS-BDATE.
          W_UTIME = T_STATUS-UTIME.
          W_STCNT = SY-TABIX.
        ENDLOOP. "t_status
        LOOP AT T_STDUP.
*!!!!!         delete t_status index t_stdup-index.
*****!!!!!
          DELETE T_STATUS WHERE ISTAT = T_STDUP-ISTAT
                            AND BDATE = T_STDUP-BDATE
                            AND UTIME = T_STDUP-UTIME.
*****!!!!!
        ENDLOOP. "t_stdup
***I_KONAKOV - 21/12/2016 - replace default status with REL on request from BFM
***       loop at t_status where istat = 'I0001'.
        LOOP AT T_STATUS WHERE ISTAT = 'I0002'.
***I_KONAKOV - 21/12/2016 - end of replacement
          T_STATUS-BDATE = I_IFMBWFUND-DATEFROM.
          MODIFY T_STATUS.
        ENDLOOP.
******end date of Fund like end date for last status
        CLEAR W_STCNT.
        DESCRIBE TABLE T_STATUS LINES W_STCNT.
        IF W_STCNT > 0.
          CLEAR T_STATUS.
          SORT T_STATUS BY BDATE UTIME. "istat.  !!!!!!!!!!!!!!!!!!!!!!!!
          READ TABLE T_STATUS INDEX W_STCNT.
          T_STATUS-EDATE = I_IFMBWFUND-DATETO.
          MODIFY T_STATUS INDEX W_STCNT.
        ENDIF. "w_stcnt


*      else.
*     ENDIF. "sy-subrc=0
****get title text
*       concatenate 'E' prps-objnr+2 into w_tdname.
        REFRESH T_TITLE.
        CALL FUNCTION 'READ_TEXT'
          EXPORTING
*           CLIENT                  = SY-MANDT
            ID                      = 'LTXT'
            LANGUAGE                = SY-LANGU
            NAME                    = W_TDNAME
            OBJECT                  = 'PMS'
*           ARCHIVE_HANDLE          = 0
*           LOCAL_CAT               = ' '
*      IMPORTING
*           HEADER                  =
          TABLES
            LINES                   = T_TITLE
          EXCEPTIONS
            ID                      = 1
            LANGUAGE                = 2
            NAME                    = 3
            NOT_FOUND               = 4
            OBJECT                  = 5
            REFERENCE_CHECK         = 6
            WRONG_ACCESS_TO_ARCHIVE = 7
            OTHERS                  = 8.

        CLEAR: W_TITLE, W_LONGTXT.
        IF SY-SUBRC = 0.
          LOOP AT T_TITLE INTO W_TITLE.
            CLEAR W_PSLEN.
            W_PSLEN = STRLEN( W_LONGTXT ).
            IF W_PSLEN < 661.
              CONCATENATE W_LONGTXT W_TITLE-TDLINE INTO W_LONGTXT
                         SEPARATED BY SPACE.
            ENDIF. "w_pslen
          ENDLOOP. "t_title
          CONDENSE W_LONGTXT.
          SEARCH W_LONGTXT FOR 'TITLE:'.
          IF SY-SUBRC = 0.
            SHIFT W_LONGTXT BY SY-FDPOS PLACES.
          ELSE.
            SEARCH W_LONGTXT FOR 'Title:'.
            IF SY-SUBRC = 0.
              SHIFT W_LONGTXT BY SY-FDPOS PLACES.
            ENDIF. "sy-subrc
          ENDIF. "sy-subrc
          I_IFMBWFUND-TITLE1 = W_LONGTXT(60).
          I_IFMBWFUND-TITLE2 = W_LONGTXT+60(60).
          I_IFMBWFUND-TITLE3 = W_LONGTXT+120(60).
          I_IFMBWFUND-TITLE4 = W_LONGTXT+180(60).
        ELSE.
          I_IFMBWFUND-TITLE1 = PROJ-POST1.
        ENDIF. "sy-subrc=0 after title read


*******continue processing of statuses
*******for porjects started before 01.01.2002 status begins from I0002
        IF I_IFMBWFUND-DATEFROM < '20020101'.
          DELETE T_STATUS WHERE ISTAT = 'I0001'.
          LOOP AT T_STATUS WHERE ISTAT = 'I0002'.
            T_STATUS-BDATE = I_IFMBWFUND-DATEFROM.
            MODIFY T_STATUS.
          ENDLOOP. "t_status
        ENDIF. "i_IFMBWFUND-datefrom
*******
********check for dates > then end date in FM
*     clear: t_status, w_stcnt.
*     sort t_status by istat descending.
*     loop at t_status.
*       if t_status-edate > i_IFMBWFUND-dateto.
*         t_status-edate = i_IFMBWFUND-dateto - w_stcnt.
*       endif. "t_status-edate
*       if t_status-bdate > t_status-edate.
*         t_status-bdate = t_status-edate.
*       endif. "t_status-bdate
*       modify t_status.
*       w_stcnt = w_stcnt + 1.
*     endloop. "t_status
********
*******end dates like start date from next status - 1 day
        SORT T_STATUS DESCENDING BY BDATE UTIME. "istat  !!!!!!!!!!!!!!!!!!
        LOOP AT T_STATUS.
          IF SY-TABIX <> 1. "not for last status
            T_STATUS-EDATE = W_PBDATE - 1.
          ELSE. "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
***commented 16/01/2014 - 31.12.9999 for last status instead of biennum
*          clear: w_year, w_bi, w_edate.
*          w_year = t_status-edate(4).
*          w_bi = w_year mod 2. "check for biennium year
*          if w_bi = 0. "if it is first year of biennium
*            w_year = w_year + 1. "get the last year of biennium
*          endif. "w_bi
*          concatenate w_year '1231' into w_edate.
*          t_status-edate = w_edate.
            T_STATUS-EDATE = '99991231'.
***
          ENDIF. "sy-tabix
          IF ( T_STATUS-BDATE > T_STATUS-EDATE ) OR
             ( T_STATUS-BDATE IS INITIAL ).
            T_STATUS-BDATE = T_STATUS-EDATE.
          ENDIF. "t_status-bdate
          IF T_STATUS-EDATE < I_IFMBWFUND-DATEFROM.
            DELETE T_STATUS.
          ELSEIF T_STATUS-BDATE < I_IFMBWFUND-DATEFROM.
            T_STATUS-BDATE = I_IFMBWFUND-DATEFROM.
            MODIFY T_STATUS.
          ELSE.
            MODIFY T_STATUS.
          ENDIF. "t_status-edate
          W_PBDATE = T_STATUS-BDATE.
        ENDLOOP. "t_status
*******

        CLEAR T_STATUS.
        SORT T_STATUS BY BDATE UTIME. "istat bdate !!!!!!!!!!!!!!!!!!!!!!!!
        READ TABLE T_STATUS INDEX 1.
        IF SY-SUBRC = 0.
          I_IFMBWFUND-STTXT_INT = T_STATUS-PSTAT.
          I_IFMBWFUND-DATETO = T_STATUS-EDATE.
        ENDIF. "sy-subrc

      ENDIF. "sy-subrc (after fund->internal project conversion)


****get country from ybw_pscountry
      CLEAR YBW_PSCOUNTRY.
      IF I_IFMBWFUND-USR01 <> SPACE.
        SELECT SINGLE *
              FROM YBW_PSCOUNTRY
              WHERE PSCOU = I_IFMBWFUND-USR01.
      ELSEIF I_IFMBWFUND-USR00 <> SPACE.
        SELECT SINGLE *
              FROM YBW_PSCOUNTRY
              WHERE PSCOU = I_IFMBWFUND-USR00.
      ENDIF. "i_IFMBWFUND-usr01
      IF YBW_PSCOUNTRY-ISOCO <> SPACE.
        I_IFMBWFUND-USR01 = YBW_PSCOUNTRY-ISOCO.
      ELSE. "isoco
        I_IFMBWFUND-USR01 = YBW_PSCOUNTRY-SUBRG.
      ENDIF. "isoco
      I_IFMBWFUND-USR00 = YBW_PSCOUNTRY-REGIO.


      SELECT SINGLE A~C5_SEL, A~FM_OUTPUT FROM YTFM_FUND_C5 AS A
                                          INNER JOIN YTFM_C5 AS C ON C~C5_ID = A~C5_ID
                                          WHERE A~FIKRS = @I_IFMBWFUND-FIKRS
                                          AND   A~FINCODE = @I_IFMBWFUND-FINCODE
                                          AND   C~YEAR_FROM <= @I_IFMBWFUND-YYACT_YEAR
                                          AND   C~YEAR_TO >= @I_IFMBWFUND-YYACT_YEAR
                    INTO ( @I_IFMBWFUND-ZZIBF, @I_IFMBWFUND-ZZOUTPUT ).
      IF SY-SUBRC <> 0.
        CLEAR: I_IFMBWFUND-ZZIBF, I_IFMBWFUND-ZZOUTPUT.
      ENDIF.

      MODIFY I_T_DATA FROM I_IFMBWFUND.

*******add other statuses to internal table
      LOOP AT T_STATUS FROM 2.
        I_IFMBWFUND-STTXT_INT = T_STATUS-PSTAT.
        I_IFMBWFUND-DATEFROM = T_STATUS-BDATE.
        I_IFMBWFUND-DATETO = T_STATUS-EDATE.
        APPEND I_IFMBWFUND TO T_T_DATA.
      ENDLOOP. "t_status
*******

***I_KONAKOV 07/09/2012 - add empty status in the end for PFF
*commented on 16/01/2014 by request from Y.Kassim
*     if i_IFMBWFUND-dateto < '99991231' and i_IFMBWFUND-type(1) = '1'.
*       i_IFMBWFUND-sttxt_int = space.
*       i_IFMBWFUND-datefrom = i_IFMBWFUND-dateto + 1.
*       i_IFMBWFUND-dateto = '99991231'.
*       append i_IFMBWFUND to t_T_DATA.
*     endif.
***

    ENDLOOP. "I_T_DATA

******read additional statuses and add to main table
    LOOP AT T_T_DATA.
      APPEND T_T_DATA TO I_T_DATA.
    ENDLOOP. "t_T_DATA
******


*****changing end date to the end of biennium
*****and adding CLSD status to all BudgCodes
*   loop at I_T_DATA into i_IFMBWFUND.
*     check i_IFMBWFUND-sttxt_int = 'CLSD'. "check for Closed status
*only
*     w_year = i_IFMBWFUND-dateto(4).
*     w_bi = w_year mod 2. "check for biennium year
*     if w_bi = 0. "if it is first year of biennium
*       w_year = w_year + 1. "get the last year of biennium
*     endif. "w_bi
*     concatenate w_year '1231' into w_edate.
*     i_IFMBWFUND-dateto = w_edate.
*     modify I_T_DATA from i_IFMBWFUND.
*   endloop. "I_T_DATA

    SORT I_T_DATA.

*****end process of '0FUND_ATTR'


****
***0EMPLOYEE_ATTR
****
  WHEN '0EMPLOYEE_ATTR'.
    CLEAR I_HRMS_BIW_IO_OCCUPANCY.
    LOOP AT I_T_DATA INTO I_HRMS_BIW_IO_OCCUPANCY.
      CALL METHOD ZCL_HR_REGION_OF_PERS_SAREA=>READ
        EXPORTING
          WERKS = I_HRMS_BIW_IO_OCCUPANCY-WERKS
          BTRTL = I_HRMS_BIW_IO_OCCUPANCY-BTRTL
          REFDA = I_HRMS_BIW_IO_OCCUPANCY-ENDDA
        RECEIVING
          T905  = W_T905.
      I_HRMS_BIW_IO_OCCUPANCY-ZZREGGR = W_T905-REGGR.

      REFRESH T_P0001.
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
*         TCLAS           = 'A'
          PERNR           = I_HRMS_BIW_IO_OCCUPANCY-PERNR
          INFTY           = '0001'
          BEGDA           = I_HRMS_BIW_IO_OCCUPANCY-BEGDA
          ENDDA           = I_HRMS_BIW_IO_OCCUPANCY-ENDDA
*         BYPASS_BUFFER   = ' '
*         LEGACY_MODE     = ' '
*       IMPORTING
*         SUBRC           =
        TABLES
          INFTY_TAB       = T_P0001
        EXCEPTIONS
          INFTY_NOT_FOUND = 1
          OTHERS          = 2.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.

      CLEAR W_P0001.
      READ TABLE T_P0001 INTO W_P0001 INDEX 1.
      CLEAR FMFINCODE.
      SELECT SINGLE * FROM FMFINCODE
                      WHERE FIKRS = W_P0001-BUKRS
                        AND FINCODE = W_P0001-GEBER.
      I_HRMS_BIW_IO_OCCUPANCY-ZZFTYPE = FMFINCODE-TYPE.

      MODIFY I_T_DATA FROM I_HRMS_BIW_IO_OCCUPANCY.
    ENDLOOP.
*****end process of 0EMPLOYEE_ATTR


****
***0EMPLOYEE_0016_ATTR
****
  WHEN '0EMPLOYEE_0016_ATTR'.
    CLEAR I_HRMS_BW_ATTR_EMPLOYEE_0016.
    LOOP AT I_T_DATA INTO I_HRMS_BW_ATTR_EMPLOYEE_0016.
      REFRESH: T_P0000, T_P0001, T_P0016.
********actions
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
*         TCLAS           = 'A'
          PERNR           = I_HRMS_BW_ATTR_EMPLOYEE_0016-PERNR
          INFTY           = '0000'
          BEGDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATETO
          ENDDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATETO
*         BYPASS_BUFFER   = ' '
*         LEGACY_MODE     = ' '
*       IMPORTING
*         SUBRC           =
        TABLES
          INFTY_TAB       = T_P0000
        EXCEPTIONS
          INFTY_NOT_FOUND = 1
          OTHERS          = 2.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.
      CLEAR W_P0000.
      READ TABLE T_P0000 INTO W_P0000 INDEX 1.

********position
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
*         TCLAS           = 'A'
          PERNR           = I_HRMS_BW_ATTR_EMPLOYEE_0016-PERNR
          INFTY           = '0001'
          BEGDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATEFROM
          ENDDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATETO
*         BYPASS_BUFFER   = ' '
*         LEGACY_MODE     = ' '
*       IMPORTING
*         SUBRC           =
        TABLES
          INFTY_TAB       = T_P0001
        EXCEPTIONS
          INFTY_NOT_FOUND = 1
          OTHERS          = 2.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.
      CLEAR W_P0001.
      READ TABLE T_P0001 INTO W_P0001 INDEX 1.
      CLEAR FMFINCODE.
      SELECT SINGLE * FROM FMFINCODE
                      WHERE FIKRS = W_P0001-BUKRS
                        AND FINCODE = W_P0001-GEBER.
      I_HRMS_BW_ATTR_EMPLOYEE_0016-ZZFTYPE = FMFINCODE-TYPE.

********Contract end date CTEDT
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
*         TCLAS           = 'A'
          PERNR           = I_HRMS_BW_ATTR_EMPLOYEE_0016-PERNR
          INFTY           = '0016'
          BEGDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATEFROM
          ENDDA           = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATETO
*         BYPASS_BUFFER   = ' '
*         LEGACY_MODE     = ' '
*       IMPORTING
*         SUBRC           =
        TABLES
          INFTY_TAB       = T_P0016
        EXCEPTIONS
          INFTY_NOT_FOUND = 1
          OTHERS          = 2.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.
      CLEAR W_P0016.
      READ TABLE T_P0016 INTO W_P0016 INDEX 1.

      I_HRMS_BW_ATTR_EMPLOYEE_0016-MASSN = W_P0000-MASSN.
      I_HRMS_BW_ATTR_EMPLOYEE_0016-ABDAT = W_P0000-BEGDA.
      I_HRMS_BW_ATTR_EMPLOYEE_0016-PLANS = W_P0001-PLANS.
      I_HRMS_BW_ATTR_EMPLOYEE_0016-GSBER = W_P0001-GSBER.
      I_HRMS_BW_ATTR_EMPLOYEE_0016-CTEDT = W_P0016-CTEDT.

      MODIFY I_T_DATA FROM I_HRMS_BW_ATTR_EMPLOYEE_0016.
    ENDLOOP.

***for Contract types 22, 23, 24
    REFRESH T_T_DATA0016.
    CLEAR I_HRMS_BW_ATTR_EMPLOYEE_0016.
    LOOP AT I_T_DATA INTO I_HRMS_BW_ATTR_EMPLOYEE_0016.
      CHECK I_HRMS_BW_ATTR_EMPLOYEE_0016-CTTYP = '22' OR
            I_HRMS_BW_ATTR_EMPLOYEE_0016-CTTYP = '23' OR
            I_HRMS_BW_ATTR_EMPLOYEE_0016-CTTYP = '24'.
      CLEAR W_P2002.
      REFRESH T_P2002.
      CALL FUNCTION 'RH_READ_INFTY_NNNN'
        EXPORTING
*         AUTHORITY             = 'DISP'
*         WITH_STRU_AUTH        = 'X'
          PLVAR                 = '01'
          OTYPE                 = 'P'
          OBJID                 = I_HRMS_BW_ATTR_EMPLOYEE_0016-PERNR
          INFTY                 = '2002'
*         ISTAT                 = ' '
*         EXTEND                = 'X'
*         SUBTY                 = ' '
          BEGDA                 = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATEFROM
          ENDDA                 = I_HRMS_BW_ATTR_EMPLOYEE_0016-DATETO
*         CONDITION             = '00000'
*         INFTB                 = '1'
*         SORT                  = 'X'
        TABLES
          INNNN                 = T_P2002
*         OBJECTS               =
        EXCEPTIONS
          NOTHING_FOUND         = 1
          WRONG_CONDITION       = 2
          INFOTYP_NOT_SUPPORTED = 3
          WRONG_PARAMETERS      = 4
          OTHERS                = 5.
      IF SY-SUBRC <> 0.
* Implement suitable error handling here
      ENDIF.

*      CALL FUNCTION 'HR_READ_INFOTYPE'
*        EXPORTING
**         TCLAS                 = 'A'
*          PERNR                 = i_HRMS_BW_ATTR_EMPLOYEE_0016-pernr
*          INFTY                 = '2002'
*          BEGDA                 = i_HRMS_BW_ATTR_EMPLOYEE_0016-datefrom
*          ENDDA                 = i_HRMS_BW_ATTR_EMPLOYEE_0016-datefrom
**         BYPASS_BUFFER         = ' '
**         LEGACY_MODE           = ' '
**       IMPORTING
**         SUBRC                 =
*        TABLES
*          INFTY_TAB             = t_p2002
*        EXCEPTIONS
*          INFTY_NOT_FOUND       = 1
*          OTHERS                = 2
*                .
*      IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*      ENDIF.
      CLEAR T_T_DATA0016.
      MOVE-CORRESPONDING I_HRMS_BW_ATTR_EMPLOYEE_0016 TO T_T_DATA0016.
      LOOP AT T_P2002 INTO W_P2002.
        T_T_DATA0016-DATEFROM = W_P2002-BEGDA.
        T_T_DATA0016-DATETO = W_P2002-ENDDA.
        T_T_DATA0016-CTEDT  = W_P2002-ENDDA.
        APPEND T_T_DATA0016.
      ENDLOOP.                                              "t_p2002
      CLEAR W_COUNTER.
      DESCRIBE TABLE T_T_DATA0016 LINES W_COUNTER.
      IF W_COUNTER > 0.
        DELETE I_T_DATA.
      ENDIF. "w_counter
    ENDLOOP. "I_T_DATA

    CLEAR T_T_DATA0016.
    LOOP AT T_T_DATA0016.
      APPEND T_T_DATA0016 TO I_T_DATA.
    ENDLOOP. "t_T_DATA0016
*****end process of 0EMPLOYEE_0016_ATTR



****
***0HR_PA_OS_1
****
  WHEN '0HR_PA_OS_1'.
    CLEAR I_HRMS_BW_IS_POSITION.
    LOOP AT I_T_DATA INTO I_HRMS_BW_IS_POSITION.
      W_BDATE(6) = I_HRMS_BW_IS_POSITION-CALMONTH.
      W_BDATE+4(2) = '01'.
      CLEAR W_EDATE.
      CALL FUNCTION 'HR_IN_LAST_DAY_OF_MONTHS'
        EXPORTING
          DAY_IN            = W_BDATE
        IMPORTING
          LAST_DAY_OF_MONTH = W_EDATE
        EXCEPTIONS
          DAY_IN_NO_DATE    = 1
          OTHERS            = 2.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.

      REFRESH T_P1018.
      CALL FUNCTION 'RH_READ_INFTY_NNNN'
        EXPORTING
*         AUTHORITY             = 'DISP'
*         WITH_STRU_AUTH        = 'X'
          PLVAR                 = '01'
          OTYPE                 = 'S'
          OBJID                 = I_HRMS_BW_IS_POSITION-PLANS
          INFTY                 = '1018'
*         ISTAT                 = ' '
*         EXTEND                = 'X'
*         SUBTY                 = ' '
          BEGDA                 = W_BDATE
          ENDDA                 = W_EDATE
*         CONDITION             = '00000'
*         INFTB                 = '1'
*         SORT                  = 'X'
        TABLES
          INNNN                 = T_P1018
*         OBJECTS               =
        EXCEPTIONS
          NOTHING_FOUND         = 1
          WRONG_CONDITION       = 2
          INFOTYP_NOT_SUPPORTED = 3
          WRONG_PARAMETERS      = 4
          OTHERS                = 5.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.

      CLEAR W_P1018.
      SORT T_P1018 BY ENDDA DESCENDING.
      LOOP AT T_P1018 INTO W_P1018.
        IF SY-TABIX <> 1.
          DELETE T_P1018.
        ENDIF.
      ENDLOOP.
      CHECK SY-SUBRC = 0.

      REFRESH T_T1018.
      CALL FUNCTION 'RH_READ_INFTY_TABDATA'
        EXPORTING
          INFTY          = '1018'
          DBMODE         = 'X'
*         RETURN_INITIAL = 'X'
        TABLES
          INNNN          = T_P1018
          HRTNNNN        = T_T1018
        EXCEPTIONS
          NO_TABLE_INFTY = 1
          INNNN_EMPTY    = 2
          NOTHING_FOUND  = 3
          OTHERS         = 4.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.

      CLEAR: W_T1018, W_PROZT.
      LOOP AT T_T1018 INTO W_T1018.
        IF W_PROZT < W_T1018-PROZT.
          W_PROZT = W_T1018-PROZT.
          I_HRMS_BW_IS_POSITION-ZZGSBER = W_T1018-GSBER.
        ENDIF. "w_prozt
      ENDLOOP.                                              "t_t1018
      MODIFY I_T_DATA FROM I_HRMS_BW_IS_POSITION.
    ENDLOOP.
*****end process of 0HR_PA_OS_1



****
***0HRPOSITION_ATTR
****
  WHEN '0HRPOSITION_ATTR'.
    CLEAR I_HRMS_BW_IO_POSITION.
    LOOP AT I_T_DATA INTO I_HRMS_BW_IO_POSITION.

      REFRESH T_P1018.
*      CALL FUNCTION 'RH_READ_INFTY_NNNN'
*        EXPORTING
**         AUTHORITY                   = 'DISP'
**         WITH_STRU_AUTH              = 'X'
*          PLVAR                       = '01'
*          OTYPE                       = 'S'
*          OBJID                       = i_HRMS_BW_IO_POSITION-plans
*          INFTY                       = '1018'
**         ISTAT                       = ' '
**         EXTEND                      = 'X'
**         SUBTY                       = ' '
*          BEGDA                       = i_HRMS_BW_IO_POSITION-begda
*          ENDDA                       = i_HRMS_BW_IO_POSITION-endda
**         CONDITION                   = '00000'
**         INFTB                       = '1'
**         SORT                        = 'X'
*        TABLES
*          INNNN                       = t_p1018
**         OBJECTS                     =
*        EXCEPTIONS
*          NOTHING_FOUND               = 1
*          WRONG_CONDITION             = 2
*          INFOTYP_NOT_SUPPORTED       = 3
*          WRONG_PARAMETERS            = 4
*          OTHERS                      = 5
*                .
*      IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*      ENDIF.

      CLEAR HRP1018.
      SELECT * INTO TABLE T_P1018
               FROM HRP1018
               WHERE PLVAR = '01'
                 AND OTYPE = 'S'
                 AND OBJID = I_HRMS_BW_IO_POSITION-PLANS
                 AND SUBTY = SPACE
                 AND BEGDA <= I_HRMS_BW_IO_POSITION-ENDDA
                 AND ENDDA >= I_HRMS_BW_IO_POSITION-BEGDA.

      CLEAR W_P1018.
      SORT T_P1018 BY ENDDA DESCENDING.
      LOOP AT T_P1018 INTO W_P1018.
        IF SY-TABIX <> 1.
          DELETE T_P1018.
        ENDIF.
      ENDLOOP.
      CHECK SY-SUBRC = 0.

      REFRESH T_T1018.
      CALL FUNCTION 'RH_READ_INFTY_TABDATA'
        EXPORTING
          INFTY          = '1018'
          DBMODE         = 'X'
*         RETURN_INITIAL = 'X'
        TABLES
          INNNN          = T_P1018
          HRTNNNN        = T_T1018
        EXCEPTIONS
          NO_TABLE_INFTY = 1
          INNNN_EMPTY    = 2
          NOTHING_FOUND  = 3
          OTHERS         = 4.
      IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.

      CLEAR: W_T1018, W_PROZT.
      LOOP AT T_T1018 INTO W_T1018.
        IF W_PROZT < W_T1018-PROZT.
          W_PROZT = W_T1018-PROZT.
          I_HRMS_BW_IO_POSITION-ZZGSBER = W_T1018-GSBER.
        ENDIF. "w_prozt
      ENDLOOP.                                              "t_t1018

      REFRESH T_P1005.
*      CALL FUNCTION 'RH_READ_INFTY_NNNN'
*        EXPORTING
**         AUTHORITY                   = 'DISP'
**         WITH_STRU_AUTH              = 'X'
*          PLVAR                       = '01'
*          OTYPE                       = 'S'
*          OBJID                       = i_HRMS_BW_IO_POSITION-plans
*          INFTY                       = '1005'
**         ISTAT                       = ' '
**         EXTEND                      = 'X'
**         SUBTY                       = ' '
*          BEGDA                       = i_HRMS_BW_IO_POSITION-begda
*          ENDDA                       = i_HRMS_BW_IO_POSITION-endda
**         CONDITION                   = '00000'
**         INFTB                       = '1'
**         SORT                        = 'X'
*        TABLES
*          INNNN                       = t_p1005
**         OBJECTS                     =
*        EXCEPTIONS
*          NOTHING_FOUND               = 1
*          WRONG_CONDITION             = 2
*          INFOTYP_NOT_SUPPORTED       = 3
*          WRONG_PARAMETERS            = 4
*          OTHERS                      = 5
*                .
*      IF SY-SUBRC <> 0.
** MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
**         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*      ENDIF.

      CLEAR HRP1005.
      SELECT * FROM HRP1005
               INTO TABLE T_P1005
               WHERE PLVAR = '01'
                 AND OTYPE = 'S'
                 AND OBJID = I_HRMS_BW_IO_POSITION-PLANS
                 AND SUBTY = SPACE
                 AND BEGDA <= I_HRMS_BW_IO_POSITION-ENDDA
                 AND ENDDA >= I_HRMS_BW_IO_POSITION-BEGDA.

      CLEAR W_P1005.
      READ TABLE T_P1005 INTO W_P1005 INDEX 1.
      I_HRMS_BW_IO_POSITION-ZZGRADE = W_P1005-TRFG2.

      MODIFY I_T_DATA FROM I_HRMS_BW_IO_POSITION.
    ENDLOOP.
*****end 0HRPOSITION_ATTR



  WHEN '0PROJECT_ATTR'.
    LOOP AT I_T_DATA INTO I_BIW_PROJ_ODP.
****convert Project to WBS int. number
      CLEAR W_PSPNR.
      CALL FUNCTION 'CONVERSION_EXIT_ABPSP_INPUT'
        EXPORTING
          INPUT     = I_BIW_PROJ_ODP-PSPID
        IMPORTING
          OUTPUT    = W_PSPNR
        EXCEPTIONS
          NOT_FOUND = 1
          OTHERS    = 2.

      IF SY-SUBRC IS INITIAL.
        CLEAR PRPS.
        SELECT SINGLE *
              FROM PRPS
              WHERE PSPNR = W_PSPNR.
        I_BIW_PROJ_ODP-ZZPSC = ( PRPS-YYE_POUR_10 +
                                 PRPS-YYE_POUR_20 +
                                 PRPS-YYE_POUR_30 +
                                 PRPS-YYE_POUR_40 +
                                 PRPS-YYE_POUR_50 ) / 5.

*check allocations to calculcate average SC perscentage
        IF I_BIW_PROJ_ODP-ZZPSC <> PRPS-YYE_POUR_10 OR
           I_BIW_PROJ_ODP-ZZPSC <> PRPS-YYE_POUR_20 OR
           I_BIW_PROJ_ODP-ZZPSC <> PRPS-YYE_POUR_30 OR
           I_BIW_PROJ_ODP-ZZPSC <> PRPS-YYE_POUR_40 OR
           I_BIW_PROJ_ODP-ZZPSC <> PRPS-YYE_POUR_50.
          REFRESH: T_BUDGET,
                   T_SEL_VERSION,
                   T_SEL_BUDCAT,
                   T_SEL_FUND,
                   T_SEL_WFSTATE,
                   T_SEL_BUDTYPE,
                   T_SEL_VALTYPE,
                   T_RETURN.

          CLEAR: W_SEL_VERSION,
                 W_SEL_BUDCAT,
                 W_SEL_FUND,
                 W_SEL_WFSTATE,
                 W_SEL_BUDTYPE,
                 W_SEL_VALTYPE.

          W_SEL_VERSION-SIGN = 'I'.
          W_SEL_VERSION-OPTION = 'EQ'.
          W_SEL_VERSION-LOW = '000'.
          APPEND W_SEL_VERSION TO T_SEL_VERSION.

          W_SEL_BUDCAT-SIGN = 'I'.
          W_SEL_BUDCAT-OPTION = 'EQ'.
          W_SEL_BUDCAT-LOW = '9F'.
          APPEND W_SEL_BUDCAT TO T_SEL_BUDCAT.

          W_SEL_WFSTATE-SIGN = 'I'.
          W_SEL_WFSTATE-OPTION = 'EQ'.
          W_SEL_WFSTATE-LOW = 'P'.
          APPEND W_SEL_WFSTATE TO T_SEL_WFSTATE.

          W_SEL_BUDTYPE-SIGN = 'I'.
          W_SEL_BUDTYPE-OPTION = 'EQ'.
          W_SEL_BUDTYPE-LOW = '3000'.
          APPEND W_SEL_BUDTYPE TO T_SEL_BUDTYPE.

          W_SEL_VALTYPE-SIGN = 'I'.
          W_SEL_VALTYPE-OPTION = 'EQ'.
          W_SEL_VALTYPE-LOW = 'B1'.
          APPEND W_SEL_VALTYPE TO T_SEL_VALTYPE.

          W_SEL_FUND-SIGN = 'I'.
          W_SEL_FUND-OPTION = 'EQ'.
          W_SEL_FUND-LOW = I_BIW_PROJ_ODP-PSPID.
          APPEND W_SEL_FUND TO T_SEL_FUND.

          CALL FUNCTION 'BAPI_0051_GET_TOTALS'
            EXPORTING
              F_MNGT_AREA         = I_BIW_PROJ_ODP-VKOKR
*             MAX_ROWS            =
*             GET_PERIOD          =
            TABLES
*             SEL_FISCAL_YEAR     =
              SEL_VERSION         = T_SEL_VERSION
              SEL_BUDGET_CATEGORY = T_SEL_BUDCAT
              SEL_FUND            = T_SEL_FUND
*             SEL_FUNDS_CENTER    =
*             SEL_COMMITMENT_ITEM =
*             SEL_FUNCTIONAL_AREA =
*             SEL_MEASURE         =
*             SEL_GRANT           =
              SEL_WORKFLOW_STATE  = T_SEL_WFSTATE
*             SEL_PROCESS         =
              SEL_BUDGET_TYPE     = T_SEL_BUDTYPE
*             SEL_PERIOD          =
              ITEM_DATA           = T_BUDGET
*             PERIOD_DATA         =
              RETURN              = T_RETURN
              SEL_VALUE_TYPE      = T_SEL_VALTYPE
*             SEL_CASH_YEAR       =
*             SEL_BUDGET_PD       =
            .

          DELETE T_BUDGET WHERE CMMT_ITEM(1) <> '1' AND
                                CMMT_ITEM(1) <> '2' AND
                                CMMT_ITEM(1) <> '3' AND
                                CMMT_ITEM(1) <> '4' AND
                                CMMT_ITEM(1) <> '5'.

          CLEAR: W_BUDGET,
                 W_TOT_BUDGET,
                 W_BUDGET_10,
                 W_BUDGET_20,
                 W_BUDGET_30,
                 W_BUDGET_40,
                 W_BUDGET_50.

          LOOP AT T_BUDGET INTO W_BUDGET.
            CASE W_BUDGET-CMMT_ITEM(1).
              WHEN '1'.
                W_BUDGET_10 = W_BUDGET_10 - W_BUDGET-TOTAL_AMOUNT_LCUR.
              WHEN '2'.
                W_BUDGET_20 = W_BUDGET_20 - W_BUDGET-TOTAL_AMOUNT_LCUR.
              WHEN '3'.
                W_BUDGET_30 = W_BUDGET_30 - W_BUDGET-TOTAL_AMOUNT_LCUR.
              WHEN '4'.
                W_BUDGET_40 = W_BUDGET_40 - W_BUDGET-TOTAL_AMOUNT_LCUR.
              WHEN '5'.
                W_BUDGET_50 = W_BUDGET_50 - W_BUDGET-TOTAL_AMOUNT_LCUR.
            ENDCASE. "cmmt_item
            W_TOT_BUDGET = W_TOT_BUDGET - W_BUDGET-TOTAL_AMOUNT_LCUR.
          ENDLOOP.

          IF W_TOT_BUDGET <> 0.
            I_BIW_PROJ_ODP-ZZPSC = ( W_BUDGET_10 / W_TOT_BUDGET * PRPS-YYE_POUR_10 ) +
                                   ( W_BUDGET_20 / W_TOT_BUDGET * PRPS-YYE_POUR_20 ) +
                                   ( W_BUDGET_30 / W_TOT_BUDGET * PRPS-YYE_POUR_30 ) +
                                   ( W_BUDGET_40 / W_TOT_BUDGET * PRPS-YYE_POUR_40 ) +
                                   ( W_BUDGET_50 / W_TOT_BUDGET * PRPS-YYE_POUR_50 ).

          ENDIF.
        ENDIF. "if PSC % is not the same for all CI

        I_BIW_PROJ_ODP-ZZRELEV = PRPS-YYE_RELEV.
      ENDIF. "sy-subrc - project to WBS


***add project start/end dates
      CLEAR: W_PSPNR, W_PROJ.
      CALL FUNCTION 'CONVERSION_EXIT_KONPD_INPUT'
        EXPORTING
          INPUT     = I_BIW_PROJ_ODP-PSPID
        IMPORTING
          OUTPUT    = W_PSPNR
          PROJWA    = W_PROJ
        EXCEPTIONS
          NOT_FOUND = 1
          OTHERS    = 2.
      IF SY-SUBRC <> 0.
* Implement suitable error handling here
      ENDIF.

      I_BIW_PROJ_ODP-ZZPLFAZ = W_PROJ-PLFAZ.
      I_BIW_PROJ_ODP-ZZPLSEZ = W_PROJ-PLSEZ.

*User status
      REFRESH T_STATUS.
      CLEAR: JCDS, W_STCNT.
      SELECT *
            FROM JCDS
            WHERE OBJNR = I_BIW_PROJ_ODP-OBJNR
            ORDER BY UDATE.
        CHECK JCDS-INACT = SPACE.
        CHECK JCDS-STAT = 'E0008'  "OREP
           OR JCDS-STAT = 'E0009'. "CREP

        CLEAR TJ30T.
        SELECT SINGLE *
              FROM TJ30T
              WHERE STSMA = 'UNESCO01'
                AND ESTAT = JCDS-STAT
                AND SPRAS = 'E'.

        CLEAR T_STATUS.
        T_STATUS-ISTAT = JCDS-STAT.
        T_STATUS-PSTAT = TJ30T-TXT04.
        T_STATUS-BDATE = JCDS-UDATE.
        T_STATUS-UTIME = JCDS-UTIME.
        APPEND T_STATUS.
      ENDSELECT. "jcds
      SORT T_STATUS BY BDATE DESCENDING UTIME DESCENDING.
      CLEAR T_STATUS.
      READ TABLE T_STATUS INDEX 1.
      I_BIW_PROJ_ODP-ZZUSRSTAT = T_STATUS-PSTAT.
      I_BIW_PROJ_ODP-ZZSTATUSDATE = T_STATUS-BDATE.

      MODIFY I_T_DATA FROM I_BIW_PROJ_ODP.
    ENDLOOP. "I_T_DATA
*****end 0PROJECT_ATTR


  WHEN OTHERS.

ENDCASE. "i_datasource