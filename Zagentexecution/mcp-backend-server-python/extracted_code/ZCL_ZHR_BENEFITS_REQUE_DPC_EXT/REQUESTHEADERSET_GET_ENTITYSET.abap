*******************************************************************************
* Procjet           : Benefit  Request                                        *
* Module            : Benefit                                                 *
*-----------------------------------------------------------------------------*
* Author            :  Saad Igueninni                                         *
* Date              :  09.07.2025                                             *
*-----------------------------------------------------------------------------*
* Description   :  Benefit request headers get entityset                      *
*******************************************************************************
method REQUESTHEADERSET_GET_ENTITYSET.

 ZCL_HR_FIORI_REQUEST=>get_instance( )->get_requests(
               IMPORTING
                 et_results       = et_entityset ).

  endmethod.
