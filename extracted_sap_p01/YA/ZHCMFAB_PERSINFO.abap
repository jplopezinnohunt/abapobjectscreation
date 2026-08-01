* ==== CLASS POOL ZHCMFAB_PERSINFO ====
CLASS-POOL .
*"* class pool for class ZHCMFAB_PERSINFO

*"* local type definitions
INCLUDE ZHCMFAB_PERSINFO==============CCDEF.

*"* class ZHCMFAB_PERSINFO definition
*"* public declarations
  INCLUDE ZHCMFAB_PERSINFO==============CU.
*"* protected declarations
  INCLUDE ZHCMFAB_PERSINFO==============CO.
*"* private declarations
  INCLUDE ZHCMFAB_PERSINFO==============CI.
ENDCLASS. "ZHCMFAB_PERSINFO definition

*"* macro definitions
INCLUDE ZHCMFAB_PERSINFO==============CCMAC.
*"* local class implementation
INCLUDE ZHCMFAB_PERSINFO==============CCIMP.

CLASS ZHCMFAB_PERSINFO IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZHCMFAB_PERSINFO implementation


* ---- ZHCMFAB_PERSINFO==============CI ----
  PRIVATE SECTION.

* ---- ZHCMFAB_PERSINFO==============CM001 ----
  METHOD IF_EX_HCMFAB_PERSINFO_CONFIG~GET_DPC_INSTANCE.

    " This method provides the Data Provider Class (DPC) for your application.
    IF IV_APP_ID = IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYPERSONALDATA.
      " CORRECTED: Using the exact 'io_context' parameter name for the class constructor.
      CO_DPC_INSTANCE = NEW CL_HCMFAB_MYPERSONALDA_DPC_GEN(
                              IO_CONTEXT = IO_CONTEXT ).
    ENDIF.

* DATA lo_dpc_instance TYPE if_ex_hcmfab_persinfo_config=>ty_s_dpc_instance.
*
*  READ TABLE gt_dpc_instance WITH KEY app_id = iv_app_id INTO lo_dpc_instance.
*  IF sy-subrc NE 0 OR NOT lo_dpc_instance-dpc_instance IS BOUND.
*    lo_dpc_instance-app_id = iv_app_id.
*    CASE iv_app_id.
*      WHEN if_hcmfab_constants=>gc_application_id-myaddresses.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_myaddresses_dpc_gen
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mybankdetails.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_mybankdetail_dpc_gen
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mycommunication.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_mycommunicat_dpc_gen
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-myinternaldata.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_myinternalda_dpc_gen
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-myfamilymembers.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_myfamilymemb_dpc_un
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mypersonaldata.
*        CREATE OBJECT lo_dpc_instance-dpc_instance TYPE cl_hcmfab_mypersonalda_dpc_gen
*          EXPORTING
*            io_context = io_context.
*        APPEND lo_dpc_instance TO gt_dpc_instance.
*        co_dpc_instance = lo_dpc_instance-dpc_instance.
*    ENDCASE.
*  ENDIF.

  ENDMETHOD.

* ---- ZHCMFAB_PERSINFO==============CM002 ----
  METHOD IF_EX_HCMFAB_PERSINFO_CONFIG~GET_MPC_INSTANCE.

    " This method provides the Model Provider Class (MPC) for your application.
    IF IV_APP_ID = IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYPERSONALDATA.
      " NOTE: The MPC class constructor takes 'io_model' which was already correct.
      CO_MPC_INSTANCE = NEW CL_HCMFAB_MYPERSONALDA_MPC_GEN(
                              IO_MODEL = IO_MODEL ).
    ENDIF.

* DATA lo_mpc_instance TYPE if_ex_hcmfab_persinfo_config=>ty_s_mpc_instance.
*
*  READ TABLE gt_mpc_instance WITH KEY app_id = iv_app_id INTO lo_mpc_instance.
*  IF sy-subrc NE 0 OR NOT lo_mpc_instance-mpc_instance IS BOUND.
*    lo_mpc_instance-app_id = iv_app_id.
*    CASE iv_app_id.
*      WHEN if_hcmfab_constants=>gc_application_id-myaddresses.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_myaddresses_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mybankdetails.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_mybankdetail_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mycommunication.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_mycommunicat_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-myinternaldata.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_myinternalda_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-myfamilymembers.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_myfamilymemb_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*      WHEN if_hcmfab_constants=>gc_application_id-mypersonaldata.
*        CREATE OBJECT lo_mpc_instance-mpc_instance TYPE cl_hcmfab_mypersonalda_mpc_gen
*          EXPORTING
*            io_model = io_model.
*        APPEND lo_mpc_instance TO gt_mpc_instance.
*        co_mpc_instance = lo_mpc_instance-mpc_instance.
*    ENDCASE.
*  ENDIF.

  ENDMETHOD.

* ---- ZHCMFAB_PERSINFO==============CM003 ----
  METHOD IF_EX_HCMFAB_PERSINFO_CONFIG~GET_PROPERTIES_NO_CONVERSION.
    " This method is used to disable backend conversion exits for specific fields.
    " This can be left empty as it is not needed for your current requirement.
  ENDMETHOD.

* ---- ZHCMFAB_PERSINFO==============CM004 ----
  METHOD IF_EX_HCMFAB_PERSINFO_CONFIG~GET_SCREEN_VERSIONS.
    " This method tells the framework which frontend XML views to use.
    DATA LS_UI_SCREENS TYPE IF_EX_HCMFAB_PERSINFO_CONFIG=>TY_S_UI_SCREENS.

    CASE IV_APP_ID.
      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYADDRESSES.
        LS_UI_SCREENS-SUBTYPE = IF_EX_HCMFAB_PERSINFO_CONFIG=>GC_SUBTYPE_DEFAULT.
        LS_UI_SCREENS-DISPLAY_SCREEN = 'UN_Display_Default_V001'. "#EC NOTEXT
        LS_UI_SCREENS-EDIT_SCREEN = 'UN_Edit_Default_V001'. "#EC NOTEXT
        APPEND LS_UI_SCREENS TO CT_UI_SCREENS.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYBANKDETAILS.
*        ls_ui_screens-subtype = if_ex_hcmfab_persinfo_config=>gc_subtype_default.
*        ls_ui_screens-display_screen = '08_Display_Default_V001'. "#EC NOTEXT
*        ls_ui_screens-edit_screen = '08_Edit_Default_V001'. "#EC NOTEXT
*        APPEND ls_ui_screens TO ct_ui_screens.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYCOMMUNICATION.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYFAMILYMEMBERS.
        LS_UI_SCREENS-SUBTYPE = IF_EX_HCMFAB_PERSINFO_CONFIG=>GC_SUBTYPE_DEFAULT.
        LS_UI_SCREENS-DISPLAY_SCREEN = 'UN_Display_Default_V001'. "#EC NOTEXT
        LS_UI_SCREENS-EDIT_SCREEN = 'UN_Edit_Default_V001'. "#EC NOTEXT
        APPEND LS_UI_SCREENS TO CT_UI_SCREENS.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYPERSONALDATA.
        LS_UI_SCREENS-SUBTYPE = IF_EX_HCMFAB_PERSINFO_CONFIG=>GC_SUBTYPE_DEFAULT.
        LS_UI_SCREENS-DISPLAY_SCREEN = 'UN_Display_Default_V001'. "#EC NOTEXT
        LS_UI_SCREENS-EDIT_SCREEN = 'UN_Edit_Default_V001'. "#EC NOTEXT
        APPEND LS_UI_SCREENS TO CT_UI_SCREENS.
    ENDCASE.
  ENDMETHOD.

* ---- ZHCMFAB_PERSINFO==============CM005 ----
  METHOD IF_EX_HCMFAB_PERSINFO_CONFIG~GET_VALUEHELP_FIELDS.
    " This method is only for fields that have a value help (F4 help).
    " This can be left empty as it is not needed for your current requirement.
    FIELD-SYMBOLS <LS_NAVPROP_VH_FIELD> TYPE IF_EX_HCMFAB_PERSINFO_CONFIG=>TY_S_NAVPROP_VH_FIELD.

    CASE IV_APP_ID.
      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYADDRESSES.
* for all subtypes
        IF CT_NAVPROP_VH_FIELD IS INITIAL.

          CASE IV_ENTITY_NAME.
            WHEN CL_HCMFAB_MYADDRESSES_MPC=>GC_VALUEHELPCOUNTRY.
              APPEND 'LAND1' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYADDRESSES_MPC=>GC_VALUEHELPCOMMUNICATIONTYPE.
              APPEND 'COM01' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYADDRESSES_MPC=>GC_VALUEHELPSTATE.
              APPEND 'STATE' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYADDRESSES_MPC=>GC_VALUEHELPRELATIONSHIP.
              APPEND 'INDRL' TO CT_VALUEHELP_FIELDS.
            WHEN ''.
              APPEND 'LAND1' TO CT_VALUEHELP_FIELDS.
              APPEND 'COM01' TO CT_VALUEHELP_FIELDS.
              APPEND 'STATE' TO CT_VALUEHELP_FIELDS.
              APPEND 'INDRL' TO CT_VALUEHELP_FIELDS.
          ENDCASE.

        ELSE.
          LOOP AT CT_NAVPROP_VH_FIELD ASSIGNING <LS_NAVPROP_VH_FIELD>.
            CASE <LS_NAVPROP_VH_FIELD>-NAV_PROPERTY.
              WHEN 'TOVALUEHELPCOUNTRY'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'LAND1'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPCOMMUNICATIONTYPE'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'COM01'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPSTATE'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'STATE'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPRELATIONSHIP'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'INDRL'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
            ENDCASE.
          ENDLOOP.
        ENDIF.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYFAMILYMEMBERS.
* for all subtypes
        IF CT_NAVPROP_VH_FIELD IS INITIAL.
          CASE IV_ENTITY_NAME.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPGENDER.
              APPEND 'FASEX' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPNATIONBR.
              APPEND 'FGBLD' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPNATION.
              APPEND 'FANAT' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPMARITALSTATUS.
              APPEND 'FAMST' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPEMPLOYERTYPE.
              APPEND 'SERTY' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPORGANIZATION.
              APPEND 'SERUN' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPDUTYSTATION.
              APPEND 'SPODS' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPCURRENCY.
              APPEND 'WAERS' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYFAMILYMEMB_MPC=>GC_VALUEHELPFAMILYCHARACTERIS.
              APPEND 'KDBSL' TO CT_VALUEHELP_FIELDS.
              APPEND 'KDGBR' TO CT_VALUEHELP_FIELDS.
              APPEND 'KDUTB' TO CT_VALUEHELP_FIELDS.
            WHEN ''.

              APPEND 'FASEX' TO CT_VALUEHELP_FIELDS.
              APPEND 'FANAT' TO CT_VALUEHELP_FIELDS.
              APPEND 'FGBLD' TO CT_VALUEHELP_FIELDS.
              APPEND 'FAMST' TO CT_VALUEHELP_FIELDS.
              APPEND 'SERTY' TO CT_VALUEHELP_FIELDS.
              APPEND 'SERUN' TO CT_VALUEHELP_FIELDS.
              APPEND 'SPODS' TO CT_VALUEHELP_FIELDS.
              APPEND 'WAERS' TO CT_VALUEHELP_FIELDS.
              APPEND 'KDBSL' TO CT_VALUEHELP_FIELDS.
              APPEND 'KDGBR' TO CT_VALUEHELP_FIELDS.
              APPEND 'KDUTB' TO CT_VALUEHELP_FIELDS.
          ENDCASE.

        ELSE.
          LOOP AT CT_NAVPROP_VH_FIELD ASSIGNING <LS_NAVPROP_VH_FIELD>.
            CASE <LS_NAVPROP_VH_FIELD>-NAV_PROPERTY.
              WHEN 'TOVALUEHELPGENDER'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'FASEX'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPMARITALSTATUS'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'FAMST'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPORGANIZATION'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'SERUN'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPNATION'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'FANAT'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPEMPLOYERTYPE'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'SERTY'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPDUTYSTATION'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'SPODS'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPNATIONBR'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'FGBLD'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPCURRENCY'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'WAERS'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPFAMILYCHAR_2'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'KDBSL'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPFAMILYCHAR_3'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'KDUTB'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPFAMILYCHAR_4'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'KDGBR'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
            ENDCASE.
          ENDLOOP.
        ENDIF.

      WHEN IF_HCMFAB_CONSTANTS=>GC_APPLICATION_ID-MYPERSONALDATA.

        IF CT_NAVPROP_VH_FIELD IS INITIAL.
          CASE IV_ENTITY_NAME.
            WHEN CL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPANREX.
              APPEND 'ANRED' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPCOUNTRYOFBIRTH.
              APPEND 'GBLND' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPNATION.
              APPEND 'NATIO' TO CT_VALUEHELP_FIELDS.
              APPEND 'NATI2' TO CT_VALUEHELP_FIELDS.
              APPEND 'NATI3' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPGENDER.
              APPEND 'GESCH' TO CT_VALUEHELP_FIELDS.
            WHEN CL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPMARISTATFATXT.
              APPEND 'FAMST' TO CT_VALUEHELP_FIELDS.

              " ********** START OF CHANGE **********
              " Add a case for your custom value help entity name
              " This name should be a constant in your custom MPC, e.g., ZCL_HCMFAB_MYPERSONALDA_MPC=>GC_VALUEHELPZZREGGR
            WHEN 'ValueHelpZzreggr'. " <-- Use the constant from your MPC for the ValueHelp entity
              APPEND 'ZZREGGR' TO CT_VALUEHELP_FIELDS.
              " ********** END OF CHANGE **********

            WHEN ''.
              APPEND 'ANRED' TO CT_VALUEHELP_FIELDS.
              APPEND 'GBLND' TO CT_VALUEHELP_FIELDS.
              APPEND 'NATIO' TO CT_VALUEHELP_FIELDS.
              APPEND 'NATI2' TO CT_VALUEHELP_FIELDS.
              APPEND 'NATI3' TO CT_VALUEHELP_FIELDS.
              APPEND 'GESCH' TO CT_VALUEHELP_FIELDS.
              APPEND 'FAMST' TO CT_VALUEHELP_FIELDS.
              " ********** START OF CHANGE **********
              APPEND 'ZZREGGR' TO CT_VALUEHELP_FIELDS. " Also add here for general case
              " ********** END OF CHANGE **********
          ENDCASE.

        ELSE.
          LOOP AT CT_NAVPROP_VH_FIELD ASSIGNING <LS_NAVPROP_VH_FIELD>.
            CASE <LS_NAVPROP_VH_FIELD>-NAV_PROPERTY.
              WHEN 'TOVALUEHELPANREX'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'ANRED'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPCOUNTRYOFBIRTH'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'GBLND'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPNATION'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'NATIO'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'NATI2'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'NATI3'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPGENDER'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'GESCH'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
              WHEN 'TOVALUEHELPMARISTATFATXT'.
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'FAMST'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.

                " ********** START OF CHANGE **********
                " Add a case for the navigation property to your custom value help
                " This navigation property name is defined in your MPC extension
              WHEN 'ToValueHelpZzreggr'. " <-- Use the navigation property name from your MPC
                <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME = 'ZZREGGR'.
                APPEND <LS_NAVPROP_VH_FIELD>-VH_FIELDNAME TO CT_VALUEHELP_FIELDS.
                " ********** END OF CHANGE **********

            ENDCASE.
          ENDLOOP.
        ENDIF.

    ENDCASE.
  ENDMETHOD.

* ---- ZHCMFAB_PERSINFO==============CO ----
  PROTECTED SECTION.

* ---- ZHCMFAB_PERSINFO==============CU ----
CLASS ZHCMFAB_PERSINFO DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.

    INTERFACES IF_BADI_INTERFACE .
    INTERFACES IF_EX_HCMFAB_PERSINFO_CONFIG .