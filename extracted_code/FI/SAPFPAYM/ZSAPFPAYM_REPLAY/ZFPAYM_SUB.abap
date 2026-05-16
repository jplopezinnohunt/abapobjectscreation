************************************************************************
* Include FPAYM_SUB
* Subroutines
************************************************************************

*----------------------------------------------------------------------*
* Form ADJUST_PARAMETERS_TO_FORMAT
* Adjust selection parameters to payment medium format porperties
*----------------------------------------------------------------------*
FORM adjust_parameters_to_format.

* Initialize print parameters
  IF gs_tfpm042f-xpri1 IS INITIAL.
    CLEAR: par_xpy1,
           par_pri1,
           par_fpy1,
           par_pdf1.
  ENDIF.
  IF gs_tfpm042f-xdme1 IS INITIAL.
    CLEAR: par_xpy3,
           par_pri3,
           par_ftyp,
           par_fpy3,
           par_pdf3,
           par_file,
           par_xfil.
  ENDIF.
  IF gs_tfpm042f-xlst1 IS INITIAL.
    CLEAR: par_xpy5,
           par_pri5,
           par_arc5.
  ENDIF.
* Assign text for check boxes
  PERFORM fill_parameter_text
          USING: gs_tfpm042ft-pri1x text-010 text_py1,
                 gs_tfpm042ft-dme1x text-015 text_py3,
                 gs_tfpm042ft-lst1x text-010 text_py5.

  CONCATENATE: text-009 text_py1 INTO text_fp1    SEPARATED BY space,
               text-014 text_py3 INTO gc_text_py3 SEPARATED BY space.

  txt_pdf1 = text_fp1.

ENDFORM.                               "ADJUST_PARAMETERS_TO_FORMAT


*----------------------------------------------------------------------*
* Form FILL_PARAMETER_TEXT
* Fills Text with imported text or imported alternative text
*----------------------------------------------------------------------*
* --> I_TEXT        Text from payment format attributes
* --> I_TEXT_SUB    Alternative text from payment format attributes
* <-- E_PAR_TEXT    Text to be output
*----------------------------------------------------------------------*
FORM fill_parameter_text USING i_text     TYPE c
                               i_text_sub TYPE c
                               e_par_text TYPE c.

  IF NOT i_text IS INITIAL.
    e_par_text = i_text.
  ELSE.
    e_par_text = i_text_sub.
  ENDIF.

ENDFORM.                               "FILL_PARAMETER_TEXT


*----------------------------------------------------------------------*
* Form CHECK_FORMAT_PARAMETERS
* Check, whether there are format parameters, customer format
* parameters and all obligatory fields of them and set icon for
* format parameters (white or green)
*----------------------------------------------------------------------*
FORM check_format_parameters.

  DATA: lt_sapobli   LIKE fpm_obli OCCURS 0 WITH HEADER LINE,
        lt_cusobli   LIKE fpm_obli OCCURS 0 WITH HEADER LINE,
        lc_xinitial  LIKE boole-boole VALUE 'X',
        lc_xentries  LIKE boole-boole.

* There are format parameters
  IF NOT gs_tfpm042ff-formf IS INITIAL.
*   Format parameters are initial
    IF par_forp IS INITIAL.
      CLEAR gc_xforp.
*   There are format parameter values
    ELSE.
*     Get obligatory fields of format parameters
      LOOP AT gt_tfpm042fm.
        MOVE-CORRESPONDING gt_tfpm042fm TO lt_sapobli.
        APPEND lt_sapobli.
      ENDLOOP.
*     Check format parameters and obligatory fields
      CALL FUNCTION 'CHECK_STRUCTURE_FIELDS'
           EXPORTING
                i_tabname       = gs_tfpm042ff-formf
           IMPORTING
                e_initial       = lc_xinitial
                e_fields_filled = gc_xforp
           TABLES
                t_obli          = lt_sapobli
           CHANGING
                c_workarea      = par_forp.
    ENDIF.
  ENDIF.

* There are no format parameters but customer format parameters
  IF gc_xforp IS INITIAL AND
     NOT gs_tfpm042ffc-formf IS INITIAL AND
     NOT par_fopc IS INITIAL.
*   Get obligatory customer fields of format parameters
    LOOP AT gt_tfpm042fmc.
      MOVE-CORRESPONDING gt_tfpm042fmc TO lt_cusobli.
      APPEND lt_cusobli.
    ENDLOOP.
*   Check customer format parameters and obligatory fields
    CALL FUNCTION 'CHECK_STRUCTURE_FIELDS'
         EXPORTING
              i_tabname       = gs_tfpm042ffc-formf
         IMPORTING
              e_initial       = lc_xinitial
              e_fields_filled = gc_xforp
         TABLES
              t_obli          = lt_cusobli
         CHANGING
              c_workarea      = par_fopc.
  ENDIF.


* Fill icons for format parameters (white or green)
  IF lc_xinitial IS INITIAL.
    lc_xentries = 'X'.
  ENDIF.
  CALL FUNCTION 'SET_ARROW_ICON'
       EXPORTING
            i_parameter  = lc_xentries
            i_icon_text  = text-006
       IMPORTING
            e_arrow_icon = fbutton.

ENDFORM.                               "CHECK_FORMAT_PARAMETERS


*----------------------------------------------------------------------*
* Form POPUP_FORMAT_PARAMETERS
* Displays one popup for the maintenance of payment medium format
* parameters and customers payment medium format parameters which
* declared in DDIC structures
*----------------------------------------------------------------------*
FORM popup_format_parameters.

  DATA: lt_sapobli   LIKE fpm_obli OCCURS 0 WITH HEADER LINE,
        lt_cusobli   LIKE fpm_obli OCCURS 0 WITH HEADER LINE,
        lc_xinitial  LIKE boole-boole,
        lc_xsapentry LIKE boole-boole,
        lc_xcusentry LIKE boole-boole,
        lc_sapfunct  LIKE tfpm042fb-fname,
        lc_cusfunct  LIKE tfpm042fbc-fname,
        lc_text      LIKE rsmpe-tittext,
        lc_sappar    LIKE fpm_selpar-param,
        lc_cuspar    LIKE fpm_selpar-param.

* Check whether there are obligatory fields in the format parameters
  IF NOT gs_tfpm042ff-formf IS INITIAL OR
     NOT gs_tfpm042ffc-formf IS INITIAL.

*   Delete the formatparameters if the corresponding structure is
*   initial
    IF gs_tfpm042ff-formf IS INITIAL.
      CLEAR par_forp.
    ENDIF.
    IF gs_tfpm042ffc-formf IS INITIAL.
      CLEAR par_fopc.
    ENDIF.
*   Get obligatory fields of format parameters
    LOOP AT gt_tfpm042fm.
      MOVE-CORRESPONDING gt_tfpm042fm TO lt_sapobli.
      APPEND lt_sapobli.
    ENDLOOP.
*   Get obligatory customer fields of format parameters
    LOOP AT gt_tfpm042fmc.
      MOVE-CORRESPONDING gt_tfpm042fmc TO lt_cusobli.
      APPEND lt_cusobli.
    ENDLOOP.
*   Get check functions for the format parameters
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_EVENTS'
         EXPORTING
              i_formi         = gs_tfpm042f-formi
              i_event         = 10
         IMPORTING
              e_eventfunction = lc_sapfunct
         EXCEPTIONS
              OTHERS          = 1.
    CALL FUNCTION 'FI_PAYM_FORMAT_READ_EVENTS'
         EXPORTING
              i_formi         = gs_tfpm042f-formi
              i_event         = 11
         IMPORTING
              e_eventfunction = lc_cusfunct
         EXCEPTIONS
              OTHERS          = 1.
*   Call Popup for format parameters
    lc_text = text-020.
    REPLACE '&format' WITH gs_tfpm042f-formi INTO lc_text.
    lc_sappar = par_forp.
    lc_cuspar = par_fopc.
    CALL FUNCTION 'DIC2DYN'
         EXPORTING
              i_saptabname   = gs_tfpm042ff-formf
              i_custabname   = gs_tfpm042ffc-formf
              i_sapcheckfunc = lc_sapfunct
              i_cuscheckfunc = lc_cusfunct
              i_tittext      = lc_text
         IMPORTING
              e_xsapentry    = lc_xsapentry
              e_xcusentry    = lc_xcusentry
         TABLES
              t_sapobli      = lt_sapobli
              t_cusobli      = lt_cusobli
         CHANGING
              c_sapentries   = lc_sappar
              c_cusentries   = lc_cuspar.
    IF NOT lc_xsapentry IS INITIAL OR
       NOT lc_xcusentry IS INITIAL.
      gc_xforp = 'X'.
      par_forp = lc_sappar.
      par_fopc = lc_cuspar.
    ELSE.
      CLEAR: sscrfields-ucomm.
    ENDIF.
  ENDIF.

ENDFORM.                               "POPUP_FORMAT_PARAMETERS


*----------------------------------------------------------------------*
* Form CHECK_FORM
* Checks the existence of a form layout set
*----------------------------------------------------------------------*
* --> I_FORM        Layout set to be checked
*----------------------------------------------------------------------*
FORM check_form USING i_form LIKE fpm_selpar-altform.

  CHECK i_form NE space.
  CALL FUNCTION 'FORM_CHECK'
       EXPORTING
            i_pzfor = i_form
       EXCEPTIONS
            OTHERS  = 4.
  CHECK sy-subrc NE 0.
  MESSAGE ID sy-msgid TYPE 'W' NUMBER sy-msgno
          WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.

ENDFORM.                                                    "CHECK_FORM


*----------------------------------------------------------------------*
* Form DISPLAY_FORM
* Maintain / Display  form layout set
*----------------------------------------------------------------------*
* --> I_FORM        Name of layout set to be displayed
*----------------------------------------------------------------------*
FORM display_form USING i_form LIKE fpm_selpar-altform.

  CHECK NOT i_form IS INITIAL.
  CALL FUNCTION 'EDIT_FORM'
       EXPORTING
            form    = i_form
            display = 'X'.

ENDFORM.                               "DISPLAY_FORM


*----------------------------------------------------------------------*
* Form FILL_SCREEN                                                     *
* Set screen fields inactive                                           *
*----------------------------------------------------------------------*
* --> I_GROUP      Screen group to be modified                        *
* --> I_ACTIVE     Parameter active                                   *
*----------------------------------------------------------------------*
FORM fill_screen USING i_group TYPE c
                       i_active.

  IF screen-group1 EQ i_group AND i_active IS INITIAL.
    screen-active = '0'.
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
FORM output_start_message.

  IF NOT gs_dfpayg-zbukr IS INITIAL.
    CONCATENATE text-030 gs_dfpayg-zbukr INTO gc_message_text1
      SEPARATED BY space.
    CONDENSE gc_message_text1.
    IF NOT gs_dfpayg-hbkid IS INITIAL.
      IF gs_dfpayg-hktid IS INITIAL.
        CONCATENATE text-031 gs_dfpayg-hbkid INTO gc_message_text2
          SEPARATED BY space.
      ELSE.
        CONCATENATE text-032 gs_dfpayg-hbkid gs_dfpayg-hktid
          INTO gc_message_text2 SEPARATED BY space.
      ENDIF.
      CONDENSE gc_message_text2.
    ENDIF.
  ENDIF.

  IF NOT gs_dfpayg-banks IS INITIAL.
    CONCATENATE text-031 gs_dfpayg-banks gs_dfpayg-bankl INTO
      gc_message_text2 SEPARATED BY space.
    CONDENSE gc_message_text2.
  ENDIF.

  IF NOT gs_dfpayg-rzawe IS INITIAL.
    CONCATENATE text-034  gs_dfpayg-rzawe INTO
      gc_message_text3 SEPARATED BY space.
    CONDENSE gc_message_text3.
  ELSEIF gs_dfpayg-crdeb EQ '1'.
    gc_message_text3 = text-035.
  ELSEIF gs_dfpayg-crdeb EQ '2'.
    gc_message_text3 = text-036.
  ENDIF.

  TRY.                                                   "begin n2669849
    IF NOT sy-batch IS INITIAL.
      CALL FUNCTION 'FI_PAYM_FORMAT_OBSOLETE_CHECK'
        EXPORTING
          i_formi            = par_form
        EXCEPTIONS
          format_is_obsolete = 0.
    ENDIF.
    CATCH cx_root.
  ENDTRY.                                                  "end n2669849

  MESSAGE s222 WITH par_form gc_message_text1
            gc_message_text2 gc_message_text3.

ENDFORM.                               " output_start_message


*&---------------------------------------------------------------------*
*&      Form  hr_remittance_acknowledgement
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_FPAYP  text
*----------------------------------------------------------------------*
FORM hr_remittance_acknowledgement USING is_fpayh LIKE fpayh
                                         is_fpayp LIKE fpayp.

  DATA: l_xblnr     LIKE hrxblnr,
        l_lifnr     TYPE lifnr,
        l_awsys     TYPE awsys,
        l_dest      TYPE rfcdest,
        l_text(100) TYPE c.
*** begin note 1130975
  DATA: l_remsn_exist TYPE xfeld.   "Indicator REMSN exists
  DATA: l_iv_duedt_exist TYPE xfeld. "Indicator IV_DUEDT exists

  DATA: dref_xblnr TYPE REF TO data.  "N2307673
  FIELD-SYMBOLS: <xblnr>.             "N2307673

  DATA: l_remsn TYPE remsn,
        l_zfbdt like regup-zfbdt.
  DATA: l_import_tab TYPE STANDARD TABLE OF rsimp WITH HEADER
      LINE,
               l_export_tab       TYPE STANDARD TABLE OF rsexp,
               l_tables_tab       TYPE STANDARD TABLE OF rstbl,
               l_exceptions_tab   TYPE STANDARD TABLE OF rsexc.
  clear: l_remsn, l_zfbdt, l_remsn_exist, l_iv_duedt_exist.
*** end note 1130975
* check that payment is 3rd party remittance
  l_xblnr = is_fpayp-xblnr.
  CHECK:
    is_fpayh-gpa1t EQ '11' AND         "vendor
    is_fpayp-doc2t EQ '01' AND         "FI document
    is_fpayp-xvorl EQ space.           "no proposal run
  CHECK:
    l_xblnr-txtsl  EQ 'HR',
    l_xblnr-txerg  EQ 'GRN' AND l_xblnr-xhrfo EQ 'X' OR
    l_xblnr-txerg  EQ space AND l_xblnr-xhrfo EQ space.
*    l_xblnr-remsn  NE 0.
*    With extension of remsn from 5 to 10,
*    hrxblnr-remsn will always be zeros for the new posting numbers.
*    The data prior to the extension will not have zeros in the field.
*    So, removed the check.

* get vendor number
  CALL FUNCTION 'FI_REF_PARTNER_INTERPRET'
       EXPORTING
            im_gpa1t = is_fpayh-gpa1t
            im_gpa1r = is_fpayh-gpa1r
            im_gpa2t = is_fpayp-gpa2t
            im_gpa2r = is_fpayp-gpa2r
       IMPORTING
            ex_lifnr = l_lifnr.

* get rfc destination
  g_function = 'READ_DOC2R_DESTINATION'.
  CALL FUNCTION g_function
       EXPORTING
            i_doc2t        = is_fpayp-doc2t
            i_doc2r        = is_fpayp-doc2r
       IMPORTING
            e_awsys        = l_awsys
            e_rfcdest      = l_dest
       EXCEPTIONS
            no_remote_call = 1
            OTHERS         = 2.

  CASE sy-subrc.
    WHEN 0.    "means distributed.
      g_function = 'RP_REMITTANCE_ACKNOWLEDGEMENT'.
*** check if func exists.
     CALL FUNCTION 'FUNCTION_EXISTS'
        DESTINATION l_dest
        EXPORTING
          funcname           = g_function
        EXCEPTIONS
          function_not_exist = 1
          OTHERS             = 2.
*** func exists, take its interface data.
      IF sy-subrc = 0.             " Function exists
        CALL FUNCTION 'FUNCTION_IMPORT_INTERFACE'
          DESTINATION l_dest
          EXPORTING
            funcname           = g_function
            inactive_version   = ' '
          TABLES
            exception_list     = l_exceptions_tab
            export_parameter   = l_export_tab
            import_parameter   = l_import_tab
            tables_parameter   = l_tables_tab
          EXCEPTIONS
            error_message      = 1
            function_not_found = 2
            invalid_name       = 3
            OTHERS             = 4.

        IF sy-subrc <> 0.          "Function not found
          MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
           WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
*** Func found so check its import parameters.
        ELSE.
          READ TABLE l_import_tab WITH KEY parameter = 'IV_DUEDT'.
            IF sy-subrc = 0.
              l_iv_duedt_exist = 'X'.
            ENDIF.
          READ TABLE l_import_tab WITH KEY parameter = 'REMSN'.
          IF sy-subrc = 0.
            l_remsn_exist = 'X'.
          ENDIF.

      READ TABLE l_import_tab                        "N2307673
        WITH KEY parameter = 'XBLNR'.                "N2307673

      CREATE DATA dref_xblnr TYPE (l_import_tab-typ). "N2307673

      IF sy-subrc = 0.                                "N2307673
        ASSIGN dref_xblnr->* TO <xblnr>.              "N2307673
      ENDIF.                                          "N2307673
      IF NOT <xblnr> IS ASSIGNED.                     "N2307673
        ASSIGN is_fpayp-xblnr TO <xblnr>.             "N2307673
      ENDIF.                                          "N2307673

      <xblnr> = is_fpayp-xblnr.                       "N2307673

          if l_iv_duedt_exist = 'X' and l_remsn_exist = 'X'.
            IF is_fpayp-sgtxt+0(5) EQ '00000'. "means new posting run number
              l_remsn = is_fpayp-sgtxt+5(10).
            ELSE.
              l_remsn = is_fpayp-sgtxt+0(5).
            ENDIF.

*** determine iv_duedt
            select single zfbdt into l_zfbdt
                  from regup
                       where laufd = is_fpayp-laufd and
                             laufi = is_fpayp-laufi and
                             xvorl = is_fpayp-xvorl and
                             bukrs = is_fpayp-bukrs and
                             lifnr = l_lifnr        and
                             belnr = is_fpayp-doc2r+4(10) and
                             xblnr = is_fpayp-xblnr.

      CALL FUNCTION g_function
           DESTINATION
                l_dest
           EXPORTING
                laufd                 = is_fpayp-laufd
                laufi                 = is_fpayp-laufi
                bukrs                 = is_fpayp-bukrs
                lifnr                 = l_lifnr
*                xblnr                 = is_fpayp-xblnr  "N2307673
                xblnr                 = <xblnr>          "N2307673
                zfbdt                 = l_zfbdt
                remsn                 = l_remsn
           EXCEPTIONS
                communication_failure = 4 MESSAGE l_text
                system_failure        = 4 MESSAGE l_text
                OTHERS                = 0.
           ENDIF.   "if both fields exist

      if l_iv_duedt_exist IS INITIAL and l_remsn_exist IS INITIAL.
            CALL FUNCTION g_function
              DESTINATION l_dest
              EXPORTING
                laufd                 = is_fpayp-laufd
                laufi                 = is_fpayp-laufi
                bukrs                 = is_fpayp-bukrs
                lifnr                 = l_lifnr
*                xblnr                 = is_fpayp-xblnr  "N2307673
                xblnr                 = <xblnr>          "N2307673
              EXCEPTIONS
                communication_failure = 4  MESSAGE l_text
                system_failure        = 4  MESSAGE l_text
                OTHERS                = 0.
          ENDIF.  "none of the fields exist.

          IF l_iv_duedt_exist = 'X' AND l_remsn_exist IS INITIAL.
*** determine iv_duedt
            select single zfbdt into l_zfbdt
                  from regup
                       where laufd = is_fpayp-laufd and
                             laufi = is_fpayp-laufi and
                             xvorl = is_fpayp-xvorl and
                             bukrs = is_fpayp-bukrs and
                             lifnr = l_lifnr        and
                             belnr = is_fpayp-doc2r+4(10) and
                             xblnr = is_fpayp-xblnr.

            CALL FUNCTION g_function
                    DESTINATION    l_dest
            EXPORTING
             laufd                 = is_fpayp-laufd
             laufi                 = is_fpayp-laufi
             bukrs                 = is_fpayp-bukrs
             lifnr                 = l_lifnr
*            xblnr                 = is_fpayp-xblnr  "N2307673
             xblnr                 = <xblnr>         "N2307673
             iv_duedt              = l_zfbdt
            EXCEPTIONS
             communication_failure = 4 MESSAGE l_text
             system_failure        = 4 MESSAGE l_text
             OTHERS                = 0.
          ENDIF. "if iv_duedt exists but remsn does not

          IF l_remsn_exist = 'X' AND l_iv_duedt_exist IS INITIAL.
            IF is_fpayp-sgtxt+0(5) EQ '00000'. "means new posting run number
              l_remsn = is_fpayp-sgtxt+5(10).
            ELSE.
              l_remsn = is_fpayp-sgtxt+0(5).
            ENDIF.
            CALL FUNCTION g_function
              DESTINATION l_dest
              EXPORTING
                laufd                 = is_fpayp-laufd
                laufi                 = is_fpayp-laufi
                bukrs                 = is_fpayp-bukrs
                lifnr                 = l_lifnr
*                xblnr                 = is_fpayp-xblnr  "N2307673
                xblnr                 = <xblnr>          "N2307673
                remsn                 = l_remsn
              EXCEPTIONS
                communication_failure = 4 MESSAGE l_text
                system_failure        = 4 MESSAGE l_text
                OTHERS                = 0.
          ENDIF. "if remsn exists but l_due_date does not

        ENDIF.   "if func found by import_interface
      ENDIF.  "func exists take its interface data

      IF sy-subrc NE 0.
        IF sy-batch EQ space.
          MESSAGE i265(bfibl02) WITH l_awsys
                                     l_dest
                                     is_fpayp-bukrs
                                     is_fpayp-doc2r.
          MESSAGE i266(bfibl02) WITH l_text l_text+50.
          MESSAGE i267(bfibl02) WITH is_fpayh-doc1r.
        ELSE.
          MESSAGE s265(bfibl02) WITH l_awsys
                                     l_dest
                                     is_fpayp-bukrs
                                     is_fpayp-doc2r.
          MESSAGE s266(bfibl02) WITH l_text l_text+50.
          MESSAGE s267(bfibl02) WITH is_fpayh-doc1r.
        ENDIF.
      ENDIF.
    WHEN 1.    "means not distributed
      g_function = 'RP_REMITTANCE_ACKNOWLEDGEMENT'.
*** check if func exists.
      CALL FUNCTION 'FUNCTION_EXISTS'
        EXPORTING
          funcname           = g_function
        EXCEPTIONS
          function_not_exist = 1
          OTHERS             = 2.
*** func exists, take its interface data.
      IF sy-subrc = 0.             " Function exists
        CALL FUNCTION 'FUNCTION_IMPORT_INTERFACE'
          EXPORTING
            funcname           = g_function
            inactive_version   = ' '
          TABLES
            exception_list     = l_exceptions_tab
            export_parameter   = l_export_tab
            import_parameter   = l_import_tab
            tables_parameter   = l_tables_tab
          EXCEPTIONS
            error_message      = 1
            function_not_found = 2
            invalid_name       = 3
            OTHERS             = 4.

        IF sy-subrc <> 0.          "Function not found
          MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
           WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
*** Func found so check its import parameters.
        ELSE.
          READ TABLE l_import_tab WITH KEY parameter = 'IV_DUEDT'.
            IF sy-subrc = 0.
              l_iv_duedt_exist = 'X'.
            ENDIF.

          READ TABLE l_import_tab WITH KEY parameter = 'REMSN'.
          IF sy-subrc = 0.
            l_remsn_exist = 'X'.
          ENDIF.

      READ TABLE l_import_tab                        "N2307673
        WITH KEY parameter = 'XBLNR'.                "N2307673

      CREATE DATA dref_xblnr TYPE (l_import_tab-typ). "N2307673

      IF sy-subrc = 0.                                "N2307673
        ASSIGN dref_xblnr->* TO <xblnr>.              "N2307673
      ENDIF.                                          "N2307673
      IF NOT <xblnr> IS ASSIGNED.                     "N2307673
        ASSIGN is_fpayp-xblnr TO <xblnr>.             "N2307673
      ENDIF.                                          "N2307673

      <xblnr> = is_fpayp-xblnr.                       "N2307673

        if l_iv_duedt_exist = 'X' and l_remsn_exist = 'X'.
            IF is_fpayp-sgtxt+0(5) EQ '00000'. "means new posting run number
              l_remsn = is_fpayp-sgtxt+5(10).
            ELSE.
              l_remsn = is_fpayp-sgtxt+0(5).
            ENDIF.
*** determine iv_duedt
            select single zfbdt into l_zfbdt
                  from regup
                       where laufd = is_fpayp-laufd and
                             laufi = is_fpayp-laufi and
                             xvorl = is_fpayp-xvorl and
                             bukrs = is_fpayp-bukrs and
                             lifnr = l_lifnr        and
                             belnr = is_fpayp-doc2r+4(10) and
                             xblnr = is_fpayp-xblnr.

            CALL FUNCTION g_function
               EXPORTING
                laufd  = is_fpayp-laufd
                laufi  = is_fpayp-laufi
                bukrs  = is_fpayp-bukrs
                lifnr  = l_lifnr
*                xblnr  = is_fpayp-xblnr    "N2307673
                xblnr    = <xblnr>          "N2307673
                zfbdt  = l_zfbdt
                remsn  = l_remsn
           EXCEPTIONS
                OTHERS = 0.
         ENDIF.   "if both fields exist

         if l_iv_duedt_exist IS INITIAL and l_remsn_exist IS INITIAL.
            CALL FUNCTION g_function
              EXPORTING
                laufd                 = is_fpayp-laufd
                laufi                 = is_fpayp-laufi
                bukrs                 = is_fpayp-bukrs
                lifnr                 = l_lifnr
*               xblnr                 = is_fpayp-xblnr   "N2307673
                xblnr                 = <xblnr>          "N2307673
              EXCEPTIONS
                OTHERS                = 0.
          ENDIF.  "neither fields exist.

          IF l_iv_duedt_exist = 'X' AND l_remsn_exist IS INITIAL.
*** determine iv_duedt
            select single zfbdt into l_zfbdt
                  from regup
                       where laufd = is_fpayp-laufd and
                             laufi = is_fpayp-laufi and
                             xvorl = is_fpayp-xvorl and
                             bukrs = is_fpayp-bukrs and
                             lifnr = l_lifnr        and
                             belnr = is_fpayp-doc2r+4(10) and
                             xblnr = is_fpayp-xblnr.

            CALL FUNCTION g_function
             EXPORTING
             laufd                 = is_fpayp-laufd
             laufi                 = is_fpayp-laufi
             bukrs                 = is_fpayp-bukrs
             lifnr                 = l_lifnr
*             xblnr                 = is_fpayp-xblnr  "N2307673
             xblnr                 = <xblnr>          "N2307673
             iv_duedt              = l_zfbdt
            EXCEPTIONS
             OTHERS                = 0.
          ENDIF. "if iv_duedt exists but remsn does not

          IF l_remsn_exist = 'X' AND l_iv_duedt_exist IS INITIAL.
            IF is_fpayp-sgtxt+0(5) EQ '00000'. "means new posting run number
              l_remsn = is_fpayp-sgtxt+5(10).
            ELSE.
              l_remsn = is_fpayp-sgtxt+0(5).
            ENDIF.
      CALL FUNCTION g_function
           EXPORTING
                laufd  = is_fpayp-laufd
                laufi  = is_fpayp-laufi
                bukrs  = is_fpayp-bukrs
                lifnr  = l_lifnr
*                xblnr  = is_fpayp-xblnr  "N2307673
                xblnr   = <xblnr>          "N2307673
                remsn                 = l_remsn
              EXCEPTIONS
                OTHERS                = 0.
          ENDIF. "if remsn exists but l_due_date does not

         ENDIF.   "if func found by import_interface
      ENDIF.  "func exists take its interface data

    WHEN 2.
      MESSAGE ID sy-msgid TYPE 'E' NUMBER sy-msgno
              WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDCASE.


ENDFORM.                               " hr_remittance_acknowledgement


*----------------------------------------------------------------------*
* Form WAIT_FOR_VALIDATION
* If payment document validation is active (PAR_BELP) and if payment
* media creation was scheduled together with FI payment run (PAR_F11S)
* then the system shall wait until the number of payments is equal to
* the number of posted documents to enable payment document validation
*----------------------------------------------------------------------*
FORM wait_for_validation                                       "n1922823
  USING i_laufd TYPE laufd
        i_laufi TYPE laufi
        i_xvorl TYPE xvorl.

  DATA:
    l_msgty     TYPE msgts,
    l_seconds_c TYPE char10,
    l_seconds_n TYPE numc10,
    l_seconds   TYPE i,
    ls_reguv    TYPE reguv.

  CHECK i_xvorl IS INITIAL.      "no validation for proposal runs

  CHECK i_laufi+5(1) EQ space    "waiting only supported for FI payment
     OR i_laufi+5(1) EQ 'R'.     "programs F110 or F111

* check customized message for situation that postings are missing:
* W - wait and continue after wait time (with message in log)
* E - wait and stop after wait time
  CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
    EXPORTING
      i_arbgb = 'BFIBL02'
      i_dtype = 'W'
      i_msgnr = '169'
   IMPORTING
      e_msgty = l_msgty.
  CHECK l_msgty NE '-'.          "message switched off -> old behavior

* get wait time (60 seconds default)
  GET PARAMETER ID 'FIBL_VALIDATION_WAIT' FIELD l_seconds_c.
  l_seconds_n = l_seconds_c.     "eliminate non-numeric characters
  IF l_seconds_n IS INITIAL.
    l_seconds = 60.
  ELSE.
    l_seconds = l_seconds_n.
  ENDIF.

* check that all postings are finished
  DO l_seconds TIMES.
    SELECT SINGLE * FROM reguv INTO ls_reguv
      WHERE laufd EQ i_laufd
      AND   laufi eq i_laufi.
    IF ls_reguv-anzer EQ ls_reguv-anzgb.
      EXIT.
    ENDIF.
    WAIT UP TO 1 SECONDS.
  ENDDO.

* if not finished after wait time, raise message
  IF ls_reguv-anzer NE ls_reguv-anzgb.
    IF sy-batch IS INITIAL.
      IF l_msgty EQ 'E'.
        MESSAGE e169 WITH l_seconds.
      ELSE.
        MESSAGE i169 WITH l_seconds.
      ENDIF.
    ELSE.
      MESSAGE s169 WITH l_seconds.
      IF l_msgty EQ 'E'.
        STOP.
      ENDIF.
    ENDIF.
  ENDIF.

ENDFORM.                                                       "n1922823

* begin 2573070
FORM check_message_stop_creation CHANGING c_stop_creation TYPE C.

* also called out of RBNK_PAYM_GRP_N_BATCH
  c_stop_creation = space.
  DATA lt_fimsg TYPE fimsg OCCURS 0 WITH HEADER LINE.
  CALL FUNCTION 'FI_MESSAGE_GET'
  TABLES
    t_fimsg = lt_fimsg
  EXCEPTIONS
    no_message = 1
    OTHERS     = 2.
  LOOP AT lt_fimsg WHERE msgid = 'F0' AND msgno = 800 AND msgty = 'A'.
    c_stop_creation = 'X'.
  ENDLOOP.
ENDFORM.
* end 2573070