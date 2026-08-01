*&---------------------------------------------------------------------*
*& Report  YFI_VENDOR_TITLE_CLEAN                                      *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YFI_VENDOR_TITLE_CLEAN                  .

TABLES: LFA1, ADRC.

SELECT-OPTIONS: P_LIFNR FOR LFA1-LIFNR.

START-OF-SELECTION.

CLEAR LFA1.
SELECT *
      FROM LFA1
      WHERE LIFNR IN P_LIFNR.
  CLEAR ADRC.
  SELECT SINGLE *
        FROM ADRC
        WHERE ADDRNUMBER = LFA1-ADRNR.
  CLEAR LFA1-ANRED.
  UPDATE LFA1.
  CLEAR ADRC-TITLE.
  UPDATE ADRC.

  WRITE: / LFA1-LIFNR, LFA1-ANRED, LFA1-ADRNR, ADRC-TITLE.
ENDSELECT. "lfa1

END-OF-SELECTION.