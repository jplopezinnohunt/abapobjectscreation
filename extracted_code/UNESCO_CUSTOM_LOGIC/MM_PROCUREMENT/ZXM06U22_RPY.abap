*&---------------------------------------------------------------------*
*&  Include           ZXM06U22
*&---------------------------------------------------------------------*

*{   INSERT         D01K999910                                        1


*}   INSERT
*{   REPLACE        D01K999910                                        3
*\break d_siqueira.
*break d_siqueira.
*}   REPLACE


DATA WA_BEKPO LIKE LINE OF IT_BEKPO.

CONSTANTS: C_X TYPE C VALUE 'X'.

E_CEKKO = I_CEKKO.

IF NOT IT_BEKPO[] IS INITIAL.
  READ TABLE IT_BEKPO INTO WA_BEKPO INDEX 1.

*  CALL FUNCTION 'ZRFC_PO_RELEASE'
*    EXPORTING
*      po_number  = wa_bekpo-ebeln
*      po_rel_ind = c_x.

**** NME 20201215
  CALL FUNCTION 'Z_RFC_EXT_DEST_PO_RELEASE'
    EXPORTING
      PO_NUMBER       = WA_BEKPO-EBELN.

ENDIF.
*{   INSERT         D01K999910                                        2
***** UNES *****
IF      E_CEKKO-EKORG   =  'UNES'
AND   ( E_CEKKO-BSART   =  'CS'
OR      E_CEKKO-BSART   =  '205D'
OR      E_CEKKO-BSART   =  '205C'
OR      E_CEKKO-BSART   =  'PHOT'
OR      E_CEKKO-BSART   =  '354' ).

* Clean Material Group to skip release check on the field.
CLEAR E_CEKKO-MATKL.
E_CEKKO-MATKL = 'X'.

ENDIF.

IF      E_CEKKO-EKORG   =  'UNES'
AND     E_CEKKO-BSART   =  'COMM'
AND     E_CEKKO-MATKL   =  '06911110'.  "40 Phtocopier rnt/le

ELSEIF  E_CEKKO-EKORG   NE 'ICTP'.
* Clean Material Group to skip release check on the field.
CLEAR E_CEKKO-MATKL.
E_CEKKO-MATKL = 'X'.

ENDIF.

*break-point.

***** ICTP *****
TABLES: ZICTP_PO_RELEASE.
DATA WA_PO_RELEASE TYPE ZICTP_PO_RELEASE.

IF    E_CEKKO-EKORG   =  'ICTP'
AND   E_CEKKO-EKGRP   =  'I98'
AND ( E_CEKKO-BSART   =  'ICSR'          "ICTP support record
OR    E_CEKKO-BSART   =  'IMIS' ).       "ICTP mission


** Clean Material Group to skip release check on the field.
*clear e_cekko-MATKL.
*e_cekko-MATKL = 'Y'.

LOOP AT IT_BEKPO INTO WA_BEKPO.

SELECT SINGLE * FROM ZICTP_PO_RELEASE INTO CORRESPONDING FIELDS OF WA_PO_RELEASE
  WHERE BSART = E_CEKKO-BSART
    AND MATKL = E_CEKKO-MATKL.
IF SY-SUBRC NE 0.

  CLEAR E_CEKKO-MATKL.

ENDIF.

IF WA_BEKPO-KNTTP NE '6'.

  CLEAR E_CEKKO-MATKL.

ENDIF.

ENDLOOP.


IF E_CEKKO-MATKL EQ SPACE.

  E_CEKKO-MATKL = 'X'.

ELSE.

  E_CEKKO-MATKL = 'Y'.

ENDIF.

ELSEIF  E_CEKKO-EKORG   =  'ICTP'.

* Clean Material Group to skip release check on the field.
IF E_CEKKO-MATKL NE 'X'.
  E_CEKKO-MATKL = 'X'.
ENDIF.

ENDIF.

*}   INSERT