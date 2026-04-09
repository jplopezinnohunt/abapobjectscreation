* Include-Report RPUMKC00 für Aufruf der Merkmale und Rückgabe

TABLES: T100."#EC NEEDED

*---------------------------------------------------------------------*
*       FORM RE549D                                                   *
*---------------------------------------------------------------------*
*       Aufruf der Tabelle 549D mit Feldrückgabe.                     *
*---------------------------------------------------------------------*
*       IN : MERKMAL  - Name des Merkmals                             *
*            KIND_OF_ERROR - Art der Fehlerausgabe:                   *
*                             ' ' - keine Fehler-Ausgabe              *
*                             '1' - Ausgabe mit WRITE-Anweisung       *
*                             '2' - Ausgabe mit I-Message             *
*                             '3' - Ausgabe mit S-Message             *
*                             '4' - Ausgabe mit E-Message             *
*       OUT: BACK     - Rückgabe des Feldinhalts                      *
*            STATUS   - Return-Code                                   *
*                        '0' - o.k., Zuweisung hat stattgefunden      *
*                               (RPUMKG00) , initial                  *
*                        '1' - kann nicht vorkommen (RPUMKG00)        *
*                        '2' - Operation ERROR (RPUMKG00)             *
*                        '3' - keine Zuweisung, kein Fehler           *
*                        '4' - Merkmal ist nicht generiert            *
*                        '5' - kann eigentlich nicht vorkommen; im    *
*                               Feld FUNID steht ein ungültiger Wert  *
*                        '6' - Aufruf im Report: Feldrückgabe,        *
*                               Rückgabeart in PE03: Tabellenrückgabe *
*                        '7' - Aufruf im Report: Tabellenrückgabe,    *
*                               Rückgabeart in PE03: Feldrückgabe     *
*                        '8' - neu zu 4.5B: siehe message e568(p0)    *
*---------------------------------------------------------------------*
FORM RE549D USING
            MERKMAL      TYPE C
            KIND_OF_ERROR
            BACK
            STATUS.
*---------------------------------------------------------------------*
  DATA          STRUC(5).              " VLDAHRK006111
  DATA          FEATURE LIKE T549B-NAMEN.               " VLDAHRK006111
  FIELD-SYMBOLS <STRUC_CONTENT>.       " VLDAHRK006111
*---------------------------------------------------------------------*
  FEATURE = MERKMAL.
  SELECT SINGLE STRUC FROM  T549D INTO STRUC
         WHERE  NAMEN       = MERKMAL.
  IF SY-SUBRC NE 0.
*-- Merkmal existiert nicht; d.h. es ist nicht generiert
    STATUS = 4.
  ELSE.
    ASSIGN (STRUC) TO <STRUC_CONTENT>.
    IF SY-SUBRC NE 0 AND ( KIND_OF_ERROR = SPACE OR
                           KIND_OF_ERROR = 1 ).
      STATUS = 8.
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 2.
      MESSAGE I568(P0).
*   Merkmalstruktur nicht bekannt, bitte Langdokumentation lesen.
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 3.
      MESSAGE S568(P0).
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 4.
      MESSAGE E568(P0).
    ELSE.
      clear back.                                          "VLDN185055
      CALL FUNCTION 'HR_FEATURE_BACKFIELD'
           EXPORTING
                FEATURE                     = FEATURE
                STRUC_CONTENT               = <STRUC_CONTENT>
                KIND_OF_ERROR               = KIND_OF_ERROR
           IMPORTING
                BACK                        = BACK
           CHANGING
                STATUS                      = STATUS
           EXCEPTIONS
*                DUMMY                       = 1          "VLDAHRK039762
*                ERROR_OPERATION             = 2          "VLDAHRK039762
*                NO_BACKVALUE                = 3          "VLDAHRK039762
*                FEATURE_NOT_GENERATED       = 4          "VLDAHRK039762
*                INVALID_SIGN_IN_FUNID       = 5          "VLDAHRK039762
*                FIELD_IN_REPORT_TAB_IN_PE03 = 6          "VLDAHRK039762
*                OTHERS                = 0.    "VLDAL0K095544 (Checkman)
                 OTHERS                = 1.    "VLDAL0K095544 (Checkman)
      IF SY-SUBRC <> 0.
*     wg. SLIN
      ENDIF.
    ENDIF.
  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM RE549D_TAB                                               *
*---------------------------------------------------------------------*
*       Aufruf der Tabelle 549D mit Tabellenrückgabe.                 *
*---------------------------------------------------------------------*
*       IN : MERKMAL  - Name des Merkmals                             *
*            KIND_OF_ERROR - Art der Fehlerausgabe: s.o.              *
*       OUT: Tabelle BACK - Rückgabe des Tabelleninhalts              *
*       OUT: STATUS   - s.o.                                          *
*---------------------------------------------------------------------*
FORM RE549D_TAB TABLES BACK
                USING MERKMAL KIND_OF_ERROR STATUS. "#EC CALLED
*---------------------------------------------------------------------*
  DATA          STRUC(5).              " VLDAHRK006111
  DATA          FEATURE LIKE T549B-NAMEN.               " VLDAHRK006111
  FIELD-SYMBOLS <STRUC_CONTENT>.       " VLDAHRK006111
*---------------------------------------------------------------------*
  FEATURE = MERKMAL.
  SELECT SINGLE STRUC FROM  T549D INTO STRUC
         WHERE  NAMEN       = MERKMAL.
  IF SY-SUBRC NE 0.
*-- Merkmal existiert nicht; d.h. es ist nicht generiert
    STATUS = 4.
  ELSE.
    ASSIGN (STRUC) TO <STRUC_CONTENT>.
    IF SY-SUBRC NE 0 AND (  KIND_OF_ERROR = SPACE OR
                            KIND_OF_ERROR = 1 ).
      STATUS = 8.                      " siehe message e568(p0)
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 2.
      MESSAGE I568(P0).
*   Merkmalstruktur nicht bekannt, bitte Langdokumentation lesen.
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 3.
      MESSAGE S568(P0).
    ELSEIF SY-SUBRC NE 0 AND KIND_OF_ERROR = 4.
      MESSAGE E568(P0).
    ELSE.
      clear back.                                         "VLDN185055
      refresh back.                                       "VLDN185055
      CALL FUNCTION 'HR_FEATURE_BACKTABLE'
           EXPORTING
                FEATURE                     = FEATURE
                STRUC_CONTENT               = <STRUC_CONTENT>
                KIND_OF_ERROR               = KIND_OF_ERROR
           TABLES
                BACK                        = BACK
           CHANGING
                STATUS                      = STATUS
           EXCEPTIONS
*                DUMMY                       = 1          "VLDAHRK039762
*                ERROR_OPERATION             = 2          "VLDAHRK039762
*                NO_BACKVALUE                = 3          "VLDAHRK039762
*                FEATURE_NOT_GENERATED       = 4          "VLDAHRK039762
*                INVALID_SIGN_IN_FUNID       = 5          "VLDAHRK039762
*                TAB_IN_REPORT_FIELD_IN_PE03 = 6          "VLDAHRK039762
*                OTHERS                = 0.    "VLDAL0K095544 (Checkman)
                 OTHERS                = 1.    "VLDAL0K095544 (Checkman)
      IF SY-SUBRC <> 0.
*     wg. SLIN
      ENDIF.
    ENDIF.
  ENDIF.
ENDFORM.