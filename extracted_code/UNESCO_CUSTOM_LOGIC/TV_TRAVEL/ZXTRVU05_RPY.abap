*----------------------------------------------------------------------*
*   INCLUDE ZXTRVU05                                                   *
*----------------------------------------------------------------------*

DATA: W_CHECK_STATUS.

FIELD-SYMBOLS: <BELEG> TYPE PTK03,
               <KONTI> TYPE PTK17.


***check for zero amount
CLEAR W_CHECK_STATUS.
LOOP AT BELEG ASSIGNING <BELEG>.
  IF <BELEG>-BETRG <> 0.
    W_CHECK_STATUS = 'X'.
  ENDIF. "<BELEG>-betrg
ENDLOOP.
CHECK W_CHECK_STATUS = 'X' OR
      TRIP_PERIOD-VERPA = 'X' OR
      TRIP_PERIOD-UEBKZ = 'X'.
***

LOOP AT KONTI ASSIGNING <KONTI>.
  CASE <KONTI>-BUKRS.
    WHEN 'UNES'.
  CLEAR W_CHECK_STATUS.
  PERFORM INIT_CHECK USING <KONTI>-BUKRS
                           <KONTI>-GEBER
                           <KONTI>-FIPOS
                           SPACE
                           SPACE
                           SPACE
                           SPACE
                           TRIP_PERIOD-PDATV
                           TRIP_PERIOD-ABRJ1
                           <KONTI>-GSBER
                           TRIP_HEADER
                           'X'
                     CHANGING W_CHECK_STATUS.

  CHECK W_CHECK_STATUS = SPACE.

***I_KONAKOV 04/2018 - no need to check FCtr hierarchy in BCS
*  perform fund_centre_hier using <KONTI>-bukrs
*                                 <KONTI>-geber
*                                 <KONTI>-fistl
*                                 TRIP_PERIOD-abrj1.

  PERFORM COMPARE_FUND_WBS USING <KONTI>-POSNR
                                 <KONTI>-GEBER
                                 SPACE.

  PERFORM FUND_BA_WBS_CC USING <KONTI>-GEBER
                               SPACE
                               SPACE
                               SPACE
                               <KONTI>-KOSTL
                               <KONTI>-POSNR
                               <KONTI>-GSBER
                               'X'.
    WHEN 'UBO'.

    WHEN OTHERS.
*      perform inst_fund_ba_wbs_cc using <KONTI>-bukrs
*                                        <KONTI>-geber
*                                        space
*                                        space
*                                        space
*                                        <KONTI>-kostl
*                                        <KONTI>-posnr
*                                        <KONTI>-gsber
*                                        'X'.
  ENDCASE.
  IF <KONTI>-POSNR <> SPACE AND <KONTI>-KOSTL <> SPACE.
     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
     WITH 'Please specify either Cost Center or WBS-element, not both!'.
  ENDIF.
ENDLOOP. "KONTI