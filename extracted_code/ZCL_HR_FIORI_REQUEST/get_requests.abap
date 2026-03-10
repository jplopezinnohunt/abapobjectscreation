  METHOD get_requests.


    SELECT * FROM zthrfiori_breq INTO TABLE @DATA(lt_requests) WHERE creator_usr_id EQ @sy-uname .
    IF sy-subrc EQ 0.
      et_results = CORRESPONDING #( lt_requests  ).
      sort et_results by  creation_date  DESCENDING request_key  DESCENDING .
    ENDIF.


*    et_results = VALUE #(
*  ( guid = '001' request_key = '001' request_type = 'Rental')
*  ( guid = '002' request_key = '002' request_type = 'Education')
*
*).

  ENDMETHOD.
