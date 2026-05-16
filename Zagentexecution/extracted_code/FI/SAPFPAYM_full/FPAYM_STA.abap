************************************************************************
* Include FPAYM_STA                                                    *
* Start Of Selection                                                   *
************************************************************************

START-OF-SELECTION.

  CLEAR GC_XSELECT.

* Check that run date and identification are filled
  IF PM_LAUFD IS INITIAL OR PM_LAUFI IS INITIAL.
    MESSAGE S153.
    STOP.
  ENDIF.

* No payment media for direct debit prenotifications
  CLEAR GC_DD_PRENOTIF.
  SELECT SINGLE X_DD_PRENOTIF FROM REGUV INTO GC_DD_PRENOTIF
    WHERE LAUFD EQ PM_LAUFD
    AND   LAUFI EQ PM_LAUFI.
  IF NOT GC_DD_PRENOTIF IS INITIAL.
    IF SY-BATCH EQ SPACE.
      MESSAGE I477(F0).
    ELSE.
      MESSAGE S477(F0).
    ENDIF.
    STOP.
  ENDIF.

* Check that run id is not reserved for cross payment run media
  G_FUNCTION = 'FIBL_PAYMENT_RUN_MERGE_CHECK'.
  CALL FUNCTION 'FUNCTION_EXISTS'
    EXPORTING
      FUNCNAME           = G_FUNCTION
    EXCEPTIONS
      FUNCTION_NOT_EXIST = 1.
  IF SY-SUBRC = 0.
    CALL FUNCTION G_FUNCTION
         EXPORTING
              I_LAUFD    = PM_LAUFD
              I_LAUFI    = PM_LAUFI
         EXCEPTIONS
              MERGE_ONLY = 1.
    IF SY-SUBRC NE 0.
* begin 2547830
      IF SY-BATCH = SPACE.
        MESSAGE ID SY-MSGID TYPE 'I' NUMBER SY-MSGNO
                WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ELSE.
* end 2547830
        MESSAGE ID SY-MSGID TYPE 'S' NUMBER SY-MSGNO
                WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      ENDIF.     " 2547830
      STOP.
    ENDIF.
  ENDIF.

* Check filesytem and map into right field
  IF PAR_XFIL IS INITIAL.
    GC_FILESYSTEM = '1'.
* In the TemSe case we do not allow to populate both        "nte1428908
    CLEAR PAR_BOTH.                                         "nte1428908
  ELSE.
    GC_FILESYSTEM = '2'.
  ENDIF.

* Convert selection parameters for payment medium format parameters
* and customer payment medium format parameters to initial values
* of structures of payment medium format parameters and customer
* payment medium format parameters if required
  IF PAR_FORP IS INITIAL AND
     NOT GS_TFPM042FF-FORMF IS INITIAL.
    CALL FUNCTION 'CHECK_STRUCTURE_IS_INITIAL'
      EXPORTING
        I_TABNAME = GS_TFPM042FF-FORMF
      CHANGING
        C_ENTRIES = PAR_FORP
      EXCEPTIONS
        OTHERS    = 1.
  ENDIF.
  IF PAR_FOPC IS INITIAL AND
     NOT GS_TFPM042FFC-FORMF IS INITIAL.
    CALL FUNCTION 'CHECK_STRUCTURE_IS_INITIAL'
      EXPORTING
        I_TABNAME = GS_TFPM042FFC-FORMF
      CHANGING
        C_ENTRIES = PAR_FOPC
      EXCEPTIONS
        OTHERS    = 1.
  ENDIF.

* begin 2421548
  DATA LD_ERROR(1) TYPE C.
  PERFORM CHECK_REGUV_STATUS(SAPFPAYM_SCHEDULE)
    USING    PM_LAUFD PM_LAUFI PM_XVORL
    CHANGING LD_ERROR.
  IF LD_ERROR <> SPACE.
    STOP.
  ENDIF.
* end 2421548

* Get a payment group -------------------------------------------------*
  IF PM_GRPNO IS INITIAL.

*   Check whether the arrangement of payment groups is done yet - if
*-- it isn't -  call the pre-service of the payment medium tool -------*
    CALL FUNCTION 'FI_CHECK_PAYMENT_DATA'
      EXPORTING
        ID_LAUFD   = PM_LAUFD
        IC_LAUFI   = PM_LAUFI
        IC_XVORL   = PM_XVORL
      IMPORTING
        EC_UPDATED = GC_XPRESRV
      EXCEPTIONS
        OTHERS     = 1.
    IF SY-SUBRC NE 0.
      MESSAGE S151 WITH PM_LAUFD PM_LAUFI PM_XVORL.
      STOP.
    ENDIF.

    IF GC_XPRESRV IS INITIAL.
*     Call pre-service and send a commit Work to make further changes
*     database tables persistent if the pre-service was successful.
      CALL FUNCTION 'FI_UPDATE_PAYMENT_DATA'
        EXPORTING
          I_LAUFD   = PM_LAUFD
          I_LAUFI   = PM_LAUFI
          I_XVORL   = PM_XVORL
        IMPORTING
          E_UPDATED = GC_XPRESRV.

    ENDIF.

*   Get a payment group - if there is more than one payment group -
*-- by F4 value selection ---------------------------------------------*
    CALL FUNCTION 'FI_PAYGROUP_F4'
      EXPORTING
        I_LAUFD            = PM_LAUFD
        I_LAUFI            = PM_LAUFI
        I_XVORL            = PM_XVORL
        I_FORMI            = PAR_FORM
      IMPORTING
        E_GRPNO            = PM_GRPNO
      EXCEPTIONS
        PARAMETERS_INVALID = 1
        NOT_FOUND          = 2
        CANCELED           = 3
        OTHERS             = 4.
    IF SY-SUBRC NE 0 OR PM_GRPNO IS INITIAL.
      IF SY-SUBRC NE 0.                                   "note 2125472
        MESSAGE ID SY-MSGID TYPE 'S' NUMBER SY-MSGNO      "note 2125472
          WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.       "note 2125472
      ENDIF.                                              "note 2125472
      STOP.
    ENDIF.

* begin  2380623
* Dequeue is done in FI_UPDATE_REGUH_FPM
  ENDIF.  "  IF pm_grpno IS INITIAL.
* end 2380623
    CALL FUNCTION 'ENQUEUE_EFDFPAYG'
      EXPORTING
        LAUFD = PM_LAUFD
        LAUFI = PM_LAUFI
        XVORL = PM_XVORL
        GRPNO = PM_GRPNO
        _SCOPE = '1'                  "  2380623
        _WAIT = 'X'                   "  2136524
      EXCEPTIONS
         FOREIGN_LOCK   = 1
         SYSTEM_FAILURE = 2
         OTHERS         = 3.
      IF SY-SUBRC <> 0.
        DATA : LC_USER LIKE SY-UNAME,
               LC_PAYRUN(30) TYPE C.
        LC_USER = SY-MSGV1.
        DATA LC_SUBRC TYPE TEXT20 VALUE '| RC'.                        " 2380623
        WRITE SY-SUBRC TO LC_SUBRC+5.
        CONDENSE LC_SUBRC.
        MESSAGE S781(FB) WITH 'DFPAYG' PM_GRPNO LC_SUBRC '| PROG FPAYM_STA'.
        CONCATENATE PM_LAUFD PM_LAUFI PM_XVORL INTO LC_PAYRUN SEPARATED BY SPACE.
        MESSAGE E202 WITH LC_PAYRUN LC_USER.
        STOP.
      ENDIF.
*  ENDIF. " 2380623

* Read payment group --------------------------------------------------*
  CALL FUNCTION 'FI_PAYGROUP_READ'
    EXPORTING
      I_LAUFD   = PM_LAUFD
      I_LAUFI   = PM_LAUFI
      I_XVORL   = PM_XVORL
      I_GRPNO   = PM_GRPNO
    IMPORTING
      E_FPAYG   = GS_DFPAYG
    EXCEPTIONS
      NOT_FOUND = 1.
  IF SY-SUBRC NE 0.
    MESSAGE ID SY-MSGID TYPE 'S' NUMBER SY-MSGNO
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    STOP.
  ELSEIF GS_DFPAYG-FORMI NE PAR_FORM.
    MESSAGE S157 WITH PM_GRPNO GS_DFPAYG-FORMI PAR_FORM.
    STOP.
  ELSEIF GS_DFPAYG-ANZ_ERZ LE GS_DFPAYG-ANZ_ERL
     AND GS_DFPAYG-ANZ_ERZ GT 0.
    CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
      EXPORTING
        I_ARBGB = 'BFIBL02'
        I_DTYPE = '-'
        I_MSGNR = '166'
      IMPORTING
        E_MSGTY = GC_MESSAGE_TYPE.
*   SAP Note 2927769 - BCM: Enable Re-Send of Payment Batch in BNK_MONI
*   Skip customized message BFIBL02(166) from transaction BNK_MONI
    IF P_BCMRSD EQ ABAP_TRUE.
       AUTHORITY-CHECK OBJECT 'F_BNK_RSND'
        ID 'ACTVT' FIELD '01'.
      IF SY-SUBRC EQ 0.
*       Override customized message - in case this was called from BNK_MONI
        GC_MESSAGE_TYPE = '-'.
      ENDIF.
    ENDIF. "IF p_bcmrsd EQ abap_true.
*   SAP Note 2927769
    IF GC_MESSAGE_TYPE NE '-'.
      MESSAGE S166 WITH GS_DFPAYG-GRPNO
                        GS_DFPAYG-ANZ_ERZ
                        GS_DFPAYG-ANZ_ERL.
      GC_TOO_MANY_FILES(1) = 'X'.
      STOP.
    ENDIF.
  ENDIF.

* only important for the log of the payment program
* construct a message depending on the granularity of the payment group
  IF NOT ( PAR_XPY1 IS INITIAL AND
           PAR_XPY3 IS INITIAL AND
           PAR_XPY5 IS INITIAL ).
    PERFORM OUTPUT_START_MESSAGE.
  ENDIF.

* Error log should always be printed if program is started online
  IF NOT SY-BATCH IS INITIAL.
    PAR_XERR = 'X'.
  ENDIF.

* Get format details
  CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
    EXPORTING
      I_FORMI     = PAR_FORM
    IMPORTING
      E_TFPM042F  = GS_TFPM042F
      E_TFPM042FT = GS_TFPM042FT.

* Adjust parameters to the attributes of the payment format
  PERFORM ADJUST_PARAMETERS_TO_FORMAT.

* Check parameters for SAPscript output
  IF NOT PAR_XPY1 IS INITIAL.
    CALL FUNCTION 'CHECK_TEXT_PRINT_PARAMETERS'
      EXPORTING
        I_TITLE_TEXT = TEXT_PY1
        I_ITCPO      = PAR_PRI1
      IMPORTING
        E_ITCPO      = GS_PRI1.
  ENDIF.
  IF NOT PAR_XPY3 IS INITIAL.
    CALL FUNCTION 'CHECK_TEXT_PRINT_PARAMETERS'
      EXPORTING
        I_TITLE_TEXT = GC_TEXT_PY3
        I_ITCPO      = PAR_PRI3
      IMPORTING
        E_ITCPO      = GS_PRI3.
  ENDIF.

* Check parameters for list output
  CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
    EXPORTING
      I_TITLE_TEXT = TEXT-013
      I_PRI_PARAMS = PAR_PRIE
      I_ARC_PARAMS = PAR_ARCE
    IMPORTING
      E_PRI_PARAMS = GS_PRIE
      E_ARC_PARAMS = GS_ARCE.
  IF NOT PAR_XPY5 IS INITIAL.
    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
      EXPORTING
        I_TITLE_TEXT = TEXT_PY5
        I_PRI_PARAMS = PAR_PRI5
        I_ARC_PARAMS = PAR_ARC5
      IMPORTING
        E_PRI_PARAMS = GS_PRI5
        E_ARC_PARAMS = GS_ARC5.
  ENDIF.

* check parameters for accompanying list
  IF NOT PAR_XLST IS INITIAL.
    CLEAR GS_VARIANT.
    GS_VARIANT-REPORT  = SY-REPID.
    IF NOT PAR_VARI IS INITIAL.
      GS_VARIANT-VARIANT = PAR_VARI.
      CALL FUNCTION 'REUSE_ALV_VARIANT_EXISTENCE'
        EXPORTING
          I_SAVE     = 'A'
        CHANGING
          CS_VARIANT = GS_VARIANT
        EXCEPTIONS
          OTHERS     = 0.
    ENDIF.

    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
      EXPORTING
        I_TITLE_TEXT = TEXT-012
        I_PRI_PARAMS = PAR_PRIL
        I_ARC_PARAMS = PAR_ARCL
      IMPORTING
        E_PRI_PARAMS = GS_PRIL
        E_ARC_PARAMS = GS_ARCL.
    IF NOT PAR_SCRN IS INITIAL.
      CLEAR GS_PRIL-PDEST.
    ENDIF.
  ENDIF.

* get the free selections from Logical Database FPMF
  PERFORM GET_FREE_SELECTIONS IN PROGRAM SAPDBFPMF
                                  TABLES GT_FREESEL.

* concerning the form for the accompany-sheet:
* only one form-parameter can be filled par_fyp3 or par_pdf3
  IF PAR_FTYP IS INITIAL.
    CLEAR PAR_PDF3.
  ELSE.
    CLEAR PAR_FPY3.
  ENDIF.

* Transfer of all parameters to the tool box
  CALL FUNCTION 'FI_PAYM_PARAMETERS_PUT'
    EXPORTING
      I_LAUFD            = PM_LAUFD
      I_LAUFI            = PM_LAUFI
      I_XVORL            = PM_XVORL
      I_XPRINT_1         = PAR_XPY1
      I_LAYOUT_SET_Z     = PAR_FPY1
      I_PDF_Z            = PAR_PDF1
      I_PRINT_PARAMS_1   = GS_PRI1
      I_FILLER           = PAR_FILL  " note 1498990
      I_XDME             = PAR_XPY3
      I_XDME_FILE_SYSTEM = GC_FILESYSTEM
      I_TEMSE_AND_FILE   = PAR_BOTH                         "nte1428908
      I_DME_FILE_NAME    = PAR_FILE
      I_LAYOUT_SET_W     = PAR_FPY3
      I_PDF_W            = PAR_PDF3
      I_DME_SHEET_PARAMS = GS_PRI3
      I_XLIST            = PAR_XPY5
      I_LIST_PARAMS      = GS_PRI5
      I_LIST_ARCPAR      = GS_ARC5
      I_XACC             = PAR_XLST
      I_ACC_PARAMS       = GS_PRIL
      I_ACC_ARCPAR       = GS_ARCL
      I_ACC_VARIANT      = GS_VARIANT
      I_XERROR           = PAR_XERR
      I_ERROR_PARAMS     = GS_PRIE
      I_ERROR_ARCPAR     = GS_ARCE
      I_FORMAT           = PAR_FORM
      I_FORMAT_PARAMS    = PAR_FORP
      I_FORMAT_PARAMS_C  = PAR_FOPC
    TABLES
      IT_FREESEL         = GT_FREESEL.

* Fill the reference field of the application log
  CONCATENATE PM_LAUFI PM_LAUFD PM_XVORL INTO GC_EXTNUMBER.

* Initialise the application log
  CALL FUNCTION 'FI_PAYM_MESSAGE_LOG_CREATE'
    EXPORTING
      IM_EXTNUMBER = GC_EXTNUMBER.

  COMMIT WORK.
  CLEAR SY-MSGNO.

  IF NOT PAR_F11S IS INITIAL AND NOT PAR_BELP IS INITIAL.      "n1922823
    PERFORM WAIT_FOR_VALIDATION
      USING PM_LAUFD
            PM_LAUFI
            PM_XVORL.
  ENDIF.