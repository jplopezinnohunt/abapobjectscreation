*&---------------------------------------------------------------------*
*& Report Z_GATEWAY_ENTITY_IMPORTER
*&---------------------------------------------------------------------*
*& Import entity definitions from JSON file and create them in Gateway
*& Service Builder (SEGW) programmatically
*&---------------------------------------------------------------------*
REPORT z_gateway_entity_importer.

*----------------------------------------------------------------------*
* Type Definitions
*----------------------------------------------------------------------*
TYPES: BEGIN OF ty_property,
         name           TYPE string,
         type           TYPE string,
         is_key         TYPE abap_bool,
         nullable       TYPE abap_bool,
         max_length     TYPE i,
         precision      TYPE i,
         scale          TYPE i,
         label          TYPE string,
         abap_fieldname TYPE string,
       END OF ty_property.

TYPES: BEGIN OF ty_navigation,
         name          TYPE string,
         target_entity TYPE string,
         multiplicity  TYPE string,
       END OF ty_navigation.

TYPES: BEGIN OF ty_entity,
         name            TYPE string,
         label           TYPE string,
         entity_set_name TYPE string,
         properties      TYPE STANDARD TABLE OF ty_property WITH DEFAULT KEY,
         navigations     TYPE STANDARD TABLE OF ty_navigation WITH DEFAULT KEY,
       END OF ty_entity.

TYPES: BEGIN OF ty_config,
         service_name TYPE string,
         entities     TYPE STANDARD TABLE OF ty_entity WITH DEFAULT KEY,
       END OF ty_config.

*----------------------------------------------------------------------*
* Data Declarations
*----------------------------------------------------------------------*
DATA: lv_file_path    TYPE string,
      lv_json_string  TYPE string,
      lt_file_content TYPE TABLE OF string,
      ls_config       TYPE ty_config,
      lv_message      TYPE string.

*----------------------------------------------------------------------*
* Selection Screen
*----------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
PARAMETERS: p_file TYPE string LOWER CASE DEFAULT 'C:\temp\entity_config.json'.
SELECTION-SCREEN END OF BLOCK b1.

*----------------------------------------------------------------------*
* F4 Help for File Path
*----------------------------------------------------------------------*
AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_file.
  PERFORM f4_file_path CHANGING p_file.

*----------------------------------------------------------------------*
* Main Processing
*----------------------------------------------------------------------*
START-OF-SELECTION.

  WRITE: / 'SAP Gateway Entity Importer'.
  WRITE: / '================================'.
  SKIP.

  " Step 1: Read JSON file
  WRITE: / '1. Reading JSON file:', p_file.
  PERFORM read_json_file USING p_file
                         CHANGING lv_json_string lv_message.

  IF lv_message IS NOT INITIAL.
    WRITE: / '   ❌ Error:', lv_message COLOR COL_NEGATIVE.
    RETURN.
  ENDIF.

  WRITE: / '   ✓ File read successfully' COLOR COL_POSITIVE.
  SKIP.

  " Step 2: Parse JSON
  WRITE: / '2. Parsing JSON configuration...'.
  PERFORM parse_json USING lv_json_string
                     CHANGING ls_config lv_message.

  IF lv_message IS NOT INITIAL.
    WRITE: / '   ❌ Error:', lv_message COLOR COL_NEGATIVE.
    RETURN.
  ENDIF.

  WRITE: / '   ✓ JSON parsed successfully' COLOR COL_POSITIVE.
  WRITE: / '   Service:', ls_config-service_name.
  WRITE: / '   Entities:', lines( ls_config-entities ).
  SKIP.

  " Step 3: Display entities to be created
  WRITE: / '3. Entities to be created:'.
  PERFORM display_entities USING ls_config.
  SKIP.

  " Step 4: Generate MPC_EXT code
  WRITE: / '4. Generating MPC_EXT code...'.
  PERFORM generate_mpc_code USING ls_config.

  SKIP.
  WRITE: / '================================'.
  WRITE: / '✓ Process completed' COLOR COL_POSITIVE.
  SKIP.
  WRITE: / 'Next steps:'.
  WRITE: / '  1. Copy the generated code below'.
  WRITE: / '  2. Open SEGW transaction'.
  WRITE: / '  3. Navigate to your service MPC_EXT class'.
  WRITE: / '  4. Paste the code in the DEFINE method'.
  WRITE: / '  5. Activate and regenerate the service'.

*----------------------------------------------------------------------*
* Form Implementations
*----------------------------------------------------------------------*

*&---------------------------------------------------------------------*
*& Form f4_file_path
*&---------------------------------------------------------------------*
FORM f4_file_path CHANGING p_path TYPE string.
  DATA: lv_file TYPE string.

  CALL METHOD cl_gui_frontend_services=>file_open_dialog
    EXPORTING
      window_title            = 'Select JSON Configuration File'
      default_extension       = 'json'
      file_filter             = 'JSON Files (*.json)|*.json|All Files (*.*)|*.*'
    CHANGING
      file_table              = VALUE filetable( )
      rc                      = DATA(lv_rc)
    EXCEPTIONS
      file_open_dialog_failed = 1
      cntl_error              = 2
      error_no_gui            = 3
      not_supported_by_gui    = 4
      OTHERS                  = 5.

  IF sy-subrc = 0.
    READ TABLE VALUE filetable( ) INDEX 1 INTO DATA(ls_file).
    IF sy-subrc = 0.
      p_path = ls_file-filename.
    ENDIF.
  ENDIF.
ENDFORM.

*&---------------------------------------------------------------------*
*& Form read_json_file
*&---------------------------------------------------------------------*
FORM read_json_file USING    iv_file_path TYPE string
                    CHANGING ev_json TYPE string
                             ev_message TYPE string.

  DATA: lt_data TYPE TABLE OF string.

  CLEAR: ev_json, ev_message.

  " Read file from frontend
  CALL METHOD cl_gui_frontend_services=>gui_upload
    EXPORTING
      filename                = iv_file_path
      filetype                = 'ASC'
      has_field_separator     = ' '
    CHANGING
      data_tab                = lt_data
    EXCEPTIONS
      file_open_error         = 1
      file_read_error         = 2
      no_batch                = 3
      gui_refuse_filetransfer = 4
      invalid_type            = 5
      no_authority            = 6
      unknown_error           = 7
      bad_data_format         = 8
      header_not_allowed      = 9
      separator_not_allowed   = 10
      header_too_long         = 11
      unknown_dp_error        = 12
      access_denied           = 13
      dp_out_of_memory        = 14
      disk_full               = 15
      dp_timeout              = 16
      not_supported_by_gui    = 17
      error_no_gui            = 18
      OTHERS                  = 19.

  IF sy-subrc <> 0.
    ev_message = |File read error: { sy-subrc }|.
    RETURN.
  ENDIF.

  " Concatenate lines into single JSON string
  LOOP AT lt_data INTO DATA(lv_line).
    CONCATENATE ev_json lv_line INTO ev_json.
  ENDLOOP.

  IF ev_json IS INITIAL.
    ev_message = 'File is empty'.
  ENDIF.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form parse_json
*&---------------------------------------------------------------------*
FORM parse_json USING    iv_json TYPE string
                CHANGING es_config TYPE ty_config
                         ev_message TYPE string.

  CLEAR: es_config, ev_message.

  TRY.
      " Use SAP's JSON parser (available in NW 7.40+)
      /ui2/cl_json=>deserialize(
        EXPORTING
          json = iv_json
          pretty_name = /ui2/cl_json=>pretty_mode-camel_case
        CHANGING
          data = es_config ).

    CATCH cx_root INTO DATA(lx_error).
      ev_message = lx_error->get_text( ).
  ENDTRY.

  IF es_config-service_name IS INITIAL.
    ev_message = 'Invalid JSON: service_name is required'.
  ENDIF.

  IF es_config-entities IS INITIAL.
    ev_message = 'Invalid JSON: at least one entity is required'.
  ENDIF.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form display_entities
*&---------------------------------------------------------------------*
FORM display_entities USING is_config TYPE ty_config.

  LOOP AT is_config-entities INTO DATA(ls_entity).
    WRITE: / '   -', ls_entity-name, '(', lines( ls_entity-properties ), 'properties)'.

    " Show key properties
    LOOP AT ls_entity-properties INTO DATA(ls_prop) WHERE is_key = abap_true.
      WRITE: / '     [KEY]', ls_prop-name, ':', ls_prop-type.
    ENDLOOP.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form generate_mpc_code
*&---------------------------------------------------------------------*
FORM generate_mpc_code USING is_config TYPE ty_config.

  DATA: lt_code TYPE TABLE OF string,
        lv_line TYPE string.

  SKIP.
  WRITE: / '========================================'.
  WRITE: / 'GENERATED MPC_EXT CODE'.
  WRITE: / '========================================'.
  SKIP.

  " Header
  APPEND 'METHOD define.' TO lt_code.
  APPEND '  " Auto-generated by Z_GATEWAY_ENTITY_IMPORTER' TO lt_code.
  APPEND '  " ' TO lt_code.
  APPEND '  CALL METHOD super->define.' TO lt_code.
  APPEND '  ' TO lt_code.
  APPEND '  DATA: lo_entity TYPE REF TO /iwbep/if_mgw_odata_entity_typ,' TO lt_code.
  APPEND '        lo_property TYPE REF TO /iwbep/if_mgw_odata_property.' TO lt_code.
  APPEND '  ' TO lt_code.

  " Generate code for each entity
  LOOP AT is_config-entities INTO DATA(ls_entity).

    APPEND |  " Create entity: { ls_entity-name }| TO lt_code.
    APPEND |  lo_entity = model->create_entity_type( iv_entity_type_name = '{ ls_entity-name }' ).| TO lt_code.

    IF ls_entity-label IS NOT INITIAL.
      APPEND |  lo_entity->set_label( '{ ls_entity-label }' ).| TO lt_code.
    ENDIF.

    APPEND '  ' TO lt_code.

    " Generate properties
    LOOP AT ls_entity-properties INTO DATA(ls_prop).

      APPEND |  " Property: { ls_prop-name }| TO lt_code.
      APPEND |  lo_property = lo_entity->create_property(| TO lt_code.
      APPEND |    iv_property_name = '{ ls_prop-name }'| TO lt_code.

      IF ls_prop-abap_fieldname IS NOT INITIAL.
        APPEND |    iv_abap_fieldname = '{ ls_prop-abap_fieldname }'| TO lt_code.
      ENDIF.

      APPEND |  ).| TO lt_code.

      " Set key
      IF ls_prop-is_key = abap_true.
        APPEND |  lo_property->set_is_key( ).| TO lt_code.
      ENDIF.

      " Set nullable
      IF ls_prop-nullable = abap_false.
        APPEND |  lo_property->set_nullable( abap_false ).| TO lt_code.
      ENDIF.

      " Set type based on EDM type
      CASE ls_prop-type.
        WHEN 'Edm.String'.
          IF ls_prop-max_length > 0.
            APPEND |  lo_property->set_max_length( { ls_prop-max_length } ).| TO lt_code.
          ENDIF.
        WHEN 'Edm.Decimal'.
          IF ls_prop-precision > 0.
            APPEND |  lo_property->set_precision( { ls_prop-precision } ).| TO lt_code.
          ENDIF.
          IF ls_prop-scale > 0.
            APPEND |  lo_property->set_scale( { ls_prop-scale } ).| TO lt_code.
          ENDIF.
      ENDCASE.

      " Set label
      IF ls_prop-label IS NOT INITIAL.
        APPEND |  lo_property->set_label( '{ ls_prop-label }' ).| TO lt_code.
      ENDIF.

      APPEND '  ' TO lt_code.

    ENDLOOP.

    " Create entity set
    DATA(lv_entity_set) = ls_entity-entity_set_name.
    IF lv_entity_set IS INITIAL.
      lv_entity_set = |{ ls_entity-name }Set|.
    ENDIF.

    APPEND |  " Create entity set| TO lt_code.
    APPEND |  model->create_entity_set(| TO lt_code.
    APPEND |    iv_entity_set_name = '{ lv_entity_set }'| TO lt_code.
    APPEND |    iv_entity_type_name = '{ ls_entity-name }' ).| TO lt_code.
    APPEND '  ' TO lt_code.

  ENDLOOP.

  APPEND 'ENDMETHOD.' TO lt_code.

  " Output generated code
  LOOP AT lt_code INTO lv_line.
    WRITE: / lv_line.
  ENDLOOP.

  SKIP.
  WRITE: / '========================================'.

ENDFORM.
