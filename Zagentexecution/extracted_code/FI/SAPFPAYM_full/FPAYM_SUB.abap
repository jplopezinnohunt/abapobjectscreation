************************************************************************
* Include FPAYM_SUB
* Subroutines
************************************************************************

*----------------------------------------------------------------------*
* Form ADJUST_PARAMETERS_TO_FORMAT
* Adjust selection parameters to payment medium format porperties
*----------------------------------------------------------------------*
FORM ADJUST_PARAMETERS_TO_FORMAT.

* Initialize print parameters
  IF GS_TFPM042F-XPRI1 IS INITIAL.
    CLEAR: PAR_XPY1,
           PAR_PRI1,
           PAR_FPY1,
           PAR_PDF1.
  ENDIF.
  IF GS_TFPM042F-XDME1 IS INITIAL.
    CLEAR: PAR_XPY3,
           PAR_PRI3,
           PAR_FTYP,
           PAR_FPY3,
           PAR_PDF3,
           PAR_FILE,
           PAR_XFIL.
  ENDIF.
  IF GS_TFPM042F-XLST1 IS INITIAL.
    CLEAR: PAR_XPY5,
           PAR_PRI5,
           PAR_ARC5.
  ENDIF.
* Assign text for check boxes
  PERFORM FILL_PARAMETER_TEXT
          USING: GS_TFPM042FT-PRI1X TEXT-010 TEXT_PY1,
                 GS_TFPM042FT-DME1X TEXT-015 TEXT_PY3,
                 GS_TFPM042FT-LST1X TEXT-010 TEXT_PY5.

  CONCATENATE: TEXT-009 TEXT_PY1 INTO TEXT_FP1    SEPARATED BY SPACE,
               TEXT-014 TEXT_PY3 INTO GC_TEXT_PY3 SEPARATED BY SPACE.

  TXT_PDF1 = TEXT_FP1.

ENDFORM.                               "ADJUST_PARAMETERS_TO_FORMAT


*----------------------------------------------------------------------*
* Form FILL_PARAMETER_TEXT
* Fills Text with imported text or imported alternative text
*----------------------------------------------------------------------*
* --> I_TEXT        Text from payment format attributes
* --> I_TEXT_SUB    Alternative text from payment format attributes
* <-- E_PAR_TEXT    Text to be output
*----------------------------------------------------------------------*
FORM FILL_PARAMETER_TEXT USING I_TEXT     TYPE C
                               I_TEXT_SUB TYPE C
                               E_PAR_TEXT TYPE C.

  IF NOT I_TEXT IS INITIAL.
    E_PAR_TEXT = I_TEXT.
  ELSE.
    E_PAR_TEXT = I_TEXT_SUB.
  ENDIF.

ENDFORM.                               "FILL_PARAMETER_TEXT


*----------------------------------------------------------------------*
* Form CHECK_FORMAT_PARAMETERS
* Check, whether there are format parameters, customer format
* parameters and all obligatory fields of them and set icon for
* format parameters (white or green)
*----------------------------------------------------------------------*
FORM CHECK_FORMAT_PARAMETERS.

  DATA: LT_SAPOBLI   LIKE FPM_OBLI OCCURS 0 WITH HEADER LINE,
        LT_CUSOBLI   LIKE FPM_OBLI OCCURS 0 WITH HEADER LINE,
        LC_XINITIAL  LIKE BOOLE-BOOLE VALUE 'X',
        LC_XENTRIES  LIKE BOOLE-BOOLE.

* There are format parameters
  IF NOT GS_TFPM042FF-FORMF IS INITIAL.
*   Format parameters are initial
    IF PAR_FORP IS INITIAL.
      CLEAR GC_XFORP.
*   There are format parameter values
    ELSE.
*     Get obligatory fields of format parameters
      LOOP AT GT_TFPM042FM.
        MOVE-CORRESPONDING GT_TFPM042FM TO LT_SAPOBLI.
        APPEND LT_SAPOBLI.
      ENDLOOP.
*     Check format parameters and obligatory fields
      CALL FUNCTION 'CHECK_STRUCTURE_FIELDS'
           EXPORTING
                I_TABNAME       = GS_TFPM042FF-FORMF
           IMPORTING
                E_INITIAL       = LC_XINITIAL
                E_FIELDS_FILLED = GC_XFORP
           TABLES
                T_OBLI          = LT_SAPOBLI
           CHANGING
                C_WORKAREA      = PAR_FORP.
    ENDIF.
  ENDIF.

* There are no format parameters but customer format parameters
  IF GC_XFORP IS INITIAL AND
     NOT GS_TFPM042FFC-FORMF IS INITIAL AND
     NOT PAR_FOPC IS INITIAL.
*   Get obligatory customer fields of format parameters
    LOOP AT GT_TFPM042FMC.
      MOVE-CORRESPONDING GT_TFPM042FMC TO LT_CUSOBLI.
      APPEND LT_CUSOBLI.
    ENDLOOP.
*   Check customer format parameters and obligatory fields
    CALL FUNCTION 'CHECK_STRUCTURE_FIELDS'
         EXPORTING
              I_TABNAME       = GS_TFPM042FFC-FORMF
         IMPORTING
              E_INITIAL       = LC_XINITIAL
              E_FIELDS_FILLED = GC_XFORP
         TABLES
              T_OBLI          = LT_CUSOBLI
         CHANGING
              C_WORKAREA      = PAR_FOPC.
  ENDIF.


* Fill icons for format parameters (white or green)
  IF LC_XINITIAL IS INITIAL.
    LC_XENTRIES = 'X'.
  ENDIF.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            I_PARAMETER  = LC_XENTRIES
            I_ICON_TEXT  = TEXT-006
       IMPORTING
            E_ARROW_ICON = FBUTTON.

ENDFORM.                               "CHECK_FORMAT_PARAMETERS


*----------------------------------------------------------------------*
* Form POPUP_FORMAT_PARAMETERS
* Displays one popup for the maintenance of payment medium format
* parameters and customers payment medium format parameters which
* declared in DDIC structures
*----------------------------------------------------------------------*
FORM POPUP_FORMAT_PARAMETERS.

  DATA: LT_SAPOBLI   LIKE FPM_OBLI OCCURS 0 WITH HEADER LINE,
        LT_CUSOBLI   LIKE FPM_OBLI OCCURS 0 WITH HEADER LINE,
        LC_XINITIAL  LIKE BOOLE-BOOLE,
        LC_XSAPENTRY LIKE BOOLE-BOOLE,
        LC_XCUSENTRY LIKE BOOLE-BOOLE,
        LC_SAPFUNCT  LIKE TFPM042FB-FNAME,
        LC_CUSFUNCT  LIKE TFPM042FBC-FNAME,
        LC_TEXT      LIKE RSMPE-TITTEXT,
        LC_SAPPAR    LIKE FPM_SELPAR-PARAM,
        LC_CUSPAR    LIKE FPM_SELPAR-PARAM.

* Check whether there are obligatory fields in the format parameters
  IF NOT GS_TFPM042FF-FORMF IS INITIAL OR
     NOT GS_TFPM042FFC-FORMF IS INITIAL.

*   Delete the formatparameters if the corresponding structure is
*   initial
    IF GS_TFPM042FF-FORMF IS INITIAL.
      CLEAR PAR_FORP.
    ENDIF.
    IF GS_TFPM042FFC-FORMF IS INITIAL.
      CLEAR PAR_FOPC.
    ENDIF.
*   Get obligatory fields of format parameters
    LOOP AT GT_TFPM042FM.
      MOVE-CORRESPONDING GT_TFPM042FM TO LT_SAPOBLI.
      APPEND LT_SAPOBLI.
    ENDLOOP.
*   Get obligatory customer fields of format parameters
    LOOP AT GT_TFPM042FMC.
      MOVE-CORRESPONDING GT_TFPM042FMC TO LT_CUSOBLI.
      APPEND LT_CUSOBLI.
    ENDLOOP.
*   Get check functions for the format parameters
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_EVENTS'
         EXPORTING
              I_FORMI         = GS_TFPM042F-FORMI
              I_EVENT         = 10
         IMPORTING
              E_EVENTFUNCTION = LC_SAPFUNCT
         EXCEPTIONS
              OTHERS          = 1.
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_EVENTS'
         EXPORTING
              I_FORMI         = GS_TFPM042F-FORMI
              I_EVENT         = 11
         IMPORTING
              E_EVENTFUNCTION = LC_CUSFUNCT
         EXCEPTIONS
              OTHERS          = 1.
*   Call Popup for format parameters
    LC_TEXT = TEXT-020.
    REPLACE '&format' WITH GS_TFPM042F-FORMI INTO LC_TEXT.
    LC_SAPPAR = PAR_FORP.
    LC_CUSPAR = PAR_FOPC.
    CALL FUNCTION 'DIC2DYN'
         EXPORTING
              I_SAPTABNAME   = GS_TFPM042FF-FORMF
              I_CUSTABNAME   = GS_TFPM042FFC-FORMF
              I_SAPCHECKFUNC = LC_SAPFUNCT
              I_CUSCHECKFUNC = LC_CUSFUNCT
              I_TITTEXT      = LC_TEXT
         IMPORTING
              E_XSAPENTRY    = LC_XSAPENTRY
              E_XCUSENTRY    = LC_XCUSENTRY
         TABLES
              T_SAPOBLI      = LT_SAPOBLI
              T_CUSOBLI      = LT_CUSOBLI
         CHANGING
              C_SAPENTRIES   = LC_SAPPAR
              C_CUSENTRIES   = LC_CUSPAR.
    IF NOT LC_XSAPENTRY IS INITIAL OR
       NOT LC_XCUSENTRY IS INITIAL.
      GC_XFORP = 'X'.
      PAR_FORP = LC_SAPPAR.
      PAR_FOPC = LC_CUSPAR.
    ELSE.
      CLEAR: SSCRFIELDS-UCOMM.
    ENDIF.
  ENDIF.

ENDFORM.                               "POPUP_FORMAT_PARAMETERS


*----------------------------------------------------------------------*
* Form CHECK_FORM
* Checks the existence of a form layout set
*----------------------------------------------------------------------*
* --> I_FORM        Layout set to be checked
*----------------------------------------------------------------------*
FORM CHECK_FORM USING I_FORM LIKE FPM_SELPAR-ALTFORM.

  CHECK I_FORM NE SPACE.
  CALL FUNCTION 'FORM_CHECK'
       EXPORTING
            I_PZFOR = I_FORM
       EXCEPTIONS
            OTHERS  = 4.
  CHECK SY-SUBRC NE 0.
  MESSAGE ID SY-MSGID TYPE 'W' NUMBER SY-MSGNO
          WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.

ENDFORM.                                                    "CHECK_FORM


*----------------------------------------------------------------------*
* Form DISPLAY_FORM
* Maintain / Display  form layout set
*----------------------------------------------------------------------*
* --> I_FORM        Name of layout set to be displayed
*----------------------------------------------------------------------*
FORM DISPLAY_FORM USING I_FORM LIKE FPM_SELPAR-ALTFORM.

  CHECK NOT I_FORM IS INITIAL.
  CALL FUNCTION 'EDIT_FORM'
       EXPORTING
            FORM    = I_FORM
            DISPLAY = 'X'.

ENDFORM.                               "DISPLAY_FORM


*----------------------------------------------------------------------*
* Form FILL_SCREEN                                                     *
* Set screen fields inactive                                           *
*----------------------------------------------------------------------*
* --> I_GROUP      Screen group to be modified                        *
* --> I_ACTIVE     Parameter active                                   *
*----------------------------------------------------------------------*
FORM FILL_SCREEN USING I_GROUP TYPE C
                       I_ACTIVE.

  IF SCREEN-GROUP1 EQ I_GROUP AND I_ACTIVE IS INITIAL.
    SCREEN-ACTIVE = '0'.
  ENDIF.

ENDFORM.


*&---------------------------------------------------------------------*
*&      Form  output_start_message
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM OUTPUT_START_MESSAGE.

  IF NOT GS_DFPAYG-ZBUKR IS INITIAL.
    CONCATENATE TEXT-030 GS_DFPAYG-ZBUKR INTO GC_MESSAGE_TEXT1
      SEPARATED BY SPACE.
    CONDENSE GC_MESSAGE_TEXT1.
    IF NOT GS_DFPAYG-HBKID IS INITIAL.
      IF GS_DFPAYG-HKTID IS INITIAL.
        CONCATENATE TEXT-031 GS_DFPAYG-HBKID INTO GC_MESSAGE_TEXT2
          SEPARATED BY SPACE.
      ELSE.
        CONCATENATE TEXT-032 GS_DFPAYG-HBKID GS_DFPAYG-HKTID
          INTO GC_MESSAGE_TEXT2 SEPARATED BY SPACE.
      ENDIF.
      CONDENSE GC_MESSAGE_TEXT2.
    ENDIF.
  ENDIF.

  IF NOT GS_DFPAYG-BANKS IS INITIAL.
    CONCATENATE TEXT-031 GS_DFPAYG-BANKS GS_DFPAYG-BANKL INTO
      GC_MESSAGE_TEXT2 SEPARATED BY SPACE.
    CONDENSE GC_MESSAGE_TEXT2.
  ENDIF.

  IF NOT GS_DFPAYG-RZAWE IS INITIAL.
    CONCATENATE TEXT-034  GS_DFPAYG-RZAWE INTO
      GC_MESSAGE_TEXT3 SEPARATED BY SPACE.
    CONDENSE GC_MESSAGE_TEXT3.
  ELSEIF GS_DFPAYG-CRDEB EQ '1'.
    GC_MESSAGE_TEXT3 = TEXT-035.
  ELSEIF GS_DFPAYG-CRDEB EQ '2'.
    GC_MESSAGE_TEXT3 = TEXT-036.
  ENDIF.

  TRY.                                                   "begin n2669849
    IF NOT SY-BATCH IS INITIAL.
      CALL FUNCTION 'FI_PAYM_FORMAT_OBSOLETE_CHECK'
        EXPORTING
          I_FORMI            = PAR_FORM
        EXCEPTIONS
          FORMAT_IS_OBSOLETE = 0.
    ENDIF.
    CATCH CX_ROOT.
  ENDTRY.                                                  "end n2669849

  MESSAGE S222 WITH PAR_FORM GC_MESSAGE_TEXT1
            GC_MESSAGE_TEXT2 GC_MESSAGE_TEXT3.

ENDFORM.                               " output_start_message


*&---------------------------------------------------------------------*
*&      Form  hr_remittance_acknowledgement
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_FPAYP  text
*----------------------------------------------------------------------*
FORM HR_REMITTANCE_ACKNOWLEDGEMENT USING IS_FPAYH LIKE FPAYH
                                         IS_FPAYP LIKE FPAYP.

  DATA: L_XBLNR     LIKE HRXBLNR,
        L_LIFNR     TYPE LIFNR,
        L_AWSYS     TYPE AWSYS,
        L_DEST      TYPE RFCDEST,
        L_TEXT(100) TYPE C.
*** begin note 1130975
  DATA: L_REMSN_EXIST TYPE XFELD.   "Indicator REMSN exists
  DATA: L_IV_DUEDT_EXIST TYPE XFELD. "Indicator IV_DUEDT exists

  DATA: DREF_XBLNR TYPE REF TO DATA.  "N2307673
  FIELD-SYMBOLS: <XBLNR>.             "N2307673

  DATA: L_REMSN TYPE REMSN,
        L_ZFBDT LIKE REGUP-ZFBDT.
  DATA: L_IMPORT_TAB TYPE STANDARD TABLE OF RSIMP WITH HEADER
      LINE,
               L_EXPORT_TAB       TYPE STANDARD TABLE OF RSEXP,
               L_TABLES_TAB       TYPE STANDARD TABLE OF RSTBL,
               L_EXCEPTIONS_TAB   TYPE STANDARD TABLE OF RSEXC.
  CLEAR: L_REMSN, L_ZFBDT, L_REMSN_EXIST, L_IV_DUEDT_EXIST.
*** end note 1130975
* check that payment is 3rd party remittance
  L_XBLNR = IS_FPAYP-XBLNR.
  CHECK:
    IS_FPAYH-GPA1T EQ '11' AND         "vendor
    IS_FPAYP-DOC2T EQ '01' AND         "FI document
    IS_FPAYP-XVORL EQ SPACE.           "no proposal run
  CHECK:
    L_XBLNR-TXTSL  EQ 'HR',
    L_XBLNR-TXERG  EQ 'GRN' AND L_XBLNR-XHRFO EQ 'X' OR
    L_XBLNR-TXERG  EQ SPACE AND L_XBLNR-XHRFO EQ SPACE.
*    l_xblnr-remsn  NE 0.
*    With extension of remsn from 5 to 10,
*    hrxblnr-remsn will always be zeros for the new posting numbers.
*    The data prior to the extension will not have zeros in the field.
*    So, removed the check.

* get vendor number
  CALL FUNCTION 'FI_REF_PARTNER_INTERPRET'
       EXPORTING
            IM_GPA1T = IS_FPAYH-GPA1T
            IM_GPA1R = IS_FPAYH-GPA1R
            IM_GPA2T = IS_FPAYP-GPA2T
            IM_GPA2R = IS_FPAYP-GPA2R
       IMPORTING
            EX_LIFNR = L_LIFNR.

* get rfc destination
  G_FUNCTION = 'READ_DOC2R_DESTINATION'.
  CALL FUNCTION G_FUNCTION
       EXPORTING
            I_DOC2T        = IS_FPAYP-DOC2T
            I_DOC2R        = IS_FPAYP-DOC2R
       IMPORTING
            E_AWSYS        = L_AWSYS
            E_RFCDEST      = L_DEST
       EXCEPTIONS
            NO_REMOTE_CALL = 1
            OTHERS         = 2.

  CASE SY-SUBRC.
    WHEN 0.    "means distributed.
      G_FUNCTION = 'RP_REMITTANCE_ACKNOWLEDGEMENT'.
*** check if func exists.
     CALL FUNCTION 'FUNCTION_EXISTS'
        DESTINATION L_DEST
        EXPORTING
          FUNCNAME           = G_FUNCTION
        EXCEPTIONS
          FUNCTION_NOT_EXIST = 1
          OTHERS             = 2.
*** func exists, take its interface data.
      IF SY-SUBRC = 0.             " Function exists
        CALL FUNCTION 'FUNCTION_IMPORT_INTERFACE'
          DESTINATION L_DEST
          EXPORTING
            FUNCNAME           = G_FUNCTION
            INACTIVE_VERSION   = ' '
          TABLES
            EXCEPTION_LIST     = L_EXCEPTIONS_TAB
            EXPORT_PARAMETER   = L_EXPORT_TAB
            IMPORT_PARAMETER   = L_IMPORT_TAB
            TABLES_PARAMETER   = L_TABLES_TAB
          EXCEPTIONS
            ERROR_MESSAGE      = 1
            FUNCTION_NOT_FOUND = 2
            INVALID_NAME       = 3
            OTHERS             = 4.

        IF SY-SUBRC <> 0.          "Function not found
          MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
           WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*** Func found so check its import parameters.
        ELSE.
          READ TABLE L_IMPORT_TAB WITH KEY PARAMETER = 'IV_DUEDT'.
            IF SY-SUBRC = 0.
              L_IV_DUEDT_EXIST = 'X'.
            ENDIF.
          READ TABLE L_IMPORT_TAB WITH KEY PARAMETER = 'REMSN'.
          IF SY-SUBRC = 0.
            L_REMSN_EXIST = 'X'.
          ENDIF.

      READ TABLE L_IMPORT_TAB                        "N2307673
        WITH KEY PARAMETER = 'XBLNR'.                "N2307673

      CREATE DATA DREF_XBLNR TYPE (L_IMPORT_TAB-TYP). "N2307673

      IF SY-SUBRC = 0.                                "N2307673
        ASSIGN DREF_XBLNR->* TO <XBLNR>.              "N2307673
      ENDIF.                                          "N2307673
      IF NOT <XBLNR> IS ASSIGNED.                     "N2307673
        ASSIGN IS_FPAYP-XBLNR TO <XBLNR>.             "N2307673
      ENDIF.                                          "N2307673

      <XBLNR> = IS_FPAYP-XBLNR.                       "N2307673

          IF L_IV_DUEDT_EXIST = 'X' AND L_REMSN_EXIST = 'X'.
            IF IS_FPAYP-SGTXT+0(5) EQ '00000'. "means new posting run number
              L_REMSN = IS_FPAYP-SGTXT+5(10).
            ELSE.
              L_REMSN = IS_FPAYP-SGTXT+0(5).
            ENDIF.

*** determine iv_duedt
            SELECT SINGLE ZFBDT INTO L_ZFBDT
                  FROM REGUP
                       WHERE LAUFD = IS_FPAYP-LAUFD AND
                             LAUFI = IS_FPAYP-LAUFI AND
                             XVORL = IS_FPAYP-XVORL AND
                             BUKRS = IS_FPAYP-BUKRS AND
                             LIFNR = L_LIFNR        AND
                             BELNR = IS_FPAYP-DOC2R+4(10) AND
                             XBLNR = IS_FPAYP-XBLNR.

      CALL FUNCTION G_FUNCTION
           DESTINATION
                L_DEST
           EXPORTING
                LAUFD                 = IS_FPAYP-LAUFD
                LAUFI                 = IS_FPAYP-LAUFI
                BUKRS                 = IS_FPAYP-BUKRS
                LIFNR                 = L_LIFNR
*                xblnr                 = is_fpayp-xblnr  "N2307673
                XBLNR                 = <XBLNR>          "N2307673
                ZFBDT                 = L_ZFBDT
                REMSN                 = L_REMSN
           EXCEPTIONS
                COMMUNICATION_FAILURE = 4 MESSAGE L_TEXT
                SYSTEM_FAILURE        = 4 MESSAGE L_TEXT
                OTHERS                = 0.
           ENDIF.   "if both fields exist

      IF L_IV_DUEDT_EXIST IS INITIAL AND L_REMSN_EXIST IS INITIAL.
            CALL FUNCTION G_FUNCTION
              DESTINATION L_DEST
              EXPORTING
                LAUFD                 = IS_FPAYP-LAUFD
                LAUFI                 = IS_FPAYP-LAUFI
                BUKRS                 = IS_FPAYP-BUKRS
                LIFNR                 = L_LIFNR
*                xblnr                 = is_fpayp-xblnr  "N2307673
                XBLNR                 = <XBLNR>          "N2307673
              EXCEPTIONS
                COMMUNICATION_FAILURE = 4  MESSAGE L_TEXT
                SYSTEM_FAILURE        = 4  MESSAGE L_TEXT
                OTHERS                = 0.
          ENDIF.  "none of the fields exist.

          IF L_IV_DUEDT_EXIST = 'X' AND L_REMSN_EXIST IS INITIAL.
*** determine iv_duedt
            SELECT SINGLE ZFBDT INTO L_ZFBDT
                  FROM REGUP
                       WHERE LAUFD = IS_FPAYP-LAUFD AND
                             LAUFI = IS_FPAYP-LAUFI AND
                             XVORL = IS_FPAYP-XVORL AND
                             BUKRS = IS_FPAYP-BUKRS AND
                             LIFNR = L_LIFNR        AND
                             BELNR = IS_FPAYP-DOC2R+4(10) AND
                             XBLNR = IS_FPAYP-XBLNR.

            CALL FUNCTION G_FUNCTION
                    DESTINATION    L_DEST
            EXPORTING
             LAUFD                 = IS_FPAYP-LAUFD
             LAUFI                 = IS_FPAYP-LAUFI
             BUKRS                 = IS_FPAYP-BUKRS
             LIFNR                 = L_LIFNR
*            xblnr                 = is_fpayp-xblnr  "N2307673
             XBLNR                 = <XBLNR>         "N2307673
             IV_DUEDT              = L_ZFBDT
            EXCEPTIONS
             COMMUNICATION_FAILURE = 4 MESSAGE L_TEXT
             SYSTEM_FAILURE        = 4 MESSAGE L_TEXT
             OTHERS                = 0.
          ENDIF. "if iv_duedt exists but remsn does not

          IF L_REMSN_EXIST = 'X' AND L_IV_DUEDT_EXIST IS INITIAL.
            IF IS_FPAYP-SGTXT+0(5) EQ '00000'. "means new posting run number
              L_REMSN = IS_FPAYP-SGTXT+5(10).
            ELSE.
              L_REMSN = IS_FPAYP-SGTXT+0(5).
            ENDIF.
            CALL FUNCTION G_FUNCTION
              DESTINATION L_DEST
              EXPORTING
                LAUFD                 = IS_FPAYP-LAUFD
                LAUFI                 = IS_FPAYP-LAUFI
                BUKRS                 = IS_FPAYP-BUKRS
                LIFNR                 = L_LIFNR
*                xblnr                 = is_fpayp-xblnr  "N2307673
                XBLNR                 = <XBLNR>          "N2307673
                REMSN                 = L_REMSN
              EXCEPTIONS
                COMMUNICATION_FAILURE = 4 MESSAGE L_TEXT
                SYSTEM_FAILURE        = 4 MESSAGE L_TEXT
                OTHERS                = 0.
          ENDIF. "if remsn exists but l_due_date does not

        ENDIF.   "if func found by import_interface
      ENDIF.  "func exists take its interface data

      IF SY-SUBRC NE 0.
        IF SY-BATCH EQ SPACE.
          MESSAGE I265(BFIBL02) WITH L_AWSYS
                                     L_DEST
                                     IS_FPAYP-BUKRS
                                     IS_FPAYP-DOC2R.
          MESSAGE I266(BFIBL02) WITH L_TEXT L_TEXT+50.
          MESSAGE I267(BFIBL02) WITH IS_FPAYH-DOC1R.
        ELSE.
          MESSAGE S265(BFIBL02) WITH L_AWSYS
                                     L_DEST
                                     IS_FPAYP-BUKRS
                                     IS_FPAYP-DOC2R.
          MESSAGE S266(BFIBL02) WITH L_TEXT L_TEXT+50.
          MESSAGE S267(BFIBL02) WITH IS_FPAYH-DOC1R.
        ENDIF.
      ENDIF.
    WHEN 1.    "means not distributed
      G_FUNCTION = 'RP_REMITTANCE_ACKNOWLEDGEMENT'.
*** check if func exists.
      CALL FUNCTION 'FUNCTION_EXISTS'
        EXPORTING
          FUNCNAME           = G_FUNCTION
        EXCEPTIONS
          FUNCTION_NOT_EXIST = 1
          OTHERS             = 2.
*** func exists, take its interface data.
      IF SY-SUBRC = 0.             " Function exists
        CALL FUNCTION 'FUNCTION_IMPORT_INTERFACE'
          EXPORTING
            FUNCNAME           = G_FUNCTION
            INACTIVE_VERSION   = ' '
          TABLES
            EXCEPTION_LIST     = L_EXCEPTIONS_TAB
            EXPORT_PARAMETER   = L_EXPORT_TAB
            IMPORT_PARAMETER   = L_IMPORT_TAB
            TABLES_PARAMETER   = L_TABLES_TAB
          EXCEPTIONS
            ERROR_MESSAGE      = 1
            FUNCTION_NOT_FOUND = 2
            INVALID_NAME       = 3
            OTHERS             = 4.

        IF SY-SUBRC <> 0.          "Function not found
          MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
           WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
*** Func found so check its import parameters.
        ELSE.
          READ TABLE L_IMPORT_TAB WITH KEY PARAMETER = 'IV_DUEDT'.
            IF SY-SUBRC = 0.
              L_IV_DUEDT_EXIST = 'X'.
            ENDIF.

          READ TABLE L_IMPORT_TAB WITH KEY PARAMETER = 'REMSN'.
          IF SY-SUBRC = 0.
            L_REMSN_EXIST = 'X'.
          ENDIF.

      READ TABLE L_IMPORT_TAB                        "N2307673
        WITH KEY PARAMETER = 'XBLNR'.                "N2307673

      CREATE DATA DREF_XBLNR TYPE (L_IMPORT_TAB-TYP). "N2307673

      IF SY-SUBRC = 0.                                "N2307673
        ASSIGN DREF_XBLNR->* TO <XBLNR>.              "N2307673
      ENDIF.                                          "N2307673
      IF NOT <XBLNR> IS ASSIGNED.                     "N2307673
        ASSIGN IS_FPAYP-XBLNR TO <XBLNR>.             "N2307673
      ENDIF.                                          "N2307673

      <XBLNR> = IS_FPAYP-XBLNR.                       "N2307673

        IF L_IV_DUEDT_EXIST = 'X' AND L_REMSN_EXIST = 'X'.
            IF IS_FPAYP-SGTXT+0(5) EQ '00000'. "means new posting run number
              L_REMSN = IS_FPAYP-SGTXT+5(10).
            ELSE.
              L_REMSN = IS_FPAYP-SGTXT+0(5).
            ENDIF.
*** determine iv_duedt
            SELECT SINGLE ZFBDT INTO L_ZFBDT
                  FROM REGUP
                       WHERE LAUFD = IS_FPAYP-LAUFD AND
                             LAUFI = IS_FPAYP-LAUFI AND
                             XVORL = IS_FPAYP-XVORL AND
                             BUKRS = IS_FPAYP-BUKRS AND
                             LIFNR = L_LIFNR        AND
                             BELNR = IS_FPAYP-DOC2R+4(10) AND
                             XBLNR = IS_FPAYP-XBLNR.

            CALL FUNCTION G_FUNCTION
               EXPORTING
                LAUFD  = IS_FPAYP-LAUFD
                LAUFI  = IS_FPAYP-LAUFI
                BUKRS  = IS_FPAYP-BUKRS
                LIFNR  = L_LIFNR
*                xblnr  = is_fpayp-xblnr    "N2307673
                XBLNR    = <XBLNR>          "N2307673
                ZFBDT  = L_ZFBDT
                REMSN  = L_REMSN
           EXCEPTIONS
                OTHERS = 0.
         ENDIF.   "if both fields exist

         IF L_IV_DUEDT_EXIST IS INITIAL AND L_REMSN_EXIST IS INITIAL.
            CALL FUNCTION G_FUNCTION
              EXPORTING
                LAUFD                 = IS_FPAYP-LAUFD
                LAUFI                 = IS_FPAYP-LAUFI
                BUKRS                 = IS_FPAYP-BUKRS
                LIFNR                 = L_LIFNR
*               xblnr                 = is_fpayp-xblnr   "N2307673
                XBLNR                 = <XBLNR>          "N2307673
              EXCEPTIONS
                OTHERS                = 0.
          ENDIF.  "neither fields exist.

          IF L_IV_DUEDT_EXIST = 'X' AND L_REMSN_EXIST IS INITIAL.
*** determine iv_duedt
            SELECT SINGLE ZFBDT INTO L_ZFBDT
                  FROM REGUP
                       WHERE LAUFD = IS_FPAYP-LAUFD AND
                             LAUFI = IS_FPAYP-LAUFI AND
                             XVORL = IS_FPAYP-XVORL AND
                             BUKRS = IS_FPAYP-BUKRS AND
                             LIFNR = L_LIFNR        AND
                             BELNR = IS_FPAYP-DOC2R+4(10) AND
                             XBLNR = IS_FPAYP-XBLNR.

            CALL FUNCTION G_FUNCTION
             EXPORTING
             LAUFD                 = IS_FPAYP-LAUFD
             LAUFI                 = IS_FPAYP-LAUFI
             BUKRS                 = IS_FPAYP-BUKRS
             LIFNR                 = L_LIFNR
*             xblnr                 = is_fpayp-xblnr  "N2307673
             XBLNR                 = <XBLNR>          "N2307673
             IV_DUEDT              = L_ZFBDT
            EXCEPTIONS
             OTHERS                = 0.
          ENDIF. "if iv_duedt exists but remsn does not

          IF L_REMSN_EXIST = 'X' AND L_IV_DUEDT_EXIST IS INITIAL.
            IF IS_FPAYP-SGTXT+0(5) EQ '00000'. "means new posting run number
              L_REMSN = IS_FPAYP-SGTXT+5(10).
            ELSE.
              L_REMSN = IS_FPAYP-SGTXT+0(5).
            ENDIF.
      CALL FUNCTION G_FUNCTION
           EXPORTING
                LAUFD  = IS_FPAYP-LAUFD
                LAUFI  = IS_FPAYP-LAUFI
                BUKRS  = IS_FPAYP-BUKRS
                LIFNR  = L_LIFNR
*                xblnr  = is_fpayp-xblnr  "N2307673
                XBLNR   = <XBLNR>          "N2307673
                REMSN                 = L_REMSN
              EXCEPTIONS
                OTHERS                = 0.
          ENDIF. "if remsn exists but l_due_date does not

         ENDIF.   "if func found by import_interface
      ENDIF.  "func exists take its interface data

    WHEN 2.
      MESSAGE ID SY-MSGID TYPE 'E' NUMBER SY-MSGNO
              WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDCASE.


ENDFORM.                               " hr_remittance_acknowledgement


*----------------------------------------------------------------------*
* Form WAIT_FOR_VALIDATION
* If payment document validation is active (PAR_BELP) and if payment
* media creation was scheduled together with FI payment run (PAR_F11S)
* then the system shall wait until the number of payments is equal to
* the number of posted documents to enable payment document validation
*----------------------------------------------------------------------*
FORM WAIT_FOR_VALIDATION                                       "n1922823
  USING I_LAUFD TYPE LAUFD
        I_LAUFI TYPE LAUFI
        I_XVORL TYPE XVORL.

  DATA:
    L_MSGTY     TYPE MSGTS,
    L_SECONDS_C TYPE CHAR10,
    L_SECONDS_N TYPE NUMC10,
    L_SECONDS   TYPE I,
    LS_REGUV    TYPE REGUV.

  CHECK I_XVORL IS INITIAL.      "no validation for proposal runs

  CHECK I_LAUFI+5(1) EQ SPACE    "waiting only supported for FI payment
     OR I_LAUFI+5(1) EQ 'R'.     "programs F110 or F111

* check customized message for situation that postings are missing:
* W - wait and continue after wait time (with message in log)
* E - wait and stop after wait time
  CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
    EXPORTING
      I_ARBGB = 'BFIBL02'
      I_DTYPE = 'W'
      I_MSGNR = '169'
   IMPORTING
      E_MSGTY = L_MSGTY.
  CHECK L_MSGTY NE '-'.          "message switched off -> old behavior

* get wait time (60 seconds default)
  GET PARAMETER ID 'FIBL_VALIDATION_WAIT' FIELD L_SECONDS_C.
  L_SECONDS_N = L_SECONDS_C.     "eliminate non-numeric characters
  IF L_SECONDS_N IS INITIAL.
    L_SECONDS = 60.
  ELSE.
    L_SECONDS = L_SECONDS_N.
  ENDIF.

* check that all postings are finished
  DO L_SECONDS TIMES.
    SELECT SINGLE * FROM REGUV INTO LS_REGUV
      WHERE LAUFD EQ I_LAUFD
      AND   LAUFI EQ I_LAUFI.
    IF LS_REGUV-ANZER EQ LS_REGUV-ANZGB.
      EXIT.
    ENDIF.
    WAIT UP TO 1 SECONDS.
  ENDDO.

* if not finished after wait time, raise message
  IF LS_REGUV-ANZER NE LS_REGUV-ANZGB.
    IF SY-BATCH IS INITIAL.
      IF L_MSGTY EQ 'E'.
        MESSAGE E169 WITH L_SECONDS.
      ELSE.
        MESSAGE I169 WITH L_SECONDS.
      ENDIF.
    ELSE.
      MESSAGE S169 WITH L_SECONDS.
      IF L_MSGTY EQ 'E'.
        STOP.
      ENDIF.
    ENDIF.
  ENDIF.

ENDFORM.                                                       "n1922823

* begin 2573070
FORM CHECK_MESSAGE_STOP_CREATION CHANGING C_STOP_CREATION TYPE C.

* also called out of RBNK_PAYM_GRP_N_BATCH
  C_STOP_CREATION = SPACE.
  DATA LT_FIMSG TYPE FIMSG OCCURS 0 WITH HEADER LINE.
  CALL FUNCTION 'FI_MESSAGE_GET'
  TABLES
    T_FIMSG = LT_FIMSG
  EXCEPTIONS
    NO_MESSAGE = 1
    OTHERS     = 2.
  LOOP AT LT_FIMSG WHERE MSGID = 'F0' AND MSGNO = 800 AND MSGTY = 'A'.
    C_STOP_CREATION = 'X'.
  ENDLOOP.
ENDFORM.
* end 2573070