************************************************************************
* Include FPAYM_TOP                                                    *
* Global Data Declarations                                             *
************************************************************************

REPORT sapfpaym
       LINE-SIZE 132
       MESSAGE-ID bfibl02
       NO STANDARD PAGE HEADING.


*- Function module name variable for illegal calls --------------------*
INCLUDE ifpaym_module_name.


*- Include for general data declarations ------------------------------*
INCLUDE <icon>.


*- Type Pools ---------------------------------------------------------*
TYPE-POOLS rsds.


*- Tables -------------------------------------------------------------*
TABLES:
  fpayh,
  fpayp,


*- Structures ---------------------------------------------------------*
  sscrfields.


*- Selection screen decalaration --------------------------------------*

*- Format ---
SELECTION-SCREEN SKIP.
SELECTION-SCREEN BEGIN OF BLOCK 1 WITH FRAME TITLE text-002.
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN:
  COMMENT 1(30) text-007 FOR FIELD par_form,
  POSITION pos_low.
PARAMETERS:
  par_form LIKE tfpm042f-formi OBLIGATORY,
  par_forp LIKE fpm_selpar-param NO-DISPLAY,
  par_fopc LIKE fpm_selpar-param NO-DISPLAY.
SELECTION-SCREEN
  PUSHBUTTON 76(04) ibutton USER-COMMAND info MODIF ID i.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN
  PUSHBUTTON 33(30) fbutton USER-COMMAND form MODIF ID f.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN END OF BLOCK 1.

*- Payment mediums and Lists ---
SELECTION-SCREEN BEGIN OF BLOCK 2 WITH FRAME TITLE text-001.

* Payment medium 1 (Paper)
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS:
  par_xpy1 LIKE tfpm042f-xpri1 MODIF ID py1,
  par_pri1 TYPE fpm_parcon NO-DISPLAY.
SELECTION-SCREEN:
  COMMENT 3(28) text_py1 FOR FIELD par_xpy1 MODIF ID py1,
  PUSHBUTTON 33(30) p1button USER-COMMAND pri1 MODIF ID py1.
SELECTION-SCREEN END OF LINE.

* Payment medium 3 (File)
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS:
  par_xpy3 LIKE tfpm042f-xdme1 MODIF ID py3,
  par_pri3 TYPE fpm_parcon NO-DISPLAY.
SELECTION-SCREEN:
  COMMENT 3(28) text_py3 FOR FIELD par_xpy3 MODIF ID py3,
  PUSHBUTTON 33(30) p3button USER-COMMAND pri3 MODIF ID py2.
SELECTION-SCREEN END OF LINE.

* Payment medium 5 (List)
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS:
  par_xpy5 LIKE tfpm042f-xlst1 MODIF ID py5,
  par_pri5 LIKE fpm_parcon NO-DISPLAY,
  par_arc5 LIKE fpm_parcon NO-DISPLAY.
SELECTION-SCREEN:
  COMMENT 3(28) text_py5 FOR FIELD par_xpy5 MODIF ID py5,
  PUSHBUTTON 33(30) p5button USER-COMMAND pri5 MODIF ID py5.
SELECTION-SCREEN END OF LINE.

* Accompanying list
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS:
  par_xlst LIKE fpm_selpar-xplst MODIF ID lst,
  par_pril LIKE fpm_parcon NO-DISPLAY MODIF ID lst,
  par_arcl LIKE fpm_parcon NO-DISPLAY MODIF ID lst.
SELECTION-SCREEN:
  COMMENT 3(28) text-012 FOR FIELD par_xlst MODIF ID lst,
  PUSHBUTTON 33(30) lbutton USER-COMMAND pril MODIF ID lst.
SELECTION-SCREEN END OF LINE.

* Error log
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS:
  par_xerr LIKE fpm_selpar-xperr,
  par_prie LIKE fpm_parcon NO-DISPLAY,
  par_arce LIKE fpm_parcon NO-DISPLAY.
SELECTION-SCREEN:
  COMMENT 03(28) text-013 FOR FIELD par_xerr,
  PUSHBUTTON 33(30) ebutton USER-COMMAND prie.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN END OF BLOCK 2.

*- Further file and form parameters ---
SELECTION-SCREEN BEGIN OF BLOCK 3 WITH FRAME TITLE text-003.

* File name
PARAMETERS:
  par_belp LIKE fpm_selpar-xbelp DEFAULT 'X',                  "n2783609
  p_bcmrsd TYPE xfeld NO-DISPLAY,    "Resend payment batch     "n2927769
  par_f11s TYPE xfeld NO-DISPLAY,    "wait if PAR_BELP = X     "n1922823
  par_xfil LIKE fpm_selpar-xpfil MODIF ID py4,
  par_both TYPE xtemse_and_file_fpm NO-DISPLAY MODIF ID py4,"nte1428908
  par_file LIKE fpm_selpar-pfile MODIF ID py4.

* Layout sets
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN:
  COMMENT 1(30) text_fp1 FOR FIELD par_fpy1 MODIF ID py1,
  POSITION pos_low.
PARAMETERS:
  par_fpy1 LIKE fpm_selpar-altform MODIF ID py1.
SELECTION-SCREEN:
  PUSHBUTTON 58(20) f1button USER-COMMAND scr1 MODIF ID py1.
SELECTION-SCREEN END OF LINE.

SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN:
  COMMENT 1(30) txt_pdf1 FOR FIELD par_pdf1 MODIF ID py1,
  POSITION pos_low.
PARAMETERS:
  par_pdf1 TYPE fpwbformname MODIF ID py1.
SELECTION-SCREEN END OF LINE.

* filler
PARAMETERS:
  par_fill TYPE filler_fpm MODIF ID py1.

*accompanying sheet
PARAMETERS:
  par_ftyp TYPE fpm_formtype
    AS LISTBOX VISIBLE LENGTH 12 USER-COMMAND form_type_changed MODIF ID py2,
  par_fpy3 LIKE fpm_selpar-altform MODIF ID py2.
SELECTION-SCREEN:
  PUSHBUTTON 58(20) f3button USER-COMMAND scr3 MODIF ID py2.
PARAMETERS:
  par_pdf3 TYPE fpwbformname MODIF ID py2.

* accompanying list
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN:
  COMMENT 1(30) text-017 FOR FIELD par_vari,
  POSITION pos_low.
PARAMETERS:
  par_vari LIKE disvariant-variant.
SELECTION-SCREEN POSITION 58.
PARAMETERS:
  par_scrn LIKE fpm_selpar-xscrn.
SELECTION-SCREEN:
  COMMENT 60(20) text-018 FOR FIELD par_scrn.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN END OF BLOCK 3.


*- Internal tables ----------------------------------------------------*
DATA:
  gt_fpayp        LIKE fpayp      OCCURS 0 WITH HEADER LINE,
  gt_tfpm042fm    LIKE tfpm042fm  OCCURS 0 WITH HEADER LINE,
  gt_tfpm042fmc   LIKE tfpm042fmc OCCURS 0 WITH HEADER LINE,
  gt_freesel      TYPE rsds_twhere,


*- Internal structures ------------------------------------------------*
  gs_prie         LIKE pri_params,                          "Error list
  gs_arce         LIKE arc_params,
  gs_pril         LIKE pri_params,     "Accompanying list
  gs_arcl         LIKE arc_params,
  gs_pri1         LIKE itcpo,          "Payment medium (1-5)
  gs_pri3         LIKE itcpo,
  gs_pri5         LIKE pri_params,
  gs_arc5         LIKE arc_params,
  gs_fpayh        LIKE fpayh,
  gs_dfpayg       LIKE dfpayg,
  gs_tfpm042f     LIKE tfpm042f,
  gs_tfpm042f_2   LIKE tfpm042f,
  gs_tfpm042ft    LIKE tfpm042ft,
  gs_tfpm042ff    LIKE tfpm042ff,
  gs_tfpm042ffc   LIKE tfpm042ffc,
  gs_tfpm042fd    LIKE tfpm042fd,
  gs_tfpm042fdc   LIKE tfpm042fdc,
  gs_variant      LIKE disvariant,

*- Help fields --------------------------------------------------------*
  gc_answer(1)    TYPE c,              "Answer of popups
  gc_text_py3     LIKE itcpo-tdtitle,
  gc_filesystem   TYPE dfilesyst,
  gc_extnumber    TYPE balnrext,
  gc_message_text1 LIKE sy-msgv1,
  gc_message_text2 LIKE sy-msgv2,
  gc_message_text3 LIKE sy-msgv3,
  gc_message_type  LIKE sy-msgty,
  gc_too_many_files TYPE BOOLE-BOOLE,

*- Flags --------------------------------------------------------------*
  gc_dd_prenotif  TYPE x_dd_prenotif,  "X direct debit prenotification
  gc_xfile        LIKE boole-boole,    "X file creation (DTTYP = 01)
  gc_xformf       LIKE boole-boole,    "Format popup button?
  gc_xforp        LIKE boole-boole,    "Format params maint?
  gc_xselect      LIKE boole-boole,    "Paym. data selected?
  gc_xpresrv      LIKE boole-boole,    "Pre-service called?


*- Constants without initial value ------------------------------------*
  gc_icon_form_ok(50) TYPE c,          "Format parameters
  gc_icon_form_no(50) TYPE c,
  gc_icon_prin_ok(50) TYPE c,          "Print parameters
  gc_icon_prin_no(50) TYPE c.