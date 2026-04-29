class CL_IDFI_CGI_CALL05_GENERIC definition
  public
  create public .

public section.
  type-pools ABAP .

  interfaces IF_IDFI_CGI_CALL05
      all methods final .

  constants CON_TREE_TYPE_PAYM type DMEE_TREETYPE value 'PAYM' ##NO_TEXT.
  constants CON_CL_DMEE_RUNTIME type STRING value 'CL_DMEE_RUNTIME' ##NO_TEXT.
  constants CON_METHOD_DMEEX type STRING value 'DMEEX' ##NO_TEXT.