* ==== CLASS POOL YCL_FI_TO_PAYROLL_POSTING_BL ====
CLASS-POOL .
*"* class pool for class YCL_FI_TO_PAYROLL_POSTING_BL

*"* local type definitions
INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CCDEF.

*"* class YCL_FI_TO_PAYROLL_POSTING_BL definition
*"* public declarations
  INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CU.
*"* protected declarations
  INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CO.
*"* private declarations
  INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CI.
ENDCLASS. "YCL_FI_TO_PAYROLL_POSTING_BL definition

*"* macro definitions
INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CCMAC.
*"* local class implementation
INCLUDE YCL_FI_TO_PAYROLL_POSTING_BL==CCIMP.

CLASS YCL_FI_TO_PAYROLL_POSTING_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_TO_PAYROLL_POSTING_BL implementation


* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_PPOIX,
      PERNR   TYPE PPOIX-PERNR,
      SEQNO   TYPE PPOIX-SEQNO,
      ACTSIGN TYPE PPOIX-ACTSIGN,
      RUNID   TYPE PPOIX-RUNID,
      POSTNUM TYPE PPOIX-POSTNUM,
      RTLINE  TYPE PPOIX-RTLINE,
      WPBPREF TYPE PPOIX-WPBPREF,
      C0REF   TYPE PPOIX-C0REF,
      TSLIN   TYPE PPOIX-TSLIN,
      LGART   TYPE PPOIX-LGART,
      BETRG   TYPE PPOIX-BETRG,
      WAERS   TYPE PPOIX-WAERS,
      DOCNUM  TYPE PPDIX-DOCNUM,
      DOCLIN  TYPE PPDIX-DOCLIN,
    END OF TY_PPOIX .
  TYPES:
    BEGIN OF TY_DISTRIB_WT,
      PERNR   TYPE P_PERNR,
      SEQNO   TYPE PPOIX-SEQNO,
      ACTSIGN TYPE PPOIX-ACTSIGN,
      RUNID   TYPE PPOIX-RUNID,
      LGART_O TYPE PPOIX-LGART,
      BETRG_O TYPE PPOIX-BETRG,
      WAERS_O TYPE WAERS,
    END OF TY_DISTRIB_WT .
  TYPES:
    BEGIN OF TY_DISTRIB.
      INCLUDE TYPE TY_DISTRIB_WT.
      TYPES: RTLINE_O TYPE PPOIX-RTLINE,
      LGART_9  TYPE PPOIX-LGART,
      BETRG_9  TYPE PPOIX-BETRG,
      WAERS_9  TYPE WAERS,
      REDUC    TYPE CHAR1,
      SEQNO_P  TYPE PPOIX-SEQNO,
      RUNID_A  TYPE PPOIX-RUNID,
      FIPOS    TYPE BSEG-FIPOS,
      C0       TYPE HRPAY99_C0,
    END OF TY_DISTRIB .
  TYPES:
    TTY_DISTRIB TYPE TABLE OF TY_DISTRIB .
  TYPES:
    BEGIN OF TY_T512W,
      LGART TYPE T512W-LGART,
      ENDDA TYPE T512W-ENDDA,
      BEGDA TYPE T512W-BEGDA,
      PZALA TYPE T512W-PZALA,
      FZALA TYPE T512W-FZALA,
    END OF TY_T512W .
  TYPES:
    TTY_LGART_RANGE TYPE RANGE OF LGART .
  TYPES:
    BEGIN OF TY_PERNR_CHECK,
      PERNR TYPE P_PERNR,
      DIFF  TYPE MAXBT,
    END OF TY_PERNR_CHECK .
  TYPES:
    BEGIN OF TY_CUMUL_WT,
      LGART TYPE PPOIX-LGART,
      BETRG TYPE WERTV9,
    END OF TY_CUMUL_WT .
  TYPES:
    TTY_APZNR_RANGE TYPE RANGE OF APZNR .
  TYPES:
    TTY_C1ZNR_RANGE TYPE RANGE OF C1ZNO .

  CLASS-DATA MT_APZNR_A TYPE TTY_APZNR_RANGE .
  CLASS-DATA MT_APZNR_P TYPE TTY_APZNR_RANGE .
  CLASS-DATA MT_C1ZNR_A TYPE TTY_C1ZNR_RANGE .
  CLASS-DATA MT_C1ZNR_P TYPE TTY_C1ZNR_RANGE .
  CLASS-DATA MV_FIKRS TYPE FIKRS .
  CLASS-DATA MV_BUKRS TYPE BUKRS .
  CLASS-DATA MV_FUNDTYPE TYPE FM_FUNDTYPE .
  CLASS-DATA MV_GEBER TYPE BP_GEBER .
  CLASS-DATA MT_PERNR_DEBUG TYPE YTTHR_PERNR_RANGE .
  CLASS-DATA MV_MODE_DEBUG TYPE XFELD .
  CLASS-DATA MT_PAY_RESULT TYPE ZHRPAYUN_T_PAY_RESULTS .
  CLASS-DATA MV_ABKRS TYPE ABKRS .
  CLASS-DATA MV_PERMO TYPE PERMO .
  CLASS-DATA MV_INPER TYPE IPERI .
  CLASS-DATA MV_RUNID TYPE P_EVNUM .
  CLASS-DATA:
    MT_PPDIT_PPDIX TYPE TABLE OF TY_PPDIT_PPDIX .
  CLASS-DATA:
    MT_PPOIX TYPE SORTED TABLE OF TY_PPOIX WITH UNIQUE KEY PERNR SEQNO ACTSIGN RUNID POSTNUM .
  CLASS-DATA:
    MT_DISTRIB TYPE TABLE OF TY_DISTRIB .
  CLASS-DATA:
    MT_T512W TYPE SORTED TABLE OF TY_T512W WITH UNIQUE KEY LGART ENDDA .
  CLASS-DATA:
    MT_DISTRIB_WT TYPE SORTED TABLE OF TY_DISTRIB_WT WITH UNIQUE KEY PERNR SEQNO ACTSIGN RUNID LGART_O .
  CLASS-DATA:
    MT_PERNR_CHECK TYPE TABLE OF TY_PERNR_CHECK .
  CLASS-DATA:
    MT_CUMUL_WT TYPE TABLE OF TY_CUMUL_WT .

  CLASS-METHODS GET_FUND_TYPE
    IMPORTING
      !IV_BUKRS TYPE BUKRS
      !IV_GEBER TYPE BP_GEBER
    RETURNING
      VALUE(RV_FUNDTYPE) TYPE FM_FUNDTYPE .
  CLASS-METHODS GET_FX_COST_POINTERS
    IMPORTING
      !IT_C0 TYPE HRPAY99_C0
      !IT_C1 TYPE HRPAY99_C1
    EXPORTING
      !ET_APZNR TYPE TTY_APZNR_RANGE
      !ET_C1ZNR TYPE TTY_C1ZNR_RANGE .
  CLASS-METHODS __FOR_DEBUG_ANALYZE
    IMPORTING
      !IV_PERNR TYPE P_PERNR
      !IV_AMOUNT TYPE MAXBT .
  CLASS-METHODS PREPARE_DOC_LINES
    EXPORTING
      !ET_DOC_LINES TYPE TTY_DOC_LINES .
  CLASS-METHODS CALCULATE_DISTRIBUTION
    IMPORTING
      !IS_RT_9 TYPE PC207
      !IT_RT TYPE HRPAY99_RT
      !IT_C0 TYPE HRPAY99_C0
      !IV_PERNR TYPE P_PERNR
      !IV_SEQNO TYPE CDSEQ
      !IV_ACTSIGN TYPE SRTZA
      !IV_RUNID TYPE P_EVNUM
      !IV_WAERS TYPE WAERS
      !IV_DATE TYPE DATUM
      !IV_SEQNO_P TYPE CDSEQ
      !IV_RUNID_A TYPE P_EVNUM OPTIONAL
      !IV_FIPOS TYPE FIPOS OPTIONAL
      !IT_APZNR TYPE TTY_APZNR_RANGE OPTIONAL
      !IT_C1ZNR TYPE TTY_C1ZNR_RANGE OPTIONAL
    EXPORTING
      !ET_DISTRIB TYPE TTY_DISTRIB .
  CLASS-METHODS PRORATE_DISTRIBUTION_BR_AMOUNT .
  CLASS-METHODS PUT_TO_CUMUL_DISTRIB
    IMPORTING
      !IT_DISTRIB TYPE TTY_DISTRIB
      !IV_SUBTRACT TYPE XFELD DEFAULT ABAP_FALSE .
  CLASS-METHODS GET_PAYROLL_IN_PERIOD
    IMPORTING
      !IV_RUNID TYPE P_EVNUM
    RETURNING
      VALUE(RV_INPER) TYPE IPERI .
  CLASS-METHODS GET_PAYROLL_RESULT
    IMPORTING
      !IV_PERNR TYPE P_PERNR
      !IV_RUNID TYPE P_EVNUM
    EXPORTING
      !ET_RESULT TYPE ZHRPAYUN_T_PAY_RESULTS
      !EV_INPER TYPE IPERI .
  CLASS-METHODS GET_PERMO
    IMPORTING
      !IV_ABKRS TYPE ABKRS
    RETURNING
      VALUE(RV_PERMO) TYPE PERMO .
  CLASS-METHODS SET_DISTRIBUTION_BR_AMOUNTS .
  CLASS-METHODS GET_LGART_RANGE
    IMPORTING
      !IV_DATE TYPE DATUM
    EXPORTING
      !ET_LGART TYPE TTY_LGART_RANGE .
  CLASS-METHODS GET_PZALA_RANGE
    IMPORTING
      !IV_DATE TYPE DATUM
    EXPORTING
      !ET_LGART TYPE TTY_LGART_RANGE .
  CLASS-METHODS READ_PPOIX_FROM_FI_TO_HR .
  CLASS-METHODS READ_PPOIX_FROM_HR_TO_FI .

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM001 ----
  METHOD CALCULATE_DISTRIBUTION.

    TYPES: BEGIN OF LTY_LGART_O_VENTIL,
             LGART_O  TYPE PPOIX-LGART,
             BETRG_O  TYPE PPOIX-BETRG,
             WAERS_O  TYPE WAERS,
             RTLINE_O TYPE PPOIX-RTLINE,
           END OF LTY_LGART_O_VENTIL.

    DATA LS_DISTRIB TYPE TY_DISTRIB.
    DATA LT_LGART_O_VENTIL TYPE TABLE OF LTY_LGART_O_VENTIL.
    DATA LS_LGART_O_VENTIL TYPE LTY_LGART_O_VENTIL.
    DATA LV_BETRG_TOTAL TYPE MAXBT.
    DATA LV_BETRG_CUMUL TYPE MAXBT.
    DATA LV_FIRST TYPE XFELD.
    DATA LV_LAST TYPE XFELD.

    CLEAR ET_DISTRIB.

    LS_DISTRIB-PERNR = IV_PERNR.
    LS_DISTRIB-SEQNO = IV_SEQNO.
    LS_DISTRIB-ACTSIGN = IV_ACTSIGN.
    LS_DISTRIB-RUNID = IV_RUNID.
    LS_DISTRIB-SEQNO_P = IV_SEQNO_P.
    LS_DISTRIB-LGART_9 = IS_RT_9-LGART.
    LS_DISTRIB-BETRG_9 = IS_RT_9-BETRG.
    LS_DISTRIB-RUNID_A = IV_RUNID_A.
    LS_DISTRIB-FIPOS = IV_FIPOS.
    LS_DISTRIB-C0 = IT_C0.

    "Get wage wage type corresponding to PZALA wage type
    CLEAR: LT_LGART_O_VENTIL, LV_BETRG_TOTAL, LV_BETRG_CUMUL, LV_FIRST, LV_LAST.
    LOOP AT MT_T512W INTO DATA(LS_T512W) WHERE PZALA = IS_RT_9-LGART
                                         AND   ENDDA >= IV_DATE
                                         AND   BEGDA <= IV_DATE.
      LOOP AT IT_RT INTO DATA(LS_RT) WHERE ABART = IS_RT_9-ABART
                                     AND   LGART = LS_T512W-LGART
                                     AND   APZNR = IS_RT_9-APZNR
                                     AND   C1ZNR = IS_RT_9-C1ZNR.
        LS_LGART_O_VENTIL-RTLINE_O = SY-TABIX.
        "Check wage type fill the Fixed rate condition
*        IF ls_rt-c1znr IS NOT INITIAL AND ls_rt-c1znr NOT IN it_c1znr.
*          CONTINUE.
*        ELSEIF ls_rt-apznr IS NOT INITIAL AND ls_rt-apznr NOT IN it_apznr.
*          CONTINUE.
*        ENDIF.
        LS_LGART_O_VENTIL-LGART_O = LS_RT-LGART.
        LS_LGART_O_VENTIL-BETRG_O = LS_RT-BETRG.
        LS_LGART_O_VENTIL-WAERS_O = IV_WAERS.
        APPEND LS_LGART_O_VENTIL TO LT_LGART_O_VENTIL.
        ADD LS_RT-BETRG TO LV_BETRG_TOTAL.
      ENDLOOP.
    ENDLOOP.

    CHECK LV_BETRG_TOTAL IS NOT INITIAL.

    "Ventilate BR amount
    LOOP AT LT_LGART_O_VENTIL INTO LS_LGART_O_VENTIL.
      AT FIRST.
        LV_FIRST = ABAP_TRUE.
      ENDAT.
      AT LAST.
        LV_LAST = ABAP_TRUE.
      ENDAT.
      LS_DISTRIB-LGART_9 = IS_RT_9-LGART.
      LS_DISTRIB-WAERS_9 = IV_WAERS.
      MOVE-CORRESPONDING LS_LGART_O_VENTIL TO LS_DISTRIB.
      IF LV_FIRST = ABAP_TRUE AND LV_LAST = ABAP_TRUE.
        LS_DISTRIB-BETRG_9 = IS_RT_9-BETRG.
      ELSEIF LV_LAST = ABAP_FALSE.
        LS_DISTRIB-BETRG_9 = LS_LGART_O_VENTIL-BETRG_O * IS_RT_9-BETRG / LV_BETRG_TOTAL.
        ADD LS_DISTRIB-BETRG_9 TO LV_BETRG_CUMUL.
      ELSE.
        LS_DISTRIB-BETRG_9 = IS_RT_9-BETRG - LV_BETRG_CUMUL.   "to avoid rouding gap.
      ENDIF.
      APPEND LS_DISTRIB TO ET_DISTRIB.
      CLEAR: LV_FIRST, LV_LAST.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM002 ----
  METHOD CLASS_CONSTRUCTOR.

    SELECT LGART, ENDDA, BEGDA, PZALA, FZALA FROM T512W WHERE MOLGA = 'UN'
                                                        AND   ENDDA >= '20240101'
                                                        AND   FZALA = '999S'
                                             INTO TABLE @MT_T512W.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM003 ----
  METHOD GET_LGART_RANGE.

    CLEAR ET_LGART.

    LOOP AT MT_T512W INTO DATA(LS_T512W) WHERE ENDDA >= IV_DATE
                                         AND   BEGDA <= IV_DATE.
      APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = LS_T512W-LGART ) TO ET_LGART.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM004 ----
  METHOD GET_PAYROLL_IN_PERIOD.

    DATA LV_DUMMY TYPE STRING.

    IF IV_RUNID <> MV_RUNID.
      SELECT SINGLE VALUE FROM PEVAT WHERE TYPE = 'PP'
                                     AND   RUNID = @IV_RUNID
                                     AND   ATTR = 'AKPER'
                                     AND   ID = 0
                          INTO @DATA(LV_VALUE).
      IF SY-SUBRC = 0.
        SPLIT LV_VALUE AT '/' INTO LV_DUMMY MV_INPER+4(2) MV_INPER(4).
      ENDIF.
      MV_RUNID = IV_RUNID.
    ENDIF.

    RV_INPER = MV_INPER.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM005 ----
  METHOD GET_PAYROLL_RESULT.

    DATA LT_RGDIR TYPE TABLE OF PC261.
    DATA LT_EVAL TYPE PAY_T_EVAL_PERIOD.
    DATA LV_ABKRS TYPE ABKRS.
    DATA LS_PAY_RESULT TYPE PAYUN_RESULT.

    IF IV_RUNID <> MV_RUNID.
      CLEAR MT_PAY_RESULT.
      "Get IN period fromRUNID
      SELECT SINGLE VALUE FROM PEVAT WHERE TYPE = 'PP'
                                     AND   RUNID = @IV_RUNID
                                     AND   ATTR = 'AKPER'
                                     AND   ID = 0
                          INTO @DATA(LV_VALUE).
      IF SY-SUBRC = 0.
        SPLIT LV_VALUE AT '/' INTO LV_ABKRS MV_INPER+4(2) MV_INPER(4).
      ENDIF.

      """""Get payroll result for IN-PERIOD
      "Get payroll directory for Personel number
      CALL FUNCTION 'CU_READ_RGDIR'
        EXPORTING
          PERSNR             = IV_PERNR
          NO_AUTHORITY_CHECK = ABAP_TRUE
        TABLES
          IN_RGDIR           = LT_RGDIR
        EXCEPTIONS
          NO_RECORD_FOUND    = 1
          OTHERS             = 2.

      "Get 'A' for In-period
      LT_EVAL = CL_HR_CD_MANAGER=>EVAL_PERIODS( IMP_INPTY      = SPACE
                                                IMP_INPER      = MV_INPER
                                                IMP_IPERM      = GET_PERMO( LV_ABKRS )
                                                IMP_BONDT      = '00000000'
                                                IMP_INPID      = ABAP_FALSE
                                                IMP_RGDIR      = LT_RGDIR
                                                IMP_ALL_OF_RUN = ABAP_TRUE ).

      LOOP AT LT_EVAL INTO DATA(LS_EVAL).
        LOOP AT LS_EVAL-EVP INTO DATA(LS_EVP).
          "Get payroll result
          LS_PAY_RESULT = YCL_HR_READ_PAYROLL_RESULT=>GET_RESULT_FOR_PERNR_SEQNO( IV_PERNR = IV_PERNR
                                                                                  IV_SEQNO = LS_EVP-SEQNR ).
          LS_PAY_RESULT-EVP = LS_EVP.
          APPEND LS_PAY_RESULT TO MT_PAY_RESULT.
        ENDLOOP.
      ENDLOOP.

      MV_RUNID = IV_RUNID.

    ENDIF.

    ET_RESULT = MT_PAY_RESULT.
    EV_INPER = MV_INPER.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM006 ----
  METHOD GET_PERMO.

    IF IV_ABKRS <> MV_ABKRS.
      SELECT SINGLE PERMO FROM T549A WHERE ABKRS = @IV_ABKRS INTO @MV_PERMO.
      MV_ABKRS = IV_ABKRS.
    ENDIF.

    RV_PERMO = MV_PERMO.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM007 ----
  METHOD GET_PZALA_RANGE.

    CLEAR ET_LGART.

    LOOP AT MT_T512W INTO DATA(LS_T512W) WHERE ENDDA >= IV_DATE
                                         AND   BEGDA <= IV_DATE.
      APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = LS_T512W-PZALA ) TO ET_LGART.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM008 ----
  METHOD PREPARE_DOC_LINES.

    DATA LS_DOC_LINES TYPE TY_DOC_LINES.
    DATA LV_BETRG_O TYPE MAXBT.
    DATA LV_BETRG_9 TYPE MAXBT.

    CLEAR ET_DOC_LINES.

    LOOP AT MT_DISTRIB INTO DATA(LS_DISTRIB).
      "Get ppoix document

      LOOP AT MT_PPOIX INTO DATA(LS_PPOIX) WHERE PERNR = LS_DISTRIB-PERNR
                                           AND   SEQNO = LS_DISTRIB-SEQNO
                                           AND   ACTSIGN = LS_DISTRIB-ACTSIGN
                                           AND   RUNID = LS_DISTRIB-RUNID
                                           AND   RTLINE = LS_DISTRIB-RTLINE_O.

        IF LS_DISTRIB-SEQNO = LS_DISTRIB-SEQNO_P.   "Case of wage type only exists in Previous and not in actual.
          SELECT SINGLE TSLIN FROM PPOPX WHERE PERNR = @LS_PPOIX-PERNR
                                         AND   SEQNO = @LS_PPOIX-SEQNO
                                         AND   RUNID = @LS_DISTRIB-RUNID_A
                                         AND   POSTNUM = @LS_PPOIX-POSTNUM
                              INTO @DATA(LV_TSLIN).
          IF SY-SUBRC = 0.
            SELECT SINGLE DOCNUM, DOCLIN FROM PPDIX WHERE EVTYP = 'PP'
                                                    AND   RUNID = @LS_DISTRIB-RUNID_A
                                                    AND   LINUM = @LV_TSLIN
                                         INTO ( @LS_PPOIX-DOCNUM, @LS_PPOIX-DOCLIN ).
          ENDIF.
        ENDIF.

        CHECK LS_PPOIX-DOCNUM IS NOT INITIAL.

        "Prorate amount with cost %
        READ TABLE LS_DISTRIB-C0 INTO DATA(LS_C0) WITH KEY APZNR = LS_PPOIX-WPBPREF
                                                           SEQNO = LS_PPOIX-C0REF.
        IF SY-SUBRC = 0 AND LS_C0-KPRNN <> 100.
          LV_BETRG_O = LS_DISTRIB-BETRG_O * LS_C0-KPRNN / 100.
          LV_BETRG_9 = LS_DISTRIB-BETRG_9 * LS_C0-KPRNN / 100.
        ELSE.
          LV_BETRG_O = LS_DISTRIB-BETRG_O.
          LV_BETRG_9 = LS_DISTRIB-BETRG_9.
        ENDIF.

        READ TABLE ET_DOC_LINES ASSIGNING FIELD-SYMBOL(<LS_DOC_LINES>) WITH KEY DOCNUM = LS_PPOIX-DOCNUM
                                                                                DOCLIN = LS_PPOIX-DOCLIN.
        IF SY-SUBRC = 0.
          ADD LV_BETRG_O TO <LS_DOC_LINES>-BETRG_O.
          ADD LV_BETRG_9 TO <LS_DOC_LINES>-BETRG_9.
          IF LS_DISTRIB-REDUC IS NOT INITIAL.
            <LS_DOC_LINES>-REDUC = LS_DISTRIB-REDUC.
          ENDIF.
        ELSE.
          MOVE-CORRESPONDING LS_DISTRIB TO LS_DOC_LINES.
          LS_DOC_LINES-BETRG_O = LV_BETRG_O.
          LS_DOC_LINES-BETRG_9 = LV_BETRG_9.
          LS_DOC_LINES-DOCNUM = LS_PPOIX-DOCNUM.
          LS_DOC_LINES-DOCLIN = LS_PPOIX-DOCLIN.
          INSERT LS_DOC_LINES INTO TABLE ET_DOC_LINES.
        ENDIF.
      ENDLOOP.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM009 ----
  METHOD PRORATE_DISTRIBUTION_BR_AMOUNT.

    DATA LV_NEW_SEQNO TYPE XFELD.
    DATA LT_PPOPX TYPE TABLE OF PPOPX.
    DATA LV_RUNID_P TYPE PCALAC-RUNID.
    DATA LT_PPOIX TYPE TABLE OF PPOIX.
    DATA LV_BETRG_P TYPE PPOIX-BETRG.
    DATA LV_ECART TYPE P DECIMALS 5.

    "Process lines with retroactivity of MT_DISTRIB to prorate the BR impact
    SORT MT_DISTRIB.
    LOOP AT MT_DISTRIB ASSIGNING FIELD-SYMBOL(<LS_DISTRIB>).
      CLEAR: LV_NEW_SEQNO.
      AT NEW SEQNO.
        LV_NEW_SEQNO = ABAP_TRUE.
      ENDAT.

      CHECK <LS_DISTRIB>-SEQNO_P IS NOT INITIAL.  "Only retroactivity

      READ TABLE MT_DISTRIB_WT INTO DATA(LS_DISTRIB_WT) WITH KEY PERNR = <LS_DISTRIB>-PERNR
                                                                 SEQNO = <LS_DISTRIB>-SEQNO
                                                                 ACTSIGN = <LS_DISTRIB>-ACTSIGN
                                                                 RUNID = <LS_DISTRIB>-RUNID
                                                                 LGART_O = <LS_DISTRIB>-LGART_O.
      CHECK SY-SUBRC = 0.

      IF LV_NEW_SEQNO = ABAP_TRUE.
        CLEAR: LT_PPOPX, LV_RUNID_P.
        "Get PPOPX corresponding entries
        SELECT * FROM PPOPX WHERE PERNR = @<LS_DISTRIB>-PERNR
                            AND   SEQNO = @<LS_DISTRIB>-SEQNO_P
                            AND   RUNID = @<LS_DISTRIB>-RUNID
                      INTO TABLE @LT_PPOPX.
        "Get the Runid retro
        SELECT SINGLE RUNID INTO @LV_RUNID_P FROM PCALAC WHERE PERNR = @<LS_DISTRIB>-PERNR
                                                         AND   SEQNO = @<LS_DISTRIB>-SEQNO_P
                                                         AND   TYPE = 'PP'
                                                         AND   SRTZA = 'A'.
        "Get the PPOIX corresponding lines
        SELECT * FROM PPOIX WHERE PERNR = @<LS_DISTRIB>-PERNR
                            AND   SEQNO = @<LS_DISTRIB>-SEQNO_P
                            AND   ACTSIGN = @<LS_DISTRIB>-ACTSIGN
                            AND   RUNID = @LV_RUNID_P
                 INTO TABLE @LT_PPOIX.
      ENDIF.

      "Get PPOIX corresponding line
      READ TABLE MT_PPOIX INTO DATA(LS_PPOIX_A) WITH KEY PERNR = <LS_DISTRIB>-PERNR
                                                         SEQNO = <LS_DISTRIB>-SEQNO
                                                         ACTSIGN = <LS_DISTRIB>-ACTSIGN
                                                         RUNID = <LS_DISTRIB>-RUNID
                                                         RTLINE = <LS_DISTRIB>-RTLINE_O
                                                         BETRG = <LS_DISTRIB>-BETRG_O.
      IF SY-SUBRC = 0 AND LS_PPOIX_A-TSLIN IS NOT INITIAL.
        "Get the entries in PPOPX
        CLEAR LV_BETRG_P.
        LOOP AT LT_PPOPX INTO DATA(LS_PPOPX) WHERE PERNR = <LS_DISTRIB>-PERNR
                                             AND   SEQNO = <LS_DISTRIB>-SEQNO_P
                                             AND   RUNID = <LS_DISTRIB>-RUNID
                                             AND   TSLIN = LS_PPOIX_A-TSLIN.
          READ TABLE LT_PPOIX INTO DATA(LS_PPOIX_P) WITH KEY POSTNUM = LS_PPOPX-POSTNUM
                                                             LGART = LS_PPOIX_A-LGART.
          CHECK SY-SUBRC = 0.
          ADD LS_PPOIX_P-BETRG TO LV_BETRG_P.
        ENDLOOP.
        "Calculate the prorata for BR amount
        LV_ECART = 1 - ( LV_BETRG_P / LS_DISTRIB_WT-BETRG_O ).
        "Identify if it is an amount reduction
        IF LV_BETRG_P > LS_DISTRIB_WT-BETRG_O.
          <LS_DISTRIB>-REDUC = 'R'.    "The Previous amount is higher than the Actual amount => Reduction
        ENDIF.
        "Adjust the BR amount
        <LS_DISTRIB>-BETRG_9 = <LS_DISTRIB>-BETRG_9 * LV_ECART.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00A ----
  METHOD PUT_TO_CUMUL_DISTRIB.

    DATA LS_DISTRIB_WT TYPE TY_DISTRIB_WT.
    DATA LS_CUMUL_WT TYPE TY_CUMUL_WT.

    LOOP AT IT_DISTRIB INTO DATA(LS_DISTRIB).

      READ TABLE MT_DISTRIB_WT ASSIGNING FIELD-SYMBOL(<LS_DISTRIB_WT>) WITH KEY PERNR = LS_DISTRIB-PERNR
                                                                                SEQNO = LS_DISTRIB-SEQNO
                                                                                ACTSIGN = LS_DISTRIB-ACTSIGN
                                                                                RUNID = LS_DISTRIB-RUNID
                                                                                LGART_O = LS_DISTRIB-LGART_O.
      IF SY-SUBRC = 0.
        ADD LS_DISTRIB-BETRG_O TO <LS_DISTRIB_WT>-BETRG_O.
      ELSE.
        MOVE-CORRESPONDING LS_DISTRIB TO LS_DISTRIB_WT.
        INSERT LS_DISTRIB_WT INTO TABLE MT_DISTRIB_WT.
      ENDIF.

      READ TABLE MT_CUMUL_WT ASSIGNING FIELD-SYMBOL(<LS_CUMUL_WT>) WITH KEY LGART = LS_DISTRIB-LGART_O.
      IF SY-SUBRC = 0.
        IF IV_SUBTRACT = ABAP_TRUE.
          SUBTRACT LS_DISTRIB-BETRG_O FROM <LS_CUMUL_WT>-BETRG.
        ELSE.
          ADD LS_DISTRIB-BETRG_O TO <LS_CUMUL_WT>-BETRG.
        ENDIF.
      ELSE.
        LS_CUMUL_WT-LGART = LS_DISTRIB-LGART_O.
        LS_CUMUL_WT-BETRG = LS_DISTRIB-BETRG_O.
        IF IV_SUBTRACT = ABAP_TRUE.
          MULTIPLY LS_CUMUL_WT-BETRG BY -1.
        ENDIF.
        APPEND LS_CUMUL_WT TO MT_CUMUL_WT.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00B ----
  METHOD READ_PPOIX_FROM_FI_TO_HR.

    CLEAR MT_PPOIX.

    SELECT PERNR, SEQNO, ACTSIGN, RUNID, POSTNUM, RTLINE, WPBPREF, C0REF, TSLIN, LGART, BETRG, WAERS
           FROM PPOIX
           FOR ALL ENTRIES IN @MT_PPDIT_PPDIX
           WHERE PERNR = @MT_PPDIT_PPDIX-PERNR
           AND   ACTSIGN = 'A'
           AND   RUNID = @MT_PPDIT_PPDIX-RUNID
           AND   TSLIN = @MT_PPDIT_PPDIX-LINUM
           INTO CORRESPONDING FIELDS OF TABLE @MT_PPOIX.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00C ----
  METHOD READ_PPOIX_FROM_HR_TO_FI.

    CLEAR MT_PPOIX.

    SELECT O~PERNR, O~SEQNO, O~ACTSIGN, O~RUNID, O~POSTNUM, O~RTLINE, O~WPBPREF, O~C0REF, O~TSLIN, O~LGART, O~BETRG, O~WAERS, D~DOCNUM, D~DOCLIN
           FROM PPOIX AS O
           LEFT OUTER JOIN PPDIX AS D ON  D~EVTYP = 'PP'
                                      AND D~RUNID = O~RUNID
                                      AND D~LINUM = O~TSLIN
           FOR ALL ENTRIES IN @MT_DISTRIB
           WHERE O~PERNR = @MT_DISTRIB-PERNR
           AND   O~SEQNO = @MT_DISTRIB-SEQNO
           AND   O~ACTSIGN = @MT_DISTRIB-ACTSIGN
           AND   O~RUNID = @MT_DISTRIB-RUNID
           AND   O~RTLINE = @MT_DISTRIB-RTLINE_O
           INTO TABLE @MT_PPOIX.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00D ----
  METHOD SET_DISTRIBUTION_BR_AMOUNTS.

    TYPES: BEGIN OF LTY_999S,
             ABART TYPE PC207-ABART,
             LGART TYPE PC207-LGART,
             APZNR TYPE PC207-APZNR,
           END OF LTY_999S.

    DATA LS_PAY_RESULT TYPE PAYUN_RESULT.
    DATA LS_PAY_RESULT_P TYPE PAYUN_RESULT.
    DATA LT_PAY_RESULT TYPE ZHRPAYUN_T_PAY_RESULTS.
    DATA LT_999S TYPE TABLE OF LTY_999S.
    DATA LS_999S TYPE LTY_999S.
    DATA LT_PZALA TYPE TTY_LGART_RANGE.
    DATA LT_LGART TYPE TTY_LGART_RANGE.
    DATA LV_INPER TYPE IPERI.
    DATA LV_END_SEQNO TYPE XFELD.
    DATA LT_DISTRIB TYPE TTY_DISTRIB.
    DATA LT_DISTRIB_P TYPE TTY_DISTRIB.
    DATA LV_RUNID_P TYPE PCALAC-RUNID.
*    DATA lt_apznr_a TYPE tty_apznr_range.
*    DATA lt_apznr_p TYPE tty_apznr_range.
*    DATA lt_c1znr_a TYPE tty_c1znr_range.
*    DATA lt_c1znr_p TYPE tty_c1znr_range.

    CLEAR: MT_DISTRIB, MT_DISTRIB_WT.

    LOOP AT MT_PPOIX INTO DATA(LS_PPOIX).

      AT NEW PERNR.
        CLEAR: MV_RUNID, MV_INPER, LT_PAY_RESULT.
      ENDAT.

      "Get payroll result for Personnel number / Runid
      GET_PAYROLL_RESULT( EXPORTING IV_PERNR = LS_PPOIX-PERNR
                                    IV_RUNID = LS_PPOIX-RUNID
                          IMPORTING ET_RESULT = LT_PAY_RESULT
                                    EV_INPER = LV_INPER ).

      CLEAR LV_END_SEQNO.

      AT NEW SEQNO.
        CLEAR: LT_999S, LS_PAY_RESULT, LS_PAY_RESULT_P, MT_CUMUL_WT.
               "lt_apznr_a, lt_apznr_p, lt_c1znr_a, lt_c1znr_p.
        "Get payroll result for SEQNO
        READ TABLE LT_PAY_RESULT INTO LS_PAY_RESULT WITH KEY EVP-SEQNR = LS_PPOIX-SEQNO.
        IF SY-SUBRC = 0.
          "Get range of PZALA lgart valid at payroll date
          GET_PZALA_RANGE( EXPORTING IV_DATE = LS_PAY_RESULT-INTER-VERSC-FPBEG
                           IMPORTING ET_LGART = LT_PZALA ).
*          get_fx_cost_pointers( EXPORTING it_c0 = ls_pay_result-inter-c0
*                                          it_c1 = ls_pay_result-inter-c1
*                                IMPORTING et_apznr = lt_apznr_a
*                                          et_c1znr = lt_c1znr_a ).
        ENDIF.
        IF LV_INPER <> LS_PAY_RESULT-EVP-FPPER.   "Retroactivity case
          "Get the SEQNO of the P
          READ TABLE LT_PAY_RESULT INTO LS_PAY_RESULT_P WITH KEY EVP-FPPER = LS_PAY_RESULT-EVP-FPPER
                                                                 EVP-SRTZA = 'P'.
*          get_fx_cost_pointers( EXPORTING it_c0 = ls_pay_result-inter-c0
*                                          it_c1 = ls_pay_result-inter-c1
*                                IMPORTING et_apznr = lt_apznr_p
*                                          et_c1znr = lt_c1znr_p ).
        ENDIF.
      ENDAT.

      "Get the commitment item
      READ TABLE MT_PPDIT_PPDIX INTO DATA(LS_PPDIT_PPDIX) WITH KEY PERNR = LS_PPOIX-PERNR
                                                                   RUNID = LS_PPOIX-RUNID
                                                                   LINUM = LS_PPOIX-TSLIN.
      IF SY-SUBRC <> 0.
        CLEAR LS_PPDIT_PPDIX.
      ENDIF.

      "Get corresponding line in RT for 999S
      READ TABLE LS_PAY_RESULT-INTER-RT INTO DATA(LS_RT_999S) INDEX LS_PPOIX-RTLINE.
      IF SY-SUBRC = 0.
        "Check ABART / APZNR not already processed
        READ TABLE LT_999S TRANSPORTING NO FIELDS WITH KEY ABART = LS_RT_999S-ABART
                                                           LGART = LS_RT_999S-LGART
                                                           APZNR = '00'.
        IF SY-SUBRC <> 0.
          READ TABLE LT_999S TRANSPORTING NO FIELDS WITH KEY ABART = LS_RT_999S-ABART
                                                             LGART = LS_RT_999S-LGART
                                                             APZNR = LS_RT_999S-APZNR.
        ENDIF.
        IF SY-SUBRC <> 0.
          "Get the 9xxx on the same ABART and APZNR
          LOOP AT LS_PAY_RESULT-INTER-RT INTO DATA(LS_RT_9) WHERE ABART = LS_RT_999S-ABART
                                                            AND   LGART IN LT_PZALA.
            "Check if wage type is in the scope of fixed rate
            CALCULATE_DISTRIBUTION( EXPORTING IS_RT_9 = LS_RT_9
                                              IT_RT = LS_PAY_RESULT-INTER-RT
                                              IT_C0 = LS_PAY_RESULT-INTER-C0
                                              IV_PERNR = LS_PPOIX-PERNR
                                              IV_SEQNO = LS_PPOIX-SEQNO
                                              IV_ACTSIGN = LS_PPOIX-ACTSIGN
                                              IV_RUNID = LS_PPOIX-RUNID
                                              IV_WAERS = LS_PAY_RESULT-INTER-VERSC-WAERS
                                              IV_DATE = LS_PAY_RESULT-INTER-VERSC-FPBEG
                                              IV_SEQNO_P = LS_PAY_RESULT_P-EVP-SEQNR
                                              IV_FIPOS = LS_PPDIT_PPDIX-FIPOS
                                              "it_apznr = lt_apznr_a
                                              "it_c1znr = lt_c1znr_a
                                    IMPORTING ET_DISTRIB = LT_DISTRIB ).
            IF LS_RT_9-APZNR = LS_RT_999S-APZNR. "OR ls_rt_999s-apznr IS INITIAL.
              APPEND LINES OF LT_DISTRIB TO MT_DISTRIB.
              PUT_TO_CUMUL_DISTRIB( IT_DISTRIB = LT_DISTRIB ).
              "Set the cumul of wt in case of retroactivity
            ELSEIF LV_INPER <> LS_PAY_RESULT-EVP-FPPER.   "Retroactivity case
              APPEND LINES OF LT_DISTRIB TO MT_DISTRIB.
              PUT_TO_CUMUL_DISTRIB( IT_DISTRIB = LT_DISTRIB ).
              "Set the APZNR processed
              READ TABLE LT_999S TRANSPORTING NO FIELDS WITH KEY ABART = LS_RT_999S-ABART
                                                                 LGART = LS_RT_999S-LGART
                                                                 APZNR = LS_RT_9-APZNR.
              IF SY-SUBRC <> 0.
                MOVE-CORRESPONDING LS_RT_999S TO LS_999S.
                LS_RT_999S-APZNR = LS_RT_9-APZNR.
                APPEND LS_999S TO LT_999S.
              ENDIF.
            ENDIF.
          ENDLOOP.
          "Save the ABART / APZNR processed to avoid to do twice or higher
          MOVE-CORRESPONDING LS_RT_999S TO LS_999S.
          APPEND LS_999S TO LT_999S.
        ENDIF.
      ENDIF.

      AT END OF SEQNO.
        LV_END_SEQNO = ABAP_TRUE.
      ENDAT.

      IF LV_END_SEQNO = ABAP_TRUE AND LV_INPER <> LS_PAY_RESULT-EVP-FPPER.   "Retroactivity case
        """"Get the wage types concerned by BR in Previous not in Actual
        "Get range of PZALA lgart valid at payroll date
        GET_PZALA_RANGE( EXPORTING IV_DATE = LS_PAY_RESULT_P-INTER-VERSC-FPBEG
                         IMPORTING ET_LGART = LT_PZALA ).
        "Get the Runid retro
        SELECT SINGLE RUNID INTO @LV_RUNID_P FROM PCALAC WHERE PERNR = @LS_PPOIX-PERNR
                                                         AND   SEQNO = @LS_PAY_RESULT_P-EVP-SEQNR
                                                         AND   TYPE = 'PP'
                                                         AND   SRTZA = 'A'.
        LOOP AT LS_PAY_RESULT_P-INTER-RT INTO LS_RT_9 WHERE LGART IN LT_PZALA.
          "Check ABART
          READ TABLE LT_999S TRANSPORTING NO FIELDS WITH KEY ABART = LS_RT_9-ABART.
          CHECK SY-SUBRC = 0.
          CALCULATE_DISTRIBUTION( EXPORTING IS_RT_9 = LS_RT_9
                                            IT_RT = LS_PAY_RESULT_P-INTER-RT
                                            IT_C0 = LS_PAY_RESULT_P-INTER-C0
                                            IV_PERNR = LS_PPOIX-PERNR
                                            IV_SEQNO = LS_PAY_RESULT_P-EVP-SEQNR
                                            IV_ACTSIGN = LS_PPOIX-ACTSIGN
                                            IV_RUNID = LV_RUNID_P
                                            IV_WAERS = LS_PAY_RESULT_P-INTER-VERSC-WAERS
                                            IV_DATE = LS_PAY_RESULT_P-INTER-VERSC-FPBEG
                                            IV_SEQNO_P = LS_PAY_RESULT_P-EVP-SEQNR
                                            IV_RUNID_A = LS_PPOIX-RUNID
                                            IV_FIPOS = LS_PPDIT_PPDIX-FIPOS
                                            "it_apznr = lt_apznr_p
                                            "it_c1znr = lt_c1znr_p
                                  IMPORTING ET_DISTRIB = LT_DISTRIB_P ).
          LOOP AT LT_DISTRIB_P ASSIGNING FIELD-SYMBOL(<LS_DISTRIB>).
*          LOOP AT lt_distrib_p INTO DATA(ls_distrib_p).
*            READ TABLE mt_distrib TRANSPORTING NO FIELDS WITH KEY pernr = ls_ppoix-pernr
*                                                                  seqno = ls_ppoix-seqno
*                                                                  actsign = ls_ppoix-actsign
*                                                                  runid = ls_ppoix-runid
*                                                                  lgart_o = ls_distrib_p-lgart_o.
*            IF sy-subrc = 0.
*              "DELETE mt_distrib INDEX sy-tabix.
*              DELETE lt_distrib_p.
*            ENDIF.
            MULTIPLY <LS_DISTRIB>-BETRG_9 BY -1.
          ENDLOOP.
          IF LT_DISTRIB_P IS NOT INITIAL.
            APPEND LINES OF LT_DISTRIB_P TO MT_DISTRIB.
            PUT_TO_CUMUL_DISTRIB( IT_DISTRIB = LT_DISTRIB_P
                                  IV_SUBTRACT = ABAP_TRUE ).
          ENDIF.
        ENDLOOP.

        "Clean ditribution
        LOOP AT MT_CUMUL_WT INTO DATA(LS_CUMUL_WT) WHERE BETRG = 0.
          DELETE MT_DISTRIB WHERE PERNR = LS_PPOIX-PERNR
                            AND   ( SEQNO = LS_PAY_RESULT-EVP-SEQNR OR SEQNO = LS_PAY_RESULT_P-EVP-SEQNR )
                            AND   LGART_O = LS_CUMUL_WT-LGART .
        ENDLOOP.

      ENDIF.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00E ----
  METHOD __FOR_DEBUG_ANALYZE.

    DATA LS_PERNR_CHECK TYPE TY_PERNR_CHECK.

    CHECK MV_MODE_DEBUG = ABAP_TRUE.

    LS_PERNR_CHECK-PERNR = IV_PERNR.
    LS_PERNR_CHECK-DIFF = IV_AMOUNT.
    COLLECT LS_PERNR_CHECK INTO MT_PERNR_CHECK.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00F ----
  METHOD BUILD_FX_DISTRIBUTION.

    CHECK IT_PPDIT_PPDIX IS NOT INITIAL.
    MT_PPDIT_PPDIX = IT_PPDIT_PPDIX.

    IF MV_MODE_DEBUG = ABAP_TRUE.
      DELETE MT_PPDIT_PPDIX WHERE PERNR NOT IN MT_PERNR_DEBUG.
    ENDIF.

    "Extract lines from payroll posting
    READ_PPOIX_FROM_FI_TO_HR( ).

    "set the distribution Br amount from payroll
    SET_DISTRIBUTION_BR_AMOUNTS( ).

    CHECK MT_DISTRIB IS NOT INITIAL.

    "Get lines in PPOIX for the original wage types
    READ_PPOIX_FROM_HR_TO_FI( ).

    "Prorate BR amount in case of retroactivity
    "prorate_distribution_br_amount( ).

    "Prepare document lines
    PREPARE_DOC_LINES( IMPORTING ET_DOC_LINES = ET_DOC_LINES ).

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00G ----
  METHOD GET_FUND_TYPE.

    IF IV_BUKRS <> MV_BUKRS OR IV_GEBER <> MV_GEBER.
      IF IV_BUKRS <> MV_BUKRS.
        SELECT SINGLE FIKRS FROM T001 WHERE BUKRS = @IV_BUKRS INTO @MV_FIKRS.
        MV_BUKRS = IV_BUKRS.
      ENDIF.
      SELECT SINGLE TYPE FROM FMFINCODE WHERE FIKRS = @MV_FIKRS
                                        AND   FINCODE = @IV_GEBER
                         INTO @MV_FUNDTYPE.
      MV_GEBER = IV_GEBER.
    ENDIF.

    RV_FUNDTYPE = MV_FUNDTYPE.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CM00H ----
  METHOD GET_FX_COST_POINTERS.

    CLEAR: ET_APZNR, ET_C1ZNR.

    LOOP AT IT_C0 INTO DATA(LS_C0).
      CHECK LS_C0-KGBNN = 'GEF'.
      CHECK GET_FUND_TYPE( IV_BUKRS = LS_C0-KBUNN
                           IV_GEBER = LS_C0-GEBER ) <> '019'.
      APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = LS_C0-APZNR ) TO ET_APZNR.
    ENDLOOP.

    LOOP AT IT_C1 INTO DATA(LS_C1).
      CHECK LS_C1-GSBER = 'GEF'.
      CHECK GET_FUND_TYPE( IV_BUKRS = LS_C1-BUKRS
                           IV_GEBER = LS_C1-GEBER ) <> '019'.
      APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = LS_C1-C1ZNR ) TO ET_C1ZNR.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CO ----
PROTECTED SECTION.

* ---- YCL_FI_TO_PAYROLL_POSTING_BL==CU ----
CLASS YCL_FI_TO_PAYROLL_POSTING_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.

    TYPES:
      BEGIN OF TY_PPDIT_PPDIX,
        CT_INDEX TYPE SY-INDEX,
        DOCNUM   TYPE PPDIT-DOCNUM,
        DOCLIN   TYPE PPDIT-DOCLIN,
        PERNR    TYPE PPDIT-PERNR,
        RUNID    TYPE PPDIX-RUNID,
        LINUM    TYPE PPDIX-LINUM,
        FIPOS    TYPE BSEG-FIPOS,
      END OF TY_PPDIT_PPDIX .
    TYPES:
      TTY_PPDIT_PPDIX TYPE TABLE OF TY_PPDIT_PPDIX .
    TYPES:
      BEGIN OF TY_DOC_LINES,
        DOCNUM  TYPE PPDIX-DOCNUM,
        DOCLIN  TYPE PPDIX-DOCLIN,
        BETRG_O TYPE PPOIX-BETRG,
        WAERS_O TYPE WAERS,
        BETRG_9 TYPE PPOIX-BETRG,
        WAERS_9 TYPE WAERS,
        FIPOS   TYPE FIPOS,
        REDUC   TYPE CHAR1,
      END OF TY_DOC_LINES .
    TYPES:
      TTY_DOC_LINES TYPE SORTED TABLE OF TY_DOC_LINES WITH UNIQUE KEY DOCNUM DOCLIN .

    CLASS-METHODS CLASS_CONSTRUCTOR .
    CLASS-METHODS BUILD_FX_DISTRIBUTION
      IMPORTING
        !IT_PPDIT_PPDIX TYPE TTY_PPDIT_PPDIX
      EXPORTING
        !ET_DOC_LINES   TYPE TTY_DOC_LINES .