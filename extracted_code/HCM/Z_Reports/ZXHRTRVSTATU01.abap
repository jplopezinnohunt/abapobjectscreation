*&---------------------------------------------------------------------*
*&  Include           ZXHRTRVSTATU01
*&---------------------------------------------------------------------*
* <Unesco> – <Deletion the Travel Order> – INICIO
* DESCRIÇÃO: <Inclusão de função para envio de dados ao BizTalk>
*CALL FUNCTION 'ZRFC_TRAVEL_DELETE'
*  EXPORTING
*    i_personnel_number       = personnel_number
*    i_trip_number            = trip_number
*    i_trip_schema            = trip_schema
*    i_user_name              = sy-uname
*    i_update_type            = update_type
** IMPORTING
**   E_PERSONNEL_NUMBER       =
**   E_TRIP_NUMBER            =
**   E_TRIP_SCHEMA            =
**   E_USER_NAME              =
**   E_UPDATE_TYPE            =
*          .
**** NME 20201215
CALL FUNCTION 'Z_RFC_EXT_DEST_TRIP_DELETE'
  EXPORTING
    i_personnel_number       = personnel_number
    i_trip_number            = trip_number
          .
* <Unesco> – <Deletion the Travel Order> – FIM