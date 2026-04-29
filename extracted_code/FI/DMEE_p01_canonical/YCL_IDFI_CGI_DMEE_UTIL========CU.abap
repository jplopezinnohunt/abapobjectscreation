class YCL_IDFI_CGI_DMEE_UTIL definition
  public
  final
  create public .

public section.

  class-methods GET_INSTANCE
    returning
      value(RO_INSTANCE) type ref to YCL_IDFI_CGI_DMEE_UTIL .
  methods GET_TAG_VALUE_FROM_CUSTO
    importing
      !IV_LAND1 type LAND1
      !IV_DEB_CRE type ANY
      !IV_TAG_FULL type STRING
      !IS_FPAYH type FPAYH
      !IS_FPAYHX type FPAYHX
      !IS_FPAYP type FPAYP
    exporting
      !EV_SUBRC type SY-SUBRC
    changing
      !CV_VALUE_C type ANY .
  methods CONSTRUCTOR .