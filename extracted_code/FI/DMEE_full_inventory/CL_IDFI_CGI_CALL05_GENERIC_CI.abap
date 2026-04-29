private section.

  data MV_TREE_TYPE type DMEE_TREETYPE .
  data MV_TREE_ID type DMEE_TREEID .

  methods COMPARE_BY_CHARS
    importing
      !IV_GENERIC type CLIKE
      !IV_CNTRY_SPEC type CLIKE
    exceptions
      CHANGE_FOUND .
  methods COMPARE_STRUCTURES
    importing
      !IS_GENERIC type ANY
      !IS_CNTRY_SPEC type ANY
      !IV_STRUC_NAME type STRING
    exceptions
      CHANGE_FOUND .
  methods IS_DMEEX_TREE
    importing
      !IV_TREE_TYPE type DMEE_TREETYPE default CON_TREE_TYPE_PAYM
      !IV_TREE_ID type DMEE_TREEID
    returning
      value(RV_IS_DMEEX_TREE) type ABAP_BOOL .