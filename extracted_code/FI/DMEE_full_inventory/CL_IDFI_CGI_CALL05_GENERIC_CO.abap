protected section.

  data MV_COUNTRY_KEY type LAND1 .
  data MV_IS_DMEEX_TREE type ABAP_BOOL .

  methods GENERIC_CALL
  final
    importing
      !IS_FPAYH type FPAYH
      !IS_FPAYHX type FPAYHX
      !IV_PAYMEDIUM type XFELD
    changing
      !CS_FPAYHX_FREF type FPAYHX_FREF
      !CT_FPAYP_FREF type FPM_T_FPAYP .
  methods CHECK_CHANGES
  final
    importing
      !IS_FPAYHX_FREF_GEN type FPAYHX_FREF
      !IT_FPAYP_FREF_GEN type FPM_T_FPAYP
      !IS_FPAYHX_FREF_CNTRY type FPAYHX_FREF
      !IT_FPAYP_FREF_CNTRY type FPM_T_FPAYP
    exceptions
      CHANGE_FOUND .
  methods COUNTRY_SPECIFIC_CALL
    importing
      !IS_FPAYH type FPAYH
      !IS_FPAYHX type FPAYHX
      !IV_PAYMEDIUM type XFELD
    changing
      !CS_FPAYHX_FREF type FPAYHX_FREF
      !CT_FPAYP_FREF type FPM_T_FPAYP .
  methods GET_BATCH_NUMBER
    importing
      !IS_FPAYH type FPAYH
      !IS_FPAYHX type FPAYHX
      !IV_PAYMEDIUM type XFELD
      value(IT_FPAYP_FREF) type FPM_T_FPAYP
    returning
      value(RV_RENUM) type STRING .