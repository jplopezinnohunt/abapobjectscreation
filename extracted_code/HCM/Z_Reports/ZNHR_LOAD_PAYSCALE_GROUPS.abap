*&---------------------------------------------------------------------*
*& Report  ZNYHR_LOAD_PAYSCALE_GROUPS                                  *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*
*----------------------------------------------------------------------*
*                             UNICEF                                   *
*----------------------------------------------------------------------*
* Program name               ZNYHR_LOAD_PAYSCALE_GROUPS                *
* Functional Area            HR                                        *
* Program Type               Conversion                                *
* Responsible/Analyst        Atul Vayda                               *
* Author                     Kalyan Yenneti                            *
* Creation Date              10/06/2003                                *
* Change Request Number      0001                                      *
* CTS Number                 DEVK936661                                *
*----------------------------------------------------------------------*
* Description             (1)This program is for loading the Payscale
*                            Groups data into the New SAP HR table
*                            V_T510_C
*                         (2) This will be used for one time data load
*                         (3)
*----------------------------------------------------------------------*
* Notes
* Correction Number        0001                                        *
*----------------------------------------------------------------------*
* Modification Log
* Programmer          Date             Modif
* Kalyan Yenneti
*
* Correction Number 0001
* CTS                DEVK937185
* Notes   Handle the Transport number Screen
*----------------------------------------------------------------------*
* Modification Log
* Programmer          Date             Modif
* Kalyan Yenneti      12/29/03
*
* Correction Number 0001
* Currency Changes
* CTS   DEVK937265
*----------------------------------------------------------------------*
* Modification Log
* Programmer          Date             Modif
* Kalyan Yenneti      12/29/03
*
* Correction Number 0001
* Changes for Call transaction
* CTS   DEVK937289
*----------------------------------------------------------------------*
* Modification Log
* Programmer          Date             Modif
* Taneeja Rudraraju   01 Oct 2004
*
* Correction Number 0001
* Changes for Call transaction
* CTS   DEVK940109
*----------------------------------------------------------------------*
REPORT  ZNYHR_LOAD_PAYSCALE_GROUPS
                line-size 132
                 line-count 65
*                message-id z1
                 no standard page heading.
*----------------------------------------------------------
*                       T A B L E S
*----------------------------------------------------------
tables: V_T510_C,    " Pay Scale Groups (All)
        t510,        " Pay Scale Groups
        t510f,
        TCURX,
        t100.
*----------------------------------------------------------------------*
*                 G L O B A L   D A T A                                *
*----------------------------------------------------------------------*
data: t_lines type i.
data: t_no(2).
data: t_submit(1).
data: t_times like sy-index.
data: t_check like sy-index.
data: t_bdc like sy-index.
*----------------------------------------------------------------------*
*   I N T E R N A L  T A B L E S   /    S T R U C T U R E S            *
*----------------------------------------------------------------------*
* Internal table for the Input File upload
data: begin of it_data occurs 10,
    molga like V_T510_C-MOLGA,  " Country Grouping
    trfar like V_T510_C-TRFAR,  " Pay scale type
    trfgb like V_T510_C-TRFGB,  " Pay Scale Area
    trfkz like V_T510_C-TRFKZ,  " ES grouping
    trfgr like V_T510_C-TRFGR,  " Pay Scale Group
    TRFST like V_T510_C-TRFST,  " Pay Scale Level
    lgart like V_T510_C-LGART,  " Wage Type
    begda like V_T510_C-BEGDA,  " Start Date
    endda like V_T510_C-ENDDA,  " End Date
*    betrg like V_T510_C-BETRG,  " Wage Type Amount for Payments
    betrg(12),    "  type p decimals 2,
 end of it_data.
data: it_records like it_data occurs 10 with header line.
data: it_success like it_data occurs 10 with header line.
data: it_fail like it_data occurs 10 with header line.
* Internal table for the BDC data
*  Batchinputdata of single transaction
DATA: BEGIN OF BDCDATA OCCURS 0.
        INCLUDE STRUCTURE BDCDATA.
DATA: END OF BDCDATA.
DATA: BEGIN OF IT_MESSAGES OCCURS 0.
        INCLUDE STRUCTURE BDCMSGCOLL.
DATA: END OF IT_MESSAGES.
* For Errors
data: begin of it_errors occurs 0,
         TEXT(150),
   end of it_errors.
*----------------------------------------------------------------------*
*          S E L E C T I O N  O P T I O N S/ P A R A M E T E R S       *
*----------------------------------------------------------------------*
parameters: P_f_name LIKE RLGRAP-FILENAME DEFAULT
             'C:\ABAP Unicef HR\Conversions'       obligatory.
parameters: p_call as checkbox default 'X'.
parameters: p_trans like TRHEADER-TRKORR
 default 'GLDK900092'.
*----------------------------------------------------------------------*
*                    AT SELECTION SCREEN                               *
*----------------------------------------------------------------------*
AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_f_name.
  CALL FUNCTION 'KD_GET_FILENAME_ON_F4'
    EXPORTING
      mask      = '*.xls'
      static    = 'X'
    CHANGING
      file_name = p_f_name.
*----------------------------------------------------------------------*
*                  S T A R T  OF  S E L E C T I O N                    *
*----------------------------------------------------------------------*
start-of-selection.
* Load the Data from the File
  perform upload_file_data.
* Check The currency - To Handle decimals
*  perform check_currency.
  clear t_lines.
  describe table it_data lines t_lines.
  if t_lines ne 0.
    perform bdc_submit_data.
  endif.
end-of-selection.
  perform write_report.
TOP-OF-PAGE.
* Common Header
  PERFORM WRITE_REPORT_HEADER .
*&---------------------------------------------------------------------*
*&      Form  upload_file_data
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM upload_file_data .
  data: p_file type string.
  p_file = p_f_name.
* Upload the File from the Excel File
  CALL FUNCTION 'Z_FLS_FILE_UPLOAD_DOWNLOAD'
   EXPORTING
     P_FILENAME              = P_file
     P_UPLOAD_DOWNLOAD       = 'U'
     P_FILE_EXT              = 'XLS'
*      P_APPEND                = ' '
*      P_DATEMODE              = 'X'
*    IMPORTING
*      P_FILELENGTH            =
   TABLES
     P_DATA_TAB              = it_data
  EXCEPTIONS
    OTHERS                  = 1
*      OTHERS                  = 2
           .
  IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    write: / 'Subrc', sy-subrc, 'File Upload Failed'.
  else.
*  delete   it_data where trfst ne '01'.
* Now fill in the Default value for the Group
* If the Record Already Exists - then do not load the Data
    loop at it_data.
*      it_data-trfkz = '3'.
      select single * from T510 where
                           molga = it_data-molga and
                          trfar = it_data-TRFAR and  " Pay scale type
                           trfgb = it_data-TRFGB and  " Pay Scale Area
                           trfkz  = it_data-TRFKZ and " ES grouping
                           trfgr =  it_data-TRFGR and " Pay Scale Group
                           TRFST =  it_data-TRFST and " Pay Scale Level
                           lgart =  it_data-LGART    and " Wage Type
*                           begda like V_T510_C-BEGDA,  " Start Date
                            endda = it_data-endda. " End Date
      if sy-subrc eq 0.
        it_fail = it_data.
        append it_fail.
        clear it_fail.
        delete it_data.
      endif.
    endloop.
*
    loop at it_data.
      write it_data-begda to it_data-begda ddmmyy.
*      write it_data-endda to it_data-endda ddmmyyyy.
      if it_data-endda+0(4) eq '9999'.
        it_data-endda = '31129999'.
      else.
        write it_data-endda to it_data-endda ddmmyy.
      endif.
*      it_data-trfkz = '3'.
      modify it_data transporting trfkz begda endda.
      clear it_data.
    endloop.
  ENDIF.
*
** If the Record Already Exists - then do not load the Data
*  loop at it_data.
*
*    select single * from T510 where
*                         molga = it_data-molga and
*                         trfar = it_data-TRFAR and  " Pay scale type
*                         trfgb = it_data-TRFGB and  " Pay Scale Area
*                         trfkz  = it_data-TRFKZ and " ES grouping
*                         trfgr =  it_data-TRFGR and " Pay Scale Group
*                         TRFST =  it_data-TRFST and " Pay Scale Level
*                         lgart =  it_data-LGART and " Wage Type
**                           begda like V_T510_C-BEGDA,  " Start Date
*                         endda = it_data-endda. " End Date
*
*
*  if sy-subrc eq 0.
*
*     it_fail = it_data.
*     append it_fail.
*     clear it_fail.
*
*    delete it_data.
*
*  endif.
*  endloop.
  sort it_data by   molga
                    trfar
                    trfgb
                    trfkz
                    trfgr
                    TRFST
                    lgart
                    begda
                    endda.
  DELETE ADJACENT DUPLICATES FROM it_data comparing
                      molga
                      trfar
                      trfgb
                      trfkz
                      trfgr
                      TRFST
                      lgart
*                     begda
                      endda.
ENDFORM.                    " upload_file_data
*&---------------------------------------------------------------------*
*&      Form  bdc_submit_data
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM bdc_submit_data .
  data: t_count type i.
* Only of the Calling method is not call Tranaction
  if p_call ne 'X'.
    PERFORM OPEN_GROUP.
  endif.
* Initialize the Data
  t_submit = 'N'.
  REFRESH BDCDATA.
  REFRESH IT_MESSAGES.
  if t_lines le 18.
    t_times = 1.
  else.
* Integer Division
    t_times = t_lines div 18.
    t_times = t_times + 1.
  endif.
  t_bdc = 1.
  do t_times times.
    perform build_bdc.
  enddo.
* Close BDC Group
  if  p_call ne 'X'.
    CALL FUNCTION 'BDC_CLOSE_GROUP'.
  endif.
ENDFORM.                    " bdc_submit_data
*&---------------------------------------------------------------------*
*&      Form  build_bdc
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM build_bdc .
  data: t_current like sy-index.
  Data: t_loop_times like sy-index.
  data: t_times1 like sy-index,
        t_times2 like sy-index.
  data: t_index like sy-index,
        t_index2 like sy-index.
  data: t_molga(20),
        t_TRFAR(20),   " Pay scale type
        t_trfgb(20),   " Pay Scale Area
        t_trfkz(20),    " ES grouping
        t_trfgr(20),    " Pay Scale Group
        t_TRFST(20),    " Pay Scale Level
        t_lgart(20),    " Wage Type
        t_begda(20),    " Start Date
        t_endda(20),    " End Date
        t_betrg(20).
  if sy-index eq t_lines.
    t_submit = 'Y'.
  endif.
  PERFORM BDC_DYNPRO      USING  'SAPMSVMA' '0100' 'X'.
  PERFORM BDC_FIELD       USING 'VIEWNAME'  'V_T510_C'.
  PERFORM BDC_FIELD       USING 'VIMDYNFLDS-LTD_DTA_NO'  'X'.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'    '=UPD'.
  PERFORM BDC_DYNPRO      USING  'SAPL3201' '0005' 'X'.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '=NEWL'.
  PERFORM BDC_DYNPRO      USING  'SAPL3201' '0005' 'X'.
  clear t_current.
  clear t_index.
  clear t_no.
  t_no = '01'.
* If the No of Lines are less than or Equal to 18
  if t_lines le 18.
    t_loop_times = t_lines.
    t_index = 1.
* If More than 18
  else.
    t_times1 = sy-index * 18.
* For limiting BDC sessions to 2000
    t_times2 =  t_bdc * 18.
    t_index = t_times1 - 17.
    if t_times1 le t_lines.
      t_loop_times = 18.
    else.
      t_loop_times =  t_lines mod 18.
    endif.
  endif.
  clear t_check.
  refresh it_records.
  t_index2 = t_index.
  do t_loop_times times.
    clear: t_molga(20),
           t_TRFAR(20),   " Pay scale type
           t_trfgb(20),   " Pay Scale Area
           t_trfkz(20),    " ES grouping
           t_trfgr(20),    " Pay Scale Group
           t_TRFST(20),    " Pay Scale Level
           t_lgart(20),    " Wage Type
           t_begda(20),    " Start Date
           t_endda(20),    " End Date
           t_betrg(20).
    read table it_data index t_index.
    if sy-subrc eq 0.
      concatenate 'V_T510_C-MOLGA' '(' t_no ')' into t_molga.
      PERFORM BDC_FIELD       USING t_molga   it_data-molga.
      concatenate 'V_T510_C-TRFAR' '(' t_no ')' into t_trfar.
      PERFORM BDC_FIELD       USING  t_TRFAR  it_data-trfar.
      concatenate 'V_T510_C-TRFGB' '(' t_no ')' into t_TRFGB.
      PERFORM BDC_FIELD       USING  t_TRFGB it_data-trfgb.
      concatenate 'V_T510_C-TRFKZ' '(' t_no ')' into t_TRFKZ.
      PERFORM BDC_FIELD       USING  t_TRFKZ   it_data-trfkz.
      concatenate 'V_T510_C-TRFGR' '(' t_no ')' into t_TRFGR.
      PERFORM BDC_FIELD       USING  t_TRFGR  it_data-TRFGR.
      concatenate 'V_T510_C-TRFST' '(' t_no ')' into t_TRFST.
      PERFORM BDC_FIELD       USING  t_TRFST it_data-TRFST.
      concatenate 'V_T510_C-LGART' '(' t_no ')' into t_LGART.
      PERFORM BDC_FIELD       USING  t_LGART  it_data-lgart.
      concatenate 'V_T510_C-BEGDA' '(' t_no ')' into t_BEGDA.
      PERFORM BDC_FIELD       USING  t_BEGDA   it_data-begda.
      concatenate 'V_T510_C-ENDDA' '(' t_no ')' into t_ENDDA.
      PERFORM BDC_FIELD       USING  t_ENDDA  it_data-endda.
      concatenate 'V_T510_C-BETRG' '(' t_no ')' into t_BETRG.
      perform BDC_FIELD       USING   t_BETRG  it_data-betrg.
      it_records = it_data.
      append it_records.
      clear it_records.
    endif.
    t_index = t_index + 1.
    t_no = t_no + 1.
  enddo.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '/00'.
  PERFORM BDC_DYNPRO      USING  'SAPL3201' '0005' 'X'.
  t_no = '01'.
  do t_loop_times times.
    clear: t_molga(20),
           t_TRFAR(20),   " Pay scale type
           t_trfgb(20),   " Pay Scale Area
           t_trfkz(20),    " ES grouping
           t_trfgr(20),    " Pay Scale Group
           t_TRFST(20),    " Pay Scale Level
           t_lgart(20),    " Wage Type
           t_begda(20),    " Start Date
           t_endda(20),    " End Date
           t_betrg(20).
    read table it_data index t_index2.
    if sy-subrc eq 0.
      concatenate 'V_T510_C-BETRG' '(' t_no ')' into t_BETRG.
      perform BDC_FIELD       USING   t_BETRG  it_data-betrg.
    endif.
    t_index2 = t_index2 + 1.
    t_no = t_no + 1.
  enddo.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '/00'.
  PERFORM BDC_DYNPRO      USING  'SAPL3201' '0005' 'X'.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '=SAVE'.
* New Popup for the Transport Number
  PERFORM BDC_DYNPRO      USING  'SAPLSTRD' '0300' 'X'.
  PERFORM BDC_FIELD       USING 'KO008-TRKORR'  p_trans.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '=LOCK'.
* End -
  PERFORM BDC_DYNPRO      USING  'SAPL3201' '0005' 'X'.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '=ENDE'.
  perform bdc_dynpro using 'SAPMSVMA' '0100' 'X'.
  PERFORM BDC_FIELD       USING 'BDC_OKCODE'  '=ENDE'.
* Call the Transaction
  perform submit_bdc.
  t_bdc = t_bdc + 1.
  if p_call ne 'X'.
    if t_times2 ge 1800.
      CALL FUNCTION 'BDC_CLOSE_GROUP'.
      perform open_group.
    endif.
  endif.
ENDFORM.                    " build_bdc
*&---------------------------------------------------------------------*
*&      Form  BDC_DYNPRO
*&---------------------------------------------------------------------*
*       text  Start new screen
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM BDC_DYNPRO USING PROGRAM DYNPRO DYNBEGIN.
  CLEAR BDCDATA.
  BDCDATA-PROGRAM  = PROGRAM.
  BDCDATA-DYNPRO   = DYNPRO.
  BDCDATA-DYNBEGIN = DYNBEGIN.
  APPEND BDCDATA.
ENDFORM.                    "BDC_DYNPRO
*&---------------------------------------------------------------------*
*&      Form  BDC_FIELD
*&---------------------------------------------------------------------*
*       text  Insert field
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM BDC_FIELD USING FNAM FVAL.
  IF FVAL <> SPACE.
    CLEAR BDCDATA.
    BDCDATA-FNAM = FNAM.
    BDCDATA-FVAL = FVAL.
    IF FNAM EQ 'EKKO-WKURS'.
      SHIFT BDCDATA-FVAL LEFT DELETING LEADING SPACE.
    ENDIF.
    APPEND BDCDATA.
  ENDIF.
ENDFORM.                    "BDC_FIELD
*&---------------------------------------------------------------------*
*&      Form  submit_bdc
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM submit_bdc .
  if p_call eq 'X'.
    refresh it_messages.
    CALL TRANSACTION 'SM30' USING BDCDATA
                    MODE 'E'
              MESSAGES INTO   IT_MESSAGES.
    if sy-subrc ne 0.
      loop at IT_MESSAGES where MSGTYP = 'E'.
        SELECT SINGLE TEXT FROM T100 INTO (T100-TEXT)
                           WHERE SPRSL EQ 'EN' AND
                                 ARBGB EQ IT_MESSAGES-MSGID AND
                                 MSGNR EQ IT_MESSAGES-MSGNR.
*      CONDENSE IT_MESSAGES-MSGV1 NO-GAPS.
*      CONDENSE IT_MESSAGES-MSGV2 NO-GAPS.
*      CONDENSE IT_MESSAGES-MSGV3 NO-GAPS.
        REPLACE '&' WITH IT_MESSAGES-MSGV1+0(20) INTO T100-TEXT.
        CONDENSE T100-TEXT NO-GAPS.
        REPLACE '&' WITH IT_MESSAGES-MSGV2+0(20) INTO T100-TEXT.
        CONDENSE T100-TEXT NO-GAPS.
        REPLACE '&' WITH IT_MESSAGES-MSGV3 INTO T100-TEXT.
        CONDENSE T100-TEXT NO-GAPS.
        IT_ERRORS-TEXT  = T100-TEXT.
        APPEND IT_ERRORS.
        CLEAR  IT_ERRORS.
      endloop.
* Failed Records -
      loop at it_records.
        it_fail = it_records.
        append it_fail.
        clear it_fail.
      endloop.
* If the Call transaction is Success -
    else.
      loop at it_recorDs.
        it_success  = it_records.
        append it_success.
        clear  it_success.
      endloop.
    endif.
  else.
* Submit the Data for the Transaction
    CALL FUNCTION 'BDC_INSERT'
      EXPORTING
        TCODE     = 'SM30'
      TABLES
        DYNPROTAB = bdcdata.
    if sy-subrc eq 0.
      loop at it_records.
        it_success  = it_records.
        append it_success.
        clear  it_success.
      endloop.
    endif.
  endif.
  refresh bdcdata.
ENDFORM.                    " submit_bdc
*&---------------------------------------------------------------------*
*&      Form  OPEN_GROUP
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM OPEN_GROUP .
  DATA: GROUP_NAME(12).
  CONCATENATE 'PGrp' SY-UZEIT INTO GROUP_NAME.
  CALL FUNCTION 'BDC_OPEN_GROUP'
       EXPORTING
*           CLIENT              = SY-MANDT
*           DEST                = FILLER8
            GROUP               = GROUP_NAME
*           HOLDDATE            = FILLER8
*           KEEP                = FILLER1
            USER                = SY-UNAME
*           RECORD              = FILLER1
*      IMPORTING
*           QID                 =
       EXCEPTIONS
            CLIENT_INVALID      = 1
            DESTINATION_INVALID = 2
            GROUP_INVALID       = 3
            GROUP_IS_LOCKED     = 4
            HOLDDATE_INVALID    = 5
            INTERNAL_ERROR      = 6
            QUEUE_ERROR         = 7
            RUNNING             = 8
            SYSTEM_LOCK_ERROR   = 9
            USER_INVALID        = 10
            OTHERS              = 11.
ENDFORM.                    " OPEN_GROUP
*&---------------------------------------------------------------------*
*&      Form  write_report
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM write_report .
  if p_call eq 'X'.
* For the Call transaction - Succcess Records
    format color col_positive.
    write: / 'Success Records'.
    format color col_normal.
    loop at it_success.
      write: / it_success-molga, "  Country Grouping
                it_success-trfar, " Pay scale type
              it_success-trfgb ,  " Pay Scale Area
            it_success-trfkz ,  " ES grouping
        it_success-trfgr,  " Pay Scale Group
        it_success-TRFST ,  " Pay Scale Level
        it_success-lgart ,  " Wage Type
*        it_success-begda ,  " Start Date
*        it_success-endda ,  " End Date
        it_success-betrg.
    endloop.
* Error Report in the Call Transaction
    format color col_negative.
    write: / 'Error Report - '.
    format color col_normal.
    loop at it_errors.
      write: / it_errors-text.
    endloop.
* Error Records
    skip 2.
    loop at  it_fail.
      write: / it_fail-molga, "  Country Grouping
                      it_fail-trfar, " Pay scale type
                    it_fail-trfgb ,  " Pay Scale Area
                  it_fail-trfkz ,  " ES grouping
              it_fail-trfgr,  " Pay Scale Group
              it_fail-TRFST ,  " Pay Scale Level
              it_fail-lgart ,  " Wage Type
*        it_success-begda ,  " Start Date
*        it_success-endda ,  " End Date
              it_fail-betrg.
    endloop.
  else.
* Success Records in the BDC session Method
    write: / 'The Following Records are Submitted to the BDC Session'.
    format color col_normal.
    loop at it_success.
      write: / it_success-molga, "  Country Grouping
                it_success-trfar, " Pay scale type
              it_success-trfgb ,  " Pay Scale Area
            It_success-trfkz ,  " ES grouping
        it_success-trfgr,  " Pay Scale Group
        it_success-TRFST ,  " Pay Scale Level
        it_success-lgart ,  " Wage Type
*        it_success-begda yyyy/dd/mm,  " Start Date
*        it_success-endda yyyy/dd/mm ,  " End Date
        it_success-betrg.
    endloop.
  endif.
ENDFORM.                    " write_report
*&---------------------------------------------------------------------*
*&      Form  WRITE_REPORT_HEADER
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM WRITE_REPORT_HEADER .
  constants: page_text_length like sy-linsz value 17,
             report_id_length like sy-linsz value 25.
*- Data Definition
  data: general_id(43)       type c,
        report(8)            type c,
        text_key(9)          type c,
        title_position       type i,
        page_position        type i,
        title_size           type i.
*- Sizing
  title_size     = strlen( sy-title ).
  title_position = ( sy-linsz - page_text_length - report_id_length
                              - title_size ) / 2.
  page_position  = sy-linsz - page_text_length.
  if title_position ge 0.
    title_position = report_id_length + title_position.
  else.
    title_size     = sy-linsz - report_id_length - page_text_length - 3.
    title_position = report_id_length + 2.
  endif.
*- Header Formatting
  format color col_heading on.
*- Date & Time (NY)
  write: / sy-datum using edit mask '__/__/____',
           sy-uzeit using edit mask '__:__:__', '(NY)'.
*- Title
  write at title_position(title_size) sy-title.
*- Page
  write:at page_position 'Page:', sy-pagno.
  write: at sy-linsz ' '.
*- System ID/Client/Report name......................*
  concatenate sy-sysid sy-mandt sy-repid
              into general_id separated by '/'.
  condense general_id no-gaps.
  write at /(sy-linsz) general_id.
  write: at page_position 'User:', sy-uname.
  format color col_heading off.
  uline.
ENDFORM.                    " WRITE_REPORT_HEADER
*&---------------------------------------------------------------------*
*&      Form  check_currency
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM check_currency .
  DATA: digits TYPE i VALUE 11.
  data: t_betrg2 like v_t510_c-betrg.
  data: t_betrg1 like BAPICURR-BAPICURR.
  loop at it_data.
    select single *  from t510f where
                         molga eq it_data-molga and
                         trfar eq it_data-trfar and
                         trfgb eq it_data-trfgb and
                         trfkz eq it_data-trfkz and
                         endda ge it_data-endda.
    if sy-subrc eq 0.
      t_betrg1 = it_data-betrg.
*      CALL FUNCTION 'BAPI_CURRENCY_CONV_TO_INTERNAL'
*        EXPORTING
*          CURRENCY             = t510f-waers
*          AMOUNT_EXTERNAL      = t_BETRG1
*          MAX_NUMBER_OF_DIGITS = digits
*        IMPORTING
*          AMOUNT_INTERNAL      = t_BETRG1
*        EXCEPTIONS
*          OTHERS               = 1.
      SELECT SINGLE * FROM TCURX WHERE CURRKEY =  t510f-waers.
      IF SY-SUBRC eq  0.
        it_data-betrg =
                 it_data-betrg / ( 10 ** ( 2 - TCURX-CURRDEC ) ).
        MODIFY it_data  TRANSPORTING betrg.
        CLEAR  it_data.
      ENDIF.
*      if sy-subrc eq 0.
*        if t_betrg1 ne it_data-betrg.
*
*
*          it_data-betrg = t_betrg1.
*
**          shift it_data-betrg deleting trailing
*          modify it_data transporting betrg.
*
*        endif.
*
*      endif.
    endif.
  endloop.
ENDFORM.                    " check_currency