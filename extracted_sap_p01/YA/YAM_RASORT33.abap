*----------------------------------------------------------------------*
*   INCLUDE ZASORT33                                                   *
*----------------------------------------------------------------------*
DATA: HLP_TABIX.
LOOP AT FELD.
  CLEAR X_SORT.
  X_SORT-SPOS = SY-TABIX.
  X_SORT-FIELDNAME(1) = 'S'.
  HLP_TABIX = SY-TABIX.
  CONCATENATE X_SORT-FIELDNAME HLP_TABIX INTO X_SORT-FIELDNAME.
  X_SORT-GROUP   = 'UL'.
  X_SORT-SUBTOT  = 'X'.
  APPEND X_SORT TO T_SORT.
ENDLOOP.

***X_LAYOUT_SETTINGS-NO_TOTALLINE = 'X'.
X_LAYOUT_SETTINGS-GET_SELINFOS = 'X'.
IF NOT SUMMB IS INITIAL.
   X_LAYOUT_SETTINGS-TOTALS_ONLY = 'X'.
   X_LAYOUT_SETTINGS-NO_SUBCHOICE = 'X'.
   X_LAYOUT_SETTINGS-NO_SUMCHOICE = 'X'.
ENDIF.

X_EVENT-NAME = 'TOP_OF_PAGE'.
X_EVENT-FORM = 'TOP_OF_PAGE'.
APPEND X_EVENT TO T_EVENT.

CALL FUNCTION 'REUSE_ALV_LIST_DISPLAY'
     EXPORTING
*         I_INTERFACE_CHECK        = ' '
         I_CALLBACK_PROGRAM       = SY-CPROG
*         I_CALLBACK_PF_STATUS_SET = ' '
*         I_CALLBACK_USER_COMMAND  = ' '
*         I_STRUCTURE_NAME         =
          IS_LAYOUT                = X_LAYOUT_SETTINGS
          IT_FIELDCAT              = T_FIELD_CAT
*         IT_EXCLUDING             =
*         IT_SPECIAL_GROUPS        =
          IT_SORT                  = T_SORT
*         IT_FILTER                =
*         IS_SEL_HIDE              =
*         I_DEFAULT                = 'X'
          I_SAVE                   = 'A'
*         IS_VARIANT               = ' '
          IT_EVENTS                = T_EVENT
*         IT_EVENT_EXIT            =
*         IS_PRINT                 =
*         IS_REPREP_ID             =
*         I_SCREEN_START_COLUMN    = 0
*         I_SCREEN_START_LINE      = 0
*         I_SCREEN_END_COLUMN      = 0
*         I_SCREEN_END_LINE        = 0
*    IMPORTING
*         E_EXIT_CAUSED_BY_CALLER  =
*         ES_EXIT_CAUSED_BY_USER   =
     TABLES
          T_OUTTAB                 = ITAB_DATA
     EXCEPTIONS
          PROGRAM_ERROR            = 1
          OTHERS                   = 2.
IF SY-SUBRC <> 0.
  MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
          WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.