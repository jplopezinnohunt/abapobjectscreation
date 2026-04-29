class YCL_IDFI_CGI_DMEE_FALLBACK definition
  public
  create public .

public section.

  class-methods GET_INSTANCE
    returning
      value(RO_INSTANCE) type ref to YCL_IDFI_CGI_DMEE_FALLBACK .
  methods GET_CREDIT
    importing
      !FLT_VAL_DEBIT_OR_CREDIT type ANY
      !FLT_VAL_COUNTRY type INTCA
      !I_TREE_ID type DMEE_TREEID_ABA
      !I_TREE_TYPE type DMEE_TREETYPE_ABA
      !I_PARAM type ANY
      !I_UPARAM type ANY
      !I_EXTENSION type DMEE_EXIT_INTERFACE_ABA
      !I_FPAYH type FPAYH
      !I_FPAYHX type FPAYHX
      !I_FPAYP type FPAYP
      !I_ROOT_NODES type STRING
      !I_NODE_PATH type STRING
    changing
      !C_VALUE type ANY
      !O_VALUE type ANY
      !N_VALUE type ANY
      !P_VALUE type ANY .