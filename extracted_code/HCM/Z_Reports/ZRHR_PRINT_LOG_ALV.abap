*&---------------------------------------------------------------------*
*& Report ZRHR_PRINT_LOG_ALV
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT ZRHR_PRINT_LOG_ALV.
INCLUDE ZRHR_PRINT_LOG_ALV_DATA.
INCLUDE ZRHR_PRINT_LOG_ALV_SEL.
INCLUDE ZRHR_PRINT_LOG_ALV_CLASS.
INCLUDE ZRHR_PRINT_LOG_ALV_FORM.
INCLUDE ZRHR_PRINT_LOG_ALV_MODULE.
INITIALIZATION.
PERFORM DESABLE_TEST_PERAMETERS.
START-OF-SELECTION.
*Identify num of columns to be displayed
PERFORM HOW_MANY_COLUMNS.
IF pt_in[] is not initial and gv_nbr_col is not initial.
  CALL SCREEN 9001.
ENDIF.
END-OF-SELECTION.