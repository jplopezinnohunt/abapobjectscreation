*&---------------------------------------------------------------------*
*&  Include           ZXFMFUNDU01
*&---------------------------------------------------------------------*

DATA: LR_GOS_MANAGER TYPE REF TO CL_GOS_MANAGER,
      LS_BORIDENT    TYPE BORIDENT.

DATA LO_IBF_BL TYPE REF TO YCL_FM_FUND_IBF_BL.


LS_BORIDENT-OBJTYPE = 'BUS00634'.

CONCATENATE I_F_IFMFINCODE-FIKRS I_F_IFMFINCODE-FINCODE INTO LS_BORIDENT-OBJKEY .

CREATE OBJECT LR_GOS_MANAGER
  EXPORTING
    IS_OBJECT      = LS_BORIDENT
    IP_NO_COMMIT   = ' '
  EXCEPTIONS
    OBJECT_INVALID = 1.

IFMFINCODE = I_F_IFMFINCODE.

"IBF Management NME20210928
*ifmfincode-zzibf = i_f_ifmfincode-zzibf.
*ifmfincode-zzoutput = i_f_ifmfincode-zzoutput.

IF I_DISPLAY_ONLY = ABAP_TRUE.
  GV_MODE = 'D'.
  "Instanciate class for UNESCO specific fields
  LO_IBF_BL = YCL_FM_FUND_IBF_BL=>GET_INSTANCE( IV_FIKRS = I_F_IFMFINCODE-FIKRS
                                                IV_FINCODE = I_F_IFMFINCODE-FINCODE
                                                IV_NEW_INSTANCE = ABAP_TRUE ).
*ELSE.
*  lo_ibf_bl = ycl_fm_fund_ibf_bl=>get_instance( iv_fikrs = i_f_ifmfincode-fikrs
*                                                iv_fincode = i_f_ifmfincode-fincode ).
ENDIF.