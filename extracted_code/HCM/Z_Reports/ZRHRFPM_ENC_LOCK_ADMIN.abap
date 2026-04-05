*&--------------------------------------------------------------------*
*& Report ZRHRFPM_ENC_LOCK_ADMIN
*&--------------------------------------------------------------------*
*  Titre     :
*
* --------------------------------------------------------------------*
*  Auteur :  Franck Guillou
*  Date   :  04/03/2019
* ------------------------------------------------------------------- *
*  Historique des modifications                                       *
*  Date      | Nom      | Objet                                       *
*  ------------------------------------------------------------------ *
*
*&--------------------------------------------------------------------*
REPORT zrhrfpm_enc_lock_admin.
DATA : go_lock    TYPE REF TO ycl_hrfpm_enc_lock_admin,
       gt_objects TYPE hrobject_tab.
TABLES:
  objec,
  gdstr.
SELECTION-SCREEN BEGIN OF BLOCK add WITH FRAME TITLE TEXT-add.
PARAMETERS:
  reason   TYPE hrfpm_enc_lock-reason
           AS LISTBOX VISIBLE LENGTH 60 DEFAULT 'REMOVE_VAC'.
SELECTION-SCREEN BEGIN OF BLOCK dat.
PARAMETERS:
  lockbegd TYPE hrfpm_enc_lock-begda,
  lockendd TYPE hrfpm_enc_lock-endda.
SELECTION-SCREEN END OF BLOCK dat.
PARAMETERS p_new AS CHECKBOX DEFAULT 'X'.
SELECTION-SCREEN END OF BLOCK add.
AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF screen-name CP '*REASON*'.
      screen-input = 0.
      MODIFY SCREEN.
    ENDIF.
    IF screen-name = 'P_NEW'.
      IF sy-sysid = 'P01'.
        screen-invisible = 1.
        MODIFY SCREEN.
      ENDIF.
    ENDIF.
  ENDLOOP.
INITIALIZATION.
START-OF-SELECTION.
  CREATE OBJECT go_lock
    EXPORTING
      iv_sel_per_begda = lockbegd
      iv_sel_per_endda = lockendd.
GET objec.
  FIELD-SYMBOLS <hrobject> LIKE LINE OF gt_objects.
  INSERT INITIAL LINE INTO TABLE gt_objects ASSIGNING <hrobject>.
  MOVE-CORRESPONDING objec TO <hrobject>.
END-OF-SELECTION.
  IF p_new = abap_false.
    go_lock->extraction( EXPORTING it_object = gt_objects
                                   iv_reason = reason ).
  ELSE.
    go_lock->extraction_new( EXPORTING it_object = gt_objects
                                       iv_reason = reason ).
  ENDIF.
  go_lock->display_alv( ).