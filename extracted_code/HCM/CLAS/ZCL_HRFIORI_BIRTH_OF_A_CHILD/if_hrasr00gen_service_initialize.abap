  METHOD if_hrasr00gen_service~initialize.

    DATA: lv_subtype_txt TYPE sbttx,
          lo_common      TYPE REF TO zcl_hrfiori_pf_common,
          lv_birthdate   TYPE FGBDT,
          lv_temp_date   TYPE datum,
          lv_information         TYPE string,
          lv_notif_date  TYPE begda.

    FIELD-SYMBOLS <fs_fld_value> TYPE hrasr00gensrv_dataset_init.
    FIELD-SYMBOLS: <help_dataset_wa>  TYPE hrasr00gs_help_dataset,
                   <ls_data>          TYPE hrasr00gs_help_dataset,
                   <help_values>      TYPE table,
                   <fs__ui_attr>      TYPE if_hrasr00_types=>ty_s_gensrv_init_ui_attribute,
                   <fs_service_field> TYPE hrasr00gensrv_dataset_init.

*   Display information text for yearly amount
    MESSAGE ID 'ZHRFIORI' TYPE 'I' NUMBER '132'
      INTO lv_information.
    LOOP AT service_field_values ASSIGNING <fs_service_field>
      WHERE fieldname = 'AMOUNT_PRECISION'.
      <fs_service_field>-fieldvalue = lv_information.
    ENDLOOP.

    CREATE OBJECT lo_common.
    lo_common->get_subtype_text( EXPORTING iv_infotype = '0021'
                                           iv_subtype = '14'
                                 IMPORTING ov_subtype_text = lv_subtype_txt ).

    LOOP AT  service_field_values ASSIGNING <fs_fld_value>
      WHERE fieldname = 'I0021_FAMSA_TEXT'.
      <fs_fld_value>-fieldvalue = lv_subtype_txt.
    ENDLOOP.

* ------ Infotype 0378 is handled in method DO_OPERATIONS ------
**Case 1 – Notification received within one month of the birth date
**•  Condition: notification_date ≤ birth_date + 1 month
**•  Action: effective_date = birth_date
**Case 2 – Notification received more than one month after the birth date
**•  Condition: notification_date > (birth_date + 1 month)
**•  Action: effective_date of the notification
*
*    LOOP AT  service_field_values ASSIGNING <fs_fld_value>
*      WHERE fieldname = 'I0021_BEGDA'.
*      lv_notif_date = <fs_fld_value>-fieldvalue.
*    ENDLOOP.
*    LOOP AT  service_field_values ASSIGNING <fs_fld_value>
*      WHERE fieldname = 'I0021_FGBDT'.
*      lv_birthdate = <fs_fld_value>-fieldvalue.
*    ENDLOOP.
*
*    CALL FUNCTION 'MONTH_PLUS_DETERMINE'
*      EXPORTING
*        MONTHS        = 1
*        OLDDATE       = lv_birthdate
*      IMPORTING
*        NEWDATE       = lv_temp_date
*              .
*
**   Initialization fo fields for infotype 0378
*    LOOP AT service_field_values ASSIGNING <fs_fld_value>.
*      IF <fs_fld_value>-fieldname = 'I0378_BEGDA'.
*        IF lv_notif_date LE lv_temp_date.
*          MOVE lv_birthdate TO <fs_fld_value>-fieldvalue.
*        ELSE.
*          MOVE lv_notif_date TO <fs_fld_value>-fieldvalue.
*        ENDIF.
*      ENDIF.
*
*      IF <fs_fld_value>-fieldname = 'I0378_ENDDA'.
*        MOVE sy-datum TO <fs_fld_value>-fieldvalue.
*      ENDIF.
*
*      IF <fs_fld_value>-fieldname = 'I0378_EVENT'.
*        <fs_fld_value>-fieldvalue = 'CHIL'.
*      ENDIF.
*
*      IF <fs_fld_value>-fieldname = 'I0378_BAREA'.
*        <fs_fld_value>-fieldvalue = '11'.
*      ENDIF.
*
*    ENDLOOP.

  ENDMETHOD.
