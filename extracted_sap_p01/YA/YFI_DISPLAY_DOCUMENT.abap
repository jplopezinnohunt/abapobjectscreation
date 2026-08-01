*&---------------------------------------------------------------------*
*& Report YFI_DISPLAY_DOCUMENT
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_DISPLAY_DOCUMENT.

INCLUDE RFEPOSC5.

PARAMETERS P_BUKRS TYPE BUKRS.
PARAMETERS P_BELNR TYPE BELNR_D.
PARAMETERS P_GJAHR TYPE GJAHR.
PARAMETERS P_BUZEI TYPE BUZEI.

START-OF-SELECTION.

  BUZTAB-BUKRS = P_BUKRS.
  BUZTAB-BELNR = P_BELNR.
  BUZTAB-GJAHR = P_GJAHR.
  BUZTAB-BUZEI = P_BUZEI.
  APPEND BUZTAB.

  BUZTAB-ZEILE = 1.

  CALL DIALOG 'RF_ZEILEN_ANZEIGE'
            EXPORTING
              BUZTAB
              BUZTAB-ZEILE
              TCODE         FROM 'FB03'
            IMPORTING
              BUZTAB.