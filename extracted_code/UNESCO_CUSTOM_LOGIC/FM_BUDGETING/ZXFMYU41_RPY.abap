*----------------------------------------------------------------------*
*   INCLUDE ZXFMYU41                                                   *
*----------------------------------------------------------------------*

* Include pour définition con_off / con_on.
INCLUDE IFIFMCON_BOOL.

IF I_BATCH EQ 'X'.
  MOVE CON_ON TO E_CALL_AVC.
  MOVE CON_OFF TO E_CALL_AVC_MODE_WARNING.
  MOVE CON_OFF TO E_DONT_CALL_AVC.
ELSE.
ENDIF.