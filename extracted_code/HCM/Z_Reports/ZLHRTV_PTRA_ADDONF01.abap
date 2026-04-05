*&---------------------------------------------------------------------*
*&  Include           ZLHRTV_PTRA_ADDONF01                             *
*&---------------------------------------------------------------------*
* FI-TV : COST OBJECT FROM ORG MANAGEMENT (Cost distribution)
*&---------------------------------------------------------------------*
*&      Form  EXIST_COSTCENTER_P0017                     WBG 24.06.1999
*&---------------------------------------------------------------------*
FORM exist_costcenter_p1018  USING     p_employeenumber TYPE pernr_d
                                       p_begin_date     TYPE rebed
                                       p_end_date       TYPE reend
                            CHANGING   p_hri1001_cost  TYPE hri1001_cost
                                       p_answer        TYPE      c .
  DATA in_objects TYPE TABLE OF hrrootob .
  DATA ls_in_objects TYPE hrrootob .
  DATA tdist_costcenters TYPE TABLE OF hri1001_cost .
  DATA dist_costcenters TYPE hri1001_cost .
  DATA last_prozt TYPE prozt.
  ls_in_objects-otype = 'P'.
  ls_in_objects-objid =  p_employeenumber .
  APPEND ls_in_objects TO in_objects.
  CALL FUNCTION 'RH_COSTCENTER_OF_OBJECT_GET'
    EXPORTING
      plvar                              = '01'
      begda                              = p_begin_date
      endda                              = p_end_date
*       SVECT                              = '1'
*       ACTIVE                             =
    dist                               = 'X'
*       OBJECT_ONLY                        =
*       BUFFERED_ACCESS                    = 'X'
*       READ_IT0001                        = 'X'
*       I0027_FLAG                         =
*       OMBUFFER_MODE                      =
*       READ_EX_RELAT                      = ' '
*       CHECK_AUTH_1018                    = ' '
    TABLES
      in_objects                         = in_objects
*       MAIN_COSTCENTERS                   =
   dist_costcenters                   = tdist_costcenters
*       INIT_TAB                           =
*       GIVEN_P0001_TAB                    =
*       COST_PATHS                         =
*     EXCEPTIONS
*       GIVEN_P0001_TAB_NOT_COMPLETE       = 1
*       NO_AUTHORIZATION_1018              = 2
*       OTHERS                             = 3
            .
  IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ELSE.
    CLEAR last_prozt .
    LOOP AT tdist_costcenters INTO dist_costcenters.
      IF dist_costcenters-prozt GT last_prozt.
        MOVE-CORRESPONDING dist_costcenters TO p_hri1001_cost.
      ENDIF.
      last_prozt = dist_costcenters-prozt.
    ENDLOOP.
  ENDIF.
  IF p_hri1001_cost IS INITIAL.
    p_answer = no.
  ELSE.
    p_answer = yes.
  ENDIF.
ENDFORM.                               " EXIST_COSTCENTER_P1018