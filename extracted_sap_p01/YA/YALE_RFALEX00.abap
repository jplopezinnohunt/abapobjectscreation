*&---------------------------------------------------------------------*
*& Report  YALE_RFALEX00                                               *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YALE_RFALEX00.



PARAMETERS: P_DATE LIKE SY-DATUM DEFAULT SY-DATUM.


START-OF-SELECTION.

SUBMIT RFALEX00 USING SELECTION-SET 'ALEDAILY'
                WITH DATE = P_DATE.

END-OF-SELECTION.