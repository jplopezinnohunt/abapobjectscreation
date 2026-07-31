* ==== CLASS POOL YCL_YPS11_BL ====
CLASS-POOL .
*"* class pool for class YCL_YPS11_BL

*"* local type definitions
INCLUDE YCL_YPS11_BL==================CCDEF.

*"* class YCL_YPS11_BL definition
*"* public declarations
  INCLUDE YCL_YPS11_BL==================CU.
*"* protected declarations
  INCLUDE YCL_YPS11_BL==================CO.
*"* private declarations
  INCLUDE YCL_YPS11_BL==================CI.
ENDCLASS. "YCL_YPS11_BL definition

*"* macro definitions
INCLUDE YCL_YPS11_BL==================CCMAC.
*"* local class implementation
INCLUDE YCL_YPS11_BL==================CCIMP.

CLASS YCL_YPS11_BL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_YPS11_BL implementation


* ---- YCL_YPS11_BL==================CI ----
PRIVATE SECTION.

  DATA MV_BEGGJAHR TYPE GJAHR .
  DATA MV_ENDGJAHR TYPE GJAHR .
  DATA MT_PRPS TYPE TT_PRPS .
  DATA MS_PRPS TYPE PRPS .
  DATA MT_PRPS_MAIN TYPE TT_PRPS .
  DATA MT_COEP TYPE ZTTPS_COEP_BY_OBJNR .
  DATA MS_COEP TYPE ZSPS_COEP_BY_OBJNR .
  DATA MT_COOI TYPE ZTTPS_COOI_BY_OBJNR .
  DATA MS_COOI TYPE ZSPS_COOI_BY_OBJNR .
  DATA MT_OUTGEN TYPE ZTPS_OUTGEN .
  DATA MS_OUTGEN TYPE ZSPS_OUTGEN .
  DATA MT_OUT TYPE ZTTPS_OUT .
  DATA MS_OUT TYPE ZSPS_OUT .
  DATA MT_OUTLINE TYPE ZTTPS_OUTLINE .
  DATA MS_OUTLINE TYPE ZSPS_OUTLINE .
  DATA MT_RPSCO TYPE ZTT_RPSCO .
  DATA MS_RPSCO TYPE RPSCO .
  CONSTANTS C_PLCOUNT TYPE CHAR8 VALUE '0102UNES' ##NO_TEXT.
  CONSTANTS C_CLASS TYPE SETCLASS VALUE '0102' ##NO_TEXT.
  CONSTANTS C_SUBCLASS TYPE SETSUBCLS VALUE 'UNES' ##NO_TEXT.
  CONSTANTS C_STAT TYPE J_STATUS VALUE 'I0046' ##NO_TEXT.
  DATA MT_NODE TYPE GENFM_T_SETNODE .
  DATA MS_NODE TYPE SETNODE .
  DATA MT_LEAF TYPE GENFM_T_SETLEAF .
  DATA MS_LEAF TYPE SETLEAF .
  DATA MT_HEADERT TYPE ZTTPS_SETHEADERT .
  DATA MS_HEADERT TYPE SETHEADERT .

  METHODS APPEND_OUT_GENERAL
    IMPORTING
      !IS_PRPS TYPE PRPS .
  METHODS APPEND_OUT
    IMPORTING
      !IS_PRPS TYPE PRPS .
  METHODS APPEND_OUT_LINE
    IMPORTING
      !IS_PRPS TYPE PRPS .
  METHODS GET_COMMITMENT_ITEMS .
  METHODS GET_COOP_COOI_FOR_ALL_PRPS .
  METHODS APPEND_OUT_LINE_NEW
    IMPORTING
      !IS_PRPS TYPE PRPS .

* ---- YCL_YPS11_BL==================CM001 ----
  METHOD SELECTION_BY_WBS.
* Buid from FORM Project_selection_wbs from report ZEBURWBS_YPS9_NEW
    DATA : LS_PROJ TYPE PROJ,
           LS_JEST TYPE JEST,
           LS_JCDS TYPE JCDS.

    SELECT *  FROM PRPS INTO TABLE MT_PRPS  WHERE POSID IN MR_POSID
                                              AND PKOKR IN MR_KOKRS.


    LOOP AT  MT_PRPS INTO MS_PRPS.

      SELECT SINGLE * INTO LS_PROJ FROM PROJ
                                  WHERE PSPID = MS_PRPS-POSID+0(10).
      IF SY-SUBRC = 0.
        SELECT SINGLE *  INTO LS_JEST FROM JEST
                                   WHERE OBJNR = LS_PROJ-OBJNR
                                    AND INACT = ' '
                                    AND STAT = C_STAT.
        IF SY-SUBRC = 0.
          SELECT SINGLE * INTO LS_JCDS FROM JCDS
                                      WHERE OBJNR = LS_PROJ-OBJNR
                                        AND INACT = SPACE
                                        AND STAT  = C_STAT  " 'I0046'
                                        AND CHGNR = LS_JEST-CHGNR.
          IF SY-SUBRC = 0.
            IF LS_JCDS-UDATE+0(4) LE MV_ENDGJAHR
                AND ( NOT ( LS_JCDS-UDATE+0(4) BETWEEN MV_BEGGJAHR AND MV_ENDGJAHR ) ).
              CONTINUE.
            ENDIF.
          ENDIF.
        ENDIF.
      ELSE.
        CONTINUE.
      ENDIF.

      ME->APPEND_OUT_GENERAL( IS_PRPS = MS_PRPS ).

      MS_OUT-BUDGETCODE = MS_PRPS-POSID.         " Budget Code
      MS_OUT-OBJNR = MS_PRPS-OBJNR.
      ME->APPEND_OUT( IS_PRPS = MS_PRPS ).

      APPEND MS_PRPS TO MT_PRPS_MAIN.
    ENDLOOP.


    IF SY-SUBRC = 0.
      ME->GET_COOP_COOI_FOR_ALL_PRPS( ).

      LOOP AT MT_PRPS_MAIN INTO MS_PRPS.
        MS_OUTLINE-BUDGETCODE = MS_PRPS-POSID.   " Budget Code
        MS_OUTLINE-OBJNR = MS_PRPS-OBJNR.
        MS_OUTLINE-KOKRS  = MS_PRPS-PKOKR.
        ME->APPEND_OUT_LINE_NEW( IS_PRPS =  MS_PRPS ).

      ENDLOOP.

      ME->GET_COMMITMENT_ITEMS( ).

      DELETE MT_OUT WHERE BUDGET_AMOUNT = 0
                      AND ACTUAL_AMOUNT = 0
                      AND COMMIT_AMOUNT = 0.


      DELETE MT_OUTLINE WHERE ACTUAL_AMOUNT = 0
                          AND COMMIT_AMOUNT = 0.
*

    ENDIF.
    ET_OUTGEN = MT_OUTGEN.
    ET_OUT     = MT_OUT.
    ET_OUTLINE = MT_OUTLINE.




  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM002 ----
  METHOD CONSTRUCTOR.

    DATA : LS_GJAHR TYPE FQMS_FISCAL_YEAR.
    MR_POSID = IR_POSID.
    MR_PSPID = IR_PSPID.
    MR_KOKRS = IR_KOKRS[].

      MV_BEGGJAHR = IV_BEGGJAHR.
      MV_ENDGJAHR = IV_ENDGJAHR.

    SELECT  * INTO TABLE MT_LEAF FROM SETLEAF
          WHERE SETCLASS = C_CLASS                          " '0102'
            AND SUBCLASS = C_SUBCLASS                 " 'UNES'
            AND SETNAME LIKE 'U%'
      ORDER BY SETCLASS SUBCLASS VALSIGN  VALOPTION  VALFROM.


    SELECT  * INTO TABLE MT_NODE FROM SETNODE
                               WHERE SETCLASS = C_CLASS     " '0102'
                                 AND SUBCLASS = C_SUBCLASS                 " 'UNES'
      ORDER BY SETCLASS  SUBCLASS  SUBSETNAME.



    SELECT  * INTO TABLE MT_HEADERT FROM SETHEADERT
                                WHERE SETCLASS = C_CLASS    " '0102'
                                  AND SUBCLASS = C_SUBCLASS
                                  AND LANGU    = SY-LANGU            " 'UNES'
      ORDER BY SETCLASS  SUBCLASS  SETNAME .



  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM003 ----
  METHOD APPEND_OUT_GENERAL.

  MS_OUTGEN-BUDGETCODE = IS_PRPS-POSID.         " Budget Code
  MS_OUTGEN-TITLE      = IS_PRPS-POST1.         " title
   MS_OUTGEN-KOKRS      = IS_PRPS-PKOKR.         " controlling area
 MS_OUTGEN-VERNA      = IS_PRPS-VERNA.         " PO
  MS_OUTGEN-ASTNA      = IS_PRPS-ASTNA.         " AO
  MS_OUTGEN-REGION     = IS_PRPS-USR00.         " region
  MS_OUTGEN-COUNTRY    = IS_PRPS-USR01.         " country
  MS_OUTGEN-SECTOR     = IS_PRPS-USR02.         " sector
  MS_OUTGEN-DIVISION   = IS_PRPS-USR03.         " division

  APPEND MS_OUTGEN TO MT_OUTGEN.

  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM004 ----
  METHOD APPEND_OUT.

    DATA: W_SAV_ACT_FKWAEHR TYPE BP_WPL.

    CLEAR MT_RPSCO.
    SELECT *  FROM RPSCO INTO TABLE MT_RPSCO
                   WHERE OBJNR =  IS_PRPS-OBJNR.


    LOOP AT MT_RPSCO INTO MS_RPSCO.
      MS_OUT-KOKRS = IS_PRPS-PKOKR.
      MS_OUT-BUDGET_AMOUNT = 0.
      MS_OUT-ACTUAL_AMOUNT = 0.
      MS_OUT-COMMIT_AMOUNT = 0.
      MS_OUT-PLAN_AMOUNT = 0.
      MS_OUT-FISCAL_YEAR = MS_RPSCO-GJAHR.                   "fiscal year
      MS_OUT-OBJNR =  MS_RPSCO-OBJNR .
      MS_OUT-ACPOS =  MS_RPSCO-ACPOS.
      CASE MS_RPSCO-WRTTP.
        WHEN '41'.                                             "Budget
          ADD MS_RPSCO-WLP00 TO MS_OUT-BUDGET_AMOUNT.
        WHEN OTHERS.
          DO VARYING W_SAV_ACT_FKWAEHR
             FROM MS_RPSCO-WLP01 NEXT MS_RPSCO-WLP02.
            IF W_SAV_ACT_FKWAEHR NE 0.
              IF MS_RPSCO-WRTTP = '04'.                       "Actual
                ADD W_SAV_ACT_FKWAEHR TO MS_OUT-ACTUAL_AMOUNT.
              ELSEIF MS_RPSCO-WRTTP = '01'.                   "Plan
                ADD W_SAV_ACT_FKWAEHR TO MS_OUT-PLAN_AMOUNT.
              ELSE.                                         "Commit
                ADD W_SAV_ACT_FKWAEHR TO MS_OUT-COMMIT_AMOUNT.
              ENDIF.
            ENDIF.
            CHECK SY-INDEX = 16.                  "Exit DO
            EXIT.
          ENDDO.
      ENDCASE.
      APPEND MS_OUT TO MT_OUT.

    ENDLOOP.


  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM005 ----
  METHOD APPEND_OUT_LINE.

    CLEAR MT_COEP.


    SELECT OBJNR WKGBTR GJAHR KSTAR PERIO WRTTP  FROM COEP INTO CORRESPONDING FIELDS OF TABLE MT_COEP
                                                 WHERE OBJNR = IS_PRPS-OBJNR
                                                   AND  GJAHR <= MV_ENDGJAHR
                                                   AND GJAHR >= MV_BEGGJAHR
                                                   AND PERIO <= 16
    %_HINTS MSSQLNT 'TABLE COEP ABINDEX(2)'.

    LOOP AT MT_COEP INTO MS_COEP.
      MS_OUTLINE-COMMIT_AMOUNT = 0.
      MS_OUTLINE-ACTUAL_AMOUNT = MS_COEP-WKGBTR.
      MS_OUTLINE-FISCAL_YEAR   = MS_COEP-GJAHR.      "fiscal year
      MS_OUTLINE-COST_ELE      = MS_COEP-KSTAR.         "Cost element
      MS_OUTLINE-COMM_ITEM_PAR = ''.
      MS_OUTLINE-COMM_ITEM     = ''.
      MS_OUTLINE-PERIO         = MS_COEP-PERIO.
      MS_OUTLINE-WRTTP         = MS_COEP-WRTTP.
      COLLECT MS_OUTLINE INTO MT_OUTLINE.
    ENDLOOP.
*************************************************

    CLEAR MT_COOI.

    SELECT OBJNR WKGBTR GJAHR SAKTO PERIO WRTTP REFBN RFPOS FROM COOI INTO CORRESPONDING FIELDS OF TABLE MT_COOI
                                                     WHERE OBJNR = IS_PRPS-OBJNR
                                                      AND  GJAHR <= MV_ENDGJAHR
                                                      AND GJAHR >= MV_BEGGJAHR
                                                      AND PERIO <= 16.

    LOOP AT MT_COOI INTO MS_COOI.
      MS_OUTLINE-COMMIT_AMOUNT = MS_COOI-WKGBTR.
      MS_OUTLINE-ACTUAL_AMOUNT = 0.
      MS_OUTLINE-FISCAL_YEAR   = MS_COOI-GJAHR.      "fiscal year
      MS_OUTLINE-COST_ELE      = MS_COOI-SAKTO.         "Cost element
      MS_OUTLINE-COMM_ITEM_PAR = ''.
      MS_OUTLINE-COMM_ITEM     = ''.
      MS_OUTLINE-PERIO         = MS_COOI-PERIO.
      MS_OUTLINE-WRTTP         = MS_COOI-WRTTP.
      COLLECT MS_OUTLINE INTO MT_OUTLINE..
    ENDLOOP.


  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM006 ----
  METHOD GET_COMMITMENT_ITEMS.

    DATA : LS_SETLEAF    TYPE SETLEAF,
           LS_SETNODE    TYPE SETNODE,
           LS_SETHEADERT TYPE SETHEADERT.

    SORT MT_OUTLINE BY COST_ELE.
    LOOP AT MT_OUTLINE INTO MS_OUTLINE.

*      SELECT SINGLE * INTO ls_setleaf FROM setleaf
*        WHERE setclass = c_class                            " '0102'
*          AND subclass = c_subclass                 " 'UNES'
*          AND setname LIKE 'U%'
*          AND valfrom LE ms_outline-cost_ele
*          AND valto   GE ms_outline-cost_ele  .
      CLEAR MS_LEAF.
      READ TABLE MT_LEAF INTO MS_LEAF WITH KEY SETCLASS = C_CLASS
                                               SUBCLASS = C_SUBCLASS
                                               VALSIGN = 'I'
                                               VALOPTION = 'EQ'
                                               VALFROM = MS_OUTLINE-COST_ELE
                                               BINARY SEARCH.
      IF SY-SUBRC NE 0.
        LOOP AT MT_LEAF INTO MS_LEAF WHERE SETCLASS = C_CLASS
                                       AND SUBCLASS = C_SUBCLASS
                                       AND VALSIGN  = 'I'
                                       AND VALOPTION = 'BT'
                                       AND VALFROM  LE MS_OUTLINE-COST_ELE
                                       AND VALTO    GE MS_OUTLINE-COST_ELE.
        ENDLOOP.
      ENDIF.

      IF MS_LEAF IS NOT INITIAL.



        READ TABLE MT_NODE INTO MS_NODE WITH KEY SETCLASS = C_CLASS
                                                 SUBCLASS = C_SUBCLASS
                                                 SUBSETNAME = MS_LEAF-SETNAME
                                                 BINARY SEARCH.

        IF SY-SUBRC = 0.

          READ TABLE MT_HEADERT INTO MS_HEADERT WITH KEY SETCLASS = C_CLASS
                                                         SUBCLASS = C_SUBCLASS
                                                         SETNAME = MS_NODE-SETNAME
                                                         BINARY SEARCH.
          IF SY-SUBRC EQ 0.
            MS_OUTLINE-COMM_ITEM_PAR = MS_HEADERT-DESCRIPT.
          ENDIF.


          READ TABLE MT_HEADERT INTO MS_HEADERT WITH KEY SETCLASS = C_CLASS
                                                         SUBCLASS = C_SUBCLASS
                                                         SETNAME = MS_LEAF-SETNAME
                                                         BINARY SEARCH.
          IF SY-SUBRC = 0.
            MS_OUTLINE-COMM_ITEM = MS_HEADERT-DESCRIPT.
          ENDIF.

          MODIFY MT_OUTLINE FROM MS_OUTLINE.
        ENDIF.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM007 ----
  METHOD SELECTION_BY_PROJECT.

    SELECT PRPS~OBJNR PRPS~POSID PRPS~PSPHI PRPS~POST1 PRPS~VERNA PRPS~PKOKR
           PRPS~ASTNA PRPS~USR00 PRPS~USR01 PRPS~USR02 PRPS~USR03
        FROM PRPS  AS PRPS
        INNER JOIN PROJ      AS PROJ
        ON PRPS~PSPHI =  PROJ~PSPNR
        INTO CORRESPONDING FIELDS OF TABLE MT_PRPS
        WHERE PROJ~PSPID IN MR_PSPID
          AND PROJ~VKOKR IN MR_KOKRS.

    LOOP AT MT_PRPS INTO MS_PRPS.

      ME->APPEND_OUT_GENERAL( IS_PRPS = MS_PRPS ).

      MS_OUT-BUDGETCODE = MS_PRPS-POSID.         " Budget Code
              MS_OUTLINE-KOKRS  = MS_PRPS-PKOKR.
      MS_OUT-OBJNR = MS_PRPS-OBJNR.

      ME->APPEND_OUT( IS_PRPS = MS_PRPS ).

      APPEND MS_PRPS TO MT_PRPS_MAIN.

    ENDLOOP.

    IF SY-SUBRC  = 0.
      ME->GET_COOP_COOI_FOR_ALL_PRPS( ).

      LOOP AT MT_PRPS_MAIN INTO MS_PRPS.
        MS_OUTLINE-BUDGETCODE = MS_PRPS-POSID.   " Budget Code
        MS_OUTLINE-OBJNR = MS_PRPS-OBJNR.

        ME->APPEND_OUT_LINE_NEW( IS_PRPS =  MS_PRPS ).

      ENDLOOP.

      ME->GET_COMMITMENT_ITEMS( ).

      DELETE MT_OUT WHERE BUDGET_AMOUNT = 0
                      AND ACTUAL_AMOUNT = 0
                      AND COMMIT_AMOUNT = 0.


      DELETE MT_OUTLINE WHERE ACTUAL_AMOUNT = 0
                          AND COMMIT_AMOUNT = 0.
*

    ENDIF.
    ET_OUTGEN = MT_OUTGEN.
    ET_OUT     = MT_OUT.
    ET_OUTLINE = MT_OUTLINE.

  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM008 ----
  METHOD GET_COOP_COOI_FOR_ALL_PRPS.

DATA : LT_COEP TYPE ZTTPS_COEP_BY_OBJNR,
       LT_COOI TYPE ZTTPS_COOI_BY_OBJNR.

    CLEAR MT_COEP.
    SELECT OBJNR   GJAHR PERIO KSTAR  WRTTP WKGBTR BELNR BUZEI FROM COEP INTO TABLE MT_COEP
      FOR ALL ENTRIES IN MT_PRPS_MAIN
                                                 WHERE OBJNR = MT_PRPS_MAIN-OBJNR
                                                   AND  GJAHR <= MV_ENDGJAHR
                                                   AND GJAHR >= MV_BEGGJAHR
                                                   AND PERIO <= 16
      %_HINTS MSSQLNT 'TABLE COEP ABINDEX(ZOB)'.

    SORT MT_COEP BY OBJNR GJAHR PERIO KSTAR WRTTP WKGBTR.
    LOOP AT MT_COEP INTO MS_COEP.
      AT END OF WRTTP.
        SUM.
        APPEND MS_COEP TO LT_COEP.
      ENDAT.
    ENDLOOP.

    MT_COEP = LT_COEP.
    CLEAR MT_COOI.



    SELECT OBJNR   GJAHR PERIO SAKTO WRTTP WKGBTR  REFBN RFPOS
      REFBT RFKNT RFTRM RFART LIFNR LEDNR HRKFT RFORG RFTYP RFSYS
      FROM COOI INTO CORRESPONDING FIELDS OF TABLE MT_COOI
      FOR ALL ENTRIES IN MT_PRPS_MAIN
                                                     WHERE OBJNR = MT_PRPS_MAIN-OBJNR
                                                      AND  GJAHR <= MV_ENDGJAHR
                                                      AND GJAHR >= MV_BEGGJAHR
                                                      AND PERIO <= 16
            %_HINTS MSSQLNT 'TABLE COOI ABINDEX(ZOB)'.

   SORT MT_COOI BY OBJNR GJAHR PERIO SAKTO WRTTP WKGBTR.
    LOOP AT MT_COOI INTO MS_COOI.
      AT END OF WRTTP.
        SUM.
        APPEND MS_COOI TO LT_COOI.
      ENDAT.
    ENDLOOP.

MT_COOI = LT_COOI.
  ENDMETHOD.

* ---- YCL_YPS11_BL==================CM009 ----
  METHOD APPEND_OUT_LINE_NEW.

*    CLEAR mt_coep.
*
*
*    SELECT objnr wkgbtr gjahr kstar perio wrttp  FROM coep INTO CORRESPONDING FIELDS OF TABLE mt_coep
*                                                 WHERE objnr = is_prps-objnr
*                                                   AND  gjahr <= mv_endgjahr
*                                                   AND gjahr >= mv_beggjahr
*                                                   AND perio <= 16
*    %_HINTS MSSQLNT 'TABLE COEP ABINDEX(2)'.

    LOOP AT MT_COEP INTO MS_COEP WHERE OBJNR = IS_PRPS-OBJNR.
      MS_OUTLINE-KOKRS = IS_PRPS-PKOKR.
      MS_OUTLINE-COMMIT_AMOUNT = 0.
      MS_OUTLINE-ACTUAL_AMOUNT = MS_COEP-WKGBTR.
      MS_OUTLINE-FISCAL_YEAR   = MS_COEP-GJAHR.      "fiscal year
      MS_OUTLINE-COST_ELE      = MS_COEP-KSTAR.         "Cost element
      MS_OUTLINE-COMM_ITEM_PAR = ''.
      MS_OUTLINE-COMM_ITEM     = ''.
      MS_OUTLINE-PERIO         = MS_COEP-PERIO.
      MS_OUTLINE-WRTTP         = MS_COEP-WRTTP.
      COLLECT MS_OUTLINE INTO MT_OUTLINE.
    ENDLOOP.
*************************************************

*    CLEAR mt_cooi.
*
*    SELECT objnr wkgbtr gjahr sakto perio wrttp  FROM cooi INTO CORRESPONDING FIELDS OF TABLE mt_cooi
*                                                     WHERE objnr = is_prps-objnr
*                                                      AND  gjahr <= mv_endgjahr
*                                                      AND gjahr >= mv_beggjahr
*                                                      AND perio <= 16.

    LOOP AT MT_COOI INTO MS_COOI WHERE OBJNR = IS_PRPS-OBJNR.
       MS_OUTLINE-KOKRS = IS_PRPS-PKOKR.
     MS_OUTLINE-COMMIT_AMOUNT = MS_COOI-WKGBTR.
      MS_OUTLINE-ACTUAL_AMOUNT = 0.
      MS_OUTLINE-FISCAL_YEAR   = MS_COOI-GJAHR.      "fiscal year
      MS_OUTLINE-COST_ELE      = MS_COOI-SAKTO.         "Cost element
      MS_OUTLINE-COMM_ITEM_PAR = ''.
      MS_OUTLINE-COMM_ITEM     = ''.
      MS_OUTLINE-PERIO         = MS_COOI-PERIO.
      MS_OUTLINE-WRTTP         = MS_COOI-WRTTP.
      COLLECT MS_OUTLINE INTO MT_OUTLINE..
    ENDLOOP.


  ENDMETHOD.

* ---- YCL_YPS11_BL==================CO ----
PROTECTED SECTION.

* ---- YCL_YPS11_BL==================CU ----
CLASS YCL_YPS11_BL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  DATA MR_POSID TYPE CURTO_PSPNR_RANGE_T .
  DATA MR_PSPID TYPE ZSPS_PSPID_RANGE_T .
  DATA MR_GJAHR TYPE FQMR_FISCAL_YEAR .
  DATA MR_KOKRS TYPE FAGL_RANGE_T_KOKRS .

  METHODS CONSTRUCTOR
    IMPORTING
      !IR_KOKRS TYPE FAGL_RANGE_T_KOKRS
      !IR_POSID TYPE CURTO_PSPNR_RANGE_T
      !IR_PSPID TYPE ZSPS_PSPID_RANGE_T
      !IV_BEGGJAHR TYPE GJAHR
      !IV_ENDGJAHR TYPE GJAHR .
  METHODS SELECTION_BY_WBS
    EXPORTING
      !ET_OUTGEN TYPE ZTPS_OUTGEN
      !ET_OUT TYPE ZTTPS_OUT
      !ET_OUTLINE TYPE ZTTPS_OUTLINE .
  METHODS SELECTION_BY_PROJECT
    EXPORTING
      !ET_OUTGEN TYPE ZTPS_OUTGEN
      !ET_OUT TYPE ZTTPS_OUT
      !ET_OUTLINE TYPE ZTTPS_OUTLINE .