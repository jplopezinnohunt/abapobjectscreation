************************************************************************
* Include ZFPAYM_STA — REPLAY MODE                                     *
* Origin: FPAYM_STA (P01 RPY_PROGRAM_READ session #072)                *
* 8 blocks commented out — see markers '* >>> ZREPLAY-REMOVED'.        *
*                                                                      *
* Validation chain:                                                    *
*   lines  17-28   DD prenotif gate (REGUV.X_DD_PRENOTIF check)
*   lines  31-56   FIBL_PAYMENT_RUN_MERGE_CHECK gate
*   lines  92-100  check_reguv_status(sapfpaym_schedule) — REGUV.STATUS gate
*   lines 103-159  Pre-service + popup F4 + matching ENDIF of IF pm_grpno IS INITIAL
*   lines 161-184  ENQUEUE_EFDFPAYG lock
*   lines 205-231  *** CRITICAL *** ANZ_ERZ LE ANZ_ERL re-execution gate (body only — keep outer ENDIF on 232)
*   lines 378-378  COMMIT WORK (deferred — ROLLBACK at END-OF-SELECTION)
************************************************************************

************************************************************************
* Include FPAYM_STA                                                    *
* Start Of Selection                                                   *
************************************************************************

START-OF-SELECTION.

  CLEAR gc_xselect.

* Check that run date and identification are filled
  IF pm_laufd IS INITIAL OR pm_laufi IS INITIAL.
    MESSAGE s153.
    STOP.
  ENDIF.

* No payment media for direct debit prenotifications
*** >>> ZREPLAY-REMOVED (DD prenotif gate (REGUV.X_DD_PRENOTIF check)) — lines 17-28 of original FPAYM_STA
*   CLEAR gc_dd_prenotif.
*   SELECT SINGLE x_dd_prenotif FROM reguv INTO gc_dd_prenotif
*     WHERE laufd EQ pm_laufd
*     AND   laufi EQ pm_laufi.
*   IF NOT gc_dd_prenotif IS INITIAL.
*     IF sy-batch EQ space.
*       MESSAGE i477(f0).
*     ELSE.
*       MESSAGE s477(f0).
*     ENDIF.
*     STOP.
*   ENDIF.

* Check that run id is not reserved for cross payment run media
*** >>> ZREPLAY-REMOVED (FIBL_PAYMENT_RUN_MERGE_CHECK gate) — lines 31-56 of original FPAYM_STA
*   g_function = 'FIBL_PAYMENT_RUN_MERGE_CHECK'.
*   CALL FUNCTION 'FUNCTION_EXISTS'
*     EXPORTING
*       funcname           = g_function
*     EXCEPTIONS
*       function_not_exist = 1.
*   IF sy-subrc = 0.
*     CALL FUNCTION g_function
*          EXPORTING
*               i_laufd    = pm_laufd
*               i_laufi    = pm_laufi
*          EXCEPTIONS
*               merge_only = 1.
*     IF sy-subrc NE 0.
* * begin 2547830
*       IF sy-batch = space.
*         MESSAGE ID sy-msgid TYPE 'I' NUMBER sy-msgno
*                 WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
*       ELSE.
* * end 2547830
*         MESSAGE ID sy-msgid TYPE 'S' NUMBER sy-msgno
*                 WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
*       ENDIF.     " 2547830
*       STOP.
*     ENDIF.
*   ENDIF.

* Check filesytem and map into right field
  IF par_xfil IS INITIAL.
    gc_filesystem = '1'.
* In the TemSe case we do not allow to populate both        "nte1428908
    clear par_both.                                         "nte1428908
  ELSE.
    gc_filesystem = '2'.
  ENDIF.

* Convert selection parameters for payment medium format parameters
* and customer payment medium format parameters to initial values
* of structures of payment medium format parameters and customer
* payment medium format parameters if required
  IF par_forp IS INITIAL AND
     NOT gs_tfpm042ff-formf IS INITIAL.
    CALL FUNCTION 'CHECK_STRUCTURE_IS_INITIAL'
      EXPORTING
        i_tabname = gs_tfpm042ff-formf
      CHANGING
        c_entries = par_forp
      EXCEPTIONS
        OTHERS    = 1.
  ENDIF.
  IF par_fopc IS INITIAL AND
     NOT gs_tfpm042ffc-formf IS INITIAL.
    CALL FUNCTION 'CHECK_STRUCTURE_IS_INITIAL'
      EXPORTING
        i_tabname = gs_tfpm042ffc-formf
      CHANGING
        c_entries = par_fopc
      EXCEPTIONS
        OTHERS    = 1.
  ENDIF.

*** >>> ZREPLAY-REMOVED (check_reguv_status(sapfpaym_schedule) — REGUV.STATUS gate) — lines 92-100 of original FPAYM_STA
* * begin 2421548
*   DATA ld_error(1) TYPE C.
*   PERFORM check_reguv_status(sapfpaym_schedule)
*     USING    pm_laufd pm_laufi pm_xvorl
*     CHANGING ld_error.
*   IF ld_error <> space.
*     STOP.
*   ENDIF.
* * end 2421548

* Get a payment group -------------------------------------------------*
*** >>> ZREPLAY-REMOVED (Pre-service + popup F4 + matching ENDIF of IF pm_grpno IS INITIAL) — lines 103-159 of original FPAYM_STA
*   IF pm_grpno IS INITIAL.
* 
* *   Check whether the arrangement of payment groups is done yet - if
* *-- it isn't -  call the pre-service of the payment medium tool -------*
*     CALL FUNCTION 'FI_CHECK_PAYMENT_DATA'
*       EXPORTING
*         id_laufd   = pm_laufd
*         ic_laufi   = pm_laufi
*         ic_xvorl   = pm_xvorl
*       IMPORTING
*         ec_updated = gc_xpresrv
*       EXCEPTIONS
*         OTHERS     = 1.
*     IF sy-subrc NE 0.
*       MESSAGE s151 WITH pm_laufd pm_laufi pm_xvorl.
*       STOP.
*     ENDIF.
* 
*     IF gc_xpresrv IS INITIAL.
* *     Call pre-service and send a commit Work to make further changes
* *     database tables persistent if the pre-service was successful.
*       CALL FUNCTION 'FI_UPDATE_PAYMENT_DATA'
*         EXPORTING
*           i_laufd   = pm_laufd
*           i_laufi   = pm_laufi
*           i_xvorl   = pm_xvorl
*         IMPORTING
*           e_updated = gc_xpresrv.
* 
*     ENDIF.
* 
* *   Get a payment group - if there is more than one payment group -
* *-- by F4 value selection ---------------------------------------------*
*     CALL FUNCTION 'FI_PAYGROUP_F4'
*       EXPORTING
*         i_laufd            = pm_laufd
*         i_laufi            = pm_laufi
*         i_xvorl            = pm_xvorl
*         i_formi            = par_form
*       IMPORTING
*         e_grpno            = pm_grpno
*       EXCEPTIONS
*         parameters_invalid = 1
*         not_found          = 2
*         canceled           = 3
*         OTHERS             = 4.
*     IF sy-subrc NE 0 OR pm_grpno IS INITIAL.
*       IF sy-subrc NE 0.                                   "note 2125472
*         MESSAGE ID sy-msgid TYPE 'S' NUMBER sy-msgno      "note 2125472
*           WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.       "note 2125472
*       ENDIF.                                              "note 2125472
*       STOP.
*     ENDIF.
* 
* * begin  2380623
* * Dequeue is done in FI_UPDATE_REGUH_FPM
*   ENDIF.  "  IF pm_grpno IS INITIAL.
* end 2380623
*** >>> ZREPLAY-REMOVED (ENQUEUE_EFDFPAYG lock) — lines 161-184 of original FPAYM_STA
*     CALL FUNCTION 'ENQUEUE_EFDFPAYG'
*       EXPORTING
*         laufd = pm_laufd
*         laufi = pm_laufi
*         xvorl = pm_xvorl
*         grpno = pm_grpno
*         _scope = '1'                  "  2380623
*         _wait = 'X'                   "  2136524
*       EXCEPTIONS
*          foreign_lock   = 1
*          system_failure = 2
*          OTHERS         = 3.
*       IF sy-subrc <> 0.
*         DATA : lc_user LIKE sy-uname,
*                lc_payrun(30) TYPE C.
*         lc_user = sy-msgv1.
*         DATA lc_subrc TYPE text20 VALUE '| RC'.                        " 2380623
*         WRITE sy-subrc TO lc_subrc+5.
*         CONDENSE lc_subrc.
*         MESSAGE s781(fb) WITH 'DFPAYG' pm_grpno lc_subrc '| PROG FPAYM_STA'.
*         CONCATENATE pm_laufd pm_laufi pm_xvorl INTO lc_payrun SEPARATED BY space.
*         MESSAGE E202 WITH lc_payrun lc_user.
*         STOP.
*       ENDIF.
*  ENDIF. " 2380623

*** ZREPLAY: auto-populate PM_GRPNO from DFPAYG if user left it blank
*** (replaces the FI_PAYGROUP_F4 popup we removed in lines 136-155)
  IF pm_grpno IS INITIAL.
    SELECT SINGLE grpno FROM dfpayg INTO pm_grpno
      WHERE laufd = pm_laufd
      AND   laufi = pm_laufi
      AND   xvorl = pm_xvorl.
    IF sy-subrc <> 0.
      MESSAGE e151 WITH pm_laufd pm_laufi pm_xvorl.
      STOP.
    ENDIF.
    WRITE: / 'ZREPLAY auto-detected GRPNO=', pm_grpno.
  ENDIF.

* Read payment group --------------------------------------------------*
  CALL FUNCTION 'FI_PAYGROUP_READ'
    EXPORTING
      i_laufd   = pm_laufd
      i_laufi   = pm_laufi
      i_xvorl   = pm_xvorl
      i_grpno   = pm_grpno
    IMPORTING
      e_fpayg   = gs_dfpayg
    EXCEPTIONS
      not_found = 1.
  IF sy-subrc NE 0.
    MESSAGE ID sy-msgid TYPE 'S' NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    STOP.
  ELSEIF gs_dfpayg-formi NE par_form.
    MESSAGE s157 WITH pm_grpno gs_dfpayg-formi par_form.
    STOP.
*** >>> ZREPLAY-REMOVED (*** CRITICAL *** ANZ_ERZ LE ANZ_ERL re-execution gate (body only — keep outer ENDIF on 232)) — lines 205-231 of original FPAYM_STA
*   ELSEIF gs_dfpayg-anz_erz LE gs_dfpayg-anz_erl
*      AND gs_dfpayg-anz_erz GT 0.
*     CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
*       EXPORTING
*         i_arbgb = 'BFIBL02'
*         i_dtype = '-'
*         i_msgnr = '166'
*       IMPORTING
*         e_msgty = gc_message_type.
* *   SAP Note 2927769 - BCM: Enable Re-Send of Payment Batch in BNK_MONI
* *   Skip customized message BFIBL02(166) from transaction BNK_MONI
*     IF p_bcmrsd EQ abap_true.
*        AUTHORITY-CHECK OBJECT 'F_BNK_RSND'
*         ID 'ACTVT' FIELD '01'.
*       IF sy-subrc EQ 0.
* *       Override customized message - in case this was called from BNK_MONI
*         gc_message_type = '-'.
*       ENDIF.
*     ENDIF. "IF p_bcmrsd EQ abap_true.
* *   SAP Note 2927769
*     IF gc_message_type NE '-'.
*       MESSAGE s166 WITH gs_dfpayg-grpno
*                         gs_dfpayg-anz_erz
*                         gs_dfpayg-anz_erl.
*       gc_too_many_files(1) = 'X'.
*       STOP.
*     ENDIF.
  ENDIF.

* only important for the log of the payment program
* construct a message depending on the granularity of the payment group
  IF NOT ( par_xpy1 IS INITIAL AND
           par_xpy3 IS INITIAL AND
           par_xpy5 IS INITIAL ).
    PERFORM output_start_message.
  ENDIF.

* Error log should always be printed if program is started online
  IF NOT sy-batch IS INITIAL.
    par_xerr = 'X'.
  ENDIF.

* Get format details
  CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
    EXPORTING
      i_formi     = par_form
    IMPORTING
      e_tfpm042f  = gs_tfpm042f
      e_tfpm042ft = gs_tfpm042ft.

* Adjust parameters to the attributes of the payment format
  PERFORM adjust_parameters_to_format.

* Check parameters for SAPscript output
  IF NOT par_xpy1 IS INITIAL.
    CALL FUNCTION 'CHECK_TEXT_PRINT_PARAMETERS'
      EXPORTING
        i_title_text = text_py1
        i_itcpo      = par_pri1
      IMPORTING
        e_itcpo      = gs_pri1.
  ENDIF.
  IF NOT par_xpy3 IS INITIAL.
    CALL FUNCTION 'CHECK_TEXT_PRINT_PARAMETERS'
      EXPORTING
        i_title_text = gc_text_py3
        i_itcpo      = par_pri3
      IMPORTING
        e_itcpo      = gs_pri3.
  ENDIF.

* Check parameters for list output
  CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
    EXPORTING
      i_title_text = text-013
      i_pri_params = par_prie
      i_arc_params = par_arce
    IMPORTING
      e_pri_params = gs_prie
      e_arc_params = gs_arce.
  IF NOT par_xpy5 IS INITIAL.
    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
      EXPORTING
        i_title_text = text_py5
        i_pri_params = par_pri5
        i_arc_params = par_arc5
      IMPORTING
        e_pri_params = gs_pri5
        e_arc_params = gs_arc5.
  ENDIF.

* check parameters for accompanying list
  IF NOT par_xlst IS INITIAL.
    CLEAR gs_variant.
    gs_variant-report  = sy-repid.
    IF NOT par_vari IS INITIAL.
      gs_variant-variant = par_vari.
      CALL FUNCTION 'REUSE_ALV_VARIANT_EXISTENCE'
        EXPORTING
          i_save     = 'A'
        CHANGING
          cs_variant = gs_variant
        EXCEPTIONS
          OTHERS     = 0.
    ENDIF.

    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
      EXPORTING
        i_title_text = text-012
        i_pri_params = par_pril
        i_arc_params = par_arcl
      IMPORTING
        e_pri_params = gs_pril
        e_arc_params = gs_arcl.
    IF NOT par_scrn IS INITIAL.
      CLEAR gs_pril-pdest.
    ENDIF.
  ENDIF.

* get the free selections from Logical Database FPMF
  PERFORM get_free_selections IN PROGRAM sapdbfpmf
                                  TABLES gt_freesel.

* concerning the form for the accompany-sheet:
* only one form-parameter can be filled par_fyp3 or par_pdf3
  IF par_ftyp IS INITIAL.
    CLEAR par_pdf3.
  ELSE.
    CLEAR par_fpy3.
  ENDIF.

* Transfer of all parameters to the tool box
  CALL FUNCTION 'FI_PAYM_PARAMETERS_PUT'
    EXPORTING
      i_laufd            = pm_laufd
      i_laufi            = pm_laufi
      i_xvorl            = pm_xvorl
      i_xprint_1         = par_xpy1
      i_layout_set_z     = par_fpy1
      i_pdf_z            = par_pdf1
      i_print_params_1   = gs_pri1
      i_filler           = par_fill  " note 1498990
      i_xdme             = par_xpy3
      i_xdme_file_system = gc_filesystem
      i_temse_and_file   = par_both                         "nte1428908
      i_dme_file_name    = par_file
      i_layout_set_w     = par_fpy3
      i_pdf_w            = par_pdf3
      i_dme_sheet_params = gs_pri3
      i_xlist            = par_xpy5
      i_list_params      = gs_pri5
      i_list_arcpar      = gs_arc5
      i_xacc             = par_xlst
      i_acc_params       = gs_pril
      i_acc_arcpar       = gs_arcl
      i_acc_variant      = gs_variant
      i_xerror           = par_xerr
      i_error_params     = gs_prie
      i_error_arcpar     = gs_arce
      i_format           = par_form
      i_format_params    = par_forp
      i_format_params_c  = par_fopc
    TABLES
      it_freesel         = gt_freesel.

* Fill the reference field of the application log
  CONCATENATE pm_laufi pm_laufd pm_xvorl INTO gc_extnumber.

* Initialise the application log
  CALL FUNCTION 'FI_PAYM_MESSAGE_LOG_CREATE'
    EXPORTING
      im_extnumber = gc_extnumber.

*** >>> ZREPLAY-REMOVED (COMMIT WORK (deferred — ROLLBACK at END-OF-SELECTION)) — lines 378-378 of original FPAYM_STA
*   COMMIT WORK.
*** <<< ZREPLAY-REMOVED
  CLEAR sy-msgno.

  IF NOT par_f11s IS INITIAL AND NOT par_belp IS INITIAL.      "n1922823
    PERFORM wait_for_validation
      USING pm_laufd
            pm_laufi
            pm_xvorl.
  ENDIF.
