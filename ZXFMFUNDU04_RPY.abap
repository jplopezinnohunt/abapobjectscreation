*&---------------------------------------------------------------------*
*&  Include           ZXFMFUNDU04
*&---------------------------------------------------------------------*

DATA LT_FUND_C5 TYPE YTTFM_FUND_C5.
DATA LV_BEGBI TYPE DATUM.
DATA LV_ENDBI TYPE DATUM.
DATA LV_DATAB_C(10) TYPE C.
DATA LV_DATBIS_C(10) TYPE C.

IF I_F_IFMFINCODE-TYPE IS INITIAL.
  IF SY-CALLD = ABAP_TRUE OR SY-TCODE(2) <> 'FM'.
    MESSAGE E032(ZFI) WITH 'Fund Type'.
  ELSE.  "To avoid leave screen if RFC call
    MESSAGE E032(ZFI) RAISING ERROR WITH 'Fund Type'.
  ENDIF.
ENDIF.

IF I_F_IFMFINCODE-PROFIL IS INITIAL.
  IF SY-CALLD = ABAP_TRUE OR SY-TCODE(2) <> 'FM'.
    MESSAGE E032(ZFI) WITH 'Budget Profile'.
  ELSE.    "To avoid leave screen if RFC call
    MESSAGE E032(ZFI) RAISING ERROR WITH 'Budget Profile'.
  ENDIF.
ENDIF.

"If IBF flag is set, check output filed is filled
"IBF flag de-activation NME20240618
*IF i_f_ifmfincode-zzibf = abap_true AND i_f_ifmfincode-zzoutput IS INITIAL.
*  IF sy-calld = abap_true OR sy-tcode(2) <> 'FM'.
*    MESSAGE e035(zfi).  "To avoid leave screen if RFC call
*  ELSE.
*    MESSAGE e035(zfi) RAISING error.
*  ENDIF.
*ENDIF.

GO_FUND_IBF_BL = YCL_FM_FUND_IBF_BL=>GET_CURRENT_INSTANCE( ).
IF GO_FUND_IBF_BL IS BOUND.
  LT_FUND_C5 = GO_FUND_IBF_BL->MT_FUND_C5.
*ELSE.
*  SELECT 'X' AS c5_sel, a~c5_id, b~year_from, b~year_to, ychk_output, fm_output, zzibf
*         FROM ytfm_fund_c5 AS a
*         LEFT OUTER JOIN ytfm_c5 AS b ON b~c5_id = a~c5_id
*         WHERE a~fikrs = @i_f_ifmfincode-fikrs
*         AND   a~fincode = @i_f_ifmfincode-fincode
*         INTO CORRESPONDING FIELDS OF TABLE @lt_fund_c5.
ENDIF.
"Check C/5 assignment is in validity date
LOOP AT LT_FUND_C5 INTO DATA(LS_FUND_C5) WHERE C5_SEL = ABAP_TRUE OR FM_OUTPUT IS NOT INITIAL.
  LV_BEGBI = |{ LS_FUND_C5-YEAR_FROM }0101|.
  LV_ENDBI = |{ LS_FUND_C5-YEAR_TO }1231|.
  IF I_F_IFMFINCODE-DATAB > LV_ENDBI OR I_F_IFMFINCODE-DATBIS < LV_BEGBI.
    "Biennium assignment is not in Fund validity
    WRITE I_F_IFMFINCODE-DATAB TO LV_DATAB_C.
    WRITE I_F_IFMFINCODE-DATBIS TO LV_DATBIS_C.
    IF SY-CALLD = ABAP_TRUE OR SY-TCODE(2) <> 'FM'.
      MESSAGE E022(YFM1) WITH LS_FUND_C5-C5_ID LV_DATAB_C LV_DATBIS_C.  "To avoid leave screen if RFC call
    ELSE.
      MESSAGE E022(YFM1) WITH LS_FUND_C5-C5_ID LV_DATAB_C LV_DATBIS_C RAISING ERROR.
    ENDIF.
  ENDIF.
  "Check if output must be filled
  IF LS_FUND_C5-C5_SEL = ABAP_TRUE AND LS_FUND_C5-YCHK_OUTPUT = ABAP_TRUE AND LS_FUND_C5-FM_OUTPUT IS INITIAL.
    IF SY-CALLD = ABAP_TRUE OR SY-TCODE(2) <> 'FM'.
      MESSAGE E037(ZFI) WITH LS_FUND_C5-C5_ID.  "To avoid leave screen if RFC call
    ELSE.
      MESSAGE E037(ZFI) WITH LS_FUND_C5-C5_ID RAISING ERROR.
    ENDIF.
  ENDIF.
ENDLOOP.

IF I_FLG_SAVE = ABAP_TRUE.
  IF GO_FUND_IBF_BL IS BOUND.
    "Check for update for fund assignent to C5 specific table
    GO_FUND_IBF_BL->FUND_C5_ACTION( IV_ACTION = 'U'
                                    IV_MODE = GV_MODE ).
    "Free instance for IBF management
  ENDIF.
  YCL_FM_FUND_IBF_BL=>CLEAR_INSTANCE( ).
ENDIF.