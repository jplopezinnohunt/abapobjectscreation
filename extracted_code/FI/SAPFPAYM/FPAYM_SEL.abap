************************************************************************
* Include FPAYM_SEL                                                    *
* Selection Screen                                                     *
************************************************************************

*- At selection screen output (PBO) -----------------------------------*
AT SELECTION-SCREEN OUTPUT.

* Action on change of format
  IF par_form NE gs_tfpm042f-formi.

*   Get format details
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
         EXPORTING
              i_formi     = par_form
         IMPORTING
              e_tfpm042f  = gs_tfpm042f
              e_tfpm042ft = gs_tfpm042ft
         EXCEPTIONS
              not_found   = 1.
    IF sy-subrc EQ 0.
      CALL FUNCTION 'FI_PAYM_FORMAT_READ_PARAMETERS'
           EXPORTING
                i_formi      = par_form
           IMPORTING
                e_tfpm042ff  = gs_tfpm042ff
                e_tfpm042ffc = gs_tfpm042ffc
           TABLES
                t_tfpm042fm  = gt_tfpm042fm
                t_tfpm042fmc = gt_tfpm042fmc
           EXCEPTIONS
                not_found    = 1.
    ELSE.
      CLEAR: gs_tfpm042f, gs_tfpm042ft,
             gs_tfpm042ff, gs_tfpm042ffc.
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
    PERFORM adjust_parameters_to_format.

  ENDIF.

* Fill icons for print parameters (white or green)
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = par_prie
            i_icon_text  = text-005
       IMPORTING
            e_arrow_icon = ebutton.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = par_pril
            i_icon_text  = text-005
       IMPORTING
            e_arrow_icon = lbutton.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = par_pri1
            i_icon_text  = text-005
       IMPORTING
            e_arrow_icon = p1button.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = par_pri3
            i_icon_text  = text-005
       IMPORTING
            e_arrow_icon = p3button.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = par_pri5
            i_icon_text  = text-005
       IMPORTING
            e_arrow_icon = p5button.

  f1button = text-105.
  f3button = text-105.

* Check, whether there are format parameters, customer format
* parameters and all obligatory fields of them and set icon for
* format parameters (white or green)
  PERFORM check_format_parameters.

* Set check boxes and push buttons activ/inactive
  IF NOT gs_tfpm042ff-formf IS INITIAL OR
     NOT gs_tfpm042ffc-formf IS INITIAL.
    gc_xformf = 'X'.
  ELSE.
    CLEAR gc_xformf.
  ENDIF.
  IF NOT gs_tfpm042f-xdme1 IS INITIAL
     AND ( gs_tfpm042f-dttyp EQ '01' OR gs_tfpm042f-dttyp EQ '04' ).
    gc_xfile = 'X'.
  ELSE.
    CLEAR gc_xfile.
  ENDIF.

  data: L_BADI_BATCH_PAYM_MEDIUM type ref to FPAYM_BATCH_PAYMENTS_MEDIUM.
  TRY.
      GET BADI L_BADI_BATCH_PAYM_MEDIUM.
      CALL BADI L_BADI_BATCH_PAYM_MEDIUM->IS_FILE_CREATION_ALLOWED
        EXPORTING
          I_TFPM042F      = gs_tfpm042f
        IMPORTING
          E_XFILE_ALLOWED = gc_xfile.
    CATCH cx_badi_not_implemented cx_badi_multiply_implemented.
  ENDTRY.


  LOOP AT SCREEN.
    PERFORM fill_screen
            USING: 'F'   gc_xformf,
                   'I'   gs_tfpm042f-formd,
                   'PY1' gs_tfpm042f-xpri1,
                   'PY2' gs_tfpm042f-xpri2,
                   'PY3' gs_tfpm042f-xdme1,
                   'PY4' gc_xfile,
                   'PY5' gs_tfpm042f-xlst1.

*-- PAR_FPY1 and TEXT_PY1 ---
    IF gs_tfpm042f-formt EQ 'P'  AND
      ( screen-name = 'TEXT_FP1' OR  " 01454480
        screen-name = 'PAR_FPY1' OR
        screen-name = 'F1BUTTON' ).
      screen-active = 0.
    ENDIF.

*-- PAR_PDF1 and TXT_PDF1 ---
    IF gs_tfpm042f-formt IS INITIAL AND
      ( screen-name = 'PAR_PDF1' OR  " 01454480
        screen-name = 'TXT_PDF1' ).
      screen-active = 0.
    ENDIF.

*-- PAR_PDF3 plus name ---
    IF par_ftyp IS INITIAL AND
*     PDF accompanying sheet
      ( screen-name = '%_PAR_PDF3_%_APP_%-TEXT' OR " 01454480
        screen-name = 'PAR_PDF3' ).
      screen-active = 0.
    ENDIF.

*-- PAR_FPY3 plus name ---
    IF par_ftyp EQ 'P' AND
*     SAPSCRIPT accompanying sheet
       ( screen-name = '%_PAR_FPY3_%_APP_%-TEXT' OR  " 01454480
         screen-name = 'PAR_FPY3' OR
         screen-name = 'F3BUTTON' ).
      screen-active = 0.
    ENDIF.

    MODIFY SCREEN.
  ENDLOOP.


*- At selection screen (PAI) ------------------------------------------*

* F4 for SAPScript formulars
AT SELECTION-SCREEN ON VALUE-REQUEST FOR par_fpy3.

  DATA l_form_name TYPE tdform.                             "lokal !!

  CALL FUNCTION 'DISPLAY_FORM_TREE_F4'
       EXPORTING
            p_tree_name = 'FI-2'
       IMPORTING
            p_form_name = l_form_name
       EXCEPTIONS
            OTHERS      = 4.

  IF sy-subrc EQ 0 AND l_form_name NE space.
    par_fpy3 = l_form_name.
  ENDIF.

* value request for layout variant for accompanying list
AT SELECTION-SCREEN ON VALUE-REQUEST FOR par_vari.
  CLEAR gs_variant.
  gs_variant-report = sy-repid.
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
      par_vari = gs_variant-variant.
    ENDIF.
  ENDIF.


* check layout variant for accompanying list
AT SELECTION-SCREEN ON par_vari.
  CLEAR gs_variant.
  gs_variant-report  = sy-repid.
  IF NOT par_vari IS INITIAL.
    gs_variant-variant = par_vari.
    CALL FUNCTION 'REUSE_ALV_VARIANT_EXISTENCE'
         EXPORTING
              i_save     = 'A'
         CHANGING
              cs_variant = gs_variant.
  ENDIF.


* Check payment medium format parameters
AT SELECTION-SCREEN ON par_form.

* New payment medium format
  IF par_form NE gs_tfpm042f-formi.

*   Check that the new payment medium format is valid
    IF NOT par_form IS INITIAL.
      CALL FUNCTION 'FI_PAYM_FORMAT_CHECK'
           EXPORTING
                i_formi = par_form.
    ENDIF.

*   Warning on change of payment medium format
    IF NOT gs_tfpm042f-formi IS INITIAL.
      CALL FUNCTION 'POPUP_TO_CONFIRM'
           EXPORTING
                titlebar        = text-100
                diagnose_object = 'FPM_FORMAT_CHANGE'
                text_question   = text-101
           IMPORTING
                answer          = gc_answer.
      IF gc_answer NE '1'.
        par_form = gs_tfpm042f-formi.
      ENDIF.
    ENDIF.
  ENDIF.

* Action on change of payment medium format
  IF par_form NE gs_tfpm042f-formi.

    TRY.                                                 "begin n2669849
      CALL FUNCTION 'FI_PAYM_FORMAT_OBSOLETE_CHECK'
        EXPORTING
          i_formi            = par_form
        EXCEPTIONS
          format_is_obsolete = 0.
      CATCH cx_root.
    ENDTRY.                                                "end n2669849

*   Initialize format parameters
    CLEAR: par_forp, par_fopc, gc_xforp, gs_tfpm042fd, gs_tfpm042fdc.

*   Get default values from database
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_DEFAULTS'
         EXPORTING
              i_formi      = par_form
         IMPORTING
              e_tfpm042fd  = gs_tfpm042fd
              e_tfpm042fdc = gs_tfpm042fdc.
    par_forp     = gs_tfpm042fd-def_params1.
    par_forp+250 = gs_tfpm042fd-def_params2.
    par_fopc     = gs_tfpm042fdc-def_params1.
    par_fopc+250 = gs_tfpm042fdc-def_params2.

*   Set defaults for check boxes
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_PROPERTIES'
         EXPORTING
              i_formi    = par_form
         IMPORTING
              e_tfpm042f = gs_tfpm042f_2.
    IF gs_tfpm042f_2-xdme1 IS INITIAL.
      par_xpy1 = gs_tfpm042f_2-xpri1.
    ELSE.
      CLEAR: par_xpy1.
    ENDIF.
    IF NOT gs_tfpm042f_2-xdme1 IS INITIAL.
      par_xpy3 = gs_tfpm042f_2-xdme1.
    ENDIF.
    par_xpy5 = gs_tfpm042f_2-xlst1.

*   Deactivate ok-code
    IF NOT sscrfields-ucomm IS INITIAL.
      MESSAGE s603.
      CLEAR sscrfields-ucomm.
    ENDIF.

* No change of payment medium format
  ELSE.

*   Check whether obligatory format parameters have to be filled
    IF gc_xforp IS INITIAL AND
       ( NOT gt_tfpm042fm[] IS INITIAL OR
         NOT gt_tfpm042fmc[] IS INITIAL ).
      MESSAGE s055(00).
      IF sy-batch IS INITIAL.
        PERFORM popup_format_parameters.
        IF sscrfields-ucomm EQ 'FORM'.
          CLEAR sscrfields-ucomm.
        ENDIF.
      ELSE.
        STOP.
      ENDIF.
    ENDIF.

  ENDIF.


* Check the existence of entered layout sets
AT SELECTION-SCREEN ON par_fpy1.
  PERFORM check_form USING par_fpy1.

AT SELECTION-SCREEN ON par_pdf1.
  CALL FUNCTION 'PDF_FORM_CHECK'
    EXPORTING
      i_formname = par_pdf1.

AT SELECTION-SCREEN ON par_fpy3.
  PERFORM check_form USING par_fpy3.

AT SELECTION-SCREEN ON par_pdf3.
  CALL FUNCTION 'PDF_FORM_CHECK'
    EXPORTING
      i_formname = par_pdf3.

*- User commands ------------------------------------------------------*
AT SELECTION-SCREEN.

  CASE sscrfields-ucomm.

*   Format documentation
    WHEN 'INFO'.
      CALL FUNCTION 'FI_PAYM_FORMAT_DOCUMENTATION'
           EXPORTING
                i_formi = par_form.

*   Format parameters
    WHEN 'FORM'.
      PERFORM popup_format_parameters.

*   Print parameters for the error list
    WHEN 'PRIE'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                i_title_text         = text-013
           CHANGING
                c_pri_params         = par_prie
                c_arc_params         = par_arce
           EXCEPTIONS
                parameters_not_valid = 1
                OTHERS               = 2.

*  Print parameters for the accompanying list
    WHEN 'PRIL'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                i_title_text         = text-012
           CHANGING
                c_pri_params         = par_pril
                c_arc_params         = par_arcl
           EXCEPTIONS
                parameters_not_valid = 1
                OTHERS               = 2.

*   Print parameters for the payment medium 1
    WHEN 'PRI1'.
      CALL FUNCTION 'MAINTAIN_TEXT_PRINT_PARAMETERS'
           EXPORTING
                i_title_text         = text_py1
           CHANGING
                c_itcpo              = par_pri1
           EXCEPTIONS
                parameters_not_valid = 1
                OTHERS               = 2.

*   Print parameters for the payment medium 3
    WHEN 'PRI3'.
      CALL FUNCTION 'MAINTAIN_TEXT_PRINT_PARAMETERS'
           EXPORTING
                i_title_text         = gc_text_py3
           CHANGING
                c_itcpo              = par_pri3
           EXCEPTIONS
                parameters_not_valid = 1
                OTHERS               = 2.

*   Additional payment medium list
    WHEN 'PRI5'.
      CALL FUNCTION 'MAINTAIN_PRINT_PARAMETERS'
           EXPORTING
                i_title_text         = text_py5
           CHANGING
                c_pri_params         = par_pri5
                c_arc_params         = par_arc5
           EXCEPTIONS
                parameters_not_valid = 1
                OTHERS               = 2.

*   Display SAPscript payment medium form 1
    WHEN 'SCR1'.
      PERFORM display_form USING par_fpy1.

*   Display SAPscript payment medium form 3
    WHEN 'SCR3'.
      PERFORM display_form USING par_fpy3.

    WHEN 'FORM_TYPE_CHANGED'.
      IF NOT par_pdf3 IS INITIAL OR NOT par_fpy3 IS INITIAL.
        MESSAGE s168 DISPLAY LIKE 'W'.
      ENDIF.

  ENDCASE.

* two options for accompanying list: printer or screen output
  IF par_scrn IS INITIAL AND NOT par_xlst IS INITIAL.
    CALL FUNCTION 'CHECK_PRINT_PARAMETERS'
         EXPORTING
              i_title_text = text-012
              i_pri_params = par_pril
              i_arc_params = par_arcl
         IMPORTING
              e_pri_params = gs_pril
              e_arc_params = gs_arcl.
* delete by note 1763901
*    IF gs_pril-pdest IS INITIAL.
*      MESSAGE s615.
*      CLEAR sscrfields-ucomm.
*    ENDIF.

* insert by note 1763901
     IF gs_pril-pdest IS INITIAL.
       IF sy-batch is initial. " note 1763901
         MESSAGE s615.
         CLEAR sscrfields-ucomm.
       ELSE.
         MESSAGE S065 WITH 'Report' sy-cprog sy-slset ':'.
         MESSAGE S615.
*        no clear on sscrfields-ucomm, we continue, see note 1763901
       ENDIF.
    ENDIF.
* end insert
  ENDIF.

AT SELECTION-SCREEN ON HELP-REQUEST FOR par_pdf1.
  CALL FUNCTION 'FI_DOCUMENTATION_SHOW'
    EXPORTING
      ic_fname          = 'FORDZFOR'
      ic_dokclass       = 'DE'.

AT SELECTION-SCREEN ON HELP-REQUEST FOR par_pdf3.
  CALL FUNCTION 'FI_DOCUMENTATION_SHOW'
    EXPORTING
      ic_fname          = 'FORDZFOR'
      ic_dokclass       = 'DE'.
AT selection-SCREEN ON par_file.  " note 1511617
IF par_file IS NOT INITIAL AND par_xfil IS NOT INITIAL.
    DATA ld_filename(255) TYPE C.
    ld_filename = par_file.
    CALL FUNCTION 'FILE_VALIDATE_NAME'
    EXPORTING
      logical_filename  = 'FI_DME_CREATE_FILE'
      parameter_1       = sy-cprog
    CHANGING
      physical_filename = ld_filename
    EXCEPTIONS
      validation_failed          = 1
      logical_filename_not_found = 2
      others                     = 3.
* in case no exception is thrown, we keep the original filename
    IF sy-subrc <> 0.
      MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
      WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    ENDIF.
  ENDIF.