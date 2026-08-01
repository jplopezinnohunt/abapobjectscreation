*&---------------------------------------------------------------------*
*& Report  YFI_VENDOR_TITLE_CHANGE                                     *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YFI_VENDOR_TITLE_CHANGE                 .


PARAMETERS: P_FILE LIKE RLGRAP-FILENAME DEFAULT 'c:\vendors.csv',
            P_DELIM DEFAULT ';'. "Delimiter

DATA: BEGIN OF T_WTAB OCCURS 0,
        STR1(255),
      END OF T_WTAB.

DATA: BEGIN OF T_BDC OCCURS 0.
        INCLUDE STRUCTURE BDCDATA.
DATA: END OF T_BDC.

DATA: W_POS TYPE I,
      W_STR(255),
      W_VENDOR LIKE LFA1-LIFNR,
      W_TITLE LIKE LFA1-ANRED.


START-OF-SELECTION.

***read file
CALL FUNCTION 'WS_UPLOAD'
  EXPORTING
*   CODEPAGE                      = ' '
    FILENAME                      = P_FILE
*   FILETYPE                      = 'ASC'
*   HEADLEN                       = ' '
*   LINE_EXIT                     = ' '
*   TRUNCLEN                      = ' '
*   USER_FORM                     = ' '
*   USER_PROG                     = ' '
*   DAT_D_FORMAT                  = ' '
* IMPORTING
*   FILELENGTH                    =
  TABLES
    DATA_TAB                      = T_WTAB
 EXCEPTIONS
   CONVERSION_ERROR              = 1
   FILE_OPEN_ERROR               = 2
   FILE_READ_ERROR               = 3
   INVALID_TYPE                  = 4
   NO_BATCH                      = 5
   UNKNOWN_ERROR                 = 6
   INVALID_TABLE_WIDTH           = 7
   GUI_REFUSE_FILETRANSFER       = 8
   CUSTOMER_ERROR                = 9
   NO_AUTHORITY                  = 10
   OTHERS                        = 11
          .
IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.


***loop at file data
LOOP AT T_WTAB.
*****prepare data table  for Batch input
  REFRESH T_BDC.
  CLEAR: W_POS, W_STR, W_VENDOR, W_TITLE.
  W_STR = T_WTAB-STR1.
  SEARCH W_STR FOR P_DELIM.
  W_POS = SY-FDPOS.
  W_VENDOR = W_STR(W_POS).
  W_POS = W_POS + 1.
  W_TITLE = W_STR+W_POS(3).

  CLEAR T_BDC.
  T_BDC-PROGRAM = 'SAPMF02K'.
  T_BDC-DYNPRO = '0106'.
  T_BDC-DYNBEGIN = 'X'.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-FNAM = 'RF02K-LIFNR'.
  T_BDC-FVAL = W_VENDOR.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-FNAM = 'RF02K-D0110'.
  T_BDC-FVAL = 'X'.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-FNAM = 'BDC_OKCODE'.
  T_BDC-FVAL = 'ENTE'.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-PROGRAM = 'SAPMF02K'.
  T_BDC-DYNPRO = '0110'.
  T_BDC-DYNBEGIN = 'X'.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-FNAM = 'LFA1-ANRED'.
  T_BDC-FVAL = W_TITLE.
  APPEND T_BDC.

  CLEAR T_BDC.
  T_BDC-FNAM = 'BDC_OKCODE'.
  T_BDC-FVAL = 'UPDA'.
  APPEND T_BDC.

  CALL TRANSACTION 'FK02' USING T_BDC MODE 'A'.

  IF SY-SUBRC = 0.
    FORMAT COLOR 2.
   ELSE.
     FORMAT COLOR 6.
  ENDIF.
  WRITE: / W_VENDOR, W_TITLE, SY-SUBRC.
ENDLOOP. "t_wtab

END-OF-SELECTION.