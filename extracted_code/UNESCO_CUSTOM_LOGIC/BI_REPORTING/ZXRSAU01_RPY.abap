*----------------------------------------------------------------------*
*   INCLUDE ZXRSAU01                                                   *
*----------------------------------------------------------------------*
TABLES: BSEG,
        FMIFIIT,
        FMIFIHD,
        FMIOI,
        HRP1018,
        HRP1516.

DATA: W_IFMBWACTFIIT LIKE IFMBWACTFIIT_ISPS. "like IFMBWACTFIIT.

DATA: W_IFMBWACTOPIT_ISPS LIKE IFMBWACTOPIT_ISPS.

DATA: W_EINDT LIKE EKET-EINDT,
      W_PDATE TYPE D,
      W_PO_CRDATE TYPE D,
      W_KBLE  TYPE KBLE,
      W_KBLP  TYPE KBLP,
      W_BSEG  TYPE BSEG,
      W_SIGN  TYPE I,
      W_OBJNR TYPE J_OBJNR,
      W_AMNT  TYPE FM_FKBTR,
      W_XBLNR TYPE XBLNR1,
      W_FTYPE TYPE FM_FUNDTYPE.

DATA: T_KBLE TYPE TABLE OF KBLE.

DATA: BEGIN OF T_PDATE OCCURS 0.
*        vrgng like fmifiit-vrgng,
*        pdate type d,
*        trbtr like fmifiit-trbtr,
        INCLUDE STRUCTURE FMIFIIT.
      DATA: END OF T_PDATE.


***for 0HR_PA_OS_1
DATA: I_HRMS_BW_IS_POSITION LIKE HRMS_BW_IS_POSITION.

DATA: T_P1018 TYPE TABLE OF HRP1018,
      W_P1018 TYPE HRP1018,
      T_T1018 TYPE TABLE OF HRT1018,
      W_T1018 TYPE HRT1018,
      W_PROZT LIKE HRT1018-PROZT,
      W_BDATE TYPE D,
      W_EDATE TYPE D.

***

***for 0PSM_PBC_01
DATA: I_HRFPM_BW_FPM_01 LIKE HRFPM_BW_FPM_01.

DATA: W_SDATE TYPE D.
***


***for 0CO_OM_WBS_8
DATA: W_VORGA     LIKE BPEJ-VORGA,
      W_BPEJ      LIKE BPEJ,
      W_PRPS      TYPE PRPS,
      W_PRHI      TYPE PRHI,
      W_ICWBSBUD1 LIKE ICWBSBUD1.
***


***for 0FI_AR_4
DATA: W_DTFIAR_3 LIKE DTFIAR_3.
***




CASE I_DATASOURCE.
****
***0PU_IS_PS_32 - FM actuals
****
  WHEN '0PU_IS_PS_32'. "'0FI_FM_32'
    LOOP AT C_T_DATA INTO W_IFMBWACTFIIT.
*      replace all occurrences of regex '\t' in w_IFMBWACTFIIT-sgtxt with '_'.
*      replace all occurrences of regex '[[:cntrl:]]' in w_IFMBWACTFIIT-sgtxt with '_'.
      SELECT SINGLE HWAE2 INTO W_IFMBWACTFIIT-ZZHWAE2
                          FROM BKPF
                          WHERE BUKRS = W_IFMBWACTFIIT-BUKRS
                            AND BELNR = W_IFMBWACTFIIT-KNBELNR
                            AND GJAHR = W_IFMBWACTFIIT-KNGJAHR.

      CLEAR W_BSEG.
      SELECT SINGLE * INTO W_BSEG
                      FROM BSEG
                      WHERE BUKRS = W_IFMBWACTFIIT-BUKRS
                        AND BELNR = W_IFMBWACTFIIT-KNBELNR
                        AND GJAHR = W_IFMBWACTFIIT-KNGJAHR
                        AND BUZEI = W_IFMBWACTFIIT-KNBUZEI.
      IF W_IFMBWACTFIIT-KOSTL IS INITIAL.
        W_IFMBWACTFIIT-KOSTL = BSEG-KOSTL.
      ENDIF. "w_IFMBWACTFIIT-kostl
      IF W_IFMBWACTFIIT-POSID IS INITIAL.
        CLEAR PRPS.
        SELECT SINGLE *
              FROM PRPS
              WHERE PSPNR = BSEG-PROJK.
        W_IFMBWACTFIIT-POSID = PRPS-POSID.
      ENDIF. "w_IFMBWACTFIIT-posid

      IF W_IFMBWACTFIIT-ZZHWAE2 = 'USD'.
        W_IFMBWACTFIIT-ZZDMBE2 = W_BSEG-DMBE2.
        IF W_BSEG-SHKZG = 'H'. "if credit entry
          W_IFMBWACTFIIT-ZZDMBE2 = -1 * W_IFMBWACTFIIT-ZZDMBE2.
        ENDIF. "shkzg
********check sign of the FM entry vs FI entry in case of multiple FM entries per one FI
        W_SIGN = SIGN( W_IFMBWACTFIIT-FKBTR ) * SIGN( W_IFMBWACTFIIT-ZZDMBE2 ).
        IF W_SIGN <> 0.
          W_IFMBWACTFIIT-ZZDMBE2 = W_SIGN * W_IFMBWACTFIIT-ZZDMBE2.
        ENDIF. "w_sign
********
      ELSEIF W_IFMBWACTFIIT-WAERS = 'USD'.
        W_IFMBWACTFIIT-ZZDMBE2 = W_IFMBWACTFIIT-FKBTR.
        W_IFMBWACTFIIT-ZZHWAE2 = W_IFMBWACTFIIT-WAERS.
****put amount in UNORE rate from FI for RP postings in EUR
        IF W_IFMBWACTFIIT-TWAER = 'EUR' AND W_IFMBWACTFIIT-BUKRS = 'UNES' AND W_BSEG-GJAHR >= 2025.
          CLEAR W_FTYPE.
          SELECT SINGLE TYPE INTO W_FTYPE
                        FROM  FMFINCODE
                        WHERE FIKRS = W_IFMBWACTFIIT-FIKRS
                          AND FINCODE = W_IFMBWACTFIIT-FONDS.

         IF W_FTYPE BETWEEN '001' AND '099'.
           W_IFMBWACTFIIT-ZZDMBE2 = W_BSEG-DMBTR.
           IF W_BSEG-SHKZG = 'H'. "if credit entry
             W_IFMBWACTFIIT-ZZDMBE2 = -1 * W_IFMBWACTFIIT-ZZDMBE2.
           ENDIF. "shkzg
***********check sign of the FM entry vs FI entry in case of multiple FM entries per one FI
           W_SIGN = SIGN( W_IFMBWACTFIIT-FKBTR ) * SIGN( W_IFMBWACTFIIT-ZZDMBE2 ).
           IF W_SIGN <> 0.
             W_IFMBWACTFIIT-ZZDMBE2 = W_SIGN * W_IFMBWACTFIIT-ZZDMBE2.
           ENDIF. "w_sign
***********
         ENDIF. "RP fund type
        ENDIF. "RP conditions
****end of UNORE insert
      ENDIF.

      MODIFY C_T_DATA FROM W_IFMBWACTFIIT.
    ENDLOOP. "c_t_data



****
***0HR_PA_OS_1
****
  WHEN '0HR_PA_OS_1'.

*to remove double lines for occupied posts
    DATA: BEGIN OF T_TEMPDATA OCCURS 0.
            INCLUDE STRUCTURE HRMS_BW_IS_POSITION.
          DATA: END OF T_TEMPDATA.

    T_TEMPDATA[] = C_T_DATA[].
    CLEAR I_HRMS_BW_IS_POSITION.
    LOOP AT C_T_DATA INTO I_HRMS_BW_IS_POSITION.
      CHECK I_HRMS_BW_IS_POSITION-PERNR <> SPACE.
      CLEAR T_TEMPDATA.
      READ TABLE T_TEMPDATA
           WITH KEY CALMONTH = I_HRMS_BW_IS_POSITION-CALMONTH
                    PLANS = I_HRMS_BW_IS_POSITION-PLANS
                    STELL = I_HRMS_BW_IS_POSITION-STELL
                    ORGEH = I_HRMS_BW_IS_POSITION-ORGEH
                    PERNR = SPACE.
      CHECK SY-SUBRC = 0.
      I_HRMS_BW_IS_POSITION-IS_LEADER = T_TEMPDATA-IS_LEADER.
      I_HRMS_BW_IS_POSITION-CONTROL_SPAN = T_TEMPDATA-CONTROL_SPAN.
      MODIFY C_T_DATA FROM I_HRMS_BW_IS_POSITION.
    ENDLOOP. "C_T_DATA

    LOOP AT C_T_DATA INTO I_HRMS_BW_IS_POSITION.
      CHECK I_HRMS_BW_IS_POSITION-PERNR = SPACE.
      LOOP AT T_TEMPDATA
              WHERE CALMONTH = I_HRMS_BW_IS_POSITION-CALMONTH AND
                    PLANS = I_HRMS_BW_IS_POSITION-PLANS AND
                    STELL = I_HRMS_BW_IS_POSITION-STELL AND
                    ORGEH = I_HRMS_BW_IS_POSITION-ORGEH AND
                    PERNR <> SPACE.
      ENDLOOP. "t_tempdata
      CHECK SY-SUBRC IS INITIAL.
      DELETE C_T_DATA.
    ENDLOOP. "C_T_DATA
*

    CLEAR I_HRMS_BW_IS_POSITION.
    LOOP AT C_T_DATA INTO I_HRMS_BW_IS_POSITION.
      W_BDATE(6) = I_HRMS_BW_IS_POSITION-CALMONTH.
      W_BDATE+6(2) = '01'.
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

      CLEAR HRP1018.
      SELECT * INTO TABLE T_P1018
               FROM HRP1018
               WHERE PLVAR = '01'
                 AND OTYPE = 'S'
                 AND OBJID = I_HRMS_BW_IS_POSITION-PLANS
                 AND SUBTY = SPACE
                 AND BEGDA <= W_EDATE
                 AND ENDDA >= W_BDATE.


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
      MODIFY C_T_DATA FROM I_HRMS_BW_IS_POSITION.
    ENDLOOP.
*****end process of 0HR_PA_OS_1



*****
*****0PSM_PBC_01
*****
  WHEN '0PSM_PBC_01'.
    LOOP AT C_T_DATA INTO I_HRFPM_BW_FPM_01.
      CONCATENATE I_HRFPM_BW_FPM_01-CALMONTH '01'
                  INTO W_SDATE.
      CLEAR HRP1516.
      SELECT *
            FROM HRP1516
            WHERE PLVAR = I_HRFPM_BW_FPM_01-PLVAR
              AND OTYPE = 'S'
              AND OBJID = I_HRFPM_BW_FPM_01-HRPOSITION
              AND BEGDA <= W_SDATE
              AND ENDDA >= W_SDATE.

      ENDSELECT.                                            "hrp1516
      I_HRFPM_BW_FPM_01-ZZRUNID = HRP1516-RUNID.
      MODIFY C_T_DATA FROM I_HRFPM_BW_FPM_01.
    ENDLOOP. "c_t_data
*****end of 0PSM_PBC_01



*****
*****0PU_IS_PS_31
*****
  WHEN '0PU_IS_PS_31'. "PSM commitments
    CLEAR W_IFMBWACTOPIT_ISPS.
    LOOP AT C_T_DATA INTO W_IFMBWACTOPIT_ISPS.
********"real" posting date
      REFRESH T_PDATE.
      CLEAR W_PDATE.
      CASE W_IFMBWACTOPIT_ISPS-BTART.
        WHEN '0200' OR '0500'.
          CLEAR W_OBJNR.
          IF W_IFMBWACTOPIT_ISPS-KOSTL <> SPACE.
            SELECT SINGLE OBJNR INTO W_OBJNR
                                FROM CSKS WHERE KOKRS = W_IFMBWACTOPIT_ISPS-FIKRS
                                            AND KOSTL = W_IFMBWACTOPIT_ISPS-KOSTL.
          ENDIF. "kostl
          IF W_IFMBWACTOPIT_ISPS-POSID <> SPACE.
            SELECT SINGLE OBJNR INTO W_OBJNR
                                FROM PRPS WHERE POSID = W_IFMBWACTOPIT_ISPS-POSID.
          ENDIF. "posid

**************  Begin Performance issue NME20240117
*          SELECT *
*                FROM fmifiit
*                WHERE fikrs  = w_ifmbwactopit_isps-fikrs
*                  AND objnrz = w_objnr
*                  AND fonds  = w_ifmbwactopit_isps-fonds
*                  AND vrefbn = w_ifmbwactopit_isps-refbn
*                  AND vrforg = w_ifmbwactopit_isps-rforg
*                  AND vrfpos = w_ifmbwactopit_isps-rfpos
*                  AND vrfknt = w_ifmbwactopit_isps-rfknt.
*
*            CLEAR fmifihd.
*            SELECT SINGLE * FROM fmifihd
*                            WHERE fmbelnr = fmifiit-fmbelnr
*                              AND fikrs = fmifiit-fikrs.
*
*            IF fmifihd-xrevs = 'X'. "check FM doc is not reversed
*              CONTINUE.
*            ENDIF. "xrevs
*
*            CLEAR t_pdate.
*            MOVE-CORRESPONDING fmifiit TO t_pdate.
*            APPEND t_pdate. "collect actuals' dates and op.types
*
*          ENDSELECT. "fmifiit

          SELECT A~* FROM FMIFIIT AS A INNER JOIN FMIFIHD AS B ON  B~FMBELNR = A~FMBELNR
                                                               AND B~FIKRS = A~FIKRS
                              WHERE A~FIKRS = @W_IFMBWACTOPIT_ISPS-FIKRS
                              AND   A~OBJNRZ = @W_OBJNR
                              AND   A~FONDS = @W_IFMBWACTOPIT_ISPS-FONDS
                              AND   A~VREFBN = @W_IFMBWACTOPIT_ISPS-REFBN
                              AND   A~VRFORG = @W_IFMBWACTOPIT_ISPS-RFORG
                              AND   A~VRFPOS = @W_IFMBWACTOPIT_ISPS-RFPOS
                              AND   A~VRFKNT = @W_IFMBWACTOPIT_ISPS-RFKNT
                              AND   B~XREVS = @SPACE
                              %_HINTS MSSQLNT '&REPARSE&'
                        APPENDING CORRESPONDING FIELDS OF TABLE @T_PDATE.
**************  End Performance issue NME20240117

          CLEAR T_PDATE.
          SORT T_PDATE BY ZHLDT DESCENDING.
          READ TABLE T_PDATE WITH KEY TRBTR = W_IFMBWACTOPIT_ISPS-TRBTR.
          IF SY-SUBRC <> 0.
            READ TABLE T_PDATE WITH KEY FKBTR = W_IFMBWACTOPIT_ISPS-FKBTR.
          ENDIF.
          IF SY-SUBRC <> 0.
            READ TABLE T_PDATE INDEX 1.
          ENDIF. "sy-subrc
          W_PDATE = T_PDATE-ZHLDT.

          IF W_IFMBWACTOPIT_ISPS-BTART = '0500'.
            CLEAR T_PDATE.
            LOOP AT T_PDATE WHERE VRGNG = 'RMRP'.
              W_PDATE = T_PDATE-ZHLDT.
              EXIT.
            ENDLOOP. "t_pdate
          ENDIF. "btart

          CASE W_IFMBWACTOPIT_ISPS-ACTDETL.
            WHEN '030'. "FR
              IF W_IFMBWACTOPIT_ISPS-BTART = '0500'.
                SELECT SINGLE ERLDAT
                      INTO W_PDATE
                      FROM KBLP
                      WHERE BELNR = W_IFMBWACTOPIT_ISPS-REFBN
                        AND BLPOS = W_IFMBWACTOPIT_ISPS-RFPOS.

              ELSE. "btart = 200
                CLEAR W_KBLE.
                REFRESH T_KBLE.
                SELECT *
                      INTO W_KBLE
                      FROM KBLE
                      WHERE BELNR = W_IFMBWACTOPIT_ISPS-REFBN
                        AND BLPOS = W_IFMBWACTOPIT_ISPS-RFPOS.
                  CHECK W_KBLE-RGJAHR = W_IFMBWACTOPIT_ISPS-FISCYEAR.
                  W_KBLE-WTABB = -1 * W_KBLE-WTABB.
                  CHECK W_KBLE-WTABB = W_IFMBWACTOPIT_ISPS-TRBTR.
                  APPEND W_KBLE TO T_KBLE.
                ENDSELECT. "kble
                CLEAR W_KBLE.
                LOOP AT T_KBLE INTO W_KBLE.
                  SELECT BUDAT
                        INTO W_PDATE
                        FROM BKPF
                        WHERE BUKRS = W_KBLE-RBUKRS
                          AND BELNR = W_KBLE-RBELNR
                          AND GJAHR = W_KBLE-RGJAHR.
                  ENDSELECT. "bkpf
                ENDLOOP. "t_kble
              ENDIF. "btart

*            when '040'. "PBC Pre-commitments
*              if w_IFMBWACTOPIT_ISPS-erlkz = 'X'. "completion flag
*                clear w_kble.
*                select single *
*                      into corresponding fields of w_kble
*                      from kble
*                      where belnr = w_IFMBWACTOPIT_ISPS-refbn
*                        and blpos = w_IFMBWACTOPIT_ISPS-rfpos.
*
*                select single bldat
*                      into w_pdate
*                      from kble
*                      where belnr = w_kble-rbelnr
*                        and blpos = w_kble-rbuzei.
*              endif. "erlkz

            WHEN '050'. "PBC Commitments
*              if w_IFMBWACTOPIT_ISPS-erlkz = 'X'. "completion flag
              CLEAR W_KBLP.
              SELECT SINGLE *
                    INTO W_KBLP
                    FROM KBLP
                    WHERE BELNR = W_IFMBWACTOPIT_ISPS-REFBN
                      AND BLPOS = W_IFMBWACTOPIT_ISPS-RFPOS.

              IF W_IFMBWACTOPIT_ISPS-BTART = '0200'.
                REFRESH T_KBLE.
                SELECT *
                      INTO TABLE T_KBLE
                      FROM KBLE
                      WHERE BELNR = W_IFMBWACTOPIT_ISPS-REFBN
                        AND BLPOS = W_IFMBWACTOPIT_ISPS-RFPOS.

                SORT T_KBLE BY ERDAT.
                CLEAR W_KBLE.
                READ TABLE T_KBLE INDEX 1 INTO W_KBLE.
                W_PDATE = W_KBLE-ERDAT.
              ENDIF.                                        "if 0200

              IF W_IFMBWACTOPIT_ISPS-BTART = '0500'.
                W_PDATE = W_KBLP-ERLDAT.
              ENDIF.                                        "if 0500

              IF W_PDATE IS INITIAL.
                W_PDATE = W_KBLP-AEDAT.
              ENDIF. "w_pdate is initial
*              endif. "erlkz

          ENDCASE. "actdetl


        WHEN '0150' OR '0300' OR '0350'.
          W_PDATE = W_IFMBWACTOPIT_ISPS-ZHLDT.

        WHEN '0100'.
          W_PDATE = W_IFMBWACTOPIT_ISPS-BUDAT.
********get PO creation date
          IF W_IFMBWACTOPIT_ISPS-ACTDETL = '090'. "PO
            CLEAR W_PO_CRDATE.
            SELECT SINGLE AEDAT INTO W_PO_CRDATE
                                FROM EKKO
                                WHERE EBELN = W_IFMBWACTOPIT_ISPS-REFBN.
            IF NOT ( W_PO_CRDATE IS INITIAL ).
              W_PDATE = W_PO_CRDATE.
            ENDIF.
          ENDIF. "actdetl = 090
*********PO creation date - end of insert


          IF W_IFMBWACTOPIT_ISPS-FKBTR < 0.
            CLEAR FMIOI.
            SELECT *
                  FROM FMIOI
                  WHERE REFBN = W_IFMBWACTOPIT_ISPS-REFBN
*                    and refbt = w_IFMBWACTOPIT_ISPS-refbt
                    AND RFORG = W_IFMBWACTOPIT_ISPS-RFORG
                    AND RFPOS = W_IFMBWACTOPIT_ISPS-RFPOS
                    AND RFKNT = W_IFMBWACTOPIT_ISPS-RFKNT
                    AND RFETE = W_IFMBWACTOPIT_ISPS-RFETE
                    AND RCOND = W_IFMBWACTOPIT_ISPS-RCOND
*                    and rftyp = w_IFMBWACTOPIT_ISPS-rftyp
                    AND RFSYS = W_IFMBWACTOPIT_ISPS-RFSYS
                    AND BTART = '0200'
*                    and rldnr = w_IFMBWACTOPIT_ISPS-rldnr
                    AND GJAHR = W_IFMBWACTOPIT_ISPS-FISCYEAR
                    AND STUNR = W_IFMBWACTOPIT_ISPS-STUNR.

**************  Begin Performance issue NME20240117
*              CLEAR fmifiit.
*              SELECT *
*                FROM fmifiit
*                WHERE fikrs  = fmioi-fikrs
*                  AND objnrz = fmioi-objnrz
*                  AND fonds  = fmioi-fonds
*                  AND vrefbt = fmioi-refbt
*                  AND vrefbn = fmioi-refbn
*                  AND vrforg = fmioi-rforg
*                  AND vrfpos = fmioi-rfpos
*                  AND vrfknt = fmioi-rfknt
*                  AND vrftyp = fmioi-rftyp.
*
*                CLEAR fmifihd.
*                SELECT SINGLE * FROM fmifihd
*                                WHERE fmbelnr = fmifiit-fmbelnr
*                                  AND fikrs = fmifiit-fikrs.
*
*                IF fmifihd-xrevs = 'X'. "check FM doc is not reversed
*                  CONTINUE.
*                ENDIF. "xrevs
*
*                CLEAR t_pdate.
*                MOVE-CORRESPONDING fmifiit TO t_pdate.
*                APPEND t_pdate. "collect actuals' dates and op.types
*
*              ENDSELECT. "fmifiit

              SELECT A~* FROM FMIFIIT AS A INNER JOIN FMIFIHD AS B ON  B~FMBELNR = A~FMBELNR
                                                                   AND B~FIKRS = A~FIKRS
                                WHERE A~FIKRS = @FMIOI-FIKRS
                                AND   A~OBJNRZ = @FMIOI-OBJNRZ
                                AND   A~FONDS = @FMIOI-FONDS
                                AND   A~VREFBT = @FMIOI-REFBT
                                AND   A~VREFBN = @FMIOI-REFBN
                                AND   A~VRFORG = @FMIOI-RFORG
                                AND   A~VRFPOS = @FMIOI-RFPOS
                                AND   A~VRFKNT = @FMIOI-RFKNT
                                AND   A~VRFTYP = @FMIOI-RFTYP
                                AND   B~XREVS = @SPACE
                                %_HINTS MSSQLNT '&REPARSE&'
                          APPENDING CORRESPONDING FIELDS OF TABLE @T_PDATE.
**************  End Performance issue NME20240117
            ENDSELECT. "fmioi


            CLEAR T_PDATE.
            SORT T_PDATE BY ZHLDT DESCENDING.
            CLEAR W_AMNT.
            W_AMNT = W_AMNT - W_IFMBWACTOPIT_ISPS-TRBTR.
            READ TABLE T_PDATE WITH KEY TRBTR = W_AMNT. "w_IFMBWACTOPIT_ISPS-trbtr.
            IF SY-SUBRC <> 0.
              CLEAR W_AMNT.
              W_AMNT = W_AMNT - W_IFMBWACTOPIT_ISPS-FKBTR.
              READ TABLE T_PDATE WITH KEY FKBTR = W_AMNT. "w_IFMBWACTOPIT_ISPS-fkbtr.
            ENDIF.
            IF SY-SUBRC <> 0.
              READ TABLE T_PDATE INDEX 1.
            ENDIF. "sy-subrc
            W_PDATE = T_PDATE-ZHLDT.
          ENDIF. "fkbtr < 0

        WHEN OTHERS.
          W_PDATE = W_IFMBWACTOPIT_ISPS-BUDAT.
      ENDCASE.

      IF W_PDATE IS INITIAL.
        W_PDATE = W_IFMBWACTOPIT_ISPS-BUDAT.
      ENDIF.

      IF W_IFMBWACTOPIT_ISPS-ZHLDT > W_PDATE.
        W_PDATE = W_IFMBWACTOPIT_ISPS-ZHLDT.
      ENDIF.

      W_IFMBWACTOPIT_ISPS-ZZPOST_DATE = W_PDATE.

********delivery date
      CLEAR W_EINDT.
      IF W_IFMBWACTOPIT_ISPS-ACTDETL = '080' OR "PR
         W_IFMBWACTOPIT_ISPS-ACTDETL = '090'.   "PO
        SELECT SINGLE EINDT INTO W_EINDT
              FROM EKET
              WHERE EBELN = W_IFMBWACTOPIT_ISPS-REFBN
                AND EBELP = W_IFMBWACTOPIT_ISPS-RFPOS
                AND ETENR = W_IFMBWACTOPIT_ISPS-RFETE.
      ENDIF. "w_IFMBWACTOPIT_ISPS-actdetl for PO/PR


      IF W_IFMBWACTOPIT_ISPS-ACTDETL = '030'. "PR
        CLEAR W_XBLNR.
        SELECT SINGLE XBLNR
              INTO W_XBLNR
              FROM KBLK
              WHERE BELNR = W_IFMBWACTOPIT_ISPS-REFBN.
        CONDENSE W_XBLNR NO-GAPS.
        W_EINDT(4) = W_XBLNR+6(4).
        W_EINDT+4(2) = W_XBLNR+3(2).
        W_EINDT+6(2) = W_XBLNR(2).

        CALL FUNCTION 'DATE_CHECK_PLAUSIBILITY'
          EXPORTING
            DATE                            = W_EINDT
          EXCEPTIONS
            PLAUSIBILITY_CHECK_FAILED       = 1
            OTHERS                          = 2.

        IF SY-SUBRC <> 0 OR W_EINDT < '20000101'.
          CLEAR W_EINDT.
        ENDIF.

      ENDIF. "FR


      IF W_EINDT IS INITIAL.
        W_EINDT = W_PDATE.
      ENDIF. "w_eindt
      W_IFMBWACTOPIT_ISPS-ZZDELIV_DATE = W_EINDT.

*      replace all occurrences of regex '[[:cntrl:]]' in w_IFMBWACTFIIT-sgtxt with '_'.
      MODIFY C_T_DATA FROM W_IFMBWACTOPIT_ISPS.
    ENDLOOP. "c_t_data
*****end of 0PU_IS_PS_31



*****
*****0CO_OM_WBS_8
*****
  WHEN '0CO_OM_WBS_8'.
    CLEAR W_ICWBSBUD1.
    LOOP AT C_T_DATA INTO W_ICWBSBUD1.
      CLEAR W_BPEJ.
      SELECT SINGLE *
            INTO W_BPEJ
            FROM BPEJ
            WHERE BELNR = W_ICWBSBUD1-BELNR
              AND BUZEI = W_ICWBSBUD1-BUZEI.
      W_ICWBSBUD1-ZZVORGA = W_BPEJ-VORGA. "Budget operation for WBS allotments
      W_ICWBSBUD1-ZZWLJHR = W_ICWBSBUD1-SWG. "Copy total allotment per WBS-element
      W_ICWBSBUD1-SWG = W_BPEJ-WLJHR - W_BPEJ-WLJHV. "Non-distributed allotment only

*      get parent WBS-element
*      clear w_prps. "get internal number for current WBS-element
*      select single *
*                   into w_prps
*                   from prps
*                   where posid = w_ICWBSBUD1-posid
*                     and pkokr = w_ICWBSBUD1-kokrs.

      CLEAR W_PRHI. "get hierarchy neighbours for WBS-element
      SELECT SINGLE *
                   INTO W_PRHI
                   FROM PRHI
                   WHERE POSNR = W_BPEJ-OBJNR+2(8). "w_prps-pspnr.

      CLEAR W_PRPS. "get parent WBS-element
      SELECT SINGLE *
                   INTO W_PRPS
                   FROM PRPS
                   WHERE PSPNR = W_PRHI-UP.

      W_ICWBSBUD1-ZZPARENT_WBS = W_PRPS-POSID.

      MODIFY C_T_DATA FROM W_ICWBSBUD1.
    ENDLOOP. "c_t_data
*****end of 0CO_OM_WBS_8



*****
*****0FI_AR_4
*****
  WHEN '0FI_AR_4'.
    CLEAR W_DTFIAR_3.
    LOOP AT C_T_DATA INTO W_DTFIAR_3.
      SELECT SINGLE GSBER INTO W_DTFIAR_3-ZZGSBER
                          FROM BSEG
                          WHERE BUKRS = W_DTFIAR_3-BUKRS
                            AND BELNR = W_DTFIAR_3-BELNR
                            AND GJAHR = W_DTFIAR_3-FISCPER(4)
                            AND BUZEI = W_DTFIAR_3-BUZEI.

      MODIFY C_T_DATA FROM W_DTFIAR_3.
    ENDLOOP. "c_t_data
*****end of 0FI_AR_4


  WHEN OTHERS.
ENDCASE. "i_datasource