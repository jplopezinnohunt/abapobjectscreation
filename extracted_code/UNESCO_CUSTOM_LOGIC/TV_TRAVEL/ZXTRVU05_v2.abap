*----------------------------------------------------------------------*
*   INCLUDE ZXTRVU05                                                   *
*----------------------------------------------------------------------*

data: w_check_status.

field-symbols: <BELEG> type PTK03,
               <KONTI> type PTK17.


***check for zero amount
clear w_check_status.
loop at BELEG assigning <BELEG>.
  if <BELEG>-betrg <> 0.
    w_check_status = 'X'.
  endif. "<BELEG>-betrg
endloop.
check w_check_status = 'X' or
      TRIP_PERIOD-verpa = 'X' or
      TRIP_PERIOD-uebkz = 'X'.
***

loop at KONTI assigning <KONTI>.
  case <KONTI>-bukrs.
    when 'UNES'.
  clear w_check_status.
  perform init_check using <KONTI>-bukrs
                           <KONTI>-geber
                           <KONTI>-fipos
                           space
                           space
                           space
                           space
                           TRIP_PERIOD-pdatv
                           TRIP_PERIOD-abrj1
                           <KONTI>-gsber
                           TRIP_HEADER
                           'X'
                     changing w_check_status.

  check w_check_status = space.

***I_KONAKOV 04/2018 - no need to check FCtr hierarchy in BCS
*  perform fund_centre_hier using <KONTI>-bukrs
*                                 <KONTI>-geber
*                                 <KONTI>-fistl
*                                 TRIP_PERIOD-abrj1.

  perform compare_fund_wbs using <KONTI>-posnr
                                 <KONTI>-geber
                                 space.

  perform fund_ba_wbs_cc using <KONTI>-geber
                               space
                               space
                               space
                               <KONTI>-kostl
                               <KONTI>-posnr
                               <KONTI>-gsber
                               'X'.
    when 'UBO'.

    when others.
*      perform inst_fund_ba_wbs_cc using <KONTI>-bukrs
*                                        <KONTI>-geber
*                                        space
*                                        space
*                                        space
*                                        <KONTI>-kostl
*                                        <KONTI>-posnr
*                                        <KONTI>-gsber
*                                        'X'.
  endcase.
  if <KONTI>-posnr <> space and <KONTI>-kostl <> space.
     message id 'ZFI' type 'E' number '009'
     with 'Please specify either Cost Center or WBS-element, not both!'.
  endif.
endloop. "KONTI
