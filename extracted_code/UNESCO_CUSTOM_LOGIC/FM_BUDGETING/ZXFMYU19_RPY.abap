TYPE-POOLS:
  FMFI.
DATA:
  L_F_COBL LIKE COBL.

*----- Give SGTXT
  C_DEFAULT_SGTXT  = I_F_FMIFIIT-SGTXT.

*----- Give OBJNRZ according to ACCIT-information
  C_DEFAULT_OBJNRZ = I_F_FMIFIIT-OBJNRZ.

*----- Give VREFBN for documents with PO-reference
*   for funds reservation the information is already in DEFAULT_VREFBN *
IF NOT I_F_ACCIT-EBELN IS INITIAL.

  C_DEFAULT_VREFBN = I_F_ACCIT-EBELN.

ENDIF.

*--3.) CO-objectnumber not yet updated to  PO commitment---------------*
IF C_DEFAULT_OBJNRZ IS INITIAL.

 CHECK NOT I_F_ACCIT-KOKRS IS INITIAL.                "<-ins 2000-11-15
  MOVE-CORRESPONDING I_F_ACCIT TO L_F_COBL.           "<-ins 2000-11-14
  IF L_F_COBL-GLVOR IS INITIAL.                       "<-ins 2000-11-14
     L_F_COBL-GLVOR = I_F_ACCHD-GLVOR.                "<-ins 2000-11-14
  ENDIF.                                              "<-ins 2000-11-14
  CLEAR L_F_COBL-EBELN.
  CLEAR L_F_COBL-KTOSL.
  CALL FUNCTION 'FM_ACCOUNT_GET_COBL'
       EXPORTING
            I_FLG_BUFFER_ALL = 'X'
       IMPORTING
            E_OBJNR          = C_DEFAULT_OBJNRZ
       CHANGING
            C_COBL           = L_F_COBL.
ENDIF.


*----- Give HKONT
  C_DEFAULT_HKONT = I_F_FMIFIIT-HKONT.

*----- Give KNBUZEI
  C_DEFAULT_KNBUZEI = I_F_FMIFIIT-KNBUZEI.