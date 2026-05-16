************************************************************************
*                                                                      *
* Include RFFORI0M der Zahlungsträgerprogramme für Makrodefinitionen   *
*                                                                      *
* AUSWAHL   Aufbau einer Zeile im Selektionsbild zur Wahl der Ausgabe  *
* BLOCK     Beginn eines Blocks auf dem Selektionsbild                 *
*                                                                      *
************************************************************************



*----------------------------------------------------------------------*
* Tabelle zum Merken der Felder der Auswahl / Feldsymbol zum Füllen    *
*----------------------------------------------------------------------*
DATA:
  BEGIN OF TAB_SELFIELDS OCCURS 12,
    FIELD(8) TYPE C,
    TEXT(3)  TYPE N,
  END OF TAB_SELFIELDS.

FIELD-SYMBOLS <SELFIELD>.

*----------------------------------------------------------------------*
* Felder für F4-Hilfe und Eingabeprüfung fürs Layout der               *
* ALV-Zahlungsbegleitliste                                             *
*----------------------------------------------------------------------*
DATA:
  gs_variant        TYPE disvariant,
  gc_answer(1)      TYPE c.

*----------------------------------------------------------------------*
* Makro, das eine Zeile zur Auswahl der Ausgabe (Zahlungsträger, DTA,  *
* Avis, Begleitliste) mit Drucker und Sofortdruck aufs Selektionsbild  *
* bringt und die Felder für ein Füllen in Routine INIT merkt.          *
*----------------------------------------------------------------------*
DEFINE AUSWAHL.

  SELECTION-SCREEN:
    BEGIN OF LINE.
  PARAMETERS:
    PAR_&1 LIKE RFPDO-FORD&1.
  SELECTION-SCREEN:
    COMMENT 03(28) TEXT&1 FOR FIELD PAR_&1,
    COMMENT POS_LOW(10) TEXTPRI&2 FOR FIELD PAR_PRI&2.
  PARAMETERS:
    PAR_PRI&2 LIKE RFPDO-FORDPRI&2 VISIBLE LENGTH 11.
  SELECTION-SCREEN:
    POSITION POS_HIGH.
  PARAMETERS:
    PAR_SOF&2 LIKE RFPDO1-FORDSOF&2.
  SELECTION-SCREEN:
    COMMENT 60(18) TEXTSOF&2 FOR FIELD PAR_SOF&2,
    END OF LINE.

  TAB_SELFIELDS-FIELD = 'TEXT&1'.

  CASE TAB_SELFIELDS-FIELD+4.
    WHEN 'ZDRU'. TAB_SELFIELDS-TEXT  = 101.      "Zahlungsträger drucken
    WHEN 'WDRU'. TAB_SELFIELDS-TEXT  = 103.      "Wechsel drucken
    WHEN 'XDTA'. TAB_SELFIELDS-TEXT  = 104.      "Datenträgeraustausch
    WHEN 'AVIS'. TAB_SELFIELDS-TEXT  = 105.      "Avis ausgeben
    WHEN 'BEGL'. TAB_SELFIELDS-TEXT  = 106.      "Begleitliste drucken
  ENDCASE.
  APPEND TAB_SELFIELDS.
  TAB_SELFIELDS-FIELD = 'TEXTPRI&2'.
  TAB_SELFIELDS-TEXT  = 107.                     "auf Drucker
  APPEND TAB_SELFIELDS.
  TAB_SELFIELDS-FIELD = 'TEXTSOF&2'.
  TAB_SELFIELDS-TEXT  = 108.                     "Sofortdruck
  APPEND TAB_SELFIELDS.

END-OF-DEFINITION.

*----------------------------------------------------------------------*
* Makro, das eine Auswahlzeile für eine ALV Zahlungsbegleitliste mit
* Layoutvorgabe und Bildschirmausgabe-Checkbox erzeugt
*----------------------------------------------------------------------*
DEFINE AUSWAHL_ALV_LIST.

  SELECTION-SCREEN:
    BEGIN OF LINE.
  PARAMETERS:
    PAR_ALVB TYPE ACCLIST_ALV.
  SELECTION-SCREEN:
    COMMENT 03(28) TEXTALVB FOR FIELD PAR_ALVB,
    COMMENT POS_LOW(10) TEXTLAYB FOR FIELD PAR_LAYB.
  PARAMETERS:
    PAR_LAYB TYPE SLIS_VARI VISIBLE LENGTH 11.
  SELECTION-SCREEN:
    POSITION POS_HIGH.
  PARAMETERS:
    PAR_DISB TYPE XSCREEN_FPM.
  SELECTION-SCREEN:
    COMMENT 60(18) TEXTDISB FOR FIELD PAR_DISB,
    END OF LINE.

  TAB_SELFIELDS-FIELD = 'TEXTALVB'.
  TAB_SELFIELDS-TEXT  = 110.                     "Begleitliste als ALV
  APPEND TAB_SELFIELDS.
  TAB_SELFIELDS-FIELD = 'TEXTLAYB'.
  TAB_SELFIELDS-TEXT  = 111.                     "Layout
  APPEND TAB_SELFIELDS.
  TAB_SELFIELDS-FIELD = 'TEXTDISB'.
  TAB_SELFIELDS-TEXT  = 112.                     "Bildschirmausgabe
  APPEND TAB_SELFIELDS.

END-OF-DEFINITION.

*----------------------------------------------------------------------*
* Makro für Wertehilfe und Eingabeprüfung für die Layoutvorgabe für die
* ALV Zahlungsbegleitliste
*----------------------------------------------------------------------*
DEFINE AUSWAHL_ALV_LIST_F4_AND_CHECK.
* F4-Help for Layout
  AT SELECTION-SCREEN ON VALUE-REQUEST FOR par_layb.
    CLEAR gs_variant.
    gs_variant-report = gc_list_report.          "'SAPFPAYM' (RFFORI00)
    CALL FUNCTION 'REUSE_ALV_VARIANT_F4'
         EXPORTING
              is_variant = gs_variant
              i_save     = 'A'
         IMPORTING
              e_exit     = gc_answer
              es_variant = gs_variant
         EXCEPTIONS
              not_found  = 2.
    IF sy-subrc NE 0.
      MESSAGE ID sy-msgid TYPE 'S' NUMBER sy-msgno
              WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    ELSE.
      IF gc_answer EQ space.
        par_layb = gs_variant-variant.
      ENDIF.
    ENDIF.


* check layout variant for accompanying list
  AT SELECTION-SCREEN ON par_layb.
    CLEAR gs_variant.
    gs_variant-report = gc_list_report.           "'SAPFPAYM' (RFFORI00)
    IF NOT par_layb IS INITIAL.
      gs_variant-variant = par_layb.
      CALL FUNCTION 'REUSE_ALV_VARIANT_EXISTENCE'
           EXPORTING
                i_save     = 'A'
           CHANGING
                cs_variant = gs_variant.
    ENDIF.
    HLP_LAYB = PAR_LAYB.

  AT SELECTION-SCREEN ON par_alvb.
    HLP_ALVB = PAR_ALVB.

  AT SELECTION-SCREEN ON par_disb.
    HLP_DISB = PAR_DISB.

END-OF-DEFINITION.

*----------------------------------------------------------------------*
* Macro zur Definition eines Paramters zur Druckberechtigungsvergabe   *
*----------------------------------------------------------------------*
DEFINE SPOOL_AUTHORITY.

* selection-screen: skip 1,
*                   begin of line,
*                   comment 01(31) textauth for field par_auth.
* parameters par_auth like itcpo-tdautority.
* selection-screen end of line.

* tab_selfields-field = 'TEXTAUTH'.
* tab_selfields-text = 109.
* append tab_selfields.

 PARAMETERS PAR_AUTH LIKE ITCPO-TDAUTORITY NO-DISPLAY.

END-OF-DEFINITION.


*----------------------------------------------------------------------*
* Makro, das einen Frame mit angegebener Nummer startet und den Text   *
* zum Füllen in Routine INIT merkt.                                    *
*----------------------------------------------------------------------*
DEFINE BLOCK.

  SELECTION-SCREEN BEGIN OF BLOCK &1 WITH FRAME TITLE BLOCK00&1.

  TAB_SELFIELDS-FIELD = 'BLOCK00&1'.
  TAB_SELFIELDS-TEXT  = 90&1.                    "Blocktext
  APPEND TAB_SELFIELDS.

END-OF-DEFINITION.