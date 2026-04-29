class CL_IDFI_CGI_CALL05_FACTORY definition
  public
  final
  create public .

public section.

  class-methods GET_INSTANCE
    importing
      !IS_FPAYH type FPAYH
      !IS_FPAYHX type FPAYHX
      !IV_PAYMEDIUM type XFELD
      !IT_FPAYP type FPM_T_FPAYP
    returning
      value(RO_INSTANCE) type ref to IF_IDFI_CGI_CALL05 .