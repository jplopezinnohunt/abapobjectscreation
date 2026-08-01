*&---------------------------------------------------------------------*
*&  Include           YFI_CASH_FORECAST_DATA
*&---------------------------------------------------------------------*

"For selection-screen
DATA GS_GLT0 TYPE GLT0.
DATA GS_BSEG TYPE BSEG.
DATA GS_BSIS TYPE BSIS.
DATA GS_FMFINCODE TYPE FMFINCODE.

"Class for cash forecast business logic
DATA GO_CASH_FORECAST TYPE REF TO YCL_FI_CASH_FORECAST_BL.

"Screen management
DATA OK_CODE TYPE SY-UCOMM.
DATA GO_CUSTOM_CONTAINER TYPE REF TO CL_GUI_CUSTOM_CONTAINER.
DATA GO_GRID TYPE REF TO CL_GUI_ALV_GRID.
TABLES YSFI_CASH_FORECAST_DYNP.