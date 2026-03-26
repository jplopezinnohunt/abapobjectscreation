  METHOD childsvhset_get_entityset.


    DATA : lo_education    TYPE REF TO zcl_hr_fiori_education_grant.

    ##TODO "Get pernr from uname
    CREATE OBJECT lo_education.

    "get pernr from uname
    ##TODO "Send begda from front
    SELECT SINGLE pernr FROM pa0105 INTO @DATA(lv_pernr)
              WHERE usrid EQ  @sy-uname AND subty EQ '0001' AND begda LE @sy-datum AND endda GE @sy-datum.

    lo_education->get_child_list(
       EXPORTING
         iv_pernr  =         lv_pernr         " Personnel Number
         iv_begda  =         sy-datum         " Start Date
         iv_endda  =         sy-datum          " End Date
       RECEIVING
         rt_childs =         et_entityset " Benefit App - type of table child
     ).
* CATCH zcx_hr_benef_exception. " Exception class for Benefits
  ENDMETHOD.
