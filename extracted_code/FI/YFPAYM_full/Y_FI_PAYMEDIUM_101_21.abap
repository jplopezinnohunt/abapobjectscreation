FUNCTION Y_FI_PAYMEDIUM_101_21 .
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_FORMAT_PARAMS) TYPE  FPM_SELPAR-PARAM
*"     VALUE(I_FORMAT_PARAMS_C) TYPE  FPM_SELPAR-PARAM
*"     VALUE(I_FILENAME) LIKE  REGUT-FSNAM
*"     VALUE(I_XFILESYSTEM) TYPE  DFILESYST
*"  TABLES
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"  CHANGING
*"     REFERENCE(C_FILENAME) LIKE  REGUT-FSNAM
*"--------------------------------------------------------------------

data: begin of ls_101plus,
        21r_tag(5),
        21r_value(16),
      end   of ls_101plus.

ls_101plus-21r_tag = ':21R:'.
ls_101plus-21r_value = 'Just 21R test'.

*perform prepare_string_with_x_chars changing ls_101plus-21r_value.

*perform fill_output_table
*       using    ls_101plus
*       changing t_file_output[].

ENDFUNCTION.