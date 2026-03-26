 method employeegroupset_get_entityset.
   data: ls_persg  type zcl_hr_fiori_offboarding_req=>ty_persg,
         ls_return type zcl_zhrf_offboard_mpc=>ts_employeegroup,
         lt_persg  type zcl_hr_fiori_offboarding_req=>tt_persg,
         lt_return type zcl_zhrf_offboard_mpc=>tt_employeegroup,
         lo_object type ref to zcl_hr_fiori_offboarding_req.

   lo_object = zcl_hr_fiori_offboarding_req=>get_instance( ).
   lo_object->get_persg_list( importing ot_list = lt_persg ).

   loop at lt_persg into ls_persg.
     move ls_persg-id to ls_return-id.
     move ls_persg-text to ls_return-text.
     append ls_return to lt_return.
   endloop.

   et_entityset = lt_return.
 endmethod.
