* ==== CLASS POOL ZCL_IM__FI_DOCUMNT_IDX_DEL ====
CLASS-POOL .
*"* class pool for class ZCL_IM__FI_DOCUMNT_IDX_DEL

*"* local classes
INCLUDE ZCL_IM__FI_DOCUMNT_IDX_DEL====CL.

*"* class ZCL_IM__FI_DOCUMNT_IDX_DEL definition
*"* public declarations
  INCLUDE ZCL_IM__FI_DOCUMNT_IDX_DEL====CU.
*"* protected declarations
  INCLUDE ZCL_IM__FI_DOCUMNT_IDX_DEL====CO.
*"* private declarations
  INCLUDE ZCL_IM__FI_DOCUMNT_IDX_DEL====CI.
ENDCLASS. "ZCL_IM__FI_DOCUMNT_IDX_DEL definition

CLASS ZCL_IM__FI_DOCUMNT_IDX_DEL IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM__FI_DOCUMNT_IDX_DEL implementation


* ---- ZCL_IM__FI_DOCUMNT_IDX_DEL====CI ----
*"* private components of class ZCL_IM__FI_DOCUMNT_IDX_DEL
*"* do not include other source files here!!!
PRIVATE SECTION.

* ---- ZCL_IM__FI_DOCUMNT_IDX_DEL====CM001 ----
METHOD IF_EX_FI_DOCUMNT_IDX_DEL~DELETE_FLAG_SET .
CH_IDX_DEL_FLAG = 'X'.
ENDMETHOD.

* ---- ZCL_IM__FI_DOCUMNT_IDX_DEL====CO ----
*"* protected components of class ZCL_IM__FI_DOCUMNT_IDX_DEL
*"* do not include other source files here!!!
PROTECTED SECTION.

* ---- ZCL_IM__FI_DOCUMNT_IDX_DEL====CU ----
CLASS ZCL_IM__FI_DOCUMNT_IDX_DEL DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

*"* public components of class ZCL_IM__FI_DOCUMNT_IDX_DEL
*"* do not include other source files here!!!
PUBLIC SECTION.

  INTERFACES IF_EX_FI_DOCUMNT_IDX_DEL .