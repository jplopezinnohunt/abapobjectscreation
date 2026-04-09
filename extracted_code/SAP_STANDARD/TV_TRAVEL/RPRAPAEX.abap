* include rprapaex.
* This include is reserved for user specific routines

*----------------------------------------------------------------------*
*       FORM SET_MC_FIELD_BY_USER
*----------------------------------------------------------------------*
*  routine changes the sortfield of the A/P-account
*----------------------------------------------------------------------*
FORM SET_MC_FIELD_BY_USER.
* blfa1-sortl = ...                                 "sort-field
ENDFORM.

*----------------------------------------------------------------------*
*       Form  SET_ADRESS_BY_USER
*----------------------------------------------------------------------*
*  routine changes the adress fields in blfa1
*----------------------------------------------------------------------*
FORM SET_ADDRESS_BY_USER.
* blfa1-stras = ...                                 "street
* blfa1-ort01 = ...                                 "City
* blfa1-ort02 = ...                                 "other location
* ...
ENDFORM.