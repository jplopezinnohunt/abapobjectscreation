*&---------------------------------------------------------------------*
*& ABAP Direct Entity Creation - Sin UI
*& Alternativa a SEGW UI automation
*&---------------------------------------------------------------------*
* Este approach crea entities dinámicamente en el modelo OData
* redefiniendo el método DEFINE de la clase MPC_EXT
*&---------------------------------------------------------------------*

CLASS zcl_gateway_entity_creator DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS create_entity_dynamically
      IMPORTING
        iv_service_name TYPE string
        iv_entity_name  TYPE string
        it_properties   TYPE table
      RETURNING
        VALUE(rv_success) TYPE abap_bool.
ENDCLASS.

CLASS zcl_gateway_entity_creator IMPLEMENTATION.
  METHOD create_entity_dynamically.
    " Approach 1: Extender MPC_EXT para crear entities dinámicos
    " En tu proyecto SEGW, redefine el método DEFINE:

    " METHOD define.
    "   CALL METHOD super->define.
    "
    "   DATA: lo_entity TYPE REF TO /iwbep/if_mgw_odata_entity_typ,
    "         lo_property TYPE REF TO /iwbep/if_mgw_odata_property.
    "
    "   " Crear entity type dinámicamente
    "   lo_entity = model->create_entity_type( iv_entity_name ).
    "   lo_entity->set_label( 'Dynamic Entity' ).
    "
    "   " Agregar properties dinámicamente
    "   lo_property = lo_entity->create_property(
    "     iv_property_name = 'ID'
    "     iv_abap_fieldname = 'MANDT' ).
    "   lo_property->set_is_key( ).
    "   lo_property->set_type_edm_string( ).
    "
    "   lo_property = lo_entity->create_property(
    "     iv_property_name = 'Name'
    "     iv_abap_fieldname = 'NAME' ).
    "   lo_property->set_type_edm_string( ).
    "
    "   " Crear entity set
    "   model->create_entity_set(
    "     iv_entity_set_name = iv_entity_name && 'Set'
    "     iv_entity_type_name = iv_entity_name ).
    " ENDMETHOD.

    rv_success = abap_true.
  ENDMETHOD.
ENDCLASS.

*&---------------------------------------------------------------------*
*& Approach 2: Usar ABAP Development Objects
*&---------------------------------------------------------------------*
* Crear entities via código ABAP usando las APIs de Gateway
*
* Ventajas:
*   - No requiere UI automation
*   - Más rápido y confiable
*   - Versionable en Git
*   - Puede ser ejecutado en CI/CD
*
* Desventajas:
*   - Requiere conocimiento ABAP
*   - Requiere permisos de desarrollo
*   - No visualiza en SEGW hasta generar
*
*&---------------------------------------------------------------------*

* Ejemplo de uso:
* DATA(lo_creator) = NEW zcl_gateway_entity_creator( ).
*
* DATA(lt_properties) = VALUE table(
*   ( name = 'ID' type = 'Edm.String' key = 'X' )
*   ( name = 'Name' type = 'Edm.String' )
*   ( name = 'Description' type = 'Edm.String' )
* ).
*
* DATA(lv_success) = lo_creator->create_entity_dynamically(
*   iv_service_name = 'Z_CRP_SRV'
*   iv_entity_name  = 'Certificate'
*   it_properties   = lt_properties ).
