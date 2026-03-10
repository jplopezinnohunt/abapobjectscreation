*&---------------------------------------------------------------------*
*&  Include           ZXFMFUNDU02
*&---------------------------------------------------------------------*
DATA LO_IBF_BL TYPE REF TO YCL_FM_FUND_IBF_BL.
DATA LV_FIELDNAME TYPE FIELDNAME VALUE '(SAPLFM52)IFMFINCODE'.
FIELD-SYMBOLS <FIELD> TYPE IFMFINCODE.

E_F_IFMCI_FMFINCODE-ZZIBF = IFMFINCODE-ZZIBF.
E_F_IFMCI_FMFINCODE-ZZOUTPUT = IFMFINCODE-ZZOUTPUT.

LO_IBF_BL = YCL_FM_FUND_IBF_BL=>GET_CURRENT_INSTANCE( ).
IF LO_IBF_BL IS BOUND.
  "IBF de-activation NME20240618
*  ASSIGN (lv_fieldname) TO <field>.
*  IF <field> IS ASSIGNED.
*    IF lo_ibf_bl->check_fund_type_modified( <field>-type ) = abap_true.
*      e_f_ifmci_fmfincode-zzibf = lo_ibf_bl->get_ibf( iv_fikrs = <field>-fikrs
*                                                      iv_fund_type = <field>-type ).
*    ENDIF.
*  ENDIF.
  "Check if fund assignment to C5 has been modified
  LO_IBF_BL->FUND_C5_ACTION( EXPORTING IV_ACTION = 'C'
                                       IV_MODE = GV_MODE
                             IMPORTING EV_IS_OK = E_F_IFMCI_FMFINCODE-DUMMX ).
ENDIF.