* ==== CLASS POOL YCL_IM_TR_GET_ACCNT_ASSIGN ====
CLASS-POOL .
*"* class pool for class YCL_IM_TR_GET_ACCNT_ASSIGN

*"* local classes
INCLUDE YCL_IM_TR_GET_ACCNT_ASSIGN====CL.

*"* class YCL_IM_TR_GET_ACCNT_ASSIGN definition
*"* public declarations
  INCLUDE YCL_IM_TR_GET_ACCNT_ASSIGN====CU.
*"* protected declarations
  INCLUDE YCL_IM_TR_GET_ACCNT_ASSIGN====CO.
*"* private declarations
  INCLUDE YCL_IM_TR_GET_ACCNT_ASSIGN====CI.
ENDCLASS. "YCL_IM_TR_GET_ACCNT_ASSIGN definition

CLASS YCL_IM_TR_GET_ACCNT_ASSIGN IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IM_TR_GET_ACCNT_ASSIGN implementation


* ---- YCL_IM_TR_GET_ACCNT_ASSIGN====CI ----
*"* private components of class YCL_IM_TR_GET_ACCNT_ASSIGN
*"* do not include other source files here!!!
PRIVATE SECTION.

* ---- YCL_IM_TR_GET_ACCNT_ASSIGN====CM001 ----
METHOD IF_EX_TR_GET_ACCNT_ASSIGN~GET_ACCNT_ASSIGN .

* This Coding is only for customers which used EXIT_SAPLFMCH_001

* decomment the line if you have Type/Data definitions in ZXFMYTOP
* INCLUDE ZXFMYTOP


*  INCLUDE ZXFMYU03.
DATA: W_X.

W_X = 1.
CHECK W_X = 1.

ENDMETHOD.

* ---- YCL_IM_TR_GET_ACCNT_ASSIGN====CO ----
*"* protected components of class YCL_IM_TR_GET_ACCNT_ASSIGN
*"* do not include other source files here!!!
PROTECTED SECTION.

* ---- YCL_IM_TR_GET_ACCNT_ASSIGN====CU ----
CLASS YCL_IM_TR_GET_ACCNT_ASSIGN DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

*"* public components of class YCL_IM_TR_GET_ACCNT_ASSIGN
*"* do not include other source files here!!!
PUBLIC SECTION.

  INTERFACES IF_EX_TR_GET_ACCNT_ASSIGN .