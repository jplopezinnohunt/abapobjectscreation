*&---------------------------------------------------------------------*
*& Report  ZPBC_CLEAR_INIT_LOG
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*

REPORT  ZPBC_CLEAR_INIT_LOG.

TABLES: HRFPM_INIT_LOG.

IF 1 = 2 .
  DELETE FROM HRFPM_INIT_LOG WHERE KCLOG = 'X'.
  COMMIT WORK.
ENDIF.