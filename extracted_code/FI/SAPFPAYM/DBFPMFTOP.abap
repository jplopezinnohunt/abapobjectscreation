*----------------------------------------------------------------------*
*      DATABASE PROGRAM OF LOGICAL DATABASE FPMF
*----------------------------------------------------------------------*
*
* The automatically generated subroutines (FORMs) are called by
* system routines. Therefore their names must not be changed!!!
*
* If the source code is automatically generated,
* please perform the following steps:
*
* 1. Replace ? by suitable ABAP statements.
* 2. Activate ABAP statements (delete stars).
* 3. Check syntax of database program.
* 4. Save source code.
*    SELECT-OPTIONS and PARAMETERS will be checked automatically.
*----------------------------------------------------------------------*

*----------------------------------------------------------------------*
* Performance notes
*----------------------------------------------------------------------*
* General information about the use of logical databases is contained
* in the extended help information of transaction SE36.
* Please consider in particular the following aspects:
*
* 1. Use of internal tables:
*    SELECT * FROM table INTO TABLE i_table WHERE ... .
*    LOOP AT i_table.
*      MOVE-CORRESPONDING i_table TO table.
*      PUT table.
*    ENDLOOP.
* 2. Use of OPEN/FETCH CURSOR for nested structures.
* 3. Use of dynamic selections to enable further selection criteria
*    (cf. documentation of SELECTION-SCREEN DYNAMIC SELECTIONS).
* 4. Use of field selection to enable get fields statement in reports
*    (cf. documentation of SELECTION-SCREEN FIELD SELECTION).
* 5. Authority checks already at PAI of selection screen.
*----------------------------------------------------------------------*

PROGRAM SAPDBFPMF DEFINING DATABASE FPMF.
INCLUDE IFPAYM_MODULE_NAME.

TABLES : FPAYH,
         FPAYP.


* data: ...          "user defined variables
data lt_fpayp like table of fpayp with header line.