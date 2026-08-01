*&---------------------------------------------------------------------*
*& Report YFI_OPEN_VENDORS
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_OPEN_VENDORS.

INCLUDE YFI_OPEN_VENDORS_DATA.
INCLUDE YFI_OPEN_VENDORS_SEL.


START-OF-SELECTION.

  GO_OPEN_VENDORS_BL = NEW YCL_FI_OPEN_VENDORS_BL( ).
  "check global authorizations
  GO_OPEN_VENDORS_BL->CHECK_GLOBAL_AUTHORITY( EXPORTING IV_BUKRS = P_BUKRS
                                              EXCEPTIONS NO_AUTHORIZATION = 1 ).
  IF SY-SUBRC <> 0.
    MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    EXIT.
  ENDIF.
  "Amounts filter
  IF P_ONLY_0 = ABAP_TRUE.
    GV_AMOUNT_FILTER = 'Z'.
  ELSEIF P_NON_0 = ABAP_TRUE.
    GV_AMOUNT_FILTER = 'N'.
  ELSE.
    GV_AMOUNT_FILTER = 'A'.
  ENDIF.
  "Do total or not
  IF P_NOTOT = ABAP_TRUE.
    GV_DO_TOTAL = ABAP_FALSE.
  ELSE.
    GV_DO_TOTAL = ABAP_TRUE.
  ENDIF.
  "Set selection criteria
  GO_OPEN_VENDORS_BL->SET_SELECTION_VALUES( IV_SELNAME = 'P_BUKRS' IV_KIND = 'P' IV_VALUE = P_BUKRS ).
  GO_OPEN_VENDORS_BL->SET_SELECTION_VALUES( IV_SELNAME = 'S_LIFNR' IV_KIND = 'S' IT_VALUE = S_LIFNR[] ).
  "Get data
  GO_OPEN_VENDORS_BL->GET_DATA( IV_DATE = P_DATE
                                IV_AMOUNT_FILTER = GV_AMOUNT_FILTER
                                IV_DO_TOTAL = GV_DO_TOTAL ).
  "Display ALV list
  GO_OPEN_VENDORS_BL->DISPLAY_ALV( SY-REPID ).