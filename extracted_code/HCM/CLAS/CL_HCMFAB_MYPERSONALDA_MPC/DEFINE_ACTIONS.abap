method DEFINE_ACTIONS.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS          &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL   &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                    &*
*&                                                                     &*
*&---------------------------------------------------------------------*


data:
lo_action         type ref to /iwbep/if_mgw_odata_action,                 "#EC NEEDED
lo_parameter      type ref to /iwbep/if_mgw_odata_parameter.              "#EC NEEDED

***********************************************************************************************************************************
*   ACTION - FI42_CalculateMinguo
***********************************************************************************************************************************

lo_action = model->create_action( 'FI42_CalculateMinguo' ).  "#EC NOTEXT
*Set return complex type
lo_action->set_return_complex_type( 'Taiwan42Minguo' ). "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '0' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Date'    iv_abap_fieldname = 'BEGDA' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '099' iv_text_element_container = 'CL_HCMFAB_MYPERSONALDA_MPC_EXT' ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_datetime( ).
lo_action->bind_input_structure( iv_structure_name  = 'CL_HCMFAB_MYPERSONALDA_MPC=>TS_FI42_CALCULATEMINGUO' ). "#EC NOTEXT
endmethod.
