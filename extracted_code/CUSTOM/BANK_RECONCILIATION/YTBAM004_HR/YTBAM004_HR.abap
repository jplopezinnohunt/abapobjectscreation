*INCLUDE YTBAM004


*******************************************************************
* PROGRAM        YTBAM004
* TITLE          Bank reconciliation with type of funds
* AUTHOR         S.MAGAL
* DATE WRITTEN   July 2001
* R/3 RELEASE    4.6C
*******************************************************************
* COPIED FROM
* TITLE
*******************************************************************
* USED BY....... < user or usergroups >
*******************************************************************
* PROGRAM TYPE
* DEV.CLASS
* LOGICAL DB
*******************************************************************
* SCREENS
* GUI TITLE
* GUI STATUS
*******************************************************************
* CHANGE HISTORY
*
* Date       By      Correction Number & Brief Description  Release
*
* 16/05/2001 S.magal     0001 Correction ?????----------- -------
*
* 28/11/2001 A.Arkwright 0002 Update
*
*******************************************************************




* INPUT MODULE FOR TABLECONTROL 'T_CONTROL_TEMP': MODIFY TABLE
MODULE T_CONTROL_TEMP_MODIFY INPUT.
  MODIFY T_BSIS_TEMP
    INDEX T_CONTROL_TEMP-CURRENT_LINE.
ENDMODULE.

* INPUT MODULE FOR TABLECONTROL 'T_CONTROL_TEMP': PROCESS USER COMMAND
MODULE T_CONTROL_TEMP_USER_COMMAND INPUT.
  PERFORM USER_OK_TC USING    'T_CONTROL_TEMP'
                              'T_BSIS_TEMP'
                              'Y_CHAR'
                     CHANGING OK_CODE.
ENDMODULE.


*******************************************************************
*   INCLUDE TABLECONTROL_FORMS
*******************************************************************



*******************************************************************
*      Form  USER_OK_TC
*******************************************************************
*  -->  p_tc_name p_table_name p_mark_name p_ok
*  <--  p_ok
*******************************************************************
FORM USER_OK_TC USING    P_TC_NAME TYPE DYNFNAM
                         P_TABLE_NAME
                         P_MARK_NAME
                CHANGING P_OK      LIKE SY-UCOMM.

*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA: L_OK              TYPE SY-UCOMM,
        L_OFFSET          TYPE I.
*-END OF LOCAL DATA-----------------------------------------------*


* Table control specific operations
*   evaluate TC name and operations
  SEARCH P_OK FOR P_TC_NAME.
  IF SY-SUBRC <> 0.
    EXIT.
  ENDIF.

  L_OFFSET = STRLEN( P_TC_NAME ) + 1.
  L_OK = P_OK+L_OFFSET.

* execute general and TC specific operations
  CASE L_OK.

    WHEN 'INSR'.                                "insert row
      PERFORM FCODE_INSERT_ROW USING P_TC_NAME
                                     P_TABLE_NAME.
      CLEAR P_OK.

    WHEN 'DELE'.                                "delete row
      PERFORM FCODE_DELETE_ROW USING P_TC_NAME
                                     P_TABLE_NAME
                                     P_MARK_NAME.
      CLEAR P_OK.

    WHEN 'P--' OR                               "top of list
         'P-'  OR                               "previous page
         'P+'  OR                               "next page
         'P++'.                                 "bottom of list
      PERFORM COMPUTE_SCROLLING_IN_TC USING P_TC_NAME
                                            L_OK.
      CLEAR P_OK.

    WHEN 'MARK'.                                "mark all filled lines
      PERFORM FCODE_TC_MARK_LINES USING P_TC_NAME
                                        P_TABLE_NAME
                                        P_MARK_NAME   .
      CLEAR P_OK.

    WHEN 'DMRK'.                                "demark all filled lines
      PERFORM FCODE_TC_DEMARK_LINES USING P_TC_NAME
                                          P_TABLE_NAME
                                          P_MARK_NAME .
      CLEAR P_OK.

  ENDCASE.

ENDFORM.                                                "USER_OK_TC


*******************************************************************
*      Form  FCODE_INSERT_ROW
*******************************************************************
*  -->  p_tc_name p_table_name
*  <--
*******************************************************************
FORM FCODE_INSERT_ROW USING P_TC_NAME TYPE DYNFNAM
                            P_TABLE_NAME.

*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA L_LINES_NAME       LIKE FELD-NAME.
  DATA L_SELLINE          LIKE SY-STEPL.
  DATA L_LASTLINE         TYPE I.
  DATA L_LINE             TYPE I.
  DATA L_TABLE_NAME       LIKE FELD-NAME.
  FIELD-SYMBOLS <TC>                 TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>              TYPE STANDARD TABLE.
  FIELD-SYMBOLS <LINES>              TYPE I.
*-END OF LOCAL DATA-----------------------------------------------*


  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* get looplines of TableControl
  CONCATENATE 'G_' P_TC_NAME '_LINES' INTO L_LINES_NAME.
  ASSIGN (L_LINES_NAME) TO <LINES>.

* get current line
  GET CURSOR LINE L_SELLINE.
  IF SY-SUBRC <> 0.                             " append line to table
    L_SELLINE = <TC>-LINES + 1.
*   set top line and new cursor line
    IF L_SELLINE > <LINES>.
      <TC>-TOP_LINE = L_SELLINE - <LINES> + 1 .
      L_LINE = 1.
    ELSE.
      <TC>-TOP_LINE = 1.
      L_LINE = L_SELLINE.
    ENDIF.
  ELSE.                                         " insert line into table
    L_SELLINE = <TC>-TOP_LINE + L_SELLINE - 1.
*   set top line and new cursor line
    L_LASTLINE = L_SELLINE + <LINES> - 1.
    IF L_LASTLINE <= <TC>-LINES.
      <TC>-TOP_LINE = L_SELLINE.
      L_LINE = 1.
    ELSEIF <LINES> > <TC>-LINES.
      <TC>-TOP_LINE = 1.
      L_LINE = L_SELLINE.
    ELSE.
      <TC>-TOP_LINE = <TC>-LINES - <LINES> + 2 .
      L_LINE = L_SELLINE - <TC>-TOP_LINE + 1.
    ENDIF.
  ENDIF.
* insert initial line
  INSERT INITIAL LINE INTO <TABLE> INDEX L_SELLINE.
  <TC>-LINES = <TC>-LINES + 1.
* set cursor
  SET CURSOR LINE L_LINE.

ENDFORM.                                          "FCODE_INSERT_ROW


*******************************************************************
*      Form  FCODE_DELETE_ROW
*******************************************************************
*  -->  p_tc_name p_table_name p_mark_name
*  <--
*******************************************************************
FORM FCODE_DELETE_ROW USING P_TC_NAME TYPE DYNFNAM
                            P_TABLE_NAME
                            P_MARK_NAME.

*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA L_TABLE_NAME       LIKE FELD-NAME.
  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>      TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.
*-END OF LOCAL DATA-----------------------------------------------*


  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* delete marked lines
  DESCRIBE TABLE <TABLE> LINES <TC>-LINES.

  LOOP AT <TABLE> ASSIGNING <WA>.

*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.

    IF <MARK_FIELD> = 'X'.
      DELETE <TABLE> INDEX SYST-TABIX.
      IF SY-SUBRC = 0.
        <TC>-LINES = <TC>-LINES - 1.
      ENDIF.
    ENDIF.

  ENDLOOP.

ENDFORM.                              " FCODE_DELETE_ROW


*******************************************************************
*      Form  COMPUTE_SCROLLING_IN_TC
*******************************************************************
*       text
*******************************************************************
*      -->P_TC_NAME  name of tablecontrol
*      -->P_OK       ok code
*******************************************************************
FORM COMPUTE_SCROLLING_IN_TC USING P_TC_NAME
                                   P_OK.
*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA L_TC_NEW_TOP_LINE     TYPE I.
  DATA L_TC_NAME             LIKE FELD-NAME.
  DATA L_TC_LINES_NAME       LIKE FELD-NAME.
  DATA L_TC_FIELD_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <LINES>      TYPE I.
*-END OF LOCAL DATA-----------------------------------------------*


  ASSIGN (P_TC_NAME) TO <TC>.
* get looplines of TableControl
  CONCATENATE 'G_' P_TC_NAME '_LINES' INTO L_TC_LINES_NAME.
  ASSIGN (L_TC_LINES_NAME) TO <LINES>.


* is no line filled?
  IF <TC>-LINES = 0.
*   yes, ...
    L_TC_NEW_TOP_LINE = 1.
  ELSE.
*   no, ...
    CALL FUNCTION 'SCROLLING_IN_TABLE'
         EXPORTING
              ENTRY_ACT             = <TC>-TOP_LINE
              ENTRY_FROM            = 1
              ENTRY_TO              = <TC>-LINES
              LAST_PAGE_FULL        = 'X'
              LOOPS                 = <LINES>
              OK_CODE               = P_OK
              OVERLAPPING           = 'X'
         IMPORTING
              ENTRY_NEW             = L_TC_NEW_TOP_LINE
         EXCEPTIONS
              NO_ENTRY_OR_PAGE_ACT  = 01
              NO_ENTRY_TO           = 02
              NO_OK_CODE_OR_PAGE_GO = 03
              OTHERS                = 99.
  ENDIF.

* get actual tc and column
  GET CURSOR FIELD L_TC_FIELD_NAME
             AREA  L_TC_NAME.

  IF SYST-SUBRC = 0.
    IF L_TC_NAME = P_TC_NAME.
*     set actual column
      SET CURSOR FIELD L_TC_FIELD_NAME LINE 1.
    ENDIF.
  ENDIF.

* set the new top line
  <TC>-TOP_LINE = L_TC_NEW_TOP_LINE.

ENDFORM.                                  "COMPUTE_SCROLLING_IN_TC


*******************************************************************
*      Form  FCODE_TC_MARK_LINES
*******************************************************************
*       marks all TableControl lines
*******************************************************************
*      -->P_TC_NAME  name of tablecontrol
*******************************************************************
FORM FCODE_TC_MARK_LINES USING P_TC_NAME
                               P_TABLE_NAME
                               P_MARK_NAME.
*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA L_TABLE_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>      TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.
*-END OF LOCAL DATA-----------------------------------------------*

  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* mark all filled lines
  LOOP AT <TABLE> ASSIGNING <WA>.

*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.

    <MARK_FIELD> = 'X'.
  ENDLOOP.

ENDFORM.                                       "fcode_tc_mark_lines


*******************************************************************
*      Form  FCODE_TC_DEMARK_LINES
*******************************************************************
*       demarks all TableControl lines
*******************************************************************
*      -->P_TC_NAME  name of tablecontrol
*******************************************************************
FORM FCODE_TC_DEMARK_LINES USING P_TC_NAME
                                 P_TABLE_NAME
                                 P_MARK_NAME .
*-BEGIN OF LOCAL DATA---------------------------------------------*
  DATA L_TABLE_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>      TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.
*-END OF LOCAL DATA-----------------------------------------------*

  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* demark all filled lines
  LOOP AT <TABLE> ASSIGNING <WA>.
*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.
    <MARK_FIELD> = SPACE.
  ENDLOOP.

ENDFORM.                                       "fcode_tc_mark_lines


*******************************************************************
*      Module  STATUS_9000  OUTPUT
*******************************************************************
*       text
*******************************************************************
MODULE STATUS_9000 OUTPUT.

  SET PF-STATUS 'VALI'.
  SET TITLEBAR 'VALI'.

ENDMODULE.                                    " STATUS_9000  OUTPUT


*******************************************************************
*      Module  USER_COMMAND_9000  INPUT
*******************************************************************
*       text
*******************************************************************
MODULE USER_COMMAND_9000 INPUT.

  CASE OK_CODE.
    WHEN 'VALI' OR 'STOP' OR 'RW'.
      Y_SAVE_CODE  = OK_CODE.
      SET SCREEN 0. LEAVE SCREEN.
  ENDCASE.
  CLEAR OK_CODE.

ENDMODULE.                               " USER_COMMAND_9000  INPUT