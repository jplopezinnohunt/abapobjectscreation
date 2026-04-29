METHOD get_instance.
* This method is used to return the right Class to fill in Reference
* field into structure FPAYHX and table FPAYP in function module
* FI_PAYMEDIUM_DMEE_CGI_05.
* When the Country Specific Class (with suffix ISO Country Code) is
* found, then this class is used. (prio 1)
* When the Country Specific Class is not found, but the Generic
* Class is found, then this Generic Class is used, (prio 2)
* In other cases INITIAL value is returned. (prio 3)

  DATA:
    lv_country_class   TYPE string,
    lv_country_key       TYPE land1,
    ls_format_properties TYPE tfpm042f.

* Prepare Retrurn Parameter
  FREE ro_instance.

  CLEAR lv_country_key.
  IF is_fpayhx-formi IS NOT INITIAL.                          "n3043741
    ls_format_properties = cl_idfi_utils=>get_format_properties( iv_formi = is_fpayhx-formi ).
  ENDIF.
  IF ls_format_properties-land1 IS NOT INITIAL.               "n3043741
    lv_country_key = ls_format_properties-land1.
  ELSEIF is_fpayhx-ubiso IS NOT INITIAL.
    lv_country_key = is_fpayhx-ubiso.
  ELSE.
    lv_country_key = is_fpayhx-ubnks.
  ENDIF. "IF is_fpayhx-ubiso IS NOT INITIAL.

  IF mv_country_key IS INITIAL OR lv_country_key NE mv_country_key.
*   Delete Instance
    FREE mo_instance.
*   Prepare country version
    CONCATENATE co_cgi_call05_prefix lv_country_key
          INTO lv_country_class.
    TRY .
        mv_country_key = lv_country_key.
        CREATE OBJECT mo_instance TYPE (co_cgi_call05_generic).
        CREATE OBJECT ro_instance TYPE (lv_country_class).
*       Fill static value
        mo_instance    = ro_instance.
      CATCH cx_sy_create_object_error.
*       Fill static value
        CASE lv_country_key.
          WHEN 'LI'.                          "#EC NOTEXT
*           Special handling for LI -> CH                      n2533796
          CONCATENATE co_cgi_call05_prefix 'CH'
                 INTO lv_country_class.                     "#EC NOTEXT
          TRY .
            CREATE OBJECT ro_instance TYPE (lv_country_class).
*             Fill static value
              mo_instance    = ro_instance.
            CATCH cx_sy_create_object_error.
*             Fill static value
              ro_instance = mo_instance.
            ENDTRY.
*           Special handling for LI -> CH                      n2533796
          WHEN OTHERS.
            ro_instance = mo_instance.
        ENDCASE. "CASE lv_country_key.
    ENDTRY.

  ELSE.
*   Return parameter
    ro_instance = mo_instance.
  ENDIF. "IF mv_country_key IS INITIAL OR lv_country_key NE mv_country_key.

ENDMETHOD.