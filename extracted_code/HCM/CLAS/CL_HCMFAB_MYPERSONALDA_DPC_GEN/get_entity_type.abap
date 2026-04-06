  METHOD get_entity_type.

* we have to make sure that the entity type length does not exceed 27 chars:
* in the MPC the type has a maximum length of 30 chars and is composed from
* 'TS_' followed by the (cut off) entity name
    DATA: lv_entity_name TYPE c LENGTH 27.                  "2808465
    lv_entity_name = iv_entity_name.

    CONCATENATE 'CL_HCMFAB_MYPERSONALDA_MPC=>TS_' lv_entity_name INTO ev_entity_type.

  ENDMETHOD.
