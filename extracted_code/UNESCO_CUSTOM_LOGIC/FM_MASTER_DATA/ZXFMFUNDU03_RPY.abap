*&---------------------------------------------------------------------*
*&  Include           ZXFMFUNDU03
*&---------------------------------------------------------------------*

*DATA: LR_GOS_MANAGER TYPE REF TO CL_GOS_MANAGER,
*
*      LS_BORIDENT TYPE BORIDENT.
*
*
*
* LS_BORIDENT-OBJTYPE = 'BUS00634'.
*
* concatenate i_IFMFINCODE-fikrs i_IFMFINCODE-fincode into LS_BORIDENT-OBJKEY .



*CREATE OBJECT LR_GOS_MANAGER
*  EXPORTING
*    IS_OBJECT = LS_BORIDENT
*    IP_NO_COMMIT = ' '
*  EXCEPTIONS
*    OBJECT_INVALID = 1.

GV_MODE = I_ACTION.
E_IFMFINCODE = IFMFINCODE = I_IFMFINCODE.

"Instanciate class for UNESCO additional fields
YCL_FM_FUND_IBF_BL=>GET_INSTANCE( IV_FIKRS = I_IFMFINCODE-FIKRS
                                  IV_FINCODE = I_IFMFINCODE-FINCODE
                                  IV_NEW_INSTANCE = ABAP_TRUE ).