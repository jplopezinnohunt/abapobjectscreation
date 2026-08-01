* ==== CLASS POOL YCL_FM_FUND_C5_ACTION ====
CLASS-POOL .
*"* class pool for class YCL_FM_FUND_C5_ACTION

*"* local type definitions
INCLUDE YCL_FM_FUND_C5_ACTION=========CCDEF.

*"* class YCL_FM_FUND_C5_ACTION definition
*"* public declarations
  INCLUDE YCL_FM_FUND_C5_ACTION=========CU.
*"* protected declarations
  INCLUDE YCL_FM_FUND_C5_ACTION=========CO.
*"* private declarations
  INCLUDE YCL_FM_FUND_C5_ACTION=========CI.
ENDCLASS. "YCL_FM_FUND_C5_ACTION definition

*"* macro definitions
INCLUDE YCL_FM_FUND_C5_ACTION=========CCMAC.
*"* local class implementation
INCLUDE YCL_FM_FUND_C5_ACTION=========CCIMP.

CLASS YCL_FM_FUND_C5_ACTION IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_FUND_C5_ACTION implementation


* ---- YCL_FM_FUND_C5_ACTION=========CI ----
PRIVATE SECTION.

  CLASS-METHODS WRITE_CHANGE_DOCUMENT
    IMPORTING
      !IV_OBJECTID TYPE CDOBJECTV
      !IS_OLD_FUND_C5 TYPE YTFM_FUND_C5 OPTIONAL
      !IS_NEW_FUND_C5 TYPE YTFM_FUND_C5 OPTIONAL
      !IV_ACTION TYPE CDCHNGIND .

* ---- YCL_FM_FUND_C5_ACTION=========CM001 ----
  METHOD DO_UPDATE.

    DATA LT_OLD TYPE YTTFM_FUND_C5_DB.
    DATA LT_NEW TYPE YTTFM_FUND_C5_DB.
    DATA LT_INS TYPE YTTFM_FUND_C5_DB.
    DATA LT_UPD_AFTER TYPE YTTFM_FUND_C5_DB.
    DATA LT_UPD_BEFORE TYPE YTTFM_FUND_C5_DB.
    DATA LT_DEL TYPE YTTFM_FUND_C5_DB.

    LT_OLD = IT_FUND_C5_OLD. SORT LT_OLD.
    LT_NEW = IT_FUND_C5_NEW. SORT LT_NEW.

    LOOP AT LT_NEW INTO DATA(LS_NEW).
      "Check if already exists
      READ TABLE LT_OLD INTO DATA(LS_OLD) WITH KEY FIKRS = LS_NEW-FIKRS
                                                   FINCODE = LS_NEW-FINCODE
                                                   C5_ID = LS_NEW-C5_ID.
      IF SY-SUBRC = 0.   "Already exists
        DELETE LT_OLD INDEX SY-TABIX.
        "Check if modified
        IF LS_NEW <> LS_OLD.
          APPEND LS_OLD  TO LT_UPD_BEFORE.
          APPEND LS_NEW TO LT_UPD_AFTER.
        ENDIF.
      ELSE.   "Doesn't exist => create
        APPEND LS_NEW TO LT_INS.
      ENDIF.
    ENDLOOP.

    "Delete remaining old
    LOOP AT LT_OLD INTO LS_OLD.
      APPEND LS_OLD TO LT_DEL.
    ENDLOOP.

    "Do database updates
    IF LT_DEL IS NOT INITIAL.
      DELETE YTFM_FUND_C5 FROM TABLE LT_DEL.
      IF SY-SUBRC = 0.
        "Generate change document
        LOOP AT LT_DEL INTO DATA(LS_DEL).
          WRITE_CHANGE_DOCUMENT( IV_OBJECTID = |{ LS_DEL-FIKRS }|  "like fund masterdata change doc
                                 IS_OLD_FUND_C5 = LS_DEL
                                 IV_ACTION = 'D' ).
        ENDLOOP.
      ENDIF.
    ENDIF.

    IF LT_UPD_AFTER IS NOT INITIAL.
      UPDATE YTFM_FUND_C5 FROM TABLE LT_UPD_AFTER.
      IF SY-SUBRC = 0.
        "Generate change document
        LOOP AT LT_UPD_AFTER INTO DATA(LS_UPD_AFTER).
          READ TABLE LT_UPD_BEFORE INTO DATA(LS_UPD_BEFORE) WITH KEY FIKRS = LS_UPD_AFTER-FIKRS
                                                                     FINCODE = LS_UPD_AFTER-FINCODE
                                                                     C5_ID = LS_UPD_AFTER-C5_ID.
          IF SY-SUBRC <> 0.
            CLEAR LS_UPD_BEFORE.
          ENDIF.
          WRITE_CHANGE_DOCUMENT( IV_OBJECTID = |{ LS_UPD_AFTER-FIKRS }|  "like fund masterdata change doc
                                 IS_OLD_FUND_C5 = LS_UPD_BEFORE
                                 IS_NEW_FUND_C5 = LS_UPD_AFTER
                                 IV_ACTION = 'U' ).
        ENDLOOP.
      ENDIF.
    ENDIF.

    IF LT_INS IS NOT INITIAL.
      INSERT YTFM_FUND_C5 FROM TABLE LT_INS.
      IF SY-SUBRC = 0.
        "Generate change document
        LOOP AT LT_INS INTO DATA(LS_INS).
          WRITE_CHANGE_DOCUMENT( IV_OBJECTID = |{ LS_INS-FIKRS }|  "like fund masterdata change doc
                                 IS_NEW_FUND_C5 = LS_INS
                                 IV_ACTION = 'I' ).
        ENDLOOP.
      ENDIF.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM002 ----
  METHOD WRITE_CHANGE_DOCUMENT.

    CALL FUNCTION 'YFMFUNDC5_WRITE_DOCUMENT'
      EXPORTING
        OBJECTID         = IV_OBJECTID
        TCODE            = SY-TCODE
        UTIME            = SY-UZEIT
        UDATE            = SY-DATUM
        USERNAME         = SY-UNAME
*       PLANNED_CHANGE_NUMBER         = ' '
*       OBJECT_CHANGE_INDICATOR       = 'U'
*       PLANNED_OR_REAL_CHANGES       = ' '
*       NO_CHANGE_POINTERS            = ' '
        N_YTFM_FUND_C5   = IS_NEW_FUND_C5
        O_YTFM_FUND_C5   = IS_OLD_FUND_C5
        UPD_YTFM_FUND_C5 = IV_ACTION
* IMPORTING
*       CHANGENUMBER     =
      .

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM003 ----
  METHOD ENQUEUE_FUND.

    DATA LV_PAR1 TYPE SY-MSGV1.
    DATA LV_PAR2 TYPE SY-MSGV2.

    CLEAR: EV_SUBRC, ES_RETURN.

    CALL FUNCTION 'ENQUEUE_EFMFINCODE'
      EXPORTING
*       MODE_FMFINCODE = 'E'
*       MANDT          = SY-MANDT
        FIKRS          = IV_FIKRS
        FINCODE        = IV_FINCODE
*       X_FIKRS        = ' '
*       X_FINCODE      = ' '
*       _SCOPE         = '2'
*       _WAIT          = ' '
*       _COLLECT       = ' '
      EXCEPTIONS
        FOREIGN_LOCK   = 1
        SYSTEM_FAILURE = 2
        OTHERS         = 3.

    EV_SUBRC = SY-SUBRC.

    IF EV_SUBRC <> 0.
      LV_PAR1 = IV_FIKRS.
      LV_PAR2 = IV_FINCODE.

      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'YFM1'
          NUMBER     = '024'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
          PAR3       = SY-MSGV1
        IMPORTING
          BAPIRETURN = ES_RETURN.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM004 ----
  METHOD DEQUEUE_FUND.

    CALL FUNCTION 'DEQUEUE_EFMFINCODE'
      EXPORTING
        FIKRS   = IV_FIKRS
        FINCODE = IV_FINCODE.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM005 ----
  METHOD UPDATE_FROM_BAPI_V2.

    DATA LV_PAR1 TYPE SYST_MSGV.
    DATA LV_PAR2 TYPE SYST_MSGV.
    DATA LV_PAR3 TYPE SYST_MSGV.
    DATA LT_C5 TYPE TABLE OF YTFM_C5.
    DATA LT_C5_ACT TYPE YTTFM_FUND_C5_DB.
    DATA LV_BEGBI TYPE DATUM.
    DATA LV_ENDBI TYPE DATUM.
    DATA LV_ERROR TYPE XFELD.
    DATA LT_C5_NEW TYPE YTTFM_FUND_C5_DB.
    DATA LV_SUBRC TYPE SY-SUBRC.
    DATA LS_RETURN TYPE BAPIRETURN1.

    LV_PAR1 = IV_FM_AREA.
    LV_PAR2 = IV_FUND.

    CLEAR ET_RETURN.

    "Check fund exist
    SELECT SINGLE * FROM FMFINCODE WHERE FIKRS = @IV_FM_AREA
                                   AND   FINCODE = @IV_FUND
                              INTO @DATA(LS_FMFINCODE).
    IF SY-SUBRC <> 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'F6'
          NUMBER     = '069'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = LS_RETURN.
      APPEND LS_RETURN TO ET_RETURN.
      EXIT.
    ENDIF.

    "Get actual assignment
    SELECT * FROM YTFM_FUND_C5 WHERE FIKRS = @IV_FM_AREA
                               AND   FINCODE = @IV_FUND
                          INTO TABLE @LT_C5_ACT.

    LT_C5_NEW = LT_C5_ACT.

    "Get list of C/5 id with periods
    SELECT * FROM YTFM_C5 INTO TABLE @LT_C5.

    LOOP AT IT_C5_ASSIGNMENT INTO DATA(LS_C5_ASSIGNMENT).

      "Check first if the C5 id exists
      READ TABLE LT_C5 INTO DATA(LS_C5) WITH KEY C5_ID = LS_C5_ASSIGNMENT-C5_ID.
      IF SY-SUBRC <> 0.
        "&1 C/5 doesn't exist
        LV_PAR1 = LS_C5_ASSIGNMENT-C5_ID.
        CALL FUNCTION 'BALW_BAPIRETURN_GET1'
          EXPORTING
            TYPE       = 'E'
            CL         = 'YFM1'
            NUMBER     = '023'
            PAR1       = LV_PAR1
          IMPORTING
            BAPIRETURN = LS_RETURN.
        APPEND LS_RETURN TO ET_RETURN.
        LV_ERROR = ABAP_TRUE.
        CONTINUE.
      ENDIF.

      "Then check if fund validity is in the c/5
      IF LS_C5_ASSIGNMENT-C5_SEL = ABAP_TRUE OR LS_C5_ASSIGNMENT-FM_OUTPUT IS NOT INITIAL.  "C/5 assigned
        LV_BEGBI = |{ LS_C5-YEAR_FROM }0101|.
        LV_ENDBI = |{ LS_C5-YEAR_TO }1231|.
        IF LS_FMFINCODE-DATAB > LV_ENDBI OR LS_FMFINCODE-DATBIS < LV_BEGBI.
          LV_PAR1 = LS_C5_ASSIGNMENT-C5_ID.
          WRITE LS_FMFINCODE-DATAB TO LV_PAR2.
          WRITE LS_FMFINCODE-DATBIS TO LV_PAR3.
          "Assignment to &1 C/5 is not possible with fund validity &2 - &3
          CALL FUNCTION 'BALW_BAPIRETURN_GET1'
            EXPORTING
              TYPE       = 'E'
              CL         = 'YFM1'
              NUMBER     = '022'
              PAR1       = LV_PAR1
              PAR2       = LV_PAR2
              PAR3       = LV_PAR3
            IMPORTING
              BAPIRETURN = LS_RETURN.
          APPEND LS_RETURN TO ET_RETURN.
          LV_ERROR = ABAP_TRUE.
        ENDIF.
        IF LS_C5_ASSIGNMENT-FM_OUTPUT IS INITIAL.
          IF LS_C5-YCHK_OUTPUT = ABAP_TRUE.
            LV_PAR1 = LS_C5-C5_ID.
            "Output for fund is mandatory when &1 C/5 is selected
            CALL FUNCTION 'BALW_BAPIRETURN_GET1'
              EXPORTING
                TYPE       = 'E'
                CL         = 'ZFI'
                NUMBER     = '037'
                PAR1       = LV_PAR1
              IMPORTING
                BAPIRETURN = LS_RETURN.
            APPEND LS_RETURN TO ET_RETURN.
            LV_ERROR = ABAP_TRUE.
          ENDIF.
        ELSE.
          "Check output exists
          SELECT SINGLE * FROM YTFM_OUTPUT WHERE FM_OUTPUT = @LS_C5_ASSIGNMENT-FM_OUTPUT INTO @DATA(LS_OUTPUT).
          IF SY-SUBRC <> 0.
            "Output &1 doesn't exist
            LV_PAR1 = LS_C5_ASSIGNMENT-FM_OUTPUT.
            CALL FUNCTION 'BALW_BAPIRETURN_GET1'
              EXPORTING
                TYPE       = 'E'
                CL         = 'YFM1'
                NUMBER     = '010'
                PAR1       = LV_PAR1
              IMPORTING
                BAPIRETURN = LS_RETURN.
            APPEND LS_RETURN TO ET_RETURN.
            LV_ERROR = ABAP_TRUE.
          ENDIF.
        ENDIF.
      ENDIF.

      CHECK LV_ERROR = ABAP_FALSE.

      "Update new image
      READ TABLE LT_C5_NEW INTO DATA(LS_C5_NEW) WITH KEY FIKRS = LS_FMFINCODE-FIKRS
                                                         FINCODE = LS_FMFINCODE-FINCODE
                                                         C5_ID = LS_C5_ASSIGNMENT-C5_ID.
      IF SY-SUBRC = 0.
        IF LS_C5_ASSIGNMENT-C5_SEL = ABAP_TRUE OR LS_C5_ASSIGNMENT-FM_OUTPUT IS NOT INITIAL.
          LS_C5_NEW-FM_OUTPUT = LS_C5_ASSIGNMENT-FM_OUTPUT.
          LS_C5_NEW-C5_SEL = LS_C5_ASSIGNMENT-C5_SEL.
          MODIFY LT_C5_NEW FROM LS_C5_NEW INDEX SY-TABIX.
        ELSE.
          DELETE LT_C5_NEW INDEX SY-TABIX.
        ENDIF.
      ELSEIF LS_C5_ASSIGNMENT-C5_SEL = ABAP_TRUE OR LS_C5_ASSIGNMENT-FM_OUTPUT IS NOT INITIAL.
        "add the new entry
        CLEAR LS_C5_NEW.
        MOVE-CORRESPONDING LS_C5_ASSIGNMENT TO LS_C5_NEW.
        LS_C5_NEW-MANDT = SY-MANDT.
        LS_C5_NEW-FIKRS = LS_FMFINCODE-FIKRS.
        LS_C5_NEW-FINCODE = LS_FMFINCODE-FINCODE.
        APPEND LS_C5_NEW TO LT_C5_NEW.
      ENDIF.

    ENDLOOP.

    CHECK LV_ERROR = ABAP_FALSE.

    SORT LT_C5_NEW.

    IF LT_C5_NEW = LT_C5_ACT.
      "No update needed for fund &1 &2 C/5 assignment
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'I'
          CL         = 'YFM1'
          NUMBER     = '020'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = LS_RETURN.
      APPEND LS_RETURN TO ET_RETURN.
      EXIT.
    ENDIF.

    CHECK IV_NO_UPDATE = ABAP_FALSE.

    "Lock Fund
    ENQUEUE_FUND( EXPORTING IV_FIKRS = IV_FM_AREA
                            IV_FINCODE = IV_FUND
                  IMPORTING EV_SUBRC = LV_SUBRC
                            ES_RETURN = LS_RETURN ).
    IF LV_SUBRC <> 0.
      APPEND LS_RETURN TO ET_RETURN.
      EXIT.
    ENDIF.

    "Update database
    DO_UPDATE( IT_FUND_C5_OLD = LT_C5_ACT
               IT_FUND_C5_NEW = LT_C5_NEW ).

    "Unlock fund
    DEQUEUE_FUND( EXPORTING IV_FIKRS = IV_FM_AREA
                            IV_FINCODE = IV_FUND ).

    CALL FUNCTION 'BALW_BAPIRETURN_GET1'
      EXPORTING
        TYPE       = 'I'
        CL         = 'YFM1'
        NUMBER     = '021'
        PAR1       = LV_PAR1
        PAR2       = LV_PAR2
      IMPORTING
        BAPIRETURN = LS_RETURN.
    APPEND LS_RETURN TO ET_RETURN.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM006 ----
  METHOD UPDATE_FROM_BAPI_V1.

    DATA LV_PAR1 TYPE SYST_MSGV.
    DATA LV_PAR2 TYPE SYST_MSGV.
    DATA LV_PAR3 TYPE SYST_MSGV.
    DATA LT_C5 TYPE TABLE OF YTFM_C5.
    DATA LT_C5_ACT TYPE TABLE OF YTFM_FUND_C5.
    DATA LV_BEGBI TYPE DATUM.
    DATA LV_ENDBI TYPE DATUM.
    DATA LV_ERROR TYPE XFELD.
    DATA LT_C5_UPD TYPE TABLE OF YTFM_FUND_C5.
    DATA LS_C5_UPD TYPE YTFM_FUND_C5.
    FIELD-SYMBOLS <ZZOUTPUT> TYPE YE_FM_OUTPUT.

    LV_PAR1 = IV_FM_AREA.
    LV_PAR2 = IV_FUND.

    "Check fund exist
    SELECT SINGLE * FROM FMFINCODE WHERE FIKRS = @IV_FM_AREA
                                   AND   FINCODE = @IV_FUND
                              INTO @DATA(LS_FMFINCODE).
    IF SY-SUBRC <> 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'F6'
          NUMBER     = '069'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    "Get output
    ASSIGN COMPONENT 'ZZOUTPUT' OF STRUCTURE LS_FMFINCODE TO <ZZOUTPUT>.

    "Get actual assignment
    SELECT * FROM YTFM_FUND_C5 WHERE FIKRS = @IV_FM_AREA
                               AND   FINCODE = @IV_FUND
                          INTO TABLE @LT_C5_ACT.

    LT_C5_UPD = LT_C5_ACT.

    "Get list of C/5 id with periods
    SELECT * FROM YTFM_C5 INTO TABLE @LT_C5.

    LOOP AT IT_C5_ASSIGNMENT INTO DATA(LS_C5_NEW).

      "Check first if the C5 id exists
      READ TABLE LT_C5 INTO DATA(LS_C5) WITH KEY C5_ID = LS_C5_NEW-C5_ID.
      IF SY-SUBRC <> 0.
        LV_PAR1 = LS_C5_NEW-C5_ID.
        CALL FUNCTION 'BALW_BAPIRETURN_GET1'
          EXPORTING
            TYPE       = 'E'
            CL         = 'YFM1'
            NUMBER     = '023'
            PAR1       = LV_PAR1
          IMPORTING
            BAPIRETURN = ES_RETURN.
        LV_ERROR = ABAP_TRUE.
        EXIT.
      ENDIF.

      "Then check if fund validity is in the c/5
      IF LS_C5_NEW-C5_SEL = ABAP_TRUE.  "C/5 assigned
        LV_BEGBI = |{ LS_C5-YEAR_FROM }0101|.
        LV_ENDBI = |{ LS_C5-YEAR_TO }1231|.
        IF LS_FMFINCODE-DATAB > LV_ENDBI OR LS_FMFINCODE-DATBIS < LV_BEGBI.
          LV_PAR1 = LS_C5_NEW-C5_ID.
          WRITE LS_FMFINCODE-DATAB TO LV_PAR2.
          WRITE LS_FMFINCODE-DATBIS TO LV_PAR3.
          CALL FUNCTION 'BALW_BAPIRETURN_GET1'
            EXPORTING
              TYPE       = 'E'
              CL         = 'YFM1'
              NUMBER     = '022'
              PAR1       = LV_PAR1
              PAR2       = LV_PAR2
              PAR3       = LV_PAR3
            IMPORTING
              BAPIRETURN = ES_RETURN.
          LV_ERROR = ABAP_TRUE.
          EXIT.
        ENDIF.
        IF LS_C5-YCHK_OUTPUT = ABAP_TRUE AND <ZZOUTPUT> IS INITIAL.
          LV_PAR1 = LS_C5-C5_ID.
          CALL FUNCTION 'BALW_BAPIRETURN_GET1'
            EXPORTING
              TYPE       = 'E'
              CL         = 'ZFI'
              NUMBER     = '037'
              PAR1       = LV_PAR1
            IMPORTING
              BAPIRETURN = ES_RETURN.
          LV_ERROR = ABAP_TRUE.
          EXIT.
        ENDIF.
      ENDIF.

      READ TABLE LT_C5_UPD ASSIGNING FIELD-SYMBOL(<LS_C5_UPD>) WITH KEY C5_ID = LS_C5_NEW-C5_ID.
      IF SY-SUBRC = 0.
        "assignment exists
        <LS_C5_UPD>-C5_SEL = LS_C5_NEW-C5_SEL.
        <LS_C5_UPD>-FM_OUTPUT = <ZZOUTPUT>.
      ELSE.
        "assignment doesn't exist
        IF LS_C5_NEW-C5_SEL = ABAP_TRUE.
          "insert the entry
          CLEAR LS_C5_UPD.
          LS_C5_UPD-MANDT = SY-MANDT.
          LS_C5_UPD-FIKRS = IV_FM_AREA.
          LS_C5_UPD-FINCODE = IV_FUND.
          LS_C5_UPD-C5_ID = LS_C5_NEW-C5_ID.
          LS_C5_UPD-C5_SEL = ABAP_TRUE.
          LS_C5_UPD-FM_OUTPUT = <ZZOUTPUT>.
          APPEND LS_C5_UPD TO LT_C5_UPD.
        ENDIF.
      ENDIF.
    ENDLOOP.

    SORT LT_C5_UPD.

    CHECK LV_ERROR = ABAP_FALSE.

    IF LT_C5_UPD = LT_C5_ACT.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'I'
          CL         = 'YFM1'
          NUMBER     = '020'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    CHECK IV_NO_UPDATE = ABAP_FALSE.

    "Lock Fund
    CALL FUNCTION 'ENQUEUE_EFMFINCODE'
      EXPORTING
*       MODE_FMFINCODE = 'E'
*       MANDT          = SY-MANDT
        FIKRS          = IV_FM_AREA
        FINCODE        = IV_FUND
*       X_FIKRS        = ' '
*       X_FINCODE      = ' '
*       _SCOPE         = '2'
*       _WAIT          = ' '
*       _COLLECT       = ' '
      EXCEPTIONS
        FOREIGN_LOCK   = 1
        SYSTEM_FAILURE = 2
        OTHERS         = 3.
    IF SY-SUBRC <> 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'YFM1'
          NUMBER     = '024'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
          PAR3       = SY-MSGV1
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    "Update database
    DO_UPDATE( IT_FUND_C5_OLD = LT_C5_ACT
               IT_FUND_C5_NEW = LT_C5_UPD ).

    "Unlock fund
    CALL FUNCTION 'DEQUEUE_EFMFINCODE'
      EXPORTING
        FIKRS   = IV_FM_AREA
        FINCODE = IV_FUND.

    CALL FUNCTION 'BALW_BAPIRETURN_GET1'
      EXPORTING
        TYPE       = 'I'
        CL         = 'YFM1'
        NUMBER     = '021'
        PAR1       = LV_PAR1
        PAR2       = LV_PAR2
      IMPORTING
        BAPIRETURN = ES_RETURN.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM007 ----
  METHOD UPDATE_FROM_BAPI_V0.

    DATA LV_PAR1 TYPE SYST_MSGV.
    DATA LV_PAR2 TYPE SYST_MSGV.
    DATA LV_PAR3 TYPE SYST_MSGV.
    DATA LT_C5 TYPE TABLE OF YTFM_C5.
    DATA LT_C5_DEL TYPE TABLE OF YTFM_FUND_C5.
    DATA LT_C5_INS TYPE TABLE OF YTFM_FUND_C5.
    DATA LT_C5_ACT TYPE TABLE OF YTFM_FUND_C5.
    DATA LV_BEGBI TYPE DATUM.
    DATA LV_ENDBI TYPE DATUM.
    DATA LV_ERROR TYPE XFELD.
    FIELD-SYMBOLS <ZZOUTPUT> TYPE YE_FM_OUTPUT.

    LV_PAR1 = IV_FM_AREA.
    LV_PAR2 = IV_FUND.

    "Check fund exist
    SELECT SINGLE * FROM FMFINCODE WHERE FIKRS = @IV_FM_AREA
                                   AND   FINCODE = @IV_FUND
                              INTO @DATA(LS_FMFINCODE).
    IF SY-SUBRC <> 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'F6'
          NUMBER     = '069'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    "Get output
    ASSIGN COMPONENT 'ZZOUTPUT' OF STRUCTURE LS_FMFINCODE TO <ZZOUTPUT>.

    "Get actual assignment
    SELECT * FROM YTFM_FUND_C5 WHERE FIKRS = @IV_FM_AREA
                               AND   FINCODE = @IV_FUND
                          INTO TABLE @LT_C5_ACT.

    "Get list of C/5 id with periods
    SELECT * FROM YTFM_C5 INTO TABLE @LT_C5.

    LOOP AT IT_C5_ASSIGNMENT INTO DATA(LS_C5_NEW).

      "Check first if the C5 id exists
      READ TABLE LT_C5 INTO DATA(LS_C5) WITH KEY C5_ID = LS_C5_NEW-C5_ID.
      IF SY-SUBRC <> 0.
        LV_PAR1 = LS_C5_NEW-C5_ID.
        CALL FUNCTION 'BALW_BAPIRETURN_GET1'
          EXPORTING
            TYPE       = 'E'
            CL         = 'YFM1'
            NUMBER     = '023'
            PAR1       = LV_PAR1
          IMPORTING
            BAPIRETURN = ES_RETURN.
        LV_ERROR = ABAP_TRUE.
        EXIT.
      ENDIF.

      "Then check if fund validity is in the c/5
      IF LS_C5_NEW-C5_SEL = ABAP_TRUE.  "C/5 assigned
        LV_BEGBI = |{ LS_C5-YEAR_FROM }0101|.
        LV_ENDBI = |{ LS_C5-YEAR_TO }1231|.
        IF LS_FMFINCODE-DATAB > LV_ENDBI OR LS_FMFINCODE-DATBIS < LV_BEGBI.
          LV_PAR1 = LS_C5_NEW-C5_ID.
          WRITE LS_FMFINCODE-DATAB TO LV_PAR2.
          WRITE LS_FMFINCODE-DATBIS TO LV_PAR3.
          CALL FUNCTION 'BALW_BAPIRETURN_GET1'
            EXPORTING
              TYPE       = 'E'
              CL         = 'YFM1'
              NUMBER     = '022'
              PAR1       = LV_PAR1
              PAR2       = LV_PAR2
              PAR3       = LV_PAR3
            IMPORTING
              BAPIRETURN = ES_RETURN.
          LV_ERROR = ABAP_TRUE.
          EXIT.
        ENDIF.
        IF LS_C5-YCHK_OUTPUT = ABAP_TRUE AND <ZZOUTPUT> IS INITIAL.
          LV_PAR1 = LS_C5-C5_ID.
          CALL FUNCTION 'BALW_BAPIRETURN_GET1'
            EXPORTING
              TYPE       = 'E'
              CL         = 'ZFI'
              NUMBER     = '037'
              PAR1       = LV_PAR1
            IMPORTING
              BAPIRETURN = ES_RETURN.
          LV_ERROR = ABAP_TRUE.
          EXIT.
        ENDIF.
      ENDIF.

      READ TABLE LT_C5_ACT INTO DATA(LS_C5_ACT) WITH KEY C5_ID = LS_C5_NEW-C5_ID.
      IF SY-SUBRC = 0.
        "assignment exists
        IF LS_C5_NEW-C5_SEL = ABAP_FALSE.
          "delete the entry
          APPEND LS_C5_ACT TO LT_C5_DEL.
        ENDIF.
      ELSE.
        "assignment doesn't exist
        IF LS_C5_NEW-C5_SEL = ABAP_TRUE.
          "insert the entry
          LS_C5_ACT-MANDT = SY-MANDT.
          LS_C5_ACT-FIKRS = IV_FM_AREA.
          LS_C5_ACT-FINCODE = IV_FUND.
          LS_C5_ACT-C5_ID = LS_C5_NEW-C5_ID.
          APPEND LS_C5_ACT TO LT_C5_INS.
        ENDIF.
      ENDIF.
    ENDLOOP.

    CHECK LV_ERROR = ABAP_FALSE.

    IF LT_C5_DEL IS INITIAL AND LT_C5_INS IS INITIAL.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'I'
          CL         = 'YFM1'
          NUMBER     = '020'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    "Lock Fund
    CALL FUNCTION 'ENQUEUE_EFMFINCODE'
      EXPORTING
*       MODE_FMFINCODE = 'E'
*       MANDT          = SY-MANDT
        FIKRS          = IV_FM_AREA
        FINCODE        = IV_FUND
*       X_FIKRS        = ' '
*       X_FINCODE      = ' '
*       _SCOPE         = '2'
*       _WAIT          = ' '
*       _COLLECT       = ' '
      EXCEPTIONS
        FOREIGN_LOCK   = 1
        SYSTEM_FAILURE = 2
        OTHERS         = 3.
    IF SY-SUBRC <> 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'YFM1'
          NUMBER     = '024'
          PAR1       = LV_PAR1
          PAR2       = LV_PAR2
          PAR3       = SY-MSGV1
        IMPORTING
          BAPIRETURN = ES_RETURN.
      EXIT.
    ENDIF.

    IF LT_C5_DEL IS NOT INITIAL.
      DELETE YTFM_FUND_C5 FROM TABLE LT_C5_DEL.
    ENDIF.
    IF LT_C5_INS IS NOT INITIAL.
      INSERT YTFM_FUND_C5 FROM TABLE LT_C5_INS.
    ENDIF.

    "Unlock fund
    CALL FUNCTION 'DEQUEUE_EFMFINCODE'
      EXPORTING
        FIKRS   = IV_FM_AREA
        FINCODE = IV_FUND.

    CALL FUNCTION 'BALW_BAPIRETURN_GET1'
      EXPORTING
        TYPE       = 'I'
        CL         = 'YFM1'
        NUMBER     = '021'
        PAR1       = LV_PAR1
        PAR2       = LV_PAR2
      IMPORTING
        BAPIRETURN = ES_RETURN.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM008 ----
  METHOD UPDATE_BAPI_VERSION.

    CHECK IV_MODE_TEST = ABAP_FALSE.
    UPDATE TVARVC SET LOW = IV_VERSION
                  WHERE NAME = 'Y_FM_FUND_C5_BAPI_VERSION'
                  AND   TYPE = 'P'.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CM009 ----
  METHOD GET_BAPI_VERSION.

    CLEAR: EV_VERSION, ES_RETURN.

    SELECT SINGLE LOW FROM TVARVC WHERE NAME = 'Y_FM_FUND_C5_BAPI_VERSION'
                                  AND   TYPE = 'P'
                      INTO @EV_VERSION.
    IF SY-SUBRC <> 0 OR ( EV_VERSION <> 'V0' AND EV_VERSION <> 'V1' AND EV_VERSION <> 'V2' ).
      CALL FUNCTION 'BALW_BAPIRETURN_GET1'
        EXPORTING
          TYPE       = 'E'
          CL         = 'YFM1'
          NUMBER     = '036'
        IMPORTING
          BAPIRETURN = ES_RETURN.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FUND_C5_ACTION=========CO ----
PROTECTED SECTION.

* ---- YCL_FM_FUND_C5_ACTION=========CU ----
CLASS YCL_FM_FUND_C5_ACTION DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  CLASS-METHODS DEQUEUE_FUND
    IMPORTING
      !IV_FIKRS TYPE FIKRS
      !IV_FINCODE TYPE BP_GEBER .
  CLASS-METHODS DO_UPDATE
    IMPORTING
      !IT_FUND_C5_OLD TYPE YTTFM_FUND_C5_DB
      !IT_FUND_C5_NEW TYPE YTTFM_FUND_C5_DB .
  CLASS-METHODS ENQUEUE_FUND
    IMPORTING
      !IV_FIKRS TYPE FIKRS
      !IV_FINCODE TYPE BP_GEBER
    EXPORTING
      !EV_SUBRC TYPE SY-SUBRC
      !ES_RETURN TYPE BAPIRETURN1 .
  CLASS-METHODS GET_BAPI_VERSION
    EXPORTING
      !EV_VERSION TYPE CHAR2
      !ES_RETURN TYPE BAPIRETURN1 .
  CLASS-METHODS UPDATE_BAPI_VERSION
    IMPORTING
      !IV_VERSION TYPE CHAR2
      !IV_MODE_TEST TYPE XFELD .
  CLASS-METHODS UPDATE_FROM_BAPI_V0
    IMPORTING
      !IV_FM_AREA TYPE FIKRS
      !IV_FUND TYPE BP_GEBER
      !IT_C5_ASSIGNMENT TYPE YTTFM_FUND_C5_BAPI
    EXPORTING
      !ES_RETURN TYPE BAPIRETURN1 .
  CLASS-METHODS UPDATE_FROM_BAPI_V1
    IMPORTING
      !IV_FM_AREA TYPE FIKRS
      !IV_FUND TYPE BP_GEBER
      !IT_C5_ASSIGNMENT TYPE YTTFM_FUND_C5_BAPI
      !IV_NO_UPDATE TYPE XFELD DEFAULT SPACE
    EXPORTING
      !ES_RETURN TYPE BAPIRETURN1 .
  CLASS-METHODS UPDATE_FROM_BAPI_V2
    IMPORTING
      !IV_FM_AREA TYPE FIKRS
      !IV_FUND TYPE BP_GEBER
      !IT_C5_ASSIGNMENT TYPE YTTFM_FUND_C5_BAPI
      !IV_NO_UPDATE TYPE XFELD DEFAULT SPACE
    EXPORTING
      !ET_RETURN TYPE FM_T_BAPIRETURN1 .