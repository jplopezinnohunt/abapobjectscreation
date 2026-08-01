* ==== CLASS POOL ZCL_IM__CTRL_GL ====
CLASS-POOL .
*"* class pool for class ZCL_IM__CTRL_GL

*"* local classes
INCLUDE ZCL_IM__CTRL_GL===============CL.

*"* class ZCL_IM__CTRL_GL definition
*"* public declarations
  INCLUDE ZCL_IM__CTRL_GL===============CU.
*"* protected declarations
  INCLUDE ZCL_IM__CTRL_GL===============CO.
*"* private declarations
  INCLUDE ZCL_IM__CTRL_GL===============CI.
ENDCLASS. "ZCL_IM__CTRL_GL definition

CLASS ZCL_IM__CTRL_GL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM__CTRL_GL implementation


* ---- ZCL_IM__CTRL_GL===============CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM__CTRL_GL
*"* do not include other source files here!!!

* ---- ZCL_IM__CTRL_GL===============CM001 ----
METHOD IF_EX_FMFG_FUNDMSG_DRV_DEF~FM_DERIVE_FND_MESSAGE.
ENDMETHOD.

* ---- ZCL_IM__CTRL_GL===============CM002 ----
METHOD IF_EX_FMFG_FUNDMSG_DRV_DEF~FILL_ADDITIONAL_FIELDS.
ENDMETHOD.

* ---- ZCL_IM__CTRL_GL===============CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_IM__CTRL_GL
*"* do not include other source files here!!!

* ---- ZCL_IM__CTRL_GL===============CU ----
CLASS ZCL_IM__CTRL_GL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_IM__CTRL_GL
*"* do not include other source files here!!!

  INTERFACES IF_EX_FMFG_FUNDMSG_DRV_DEF .