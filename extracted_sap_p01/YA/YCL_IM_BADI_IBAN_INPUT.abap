* ==== CLASS POOL YCL_IM_BADI_IBAN_INPUT ====
CLASS-POOL .
*"* class pool for class YCL_IM_BADI_IBAN_INPUT

*"* local type definitions
INCLUDE YCL_IM_BADI_IBAN_INPUT========CCDEF.

*"* class YCL_IM_BADI_IBAN_INPUT definition
*"* public declarations
  INCLUDE YCL_IM_BADI_IBAN_INPUT========CU.
*"* protected declarations
  INCLUDE YCL_IM_BADI_IBAN_INPUT========CO.
*"* private declarations
  INCLUDE YCL_IM_BADI_IBAN_INPUT========CI.
ENDCLASS. "YCL_IM_BADI_IBAN_INPUT definition

*"* macro definitions
INCLUDE YCL_IM_BADI_IBAN_INPUT========CCMAC.
*"* local class implementation
INCLUDE YCL_IM_BADI_IBAN_INPUT========CCIMP.

CLASS YCL_IM_BADI_IBAN_INPUT IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_IM_BADI_IBAN_INPUT implementation


* ---- YCL_IM_BADI_IBAN_INPUT========CI ----
PRIVATE SECTION.

* ---- YCL_IM_BADI_IBAN_INPUT========CM001 ----
  METHOD IF_EX_BADI_IBAN_INPUT~CUSTOMIZE.
  ENDMETHOD.

* ---- YCL_IM_BADI_IBAN_INPUT========CM002 ----
  METHOD IF_EX_BADI_IBAN_INPUT~CHECK_ISO_CODE.

* Available local variables and values
 "CODE1  - country ISO-code of the IBAN/BIC
 "CODE2  - country ISO-code of the bank
 "TYPE   - type of check/validation
      "I - validation of an IBAN
      "B - validation of a BIC
* Output parameter
 "RESULT - result of the ISO-code check
      "X - allowed combination of ISO-code of the bank and IBAN/BIC
      "  - not allowed combination
* Available system variables and values
 "sy-tcode - name of the calling transaction
 "sy-cprog - name of the calling program
 "and many more, inclusive the complete stack information via the
 "function module SYSTEM_CALLSTACK

  CASE CODE2.
*   Example 1 - IBANs/BICs from Guernsey, Isle of Man or Jersey
*               may contain the country code 'GB'
    WHEN 'GG' OR 'IM' OR 'JE'.
*     IF type = 'I'.        "relevant only for IBAN validation
        IF CODE1 = 'GB'.
          RESULT = 'X'.     "combination allowed
        ENDIF.
*     ENDIF.
    WHEN 'RE' OR 'GP' OR 'MQ' OR 'GF'  "French overseas territories
      OR 'PF' OR 'TF' OR 'YT' OR 'NC' OR 'PM' OR 'WF'.
      IF CODE1 = 'FR'.
        RESULT = 'X'.       "combination allowed
      ENDIF.
    WHEN OTHERS.
  ENDCASE.

  IF TYPE = 'B'.
*   Example 2 - a BIC from Jersey may contain the country code 'GB'
    IF CODE1 = 'GB' AND CODE2 = 'JE'.
      RESULT = 'X'.
    ENDIF.
  ENDIF.

  ENDMETHOD.

* ---- YCL_IM_BADI_IBAN_INPUT========CO ----
PROTECTED SECTION.

* ---- YCL_IM_BADI_IBAN_INPUT========CU ----
CLASS YCL_IM_BADI_IBAN_INPUT DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES IF_EX_BADI_IBAN_INPUT .