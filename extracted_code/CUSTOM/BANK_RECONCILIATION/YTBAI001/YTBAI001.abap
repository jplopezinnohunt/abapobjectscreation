REPORT YTBAI001 MESSAGE-ID 56
                LINE-SIZE  132
                NO STANDARD PAGE HEADING.

*************************************************************
* PROGRAM	     YTBAI001
* TITLE	     SMARLTLINK INTERFACE : CONVERSION AND FILTER
* AUTHOR	     A. EL MOUCHNINO
* DATE WRITTEN...  05.11.2001
* R/3 RELEASE	     4.6C
*------------------------------------------------------------
* COPIED FROM
*
*------------------------------------------------------------
* PROGRAM TYPE	REPORT
* DEV. CLASS	       YB : Regular Budget
* LOGICAL DB
*************************************************************
* CHANGE HISTORY
* Date    By	Correction Number & Brief Description
* Release
*------------------------------------------------------------
* Date>  <Init>	<Description and correction number>/
* <Release>
*************************************************************

TABLES: T012K, TIBAN.
*AHOUNOU18042007
CONSTANTS C_SOG(13) TYPE C VALUE ':25:SOGEFRPP/'.
*AHOUNOU18042007
DATA: BEGIN OF T_IN OCCURS 0,
         LINE(80),
      END OF T_IN.

DATA: BEGIN OF T_OUT OCCURS 0,
         LINE(80),
      END OF T_OUT.

DATA: W_LINE(80),
      W_LINE1(80),
      W_LINE2(80).
DATA: W_CPT_IN(5) TYPE N,
      W_CPT_OUT(5) TYPE N.
DATA: N(5) TYPE N.
DATA: I(5) TYPE N.




PARAMETERS: P_F_IN  LIKE RLGRAP-FILENAME
      DEFAULT '/usr/sap/D01/conversion/input/TITRBK03/sg2707.txt'.
PARAMETERS: P_F_OUT LIKE RLGRAP-FILENAME
      DEFAULT '/usr/sap/D01/conversion/output/TITRBK03/sg2707out.txt'.


SELECT-OPTIONS: S_ACC FOR T012K-BANKN.
*SELECT-OPTIONS: S_ACC FOR TIBAN-IBAN.

DATA WA_BANKN LIKE T012K-BANKN.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR P_F_IN.
  CALL FUNCTION 'KD_GET_FILENAME_ON_F4'
    EXPORTING
      MASK      = '*.txt'
      STATIC    = 'X'
    CHANGING
      FILE_NAME = P_F_IN.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR P_F_OUT.
  CALL FUNCTION 'KD_GET_FILENAME_ON_F4'
    EXPORTING
      MASK      = '*.txt'
      STATIC    = 'X'
    CHANGING
      FILE_NAME = P_F_OUT.


********************************************
TOP-OF-PAGE.
********************************************
  NEW-PAGE.
* Abap Name
  WRITE: /01  SY-REPID,
* Abap Title
          40  SY-TITLE,
* Date :
          117 'Date:',
               SY-DATUM DD/MM/YYYY.
  WRITE: /01  SY-UNAME,
* Page:
          117 'Page:',
               SY-PAGNO.
  ULINE /(132).


********************************************
START-OF-SELECTION.
********************************************

  PERFORM 01_LOADFILE.


********************************************
END-OF-SELECTION.
********************************************

  PERFORM 03_TREATMENT.

  PERFORM 05_DOWNLOADFILE.

  PERFORM 07_EDITION.


*---------------------------------------------------------------------*
*       FORM 01_LOADFILE
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 01_LOADFILE.

  IF SY-BATCH IS INITIAL.
    PERFORM 011_UPLOAD.
  ELSE.
    PERFORM 013_READ.
  ENDIF.

ENDFORM.                                         " 01_LOADFILE

*---------------------------------------------------------------------*
*       FORM 011_UPLOAD
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 011_UPLOAD.

  CALL FUNCTION 'WS_UPLOAD'
    EXPORTING
      FILENAME                = P_F_IN
      FILETYPE                = 'ASC'
    TABLES
      DATA_TAB                = T_IN
    EXCEPTIONS
      CONVERSION_ERROR        = 1
      FILE_OPEN_ERROR         = 2
      FILE_READ_ERROR         = 3
      INVALID_TYPE            = 4
      NO_BATCH                = 5
      UNKNOWN_ERROR           = 6
      INVALID_TABLE_WIDTH     = 7
      GUI_REFUSE_FILETRANSFER = 8
      CUSTOMER_ERROR          = 9
      OTHERS                  = 10.

  IF SY-SUBRC <> 0.
    WRITE: / 'Upload failed'.
  ENDIF.

ENDFORM.                                         " 011_UPLOAD

*---------------------------------------------------------------------*
*       FORM 013_READ
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 013_READ.

  OPEN DATASET P_F_IN IN TEXT MODE FOR INPUT ENCODING UTF-8.
  IF SY-SUBRC NE 0.
    WRITE: / 'OPEN DATASET FOR INPUT failed'.
    WRITE: / 'Return code : ', SY-SUBRC.
    EXIT.
  ENDIF.

  WHILE SY-SUBRC EQ 0.
    READ DATASET P_F_IN INTO T_IN.
    APPEND T_IN.
  ENDWHILE.

  CLOSE DATASET P_F_IN.

ENDFORM.                                                    " 013_READ

*---------------------------------------------------------------------*
*       FORM 03_TREATMENT
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 03_TREATMENT.

  CLEAR W_LINE.
  CLEAR T_IN.
  DESCRIBE TABLE T_IN LINES N.

  CHECK N > 0.
  I = 1.
  READ TABLE T_IN INDEX I.
  I = I + 1.

* Do not keep blank lines
  WHILE I <= N.
    IF T_IN-LINE(4) = ':20:'.
      W_LINE1 = T_IN-LINE.
    ELSEIF T_IN-LINE(4) = ':25:'.

*AHOUNOU18042007
 CLEAR WA_BANKN.
 IF T_IN-LINE+5(2) NE 'FR'.
   WA_BANKN = T_IN-LINE+23(11) .
 ELSE.
   WA_BANKN = T_IN-LINE+19(11).
 ENDIF.
*AHOUNOU18042007

*      if t_in-line+23(11) in s_acc.
   IF WA_BANKN IN S_ACC.
* keep all line corresponding to the tag 25
        T_OUT-LINE = W_LINE1.
        APPEND T_OUT.
* retrieve bank key
*AHOUNOU18042007
 IF T_IN-LINE+5(2) NE 'FR'.
        CONCATENATE T_IN-LINE+0(13)
                    T_IN-LINE+23
               INTO W_LINE2.
 ELSE.
         CONCATENATE C_SOG
                    T_IN-LINE+19(11)
               INTO W_LINE2.

 ENDIF.
*AHOUNOU18042007

        CLEAR T_IN.
        T_IN = W_LINE2.
* go on until next block
        WHILE ( I <= N
         AND T_IN-LINE(1) NE '-' ).
          CLEAR T_OUT.
          T_OUT-LINE = T_IN-LINE.
          APPEND T_OUT.
          READ TABLE T_IN INDEX I.
          I = I + 1.
        ENDWHILE.
        IF T_IN-LINE(1) EQ '-'.
          T_OUT-LINE = T_IN-LINE.
          APPEND T_OUT.
        ENDIF.

      ENDIF.
    ENDIF.

    READ TABLE T_IN INDEX I.
    I = I + 1.

  ENDWHILE.

* the last line is always blank line
* do not treat

ENDFORM.                                         " 03_TREATMENT

*---------------------------------------------------------------------*
*       FORM 05_DOWNLOADFILE
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 05_DOWNLOADFILE.
  IF SY-BATCH IS INITIAL.
    PERFORM 051_DOWNLOAD.
  ELSE.
    PERFORM 053_TRANSFER.
  ENDIF.

ENDFORM.                                         " 05_DOWNLOADFILE.

*---------------------------------------------------------------------*
*       FORM 051_DOWNLOAD
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 051_DOWNLOAD.

  CALL FUNCTION 'WS_DOWNLOAD'
    EXPORTING
      FILENAME                = P_F_OUT
      FILETYPE                = 'ASC'
    TABLES
      DATA_TAB                = T_OUT
    EXCEPTIONS
      FILE_OPEN_ERROR         = 1
      FILE_WRITE_ERROR        = 2
      INVALID_FILESIZE        = 3
      INVALID_TYPE            = 4
      NO_BATCH                = 5
      UNKNOWN_ERROR           = 6
      INVALID_TABLE_WIDTH     = 7
      GUI_REFUSE_FILETRANSFER = 8
      CUSTOMER_ERROR          = 9
      OTHERS                  = 10.

  IF SY-SUBRC <> 0.
    WRITE: / 'Download failed'.
  ENDIF.

ENDFORM.                               " 03_DOWNLOAD

*---------------------------------------------------------------------*
*       FORM 053_TRANSFER
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 053_TRANSFER.

  OPEN DATASET P_F_OUT IN TEXT MODE FOR OUTPUT ENCODING UTF-8.
  IF SY-SUBRC NE 0.
    WRITE: /  'OPEN DATASET FOR OUTPUT failed'.
    EXIT.
  ENDIF.

  CLEAR T_OUT.
  LOOP AT T_OUT.
    TRANSFER T_OUT TO P_F_OUT.
  ENDLOOP.

  CLOSE DATASET P_F_OUT.

ENDFORM.                                         " 053_TRANSFER

*---------------------------------------------------------------------*
*       FORM 07_EDITION
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM 07_EDITION.

  DESCRIBE TABLE T_IN  LINES W_CPT_IN.
  DESCRIBE TABLE T_OUT  LINES W_CPT_OUT.

  WRITE: /.
  WRITE: / 'Input file    :', P_F_IN.
  WRITE: / 'Lines read    :', W_CPT_IN.
  WRITE: /.
  WRITE: / 'Output file   :', P_F_OUT.
  WRITE: / 'Lines written :', W_CPT_OUT.

ENDFORM.                                         " 07_EDITION

********************************************************************
*                         END OF LISTING                           *
********************************************************************