  method IF_HRASR00GEN_SERVICE~GET_OPERATIONS.

    data: ls_operration type hrasr00gs_operation.

    ls_operration-operation = 'SPEC'.

    append ls_operration TO operations.

  endmethod.
