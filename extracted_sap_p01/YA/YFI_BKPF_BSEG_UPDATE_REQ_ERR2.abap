*&---------------------------------------------------------------------*
*& Report YFI_BKPF_BSEG_UPDATE_REQ_ERR2
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_BKPF_BSEG_UPDATE_REQ_ERR2.

DATA LT_BSIS TYPE TABLE OF BSIS.
DATA LT_FDSB TYPE TABLE OF FDSB.

PARAMETERS P_COMMIT AS CHECKBOX.

START-OF-SELECTION.

  SELECT * FROM BSIS WHERE BUKRS = 'UNES'
                     AND   GJAHR = '2025'
                     AND   BELNR = '3500083275'
           INTO TABLE @LT_BSIS.

  LOOP AT LT_BSIS INTO DATA(LS_BSIS).
    CHECK LS_BSIS-HKONT = '1075011' OR LS_BSIS-HKONT = '1175011'.
    DELETE FROM BSIS WHERE BUKRS = LS_BSIS-BUKRS
                     AND   HKONT = LS_BSIS-HKONT
                     AND   AUGDT = LS_BSIS-AUGDT
                     AND   AUGBL = LS_BSIS-AUGBL
                     AND   ZUONR = LS_BSIS-ZUONR
                     AND   GJAHR = LS_BSIS-GJAHR
                     AND   BELNR = LS_BSIS-BELNR
                     AND   BUZEI = LS_BSIS-BUZEI.
    LS_BSIS-HKONT = |000{ LS_BSIS-HKONT }|.
    INSERT BSIS FROM LS_BSIS.
  ENDLOOP.


  SELECT * FROM FDSB WHERE BUKRS = 'UNES'
                     AND   ( BNKKO = '1075011' OR BNKKO = '1175011' )
                     AND   DATUM = '20251222'
           INTO TABLE @LT_FDSB.

  LOOP AT LT_FDSB INTO DATA(LS_FDSB).
    DELETE FROM FDSB WHERE SEGMT = LS_FDSB-SEGMT
                     AND   BUKRS = LS_FDSB-BUKRS
                     AND   BNKKO = LS_FDSB-BNKKO
                     AND   EBENE = LS_FDSB-EBENE
                     AND   DISPW = LS_FDSB-DISPW
                     AND   DATUM = LS_FDSB-DATUM
                     AND   AVDAT = LS_FDSB-AVDAT
                     AND   GSBER = LS_FDSB-GSBER.
*    ls_fdsb-bnkko = |000{ ls_fdsb-bnkko }|.
*    INSERT fdsb FROM ls_fdsb.
  ENDLOOP.

  IF P_COMMIT = ABAP_FALSE.
    ROLLBACK WORK.
    WRITE: 'Done with Rollback'.
  ELSE.
    COMMIT WORK.
    WRITE: 'Done with Commit'.
  ENDIF.