*&---------------------------------------------------------------------*
*& Report  FEB_FILE_HANDLING
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*

REPORT   FEB_FILE_HANDLING.

INCLUDE SCHEDMAN_EVENTS.
INCLUDE RKASMAWF.

TABLES: FEB_IMP_SOURCE,
        SSCRFIELDS.

DATA: O_SEL_OPT         TYPE FEBY_SELOPT,
      LV_EXECPRI        TYPE RFPDO1-FEBEINLES,
      LS_PRINTPARAM     TYPE FEBS_PRINTPARAM,
      L_SCHEDMAN_ERR(1) TYPE C VALUE SPACE.

SELECTION-SCREEN  BEGIN OF BLOCK 1 WITH FRAME TITLE TEXT-001.
SELECT-OPTIONS T_SEL_OP FOR FEB_IMP_SOURCE-PATH_SOURCE OBLIGATORY. "n2313727
SELECTION-SCREEN  END OF BLOCK 1.


SELECTION-SCREEN  BEGIN OF BLOCK 2 WITH FRAME TITLE TEXT-002.
PARAMETERS: P_KOAUSZ     LIKE RFPDO1-FEBPAUSZ,   " Kontoauszug drucken
            P_BUPRO      LIKE RFPDO2-FEBBUPRO,
            P_STATIK     LIKE RFPDO2-FEBSTAT,
            PA_LSEPA     LIKE FEBPDO-LSEPA,
            P_NO_LOG     TYPE FEB_NO_APPLOG.                    "n3081352
SELECTION-SCREEN  END OF BLOCK 2.


AT SELECTION-SCREEN ON BLOCK 2.

*---- Program started with EXEC+PRINT online
  IF SY-BATCH NE 'X'.
    IF P_BUPRO = 'X' OR P_STATIK = 'X'.
      IF SSCRFIELDS-UCOMM = 'PRIN'.
        LV_EXECPRI = 'X'.
      ENDIF.
    ENDIF.
  ENDIF.

  LS_PRINTPARAM-KOAUSZ = P_KOAUSZ.
  LS_PRINTPARAM-BUPRO = P_BUPRO.
  LS_PRINTPARAM-STATIK = P_STATIK.
  LS_PRINTPARAM-LSEPA = PA_LSEPA.
  LS_PRINTPARAM-NO_APPLOG = P_NO_LOG.                           "n3081352

START-OF-SELECTION.

  O_SEL_OPT = T_SEL_OP[].

* registration for shedule manager
  PERFORM SCHEDMAN_START_STOP USING 'START'.

  CALL METHOD CL_FEB_FILE_HANDLING=>MAIN
    EXPORTING
      IV_EXECPRI            = LV_EXECPRI
      IS_PRINTPARAM         = LS_PRINTPARAM
      IT_SEL_OPT_INPUT_PATH = O_SEL_OPT
    CHANGING
      C_SCHEDMAN_ERR        = L_SCHEDMAN_ERR.

* notice of departure from schedule manager
  PERFORM SCHEDMAN_START_STOP USING 'STOP'.



*&---------------------------------------------------------------------*
*&      Form  schedman_start_stop
*&---------------------------------------------------------------------*
*       Integration Schedule Manager
*----------------------------------------------------------------------*
FORM SCHEDMAN_START_STOP  USING    P_COMMAND.

* local statics
  STATICS: LS_KEY_STATIC TYPE SCHEDMAN_KEY.
*local data declaration
*  DATA: gs_key      LIKE schedman_key.
*  DATA: gt_spono    LIKE schedman_spool.

*  DATA: ld_worklist_flag(1).
  DATA: LS_DETAIL   LIKE SCHEDMAN_DETAIL_USER.
  DATA: LT_SELKRIT  LIKE SCHEDMAN_SELKRIT OCCURS 0 WITH HEADER LINE.
  DATA: LT_PARAM    LIKE SCHEDMAN_SELKRIT OCCURS 0 WITH HEADER LINE.
  DATA: LS_WITEM    LIKE SCMA_WITEM.
  DATA: LS_EVENT    LIKE SCMA_EVENT.
  DATA: LS_EXT      LIKE SCHEDMAN_EXT.
  DATA: LS_MESSAGE  LIKE SCHEDMAN_MESSAGE,
        LD_OBJECTS  LIKE SMMAIN-NR_OF_OBJECTS,
        LD_APLSTAT  LIKE SMMAIN-APLSTAT.

  DATA: L_STATUS   TYPE TBTCJOB-STATUS.

  DATA: JOBNAME    LIKE TBTCO-JOBNAME,
        JOBCOUNT   LIKE TBTCO-JOBCOUNT.
  DATA: LS_SEL_OPT TYPE FEBS_SELOPT.


  IF P_COMMAND = 'START'.
* muss in scmatasks
    LS_DETAIL-REPID       = SY-REPID.
    LS_DETAIL-VARIANTE    = SY-SLSET.      "<<die variante
    LS_DETAIL-APPLICATION = 'FI-BL'.
    LS_DETAIL-TESTFLAG    = ''.

    CLEAR LT_SELKRIT.
    LT_SELKRIT-STRUCTURE = 'FEB_IMP_SOURCE'.
    LT_SELKRIT-FIELD = 'PATH_SOURCE'.
    LOOP AT O_SEL_OPT INTO LS_SEL_OPT.
      MOVE-CORRESPONDING LS_SEL_OPT TO LT_SELKRIT.
      LT_SELKRIT-OPTIO = LS_SEL_OPT-OPTION.
      APPEND LT_SELKRIT.
    ENDLOOP.

    LS_WITEM-WF_WITEM = WF_WITEM.
    LS_WITEM-WF_WLIST = WF_WLIST.
    CALL FUNCTION 'KPEP_MONI_INIT_RECORD'
      EXPORTING
        LS_DETAIL  = LS_DETAIL
*       ls_witem   = ls_witem
      IMPORTING
        LS_KEY     = LS_KEY_STATIC
      TABLES
        LT_SELKRIT = LT_SELKRIT
        LT_PARAM   = LT_PARAM.

  ELSEIF P_COMMAND = 'STOP'.

    LD_APLSTAT  = '0'.
    LS_EVENT-WF_WITEM = WF_WITEM.
    LS_EVENT-WF_OKEY  = WF_OKEY.
    IF L_SCHEDMAN_ERR = 'X'.
      LS_EVENT-WF_EVENT = CS_WF_EVENTS-ERROR.
    ELSE.
      LS_EVENT-WF_EVENT = CS_WF_EVENTS-FINISHED.
    ENDIF.
    CALL FUNCTION 'KPEP_MONI_CLOSE_RECORD'
      EXPORTING
        LS_KEY        = LS_KEY_STATIC
        LS_SCMA_EVENT = LS_EVENT
      CHANGING
        LD_APLSTAT    = LD_APLSTAT
      EXCEPTIONS
*       NO_ID_GIVEN   = 1
        OTHERS        = 0.

  ENDIF.

  COMMIT WORK.           " <<<<<<<<<<  C O M M I T  W O R K  >>>>>>>

ENDFORM.                    "schedman_start_stop