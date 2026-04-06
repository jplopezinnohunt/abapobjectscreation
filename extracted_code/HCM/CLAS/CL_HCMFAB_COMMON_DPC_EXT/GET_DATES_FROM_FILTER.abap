method GET_DATES_FROM_FILTER.

  data: ls_start_filter_select_option type /IWBEP/S_MGW_SELECT_OPTION,
        ls_end_filter_select_option type /IWBEP/S_MGW_SELECT_OPTION,
        ls_start_select_option type /IWBEP/S_COD_SELECT_OPTION,
        ls_end_select_option type /IWBEP/S_COD_SELECT_OPTION.

  clear: ev_start_date, ev_end_date.

* check if one option is specified for startDate and endDate in the filter values
  read table it_filter_select_options into ls_start_filter_select_option with key property = 'StartDate'.
  if sy-subrc <> 0.
    return.
  endif.
  read table it_filter_select_options into ls_end_filter_select_option with key property = 'EndDate'.
  if sy-subrc <> 0.
    return.
  endif.
  read table ls_start_filter_select_option-select_options into ls_start_select_option index 1.
  if sy-subrc <> 0.
    return.
  endif.
  read table ls_end_filter_select_option-select_options into ls_end_select_option index 1.
  if sy-subrc <> 0.
    return.
  endif.

* we only support two cases:
  if ls_start_select_option-option = 'EQ' and ls_end_select_option-option = 'EQ'.
*   1) dates are provided via EQ
*   -> take the dates as they are
    ev_start_date = ls_start_select_option-low.
    ev_end_date = ls_end_select_option-low.
  elseif ls_start_select_option-option = 'LE' and ls_end_select_option-option = 'GE'.
*   2) interval is defined via START >= <date> AND END <= <date>
*   -> switch begin and end date to get the correct selection dates
    ev_start_date = ls_end_select_option-low.
    ev_end_date = ls_start_select_option-low.
  endif.

endmethod.
