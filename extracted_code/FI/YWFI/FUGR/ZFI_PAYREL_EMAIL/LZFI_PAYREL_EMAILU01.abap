*---------------------------------------------------------------------*
*    program for:   TABLEFRAME_ZFI_PAYREL_EMAIL
*   generation date: 03.12.2010 at 09:51:38 by user D_CROUZET
*   view maintenance generator version: #001407#
*---------------------------------------------------------------------*
FUNCTION TABLEFRAME_ZFI_PAYREL_EMAIL   .
  PERFORM TABLEFRAME TABLES X_HEADER X_NAMTAB DBA_SELLIST DPL_SELLIST
                            EXCL_CUA_FUNCT
                     USING  CORR_NUMBER VIEW_ACTION VIEW_NAME.
ENDFUNCTION.