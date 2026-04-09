FUNCTION f4if_vat_shlp_exit.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  TABLES
*"      SHLP_TAB TYPE  SHLP_DESCR_TAB_T
*"      RECORD_TAB STRUCTURE  SEAHLPRES
*"  CHANGING
*"     VALUE(SHLP) TYPE  SHLP_DESCR_T
*"     VALUE(CALLCONTROL) LIKE  DDSHF4CTRL STRUCTURE  DDSHF4CTRL
*"----------------------------------------------------------------------

  DATA:
    rc LIKE sy-subrc.

  CALL FUNCTION 'F4UT_OPTIMIZE_COLWIDTH'
    TABLES
      shlp_tab    = shlp_tab
      record_tab  = record_tab
    CHANGING
      shlp        = shlp
      callcontrol = callcontrol.


  IF callcontrol-step = 'PRESEL'.
    READ TABLE shlp-selopt WITH KEY shlpfield = 'STCEG'
      TRANSPORTING NO FIELDS.
    IF sy-subrc <> 0.
      DATA: ls_selopt LIKE LINE OF shlp-selopt,
            ls_interface LIKE LINE OF shlp-interface.
      READ TABLE shlp-interface
        WITH KEY shlpfield = 'STCEG'
        INTO ls_interface
        TRANSPORTING value.
      IF ls_interface-value IS NOT INITIAL.
        ls_selopt-low = ls_interface-value.
        ls_selopt-shlpname = 'PTRV_VATDETAIL'.
        ls_selopt-shlpfield = 'STCEG'.
        ls_selopt-sign = 'I'.
        ls_selopt-option = 'EQ'.
        APPEND ls_selopt TO shlp-selopt.
      ENDIF.
    ENDIF.
  ENDIF.

*"----------------------------------------------------------------------
* STEP DISP     (Display values)
*"----------------------------------------------------------------------
* This step is called, before the selected data is displayed.
* You can e.g. modify or reduce the data in RECORD_TAB
* according to the users authority.
* If you want to get the standard display dialog afterwards, you
* should not change CALLCONTROL-STEP.
* If you want to overtake the dialog on you own, you must return
* the following values in CALLCONTROL-STEP:
* - "RETURN" if one line was selected. The selected line must be
*   the only record left in RECORD_TAB. The corresponding fields of
*   this line are entered into the screen.
* - "EXIT" if the values request should be aborted
* - "PRESEL" if you want to return to the selection dialog
* Standard function modules F4UT_PARAMETER_VALUE_GET and
* F4UT_PARAMETER_RESULTS_PUT may be very helpfull in this step.
  IF callcontrol-step = 'DISP'.

    SORT record_tab BY string.
    DELETE ADJACENT DUPLICATES FROM record_tab COMPARING string.
    EXIT.
  ENDIF.
ENDFUNCTION.