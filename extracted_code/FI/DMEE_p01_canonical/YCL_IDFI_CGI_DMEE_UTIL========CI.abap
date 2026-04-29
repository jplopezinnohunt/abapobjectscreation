private section.

  types:
    BEGIN OF ty_ppc_cus,
      land1     TYPE ytfi_ppc_tag-land1,
      deb_cre   TYPE ytfi_ppc_tag-deb_cre,
      pay_type  TYPE ytfi_ppc_struc-pay_type,
      tag_full  TYPE ytfi_ppc_tag-tag_full,
      code_ord  TYPE ytfi_ppc_struc-code_ord,
      ppc_code  TYPE ytfi_ppc_struc-ppc_code,
      ppc_value TYPE ytfi_ppc_struc-ppc_value,
      pay_struc TYPE ytfi_ppc_struc-pay_struc,
      pay_field TYPE ytfi_ppc_struc-pay_field,
    END OF ty_ppc_cus .

  class-data MO_INSTANCE type ref to YCL_IDFI_CGI_DMEE_UTIL .
  data:
    mt_ppc_cus TYPE SORTED TABLE OF ty_ppc_cus WITH UNIQUE KEY land1 deb_cre pay_type tag_full code_ord .
  data:
    mt_t015l TYPE SORTED TABLE OF t015l WITH UNIQUE KEY lzbkz .

  methods BUILD_VALUE
    importing
      !IV_VALUE_C type ANY
      !IV_VALUE_TO_ADD type ANY
    exporting
      !EV_VALUE_C type ANY .