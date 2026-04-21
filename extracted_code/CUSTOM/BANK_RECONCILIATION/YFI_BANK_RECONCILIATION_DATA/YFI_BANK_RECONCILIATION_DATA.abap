*&---------------------------------------------------------------------*
*&  Include           YFI_BANK_RECONCILIATION_DATA
*&---------------------------------------------------------------------*
DATA GS_BSIS TYPE BSIS.
DATA GV_REPORT_TYPE(1) TYPE C.  "L: List; D: dashboard
DATA GO_BANK_RECONCILIATION_BL TYPE REF TO YCL_FI_BANK_RECONCILIATION_BL.