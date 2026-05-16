************************************************************************
* Include FPAYM_SEL                                                    *
* Selection Screen                                                     *
************************************************************************

*- At selection screen output (PBO) -----------------------------------*
AT SELECTION-SCREEN OUTPUT.

* Action on change of format
  IF PAR_FORM NE GS_TFPM042F-FORMI.

*   Get format details
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
         EXPORTING
              I_FORMI     = PAR_FORM
         IMPORTING
              E_TFPM042F  = GS_TFPM042F
              E_TFPM042FT = GS_TFPM042FT
         EXCEPTIONS
              NOT_FOUND   = 1.
    IF SY-SUBRC EQ 0.
      CALL FUNCTION 'FI_PAYM_FORMAT_READ_PARAMETERS'
           EXPORTING
                I_FORMI      = PAR_FORM
           IMPORTING
                E_TFPM042FF  = GS_TFPM042FF
                E_TFPM042FFC = GS_TFPM042FFC
           TABLES
                T_TFPM042FM  = GT_TFPM042FM
                T_TFPM042FMC = GT_TFPM042FMC
           EXCEPTIONS
                NOT_FOUND    = 1.
    ELSE.
      CLEAR: GS_TFPM042F, GS_TFPM042FT,
             GS_TFPM042FF, GS_TFPM042FFC.
    ENDIF.

*   Dummy coding for references to generic calls for event 10 and 11
*   to check payment medium format parameters
    IF 1 EQ 2.
      SET EXTENDED CHECK OFF.
      CALL FUNCTION 'FI_PAYMEDIUM_SAMPLE_10'.
      CALL FUNCTION 'FI_PAYMEDIUM_SAMPLE_11'.
      SET EXTENDED CHECK ON.
    ENDIF.

*   Adjust parameters to the attributes of the payment format
    PERFORM ADJUST_PARAMETERS_TO_FORMAT.

  ENDIF.

* Fill icons for print parameters (white or green)
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = PAR_PRIE
            I_ICON_TEXT  = TEXT-005
       IMPORTING
            E_ARROW_ICON = EBUTTON.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = PAR_PRIL
            I_ICON_TEXT  = TEXT-005
       IMPORTING
            E_ARROW_ICON = LBUTTON.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = PAR_PRI1
            I_ICON_TEXT  = TEXT-005
       IMPORTING
            E_ARROW_ICON = P1BUTTON.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = PAR_PRI3
            I_ICON_TEXT  = TEXT-005
       IMPORTING
            E_ARROW_ICON = P3BUTTON.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = PAR_PRI5
            I_ICON_TEXT  = TEXT-005
       IMPORTING
            E_ARROW_ICON = P5BUTTON.

  F1BUTTON = TEXT-105.
  F3BUTTON = TEXT-105.

* Check, whether there are format parameters, customer format
* parameters and all obligatory fields of them and set icon for
* format parameters (white or green)
  PERFORM CHECK_FORMAT_PARAMETERS.

* Set check boxes and push buttons activ/inactive
  IF NOT GS_TFPM042FF-FORMF IS INITIAL OR
     NOT GS_TFPM042FFC-FORMF IS INITIAL.
    GC_XFORMF = 'X'.
  ELSE.
    CLEAR GC_XFORMF.
  ENDIF.
  IF NOT GS_TFPM042F-XDME1 IS INITIAL
     AND ( GS_TFPM042F-DTTYP EQ '01' OR GS_TFPM042F-DTTYP EQ '04' ).
    GC_XFILE = 'X'.
  ELSE.
    CLEAR GC_XFILE.
  ENDIF.

  DATA: L_BADI_BATCH_PAYM_MEDIUM TYPE REF TO FPAYM_BATCH_PAYMENTS_MEDIUM.
  TRY.
      GET BADI L_BADI_BATCH_PAYM_MEDIUM.
      CALL BADI L_BADI_BATCH_PAYM_MEDIUM->IS_FILE_CREATION_ALLOWED
        EXPORTING
          I_TFPM042F      = GS_TFPM042F
        IMPORTING
          E_XFILE_ALLOWED = GC_XFILE.
    CATCH CX_BADI_NOT_IMPLEMENTED CX_BADI_MULTIPLY_IMPLEMENTED.
  ENDTRY.


  LOOP AT SCREEN.
    PERFORM FILL_SCREEN
            USING: 'F'   GC_XFORMF,
                   'I'   GS_TFPM042F-FORMD,
                   'PY1' GS_TFPM042F-XPRI1,
                   'PY2' GS_TFPM042F-XPRI2,
                   'PY3' GS_TFPM042F-XDME1,
                   'PY4' GC_XFILE,
                   'PY5' GS_TFPM042F-XLST1.

*-- PAR_FPY1 and TEXT_PY1 ---
    IF GS_TFPM042F-FORMT EQ 'P'  AND
      ( SCREEN-NAME = 'TEXT_FP1' OR  " 01454480
        SCREEN-NAME = 'PAR_FPY1' OR
        SCREEN-NAME = 'F1BUTTON' ).
      SCREEN-ACTIVE = 0.
    ENDIF.

*-- PAR_PDF1 and TXT_PDF1 ---
    IF GS_TFPM042F-FORMT IS INITIAL AND
      ( SCREEN-NAME = 'PAR_PDF1' OR  " 01454480
        SCREEN-NAME = 'TXT_PDF1' ).
      SCREEN-ACTIVE = 0.
    ENDIF.

*-- PAR_PDF3 plus name ---
    IF PAR_FTYP IS INITIAL AND
*     PDF accompanying sheet
      ( SCREEN-NAME = '%_PAR_PDF3_%_APP_%-TEXT' OR " 01454480
        SCREEN-NAME = 'PAR_PDF3' ).
      SCREEN-ACTIVE = 0.
    ENDIF.

*-- PAR_FPY3 plus name ---
    IF PAR_FTYP EQ 'P' AND
*     SAPSCRIPT accompanying sheet
       ( SCREEN-NAME = '%_PAR_FPY3_%_APP_%-TEXT' OR  " 01454480
         SCREEN-NAME = 'PAR_FPY3' OR
         SCREEN-NAME = 'F3BUTTON' ).
      SCREEN-ACTIVE = 0.
    ENDIF.

    MODIFY SCREEN.
  ENDLOOP.


*- At selection screen (PAI) ------------------------------------------*

* F4 for SAPScript formulars
AT SELECTION-SCREEN ON VALUE-REQUEST FOR PAR_FPY3.

  DATA L_FORM_NAME TYPE TDFORM.                             "lokal !!

  CALL FUNCTION 'DISPLAY_FORM_TREE_F4'
       EXPORTING
            P_TREE_NAME = 'FI-2'
       IMPORTING
            P_FORM_NAME = L_FORM_NAME
       EXCEPTIONS
            OTHERS      = 4.

  IF SY-SUBRC EQ 0 AND L_FORM_NAME NE SPACE.
    PAR_FPY3 = L_FORM_NAME.
  ENDIF.

* value request for layout variant for accompanying list
AT SELECTION-SCREEN ON VALUE-REQUEST FOR PAR_VARI.
  CLEAR GS_VARIANT.
  GS_VARIANT-REPORT = SY-REPID.
  CALL FUNCTION 'REUSE_ALV_VARIANT_F4'
       EXPORTING
            IS_VARIANT = GS_VARIANT
            I_SAVE     = 'A'
       IMPORTING
            E_EXIT     = GC_ANSWER
            ES_VARIANT = GS_VARIANT
       EXCEPTIONS
            NOT_FOUND  = 2.
  IF SY-SUBRC NE 0.
    MESSAGE ID SY-MSGID TYPE 'S' NUMBER SY-MSGNO
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ELSE.
    IF GC_ANSWER EQ SPACE.
      PAR_VARI = GS_VARIANT-VARIANT.
    ENDIF.
  ENDIF.


* check layout variant for accompanying list
AT SELECTION-SCREEN ON PAR_VARI.
  CLEAR GS_VARIANT.
  GS_VARIANT-REPORT  = SY-REPID.
  IF NOT PAR_VARI IS INITIAL.
    GS_VARIANT-VARIANT = PAR_VARI.
    CALL FUNCTION 'REUSE_ALV_VARIANT_EXISTENCE'
         EXPORTING
              I_SAVE     = 'A'
         CHANGING
              CS_VARIANT = GS_VARIANT.
  ENDIF.


* Check payment medium format parameters
AT SELECTION-SCREEN ON PAR_FORM.

* New payment medium format
  IF PAR_FORM NE GS_TFPM042F-FORMI.

*   Check that the new payment medium format is valid
    IF NOT PAR_FORM IS INITIAL.
      CALL FUNCTION 'FI_PAYM_FORMAT_CHECK'
           EXPORTING
                I_FORMI = PAR_FORM.
    ENDIF.

*   Warning on change of payment medium format
    IF NOT GS_TFPM042F-FORMI IS INITIAL.
      CALL FUNCTION 'POPUP_TO_CONFIRM'
           EXPORTING
                TITLEBAR        = TEXT-100
                DIAGNOSE_OBJECT = 'FPM_FORMAT_CHANGE'
                TEXT_QUESTION   = TEXT-101
           IMPORTING
                ANSWER          = GC_ANSWER.
      IF GC_ANSWER NE '1'.
        PAR_FORM = GS_TFPM042F-FORMI.
      ENDIF.
    ENDIF.
  ENDIF.

* Action on change of payment medium format
  IF PAR_FORM NE GS_TFPM042F-FORMI.

    TRY.                                                 "begin n2669849
      CALL FUNCTION 'FI_PAYM_FORMAT_OBSOLETE_CHECK'
        EXPORTING
          I_FORMI            = PAR_FORM
        EXCEPTIONS
          FORMAT_IS_OBSOLETE = 0.
      CATCH CX_ROOT.
    ENDTRY.                                                "end n2669849

*   Initialize format parameters
    CLEAR: PAR_FORP, PAR_FOPC, GC_XFORP, GS_TFPM042FD, GS_TFPM042FDC.

*   Get default values from database
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_DEFAULTS'
         EXPORTING
              I_FORMI      = PAR_FORM
         IMPORTING
              E_TFPM042FD  = GS_TFPM042FD
              E_TFPM042FDC = GS_TFPM042FDC.
    PAR_FORP     = GS_TFPM042FD-DEF_PARAMS1.
    PAR_FORP+250 = GS_TFPM042FD-DEF_PARAMS2.
    PAR_FOPC     = GS_TFPM042FDC-DEF_PARAMS1.
    PAR_FOPC+250 = GS_TFPM042FDC-DEF_PARAMS2.

*   Set defaults for check boxes
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
         EXPORTING
              I_FORMI    = PAR_FORM
         IMPORTING
              E_TFPM042F = GS_TFPM042F_2.
    IF GS_TFPM042F_2-XDME1 IS INITIAL.
      PAR_XPY1 = GS_TFPM042F_2-XPRI1.
    ELSE.
      CLEAR: PAR_XPY1.
    ENDIF.
    IF NOT GS_TFPM042F_2-XDME1 IS INITIAL.
      PAR_XPY3 = GS_TFPM042F_2-XDME1.
    ENDIF.
    PAR_XPY5 = GS_TFPM042F_2-XLST1.

*   Deactivate ok-code
    IF NOT SSCRFIELDS-UCOMM IS INITIAL.
      MESSAGE S603.
      CLEAR SSCRFIELDS-UCOMM.
    ENDIF.

* No change of payment medium format
  ELSE.

*   Check whether obligatory format parameters have to be filled
    IF GC_XFORP IS INITIAL AND
       ( NOT GT_TFPM042FM[] IS INITIAL OR
         NOT GT_TFPM042FMC[] IS INITIAL ).
      MESSAGE S055(00).
      IF SY-BATCH IS INITIAL.
        PERFORM POPUP_FORMAT_PARAMETERS.
        IF SSCRFIELDS-UCOMM EQ 'FORM'.
          CLEAR SSCRFIELDS-UCOMM.
        ENDIF.
      ELSE.
        STOP.
      ENDIF.
    ENDIF.

  ENDIF.


* Check the existence of entered layout sets
AT SELECTION-SCREEN ON PAR_FPY1.
  PERFORM CHECK_FORM USING PAR_FPY1.

AT SELECTION-SCREEN ON PAR_PDF1.
  CALL FUNCTION 'PDF_FORM_CHECK'
    EXPORTING
      I_FORMNAME = PAR_PDF1.

AT SELECTION-SCREEN ON PAR_FPY3.
  PERFORM CHECK_FORM USING PAR_FPY3.

AT SELECTION-SCREEN ON PAR_PDF3.
  CALL FUNCTION 'PDF_FORM_CHECK'
    EXPORTING
      I_FORMNAME = PAR_PDF3.

*- User commands ------------------------------------------------------*
AT SELECTION-SCREEN.

  CASE SSCRFIELDS-UCOMM.

*   Format documentation
    WHEN 'INFO'.
      CALL FUNCTION 'FI_PAYM_FORMAT_DOCUMENTATION'
           EXPORTING
                I_FORMI = PAR_FORM.

*   Format parameters
    WHEN 'FORM'.
      PERFORM POPUP_FORMAT_PARAMETERS.

*   Print parameters for the error list
    WHEN 'PRIE'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                I_TITLE_TEXT         = TEXT-013
           CHANGING
                C_PRI_PARAMS         = PAR_PRIE
                C_ARC_PARAMS         = PAR_ARCE
           EXCEPTIONS
                PARAMETERS_NOT_VALID = 1
                OTHERS               = 2.

*  Print parameters for the accompanying list
    WHEN 'PRIL'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                I_TITLE_TEXT         = TEXT-012
           CHANGING
                C_PRI_PARAMS         = PAR_PRIL
                C_ARC_PARAMS         = PAR_ARCL
           EXCEPTIONS
                PARAMETERS_NOT_VALID = 1
                OTHERS               = 2.

*   Print parameters for the payment medium 1
    WHEN 'PRI1'.
      CALL FUNCTION 'MAINTAIN_TEXT_PRINT_PARAMETERS'
           EXPORTING
                I_TITLE_TEXT         = TEXT_PY1
           CHANGING
                C_ITCPO              = PAR_PRI1
           EXCEPTIONS
                PARAMETERS_NOT_VALID = 1
                OTHERS               = 2.

*   Print parameters for the payment medium 3
    WHEN 'PRI3'.
      CALL FUNCTION 'MAINTAIN_TEXT_PRINT_PARAMETERS'
           EXPORTING
                I_TITLE_TEXT         = GC_TEXT_PY3
           CHANGING
                C_ITCPO              = PAR_PRI3
           EXCEPTIONS
                PARAMETERS_NOT_VALID = 1
                OTHERS               = 2.

*   Additional payment medium list
    WHEN 'PRI5'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                I_TITLE_TEXT         = TEXT_PY5
           CHANGING
                C_PRI_PARAMS         = PAR_PRI5
                C_ARC_PARAMS         = PAR_ARC5
           EXCEPTIONS
                PARAMETERS_NOT_VALID = 1
                OTHERS               = 2.

*   Display SAPscript payment medium form 1
    WHEN 'SCR1'.
      PERFORM DISPLAY_FORM USING PAR_FPY1.

*   Display SAPscript payment medium form 3
    WHEN 'SCR3'.
      PERFORM DISPLAY_FORM USING PAR_FPY3.

    WHEN 'FORM_TYPE_CHANGED'.
      IF NOT PAR_PDF3 IS INITIAL OR NOT PAR_FPY3 IS INITIAL.
        MESSAGE S168 DISPLAY LIKE 'W'.
      ENDIF.

  ENDCASE.

* two options for accompanying list: printer or screen output
  IF PAR_SCRN IS INITIAL AND NOT PAR_XLST IS INITIAL.
    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
         EXPORTING
              I_TITLE_TEXT = TEXT-012
              I_PRI_PARAMS = PAR_PRIL
              I_ARC_PARAMS = PAR_ARCL
         IMPORTING
              E_PRI_PARAMS = GS_PRIL
              E_ARC_PARAMS = GS_ARCL.
* delete by note 1763901
*    IF gs_pril-pdest IS INITIAL.
*      MESSAGE s615.
*      CLEAR sscrfields-ucomm.
*    ENDIF.

* insert by note 1763901
     IF GS_PRIL-PDEST IS INITIAL.
       IF SY-BATCH IS INITIAL. " note 1763901
         MESSAGE S615.
         CLEAR SSCRFIELDS-UCOMM.
       ELSE.
         MESSAGE S065 WITH 'Report' SY-CPROG SY-SLSET ':'.
         MESSAGE S615.
*        no clear on sscrfields-ucomm, we continue, see note 1763901
       ENDIF.
    ENDIF.
* end insert
  ENDIF.

AT SELECTION-SCREEN ON HELP-REQUEST FOR PAR_PDF1.
  CALL FUNCTION 'FI_DOCUMENTATION_SHOW'
    EXPORTING
      IC_FNAME          = 'FORDZFOR'
      IC_DOKCLASS       = 'DE'.

AT SELECTION-SCREEN ON HELP-REQUEST FOR PAR_PDF3.
  CALL FUNCTION 'FI_DOCUMENTATION_SHOW'
    EXPORTING
      IC_FNAME          = 'FORDZFOR'
      IC_DOKCLASS       = 'DE'.
AT SELECTION-SCREEN ON PAR_FILE.  " note 1511617
IF PAR_FILE IS NOT INITIAL AND PAR_XFIL IS NOT INITIAL.
    DATA LD_FILENAME(255) TYPE C.
    LD_FILENAME = PAR_FILE.
    CALL FUNCTION 'FILE_VALIDATE_NAME'
    EXPORTING
      LOGICAL_FILENAME  = 'FI_DME_CREATE_FILE'
      PARAMETER_1       = SY-CPROG
    CHANGING
      PHYSICAL_FILENAME = LD_FILENAME
    EXCEPTIONS
      VALIDATION_FAILED          = 1
      LOGICAL_FILENAME_NOT_FOUND = 2
      OTHERS                     = 3.
* in case no exception is thrown, we keep the original filename
    IF SY-SUBRC <> 0.
      MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
      WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    ENDIF.
  ENDIF.