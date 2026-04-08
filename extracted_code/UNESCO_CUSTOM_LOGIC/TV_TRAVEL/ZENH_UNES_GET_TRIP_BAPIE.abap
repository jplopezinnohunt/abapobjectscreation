ENHANCEMENT 1  .
FORM get_trip_form_unes
      TABLES pt_return             TYPE bapirettab
       USING p_pernr               LIKE bapiempl-pernr
             p_reinr               LIKE bapitrip-tripno
             p_perio               LIKE bapitrvxxx-period
             pv_version_trip_component TYPE ptrv_trip_component  "XMW EHP5_Versioning
             pv_version_number         TYPE ptrv_version_number  "XMW EHP5_Versioning
             p_trip_data_source    TYPE ptrv_web_source
             p_language            LIKE bapitrvxxx-langu
             p_test.

  DATA: lwa_form_control              TYPE ptra_web_form_control,
        lwa_form_header_data_employee TYPE ptrv_web_form_header_employee,
        lwa_form_header_data_employer TYPE ptrv_web_form_header_employer,
        lt_form_address_employer      TYPE ptrv_web_form_address_t,
        lt_form_address_employee      TYPE ptrv_web_form_address_t,
        lwa_general_data              TYPE ptrv_web_general_data_ext,
        lt_receipts                   TYPE ptrv_web_receipts_ext_t_2,
        lt_advances                   TYPE ptrv_web_advances_ext_t,
        lt_mileage                    TYPE ptrv_web_mileage_ext_t,
        lt_itinerary                  TYPE ptrv_web_itinerary_ext_t,
        lt_deductions                 TYPE ptrv_web_deductions_ext_t,
        lt_costdist_trip              TYPE ptrv_web_costdist_trip_ext_t,
        lt_costdist_itin              TYPE ptrv_web_costdist_itin_ext_t,
        lt_costdist_rece              TYPE ptrv_web_costdist_rece_ext_t,
        lt_costdist_pdf               TYPE ptrv_web_costdist_rece_pdf_t,
        lt_costdist_mile              TYPE ptrv_web_costdist_mile_ext_t,
        lt_mastercost_default         TYPE ptrv_web_costdist_trip_ext_t,
        lt_history                    TYPE ptrv_web_history_t,
        lt_meals_per_diems            TYPE ptrv_web_meals_per_diems_t,
        lt_meals_per_diems_totals     TYPE ptrv_web_meals_per_diems_tls_t,
        lt_accom_per_diems            TYPE ptrv_web_accom_per_diems_t,
        lt_accom_per_diems_totals     TYPE ptrv_web_accom_per_diems_tls_t,
        lt_travel_flat_rates          TYPE ptrv_web_travel_flat_rates_t,
        lt_travel_flat_rates_totals   TYPE ptrv_web_travel_flat_rates_t_t,
        lt_mileage_add_info           TYPE ptrv_web_mil_add_info_form_t,
        lt_mileage_detail             TYPE ptrv_web_mileage_detail_pdf_t,
        lt_totals                     TYPE ptrv_web_totals_t,
        lt_receipts_tax_free          TYPE ptrv_web_receipts_form_t,
        lt_receipts_tax_free_totals   TYPE ptrv_web_receipts_form_tls_t,
        lt_receipts_taxable           TYPE ptrv_web_receipts_form_t,
        lt_receipts_taxable_totals    TYPE ptrv_web_receipts_form_tls_t,
        lt_receipts_vs_max_amt        TYPE ptrv_web_receipts_form_t,
        lt_receipts_vs_max_amt_totals TYPE ptrv_web_receipts_form_tls_t,
        lt_receipts_income_rel        TYPE ptrv_web_receipts_form_t,        "ZFJ2387967
        lt_receipts_income_rel_totals TYPE ptrv_web_receipts_form_tls_t,    "ZFJ2387967
        lt_receipts_add_info          TYPE ptrv_web_rec_add_info_form_t,
        lt_hinz_werb_s_form           TYPE ptrv_web_add_amt_inc_rel_exp_t,
        lt_hinz_werb_s_form_sums      TYPE ptrv_web_add_amt_inc_rel_exp_t,
        ls_ps_form_heading_cat        TYPE ptra_web_pdf_title_headings,
        lt_res_rec_vs_max_amt         TYPE ptrv_web_res_recs_vs_max_amt_t,
        lt_res_rec_vs_max_amt_totals  TYPE ptrv_web_res_recs_max_amt_ts_t,
        lt_advances_form              TYPE ptrv_web_advances_form_t,
        lt_advances_form_totals       TYPE ptrv_web_advances_form_t,
        lt_cost_alloc                 TYPE ptrv_costdist_results_t,
        lv_policy_violation           TYPE boolean,
        lv_max_diff_violation         TYPE ptrv_web_editor, "QKW_FEH_EES_EHP5e
        lt_trip_break                 TYPE ptrv_web_trip_break_t,
        lt_add_dest                   TYPE ptrv_web_add_dest_t,
        lt_receipts_violations        TYPE ptrv_web_rec_violations_form_t.
  DATA  lt_user                       TYPE ptk99_t.            "XMWK1331867
  DATA: lt_pocket_money        TYPE ptrv_web_meals_per_diems_t,
        lt_pocket_money_totals TYPE ptrv_web_meals_per_diems_tls_t.
* HOJ_CEE_PL - Public Transport, Approaching Destination
  DATA: lt_transport            TYPE glo_ptrv_web_transport_ext_t,
        lt_pub_transport        TYPE glo_ptrv_web_transport_t,
        lt_pub_transport_totals TYPE glo_ptrv_web_transport_tls_t,
        lt_loc_transport        TYPE glo_ptrv_web_transport_t,
        lt_loc_transport_totals TYPE glo_ptrv_web_transport_tls_t.
* HOJ_CEE_PL
  DATA: lt_mahub                      TYPE ptrv_web_mahub_ps_t. "ZFJ2201281
* VRD_CEE_RU - exchange rates for exchange date
  DATA: lt_exchange_rates             TYPE glo_ptrv_web_exchange_rates_t.
* VRD_CEE_RU
* begin ZFJ2117042 PDF for TG
*  DATA: ls_perio_data_ps              TYPE ptrv_web_perio_data_ps. "ZFJ1729277 PDF for TG
  DATA: lt_ret_charge_acc              TYPE ptrv_web_ret_charge_acc_t,
        lt_meals_per_diems_tax_exempt  TYPE ptrv_web_meals_per_diems_t,
        lt_meals_per_diems_enterp_spec TYPE ptrv_web_meals_per_diems_t,
        lt_trip_home                   TYPE ptrv_web_trip_home_pdf_t,
        lt_trip_home_comp              TYPE ptrv_web_trip_home_comp_pdf_t,
        lt_trip_comp_home              TYPE ptrv_comp_pdf_t,
        lt_trip_comp_mileage           TYPE ptrv_comp_pdf_t,
        lt_parallel_pd_deduc           TYPE ptrv_web_parallel_pd_deduc_t,
        lt_household                   TYPE ptrv_household_t,
        ls_own_contribution            TYPE ptrv_own_contribution.

* end ZFJ2117042 PDF for TG

  DATA: ls_comp_data            TYPE ptrv_comp_pdf,              "ZFJ2279560
        lt_comp_add_info_ps     TYPE ptrv_web_trip_info_ps_t,    "ZFJ2279560
        lt_comp_add_dest        TYPE ptrv_web_add_dest_t,        "ZFJ2279560
        lt_comp_totals          TYPE ptrv_web_totals_t,          "ZFJ2279560
        lt_comp_meals_per_diems TYPE ptrv_web_meals_per_diems_t, "ZFJ2279560
        lt_comp_accom_per_diems TYPE ptrv_web_accom_per_diems_t, "ZFJ2279560
        lt_comp_travel_flat_rates TYPE  ptrv_web_travel_flat_rates_t,        "ZFJ2279560
        lt_comp_receipts        TYPE ptrv_web_receipts_form_t.   "ZFJ2279560


  DATA: lt_chain_mealspd              TYPE ptrv_web_trip_info_ps_t. "ZFJ2329364

  DATA: l_form_name      TYPE fpname,
        l_reinr          LIKE bapitrip-tripno,
        l_fm_name        TYPE rs38l_fnam,
        lwa_return       TYPE bapiret2,
        l_country        TYPE land1,
        l_status         TYPE c,
        l_error_occurred TYPE c,
        l_employeenumber LIKE bapiempl-pernr,
        l_tripnumber     LIKE bapitrip-tripno,
        l_trip_schema    TYPE rsche,
        l_date           TYPE date_with_fieldname,
        l_trvfe          TYPE ptrv_trvfe,
        l_trvfp          TYPE ptrv_trvfp,
        l_trvfr          TYPE ptrv_trvfr.

  DATA:  lt_return TYPE bapirettab,                         "QKWK001950
         ls_return TYPE bapiret2.                           "QKWK001950

  DATA: lt_trip_add_info_ps          TYPE ptrv_web_trip_info_ps_t. "ZFJ2139227

* expense report form...
  CALL FUNCTION 'PTRA_WEB_EXPENSE_FORM_DATA_GET'
    EXPORTING
      i_employeenumber               = p_pernr
      i_tripnumber                   = p_reinr
      i_periodnumber                 = p_perio
      iv_version_trip_component      = pv_version_trip_component      "XMW EHP5_Versioning
      iv_version_number              = pv_version_number              "XMW EHP5_Versioning
      i_trip_data_source             = p_trip_data_source
      i_language                     = p_language
    IMPORTING
      e_form_control                 = lwa_form_control
      e_form_header_data_employee    = lwa_form_header_data_employee
      e_form_header_data_employer    = lwa_form_header_data_employer
      et_form_address_employee       = lt_form_address_employee
      et_form_address_employer       = lt_form_address_employer
      e_general_data                 = lwa_general_data
      et_itinerary                   = lt_itinerary
      et_costdist_trip               = lt_costdist_trip
      et_costdist_itin               = lt_costdist_itin
      et_costdist_rece               = lt_costdist_rece
      et_costdist_pdf                = lt_costdist_pdf
      et_costdist_mile               = lt_costdist_mile
      et_mastercost_default          = lt_mastercost_default
      et_history                     = lt_history
      et_meals_per_diems             = lt_meals_per_diems
      et_meals_per_diems_totals      = lt_meals_per_diems_totals
      et_accom_per_diems             = lt_accom_per_diems
      et_accom_per_diems_totals      = lt_accom_per_diems_totals
      et_travel_flat_rates           = lt_travel_flat_rates
      et_travel_flat_rates_totals    = lt_travel_flat_rates_totals
      et_mileage_add_info            = lt_mileage_add_info
      et_mileage_detail              = lt_mileage_detail
      et_receipts_tax_free           = lt_receipts_tax_free
      et_receipts_tax_free_totals    = lt_receipts_tax_free_totals
      et_receipts_taxable            = lt_receipts_taxable
      et_receipts_taxable_totals     = lt_receipts_taxable_totals
      et_receipts_vs_max_amt         = lt_receipts_vs_max_amt
      et_receipts_vs_max_amt_totals  = lt_receipts_vs_max_amt_totals
      et_receipts_income_rel         = lt_receipts_income_rel        "ZFJ2387967
      et_receipts_income_rel_totals  = lt_receipts_income_rel_totals "ZFJ2387967
      et_receipts_add_info           = lt_receipts_add_info
      et_res_rec_vs_max_amt          = lt_res_rec_vs_max_amt
      et_res_rec_vs_max_amt_tls      = lt_res_rec_vs_max_amt_totals
      et_advances_form               = lt_advances_form
      et_advances_form_totals        = lt_advances_form_totals
      et_totals                      = lt_totals
      et_cost_alloc                  = lt_cost_alloc
      et_hinz_werb_s_form            = lt_hinz_werb_s_form
      et_hinz_werb_s_form_sums       = lt_hinz_werb_s_form_sums
      e_ps_form_heading_cat          = ls_ps_form_heading_cat
      e_policy_violation             = lv_policy_violation
      et_trip_break                  = lt_trip_break
      et_add_dest                    = lt_add_dest
      et_receipts_violations         = lt_receipts_violations
      ev_max_diff_violation          = lv_max_diff_violation    "QKW_FEH_EES_EHP5e
      et_user                        = lt_user                           "XMWK1331867
      et_pocket_money                = lt_pocket_money          "QKW_CEE_CZ_SK
      et_pocket_money_totals         = lt_pocket_money_totals   "QKW_CEE_CZ_SK
* HOJ_CEE_PL - Public Transport, Approaching Destination
      et_pub_transport               = lt_pub_transport
      et_pub_transport_totals        = lt_pub_transport_totals
      et_loc_transport               = lt_loc_transport
      et_loc_transport_totals        = lt_loc_transport_totals
* HOJ_CEE_PL
* VRD_CEE_RU 101129 - exchange rates for exchange date
      et_exchange_rates              = lt_exchange_rates
* VRD_CEE_RU
      et_trip_add_info_ps            = lt_trip_add_info_ps   "ZFJ2139227
* begin ZFJ2117042 PDF for TG
*     e_perio_data_ps                = ls_perio_data_ps   "ZFJ1729277 PDF for TG
      et_ret_charge_acc              = lt_ret_charge_acc
      et_meals_per_diems_tax_exempt  = lt_meals_per_diems_tax_exempt
      et_meals_per_diems_enterp_spec = lt_meals_per_diems_enterp_spec
      et_trip_home                   = lt_trip_home
      et_trip_comp_home              = lt_trip_comp_home
      et_trip_comp_mileage           = lt_trip_comp_mileage
      et_parallel_pd_deduc           = lt_parallel_pd_deduc
      et_household                   = lt_household
      e_own_contribution             = ls_own_contribution
* end ZFJ2117042 PDF for TG
      e_comp_data                    = ls_comp_data              "ZFJ2279560
      et_comp_add_info_ps            = lt_comp_add_info_ps       "ZFJ2279560
      et_comp_add_dest               = lt_comp_add_dest          "ZFJ2279560
      et_comp_totals                 = lt_comp_totals            "ZFJ2279560
      et_comp_meals_per_diems        = lt_comp_meals_per_diems   "ZFJ2279560
      et_comp_accom_per_diems        = lt_comp_accom_per_diems   "ZFJ2279560
      et_comp_travel_flat_rates      = lt_comp_travel_flat_rates "ZFJ2279560
      et_comp_receipts               = lt_comp_receipts          "ZFJ2279560
      et_chain_mealspd               = lt_chain_mealspd          "ZFJ2329364
      et_mahub                       = lt_mahub            "ZFJ2201281
    TABLES
      et_return                      = pt_return.

  LOOP AT pt_return INTO lwa_return WHERE type = 'E'
                                       OR type = 'A'.
    EXIT.
  ENDLOOP.
  IF sy-subrc IS INITIAL.
    RETURN.
  ENDIF.

* ARIK026400 begin
  IF lwa_general_data-country_grp = '03' AND lwa_general_data-pd_meals IS INITIAL.
    REFRESH lt_meals_per_diems.
  ENDIF.
* ARIK026400 end

* determine whether form run is test (does not set print status)
  IF lwa_form_control-fc_cancellation IS INITIAL.
    IF lwa_form_control-fc_simulation IS INITIAL.
      IF p_test IS NOT INITIAL.
        lwa_form_control-fc_test = p_test.
        CLEAR: lwa_form_control-fc_correction,
               lwa_form_control-fc_duplicate,
               lwa_form_control-fc_productive.
      ENDIF.
    ENDIF.
  ENDIF.

* determine name of Adobe form...
  l_date-date = lwa_general_data-datedep.

  CALL FUNCTION 'PTRA_UTIL_MEM_GLOBALS_GET'
    EXPORTING
      i_employeenumber = p_pernr
      i_date           = l_date
      i_trip_schema    = lwa_general_data-t_schema
    IMPORTING
      e_trvfe          = l_trvfe
    EXCEPTIONS
      error_occurred   = 1.

  IF sy-subrc IS NOT INITIAL.
    CLEAR lt_return.                                        "QKWK001950
* Because the TABLES-parameter is cleared in the form fill_bapirettab
* in case of a form call within a loop, working with local lt_return is
* necessary to save messages from previous loops
*   PERFORM fill_bapirettab TABLES pt_return                "QKWK001950
    PERFORM fill_bapirettab TABLES lt_return                "QKWK001950
                            USING p_language.
    LOOP AT lt_return INTO ls_return.                       "QKWK001950
      APPEND ls_return TO pt_return.                        "QKWK001950
    ENDLOOP.                                                "QKWK001950
    RETURN.
  ELSE.
    l_form_name = l_trvfe-trvfe.
  ENDIF.

  CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
    EXPORTING
      companycode = lwa_form_header_data_employee-comp_code
      language    = p_language
    IMPORTING
      country     = l_country
    EXCEPTIONS
      not_found   = 1
      OTHERS      = 2.

  IF sy-subrc IS NOT INITIAL.
    l_country   = 'DE'.
  ENDIF.

* handle initial trip number
  IF p_reinr EQ '9999999999'.
    l_reinr = '0000000000'.
  ELSE.
    l_reinr = p_reinr.
  ENDIF.

* ARIK032050 begin
  DATA l_timestring TYPE string.
  DATA lwa_itinerary LIKE LINE OF lt_itinerary.

  l_timestring = lwa_general_data-timearr.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timearr = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timedep.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timedep = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timeout.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timeout = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timefar.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timefar = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timefdp.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timefdp = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timeret.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timeret = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timedpe.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timedpe = l_timestring.
  ENDIF.

  l_timestring = lwa_general_data-timeape.
  IF strlen( l_timestring ) = 4.
    CONCATENATE l_timestring  '00' INTO l_timestring.
    lwa_general_data-timeape = l_timestring.
  ENDIF.

  LOOP AT lt_itinerary INTO lwa_itinerary.
    l_timestring = lwa_itinerary-timedep.
    IF strlen( l_timestring ) = 4.
      CONCATENATE l_timestring  '00' INTO l_timestring.
      lwa_itinerary-timedep = l_timestring.
      MODIFY lt_itinerary FROM lwa_itinerary.
    ENDIF.
  ENDLOOP.
* ARIK032050 end

CALL FUNCTION 'ZPTRM_UNES_FORM_SET'
  EXPORTING
    i_employeenumber                     = p_pernr
    e_form_control                       = lwa_form_control
    e_form_header_data_employee          = lwa_form_header_data_employee
    e_form_header_data_employer          = lwa_form_header_data_employer
    et_form_address_employee             = lt_form_address_employee
    et_form_address_employer             = lt_form_address_employer
    e_general_data                       = lwa_general_data
    et_itinerary                         = lt_itinerary
    et_costdist_trip                     = lt_costdist_trip
    et_costdist_itin                     = lt_costdist_itin
    et_costdist_rece                     = lt_costdist_rece
    et_costdist_pdf                      = lt_costdist_pdf
    et_costdist_mile                     = lt_costdist_mile
    et_mastercost_default                = lt_mastercost_default
    et_history                           = lt_history
    et_meals_per_diems                   = lt_meals_per_diems
    et_meals_per_diems_totals            = lt_meals_per_diems_totals
    et_accom_per_diems                   = lt_accom_per_diems
    et_accom_per_diems_totals            = lt_accom_per_diems_totals
    et_travel_flat_rates                 = lt_travel_flat_rates
    et_travel_flat_rates_totals          = lt_travel_flat_rates_totals
    et_mileage_add_info                  = lt_mileage_add_info
    et_mileage_detail                    = lt_mileage_detail
    et_receipts_tax_free                 = lt_receipts_tax_free
    et_receipts_tax_free_totals          = lt_receipts_tax_free_totals
    et_receipts_taxable                  = lt_receipts_taxable
    et_receipts_taxable_totals           = lt_receipts_taxable_totals
    et_receipts_vs_max_amt               = lt_receipts_vs_max_amt
    et_receipts_vs_max_amt_totals        = lt_receipts_vs_max_amt_totals
    et_receipts_income_rel               = lt_receipts_income_rel        "ZFJ2387967
    et_receipts_income_rel_totals        = lt_receipts_income_rel_totals "ZFJ2387967
    et_receipts_add_info                 = lt_receipts_add_info
    et_res_rec_vs_max_amt                = lt_res_rec_vs_max_amt
    et_res_rec_vs_max_amt_tls            = lt_res_rec_vs_max_amt_totals
    et_advances_form                     = lt_advances_form
    et_advances_form_totals              = lt_advances_form_totals
    et_totals                            = lt_totals
    et_cost_alloc                        = lt_cost_alloc
    et_hinz_werb_s_form                  = lt_hinz_werb_s_form
    et_hinz_werb_s_form_sums             = lt_hinz_werb_s_form_sums
    e_ps_form_heading_cat                = ls_ps_form_heading_cat
*      e_trip_summary                       =
    e_policy_violation                   = lv_policy_violation
    et_trip_break                        = lt_trip_break
    et_add_dest                          = lt_add_dest
    et_receipts_violations               = lt_receipts_violations
    ev_max_diff_violation                = lv_max_diff_violation    "QKW_FEH_EES_EHP5e
    et_user                              = lt_user                           "XMWK1331867
    et_pocket_money                      = lt_pocket_money          "QKW_CEE_CZ_SK
    et_pocket_money_totals               = lt_pocket_money_totals   "QKW_CEE_CZ_SK
*      ev_max_diff_violation                =
* HOJ_CEE_PL - Public Transport, Approaching Destination
    et_pub_transport                     = lt_pub_transport
    et_pub_transport_totals              = lt_pub_transport_totals
    et_loc_transport                     = lt_loc_transport
    et_loc_transport_totals              = lt_loc_transport_totals
* HOJ_CEE_PL
* VRD_CEE_RU 101129 - exchange rates for exchange date
    et_exchange_rates                    = lt_exchange_rates
* VRD_CEE_RU
    et_trip_add_info_ps                  = lt_trip_add_info_ps   "ZFJ2139227
* begin ZFJ2117042 PDF for TG
*     e_perio_data_ps                = ls_perio_data_ps   "ZFJ1729277 PDF for TG
    et_ret_charge_acc                    = lt_ret_charge_acc
    et_meals_per_diems_tax_exempt        = lt_meals_per_diems_tax_exempt
    et_meals_per_diems_enterp_spec       = lt_meals_per_diems_enterp_spec
    et_trip_home                         = lt_trip_home
    et_trip_comp_home                    = lt_trip_comp_home
    et_trip_comp_mileage                 = lt_trip_comp_mileage
    et_parallel_pd_deduc                 = lt_parallel_pd_deduc
    et_household                         = lt_household
    e_own_contribution                   = ls_own_contribution
* end ZFJ2117042 PDF for TG
    e_comp_data                          = ls_comp_data              "ZFJ2279560
    et_comp_add_info_ps                  = lt_comp_add_info_ps       "ZFJ2279560
    et_comp_add_dest                     = lt_comp_add_dest          "ZFJ2279560
    et_comp_totals                       = lt_comp_totals            "ZFJ2279560
    et_comp_meals_per_diems              = lt_comp_meals_per_diems   "ZFJ2279560
    et_comp_accom_per_diems              = lt_comp_accom_per_diems   "ZFJ2279560
    et_comp_travel_flat_rates            = lt_comp_travel_flat_rates "ZFJ2279560
    et_comp_receipts                     = lt_comp_receipts          "ZFJ2279560
    et_chain_mealspd                     = lt_chain_mealspd          "ZFJ2329364
    et_mahub                             = lt_mahub            "ZFJ2201281
          .




ENDFORM.                    " get_trip_form_unes
ENDENHANCEMENT.
