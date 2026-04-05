*****           Implementation of object type ZGOSREJECT           *****
INCLUDE <object>.
BEGIN_DATA OBJECT. " Do not change.. DATA is generated
* only private members may be inserted into structure private
DATA:
" begin of private,
"   to declare private attributes remove comments and
"   insert private attributes here ...
" end of private,
  BEGIN OF KEY,
      GOS_NOTE_KEY LIKE BORIDENT-OBJKEY,
  END OF KEY,
      FLAG TYPE SYST-FTYPE.
END_DATA OBJECT. " Do not change.. DATA is generated
begin_method zsgos_note_display changing container.
CALL FUNCTION 'SGOS_NOTE_DISPLAY'
  EXPORTING
*   IS_OBJECT          =
    ip_note            = object-key-gos_note_key.
*   IP_DISP_HTML       = 'X'
end_method.
GET_PROPERTY FLAG CHANGING CONTAINER.
  SWC_SET_ELEMENT CONTAINER 'FLAG' 'X'.
END_PROPERTY.