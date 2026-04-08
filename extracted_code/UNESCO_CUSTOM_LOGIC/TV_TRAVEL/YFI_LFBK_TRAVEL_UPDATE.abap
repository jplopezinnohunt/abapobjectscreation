*&---------------------------------------------------------------------*
*& Report YFI_LFBK_TRAVEL_UPDATE
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT yfi_lfbk_travel_update.

TYPES: BEGIN OF ty_country_ref,
         land1       TYPE land1,
         iban_length TYPE iban_length,
       END OF ty_country_ref.

TYPES: BEGIN OF ty_data,
         lifnr      TYPE lfa1-lifnr,
         ktokk      TYPE lfa1-ktokk,
         banks      TYPE lfbk-banks,
         bankl      TYPE lfbk-bankl,
         bankn      TYPE lfbk-bankn,
         bkont      TYPE lfbk-bkont,
         bkref      TYPE lfbk-bkref,
         yytravel   TYPE lfbk-yytravel,
         flag_bkref TYPE flag_bkref,
         iban_txt   TYPE text30,
         status     TYPE p_99s_statu,
         message    TYPE bapi_msg,
       END OF ty_data.

DATA gs_lfa1 TYPE lfa1.
DATA gt_data TYPE TABLE OF ty_data.
DATA gt_country_ref TYPE TABLE OF ty_country_ref.
DATA go_alv TYPE REF TO ycl_alv.


SELECTION-SCREEN BEGIN OF BLOCK b01 WITH FRAME TITLE TEXT-b01.
SELECT-OPTIONS s_lifnr FOR gs_lfa1-lifnr.
SELECT-OPTIONS s_ktokk FOR gs_lfa1-ktokk NO INTERVALS.
SELECTION-SCREEN END OF BLOCK b01.
SELECTION-SCREEN BEGIN OF BLOCK b02 WITH FRAME TITLE TEXT-b02.
PARAMETERS p_set RADIOBUTTON GROUP r001 DEFAULT 'X'.
PARAMETERS p_del RADIOBUTTON GROUP r001.
PARAMETERS p_update AS CHECKBOX.
SELECTION-SCREEN END OF BLOCK b02.

INITIALIZATION.
  APPEND VALUE #( sign = 'I' option = 'BT' low = '0010000000' high = '0010199999' ) TO s_lifnr.

START-OF-SELECTION.

  "Get list of vendor
  SELECT k~lifnr,
         a~ktokk,
         k~banks,
         k~bankl,
         k~bankn,
         k~bkont,
         k~bkref,
         k~yytravel
         FROM lfbk AS k
         INNER JOIN lfa1 AS a ON a~lifnr = k~lifnr
         WHERE k~bkref = 'TRAVEL'
         AND   a~lifnr IN @s_lifnr
         AND   a~ktokk IN @s_ktokk
         INTO TABLE @gt_data.

  "Get countries with reference details
  SELECT a~land1,
         c~iban_length
         FROM t005 AS a
         INNER JOIN t521a AS b ON b~landk = a~landk
         LEFT OUTER JOIN t005sepa AS c ON c~land1 = a~land1
         WHERE b~flag_bkref = @abap_true
         INTO TABLE @gt_country_ref.

  LOOP AT gt_data ASSIGNING FIELD-SYMBOL(<ls_data>).
    "Complete data
    READ TABLE gt_country_ref INTO DATA(ls_country_ref) WITH KEY land1 = <ls_data>-banks.
    IF sy-subrc = 0.
      <ls_data>-flag_bkref = abap_true.
      IF ls_country_ref-iban_length IS NOT INITIAL.
        "Check IBAN
        SELECT SINGLE iban INTO @DATA(lv_iban) FROM tiban WHERE banks = @<ls_data>-banks
                                                          AND   bankl = @<ls_data>-bankl
                                                          AND   bankn = @<ls_data>-bankn
                                                          AND   bkont = @<ls_data>-bkont.
        IF sy-subrc <> 0.
          <ls_data>-iban_txt = 'IBAN to re-generate'.
        ENDIF.
      ENDIF.
    ENDIF.
    CASE abap_true.
      WHEN p_set.
        IF <ls_data>-yytravel = abap_true.
          WRITE icon_led_inactive TO <ls_data>-status AS ICON.
          <ls_data>-message = 'Travel flag already set'.
          CONTINUE.
        ENDIF.
        IF p_update = abap_true.
          UPDATE lfbk SET yytravel = abap_true
                      WHERE lifnr = <ls_data>-lifnr
                      AND   banks = <ls_data>-banks
                      AND   bankl = <ls_data>-bankl
                      AND   bankn = <ls_data>-bankn.
          IF sy-subrc = 0.
            WRITE icon_led_green TO <ls_data>-status AS ICON.
            <ls_data>-message = 'Travel flag has been set'.
            <ls_data>-yytravel = abap_true.
          ELSE.
            WRITE icon_led_red TO <ls_data>-status AS ICON.
            <ls_data>-message = 'Unable to update travel flag'.
          ENDIF.
        ELSE.
          WRITE icon_led_yellow TO <ls_data>-status AS ICON.
          <ls_data>-message = 'Travel flag can be set'.
        ENDIF.
      WHEN p_del.
        IF <ls_data>-bkref = 'TRAVEL' AND <ls_data>-yytravel = abap_false.
          WRITE icon_led_red TO <ls_data>-status AS ICON.
          <ls_data>-message = 'Travel flag is not set'.
          CONTINUE.
        ENDIF.
        IF p_update = abap_true.
          UPDATE lfbk SET bkref = space
                      WHERE lifnr = <ls_data>-lifnr
                      AND   banks = <ls_data>-banks
                      AND   bankl = <ls_data>-bankl
                      AND   bankn = <ls_data>-bankn.
          IF sy-subrc = 0.
            WRITE icon_led_green TO <ls_data>-status AS ICON.
            <ls_data>-message = 'Reference details has been set to blank'.
            <ls_data>-bkref = space.
          ELSE.
            WRITE icon_led_red TO <ls_data>-status AS ICON.
            <ls_data>-message = 'Unable to update reference details'.
          ENDIF.
        ELSE.
          WRITE icon_led_yellow TO <ls_data>-status AS ICON.
          <ls_data>-message = 'Reference details can be set to blank'.
        ENDIF.
    ENDCASE.
  ENDLOOP.

  "Display ALV
  go_alv = NEW ycl_alv( ).
  go_alv->yif_alv_display~init_alv( CHANGING it_table = gt_data ).
  go_alv->yif_alv_display~set_main_functions( sy-repid ).
  go_alv->yif_alv_display~display_alv( ).
