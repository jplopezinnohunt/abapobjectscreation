*****           Implementation of object type YBSEG                *****
INCLUDE <object>.
BEGIN_DATA OBJECT. " Do not change.. DATA is generated
* only private members may be inserted into structure private
DATA:
" begin of private,
"   to declare private attributes remove comments and
"   insert private attributes here ...
" end of private,
  BEGIN OF KEY,
      COMPANYCODE LIKE BSEG-BUKRS,
      DOCUMENTNO LIKE BSEG-BELNR,
      FISCALYEAR LIKE BSEG-GJAHR,
      LINEITEM LIKE BSEG-BUZEI,
  END OF KEY,
      VENDORINFOS TYPE SWC_OBJECT,
      ZHEADER TYPE SWC_OBJECT,
      ZKEY_WITHOUT_ITEM(255),
      _BSEG LIKE BSEG.
END_DATA OBJECT. " Do not change.. DATA is generated
begin_method rejectionreason changing container.
DATA : lv_object TYPE  borident.
DATA : lv_title TYPE sood-objdes.
MOVE text-001 TO lv_title .
MOVE 'BKPF' TO lv_object-objtype.
MOVE object-key(18) TO lv_object-objkey.
DATA: ws_borident-objkey TYPE borident-objkey.
CALL FUNCTION 'SGOS_NOTE_CREATE_DIALOG'
  EXPORTING
    is_object        = lv_object
   ip_title         = lv_title
*   IT_CONTENT       =
 IMPORTING
   ep_note          = ws_borident-objkey
          .
swc_set_element container 'ZNOTE_KEY' ws_borident-objkey.
COMMIT WORK.
end_method.
TABLES bseg.
*
get_table_property bseg.
DATA subrc LIKE sy-subrc.
* Fill TABLES BSEG to enable Object Manager Access to Table Properties
PERFORM select_table_bseg USING subrc.
IF subrc NE 0.
  exit_object_not_found.
ENDIF.
end_property.
*
* Use Form also for other(virtual) Properties to fill TABLES BSEG
FORM select_table_bseg USING subrc LIKE sy-subrc.
* Select single * from BSEG, if OBJECT-_BSEG is initial
  IF object-_bseg-mandt IS INITIAL
  AND object-_bseg-bukrs IS INITIAL
  AND object-_bseg-belnr IS INITIAL
  AND object-_bseg-gjahr IS INITIAL
  AND object-_bseg-buzei IS INITIAL.
    SELECT SINGLE * FROM bseg CLIENT SPECIFIED
        WHERE mandt = sy-mandt
        AND bukrs = object-key-companycode
        AND belnr = object-key-documentno
        AND gjahr = object-key-fiscalyear
        AND buzei = object-key-lineitem.
    subrc = sy-subrc.
    IF subrc NE 0. EXIT. ENDIF.
    object-_bseg = bseg.
  ELSE.
    subrc = 0.
    bseg = object-_bseg.
  ENDIF.
ENDFORM.                    "SELECT_TABLE_BSEG
get_property vendorinfos changing container.
DATA: wl_vendor TYPE bseg-lifnr,
     lo_vendorinfos TYPE swc_object.
swc_get_property self 'VENDOR' wl_vendor.
swc_create_object lo_vendorinfos 'LFA1' wl_vendor.
swc_set_element container 'Vendorinfos' lo_vendorinfos.
end_property.
get_property zkey_without_item changing container.
swc_set_element container 'ZKey_Without_Item' object-key(18).
end_property.
begin_method zcreatepaymentblockwf changing container.
DATA: ls_bseg TYPE bseg.
*UPDATE vbkpf SET xwffr  = 'X'
*                 reldt = sy-datum                           "note909744
*                 reltm = sy-uzeit                           "note909744
*                 usrel = sy-uname                           "note909744
*          WHERE ausbk EQ object-key-companycode AND
*                bukrs EQ object-key-companycode AND
*                belnr EQ object-key-documentno AND
*                gjahr EQ object-key-fiscalyear.
UPDATE bseg
   SET zlspr = 'W'
 WHERE bukrs EQ object-key-companycode AND
       belnr EQ object-key-documentno AND
       gjahr EQ object-key-fiscalyear AND
       buzei EQ object-key-lineitem.
*UPDATE bsik
*   SET zlspr = 'W'
* WHERE bukrs EQ ls_bseg-bukrs AND
*       lifnr EQ ls_bseg-lifnr AND
*       umsks EQ ls_bseg-umsks AND
*       umskz EQ ls_bseg-umskz AND
*       augdt EQ ls_bseg-augdt AND
*       augbl EQ ls_bseg-augbl AND
*       zuonr EQ ls_bseg-zuonr AND
*      gjahr EQ ls_bseg-gjahr AND
*       belnr EQ ls_bseg-belnr AND
*       buzei EQ ls_bseg-buzei.
UPDATE bsik
SET zlspr = 'W'
 WHERE bukrs EQ object-key-companycode AND
        belnr EQ object-key-documentno AND
        gjahr EQ object-key-fiscalyear AND
        buzei EQ object-key-lineitem.
end_method.
GET_PROPERTY ZHEADER CHANGING CONTAINER.
DATA: wl_BUKRS TYPE bseg-BUKRS,
      wl_BELNR TYPE bseg-BELNR,
      wl_GJAHR TYPE bseg-GJAHR,
      wl_bseg(255),
     lo_bseg TYPE swc_object.
swc_get_property self 'CompanyCode' wl_BUKRS.
swc_get_property self 'DocumentNo' wl_BELNR.
swc_get_property self 'FiscalYear' wl_GJAHR.
CONCATENATE wl_bukrs wl_belnr wl_gjahr into wl_bseg.
swc_create_object lo_bseg 'BSEG' wl_bseg.
  SWC_SET_ELEMENT CONTAINER 'ZHeader' lo_bseg.
END_PROPERTY.