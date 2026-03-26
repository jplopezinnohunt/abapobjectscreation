*&---------------------------------------------------------------------*
*&  Include           YFM_COCKPITTOP
*&---------------------------------------------------------------------*

DATA : FCODE         TYPE SY-UCOMM,
       W_FIRST       TYPE BOOLE_D,
       W_STEP_1_DONE TYPE BOOLE_D,
       W_STEP_2_DONE TYPE BOOLE_D,
       W_STEP_3_DONE TYPE BOOLE_D,
       WT_EXCLUDE    TYPE TABLE OF SY-UCOMM.

DATA : GO_WORD TYPE REF TO YCL_SAP_TO_WORD.

DATA : GV_OPEN TYPE BOOLE_D.

DATA : BDC_TAB TYPE TABLE OF BDCDATA WITH HEADER LINE.

CONSTANTS : C_TRANS_1 TYPE TCODE VALUE 'FMAVCDERIAOR',
            C_TRANS_2 TYPE TCODE VALUE 'FMAVCREINIT',
            C_TRANS_3 TYPE TCODE VALUE 'FMAVCR02'.