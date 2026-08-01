* ==== CLASS POOL ZCL_IM__CTRL_FUND_CENTER ====
CLASS-POOL .
*"* class pool for class ZCL_IM__CTRL_FUND_CENTER

*"* local classes
INCLUDE ZCL_IM__CTRL_FUND_CENTER======CL.

*"* class ZCL_IM__CTRL_FUND_CENTER definition
*"* public declarations
  INCLUDE ZCL_IM__CTRL_FUND_CENTER======CU.
*"* protected declarations
  INCLUDE ZCL_IM__CTRL_FUND_CENTER======CO.
*"* private declarations
  INCLUDE ZCL_IM__CTRL_FUND_CENTER======CI.
ENDCLASS. "ZCL_IM__CTRL_FUND_CENTER definition

CLASS ZCL_IM__CTRL_FUND_CENTER IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM__CTRL_FUND_CENTER implementation


* ---- ZCL_IM__CTRL_FUND_CENTER======CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM__CTRL_FUND_CENTER
*"* do not include other source files here!!!

* ---- ZCL_IM__CTRL_FUND_CENTER======CM001 ----
METHOD IF_EX_FMFG_FUNDMSG_DRV_DEF~FM_DERIVE_FND_MESSAGE.
ENDMETHOD.

* ---- ZCL_IM__CTRL_FUND_CENTER======CM002 ----
METHOD IF_EX_FMFG_FUNDMSG_DRV_DEF~FILL_ADDITIONAL_FIELDS.


ENDMETHOD.

* ---- ZCL_IM__CTRL_FUND_CENTER======CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_IM__CTRL_FUND_CENTER
*"* do not include other source files here!!!

* ---- ZCL_IM__CTRL_FUND_CENTER======CU ----
CLASS ZCL_IM__CTRL_FUND_CENTER DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_IM__CTRL_FUND_CENTER
*"* do not include other source files here!!!

  INTERFACES IF_EX_FMFG_FUNDMSG_DRV_DEF .