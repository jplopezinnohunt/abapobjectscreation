*&---------------------------------------------------------------------*
*& Report YFI_LFBK_TRAVEL_UPDATE
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_LFBK_TRAVEL_UPDATE.

TYPES: BEGIN OF TY_COUNTRY_REF,
         LAND1       TYPE LAND1,
         IBAN_LENGTH TYPE IBAN_LENGTH,
       END OF TY_COUNTRY_REF.

TYPES: BEGIN OF TY_DATA,
         LIFNR      TYPE LFA1-LIFNR,
         KTOKK      TYPE LFA1-KTOKK,
         BANKS      TYPE LFBK-BANKS,
         BANKL      TYPE LFBK-BANKL,
         BANKN      TYPE LFBK-BANKN,
         BKONT      TYPE LFBK-BKONT,
         BKREF      TYPE LFBK-BKREF,
         YYTRAVEL   TYPE LFBK-YYTRAVEL,
         FLAG_BKREF TYPE FLAG_BKREF,
         IBAN_TXT   TYPE TEXT30,
         STATUS     TYPE P_99S_STATU,
         MESSAGE    TYPE BAPI_MSG,
       END OF TY_DATA.

DATA GS_LFA1 TYPE LFA1.
DATA GT_DATA TYPE TABLE OF TY_DATA.
DATA GT_COUNTRY_REF TYPE TABLE OF TY_COUNTRY_REF.
DATA GO_ALV TYPE REF TO YCL_ALV.


SELECTION-SCREEN BEGIN OF BLOCK B01 WITH FRAME TITLE TEXT-B01.
SELECT-OPTIONS S_LIFNR FOR GS_LFA1-LIFNR.
SELECT-OPTIONS S_KTOKK FOR GS_LFA1-KTOKK NO INTERVALS.
SELECTION-SCREEN END OF BLOCK B01.
SELECTION-SCREEN BEGIN OF BLOCK B02 WITH FRAME TITLE TEXT-B02.
PARAMETERS P_SET RADIOBUTTON GROUP R001 DEFAULT 'X'.
PARAMETERS P_DEL RADIOBUTTON GROUP R001.
PARAMETERS P_UPDATE AS CHECKBOX.
SELECTION-SCREEN END OF BLOCK B02.

INITIALIZATION.
  APPEND VALUE #( SIGN = 'I' OPTION = 'BT' LOW = '0010000000' HIGH = '0010199999' ) TO S_LIFNR.

START-OF-SELECTION.

  "Get list of vendor
  SELECT K~LIFNR,
         A~KTOKK,
         K~BANKS,
         K~BANKL,
         K~BANKN,
         K~BKONT,
         K~BKREF,
         K~YYTRAVEL
         FROM LFBK AS K
         INNER JOIN LFA1 AS A ON A~LIFNR = K~LIFNR
         WHERE K~BKREF = 'TRAVEL'
         AND   A~LIFNR IN @S_LIFNR
         AND   A~KTOKK IN @S_KTOKK
         INTO TABLE @GT_DATA.

  "Get countries with reference details
  SELECT A~LAND1,
         C~IBAN_LENGTH
         FROM T005 AS A
         INNER JOIN T521A AS B ON B~LANDK = A~LANDK
         LEFT OUTER JOIN T005SEPA AS C ON C~LAND1 = A~LAND1
         WHERE B~FLAG_BKREF = @ABAP_TRUE
         INTO TABLE @GT_COUNTRY_REF.

  LOOP AT GT_DATA ASSIGNING FIELD-SYMBOL(<LS_DATA>).
    "Complete data
    READ TABLE GT_COUNTRY_REF INTO DATA(LS_COUNTRY_REF) WITH KEY LAND1 = <LS_DATA>-BANKS.
    IF SY-SUBRC = 0.
      <LS_DATA>-FLAG_BKREF = ABAP_TRUE.
      IF LS_COUNTRY_REF-IBAN_LENGTH IS NOT INITIAL.
        "Check IBAN
        SELECT SINGLE IBAN INTO @DATA(LV_IBAN) FROM TIBAN WHERE BANKS = @<LS_DATA>-BANKS
                                                          AND   BANKL = @<LS_DATA>-BANKL
                                                          AND   BANKN = @<LS_DATA>-BANKN
                                                          AND   BKONT = @<LS_DATA>-BKONT.
        IF SY-SUBRC <> 0.
          <LS_DATA>-IBAN_TXT = 'IBAN to re-generate'.
        ENDIF.
      ENDIF.
    ENDIF.
    CASE ABAP_TRUE.
      WHEN P_SET.
        IF <LS_DATA>-YYTRAVEL = ABAP_TRUE.
          WRITE ICON_LED_INACTIVE TO <LS_DATA>-STATUS AS ICON.
          <LS_DATA>-MESSAGE = 'Travel flag already set'.
          CONTINUE.
        ENDIF.
        IF P_UPDATE = ABAP_TRUE.
          UPDATE LFBK SET YYTRAVEL = ABAP_TRUE
                      WHERE LIFNR = <LS_DATA>-LIFNR
                      AND   BANKS = <LS_DATA>-BANKS
                      AND   BANKL = <LS_DATA>-BANKL
                      AND   BANKN = <LS_DATA>-BANKN.
          IF SY-SUBRC = 0.
            WRITE ICON_LED_GREEN TO <LS_DATA>-STATUS AS ICON.
            <LS_DATA>-MESSAGE = 'Travel flag has been set'.
            <LS_DATA>-YYTRAVEL = ABAP_TRUE.
          ELSE.
            WRITE ICON_LED_RED TO <LS_DATA>-STATUS AS ICON.
            <LS_DATA>-MESSAGE = 'Unable to update travel flag'.
          ENDIF.
        ELSE.
          WRITE ICON_LED_YELLOW TO <LS_DATA>-STATUS AS ICON.
          <LS_DATA>-MESSAGE = 'Travel flag can be set'.
        ENDIF.
      WHEN P_DEL.
        IF <LS_DATA>-BKREF = 'TRAVEL' AND <LS_DATA>-YYTRAVEL = ABAP_FALSE.
          WRITE ICON_LED_RED TO <LS_DATA>-STATUS AS ICON.
          <LS_DATA>-MESSAGE = 'Travel flag is not set'.
          CONTINUE.
        ENDIF.
        IF P_UPDATE = ABAP_TRUE.
          UPDATE LFBK SET BKREF = SPACE
                      WHERE LIFNR = <LS_DATA>-LIFNR
                      AND   BANKS = <LS_DATA>-BANKS
                      AND   BANKL = <LS_DATA>-BANKL
                      AND   BANKN = <LS_DATA>-BANKN.
          IF SY-SUBRC = 0.
            WRITE ICON_LED_GREEN TO <LS_DATA>-STATUS AS ICON.
            <LS_DATA>-MESSAGE = 'Reference details has been set to blank'.
            <LS_DATA>-BKREF = SPACE.
          ELSE.
            WRITE ICON_LED_RED TO <LS_DATA>-STATUS AS ICON.
            <LS_DATA>-MESSAGE = 'Unable to update reference details'.
          ENDIF.
        ELSE.
          WRITE ICON_LED_YELLOW TO <LS_DATA>-STATUS AS ICON.
          <LS_DATA>-MESSAGE = 'Reference details can be set to blank'.
        ENDIF.
    ENDCASE.
  ENDLOOP.

  "Display ALV
  GO_ALV = NEW YCL_ALV( ).
  GO_ALV->YIF_ALV_DISPLAY~INIT_ALV( CHANGING IT_TABLE = GT_DATA ).
  GO_ALV->YIF_ALV_DISPLAY~SET_MAIN_FUNCTIONS( SY-REPID ).
  GO_ALV->YIF_ALV_DISPLAY~DISPLAY_ALV( ).