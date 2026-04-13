REPORT rhhrfpm_fm_pos_update line-size 100.
INCLUDE rhpbc_fm_doc.
DATA: it_fm_pos       TYPE TABLE OF hrfpm_fm_pos.
DATA: doc_man         TYPE REF TO cl_hrfpm_fm_doc.
DATA: dummy_header    TYPE hrfpm_fpm_doc_header.
DATA: wa_fm_pos       TYPE hrfpm_fm_pos.

SELECT * FROM hrfpm_fm_pos INTO TABLE it_fm_pos
                    WHERE bukrs IN so_bukrs
                      AND kokrs IN so_kokrs
                      AND kostl IN so_kostl
                      AND aufnr IN so_aufnr
                      AND posnr IN so_posnr
                      AND nplnr IN so_nplnr
                      AND vornr IN so_vornr
                      AND geber IN so_geber
                      AND fistl IN so_fistl
                      AND fipex IN so_fipex
                      AND grant_nbr IN so_grant
                      AND fkber IN so_fkber.

IF sy-subrc = 0.
  CREATE OBJECT doc_man
         EXPORTING p_header = dummy_header.
  LOOP AT it_fm_pos INTO wa_fm_pos.
    TRY.
        CALL METHOD doc_man->rebuild_document
          EXPORTING
            p_pos = wa_fm_pos.
      CATCH cx_hrfpm_fm_posting.
* Hier noch Fehlerprotokoll
    ENDTRY.
  ENDLOOP.
ENDIF.
