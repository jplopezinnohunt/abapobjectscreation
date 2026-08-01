* ==== CLASS POOL YCL_FM_FUND_OUTPUT_MIGRATION ====
CLASS-POOL .
*"* class pool for class YCL_FM_FUND_OUTPUT_MIGRATION

*"* local type definitions
INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CCDEF.

*"* class YCL_FM_FUND_OUTPUT_MIGRATION definition
*"* public declarations
  INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CU.
*"* protected declarations
  INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CO.
*"* private declarations
  INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CI.
ENDCLASS. "YCL_FM_FUND_OUTPUT_MIGRATION definition

*"* macro definitions
INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CCMAC.
*"* local class implementation
INCLUDE YCL_FM_FUND_OUTPUT_MIGRATION==CCIMP.

CLASS YCL_FM_FUND_OUTPUT_MIGRATION IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_FUND_OUTPUT_MIGRATION implementation


* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CI ----
PRIVATE SECTION.

  TYPES:
    BEGIN OF TY_FUND,
      FIKRS      TYPE FMFINCODE-FIKRS,
      FINCODE    TYPE FMFINCODE-FINCODE,
      DATAB      TYPE FMFINCODE-DATAB,
      DATBIS     TYPE FMFINCODE-DATBIS,
      TYPE       TYPE FMFINCODE-TYPE,
      ZZIBF_TYPE TYPE FMFUNDTYPE-ZZIBF,
      ZZOUTPUT   TYPE YE_FM_OUTPUT,
    END OF TY_FUND .
  TYPES:
    BEGIN OF TY_LIST.
      INCLUDE TYPE TY_FUND.
      TYPES: C5_ID     TYPE	YE_FM_C5_ID,
      C5_SEL    TYPE YE_FM_C5_CONTRIBUTION,
      FM_OUTPUT TYPE  YE_FM_OUTPUT,
      STATUS    TYPE  P_99S_STATU,
      MESSAGE   TYPE BAPIRETURN1-MESSAGE,
    END OF TY_LIST .

  DATA MV_DATAB TYPE FM_DATAB .
  DATA MV_DATBIS TYPE FM_DATBIS .
  DATA:
    MT_FUND TYPE TABLE OF TY_FUND .
  DATA:
    MT_LIST TYPE TABLE OF TY_LIST .

  METHODS CALL_CONVERSION_RULE
    IMPORTING
      !IV_FIKRS TYPE FIKRS
      !IV_FINCODE TYPE BP_GEBER
      !IV_OUTPUT TYPE YE_FM_OUTPUT
      !IV_DATAB TYPE FM_DATAB
      !IV_DATBIS TYPE FM_DATBIS
    EXPORTING
      !EV_SUBRC TYPE SY-SUBRC
      !EV_MESSAGE TYPE BAPI_MSG
    CHANGING
      !CS_41 TYPE YTFM_FUND_C5
      !CS_42 TYPE YTFM_FUND_C5 .
  METHODS READ_DATA_FROM_DB .

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM001 ----
  METHOD GET_DATA.

    MV_DATAB = IV_DATAB.
    MV_DATBIS = IV_DATBIS.

    "Read data from database
    ME->READ_DATA_FROM_DB( ).

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM002 ----
  METHOD READ_DATA_FROM_DB.

    CONSTANTS LC_INITIAL_OUTPUT TYPE YE_FM_OUTPUT VALUE 0.

    CLEAR: MT_FUND.

    SELECT A~FIKRS,
           A~FINCODE,
           A~DATAB,
           A~DATBIS,
           A~TYPE,
           T~ZZIBF AS ZZIBF_TYPE,
           A~ZZOUTPUT
           FROM FMFINCODE AS A
           LEFT OUTER JOIN FMFUNDTYPE AS T ON  T~FM_AREA = A~FIKRS
                                           AND T~FUND_TYPE = A~TYPE
           WHERE A~FIKRS IN @MR_FIKRS
           AND   A~FINCODE IN @MR_FUND
           AND   A~DATAB <= @MV_DATBIS
           AND   A~DATBIS >= @MV_DATAB
           AND   A~TYPE IN @MR_TYPE
           "AND   a~zzoutput <> @lc_initial_output
           INTO TABLE @MT_FUND.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM003 ----
  METHOD INIT_ALV.

    SUPER->INIT_ALV( EXPORTING IV_REPID = IV_REPID
                     CHANGING  CT_TABLE = MT_LIST ).

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM004 ----
  METHOD SET_ALV_COLUMNS.

    DATA LS_COLOR TYPE LVC_S_COLO.
    DATA LO_COLUMN TYPE REF TO CL_SALV_COLUMN_TABLE.

    SUPER->SET_ALV_COLUMNS( ).

    LS_COLOR-COL = COL_HEADING.
    LS_COLOR-INT = 1.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'FIKRS' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'FINCODE' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'DATAB' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'DATBIS' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'TYPE' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'ZZIBF_TYPE' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'ZZOUTPUT' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    LS_COLOR-COL = COL_GROUP.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'C5_ID' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'C5_SEL' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

    TRY.
        LO_COLUMN ?= MO_SALV_COLUMNS_TABLE->GET_COLUMN( 'FM_OUTPUT' ).
        LO_COLUMN->SET_COLOR( LS_COLOR ).
      CATCH CX_SALV_NOT_FOUND.
    ENDTRY.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM005 ----
  METHOD UPDATE_DATA.

    DATA LT_FUND_C5 TYPE TABLE OF YTFM_FUND_C5.
    DATA LT_FUND_C5_O TYPE TABLE OF YTFM_FUND_C5.
    DATA LS_FUND_C5  TYPE YTFM_FUND_C5.
    DATA LS_RETURN TYPE BAPIRETURN1.
    DATA LS_LIST TYPE TY_LIST.
    DATA LV_INDEX TYPE SY-INDEX.
    DATA LV_SUBRC TYPE SY-SUBRC.
    DATA LV_TABIX_41 TYPE SY-TABIX.
    DATA LV_TABIX_42 TYPE SY-TABIX.

    IF IV_WITH_BACKUP = ABAP_TRUE.
      IV_MODE_TEST = ABAP_TRUE.
    ENDIF.

    LOOP AT MT_FUND INTO DATA(LS_FUND).

      CLEAR LS_RETURN.

      "Get C/5 assignment for fund
      CLEAR LT_FUND_C5.
      SELECT * FROM YTFM_FUND_C5 WHERE FIKRS = @LS_FUND-FIKRS
                                 AND   FINCODE = @LS_FUND-FINCODE
                      INTO TABLE @LT_FUND_C5.
      IF SY-SUBRC <> 0 AND LS_FUND-ZZOUTPUT IS INITIAL.
        "No output and no assignment to C/5: nothing to do
        CONTINUE.
      ENDIF.

      LT_FUND_C5_O = LT_FUND_C5.

      IF IV_WITH_BACKUP = ABAP_TRUE.
        CLEAR LT_FUND_C5.
        SELECT * FROM YTFM_FUND_C5_BCK WHERE FIKRS = @LS_FUND-FIKRS
                                       AND   FINCODE = @LS_FUND-FINCODE
                     INTO TABLE @LT_FUND_C5.
      ENDIF.

      "Get 41 C/5 line
      READ TABLE LT_FUND_C5 INTO DATA(LS_FUND_41) WITH KEY C5_ID = '41'.
      IF SY-SUBRC <> 0.
        CLEAR: LS_FUND_41, LV_TABIX_41.
      ELSE.
        LV_TABIX_41 = SY-TABIX.
      ENDIF.

      "Get 42 C/5 line
      READ TABLE LT_FUND_C5 INTO DATA(LS_FUND_42) WITH KEY C5_ID = '42'.
      IF SY-SUBRC <> 0.
        CLEAR: LS_FUND_42, LV_TABIX_42.
      ELSE.
        LV_TABIX_42 = SY-TABIX.
      ENDIF.

      ME->CALL_CONVERSION_RULE( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                          IV_FINCODE = LS_FUND-FINCODE
                                          IV_OUTPUT = LS_FUND-ZZOUTPUT
                                          IV_DATAB = LS_FUND-DATAB
                                          IV_DATBIS = LS_FUND-DATBIS
                                IMPORTING EV_SUBRC = LV_SUBRC
                                          EV_MESSAGE = LS_RETURN-MESSAGE
                                CHANGING  CS_41 = LS_FUND_41
                                          CS_42 = LS_FUND_42 ).
      CASE LV_SUBRC.

        WHEN 0.
          IF LS_FUND_41 IS NOT INITIAL.
            IF LV_TABIX_41 <> 0.
              MODIFY LT_FUND_C5 FROM LS_FUND_41 INDEX LV_TABIX_41.
            ELSE.
              APPEND LS_FUND_41 TO LT_FUND_C5.
            ENDIF.
          ENDIF.

          IF LS_FUND_42 IS NOT INITIAL.
            IF LV_TABIX_42 <> 0.
              MODIFY LT_FUND_C5 FROM LS_FUND_42 INDEX LV_TABIX_42.
            ELSE.
              APPEND LS_FUND_42 TO LT_FUND_C5.
            ENDIF.
          ENDIF.

          SORT LT_FUND_C5.

          IF LT_FUND_C5 <> LT_FUND_C5_O.

            IF IV_MODE_TEST = ABAP_FALSE.
              "Lock Fund
              YCL_FM_FUND_C5_ACTION=>ENQUEUE_FUND( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                                             IV_FINCODE = LS_FUND-FINCODE
                                                   IMPORTING EV_SUBRC = LV_SUBRC
                                                             ES_RETURN = LS_RETURN ).
              IF LV_SUBRC = 0.
                "Update database
                YCL_FM_FUND_C5_ACTION=>DO_UPDATE( IT_FUND_C5_OLD = LT_FUND_C5_O
                                                  IT_FUND_C5_NEW = LT_FUND_C5 ).

                "Unlock fund
                YCL_FM_FUND_C5_ACTION=>DEQUEUE_FUND( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                                               IV_FINCODE = LS_FUND-FINCODE ).
              ENDIF.
            ENDIF.

          ELSE.
            LS_RETURN-MESSAGE = 'Already aligned'.
            LS_RETURN-TYPE = 'I'.
          ENDIF.

        WHEN 4.
          LS_RETURN-MESSAGE = 'No conversion case found'.
          LS_RETURN-TYPE = 'W'.

        WHEN OTHERS.
          LS_RETURN-TYPE = 'E'.

      ENDCASE.

      "Append list
      LOOP AT LT_FUND_C5 INTO LS_FUND_C5.
        CLEAR LS_LIST.
        MOVE-CORRESPONDING LS_FUND TO LS_LIST.
        MOVE-CORRESPONDING LS_FUND_C5 TO LS_LIST.
        IF LS_RETURN IS NOT INITIAL.
          LS_LIST-MESSAGE = LS_RETURN-MESSAGE.
          CASE LS_RETURN-TYPE.
            WHEN 'E'.
              WRITE ICON_LED_RED TO LS_LIST-STATUS AS ICON.
            WHEN 'W'.
              WRITE ICON_LED_YELLOW TO LS_LIST-STATUS AS ICON.
            WHEN 'I' OR 'S'.
              WRITE ICON_LED_GREEN TO LS_LIST-STATUS AS ICON.
            WHEN OTHERS.
              CLEAR LS_LIST-STATUS.
          ENDCASE.
        ENDIF.
        APPEND LS_LIST TO MT_LIST.
      ENDLOOP.




*      DO.
*        ADD 1 TO lv_index.
*        READ TABLE lt_fund_c5 INTO ls_fund_c5 INDEX lv_index.
*        IF sy-subrc <> 0.
*          CLEAR ls_fund_c5.
*        ENDIF.
*        MOVE-CORRESPONDING ls_fund_c5 TO ls_list.
*
*        READ TABLE lt_return INTO DATA(ls_return) INDEX lv_index.
*        IF sy-subrc <> 0.
*          CLEAR ls_return.
*        ENDIF.
*        ls_list-message = ls_return-message.
*        CASE ls_return-type.
*          WHEN 'E'.
*            WRITE icon_led_red TO ls_list-status AS ICON.
*          WHEN 'W'.
*            WRITE icon_led_yellow TO ls_list-status AS ICON.
*          WHEN 'I' OR 'S'.
*            WRITE icon_led_green TO ls_list-status AS ICON.
*          WHEN OTHERS.
*            CLEAR ls_list-status.
*        ENDCASE.
*
*        IF ls_fund_c5 IS INITIAL AND ls_return IS INITIAL.
*          EXIT.
*        ELSE.
*          APPEND ls_list TO mt_list.
*        ENDIF.
*
*      ENDDO.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM006 ----
  METHOD CALL_CONVERSION_RULE.

    CLEAR EV_MESSAGE.
    EV_SUBRC = 4.

    IF IV_OUTPUT IS INITIAL.
      IF CS_42 IS NOT INITIAL.
        "Error
        EV_SUBRC = 8.
        EV_MESSAGE = 'No output for fund assigned to 42 C/5'.
      ELSEIF CS_41 IS NOT INITIAL.
        "Case 7
        CS_41-C5_SEL = ABAP_TRUE.
        CLEAR CS_41-FM_OUTPUT.
      ELSE.
        "Case 6: do nothing
      ENDIF.
      EV_SUBRC = 0.
      EXIT.
    ENDIF.

    IF CS_41 IS NOT INITIAL AND CS_42 IS NOT INITIAL.
      "Case 1
      CS_41-FM_OUTPUT = CS_42-FM_OUTPUT = IV_OUTPUT.
      CS_41-C5_SEL = CS_42-C5_SEL = ABAP_TRUE.
      EV_SUBRC = 0.
      EXIT.
    ENDIF.

    IF CS_41 IS INITIAL AND CS_42 IS NOT INITIAL.
      "Case 2 and 3
*      IF iv_datab < '20240101'.
*        cs_41-mandt = sy-mandt.
*        cs_41-fikrs = iv_fikrs.
*        cs_41-fincode = iv_fincode.
*        cs_41-c5_id = '41'.
*        cs_41-fm_output = iv_output.
*        cs_41-c5_sel = abap_false.
*      ENDIF.
      CS_42-FM_OUTPUT = IV_OUTPUT.
      CS_42-C5_SEL = ABAP_TRUE.
      EV_SUBRC = 0.
      EXIT.
    ENDIF.

    IF CS_41 IS NOT INITIAL AND CS_42 IS INITIAL.
      "Case 4 and 5
*      IF iv_datbis >= '20240101'.
*        cs_42-mandt = sy-mandt.
*        cs_42-fikrs = iv_fikrs.
*        cs_42-fincode = iv_fincode.
*        cs_42-c5_id = '42'.
*        cs_42-fm_output = iv_output.
*        cs_42-c5_sel = abap_false.
*      ENDIF.
      CS_41-FM_OUTPUT = IV_OUTPUT.
      CS_41-C5_SEL = ABAP_TRUE.
      EV_SUBRC = 0.
      EXIT.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM007 ----
  METHOD BACKUP_FUND_C5.

    DATA LT_FUND_C5 TYPE TABLE OF YTFM_FUND_C5.
    DATA LV_ANSWER TYPE CHAR1.
    DATA LV_TEXT TYPE STRING.

    SELECT * FROM YTFM_FUND_C5_BCK INTO TABLE @LT_FUND_C5 WHERE FIKRS IN @MR_FIKRS.

    IF LT_FUND_C5 IS NOT INITIAL.
      LV_TEXT = 'Backup already exists. Do you want to overwrite it ?'.
    ELSE.
      LV_TEXT = 'Do you want to backup table YTFM_FUND_C5 ?'.
    ENDIF.

    LV_ANSWER = YCL_CA_UTILITIES=>POPUP_TO_CONFIRM( IV_TITLE = 'Confirm Backup'
                                                    IV_TEXT = LV_TEXT
                                                    IV_CANCEL_BUTTON = ABAP_TRUE ).
    IF LV_ANSWER = '1'.  "Yes
      CLEAR LT_FUND_C5.
      SELECT * FROM YTFM_FUND_C5 INTO TABLE @LT_FUND_C5 WHERE FIKRS IN @MR_FIKRS.
      DATA(LV_LINES) = LINES( LT_FUND_C5 ).
      IF IV_MODE_TEST = ABAP_TRUE.
        LV_TEXT = |{ LV_LINES } entries to backup. Test mode: nothing done|.
      ELSE.
        DELETE FROM YTFM_FUND_C5_BCK WHERE FIKRS IN @MR_FIKRS.
        INSERT YTFM_FUND_C5_BCK FROM TABLE LT_FUND_C5.
        IF SY-SUBRC = 0.
          LV_TEXT = |{ LV_LINES } entries saved in backup table YTFM_FUND_C5_BCK|.
        ELSE.
          LV_TEXT = 'Error during backup'.
        ENDIF.
      ENDIF.
    ELSE.
      LV_TEXT = 'Action cancelled'.
    ENDIF.

    MESSAGE LV_TEXT TYPE 'I'.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM008 ----
  METHOD BACKUP_FUND_OUTPUT.

    CONSTANTS LC_INITIAL_OUTPUT TYPE YE_FM_OUTPUT VALUE 0.
    DATA LT_DATA TYPE TABLE OF YTFM_FUND_O_BCK.
    DATA LV_ANSWER TYPE CHAR1.
    DATA LV_TEXT TYPE STRING.

    SELECT * FROM YTFM_FUND_O_BCK WHERE FIKRS IN @MR_FIKRS
             INTO TABLE @LT_DATA.

    IF LT_DATA IS NOT INITIAL.
      LV_TEXT = 'Backup already exists. Do you want to overwrite it ?'.
    ELSE.
      LV_TEXT = 'Do you want to backup fund - output ?'.
    ENDIF.

    LV_ANSWER = YCL_CA_UTILITIES=>POPUP_TO_CONFIRM( IV_TITLE = 'Confirm Backup'
                                                    IV_TEXT = LV_TEXT
                                                    IV_CANCEL_BUTTON = ABAP_TRUE ).
    IF LV_ANSWER = '1'.  "Yes
      CLEAR LT_DATA.
      SELECT MANDT, FIKRS, FINCODE, ZZOUTPUT AS FM_OUTPUT FROM FMFINCODE
                                                          WHERE FIKRS IN @MR_FIKRS
                                                          AND   ZZOUTPUT <> @LC_INITIAL_OUTPUT
             INTO TABLE @LT_DATA.
      DATA(LV_LINES) = LINES( LT_DATA ).
      IF IV_MODE_TEST = ABAP_TRUE.
        LV_TEXT = |{ LV_LINES } entries to backup. Test mode: nothing done|.
      ELSE.
        DELETE FROM YTFM_FUND_O_BCK WHERE FIKRS IN @MR_FIKRS.
        INSERT YTFM_FUND_O_BCK FROM TABLE LT_DATA.
        IF SY-SUBRC = 0.
          LV_TEXT = |{ LV_LINES } entries saved in backup table YTFM_FUND_O_BCK|.
        ELSE.
          LV_TEXT = 'Error during backup'.
        ENDIF.
      ENDIF.
    ELSE.
      LV_TEXT = 'Action cancelled'.
    ENDIF.

    MESSAGE LV_TEXT TYPE 'I'.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CM009 ----
  METHOD UPDATE_DATA_ADD.

    DATA LT_FUND_C5 TYPE TABLE OF YTFM_FUND_C5.
    DATA LT_OLD TYPE TABLE OF YTFM_FUND_C5.
    DATA LT_NEW TYPE TABLE OF YTFM_FUND_C5.
    DATA LS_RETURN TYPE BAPIRETURN1.
    DATA LV_SUBRC TYPE SY-SUBRC.
    DATA LS_LIST TYPE TY_LIST.

    CHECK MT_FUND IS NOT INITIAL.

    SELECT * FROM YTFM_FUND_C5 FOR ALL ENTRIES IN @MT_FUND
                            WHERE FIKRS = @MT_FUND-FIKRS
                            AND   FINCODE = @MT_FUND-FINCODE
                            AND   C5_ID = @IV_C5_ID
             INTO TABLE @LT_FUND_C5.

    LOOP AT MT_FUND INTO DATA(LS_FUND) WHERE ZZOUTPUT IS NOT INITIAL.

      CLEAR: LS_LIST, LT_OLD, LT_NEW.
      MOVE-CORRESPONDING LS_FUND TO LS_LIST.

      READ TABLE LT_FUND_C5 INTO DATA(LS_FUND_C5) WITH KEY FIKRS = LS_FUND-FIKRS
                                                           FINCODE = LS_FUND-FINCODE.
      IF SY-SUBRC = 0.
        IF LS_FUND_C5-C5_SEL = IV_C5_SEL AND LS_FUND_C5-FM_OUTPUT = LS_FUND-ZZOUTPUT.  "Already updated
          "Nothing to do
          WRITE ICON_LED_INACTIVE TO LS_LIST-STATUS AS ICON.
          LS_LIST-MESSAGE = 'Already updated'.
        ELSE.
          APPEND LS_FUND_C5 TO LT_OLD.
          LS_FUND_C5-C5_SEL = IV_C5_SEL.
          LS_FUND_C5-FM_OUTPUT = LS_FUND-ZZOUTPUT.
          APPEND LS_FUND_C5 TO LT_NEW.
        ENDIF.
      ELSE.
        CLEAR LS_FUND_C5.
        LS_FUND_C5-MANDT = SY-MANDT.
        LS_FUND_C5-FIKRS = LS_FUND-FIKRS.
        LS_FUND_C5-FINCODE = LS_FUND-FINCODE.
        LS_FUND_C5-C5_ID = IV_C5_ID.
        LS_FUND_C5-C5_SEL = IV_C5_SEL.
        LS_FUND_C5-FM_OUTPUT = LS_FUND-ZZOUTPUT.
        APPEND LS_FUND_C5 TO LT_NEW.
      ENDIF.

      IF LT_NEW IS NOT INITIAL.
        IF IV_MODE_TEST = ABAP_FALSE.
          YCL_FM_FUND_C5_ACTION=>ENQUEUE_FUND( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                                         IV_FINCODE = LS_FUND-FINCODE
                                               IMPORTING EV_SUBRC = LV_SUBRC
                                                         ES_RETURN = LS_RETURN ).
          IF LV_SUBRC = 0.
            "Update database
            YCL_FM_FUND_C5_ACTION=>DO_UPDATE( IT_FUND_C5_OLD = LT_OLD
                                              IT_FUND_C5_NEW = LT_NEW ).

            "Unlock fund
            YCL_FM_FUND_C5_ACTION=>DEQUEUE_FUND( EXPORTING IV_FIKRS = LS_FUND-FIKRS
                                                           IV_FINCODE = LS_FUND-FINCODE ).
            WRITE ICON_LED_GREEN TO LS_LIST-STATUS AS ICON.
            LS_LIST-MESSAGE = 'Update done'.
          ELSE.
            WRITE ICON_LED_RED TO LS_LIST-STATUS AS ICON.
            LS_LIST-MESSAGE = LS_RETURN-MESSAGE.
          ENDIF.
        ELSE.
          WRITE ICON_LED_YELLOW TO LS_LIST-STATUS AS ICON.
          LS_LIST-MESSAGE = 'Data can be updated'.
        ENDIF.
      ENDIF.

      MOVE-CORRESPONDING LS_FUND_C5 TO LS_LIST.
      APPEND LS_LIST TO MT_LIST.

    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CO ----
PROTECTED SECTION.

  METHODS SET_ALV_COLUMNS
    REDEFINITION .

* ---- YCL_FM_FUND_OUTPUT_MIGRATION==CU ----
CLASS YCL_FM_FUND_OUTPUT_MIGRATION DEFINITION
  PUBLIC
  INHERITING FROM YCL_CA_REPORT_SHARE_STATEMENTS
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  DATA MR_FUND TYPE YTT_RANGE_FINCODE .
  DATA:
    MR_FIKRS TYPE RANGE OF FIKRS .
  DATA:
    MR_TYPE TYPE RANGE OF FM_FUNDTYPE .

  METHODS UPDATE_DATA_ADD
    IMPORTING
      !IV_C5_ID TYPE YE_FM_C5_ID
      !IV_C5_SEL TYPE YE_FM_C5_CONTRIBUTION
      !IV_MODE_TEST TYPE XFELD .
  METHODS BACKUP_FUND_C5
    IMPORTING
      !IV_MODE_TEST TYPE XFELD .
  METHODS BACKUP_FUND_OUTPUT
    IMPORTING
      !IV_MODE_TEST TYPE XFELD DEFAULT ABAP_TRUE .
  METHODS GET_DATA
    IMPORTING
      !IV_DATAB TYPE FM_DATAB
      !IV_DATBIS TYPE FM_DATBIS .
  METHODS UPDATE_DATA
    IMPORTING
      VALUE(IV_MODE_TEST) TYPE XFELD DEFAULT ABAP_TRUE
      VALUE(IV_WITH_BACKUP) TYPE XFELD DEFAULT ABAP_FALSE .

  METHODS INIT_ALV
    REDEFINITION .