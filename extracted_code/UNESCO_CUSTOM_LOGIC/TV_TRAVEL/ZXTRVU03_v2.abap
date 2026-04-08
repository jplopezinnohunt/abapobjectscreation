*&---------------------------------------------------------------------*
*&  Include           ZXTRVU03                                         *
*&---------------------------------------------------------------------*

DATA lt_p0017 TYPE TABLE OF p0017.
DATA ls_p0017 TYPE p0017.
DATA subrc_inftyp TYPE sy-subrc.
DATA l_ztvck TYPE ztvck.
DATA l_return(1).
MOVE-CORRESPONDING trip_header TO l_ztvck.

CALL FUNCTION 'HR_READ_INFOTYPE'
  EXPORTING
    pernr           = trip_header-pernr
    infty           = '0017'
    begda           = trip_header-datv1
    endda           = trip_header-datv1
  IMPORTING
    subrc           = subrc_inftyp
  TABLES
    infty_tab       = lt_p0017
  EXCEPTIONS
    infty_not_found = 1
    OTHERS          = 2.

READ TABLE lt_p0017 INTO ls_p0017 INDEX 1.
IF sy-subrc EQ 0.
  MOVE ls_p0017-spebe TO l_ztvck-spebe.
ELSE.
  CLEAR l_ztvck-spebe.
ENDIF.

** read the feature ztvck
CALL METHOD cl_hrpa_feature=>get_value
  EXPORTING
    feature       = 'ZTVCK'
    struc_content = l_ztvck
  IMPORTING
    return_value  = l_return.

IF l_return = 'X' AND sy-subrc = 0.
 MESSAGE e001(zfitv) WITH trip_header-kzrea trip_header-kztkt l_ztvck-spebe.
 continue_with_update = 'N'.
ENDIF.

***********************************************************************************
* check overlapping period with dependants
DATA ls_user TYPE ptk99.
DATA l_allowed(1) .

LOOP AT user INTO ls_user. "only first line
  EXIT.
ENDLOOP.

IF zcl_trip=>is_dependants_mandatory( TRIP_HEADER ) EQ 'X' AND LS_USER IS INITIAL.
  MESSAGE e003(zfitv) WITH trip_header-kzrea trip_header-kztkt l_ztvck-spebe.
  continue_with_update = 'N'.
ENDIF.

CALL METHOD zcl_trip=>is_overlapping_allowed
  EXPORTING
    head    = trip_header
    perio   = trip_period
    users   = ls_user
  RECEIVING
    allowed = l_allowed.
IF l_allowed NE 'X'.
  continue_with_update = 'N'.
*  MESSAGE e002(zfitv) WITH trip_header-kzrea trip_header-kztkt.

ENDIF.
