*&---------------------------------------------------------------------*
*& Report YFI_COUPA_POSTING_FILE_MAIL
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_COUPA_POSTING_FILE_MAIL.

TYPES: BEGIN OF TY_APKEY,
         APPL_KEY TYPE YTBC_APPL_FUP-APPL_KEY,
         FILENAME TYPE YTBC_APPL_FUP-FILENAME,
       END OF TY_APKEY.

DATA GT_APKEY TYPE TABLE OF TY_APKEY.

DATA GS_FUP TYPE YTBC_APPL_FUP.
DATA GO_COUPA_ACCOUNTING_DIS TYPE REF TO YCL_FI_COUPA_ACCOUNTING_DIS.
DATA GV_EMAIL TYPE YE_EMAIL.
DATA GT_EMAIL TYPE TABLE OF YE_EMAIL.


SELECT-OPTIONS S_APKEY FOR GS_FUP-APPL_KEY.
SELECT-OPTIONS S_MAIL FOR GV_EMAIL NO INTERVALS.
PARAMETERS P_ERROR AS CHECKBOX DEFAULT 'X'.

INITIALIZATION.
  SELECT APPL_KEY, FILENAME FROM YTBC_APPL_FUP WHERE YAPPL = @YIF_FI_COUPA_ACCOUNTING=>C_APPL_COUPA INTO TABLE @GT_APKEY.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR S_APKEY-LOW.
  YCL_CA_UTILITIES=>VALUE_REQUEST_POPUP( EXPORTING IV_RETFIELD = 'APPL_KEY'
                                                   IV_REPID = SY-REPID
                                                   IV_DYNPRO = SY-DYNNR
                                                   IV_DYNPROFIELD = 'S_APKEY-LOW'
                                                   IT_VALUE_TAB = GT_APKEY ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR S_APKEY-HIGH.
  YCL_CA_UTILITIES=>VALUE_REQUEST_POPUP( EXPORTING IV_RETFIELD = 'APPL_KEY'
                                                   IV_REPID = SY-REPID
                                                   IV_DYNPRO = SY-DYNNR
                                                   IV_DYNPROFIELD = 'S_APKEY-HIGH'
                                                   IT_VALUE_TAB = GT_APKEY ).

START-OF-SELECTION.

  CHECK S_APKEY[] IS NOT INITIAL.

  GO_COUPA_ACCOUNTING_DIS = NEW YCL_FI_COUPA_ACCOUNTING_DIS( ).
  GO_COUPA_ACCOUNTING_DIS->GET_DATA( IV_APPL = YIF_FI_COUPA_ACCOUNTING=>C_APPL_COUPA
                                     IT_APPL_KEY = S_APKEY[] ).
  CHECK S_MAIL[] IS NOT INITIAL.
  LOOP AT S_MAIL.
    APPEND S_MAIL-LOW TO GT_EMAIL.
  ENDLOOP.
  GO_COUPA_ACCOUNTING_DIS->PREPARE_AND_SEND_MAIL( IT_MAIL_ADDRESS = GT_EMAIL
                                                  IV_ONLY_ERROR = P_ERROR ).