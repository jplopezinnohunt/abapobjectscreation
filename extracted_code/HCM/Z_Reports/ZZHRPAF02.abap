REPORT zzhrpaf02 MESSAGE-ID hrpaysi.
**********************************************************************
* CHANGE HISTORY
*--------------------------------------------------------------------*
* Date       By           Brief Description & Release
*--------------------------------------------------------------------*
* 15/11/2007 D.Andros     First delivery.
*
*
*
*
**********************************************************************
TABLES: pcl1, pcl2, tcurx.
INFOTYPES:  0000,"..Events..............
            0001,"..Organiz. assignment.
            0002,"..Personal data.......
*            0003,"..Payroll status......
            0006,"..Addresses...........
            0007,"..Work times..........
            0008,"..Basic pay...........
*            0009,"..Bank connection.....
*            0011,"..Ext. bank transfers.
*            0012,"......................
*            0013,"......................
            0014,"..Recurr. paym/deduct
            0015,"..Additional payment..
            0016,"..Contract elements...
*            0017,"..Travel privileges...
*            0019,"......................
            0021,"..Family Member/Depnds.
*            0022,"......................
*            0023,"......................
*            0024,"......................
*            0025,"......................
*            0027,"......................
*            0028,"......................
*            0030,"......................
*            0031,"......................
*            0032,"......................
*            0033,"......................
*            0034,"......................
*            0035,"......................
*            0037,"......................
*            0040,"......................
            0041,"..Date Specifications.
*            0045,"......................
*            0050,"......................
*            0054,"......................
*            0057,"......................
*            0064,"......................
*            0077,"......................
*            0078,"......................
*            0080,"......................
*            0081,"......................
*            0082,"......................
*            0083,"......................
*            0094,"......................
            0105,"..Communication.......
*            0165,"......................
            0167,"..Health Plans........
*            0168,"......................
*            0169,"......................
*            0171,"......................
*            0185,"......................
*            0262,"......................
*            0278,"......................
*            0279,"......................
            0302,"..Additional Actions..
*            0304,"......................
            0351,"..Country Information.
*            0374,"......................
*            0376,"......................
*            0377,"......................
*            0378,"......................
            0395,"..External Org. Asnmt.
*            0416,"......................
*            0487,"......................
            0509,"..SPA.................
*            0703,"......................
*            0704,"......................
*            0710,"......................
*            0712,"......................
*            0715,"......................
*            0959,"......................
            0960,"..NPO M&H Allowance...
            0961,"..NPO Pension Fund....
            0962."..NPO Rental Subsidy..
*            2001,"......................
*            2003,"......................
*            2006,"......................
*            2010,"......................
*            2013."..Quota Corrections...
NODES:  pernr.
*--------------------------------------------------------------------*
* Includes required for cluster read
*--------------------------------------------------------------------*
* Data Definition for CD Cluster
INCLUDE rpc2cd09.
* Cluster CA Data-Definition
INCLUDE rpc2ca00.
* Data Definition for PCL1 and PCL2 Buffer
INCLUDE rpppxd00.
* Data Definition for PCL1, PCL2 Buffer Handler
INCLUDE rpppxd10.
*
INCLUDE rpc2rx02.
* Data description for cluster RX (international, version 9) part 1
INCLUDE rpc2rx29.
*
INCLUDE rpc2rx39.
* UN related
INCLUDE hunpaymacro.
* UN related
INCLUDE pc2rxun0.
*--------------------------------------------------------------------*
* Types
*--------------------------------------------------------------------*
TYPE-POOLS: slis. "Global data for ALV
TYPES:
  BEGIN OF t_dataline,
    f1  TYPE char80,
    f2  TYPE char80,
    f3  TYPE char80,
    f4  TYPE char80,
    f5  TYPE char80,
    f6  TYPE char80,
    f7  TYPE char80,
    f8  TYPE char80,
    f9  TYPE char80,
    f1t TYPE char50,
    f2t TYPE char50,
    cdt TYPE char10, "Contract expiry date
    f3t TYPE char50,
    f4t TYPE char10,
    f4l TYPE char50, "Date of the next increment
    wst TYPE char10,
    wsl TYPE char50, "Work schedule
    f5t TYPE char50,
    nsl TYPE char100, "Net base salary
    f6t TYPE char30,
    f6l TYPE char100,
    f7t TYPE char50,
    f7l TYPE char100, "Post adjustment line
    f8t TYPE char30,
    mhl TYPE char200, "M&H allowance line
    aht TYPE char50,  "Additional hardship allowance
    aha TYPE char100,
    nft TYPE char50,  "Non family service allowance
    nfs TYPE char100,
    lat TYPE char50,  "First lang. allowance
    lal TYPE char100,
    sdt TYPE char50,
    sdl TYPE char100,
    fd  TYPE char30,
    fi  TYPE char30,
    usr TYPE char20,  "User name
    pfn TYPE char20,  "UNPF no
    gst TYPE char50,  "Gross base salary
    gsl TYPE char100,
    cat TYPE char50,  "Family allowance - children
    cal TYPE char100,
    rnt TYPE char50,  "Rental subsidy
    rnl TYPE char100,
    spt TYPE char50,  "Family allowance - spouse
    spl TYPE char100,
    sut TYPE char50,  "Family allowance - spouse differential
    sud TYPE char100,
    pct TYPE char50,  "Pension contribution
    pcl TYPE char100,
    mft TYPE char50,  "MBF contribution
    mfl TYPE char100,
    ost TYPE char50,  "Other source allowance
    osl TYPE char100,
    fst TYPE char50,  "Family source CAFallowance
    fsl TYPE char100,
    cst TYPE char50,  "Family allowance CAF Special
    csl TYPE char100,
    odt TYPE char50,  "Difference between Children Allowance and OSAL
    odl TYPE char100,
    nrt TYPE char50,  "Not resident's allowance
    nrl TYPE char100,
    slt TYPE char50,  "Second lang. allowance
    sll TYPE char100,
    set TYPE char50,  "Service allowance
    sel TYPE char100,
    fmt TYPE char50,  "Family allowance
    fml TYPE char100,
    rpt TYPE char50,  "Representation allowance
    rpl TYPE char100,
    trt TYPE char50,  "Transportation allowance
    trl TYPE char100,
    snt TYPE char50,  "Spec. non-pens. allowance
    snl TYPE char100,
    ptt TYPE char50,  "Personal transitional allowance
    ptl TYPE char100,
    agt TYPE char50,  "Assignment grant (DSA)
    agl TYPE char100,
    alt TYPE char50,  "Assignment grant (lump sum)
    all TYPE char100,
    sit TYPE char50,  "Settling in grant (DSA)
    sid TYPE char100,
    sgt TYPE char50,  "Settling in grant (lump sum)
    sgl TYPE char100,
    rgt TYPE char50,  "Repatriation grant
    rgl TYPE char100,
    tit TYPE char50,  "Termination indemnity
    til TYPE char100,
    dgt TYPE char50,  "Death grant
    dgl TYPE char100,
    ilt TYPE char50,  "In lieu of notice
    ill TYPE char100,
    ant TYPE char50,  "Annual leave statment
    anl TYPE char100,
    nnt TYPE char50,  "Annual leave statment - Negative
    nnl TYPE char100,
    hdt TYPE char50,  "Hairdressing indemnity
    hdl TYPE char100,
    clt TYPE char50,  "Closing allowance
    cll TYPE char100,
    pat TYPE char50,  "Spec. post allowance
    pal TYPE char100,
    smt TYPE char50,  "Separation indemnity (m)
    sml TYPE char100,
    swt TYPE char50,  "Separation indemnity (w)
    swl TYPE char100,
    ext TYPE char50,  "Except. separ. payt. temp
    exl TYPE char100,
    aft TYPE char50,  "Agency fees
    afe TYPE char100,
    dht TYPE char50,  "Deduction for housing provided
    dhl TYPE char100,
    ddt TYPE char50,  "Deduction Disability Benefit
    ddl TYPE char50,
    sst TYPE char50,  "Social security
    ssl TYPE char100,
    let TYPE char50,  "Lloyds Temporary EE
    lel TYPE char100,
    lft TYPE char50,  "Lloyds Temp Field EE
    lfl TYPE char100,
    r1t TYPE char50,  "Remb Pension SLWOP Staff
    r1l TYPE char100,
    bda TYPE char10,  "Birthdate
    ima TYPE char80,  "internal mailing address
    udt TYPE char10,  "UNESCO entry date
    unt TYPE char10,  "UN entry date
    dst TYPE char50,  "Duty station
    adt TYPE char50,  "Adm. duty station
    out TYPE char50,  "Org. unit
    pnt TYPE char25,  "Post number
    at1 TYPE char200, "Automatic text
    at2 TYPE char200, "Automatic text
    at3 TYPE char200, "Automatic text
    at4 TYPE char200, "Automatic text
    pdn TYPE char25,  "PAF document number
    pdr TYPE char10,  "PAF document revision
    ema TYPE char50,  "e-mail address
    mst TYPE char10,  "marital status
  END OF t_dataline.
TYPES: BEGIN OF t_dataline_new,
         f1  TYPE char80,
         f2  TYPE char80,
         f3  TYPE char80,
         f4  TYPE char80,
         f5  TYPE char80,
         f6  TYPE char80,
         f7  TYPE char80,
         f8  TYPE char80,
         f9  TYPE char80,
         f1t TYPE char50,
         f2t TYPE char50,
         cdt TYPE char10, "Contract expiry date
         f3t TYPE char50,
         f4t TYPE char10,
         f4l TYPE char50, "Date of the next increment
         wst TYPE char10,
         wsl TYPE char50, "Work schedule
         f5t TYPE char50,
         nsl TYPE char100, "Net base salary
         f6t TYPE char30,
         f6l TYPE char100,
         f7t TYPE char50,
         f7l TYPE char100, "Post adjustment line
         f8t TYPE char30,
         mhl TYPE char200, "M&H allowance line
         aht TYPE char50,  "Additional hardship allowance
         aha TYPE char100,
         nft TYPE char50,  "Non family service allowance
         nfs TYPE char100,
         lat TYPE char50,  "First lang. allowance
         lal TYPE char100,
         sdt TYPE char50,
         sdl TYPE char100,
         fd  TYPE char30,
         fi  TYPE char30,
         usr TYPE char20,  "User name
         pfn TYPE char20,  "UNPF no
         gst TYPE char50,  "Gross base salary
         gsl TYPE char100,
         cat TYPE char50,  "Family allowance - children
         cal TYPE char100,
         rnt TYPE char50,  "Rental subsidy
         rnl TYPE char100,
         spt TYPE char50,  "Family allowance - spouse
         spl TYPE char100,
         sut TYPE char50,  "Family allowance - spouse differential
         sud TYPE char100,
         pct TYPE char50,  "Pension contribution
         pcl TYPE char100,
         mft TYPE char50,  "MBF contribution
         mfl TYPE char100,
         ost TYPE char50,  "Other source allowance
         osl TYPE char100,
         fst TYPE char50,  "Family source CAFallowance
         fsl TYPE char100,
         cst TYPE char50,  "Family allowance CAF Special
         csl TYPE char100,
         odt TYPE char50,  "Difference between Children Allowance and OSAL
         odl TYPE char100,
         nrt TYPE char50,  "Not resident's allowance
         nrl TYPE char100,
         slt TYPE char50,  "Second lang. allowance
         sll TYPE char100,
         set TYPE char50,  "Service allowance
         sel TYPE char100,
         fmt TYPE char50,  "Family allowance
         fml TYPE char100,
*AAHOUNOU25012017
         ftt TYPE char50,  "Family allowance Transition
         ftl TYPE char100,
         fct TYPE char50,  "Family allowance Single Parent
         fcl TYPE char100,
*AAHOUNOU25012017
         rpt TYPE char50,  "Representation allowance
         rpl TYPE char100,
         trt TYPE char50,  "Transportation allowance
         trl TYPE char100,
         snt TYPE char50,  "Spec. non-pens. allowance
         snl TYPE char100,
         ptt TYPE char50,  "Personal transitional allowance
         ptl TYPE char100,
         agt TYPE char50,  "Assignment grant (DSA)
         agl TYPE char100,
         alt TYPE char50,  "Assignment grant (lump sum)
         all TYPE char100,
         sit TYPE char50,  "Settling in grant (DSA)
         sid TYPE char100,
         sgt TYPE char50,  "Settling in grant (lump sum)
         sgl TYPE char100,
         rgt TYPE char50,  "Repatriation grant
         rgl TYPE char100,
         tit TYPE char50,  "Termination indemnity
         til TYPE char100,
         dgt TYPE char50,  "Death grant
         dgl TYPE char100,
         ilt TYPE char50,  "In lieu of notice
         ill TYPE char100,
         ant TYPE char50,  "Annual leave statment
         anl TYPE char100,
         nnt TYPE char50,  "Annual leave statment - Negative
         nnl TYPE char100,
         hdt TYPE char50,  "Hairdressing indemnity
         hdl TYPE char100,
         clt TYPE char50,  "Closing allowance
         cll TYPE char100,
         pat TYPE char50,  "Spec. post allowance
         pal TYPE char100,
         smt TYPE char50,  "Separation indemnity (m)
         sml TYPE char100,
         swt TYPE char50,  "Separation indemnity (w)
         swl TYPE char100,
         ext TYPE char50,  "Except. separ. payt. temp
         exl TYPE char100,
         aft TYPE char50,  "Agency fees
         afe TYPE char100,
         dht TYPE char50,  "Deduction for housing provided
         dhl TYPE char100,
         ddt TYPE char50,  "Deduction Disability Benefit
         ddl TYPE char50,
         sst TYPE char50,  "Social security
         ssl TYPE char100,
         let TYPE char50,  "Lloyds Temporary EE
         lel TYPE char100,
         lft TYPE char50,  "Lloyds Temp Field EE
         lfl TYPE char100,
         r1t TYPE char50,  "Remb Pension SLWOP Staff
         r1l TYPE char100,
         bda TYPE char10,  "Birthdate
         ima TYPE char80,  "internal mailing address
         udt TYPE char10,  "UNESCO entry date
         unt TYPE char10,  "UN entry date
         dst TYPE char50,  "Duty station
         adt TYPE char50,  "Adm. duty station
         out TYPE char50,  "Org. unit
         pnt TYPE char25,  "Post number
         at1 TYPE char200, "Automatic text
         at2 TYPE char200, "Automatic text
         at3 TYPE char200, "Automatic text
         at4 TYPE char200, "Automatic text
         pdn TYPE char25,  "PAF document number
         pdr TYPE char10,  "PAF document revision
         ema TYPE char50,  "e-mail address
         mst TYPE char10,  "marital status
         foo TYPE char250, "footer   "EVOFGU08102019
       END OF t_dataline_new.
TYPES: BEGIN OF t_sbj,
         sbj TYPE char80.
TYPES: END OF t_sbj.
TYPES: BEGIN OF t_emp.
    INCLUDE STRUCTURE hrms_biw_io_occupancy.
TYPES: massn      TYPE massn,
       massg      TYPE massg,
       massn_text TYPE mntxt,
       massg_text TYPE mgtxt,
       effdate    TYPE dats,
       period     TYPE faper,
       sprsl      TYPE sprsl,
       sel_type   LIKE yhr_pafnum-actty,
       nchild(2)  TYPE c,
       itype(4)   TYPE c,
       apznr      TYPE apznr.
TYPES: END OF t_emp.
*--------------------------------------------------------------------*
* Constants
*--------------------------------------------------------------------*
CONSTANTS:
  gc_htab TYPE string
          VALUE cl_abap_char_utilities=>horizontal_tab,
  gc_vtab TYPE string
          VALUE cl_abap_char_utilities=>vertical_tab,
  gc_newl TYPE string
          VALUE cl_abap_char_utilities=>newline,
  gc_crlf TYPE string
          VALUE cl_abap_char_utilities=>cr_lf.
CONSTANTS:
  $tabparams TYPE string VALUE 'YPAF001T',
  $tabwtypes TYPE string VALUE 'YPAF002T'.
CONSTANTS:
  $ok    TYPE string VALUE '1',
  $empty TYPE string VALUE '',
  $cross TYPE string VALUE 'X'.
CONSTANTS:
  $nodebug(1)      TYPE c VALUE '0',
  $noworddoc(1)    TYPE c VALUE '1',
  $nosimulation(1) TYPE c VALUE '2'.
CONSTANTS:
* ALV background
    gc_background_id TYPE bds_typeid VALUE 'PMMN_BACKGROUND'.
CONSTANTS:
    gc_payroll_area  LIKE t549a-abkrs VALUE 'UN'.
CONSTANTS:
* values of those constants should not be changed;
* they have to be in this order to preserve consistency
* with data produced by old paf application;
* they are used in sequential paf number generator mechanism;
  $byact TYPE aetyp VALUE '01',
  $mobha TYPE aetyp VALUE '02',
  $rsgrt TYPE aetyp VALUE '03',
*    $RSSUS    type AETYP value '04',
  $healt TYPE aetyp VALUE '05',
  $pedat TYPE aetyp VALUE '06',
  $contr TYPE aetyp VALUE '07',
*    $EXTEN    type AETYP value '08',
  $fmall TYPE aetyp VALUE '09',
  $bspay TYPE aetyp VALUE '10',
  $coinf TYPE aetyp VALUE '11',
  $spa   TYPE aetyp VALUE '12',
  $pefnd TYPE aetyp VALUE '13',
  $post  TYPE aetyp VALUE '14',
  $paie  TYPE aetyp VALUE '15',
  $recur TYPE aetyp VALUE '16'.
CONSTANTS:
  $mindate       TYPE dats  VALUE '18000101',
  $maxdate       TYPE dats  VALUE '99991231',
  $minpayd       TYPE dats  VALUE '20070101',
  $changepafdate TYPE dats VALUE '20161231'.
*--------------------------------------------------------------------*
* Data
*--------------------------------------------------------------------*
DATA: gt_emp TYPE STANDARD TABLE OF t_emp INITIAL SIZE 0,
      gd_emp TYPE t_emp.
DATA: gt_sbj       TYPE STANDARD TABLE OF t_sbj WITH HEADER LINE INITIAL SIZE 3,
      gt_lines     TYPE TABLE OF string,
      gt_lines_new TYPE TABLE OF string.
DATA: gd_fname(200)  TYPE c,
      gd_fpath(200)  TYPE c VALUE 'C:\Temp',
      gd_fpatha(200) TYPE c,
      gd_fprint(1)   TYPE c VALUE ' '.
DATA: gd_buffer  TYPE char100,
*      gd_texts   TYPE string  VALUE 'YHR_PAFTXT',
      gt_results TYPE STANDARD TABLE OF zhrpyres.
DATA: gd_salperiod    TYPE i VALUE 12.
DATA: BEGIN OF gt_error OCCURS 0,
        msgtext(200) TYPE c,
      END OF gt_error.
DATA: gd_payroll_variant LIKE rsvar-variant,
      gd_payroll_name    LIKE rsvar-report.
* global flags
DATA: gf_anls_is_negative(1)   TYPE c VALUE '',
      gf_rnts_is_suppressed(1) TYPE c VALUE '',
      gf_mhal_is_suppressed(1) TYPE c VALUE '',
      gf_spal_is_last_recrd(1) TYPE c VALUE '',
      gf_itype_found(1)        TYPE c VALUE '',
      gf_x1x2xa(1)             TYPE c VALUE '',
      gf_dbglvl(1)             TYPE c VALUE '0'.
*--------------------------------------------------------------------*
* Selection screen
*--------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK mainpar WITH FRAME TITLE TEXT-003.
PARAMETERS:
* Action
  gp_byact RADIOBUTTON GROUP rtyp,
* Personal Data
  gp_pedat RADIOBUTTON GROUP rtyp,
* Allowances in Basic Pay
  gp_bspay RADIOBUTTON GROUP rtyp,
* Family Allowances
  gp_fmall RADIOBUTTON GROUP rtyp,
* Health Plans
  gp_healt RADIOBUTTON GROUP rtyp,
* Country Information
  gp_coinf RADIOBUTTON GROUP rtyp,
* SPA
  gp_spa   RADIOBUTTON GROUP rtyp,
* M&H
  gp_mobha RADIOBUTTON GROUP rtyp,
* Pension Fund
  gp_pefnd RADIOBUTTON GROUP rtyp,
* Rental Subsidy Grant/Change
  gp_rsgrt RADIOBUTTON GROUP rtyp,
* Post
  gp_post  RADIOBUTTON GROUP rtyp,
* Additional Payments
  gp_paie  RADIOBUTTON GROUP rtyp,
* Recurring Payments/Deductions
  gp_recur RADIOBUTTON GROUP rtyp.
SELECTION-SCREEN END OF BLOCK mainpar.
SELECTION-SCREEN BEGIN OF BLOCK addpar WITH FRAME.
PARAMETERS:
  gp_nwrev   AS CHECKBOX DEFAULT space.
SELECTION-SCREEN END OF BLOCK addpar.
* User running report
PARAMETERS:
  gp_usrid   TYPE c LENGTH 30 DEFAULT sy-uname NO-DISPLAY
                    VISIBLE LENGTH 30 LOWER CASE.
* Message Level
PARAMETERS:
  gp_msg(1)  TYPE n DEFAULT 0 NO-DISPLAY.
*....................................................................*
*   at selection-screen
*....................................................................*
AT SELECTION-SCREEN.
  IF pnppernr[] IS INITIAL.
    MESSAGE e016 WITH 'Enter a Personnel Number'.
  ENDIF.
*....................................................................*
*   initialization
*....................................................................*
INITIALIZATION.
*..only active employees.
*..this puts default value on PNP selection screen
*..-> employment status not equal 0
*  RP-SEL-EIN-AUS-INIT.
*....................................................................*
*   start-of-selection
*....................................................................*
START-OF-SELECTION.
* create variables TRUE and FALSE
  rp-def-boolean.
* Get path for Word Template
*AAHOUNOU25012017
*  PERFORM z_get_value USING 'FILETEMPLATE' CHANGING gd_buffer.
*  gd_fname = gd_buffer.
* utilisation de la transaction FILE pour identifier le modele
* dans le form START_WORD
* BEG FGU 15012020
*  IF pn-begda LE  $changepafdate.
*    PERFORM z_get_value USING 'FILETEMPLATE' CHANGING gd_buffer.
*    gd_fname = gd_buffer.
*  ELSE.
*    IF sy-sysid = 'P01'.
*      PERFORM z_get_value USING 'FILETEMPLATENEW_PRD' CHANGING gd_buffer.
*    ELSE.
*      PERFORM z_get_value USING 'FILETEMPLATENEW_OTH' CHANGING gd_buffer.
*    ENDIF.
*    gd_fname = gd_buffer.
*  ENDIF.
* END FGU 15012020
*AAHOUNOU25012017
* Get texts table name
*  BEG FGU 150120 : ça ne sert strictement à rien d'aller chercher un nom de table d
* la table des textes est la table : YHR_PAFTXT
*  PERFORM z_get_value USING 'TEXTTABLE' CHANGING gd_buffer.
*  gd_texts = gd_buffer.
* END FGU 150120
* Get debug level
  PERFORM z_get_value USING 'DEBUGLEVEL' CHANGING gd_buffer.
  gf_dbglvl = gd_buffer.
* BEG FGU 150120
* ça ne sert à rien d'aller chercher le nom du moteur de paie dans une table
* puisque c'est toujours le programme  ZUNCALC0 !!!!
* Get payroll calculator name
*  PERFORM z_get_value USING 'RPCALC' CHANGING gd_buffer.
*  gd_payroll_name = gd_buffer.
  gd_payroll_name  = 'ZUNCALC0'.
* Get payroll calculator variant
* la variante n'est pas utilisée !
*  PERFORM z_get_value USING 'RPCALC_VAR' CHANGING gd_buffer.
*  gd_payroll_variant = gd_buffer.
* END FGU 150120
  CLEAR gd_emp.
GET pernr.
*...Get communication language
  rp_provide_from_last p0002 space pn-begda pn-endda.
  MOVE p0002-sprsl TO gd_emp-sprsl.
*...Changes in Actions...............................................*
  IF NOT gp_byact IS INITIAL.
    DATA: w_text1 TYPE string,
          w_text2 TYPE string.
* check record
    CLEAR p0000.
    PERFORM z_proc_log USING '0000' pernr-pernr pn-begda.
    rp-provide-from-last p0000 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0000-begda.
* adjust effective date
    IF   p0000-massn EQ 'X1' " Separation
      OR p0000-massn EQ 'X2' " Retirement
      OR p0000-massn EQ 'XA'." Separation - Re-Hiring
* in order to get correct figures payroll simulation
* must be run for the month preceding the separation
      MOVE $cross TO gf_x1x2xa.
      IF p0000-massn EQ 'X1' OR p0000-massn EQ 'X2'.
        SUBTRACT 1 FROM gd_emp-effdate.
      ENDIF.
    ENDIF.
* push main action type and reason for action
* to global employee record
    MOVE p0000-massn TO gd_emp-massn.
    MOVE p0000-massg TO gd_emp-massg.
* check whether an additional action exists for main action
    rp-provide-from-last p0302 space gd_emp-effdate gd_emp-effdate.
    IF pnp-sw-found EQ $ok.
* scroll through additional actions to get texts
* we can add up to 3 actions
      LOOP AT p0302 WHERE begda LE gd_emp-effdate
                      AND endda GE gd_emp-effdate.
        PERFORM z_proc_txt_massng USING p0302-massn
                                        p0302-massg
                                        gd_emp-sprsl
                               CHANGING w_text1
                                        w_text2.
        CONCATENATE w_text1 '/' w_text2 INTO gt_sbj-sbj.
        APPEND gt_sbj.
      ENDLOOP.
    ELSE.
* get text for the main action
      PERFORM z_proc_txt_massng USING p0000-massn
                                      p0000-massg
                                      gd_emp-sprsl
                             CHANGING w_text1
                                      w_text2.
      CONCATENATE w_text1 '/' w_text2 INTO gt_sbj-sbj.
      APPEND gt_sbj.
* push texts for main action into fields of global employee record
      MOVE w_text1 TO gd_emp-massn_text.
      MOVE w_text2 TO gd_emp-massg_text.
    ENDIF.
* add blank lines to subject table
    DO.
      IF lines( gt_sbj ) GE 3. EXIT. ENDIF.
      APPEND INITIAL LINE TO gt_sbj.
    ENDDO.
* set selection criteria type
    gd_emp-sel_type = $byact.
  ENDIF.
*..............Personal Data.........................................*
  IF NOT gp_pedat IS INITIAL.
* check record
    CLEAR p0002.
    PERFORM z_proc_log USING '0002' pernr-pernr pn-begda.
    rp-provide-from-last p0002 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0002-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A06'.
* set selection criteria type
    gd_emp-sel_type = $pedat.
  ENDIF.
*..............Allowances in Basic Pay...............................*
  IF NOT gp_bspay IS INITIAL.
* check record
    CLEAR p0008.
    PERFORM z_proc_log USING '0008' pernr-pernr pn-begda.
    rp-provide-from-last p0008 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0008-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A09'.
* set selection criteria type
    gd_emp-sel_type = $bspay.
  ENDIF.
*..............Family Allowances......................................*
* business rule:
* There could be two records for same dependent -> one is to register
* a dependent and to grant allowances from the 1st of next
* month up to 31.12.9999; and the second is to cancel allowances
* for ongoing month. RP-PROVIDE-FROM-LAST P0021 SPACE PN-BEGDA PN-ENDDA
* will not work because 31.12.9999 is used and macro will return
* the first record with endda = maxdate
  IF NOT gp_fmall IS INITIAL.
* check record
    CLEAR p0021.
    PERFORM z_proc_log USING '0021' pernr-pernr pn-begda.
    CHECK lines( p0021 ) GT 0.
* get last record using key date
    PERFORM z_get_0021 USING pn-begda $empty space.
* set rules for current section
    gd_emp-effdate = p0021-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A08'.
* set selection criteria type
    gd_emp-sel_type = $fmall.
  ENDIF.
*..............Health Plans..........................................*
  IF NOT gp_healt IS INITIAL.
* check record
    CLEAR p0167.
    PERFORM z_proc_log USING '0167' pernr-pernr pn-begda.
    rp-provide-from-last p0167 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0167-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A05'.
* set selection criteria type
    gd_emp-sel_type = $healt.
  ENDIF.
*..............Country Information...................................*
  IF NOT gp_coinf IS INITIAL.
* check record
    CLEAR p0351.
    PERFORM z_proc_log USING '0351' pernr-pernr pn-begda.
    rp-provide-from-last p0351 'HOME' pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0351-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A10'.
* set selection criteria type
    gd_emp-sel_type = $coinf.
  ENDIF.
*..............SPA...................................................*
* normally changes in spa are managed via actions, but there where
* some cases during data migration when changes where made directly
* through PA30; to handle those cases following rule must be applied;
  IF NOT gp_spa IS INITIAL.
* check record
    CLEAR p0509.
    PERFORM z_proc_log USING '0509' pernr-pernr pn-begda.
    rp-provide-from-last p0509 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    PERFORM z_get_0509_check CHANGING gf_spal_is_last_recrd.
    IF p0509-endda NE $maxdate
       AND gf_spal_is_last_recrd EQ $cross.
      gd_emp-effdate = p0509-endda + 1.
      SELECT SINGLE atext FROM yhr_paftxt
                          INTO gt_sbj-sbj
                         WHERE spras EQ gd_emp-sprsl
                           AND txkey EQ 'A12'. " Suppression
    ELSE.
      gd_emp-effdate = p0509-begda.
      SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A11'. " Grant/Change
    ENDIF.
* set selection criteria type
    gd_emp-sel_type = $spa.
  ENDIF.
*..............Mobility & Hardship...................................*
* bus.rule -> effective date has to be the key date
* this will allow to run py.sim without having changes in IT960
  IF NOT gp_mobha IS INITIAL.
* check record
    CLEAR p0960.
    PERFORM z_proc_log USING '0960' pernr-pernr pn-begda.
    CHECK lines( p0960 ) GT 0.
* set key date as effective date
    gd_emp-effdate = pn-begda.
* get screen fields of IT0960
    PERFORM z_get_0960.
    IF gf_mhal_is_suppressed EQ $cross.
* MHAL suppression
      SELECT SINGLE atext FROM yhr_paftxt
                          INTO gt_sbj-sbj
                         WHERE spras EQ gd_emp-sprsl
                           AND txkey EQ 'A16'.
    ELSE.
* MHAL grant/change
      SELECT SINGLE atext FROM yhr_paftxt
                          INTO gt_sbj-sbj
                         WHERE spras EQ gd_emp-sprsl
                           AND txkey EQ 'A02'.
    ENDIF.
* set selection criteria type
    gd_emp-sel_type = $mobha.
  ENDIF.
*..............Pension Fund..........................................*
  IF NOT gp_pefnd IS INITIAL.
* check record
    CLEAR p0961.
    PERFORM z_proc_log USING '0961' pernr-pernr pn-begda.
    rp-provide-from-last p0961 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0961-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A13'.
* set selection criteria type
    gd_emp-sel_type = $pefnd.
  ENDIF.
*..............Rental Subsidy........................................*
* for this specific case it was agreed that we'll use
* key date as effective date; this will allow to run payroll sim.
* in the future; or without having effective infotype changes.
  IF NOT gp_rsgrt IS INITIAL.
* check record
    CLEAR p0962.
    PERFORM z_proc_log USING '0962' pernr-pernr pn-begda.
    CHECK lines( p0962 ) GT 0.
* set effective date
    gd_emp-effdate = pn-begda. " key date
* get last record and define whether or not display RNTS
    PERFORM z_get_0962.
    IF gf_rnts_is_suppressed EQ $cross.
* RNTS suppression
      SELECT SINGLE atext FROM yhr_paftxt
                          INTO gt_sbj-sbj
                         WHERE spras EQ gd_emp-sprsl
                           AND txkey EQ 'A04'. " Suppression
    ELSE.
* RNTS grant/change
      SELECT SINGLE atext FROM yhr_paftxt
                          INTO gt_sbj-sbj
                         WHERE spras EQ gd_emp-sprsl
                           AND txkey EQ 'A03'. " Grant/Change
    ENDIF.
* set selection criteria type
    gd_emp-sel_type = $rsgrt.
  ENDIF.
*..............Post..................................................*
  IF NOT gp_post IS INITIAL.
* check record
    CLEAR p0001.
    PERFORM z_proc_log USING '0001' pernr-pernr pn-begda.
    rp-provide-from-last p0001 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0001-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A14'.
* set selection criteria type
    gd_emp-sel_type = $post.
  ENDIF.
*..............Additional Payments...................................*
  IF NOT gp_paie IS INITIAL.
* check record
    CLEAR p0015.
    PERFORM z_proc_log USING '0015' pernr-pernr pn-begda.
    rp-provide-from-last p0015 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0015-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A17'.
* set selection criteria type
    gd_emp-sel_type = $paie.
  ENDIF.
*..............Recurring Payments/Deductions........................*
  IF NOT gp_recur IS INITIAL.
* check record
    CLEAR p0014.
    PERFORM z_proc_log USING '0014' pernr-pernr pn-begda.
    rp-provide-from-last p0014 space pn-begda pn-endda.
    IF NOT pnp-sw-found EQ $ok. REJECT. ENDIF.
* set rules for current section
    gd_emp-effdate = p0014-begda.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO gt_sbj-sbj
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'A18'.
* set selection criteria type
    gd_emp-sel_type = $recur.
  ENDIF.
* If we come here it means that an InfoType was found
  MOVE $cross TO gf_itype_found.
* Get latest records
  rp_provide_from_last p0000 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0001 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0002 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0006 '6'    gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0007 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0008 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0015 '1610' gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0016 space  gd_emp-effdate gd_emp-effdate.
* get number of dependent children
  PERFORM z_get_0021 USING gd_emp-effdate '14' '2'.
*  RP_PROVIDE_FROM_LAST P0021 '14'   GD_EMP-EFFDATE GD_EMP-EFFDATE.
*  RP_PROVIDE_FROM_LAST P0041 SPACE  GD_EMP-EFFDATE GD_EMP-EFFDATE.
  rp_provide_from_last p0041 space  pn-begda pn-endda.
  rp_provide_from_last p0105 '0010' gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0167 'MBF0' gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0351 'HOME' gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0395 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0509 space  gd_emp-effdate gd_emp-effdate.
  rp_provide_from_last p0961 space  gd_emp-effdate gd_emp-effdate.
* get last record and define whether to display or not RNTS
  PERFORM z_get_0962.
* Collect data for employee summary
  MOVE-CORRESPONDING p0000 TO gd_emp.
  MOVE-CORRESPONDING p0001 TO gd_emp.
  MOVE-CORRESPONDING p0007 TO gd_emp.
  MOVE-CORRESPONDING p0008 TO gd_emp.
* Get country grouping
  SELECT SINGLE molga
           FROM t001p
           INTO gd_emp-molga
          WHERE werks EQ p0001-werks AND
                btrtl EQ p0001-btrtl.
* Get hire date
  CALL FUNCTION 'HR_ENTRY_DATE'
    EXPORTING
      persnr               = pernr-pernr
*     RCLAS                =
*     BEGDA                = '18000101'
*     ENDDA                = '99991231'
*     VARKY                =
    IMPORTING
      entrydate            = gd_emp-ncsdate
*        TABLES
*     ENTRY_DATES          =
    EXCEPTIONS
      entry_date_not_found = 1
      pernr_not_assigned   = 2
      OTHERS               = 3.
  IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDIF.
* Set payroll period
  gd_emp-period = gd_emp-effdate(6).
  IF NOT gf_dbglvl EQ $nosimulation
     AND gd_emp-effdate GE $minpayd.
* Run payroll simulation and import results from memory
    PERFORM z_start_simulation USING pernr-pernr gd_emp-period.
*...Start Output.....................................................*
* Get wtypes list
    PERFORM z_get_wt_list.
* Select required wtypes from result table
    PERFORM z_get_results.
* Print results on screen
    PERFORM z_print_summary.
    PERFORM z_print_rt.
    PERFORM z_print_results.
** Collect data for output
*    PERFORM z_proc_output.
    IF pn-begda LE  $changepafdate.
* Collect data for output
      PERFORM z_proc_output.
* Perform "X5 - Leave without pay" check
      PERFORM z_check_x5_condition CHANGING gt_lines.
      IF NOT gf_dbglvl EQ $noworddoc.
* Generate output document
        PERFORM z_start_word_doc USING gt_lines.
      ENDIF.
    ELSE.
* Collect data for output
      PERFORM z_proc_output_new.
* Perform "X5 - Leave without pay" check
      PERFORM z_check_x5_condition CHANGING gt_lines_new.
      IF NOT gf_dbglvl EQ $noworddoc.
* Generate output document
        PERFORM z_start_word_doc USING gt_lines_new.
      ENDIF.
    ENDIF.
  ENDIF.
*....................................................................*
*   end-of-selection
*....................................................................*
END-OF-SELECTION.
  IF gf_dbglvl EQ $noworddoc.
    WRITE: /5 TEXT-142.
    SKIP.
  ENDIF.
  IF gf_dbglvl EQ $nosimulation.
    WRITE: /5 TEXT-143.
    SKIP.
  ENDIF.
  IF gf_itype_found NE $cross.
    WRITE: /5 TEXT-140, gd_emp-itype, 'for',
              gd_emp-pernr, 'at', gd_emp-begda.
    SKIP.
  ENDIF.
  IF NOT gd_emp-effdate IS INITIAL
     AND gd_emp-effdate LT $minpayd.
    WRITE: /5 TEXT-144, gd_emp-effdate.
    WRITE: /5 TEXT-145, $minpayd.
    SKIP.
  ENDIF.
  PERFORM z_print_error.
*--------------------------------------------------------------------*
* Handling of PCL1(2) Buffer
*--------------------------------------------------------------------*
  INCLUDE rpppxm00.
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_start_simulation USING p_pernr  TYPE pernr-pernr
                              p_period TYPE faper.
  DATA: payroll_period   LIKE t549q-pabrp,
        payroll_year     LIKE t549q-pabrj,
        ls_mem_key       TYPE hrpl_memo_key,
        variant_edt      LIKE rsvar-variant,
        employee_numbers LIKE pay_sim_pernr OCCURS 1 WITH HEADER LINE.
  DATA: w_lines   TYPE i,
        w_seq_num LIKE pc261-seqnr,
        w_sname   LIKE t596f-sname.
* set PY year and period
  payroll_year    = p_period(4).
  payroll_period  = p_period+4(2).
* set employee number
  employee_numbers-pernr = p_pernr.
  APPEND employee_numbers.
*-----------------------------------------------------------------------
* perform payroll simulation run
  CALL FUNCTION 'HR_PAYROLL_SIMULATION_SUBMIT'
    EXPORTING
      payroll_area        = gc_payroll_area
      payroll_period      = payroll_period
      payroll_year        = payroll_year
      selection_variant   = gd_payroll_variant
      program_name        = gd_payroll_name
      country_grp         = gd_emp-molga
      log_mem_key         = ls_mem_key
    TABLES
      employee_numbers    = employee_numbers
      buffer              = tbuff
      buffer_directory    = buffer_dir
    EXCEPTIONS
      program_not_exist   = 1
      variant_not_exist   = 2
      missing_parameter   = 3
      wrong_country_group = 4
      OTHERS              = 5.
  CASE sy-subrc.
    WHEN 0.
    WHEN 1.
      MESSAGE e009 WITH sy-msgv1 RAISING program_not_exist.
    WHEN 2.
      MESSAGE e010 WITH sy-msgv1 sy-msgv2 RAISING variant_not_exist.
    WHEN OTHERS.
* Payroll run was not successful
      MESSAGE e004 RAISING payroll_error.
  ENDCASE.
*--------------------------------------------------------------------*
* Evaluate return codes
  READ TABLE employee_numbers INDEX 1.
  IF employee_numbers-retcd NE 0 OR sy-subrc NE 0.
*    IF ( employee_numbers-retcd NE 0 AND  employee_numbers-retcd NE 4 )
*       OR sy-subrc NE 0.
* Payroll run was not successful
*    message E004 raising PAYROLL_ERROR.
    gt_error-msgtext = TEXT-146.
    APPEND gt_error. CLEAR gt_error.
    REJECT.
  ENDIF.
*-----------------------------------------------------------------------
* Read RGDIR from ABAP-memory
  cd-key = p_pernr.
  rp-imp-c2-cu.
  IF rp-imp-cd-subrc <> 0.
    CONCATENATE TEXT-147 p_pernr INTO gt_error-msgtext.
    APPEND gt_error. CLEAR gt_error.
    REJECT.
  ENDIF.
  DESCRIBE TABLE rgdir LINES w_lines.
  IF w_lines LT 1.
* Payroll run was not successful
    MESSAGE e004 RAISING payroll_error.
  ENDIF.
* get payroll result sequential number which correspods to determined
* period and the effective date. For cases with a split we have to
* get sequential number (which will determine payroll results)
* corresponding to the effective date!
  LOOP AT rgdir.
    CHECK rgdir-fpper EQ p_period.
    CHECK gd_emp-effdate BETWEEN rgdir-fpbeg AND rgdir-fpend.
    rx-key-seqno = rgdir-seqnr.
  ENDLOOP.
  rx-key-pernr = p_pernr.
*...Read cluster.....................................................*
  rp-imp-c2-un.
  IF rp-imp-un-subrc <> 0.
* Read was not successfull put error handler here.
  ENDIF.
*...Get split number we are interested in............................*
  LOOP AT wpbp.
    CHECK gd_emp-effdate BETWEEN wpbp-begda AND wpbp-endda.
    MOVE wpbp-apznr TO gd_emp-apznr.
  ENDLOOP.
ENDFORM.                    "RUNRPCALC
*--------------------------------------------------------------------*
* Get a named attribute from storage
*--------------------------------------------------------------------*
FORM z_get_value USING VALUE(fname)   TYPE string
              CHANGING fvalue         TYPE char100.
  CLEAR fvalue.
  SELECT SINGLE fvalue FROM ($tabparams)
                       INTO  fvalue
                       WHERE fname EQ fname.
ENDFORM.                    "GET_VALUE
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_wt_list.
  DATA:
    w_id     TYPE string,
    w_value  TYPE string,
    w_result TYPE zhrpyres.
  SELECT fname fvalue INTO (w_id, w_value)
                      FROM ($tabwtypes).
    READ TABLE gt_results INTO w_result WITH KEY id = w_id.
    IF sy-subrc > 2.
      w_result-id = w_id.
      w_result-wt = w_value.
      APPEND w_result TO gt_results.
    ENDIF.
  ENDSELECT.
  IF sy-subrc <> 0.
    WRITE: / TEXT-141.
  ENDIF.
ENDFORM.                    "Z_GET_WT_LIST
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_results.
  DATA: w_key   LIKE sy-tabix,
        w_rline TYPE zhrpyres.
* select wtypes for determined split number
* and those which are never splitted 'APZNR eq 0'
  LOOP AT rt WHERE apznr EQ gd_emp-apznr
                OR apznr EQ 0.
    READ TABLE gt_results INTO w_rline
                          WITH KEY wt = rt-lgart.
    IF sy-subrc EQ 0.
* save entry index
      w_key = sy-tabix.
      w_rline-pu = rt-betpe. " HR Payroll: Amount per unit
      w_rline-hl = rt-anzhl. " HR payroll: Number
      w_rline-bt = rt-betrg. " HR Payroll: Amount
      " ITEM 35: For part-time s/m (special leave or part-time work schedule)
      "          pensionable remuneration is prorated whereas the full figure should
      IF rt-lgart = '0080' AND p0008-bsgrd NE '100.00'.
        DATA wa510m TYPE t510m.
        DATA: ls_amount TYPE pad_amt7s, "betrg,
              ls_betrg  TYPE pad_amt7s. "betrg.
        CLEAR: ls_amount, ls_betrg.
        SELECT SINGLE betrg INTO ls_amount FROM t510
           WHERE molga = 'UN'
             AND trfar = p0008-trfar
             AND trfgb = p0008-trfgb
*     AND TRFKZ =
             AND trfgr = p0008-trfgr
             AND trfst = p0008-trfst
             AND lgart = rt-lgart
             AND endda >= gd_emp-effdate
             AND begda =< gd_emp-effdate.
        IF sy-subrc EQ 0 AND ls_amount NE space. "*AAHOUNOU24052013
          ls_betrg  = ls_amount / 12.
          w_rline-bt = ls_betrg.
*AAHOUNOU24052013
        ELSE.
          CLEAR wa510m.
          CLEAR: ls_amount, ls_betrg.
          SELECT * FROM t510m INTO wa510m
                WHERE molga = 'UN'
                  AND trfar = p0008-trfar
                  AND trfgb = p0008-trfgb
*     AND TRFKZ =
                  AND trfgr = p0008-trfgr
                  AND trfst = p0008-trfst
                  AND lgart = rt-lgart
                  AND ehire >= gd_emp-ncsdate
                  AND endda >= gd_emp-effdate
                  AND begda =< gd_emp-effdate
                  ORDER BY ehire.
            EXIT.
          ENDSELECT.
          IF sy-subrc EQ 0.
            ls_betrg  = wa510m-betrg / 12.
            w_rline-bt = ls_betrg.
          ENDIF.
*AAHOUNOU24052013
        ENDIF.
      ELSEIF rt-lgart = '0010'.
        CLEAR: ls_amount, ls_betrg.
        SELECT SINGLE betrg INTO ls_amount FROM t510
           WHERE molga = 'UN'
             AND trfar = p0008-trfar
             AND trfgb = p0008-trfgb
*     AND TRFKZ =
             AND trfgr = p0008-trfgr
             AND trfst = p0008-trfst
             AND lgart = '0010'
             AND endda >= gd_emp-effdate
             AND begda =< gd_emp-effdate.
        IF sy-subrc EQ 0  AND ls_amount NE space. ""*AAHOUNOU24052013
          ls_betrg  = ls_amount / 12.
          IF p0008-bsgrd NE '100.00'.
            w_rline-bt = ( ls_betrg *  p0008-bsgrd ) / 100.
          ELSE.
            w_rline-bt = ls_betrg.
          ENDIF.
          w_rline-bt = ls_betrg.
*AAHOUNOU24052013
        ELSE.
          CLEAR wa510m.
          CLEAR: ls_amount, ls_betrg.
          SELECT * FROM t510m INTO wa510m
            WHERE molga = 'UN'
              AND trfar = p0008-trfar
              AND trfgb = p0008-trfgb
*     AND TRFKZ =
              AND trfgr = p0008-trfgr
              AND trfst = p0008-trfst
              AND lgart = rt-lgart
              AND ehire >= gd_emp-ncsdate
              AND endda >= gd_emp-effdate
              AND begda =< gd_emp-effdate
              ORDER BY ehire.
            EXIT.
          ENDSELECT.
          IF sy-subrc EQ 0.
            ls_betrg  =  wa510m-betrg / 12.
            IF p0008-bsgrd NE '100.00'.
              w_rline-bt = ( ls_betrg *  p0008-bsgrd ) / 100.
            ELSE.
              w_rline-bt = ls_betrg.
            ENDIF.
            w_rline-bt = ls_betrg.
          ENDIF.
*AAHOUNOU24052013
        ENDIF.
      ELSEIF rt-lgart = '0032'.
        DATA w_txt TYPE string.
* check Pay Scale Group
        IF  pn-begda GT $changepafdate
            AND ( p0008-trfgr(1) EQ 'P'  "
            OR    p0008-trfgr(1) EQ 'D'  "
            OR    p0008-trfgr(1) EQ 'A' ). " ADG
          CLEAR: ls_amount, ls_betrg.
          SELECT SINGLE betrg INTO ls_amount FROM t510
            WHERE molga = 'UN'
              AND trfar = p0008-trfar
              AND trfgb = p0008-trfgb
              AND trfgr = p0008-trfgr
              AND trfst = p0008-trfst
              AND lgart = '0032'
              AND endda >= gd_emp-effdate
              AND begda =< gd_emp-effdate.
          IF sy-subrc EQ 0 AND ls_amount NE space.
            ls_amount = ls_amount / 12.
            IF p0008-bsgrd NE '100.00'.
              w_rline-bt  = ( ls_amount *  p0008-bsgrd ) / 100.
            ELSE.
              w_rline-bt  = ls_amount.
            ENDIF.
          ELSE.
            CLEAR: ls_amount, ls_betrg.
            CLEAR wa510m.
            SELECT * FROM t510m INTO  wa510m
             WHERE molga = 'UN'
               AND trfar = p0008-trfar
               AND trfgb = p0008-trfgb
               AND trfgr = p0008-trfgr
               AND trfst = p0008-trfst
               AND lgart = '0032'
               AND ehire >= gd_emp-ncsdate
               AND endda >= gd_emp-effdate
               AND begda =< gd_emp-effdate
               ORDER BY ehire.
              EXIT.
            ENDSELECT.
            IF sy-subrc EQ 0.
              wa510m-betrg = wa510m-betrg / 12.
              IF p0008-bsgrd NE '100.00'.
                w_rline-bt  = ( wa510m-betrg *  p0008-bsgrd ) / 100.
              ELSE.
                w_rline-bt  = wa510m-betrg .
              ENDIF.
            ENDIF.
          ENDIF.
        ELSE.
          IF    p0008-trfgr(1) EQ 'P'  "
            OR  p0008-trfgr(1) EQ 'D'  "
            OR  p0008-trfgr(1) EQ 'A'. " ADG
* add rate (S-rate or D-rate -> with or without family dependants)
* to text line.
            IF  p0016-cttyp NE '03'. " ALD
              PERFORM z_get_rate CHANGING w_txt.
            ENDIF.
          ENDIF.
          CLEAR: ls_amount, ls_betrg.
          IF w_txt CS 'S-rate'.
            SELECT SINGLE betrg INTO ls_amount FROM t510
               WHERE molga = 'UN'
                 AND trfar = p0008-trfar
                 AND trfgb = p0008-trfgb
*     AND TRFKZ =
                 AND trfgr = p0008-trfgr
                 AND trfst = p0008-trfst
                 AND lgart = '0030'
                 AND endda >= gd_emp-effdate
                 AND begda =< gd_emp-effdate.
          ELSEIF w_txt CS 'D-rate'.
            SELECT SINGLE betrg INTO ls_amount FROM t510
              WHERE molga = 'UN'
                AND trfar = p0008-trfar
                AND trfgb = p0008-trfgb
*            AND TRFKZ =
                AND trfgr = p0008-trfgr
                AND trfst = p0008-trfst
                AND lgart = '0040'
                AND endda >= gd_emp-effdate
                AND begda =< gd_emp-effdate.
          ELSEIF w_txt IS INITIAL.
            SELECT SINGLE betrg INTO ls_amount FROM t510
              WHERE molga = 'UN'
                AND trfar = p0008-trfar
                AND trfgb = p0008-trfgb
*            AND TRFKZ =
                AND trfgr = p0008-trfgr
                AND trfst = p0008-trfst
                AND lgart = '0030'
                AND endda >= gd_emp-effdate
                AND begda =< gd_emp-effdate.
          ENDIF.
          IF sy-subrc EQ 0  AND ls_amount NE space. "*AAHOUNOU24052013
            ls_betrg  = ls_amount / 12.
            IF p0008-bsgrd NE '100.00'.
              w_rline-bt = ( ls_betrg *  p0008-bsgrd ) / 100.
            ELSE.
              w_rline-bt = ls_betrg.
            ENDIF.
*AAHOUNOU24052013
          ELSE.
            CLEAR: ls_amount, ls_betrg.
            CLEAR wa510m.
            IF w_txt CS 'S-rate'.
              SELECT * FROM t510m INTO wa510m
                WHERE molga = 'UN'
                  AND trfar = p0008-trfar
                  AND trfgb = p0008-trfgb
*     AND TRFKZ =
                  AND trfgr = p0008-trfgr
                  AND trfst = p0008-trfst
                  AND lgart = '0030'
                  AND ehire >= gd_emp-ncsdate
                  AND endda >= gd_emp-effdate
                  AND begda =< gd_emp-effdate
                  ORDER BY ehire.
                EXIT.
              ENDSELECT.
            ELSEIF w_txt CS 'D-rate'.
              SELECT * FROM t510m INTO wa510m
                WHERE molga = 'UN'
                  AND trfar = p0008-trfar
                  AND trfgb = p0008-trfgb
*     AND TRFKZ =
                  AND trfgr = p0008-trfgr
                  AND trfst = p0008-trfst
                  AND lgart = '0040'
                  AND ehire >= gd_emp-ncsdate
                  AND endda >= gd_emp-effdate
                  AND begda =< gd_emp-effdate
                  ORDER BY ehire.
                EXIT.
              ENDSELECT.
            ELSEIF w_txt IS INITIAL.
              SELECT * FROM t510m INTO wa510m
                WHERE molga = 'UN'
                  AND trfar = p0008-trfar
                  AND trfgb = p0008-trfgb
*     AND TRFKZ =
                  AND trfgr = p0008-trfgr
                  AND trfst = p0008-trfst
                  AND lgart = '0030'
                  AND ehire >= gd_emp-ncsdate
                  AND endda >= gd_emp-effdate
                  AND begda =< gd_emp-effdate
                  ORDER BY ehire.
                EXIT.
              ENDSELECT.
            ENDIF.
            ls_betrg  =  wa510m-betrg / 12.
            IF p0008-bsgrd NE '100.00'.
              w_rline-bt = ( ls_betrg *  p0008-bsgrd ) / 100.
            ELSE.
              w_rline-bt = ls_betrg.
            ENDIF.
*AAHOUNOU24052013
          ENDIF.
          CLEAR w_txt.
        ENDIF.
      ENDIF.
* get currency key
* if there is no currency key value in rt table then
* get currencsy from pc202 'Payroll Status Information'
      w_rline-cu = rt-rte_curr. " Currency Key
      IF w_rline-cu IS INITIAL.
        w_rline-cu = rt-amt_curr. " Currency Key
        IF w_rline-cu IS INITIAL.
          w_rline-cu = versc-waers. " Currency Key
        ENDIF.
      ENDIF.
* update results table
      MODIFY gt_results FROM w_rline INDEX w_key.
    ENDIF.
  ENDLOOP.
ENDFORM.                    "Z_GET_RESULTS
*--------------------------------------------------------------------*
* Get concatenated text of action and reason
*--------------------------------------------------------------------*
FORM z_proc_txt_massng
  USING
    p_massn     TYPE massn
    p_massg     TYPE massg
    p_clang     TYPE sprsl
  CHANGING
    text
    text2.
  DATA:
    w_massnt TYPE t529t-mntxt,
    w_massgt TYPE t530t-mgtxt.
  CALL FUNCTION 'HRWPC_RFC_MASSN_TEXT_GET'
    EXPORTING
      massn      = p_massn
      langu      = p_clang
    IMPORTING
      massn_text = w_massnt.
  CALL FUNCTION 'HRWPC_RFC_MASSG_TEXT_GET'
    EXPORTING
      massn      = p_massn
      massg      = p_massg
      langu      = p_clang "sy-langu
    IMPORTING
      massg_text = w_massgt.
  text = w_massnt.
  text2 = w_massgt.
ENDFORM.                    "GET_MASSNG_TEXT
*--------------------------------------------------------------------*
* create a word document based on a form
*--------------------------------------------------------------------*
FORM z_start_word_doc USING lines TYPE table.
  DATA:
    line         TYPE string,
    lineout(100) TYPE c.
  DATA:
    filename   TYPE string,
    data_table TYPE TABLE OF string.
  DATA:
    sepitems      TYPE  string  VALUE ';',
    linetype(1)   TYPE c,
    pos           TYPE i,
    items         TYPE TABLE OF string,
    fileform      TYPE rlgrap-filename,
    filedata      TYPE rlgrap-filename VALUE 'pa_data',
    filepath      TYPE rlgrap-filename VALUE 'c:\',
    fields        TYPE TABLE OF string,
    fdataline     TYPE t_dataline,
    fdata         TYPE TABLE OF t_dataline,
    fdataline_new TYPE t_dataline_new,
    fdata_new     TYPE TABLE OF t_dataline_new,
    fname         TYPE string.
* NEW BEG 150120
  DATA : lv_param1(10), "DIR _OTHERS or _PROD
         lv_param2(20). "prefixe modele exemple : PAF_TLNEW
*  END 150120
  FIELD-SYMBOLS:
    <fs>.
  SKIP.
* BEG FGU150120
*  IF gd_emp-sprsl = 'F'.
*    REPLACE '.DOT' IN gd_fname WITH '_FR.DOT'.
*  ENDIF.
  IF sy-sysid = 'P01'.
    lv_param1 = '_PROD'.
  ELSE.
    lv_param1 = '_OTHERS'.
  ENDIF.
  IF pn-begda LE  $changepafdate.
    lv_param2 = 'PAF_TL'.
  ELSE.
    lv_param2 = 'PAF_TLNEW'.
  ENDIF.
  IF gd_emp-sprsl = 'F'.
    lv_param2 = |{ lv_param2 }_FR|.
  ENDIF.
  CALL FUNCTION 'FILE_GET_NAME'
    EXPORTING
*     CLIENT           = SY-MANDT
      logical_filename = 'Z_PAF'
*     OPERATING_SYSTEM = SY-OPSYS
      parameter_1      = lv_param1
      parameter_2      = lv_param2
*     PARAMETER_3      = ' '
*     USE_PRESENTATION_SERVER       = ' '
*     WITH_FILE_EXTENSION           = ' '
*     USE_BUFFER       = ' '
*     ELEMINATE_BLANKS = 'X'
*     INCLUDING_DIR    = ' '
    IMPORTING
*     EMERGENCY_FLAG   =
*     FILE_FORMAT      =
      file_name        = gd_fname
    EXCEPTIONS
      file_not_found   = 1
      OTHERS           = 2.
  IF sy-subrc <> 0.
* Implement suitable error handling here
  ENDIF.
* END FGU150120
  IF NOT gd_fname IS INITIAL.
    CALL FUNCTION 'RH_CHECK_WWORD_SUPPORT'
      EXCEPTIONS
        no_batch                   = 1
        internal_error             = 2
        wword_not_installed        = 3
        wrong_frontend_os          = 4
        language_problems_possible = 5
        OTHERS                     = 6.
  ENDIF.
  IF ( gd_fname IS INITIAL ) OR ( sy-subrc <> 0 ).
*...MS Word is not available
    FORMAT COLOR COL_NEGATIVE.
    WRITE: /5 'No support for MS Word on this PC.'.
    WRITE: /5 'Error details:'.
    CASE sy-subrc.
      WHEN 1. WRITE: 5 'Not allowed in Batch mode (code 1)'.
      WHEN 2. WRITE: 5 'Internal error (code 2)'.
      WHEN 3. WRITE: 5 'Word not installed (code 3)'.
      WHEN 4. WRITE: 5 'Wrong frontend operating system (code 4)'.
      WHEN 5. WRITE: 5 'Language problems possible (code 5)'.
      WHEN 6. WRITE: 5 'Other problem (code 6)'.
    ENDCASE.
    SKIP.
    FORMAT COLOR COL_POSITIVE.
    WRITE: /5 'The collected infomation will be shown below:'.
    SKIP.
    FORMAT COLOR COL_NORMAL.
    LOOP AT lines INTO line.
      WRITE: / line+1.
    ENDLOOP.
  ELSE.
*...MS Word is available
    filename  = gd_fname.
*    FILENAME = 'C:\Documents and Settings\Administrateur\Bureau\PAF_TL1.DOT'.
*...copy the parameter data into the fubas table of data
    IF NOT gd_fname IS INITIAL.
      fileform = gd_fname.
    ENDIF.
    IF NOT gd_fpath IS INITIAL.
      filepath = gd_fpath.
    ENDIF.
    IF pn-begda LE  $changepafdate.
      LOOP AT lines INTO line.
        IF NOT line IS INITIAL.
          SPLIT line AT sepitems INTO TABLE items.
          LOOP AT items INTO line.
            CASE sy-tabix.
              WHEN 1.
                fname = line.
                APPEND fname TO fields.
              WHEN 2.
                ASSIGN COMPONENT fname OF STRUCTURE fdataline TO <fs>.
                <fs> = line.
              WHEN OTHERS.
                WRITE: 'format error:', line.
            ENDCASE.
          ENDLOOP.
        ENDIF.
      ENDLOOP.
      APPEND fdataline TO fdata.
*  DATA sapworkdir TYPE string.
*  DATA i TYPE i.
*  CALL METHOD cl_gui_frontend_services=>get_sapgui_workdir
*    CHANGING
*      sapworkdir = sapworkdir.
*  i = STRLEN( sapworkdir ).
*  REPLACE '&' WITH sapworkdir(i) INTO filepath.
*  REPLACE '&' WITH sapworkdir(i) INTO gd_fpath.
*  filepath = sapworkdir.
      CALL FUNCTION 'HR_PL_WORD_OLE_FORMLETTER'
        EXPORTING
          word_doc_file       = fileform
*         HIDDEN              = 0
*         WORD_PASSWORD       =
*         PASSWORD_OPTION     = 1
          file_name           = filedata
*         NEW_DOCUMENT        =
          download_path       = filepath
*         PRINT               = PFPRINT
        TABLES
          data_tab            = fdata
          fieldnames          = fields
        EXCEPTIONS
          invalid_fieldnames  = 1
          user_cancelled      = 2
          download_problem    = 3
          communication_error = 4
          OTHERS              = 5.
    ELSE.
      LOOP AT lines INTO line.
        IF NOT line IS INITIAL.
          SPLIT line AT sepitems INTO TABLE items.
          LOOP AT items INTO line.
            CASE sy-tabix.
              WHEN 1.
                fname = line.
                APPEND fname TO fields.
              WHEN 2.
                ASSIGN COMPONENT fname OF STRUCTURE fdataline_new TO <fs>.
                <fs> = line.
              WHEN OTHERS.
                WRITE: 'format error:', line.
            ENDCASE.
          ENDLOOP.
        ENDIF.
      ENDLOOP.
      APPEND fdataline_new TO fdata_new.
*  DATA sapworkdir TYPE string.
*  DATA i TYPE i.
*  CALL METHOD cl_gui_frontend_services=>get_sapgui_workdir
*    CHANGING
*      sapworkdir = sapworkdir.
*  i = STRLEN( sapworkdir ).
*  REPLACE '&' WITH sapworkdir(i) INTO filepath.
*  REPLACE '&' WITH sapworkdir(i) INTO gd_fpath.
*  filepath = sapworkdir.
      CALL FUNCTION 'HR_PL_WORD_OLE_FORMLETTER'
        EXPORTING
          word_doc_file      = fileform
*         HIDDEN              = 0
*         WORD_PASSWORD       =
*         PASSWORD_OPTION     = 1
          file_name           = filedata
*         NEW_DOCUMENT        =
          download_path       = filepath
*         PRINT               = PFPRINT
        TABLES
          data_tab            = fdata_new
          fieldnames          = fields
        EXCEPTIONS
          invalid_fieldnames  = 1
          user_cancelled      = 2
          download_problem    = 3
          communication_error = 4
          OTHERS              = 5.
    ENDIF.
    IF sy-subrc <> 0.
      DATA:
        desc    TYPE string VALUE 'unknown'.
      CASE sy-subrc.
        WHEN  1.  desc = 'Invalid filenames'.
        WHEN  2.  desc = 'User elled'.
        WHEN  3.  desc = 'Downloadcanc problem'.
        WHEN  4.  desc = 'Communication error'.
        WHEN  5.  desc = 'Others'.
      ENDCASE.
      WRITE: /5 'Cannot launch MS Word! Reason:', desc.
    ELSE.
      WRITE: /5 'MS Word launched in a separate window'.
    ENDIF.
  ENDIF.
ENDFORM.                    "Z_START_WORD_DOC
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_makentry USING p_field
                      p_value.
  DATA w_line TYPE string.
  IF NOT p_value IS INITIAL.
    DO.
* check wheather string contains forbidden charecter
      IF NOT p_value CA ';"'. EXIT. ENDIF.
      SEARCH p_value FOR ';'.
      IF sy-subrc IS INITIAL.
        REPLACE p_value+sy-fdpos(1) WITH $empty INTO p_value.
      ENDIF.
      SEARCH p_value FOR '"'.
      IF sy-subrc IS INITIAL.
        REPLACE p_value+sy-fdpos(1) WITH $empty INTO p_value.
      ENDIF.
* leave ' to be shown for french titles
*      search P_VALUE for ''''.
*      if SY-SUBRC is initial.
*        replace P_VALUE+SY-FDPOS(1) with $EMPTY into P_VALUE.
*      endif.
    ENDDO.
  ENDIF.
  CONCATENATE p_field ';' p_value INTO w_line.
  APPEND w_line TO gt_lines.
ENDFORM.                    "Z_MAKENTRY
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_makentry_new USING p_field
                      p_value.
  DATA w_line TYPE string.
  IF NOT p_value IS INITIAL.
    DO.
* check wheather string contains forbidden charecter
      IF NOT p_value CA ';"'. EXIT. ENDIF.
      SEARCH p_value FOR ';'.
      IF sy-subrc IS INITIAL.
        REPLACE p_value+sy-fdpos(1) WITH $empty INTO p_value.
      ENDIF.
      SEARCH p_value FOR '"'.
      IF sy-subrc IS INITIAL.
        REPLACE p_value+sy-fdpos(1) WITH $empty INTO p_value.
      ENDIF.
* leave ' to be shown for french titles
*      search P_VALUE for ''''.
*      if SY-SUBRC is initial.
*        replace P_VALUE+SY-FDPOS(1) with $EMPTY into P_VALUE.
*      endif.
    ENDDO.
  ENDIF.
  CONCATENATE p_field ';' p_value INTO w_line.
  APPEND w_line TO gt_lines_new.
ENDFORM.                    "Z_MAKENTRY_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_wt     USING    p_id    TYPE string
                  CHANGING p_val   TYPE maxbt
                           p_waers TYPE waers.
  DATA: w_rline   TYPE zhrpyres.
* get accumulated value for a wtype group
  LOOP AT gt_results INTO w_rline.
* In wt table there could be values like CHAL, CHAL2, CHAL3
* the sum of which makes the value for 'child allowances' wtype group.
* Having this we have to collect all wage types related
* to specifique group.
    IF w_rline-id(4) EQ p_id.
* collect amount
      ADD w_rline-bt TO p_val.
* find corresponding currency key
      IF NOT w_rline-cu IS INITIAL.
        p_waers = w_rline-cu.
      ENDIF.
    ENDIF.
  ENDLOOP.
  " ITEM 35: For part-time s/m (special leave or part-time work schedule)
  "          pensionable remuneration is prorated whereas the full figure should app
  IF p_id = 'YNPF' AND p0008-bsgrd NE '100.00'.
    DATA: wa510m TYPE t510m.
    DATA: ls_amount TYPE pad_amt7s, "betrg,
          ls_betrg  TYPE pad_amt7s. "betrg.
    CLEAR: ls_amount, ls_betrg.
    SELECT SINGLE betrg INTO ls_amount FROM t510
       WHERE molga = 'UN'
         AND trfar = p0008-trfar
         AND trfgb = p0008-trfgb
*     AND TRFKZ =
         AND trfgr = p0008-trfgr
         AND trfst = p0008-trfst
         AND lgart = '0080'
         AND endda >= gd_emp-effdate
         AND begda =< gd_emp-effdate.
    IF sy-subrc EQ 0 AND ls_amount NE space. "*AAHOUNOU24052013
      p_val = ls_amount.
*AAHOUNOU24052013
    ELSE.
      CLEAR: ls_amount, ls_betrg.
      CLEAR wa510m.
      SELECT * FROM t510m INTO wa510m
             WHERE molga = 'UN'
               AND trfar = p0008-trfar
               AND trfgb = p0008-trfgb
*     AND TRFKZ =
               AND trfgr = p0008-trfgr
               AND trfst = p0008-trfst
               AND lgart = '0080'
               AND ehire >= gd_emp-ncsdate
               AND endda >= gd_emp-effdate
               AND begda =< gd_emp-effdate
               ORDER BY ehire.
        EXIT.
      ENDSELECT.
      IF sy-subrc EQ 0.
        p_val = wa510m-betrg .
      ENDIF.
*AAHOUNOU24052013
    ENDIF.
  ELSEIF p_id = 'GBAS'.
    CLEAR: ls_amount, ls_betrg.
    SELECT SINGLE betrg INTO ls_amount FROM t510
       WHERE molga = 'UN'
         AND trfar = p0008-trfar
         AND trfgb = p0008-trfgb
*     AND TRFKZ =
         AND trfgr = p0008-trfgr
         AND trfst = p0008-trfst
         AND lgart = '0010'
         AND endda >= gd_emp-effdate
         AND begda =< gd_emp-effdate.
    IF sy-subrc EQ 0 AND ls_amount NE space. "*AAHOUNOU24052013
      IF p0008-bsgrd NE '100.00'.
        p_val = ( ls_amount *  p0008-bsgrd ) / 100.
      ELSE.
        p_val = ls_amount.
      ENDIF.
*AAHOUNOU24052013
    ELSE.
      CLEAR: ls_amount, ls_betrg.
      CLEAR wa510m.
      SELECT * FROM t510m INTO wa510m
             WHERE molga = 'UN'
               AND trfar = p0008-trfar
               AND trfgb = p0008-trfgb
*     AND TRFKZ =
               AND trfgr = p0008-trfgr
               AND trfst = p0008-trfst
               AND lgart = '0010'
               AND ehire >= gd_emp-ncsdate
               AND endda >= gd_emp-effdate
               AND begda =< gd_emp-effdate
               ORDER BY ehire.
        EXIT.
      ENDSELECT.
      IF sy-subrc EQ 0.
        IF p0008-bsgrd NE '100.00'.
          p_val = ( wa510m-betrg *  p0008-bsgrd ) / 100.
        ELSE.
          p_val = wa510m-betrg.
        ENDIF.
      ENDIF.
*AAHOUNOU24052013
    ENDIF.
*AAHOUNOU11032012
*      IF sy-subrc EQ 0 and ls_amount ne 0.
*        IF p0008-bsgrd NE '100.00'.
*          p_val = ( ls_amount *  p0008-bsgrd ) / 100.
*        ELSE.
*          p_val = ls_amount.
*        ENDIF.
*      ENDIF.
*     ELSEIF sy-subrc EQ 0 and ls_amount eq 0.
*     A traiter pour TH / T510M
*     ENDIF.
  ENDIF.
* derive per year value
  IF
* main payroll elements
*       p_id EQ 'GBAS'   " gross base salary
*    OR p_id EQ 'BASE'   " net base salary
     p_id EQ 'POST'   " post adjustment
* allowances
    OR p_id EQ 'CHAL'   " child allowance
    OR p_id EQ 'DPAL'   " secondary dependent allowance
    OR p_id EQ 'SPAL'   " spouse allowance
    OR p_id EQ 'SPDI'   " spouse differential
    OR p_id EQ 'MHAL'   " mobility & hardship allowance
    OR p_id EQ 'TRMO'   " transitional mobility H duty station
    OR p_id EQ 'AHAL'   " additional hardship allowance
    OR p_id EQ 'NFSA'   " non family service allowance
    OR p_id EQ 'LAAL'   " first language allowance
    OR p_id EQ 'SLAL'   " second language allowance
    OR p_id EQ 'SEAL'   " service allowance (ALD)
    OR p_id EQ 'FMAL'   " family allowance (ALD)
*AAHOUNOU25012017
     OR p_id EQ 'FMAT'   " family allowance Transitoire
     OR p_id EQ 'FMAS'   " family allowance Single Parent
*AAHOUNOU25012017
    OR p_id EQ 'SPPA'   " special post allowance
    OR p_id EQ 'RPAL'   " representation allowance
    OR p_id EQ 'TRAL'   " transportation allowance
    OR p_id EQ 'SNAL'   " Spec. pers. non-pens. allowance
    OR p_id EQ 'PTAL'   " pers. transitional allowance
    OR p_id EQ 'OSAL'   " non unesco family allowance
    OR p_id EQ 'FSAL'   " Family allowance CAF
    OR p_id EQ 'CSAL'   " Family allowance CAF Special
    OR p_id EQ 'CLAL'   " closing allowance
    OR p_id EQ 'NRAL'   " non resident's allowance
* deductions
    OR p_id EQ 'PENC'   " pension contribution
    OR p_id EQ 'MBFC'   " MBF contribution
    OR p_id EQ 'DDSS'.  " social security
    MULTIPLY p_val BY gd_salperiod.
  ENDIF.
*.........................................*
* remaining wt groups:
*   'RNTS' rental subsidy (monthly)
*   'AGDS' assignment grant (DSA)
*   'AGLS' assignment grant (Lump Sum)
*   'RPGR' repatriation grant
*   'TMID' termination indemnity
*   'DEGR' death grant
*   'ILON' in lieu of notice
*   'ANLS' annual leave settlement
*   'HDID' hairdressing indemnity
*   'DDHP' deduction for housing provided
*   'PENS' pensionable remuneration
*.........................................*
* define list of foreign currencies for which amount
* should be displayed in millions. There must be an error in
* payroll calculator... here is a temporary solution
*AAHOUNOU05082013
*  IF   p_waers EQ 'XAF'
*    OR p_waers EQ 'XOF'
*    OR p_waers EQ 'IDR'
*    OR p_waers EQ 'DJF'
*    OR p_waers EQ 'RWF'
*    OR p_waers EQ 'BIF'
*    OR p_waers EQ 'MGA'.
*    MULTIPLY p_val BY 100.
*  ENDIF.
  IF p_waers EQ 'ADP'
  OR p_waers EQ 'AFA'
  OR p_waers EQ 'AFN'
  OR p_waers EQ 'BEF'
  OR p_waers EQ 'BIF'
  OR p_waers EQ 'BYB'
  OR p_waers EQ 'DJF'
  OR p_waers EQ 'ECS'
  OR p_waers EQ 'ESP'
  OR p_waers EQ 'GNF'
  OR p_waers EQ 'GRD'
  OR p_waers EQ 'HUF'
  OR p_waers EQ 'IDR'
  OR p_waers EQ 'ITL'
  OR p_waers EQ 'JPY'
  OR p_waers EQ 'KMF'
  OR p_waers EQ 'KRW'
  OR p_waers EQ 'LAK'
  OR p_waers EQ 'LUF'
  OR p_waers EQ 'MGA'
  OR p_waers EQ 'MGF'
  OR p_waers EQ 'PTE'
  OR p_waers EQ 'PYG'
  OR p_waers EQ 'ROL'
  OR p_waers EQ 'RWF'
  OR p_waers EQ 'TJR'
  OR p_waers EQ 'TJS'
  OR p_waers EQ 'TMM'
  OR p_waers EQ 'TPE'
  OR p_waers EQ 'TRL'
  OR p_waers EQ 'UGX'
  OR p_waers EQ 'VND'
  OR p_waers EQ 'VUV'
  OR p_waers EQ 'XAF'
  OR p_waers EQ 'XOF'
  OR p_waers EQ 'XPF'.
    MULTIPLY p_val BY 100.
  ENDIF.
* same as above...
* define list of foreign currencies for which amount
* should be multiplied by 10. Because of 3 decimals values are
* imported in cluster and devided by 10 in order to leave only 2
* decimals. This should be corrected here.
  IF   p_waers EQ 'JOD'
    OR p_waers EQ 'EGP'
    OR p_waers EQ 'BHD'
    OR p_waers EQ 'DEM3'
    OR p_waers EQ 'IQD'
    OR p_waers EQ 'KWD'
    OR p_waers EQ 'LYD'
    OR p_waers EQ 'OMR'
    OR p_waers EQ'TND'.
    DIVIDE p_val BY 10.
  ENDIF.
*  DATA wa_currdec like TCURX-CURRDEC.
*  CLEAR wa_currdec.
*  SELECT SINGLE * FROM tcurx
*  WHERE currkey eq p_waers .
*  IF tcurx-currdec = 3 .
*    DIVIDE p_val BY 10.
*  ELSEIF tcurx-currdec = 0.
*    MULTIPLY p_val BY 100.
*  ENDIF.
*AAHOUNOU05082013
* negative amounts are placed in a separate section in the output doc.
* as Deductions. So for any negative amount we have to change the sign
  IF p_val LT 0.
    MULTIPLY p_val BY -1.
* need to track here wheather 'Annual leave settlement' amount
* is negative
    IF p_id EQ 'ANLS'. MOVE $cross TO gf_anls_is_negative. ENDIF.
  ENDIF.
* for action 'X7 - Leave with half pay' all w.types
* wiht few exceptions have to be divided by 2
  IF gd_emp-massn EQ 'X7'
    AND p_id NE 'YNPF'
    AND p_id NE 'GBAS'
    AND p_id NE 'PENC'
    AND p_id NE 'MBFC'.
    DIVIDE p_val BY 2.
  ENDIF.
ENDFORM.                    "Z_GET_WT
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_wt1     USING    p_id    TYPE string
                   CHANGING p_val   TYPE maxbt.
  DATA: w_rline   TYPE zhrpyres.
* get accumulated value for a wtype group
  LOOP AT gt_results INTO w_rline.
    IF w_rline-id(4) EQ p_id.
* collect amount
      ADD w_rline-hl TO p_val.
    ENDIF.
  ENDLOOP.
ENDFORM.                                                    "Z_GET_WT1
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_wt2     USING    p_id    TYPE string
                            p_txt   TYPE string
                   CHANGING p_val   TYPE maxbt
                            p_waers TYPE waers.
  DATA p_val2  TYPE maxbt.
  DATA: wa510m TYPE t510m.
  DATA: w_rline   TYPE zhrpyres.
  DATA: ls_amount TYPE pad_amt7s, "betrg,
        ls_betrg  TYPE pad_amt7s. "betrg.
* get accumulated value for a wtype group
  LOOP AT gt_results INTO w_rline.
* In wt table there could be values like CHAL, CHAL2, CHAL3
* the sum of which makes the value for 'child allowances' wtype group.
* Having this we have to collect all wage types related
* to specifique group.
    IF w_rline-id(4) EQ p_id.
* collect amount
      ADD w_rline-bt TO p_val.
* find corresponding currency key
      IF NOT w_rline-cu IS INITIAL.
        p_waers = w_rline-cu.
      ENDIF.
    ENDIF.
  ENDLOOP.
  " ITEM 35: For part-time s/m (special leave or part-time work schedule)
  "          pensionable remuneration is prorated whereas the full figure should app
*AAHOUNOU25012017 "inaya
  IF p_id = 'BASE' AND  pn-begda GT $changepafdate
          AND ( p0008-trfgr(1) EQ 'P'  "
          OR    p0008-trfgr(1) EQ 'D'  "
          OR    p0008-trfgr(1) EQ 'A' ). " ADG
    CLEAR p_val.
    CLEAR: ls_amount, ls_betrg.
    SELECT SINGLE betrg INTO ls_amount FROM t510
      WHERE molga = 'UN'
        AND trfar = p0008-trfar
        AND trfgb = p0008-trfgb
        AND trfgr = p0008-trfgr
        AND trfst = p0008-trfst
        AND lgart = '0032'
        AND endda >= gd_emp-effdate
        AND begda =< gd_emp-effdate.
    IF sy-subrc EQ 0 AND ls_amount NE space.
      IF p0008-bsgrd NE '100.00'.
        p_val = ( ls_amount *  p0008-bsgrd ) / 100.
      ELSE.
        p_val = ls_amount.
      ENDIF.
    ELSE.
      CLEAR: ls_amount, ls_betrg.
      CLEAR wa510m.
      SELECT * FROM t510m INTO  wa510m
       WHERE molga = 'UN'
         AND trfar = p0008-trfar
         AND trfgb = p0008-trfgb
         AND trfgr = p0008-trfgr
         AND trfst = p0008-trfst
         AND lgart = '0032'
         AND ehire >= gd_emp-ncsdate
         AND endda >= gd_emp-effdate
         AND begda =< gd_emp-effdate
         ORDER BY ehire.
        EXIT.
      ENDSELECT.
      IF sy-subrc EQ 0.
        IF p0008-bsgrd NE '100.00'.
          p_val = ( wa510m-betrg *  p0008-bsgrd ) / 100.
        ELSE.
          p_val = wa510m-betrg .
        ENDIF.
      ENDIF.
    ENDIF.
  ELSEIF p_id = 'BASE'.
    CLEAR   p_val .
*AAHOUNOU25012017
    CLEAR: ls_amount, ls_betrg.
    IF p_txt CS 'S-rate'.
      SELECT SINGLE betrg INTO ls_amount FROM t510
         WHERE molga = 'UN'
           AND trfar = p0008-trfar
           AND trfgb = p0008-trfgb
*     AND TRFKZ =
           AND trfgr = p0008-trfgr
           AND trfst = p0008-trfst
           AND lgart = '0030'
           AND endda >= gd_emp-effdate
           AND begda =< gd_emp-effdate.
    ELSEIF p_txt CS 'D-rate'.
      SELECT SINGLE betrg INTO ls_amount FROM t510
         WHERE molga = 'UN'
           AND trfar = p0008-trfar
           AND trfgb = p0008-trfgb
*     AND TRFKZ =
           AND trfgr = p0008-trfgr
           AND trfst = p0008-trfst
           AND lgart = '0040'
           AND endda >= gd_emp-effdate
           AND begda =< gd_emp-effdate.
    ELSE.
      SELECT SINGLE betrg INTO ls_amount FROM t510
         WHERE molga = 'UN'
           AND trfar = p0008-trfar
           AND trfgb = p0008-trfgb
*     AND TRFKZ =
           AND trfgr = p0008-trfgr
           AND trfst = p0008-trfst
           AND lgart = '0030'
           AND endda >= gd_emp-effdate
           AND begda =< gd_emp-effdate.
    ENDIF.
    IF sy-subrc EQ 0 AND ls_amount NE space. "*AAHOUNOU24052013
      IF p0008-bsgrd NE '100.00'.
        p_val = ( ls_amount *  p0008-bsgrd ) / 100.
      ELSE.
        p_val = ls_amount.
      ENDIF.
*AAHOUNOU24052013
    ELSE.
      CLEAR: ls_amount, ls_betrg.
      CLEAR wa510m.
      IF p_txt CS 'S-rate'.
        SELECT * FROM t510m INTO wa510m
               WHERE molga = 'UN'
                 AND trfar = p0008-trfar
                 AND trfgb = p0008-trfgb
*     AND TRFKZ =
                 AND trfgr = p0008-trfgr
                 AND trfst = p0008-trfst
                 AND lgart = '0030'
                 AND ehire >= gd_emp-ncsdate
                 AND endda >= gd_emp-effdate
                 AND begda =< gd_emp-effdate
                 ORDER BY ehire.
          EXIT.
        ENDSELECT.
      ELSEIF p_txt CS 'D-rate'.
        SELECT * FROM t510m INTO wa510m
               WHERE molga = 'UN'
                 AND trfar = p0008-trfar
                 AND trfgb = p0008-trfgb
*     AND TRFKZ =
                 AND trfgr = p0008-trfgr
                 AND trfst = p0008-trfst
                 AND lgart = '0040'
                 AND ehire >= gd_emp-ncsdate
                 AND endda >= gd_emp-effdate
                 AND begda =< gd_emp-effdate
                 ORDER BY ehire.
          EXIT.
        ENDSELECT.
      ELSE.
        SELECT * FROM t510m INTO wa510m
               WHERE molga = 'UN'
                 AND trfar = p0008-trfar
                 AND trfgb = p0008-trfgb
*     AND TRFKZ =
                 AND trfgr = p0008-trfgr
                 AND trfst = p0008-trfst
                 AND lgart = '0030'
                 AND ehire >= gd_emp-ncsdate
                 AND endda >= gd_emp-effdate
                 AND begda =< gd_emp-effdate
                 ORDER BY ehire.
          EXIT.
        ENDSELECT.
      ENDIF.
      IF sy-subrc EQ 0.
        IF p0008-bsgrd NE '100.00'.
          p_val = ( wa510m-betrg *  p0008-bsgrd ) / 100.
        ELSE.
          p_val = wa510m-betrg .
        ENDIF.
      ENDIF.
*AAHOUNOU24052013
    ENDIF.
  ENDIF.
* define list of foreign currencies for which amount
* should be displayed in millions. There must be an error in
* payroll calculator... here is a temporary solution
*  DATA wa_currdec like TCURX-CURRDEC.
*  CLEAR wa_currdec.
*  SELECT SINGLE * FROM tcurx
*  WHERE currkey eq p_waers .
*  IF tcurx-currdec = 3 .
*    DIVIDE p_val BY 10.
*  ELSEIF tcurx-currdec = 0.
*    MULTIPLY p_val BY 100.
*  ENDIF.
*AAHOUNOU05082013
*  IF   p_waers EQ 'XAF'
*    OR p_waers EQ 'XOF'
*    OR p_waers EQ 'IDR'
*    OR p_waers EQ 'DJF'
*    OR p_waers EQ 'RWF'
*    OR p_waers EQ 'BIF'
*    OR p_waers EQ 'MGA'.
*    MULTIPLY p_val BY 100.
*  ENDIF.
  IF p_waers EQ 'ADP'
    OR p_waers EQ 'AFA'
    OR p_waers EQ 'AFN'
  OR p_waers EQ 'BEF'
  OR p_waers EQ 'BIF'
  OR p_waers EQ 'BYB'
  OR p_waers EQ 'DJF'
  OR p_waers EQ 'ECS'
  OR p_waers EQ 'ESP'
  OR p_waers EQ 'GNF'
  OR p_waers EQ 'GRD'
  OR p_waers EQ 'HUF'
  OR p_waers EQ 'IDR'
  OR p_waers EQ 'ITL'
  OR p_waers EQ 'JPY'
  OR p_waers EQ 'KMF'
  OR p_waers EQ 'KRW'
  OR p_waers EQ 'LAK'
  OR p_waers EQ 'LUF'
  OR p_waers EQ 'MGA'
  OR p_waers EQ 'MGF'
  OR p_waers EQ 'PTE'
  OR p_waers EQ 'PYG'
  OR p_waers EQ 'ROL'
  OR p_waers EQ 'RWF'
  OR p_waers EQ 'TJR'
  OR p_waers EQ 'TJS'
  OR p_waers EQ 'TMM'
  OR p_waers EQ 'TPE'
  OR p_waers EQ 'TRL'
  OR p_waers EQ 'UGX'
  OR p_waers EQ 'VND'
  OR p_waers EQ 'VUV'
  OR p_waers EQ 'XAF'
  OR p_waers EQ 'XOF'
  OR p_waers EQ 'XPF'.
    MULTIPLY p_val BY 100.
  ENDIF.
* same as above...
* define list of foreign currencies for which amount
* should be multiplied by 10. Because of 3 decimals values are
* imported in cluster and devided by 10 in order to leave only 2
* decimals. This should be corrected here.
  IF   p_waers EQ 'JOD'
   OR p_waers EQ 'EGP'
   OR p_waers EQ 'BHD'
   OR p_waers EQ 'DEM3'
   OR p_waers EQ 'IQD'
   OR p_waers EQ 'KWD'
   OR p_waers EQ 'LYD'
   OR p_waers EQ 'OMR'
   OR p_waers EQ'TND'.
    DIVIDE p_val BY 10.
  ENDIF.
*AAHOUNOU05082013
* negative amounts are placed in a separate section in the output doc.
* as Deductions. So for any negative amount we have to change the sign
  IF p_val LT 0.
    MULTIPLY p_val BY -1.
* need to track here wheather 'Annual leave settlement' amount
* is negative
    IF p_id EQ 'ANLS'. MOVE $cross TO gf_anls_is_negative. ENDIF.
  ENDIF.
* for action 'X7 - Leave with half pay' all w.types
* wiht few exceptions have to be divided by 2
  IF gd_emp-massn EQ 'X7'
    AND p_id NE 'YNPF'
    AND p_id NE 'GBAS'
    AND p_id NE 'PENC'
    AND p_id NE 'MBFC'.
    DIVIDE p_val BY 2.
  ENDIF.
ENDFORM.                                                    "Z_GET_WT2
*--------------------------------------------------------------------*
* Get formatted value for a wtype
*--------------------------------------------------------------------*
FORM z_get_wt_fmt USING    p_id    TYPE string
                  CHANGING p_val   TYPE string.
  DATA: w_betrg TYPE maxbt,
        w_waers TYPE waers.
* get accumulated amount for a wtype group
  PERFORM z_get_wt USING p_id CHANGING w_betrg w_waers.
* format result amount
  PERFORM z_format_wt USING w_betrg w_waers
                   CHANGING p_val.
ENDFORM.                    "Z_GET_WT_FMT
*--------------------------------------------------------------------*
* Get formatted value for a wtype
*--------------------------------------------------------------------*
FORM z_get_wt_fmt1 USING    p_id    TYPE string
                   CHANGING p_val   TYPE string.
  DATA: w_anzhl TYPE maxbt,
        w_waers TYPE waers.
* get accumulated amount for a wtype group
  PERFORM z_get_wt1 USING p_id CHANGING w_anzhl.
  p_val = w_anzhl.
** format result amount
*  PERFORM z_format_wt USING w_anzhl w_waers
*                   CHANGING p_val.
ENDFORM.                    "Z_GET_WT_FMT1
*--------------------------------------------------------------------*
* Get formatted value for a wtype
*--------------------------------------------------------------------*
FORM z_get_wt_fmt2 USING    p_id    TYPE string
                            p_txt   TYPE string
                   CHANGING p_val   TYPE string.
  DATA: w_betrg TYPE maxbt,
        w_waers TYPE waers.
* get accumulated amount for a wtype group
  PERFORM z_get_wt2 USING p_id p_txt CHANGING w_betrg w_waers.
* format result amount
  PERFORM z_format_wt USING w_betrg w_waers
                   CHANGING p_val.
ENDFORM.                    "Z_GET_WT_FMT2
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_format_wt USING p_betrg TYPE maxbt
                       p_waers TYPE waers
              CHANGING p_val   TYPE string.
  DATA: w_amnt      TYPE i,
        w_camnt(14) TYPE c.
* cast to I type
  w_amnt = p_betrg.
* round amount
  WRITE w_amnt TO w_camnt RIGHT-JUSTIFIED.
* add currency key to final value
  CONCATENATE w_camnt p_waers INTO p_val SEPARATED BY space.
ENDFORM.                    "Z_FORMAT_WT
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_line USING p_fld1 p_val1
                       p_fld2 p_val2.
  DATA: w_val(20) TYPE c,
        w_val1    TYPE string,
        w_val2    TYPE string,
        w_len     TYPE i.
  w_val1 = p_val1.
  w_val2 = p_val2.
* cast to char
  w_val = p_val1.
* remove leading spaces
  SHIFT w_val LEFT DELETING LEADING space.
* get string length
  w_len = strlen( w_val ).
* If length is 1 it means that the value is zero
* otherwise it should be more than 1 (with currency sign).
  IF w_len EQ 1.
    CLEAR: w_val1,
           w_val2.
  ENDIF.
  PERFORM z_makentry USING p_fld1 w_val1.
  PERFORM z_makentry USING p_fld2 w_val2.
ENDFORM.                    "z_proc_line
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_line_new USING p_fld1 p_val1
                       p_fld2 p_val2.
  DATA: w_val(20) TYPE c,
        w_val1    TYPE string,
        w_val2    TYPE string,
        w_len     TYPE i.
  w_val1 = p_val1.
  w_val2 = p_val2.
* cast to char
  w_val = p_val1.
* remove leading spaces
  SHIFT w_val LEFT DELETING LEADING space.
* get string length
  w_len = strlen( w_val ).
* If length is 1 it means that the value is zero
* otherwise it should be more than 1 (with currency sign).
  IF w_len EQ 1.
    CLEAR: w_val1,
           w_val2.
  ENDIF.
  PERFORM z_makentry_new USING p_fld1 w_val1.
  PERFORM z_makentry_new USING p_fld2 w_val2.
ENDFORM.                    "z_proc_line_new
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_anls.
  DATA: w_val     TYPE string,
        w_txt     TYPE string,
        w_num     TYPE anzhl,
        w_pertxt  TYPE string,
        w_tmp     TYPE string,
        w_cnum(6) TYPE c.
  PERFORM z_get_wt_fmt USING 'ANLS' CHANGING w_val.
* get text from texts table
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NNL'.
* get number of leaves
  w_num = p0015-anzhl.
* if number of leaves left is negative then change the sign
  IF w_num < 0. w_num = 0 - w_num. ENDIF.
* cast to character
  WRITE w_num TO w_cnum RIGHT-JUSTIFIED.
  MOVE w_cnum TO w_tmp.
* remove leading spaces
  SHIFT w_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. w_pertxt = 'days'.
    WHEN 'F'. w_pertxt = 'jours'.
  ENDCASE.
  CONCATENATE w_txt '(' w_tmp w_pertxt ')'
         INTO w_txt SEPARATED BY space.
* this flag is set in Z_GET_WT form
  IF NOT gf_anls_is_negative EQ $cross.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
    IF gf_x1x2xa EQ $cross.
      PERFORM z_proc_line USING 'ANT' w_val
                                'ANL' w_txt.
    ELSE.
      PERFORM z_proc_line USING 'ANT' $empty
                                'ANL' $empty.
    ENDIF.
* write empty values in Deductions section
    PERFORM z_proc_line USING 'NNT' $empty
                              'NNL' $empty.
  ELSE.
* write empty values in Basic Pay / Allowances section
    PERFORM z_proc_line USING 'ANT' $empty
                              'ANL' $empty.
    IF gf_x1x2xa EQ $cross.
      PERFORM z_proc_line USING 'NNT' w_val
                                'NNL' w_txt.
    ELSE.
      PERFORM z_proc_line USING 'NNT' $empty
                                'NNL' $empty.
    ENDIF.
  ENDIF.
ENDFORM.                    "Z_PROC_TXT_ANLS
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_anls_new.
  DATA: w_val     TYPE string,
        w_txt     TYPE string,
        w_num     TYPE anzhl,
        w_pertxt  TYPE string,
        w_tmp     TYPE string,
        w_cnum(6) TYPE c.
  PERFORM z_get_wt_fmt USING 'ANLS' CHANGING w_val.
* get text from texts table
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NNL'.
* get number of leaves
  w_num = p0015-anzhl.
* if number of leaves left is negative then change the sign
  IF w_num < 0. w_num = 0 - w_num. ENDIF.
* cast to character
  WRITE w_num TO w_cnum RIGHT-JUSTIFIED.
  MOVE w_cnum TO w_tmp.
* remove leading spaces
  SHIFT w_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. w_pertxt = 'days'.
    WHEN 'F'. w_pertxt = 'jours'.
  ENDCASE.
  CONCATENATE w_txt '(' w_tmp w_pertxt ')'
         INTO w_txt SEPARATED BY space.
* this flag is set in Z_GET_WT form
  IF NOT gf_anls_is_negative EQ $cross.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
    IF gf_x1x2xa EQ $cross.
      PERFORM z_proc_line_new USING 'ANT' w_val
                                'ANL' w_txt.
    ELSE.
      PERFORM z_proc_line_new USING 'ANT' $empty
                                'ANL' $empty.
    ENDIF.
* write empty values in Deductions section
    PERFORM z_proc_line_new USING 'NNT' $empty
                              'NNL' $empty.
  ELSE.
* write empty values in Basic Pay / Allowances section
    PERFORM z_proc_line_new USING 'ANT' $empty
                              'ANL' $empty.
    IF gf_x1x2xa EQ $cross.
      PERFORM z_proc_line_new USING 'NNT' w_val
                                'NNL' w_txt.
    ELSE.
      PERFORM z_proc_line_new USING 'NNT' $empty
                                'NNL' $empty.
    ENDIF.
  ENDIF.
ENDFORM.                    "Z_PROC_TXT_ANLS_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_inds.
  DATA: w_val     TYPE string,
        y_val     TYPE string,
        w_txt     TYPE string,y_num     TYPE anzhl,
        y_pertxt  TYPE string,
        y_tmp     TYPE string,
        y_cnum(6) TYPE c.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SINW' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SWL'.
* get number of leaves
  PERFORM z_get_wt_fmt1 USING 'SINW' CHANGING y_val.
  y_num = y_val.
* if number of leaves left is negative then change the sign
  IF y_num < 0. y_num = 0 - y_num. ENDIF.
* cast to character
  WRITE y_num TO y_cnum RIGHT-JUSTIFIED.
  MOVE y_cnum TO y_tmp.
* remove leading spaces
  SHIFT y_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. y_pertxt = 'weeks'.
    WHEN 'F'. y_pertxt = 'semaines'.
  ENDCASE.
  CONCATENATE w_txt '(' y_tmp y_pertxt ')'
         INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line USING 'SWT' w_val
                            'SWL' w_txt.
ENDFORM.                    "Z_PROC_TXT_INDS
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_inds_new.
  DATA: w_val     TYPE string,
        y_val     TYPE string,
        w_txt     TYPE string,y_num     TYPE anzhl,
        y_pertxt  TYPE string,
        y_tmp     TYPE string,
        y_cnum(6) TYPE c.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SINW' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SWL'.
* get number of leaves
  PERFORM z_get_wt_fmt1 USING 'SINW' CHANGING y_val.
  y_num = y_val.
* if number of leaves left is negative then change the sign
  IF y_num < 0. y_num = 0 - y_num. ENDIF.
* cast to character
  WRITE y_num TO y_cnum RIGHT-JUSTIFIED.
  MOVE y_cnum TO y_tmp.
* remove leading spaces
  SHIFT y_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. y_pertxt = 'weeks'.
    WHEN 'F'. y_pertxt = 'semaines'.
  ENDCASE.
  CONCATENATE w_txt '(' y_tmp y_pertxt ')'
         INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line_new USING 'SWT' w_val
                            'SWL' w_txt.
ENDFORM.                    "Z_PROC_TXT_INDS_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_indm.
  DATA: w_val     TYPE string,
        y_val     TYPE string,
        w_txt     TYPE string,y_num     TYPE anzhl,
        y_pertxt  TYPE string,
        y_tmp     TYPE string,
        y_cnum(6) TYPE c.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SINM' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SML'.
* get number of leaves
  PERFORM z_get_wt_fmt1 USING 'SINM' CHANGING y_val.
  y_num = y_val.
* if number of leaves left is negative then change the sign
  IF y_num < 0. y_num = 0 - y_num. ENDIF.
* cast to character
  WRITE y_num TO y_cnum RIGHT-JUSTIFIED.
  MOVE y_cnum TO y_tmp.
* remove leading spaces
  SHIFT y_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. y_pertxt = 'months'.
    WHEN 'F'. y_pertxt = 'mois'.
  ENDCASE.
  CONCATENATE w_txt '(' y_tmp y_pertxt ')'
         INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line USING 'SMT' w_val
                            'SML' w_txt.
ENDFORM.                    "Z_PROC_TXT_INDM
*
*--------------------------------------------------------------------*
FORM z_proc_txt_indm_new.
  DATA: w_val     TYPE string,
        y_val     TYPE string,
        w_txt     TYPE string,y_num     TYPE anzhl,
        y_pertxt  TYPE string,
        y_tmp     TYPE string,
        y_cnum(6) TYPE c.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SINM' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SML'.
* get number of leaves
  PERFORM z_get_wt_fmt1 USING 'SINM' CHANGING y_val.
  y_num = y_val.
* if number of leaves left is negative then change the sign
  IF y_num < 0. y_num = 0 - y_num. ENDIF.
* cast to character
  WRITE y_num TO y_cnum RIGHT-JUSTIFIED.
  MOVE y_cnum TO y_tmp.
* remove leading spaces
  SHIFT y_tmp LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. y_pertxt = 'months'.
    WHEN 'F'. y_pertxt = 'mois'.
  ENDCASE.
  CONCATENATE w_txt '(' y_tmp y_pertxt ')'
         INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line_new USING 'SMT' w_val
                            'SML' w_txt.
ENDFORM.                    "Z_PROC_TXT_INDM_NEW
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_mbfc.
  DATA: w_val   TYPE string,
        w_txt   TYPE string,
        w_ltext LIKE t5ucf-ltext.
  PERFORM z_get_wt_fmt USING 'MBFC' CHANGING w_val.
* get text from texts table
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'MFL'.
  SELECT SINGLE ltext FROM t5ucf "Benefit dependent coverage texts
                      INTO w_ltext
                     WHERE langu EQ gd_emp-sprsl
                       AND barea EQ '11'
                       AND depcv EQ p0167-depcv.
* prepare output string
  CONCATENATE w_txt '(' w_ltext ')' INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line USING 'MFT' w_val
                            'MFL' w_txt.
ENDFORM.                    "Z_PROC_TXT_MBFC
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_mbfc_new.
  DATA: w_val   TYPE string,
        w_txt   TYPE string,
        w_ltext LIKE t5ucf-ltext.
  PERFORM z_get_wt_fmt USING 'MBFC' CHANGING w_val.
* get text from texts table
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'MFL'.
  SELECT SINGLE ltext FROM t5ucf "Benefit dependent coverage texts
                      INTO w_ltext
                     WHERE langu EQ gd_emp-sprsl
                       AND barea EQ '11'
                       AND depcv EQ p0167-depcv.
* prepare output string
  CONCATENATE w_txt '(' w_ltext ')' INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line_new USING 'MFT' w_val
                            'MFL' w_txt.
ENDFORM.                    "Z_PROC_TXT_MBFC_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_post CHANGING p_val TYPE string.
  DATA: w_val(6) TYPE c,
        w_rline  TYPE zhrpyres.
  LOOP AT gt_results INTO w_rline.
* get 'multiplier for post adjustment';
* when using ZN00 value is stored in 'Amount per unit'
* field of result table W_RLINE-PU;
* when it's ZNPB -> multiplier is in W_RLINE-HL;
* must be an error in second schema;
    IF w_rline-id(4) EQ 'POST'.
      IF     gd_payroll_name(1) EQ 'Z'.
        WRITE w_rline-hl TO w_val RIGHT-JUSTIFIED.
      ELSEIF gd_payroll_name(1) EQ 'H'.
        WRITE w_rline-pu TO w_val RIGHT-JUSTIFIED.
      ENDIF.
      CONCATENATE p_val
                  '( mult.'
                  w_val
                  ')' INTO p_val SEPARATED BY space.
      EXIT.
    ENDIF.
  ENDLOOP.
ENDFORM.                    "Z_PROC_TXT_POST
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_rpgr CHANGING p_val TYPE string.
  DATA: w_weekscum TYPE anzhl,
        w_chl(6)   TYPE c,
        w_val      TYPE string,
        w_pertxt   TYPE string,
        w_rline    TYPE zhrpyres.
  LOOP AT gt_results INTO w_rline .
    IF w_rline-id(4) EQ 'RPGR'.
* collect Payroll Number figure
      ADD w_rline-hl TO w_weekscum.
    ENDIF.
  ENDLOOP.
* cast to character
  WRITE w_weekscum TO w_chl RIGHT-JUSTIFIED.
  MOVE w_chl TO w_val.
* remove leading spaces
  SHIFT w_val LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. w_pertxt = 'weeks'.
    WHEN 'F'. w_pertxt = 'semaines'.
  ENDCASE.
  CONCATENATE p_val '(' w_val w_pertxt ')'
         INTO p_val SEPARATED BY space.
ENDFORM.                    "Z_PROC_TXT_RPGR
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_udt_unt.
  DATA: w_dt(2)        TYPE n VALUE '01',
        w_dtype41(15)  TYPE c,
        w_date41(15)   TYPE c,
        w_dateun(10)   TYPE c,
        w_dateunes(10) TYPE c.
  FIELD-SYMBOLS:
    <fs_dtype41>,
    <fs_date41>.
  DO.
    CONCATENATE 'P0041-DAR' w_dt INTO w_dtype41.
    ASSIGN (w_dtype41) TO <fs_dtype41>.
    CONCATENATE 'P0041-DAT' w_dt INTO w_date41.
    ASSIGN (w_date41) TO <fs_date41>.
    CASE <fs_dtype41>.
      WHEN '01'.  "UN entry date
        WRITE <fs_date41> TO w_dateun.
      WHEN '06'.  "UNESCO entry date
        WRITE <fs_date41> TO w_dateunes.
      WHEN OTHERS.
    ENDCASE.
* check when to exit
    IF w_dt = '12'. EXIT. ENDIF.
* increment
    ADD 1 TO w_dt.
  ENDDO.
  PERFORM z_makentry USING 'UDT' w_dateunes.
  PERFORM z_makentry USING 'UNT' w_dateun.
ENDFORM.                    "z_proc_txt_udt_unt
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_udt_unt_new.
  DATA: w_dt(2)        TYPE n VALUE '01',
        w_dtype41(15)  TYPE c,
        w_date41(15)   TYPE c,
        w_dateun(10)   TYPE c,
        w_dateunes(10) TYPE c.
  FIELD-SYMBOLS:
    <fs_dtype41>,
    <fs_date41>.
  DO.
    CONCATENATE 'P0041-DAR' w_dt INTO w_dtype41.
    ASSIGN (w_dtype41) TO <fs_dtype41>.
    CONCATENATE 'P0041-DAT' w_dt INTO w_date41.
    ASSIGN (w_date41) TO <fs_date41>.
    CASE <fs_dtype41>.
      WHEN '01'.  "UN entry date
        WRITE <fs_date41> TO w_dateun.
      WHEN '06'.  "UNESCO entry date
        WRITE <fs_date41> TO w_dateunes.
      WHEN OTHERS.
    ENDCASE.
* check when to exit
    IF w_dt = '12'. EXIT. ENDIF.
* increment
    ADD 1 TO w_dt.
  ENDDO.
  PERFORM z_makentry_new USING 'UDT' w_dateunes.
  PERFORM z_makentry_new USING 'UNT' w_dateun.
ENDFORM.                    "z_proc_txt_udt_unt_new
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt USING    p_wtgrp TYPE string
                CHANGING p_val   TYPE string.
  DATA: w_ilmn   TYPE anzhl,
        w_chr(6) TYPE c,
        w_val    TYPE string,
        w_pertxt TYPE string,
        w_rline  TYPE zhrpyres.
  LOOP AT gt_results INTO w_rline .
    IF w_rline-id(4) EQ p_wtgrp.
* get number of monthes from "RT-Payroll Number".
* there could be more then one wtype for current group.
* we have to get this value only once.
      ADD w_rline-hl TO w_ilmn. EXIT.
    ENDIF.
  ENDLOOP.
* cast to character
  WRITE w_ilmn TO w_chr RIGHT-JUSTIFIED.
  MOVE w_chr TO w_val.
* remove leading spaces
  SHIFT w_val LEFT DELETING LEADING space.
  CASE gd_emp-sprsl(1).
    WHEN 'E'. w_pertxt = 'months'.
    WHEN 'F'. w_pertxt = 'mois'.
  ENDCASE.
  CONCATENATE p_val '(' w_val w_pertxt ')'
         INTO p_val SEPARATED BY space.
ENDFORM.                    "Z_PROC_TXT_ILON
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_dst.
  DATA: w_val   TYPE string,
        w_patxt LIKE t500p-name1,
        w_satxt LIKE t001p-btext.
* get Personnel Area text
  SELECT SINGLE name1 FROM t500p
                      INTO w_patxt
                     WHERE persa EQ p0001-werks.
* get Personnel Subarea text
  SELECT SINGLE btext FROM t001p
                      INTO w_satxt
                     WHERE werks EQ p0001-werks
                       AND btrtl EQ p0001-btrtl.
  IF    NOT w_satxt IS INITIAL
    AND NOT w_patxt IS INITIAL.
    CONCATENATE w_satxt '/' w_patxt INTO w_val.
  ENDIF.
  PERFORM z_makentry USING 'DST' w_val.
ENDFORM.                    "Z_PROC_TXT_DST
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_dst_new.
  DATA: w_val   TYPE string,
        w_patxt LIKE t500p-name1,
        w_satxt LIKE t001p-btext.
* get Personnel Area text
  SELECT SINGLE name1 FROM t500p
                      INTO w_patxt
                     WHERE persa EQ p0001-werks.
* get Personnel Subarea text
  SELECT SINGLE btext FROM t001p
                      INTO w_satxt
                     WHERE werks EQ p0001-werks
                       AND btrtl EQ p0001-btrtl.
  IF    NOT w_satxt IS INITIAL
    AND NOT w_patxt IS INITIAL.
    CONCATENATE w_satxt '/' w_patxt INTO w_val.
  ENDIF.
  PERFORM z_makentry_new USING 'DST' w_val.
ENDFORM.                    "Z_PROC_TXT_DST_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_adt.
  DATA: w_val   TYPE string,
        w_patxt LIKE t500p-name1,
        w_satxt LIKE t001p-btext.
* get Personnel Area text
  SELECT SINGLE name1 FROM t500p
                      INTO w_patxt
                     WHERE persa EQ p0395-werks.
* get Personnel Subarea text
  SELECT SINGLE btext FROM t001p
                      INTO w_satxt
                     WHERE werks EQ p0395-werks
                       AND btrtl EQ p0395-btrtl.
  IF    NOT w_satxt IS INITIAL
    AND NOT w_patxt IS INITIAL.
    CONCATENATE w_satxt '/' w_patxt INTO w_val.
  ENDIF.
  PERFORM z_makentry USING 'ADT' w_val.
ENDFORM.                    "Z_PROC_TXT_ADT
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_adt_new.
  DATA: w_val   TYPE string,
        w_patxt LIKE t500p-name1,
        w_satxt LIKE t001p-btext.
* get Personnel Area text
  SELECT SINGLE name1 FROM t500p
                      INTO w_patxt
                     WHERE persa EQ p0395-werks.
* get Personnel Subarea text
  SELECT SINGLE btext FROM t001p
                      INTO w_satxt
                     WHERE werks EQ p0395-werks
                       AND btrtl EQ p0395-btrtl.
  IF    NOT w_satxt IS INITIAL
    AND NOT w_patxt IS INITIAL.
    CONCATENATE w_satxt '/' w_patxt INTO w_val.
  ENDIF.
  PERFORM z_makentry_new USING 'ADT' w_val.
ENDFORM.                    "Z_PROC_TXT_ADT_NEW
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_out.
  DATA: w_val TYPE p1000-stext.
* Read Org Unit Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'O'
      objid                   = p0001-orgeh
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      object_text             = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry USING 'OUT' w_val.
ENDFORM.                    "z_proc_txt_out
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_out_new.
  DATA: w_val TYPE p1000-stext.
* Read Org Unit Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'O'
      objid                   = p0001-orgeh
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      object_text             = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry_new USING 'OUT' w_val.
ENDFORM.                    "z_proc_txt_out_new
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_pnt.
  DATA: w_val TYPE p1000-short.
*Read Post Number Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'S'
      objid                   = p0001-plans
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      short_text              = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry USING 'PNT' w_val.
ENDFORM.                    "z_proc_txt_pnt
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_pnt_new.
  DATA: w_val TYPE p1000-short.
*Read Post Number Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'S'
      objid                   = p0001-plans
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      short_text              = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry_new USING 'PNT' w_val.
ENDFORM.                    "z_proc_txt_pnt_new
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_f1t.
  DATA: w_val TYPE p1000-stext.
*Read Position Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'S'
      objid                   = p0001-plans
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      object_text             = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry USING 'F1T' w_val.
ENDFORM.                    "Z_PROC_TXT_F1T
*--------------------------------------------------------------------*
FORM z_proc_txt_f1t_new.
  DATA: w_val TYPE p1000-stext.
*Read Position Text.
  CALL FUNCTION 'HR_READ_FOREIGN_OBJECT_TEXT'
    EXPORTING
      otype                   = 'S'
      objid                   = p0001-plans
      begda                   = p0001-begda
      endda                   = p0001-endda
      reference_date          = p0001-begda
    IMPORTING
      object_text             = w_val
    EXCEPTIONS
      nothing_found           = 1
      wrong_objecttype        = 2
      missing_costcenter_data = 3
      missing_object_id       = 4
      OTHERS                  = 5.
  PERFORM z_makentry_new USING 'F1T' w_val.
ENDFORM.                    "Z_PROC_TXT_F1T
*--------------------------------------------------------------------*
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_txt_fi CHANGING p_val TYPE string.
  DATA: BEGIN OF w_usr21.
      INCLUDE TYPE usr21.
  DATA: END OF w_usr21.
  DATA: BEGIN OF w_adrp.
      INCLUDE TYPE adrp.
  DATA: END OF w_adrp.
* get person number using User Name in User Master Record
  SELECT SINGLE * FROM usr21 "Assign user name address key
                  INTO w_usr21
                 WHERE bname EQ sy-uname.
* get Full Name of Person
  SELECT SINGLE * FROM adrp "Persons (Business Address Services)
                  INTO w_adrp
                 WHERE persnumber EQ w_usr21-persnumber.
  p_val = w_adrp-name_text.
ENDFORM.                    "Z_PROC_TXT_FI
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_pafnum CHANGING p_val1 TYPE string
                            p_val2 TYPE string.
  DATA: w_pafnum TYPE yhr_pafnum.
* get sequential paf number for current action/request
  SELECT SINGLE * FROM yhr_pafnum
                  INTO w_pafnum
                 WHERE pernr EQ gd_emp-pernr
                   AND adate EQ gd_emp-effdate
                   AND massn EQ gd_emp-massn
                   AND massg EQ gd_emp-massg
                   AND actty EQ gd_emp-sel_type.
* if record exists it means that this paf has been
* alredy generated once -> just show paf number
* check wheather new revision was requested.
  IF sy-subrc IS INITIAL.
    IF NOT gp_nwrev IS INITIAL.
      ADD 1 TO w_pafnum-pafrev.
      MODIFY yhr_pafnum FROM w_pafnum.
    ENDIF.
  ELSE.
* otherwise it means that another paf is being generated
* get the latest senquential paf number.
    SELECT MAX( DISTINCT pafnum ) FROM yhr_pafnum
                    INTO w_pafnum-pafnum
                   WHERE pernr EQ gd_emp-pernr.
    w_pafnum-pernr  = gd_emp-pernr.
    w_pafnum-adate  = gd_emp-effdate.
    w_pafnum-massn  = gd_emp-massn.
    w_pafnum-massg  = gd_emp-massg.
    w_pafnum-actty  = gd_emp-sel_type.
* increment sequential paf number
    w_pafnum-pafnum = w_pafnum-pafnum + 1.
    w_pafnum-pafrev = $empty.
    INSERT yhr_pafnum FROM w_pafnum.
  ENDIF.
* check personnel subarea
  IF p0001-btrtl = 'PAR'.
    p_val1 = 'HQS'.
  ELSE.
    p_val1 = 'FLD'.
  ENDIF.
* build output string for paf number
  CONCATENATE p_val1
              gd_emp-effdate(4)
              '-'
              gd_emp-pernr
              '-'
              w_pafnum-pafnum INTO p_val1.
* build output string for paf revision
  IF NOT w_pafnum-pafrev IS INITIAL.
    CONCATENATE 'rev. ' w_pafnum-pafrev INTO p_val2.
  ENDIF.
ENDFORM.                    "Z_PROC_PAFNUM
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_output.
  DATA: w_val     TYPE string,
        w_val2    TYPE string,
        w_txt     TYPE string,
        w_tmp(10) TYPE c.
  CLASS cl_abap_char_utilities DEFINITION LOAD.
*...Define salary period.............................................*
  PERFORM z_get_value USING 'PANN_EMP' CHANGING gd_buffer.
  CLEAR: w_val.
  CONCATENATE '*' p0001-persg p0001-persk INTO w_val.
  FIND w_val IN gd_buffer.
  IF sy-subrc EQ 0. MOVE 12 TO gd_salperiod. ENDIF.
  PERFORM z_get_value USING 'PANN_CON' CHANGING gd_buffer.
  CLEAR: w_val.
  CONCATENATE '*' p0016-cttyp INTO w_val.
  FIND w_val IN gd_buffer.
  IF sy-subrc EQ 0. MOVE 12 TO gd_salperiod. ENDIF.
*--------------------------------------------------------------------*
* Header
*.......
*...Get Personnel Subarea Text.......................................*
  CLEAR: w_val, w_val2.
  SELECT SINGLE btext FROM t001p
                      INTO w_val
                     WHERE btrtl EQ p0001-btrtl.
*...Get Name of Employee Group
  SELECT SINGLE ptext FROM t501t
                      INTO w_val2
                     WHERE sprsl EQ gd_emp-sprsl
                       AND persg EQ p0001-persg.
*...F1 -> not used in current config
  CONCATENATE w_val w_val2 INTO w_val SEPARATED BY space.
  PERFORM z_makentry USING 'F1' w_val.
*...Add employee name................................................*
  PERFORM z_makentry USING 'F2' p0001-ename.
*...Add employee personnel number....................................*
  PERFORM z_makentry USING 'F3' gd_emp-pernr.
*...Add Nationality text.............................................*
  CLEAR: w_val.
  SELECT SINGLE natio FROM t005t "Country Names
                      INTO w_val
                     WHERE spras EQ gd_emp-sprsl
                       AND land1 EQ p0002-natio.
  PERFORM z_makentry USING 'F4' w_val.
*...Add home city and home station...................................*
  CLEAR: w_val.
  SELECT SINGLE landx FROM t005t "Country Names
                      INTO w_val
                     WHERE spras = gd_emp-sprsl
                       AND land1 = p0351-land1.
  CONCATENATE p0351-ort01 '/' w_val INTO w_val.
  PERFORM z_makentry USING 'F5' w_val.
*...Add PAF subject..................................................*
* for a moment there is a limitation to show only three additional
* action. There few if any cases when an employee has more than three
* actions effective at the same date.
  IF gd_emp-sel_type EQ $byact.
    LOOP AT gt_sbj.
      CASE sy-tabix.
        WHEN 1.
          PERFORM z_makentry USING 'F6' gt_sbj-sbj.
        WHEN 2.
          PERFORM z_makentry USING 'F7' gt_sbj-sbj.
        WHEN 3.
          PERFORM z_makentry USING 'F8' gt_sbj-sbj.
      ENDCASE.
    ENDLOOP.
  ELSE.
    PERFORM z_makentry USING 'F6' gt_sbj-sbj.
    PERFORM z_makentry USING 'F7' $empty.
    PERFORM z_makentry USING 'F8' $empty.
  ENDIF.
*...Add effective date...............................................*
  CLEAR: w_val, w_tmp.
  WRITE gd_emp-effdate TO w_tmp RIGHT-JUSTIFIED.
  w_val = w_tmp.
  PERFORM z_makentry USING 'F9' w_val.
*...Add position text................................................*
  PERFORM z_proc_txt_f1t.
*...Add contract text................................................*
  CLEAR: w_val.
  SELECT SINGLE cttxt FROM t547s
                        INTO w_val
                       WHERE sprsl EQ gd_emp-sprsl
                         AND cttyp EQ p0016-cttyp.
  PERFORM z_makentry USING 'F2T' w_val.
*...Add contract expiry date.....ALWAYS LAST OCCURENCE...............*
  CLEAR: w_tmp.
  IF p0016-ctedt NE $maxdate.
    PERFORM z_get_0016 CHANGING w_tmp.
  ENDIF.
  PERFORM z_makentry USING 'CDT' w_tmp.
*...Add grade and step...............................................*
  CLEAR: w_val.
  CONCATENATE p0008-trfgr '/' p0008-trfst INTO w_val.
  PERFORM z_makentry USING 'F3T' w_val.
*...Add next increment date......ALWAYS LAST OCCURENCE...............*
  CLEAR: w_tmp, w_txt.
  PERFORM z_get_next_inc_date CHANGING w_tmp.
  IF NOT w_tmp IS INITIAL.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F4L'.
  ENDIF.
  PERFORM z_makentry USING 'F4T' w_tmp.
  PERFORM z_makentry USING 'F4L' w_txt.
*...Add work schedule %
  CLEAR: w_tmp, w_val, w_txt.
  SELECT SINGLE atext FROM yhr_paftxt
                      INTO w_txt
                     WHERE spras EQ gd_emp-sprsl
                       AND txkey EQ 'WSL'.
  WRITE p0008-bsgrd TO w_tmp RIGHT-JUSTIFIED.
  CONCATENATE w_tmp '%' INTO w_val SEPARATED BY space.
  SHIFT w_val LEFT DELETING LEADING space.
  PERFORM z_makentry USING 'WST' w_val.
  PERFORM z_makentry USING 'WSL' w_txt.
*...Add net base salary..............................................*
  CLEAR: w_val, w_txt.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NSL'.
* check Pay Scale Group
  IF    p0008-trfgr(1) EQ 'P'  "
    OR  p0008-trfgr(1) EQ 'D'  "
    OR  p0008-trfgr(1) EQ 'A'. " ADG
* add rate (S-rate or D-rate -> with or without family dependants)
* to text line.
    IF  p0016-cttyp NE '03'. " ALD
      PERFORM z_get_rate CHANGING w_txt.
    ENDIF.
  ENDIF.
  PERFORM z_get_wt_fmt2 USING 'BASE' w_txt CHANGING w_val.
  PERFORM z_proc_line USING 'F5T' w_val
                            'NSL' w_txt.
*...Add pensionable remuneration.....................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'YNPF' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F6L'.
* if the person is not affiliated to NPO Pension Fund
* do not show 'pensionable remuneration'
  IF    p0961-pfsta EQ space
     OR p0961-pfsta EQ '0'.
    CLEAR: w_txt, w_val.
  ENDIF.
  PERFORM z_makentry USING 'F6T' w_val.
  PERFORM z_makentry USING 'F6L' w_txt.
*...Add post adjustment..............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'POST' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F7L'.
* adjust text with number value (like: mult. 60,20)
  PERFORM z_proc_txt_post CHANGING w_txt.
  PERFORM z_proc_line USING 'F7T' w_val
                            'F7L' w_txt.
*...Add mobility & hardship allowance................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'MHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'MHL'.
  PERFORM z_proc_line USING 'F8T' w_val
                            'MHL' w_txt.
*...Add Additional hardship allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AHA'.
  PERFORM z_proc_line USING 'AHT' w_val
                            'AHA' w_txt.
*...Add Non family service allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'NFSA' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NFS'.
  PERFORM z_proc_line USING 'NFT' w_val
                            'NFS' w_txt.
*...Add language allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LAAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LAL'.
  PERFORM z_proc_line USING 'LAT' w_val
                            'LAL' w_txt.
*...Add secondary dependent allowance................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SDL'.
  PERFORM z_proc_line USING 'SDT' w_val
                            'SDL' w_txt.
*...Add remarks......................................................*
* NOT USED
*  clear: W_VAL, W_TXT.
*  perform Z_MAKENTRY using 'R0' W_TXT.
*  perform Z_MAKENTRY using 'R1' W_TXT.
*  perform Z_MAKENTRY using 'R2' W_TXT.
*  perform Z_MAKENTRY using 'R3' W_TXT        .
*  perform Z_MAKENTRY using 'R4' W_TXT.
*  perform Z_MAKENTRY using 'R5' W_TXT.
*...Add current date.................................................*
  CLEAR: w_tmp.
  WRITE sy-datum TO w_tmp RIGHT-JUSTIFIED.
  PERFORM z_makentry USING 'FD' w_tmp.
*...Add HR officer full name.........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_proc_txt_fi CHANGING w_txt.
  PERFORM z_makentry USING 'FI' w_txt.
  PERFORM z_makentry USING 'USR' sy-uname.
*...Add pension number...............................................*
  PERFORM z_makentry USING 'PFN' p0961-pfnum.
*...Add gross base salary............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'GBAS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'GSL'.
  PERFORM z_proc_line USING 'GST' w_val
                            'GSL' w_txt.
*...Add child allowance..............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CAL'.
* add number of children to output string
  CONCATENATE w_txt gd_emp-nchild INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line USING 'CAT' w_val
                            'CAL' w_txt.
*...Add rental subsidy...............................................*
  CLEAR: w_val, w_txt.
  IF gf_rnts_is_suppressed NE $cross.
* get value and text only if it's not the case of suppression
    PERFORM z_get_wt_fmt USING 'RNTS' CHANGING w_val.
    SELECT SINGLE atext FROM yhr_paftxt
                            INTO w_txt
                           WHERE spras EQ gd_emp-sprsl
                             AND txkey EQ 'RNL'.
  ENDIF.
  PERFORM z_proc_line USING 'RNT' w_val
                            'RNL' w_txt.
*...Add spouse allowance.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SPL'.
  PERFORM z_proc_line USING 'SPT' w_val
                            'SPL' w_txt.
*...Add spouse differential.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPDI' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SUD'.
  PERFORM z_proc_line USING 'SUT' w_val
                            'SUD' w_txt.
*...Add pension contribution.........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'PENC' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PCL'.
  PERFORM z_proc_line USING 'PCT' w_val
                            'PCL' w_txt.
*...Add MBF contribution.............................................*
  PERFORM z_proc_txt_mbfc.
*...Add other allowances.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'OSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'OSL'.
  PERFORM z_proc_line USING 'OST' w_val
                            'OSL' w_txt.
*...Family all. CAF Special...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CSL'.
  PERFORM z_proc_line USING 'CST' w_val
                            'CSL' w_txt.
*...Family all. CAF..................................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FSL'.
  PERFORM z_proc_line USING 'FST' w_val
                            'FSL' w_txt.
*...Add final amount of family allowance.............................*
* TO BE CLARIFIED
  CLEAR: w_val, w_txt.
  PERFORM z_makentry USING 'ODT' w_val.
  PERFORM z_makentry USING 'ODL' w_val.
*...Add non-resident allowance.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'NRAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NRL'.
  PERFORM z_proc_line USING 'NRT' w_val
                            'NRL' w_txt.
*...Add secondary language allowance.................................* 1
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SLAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SLL'.
  PERFORM z_proc_line USING 'SLT' w_val
                            'SLL' w_txt.
*...Add service allowance............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SEAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SEL'.
  PERFORM z_proc_line USING 'SET' w_val
                            'SEL' w_txt.
*...Add family allowance.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FMAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FML'.
  PERFORM z_proc_line USING 'FMT' w_val
                            'FML' w_txt.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'RPL'.
  PERFORM z_proc_line USING 'RPT' w_val
                            'RPL' w_txt.
*...Add transportation allowance.....................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'TRAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'TRL'.
  PERFORM z_proc_line USING 'TRT' w_val
                            'TRL' w_txt.
*...Add spec. pers. non-pensionable allowance........................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SNAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SNL'.
  PERFORM z_proc_line USING 'SNT' w_val
                            'SNL' w_txt.
*...Add personal transitional allowance..............................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'PTAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PTL'.
  PERFORM z_proc_line USING 'PTT' w_val
                            'PTL' w_txt.
*...Add assignment grant (DSA).......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AGDS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AGL'.
  PERFORM z_proc_line USING 'AGT' w_val
                            'AGL' w_txt.
*...Add assignment grant (lump sum)..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AGLS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'ALL'.
  PERFORM z_proc_line USING 'ALT' w_val
                            'ALL' w_txt.
*...Add settling in grant (DSA).......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SGDS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SID'.
  PERFORM z_proc_line USING 'SIT' w_val
                            'SID' w_txt.
*...Add settling grant (lump sum)..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SGLS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SGL'.
  PERFORM z_proc_line USING 'SGT' w_val
                            'SGL' w_txt.
*...Add repatriation grant...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPGR' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'RGL'.
  PERFORM z_proc_txt_rpgr CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line USING 'RGT' w_val
                              'RGL' w_txt.
  ELSE.
    PERFORM z_proc_line USING 'RGT' $empty
                              'RGL' $empty.
  ENDIF.
*...Add separation indemnity........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'TMID' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'TIL'.
  PERFORM z_proc_txt USING 'TMID' CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line USING 'TIT' w_val
                              'TIL' w_txt.
  ELSE.
    PERFORM z_proc_line USING 'TIT' $empty
                              'TIL' $empty.
  ENDIF.
*...Add death grant..................................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DEGR' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DGL'.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line USING 'DGT' w_val
                              'DGL' w_txt.
  ELSE.
    PERFORM z_proc_line USING 'DGT' $empty
                              'DGL' $empty.
  ENDIF.
*...Add in lieu of notice............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'ILON' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'ILL'.
  PERFORM z_proc_txt USING 'ILON' CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line USING 'ILT' w_val
                              'ILL' w_txt.
  ELSE.
    PERFORM z_proc_line USING 'ILT' $empty
                              'ILL' $empty.
  ENDIF.
*...Add annual leave settlement......................................*
  PERFORM z_proc_txt_anls.
*...Add hairdressing indemnity.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'HDID' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'HDL'.
  PERFORM z_proc_line USING 'HDT' w_val
                            'HDL' w_txt.
*...Add closing Allowance............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CLAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CLL'.
  PERFORM z_proc_line USING 'CLT' w_val
                            'CLL' w_txt.
*...Add special post allowance.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPPA' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PAL'.
  CONCATENATE w_txt
              ' ('
              p0509-trfgr "Pay scale group of the higher duty position
              '/'
              p0509-trfst "Pay scale level of the higher duty position
              ')' INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line USING 'PAT' w_val
                            'PAL' w_txt.
*...Separation indemnity (m)............................................* "1311
  PERFORM z_proc_txt_indm.
*...Separation indemnity (w)............................................* "1314
  PERFORM z_proc_txt_inds.
*...Except. separ. payt. temp..........................................* "1572
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'EXSP' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'EXL'.
  PERFORM z_proc_line USING 'EXT' w_val
                            'EXL' w_txt.
*...Add Agency fees............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AFEE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AFE'.
  PERFORM z_proc_line USING 'AFT' w_val
                            'AFE' w_txt.
*...Add deduction for housing provided................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DDHP' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DHL'.
  PERFORM z_proc_line USING 'DHT' w_val
                            'DHL' w_txt.
*...Add deduction disability benefit..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DEDB' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DDB'.
  PERFORM z_proc_line USING 'DDT' w_val
                            'DDL' w_txt.
*...Add deduction - social security...................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DDSS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SSL'.
  PERFORM z_proc_line USING 'SST' w_val
                            'SSL' w_txt.
*...Lloyds Temporary EE...............................................* "1810
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LTEE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LEL'.
  PERFORM z_proc_line USING 'LET' w_val
                            'LEL' w_txt.
*...Lloyds Temp Field EE.............................................* "1820
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LTFE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LFL'.
  PERFORM z_proc_line USING 'LFT' w_val
                            'LFL' w_txt.
*...Remb Pension SLWOP Staff........................................* "7012
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPSS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'R1L'.
  PERFORM z_proc_line USING 'R1T' w_val
                            'R1L' w_txt.
*...Add birth date....................................................*
  CLEAR: w_tmp.
  WRITE p0002-gbdat TO w_tmp RIGHT-JUSTIFIED.
  PERFORM z_makentry USING 'BDA' w_tmp.
*...Add internal mailing address......................................*
  CLEAR: w_val.
  CONCATENATE p0006-name2 p0006-stras INTO w_val SEPARATED BY space.
  PERFORM z_makentry USING 'IMA' w_val.
*...Add UNESCO and UN entry date......................................*
  PERFORM z_proc_txt_udt_unt.
*...Add duty station..................................................*
  PERFORM z_proc_txt_dst.
*...Add Administrative Duty Station...................................*
  PERFORM z_proc_txt_adt.
*...Add organizational unit...........................................*
  PERFORM z_proc_txt_out.
*...Add post number...................................................*
  PERFORM z_proc_txt_pnt.
*...Add automatic texts...............................................*
* NOT USED in current config.
  CLEAR: w_txt.
  PERFORM z_makentry USING 'AT1' w_txt.
  PERFORM z_makentry USING 'AT2' w_txt.
  PERFORM z_makentry USING 'AT3' w_txt.
  PERFORM z_makentry USING 'AT4' w_txt.
*...create PAF document number or modify revision if one exists.......*
  CLEAR: w_val, w_val2.
  PERFORM z_proc_pafnum CHANGING w_val w_val2.
  PERFORM z_makentry USING 'PDN' w_val.
  PERFORM z_makentry USING 'PDR' w_val2.
*...Add e-mail address
  CLEAR: w_val.
  w_val = p0105-usrid_long.
  SHIFT w_val LEFT DELETING LEADING space.
  PERFORM z_makentry USING 'EMA' w_val.
*...Add marital status
  CLEAR: w_val.
  SELECT SINGLE ftext FROM t502t "Marital Status Designators
                      INTO w_val
                     WHERE sprsl EQ gd_emp-sprsl
                       AND famst EQ p0002-famst.
  PERFORM z_makentry USING 'MST' w_val.
ENDFORM.                    "z_proc_output
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_output_new.
  DATA: w_val     TYPE string,
        w_val2    TYPE string,
        w_txt     TYPE string,
        w_tmp(10) TYPE c.
  CLASS cl_abap_char_utilities DEFINITION LOAD.
*...Define salary period.............................................*
  PERFORM z_get_value USING 'PANN_EMP' CHANGING gd_buffer.
  CLEAR: w_val.
  CONCATENATE '*' p0001-persg p0001-persk INTO w_val.
  FIND w_val IN gd_buffer.
  IF sy-subrc EQ 0. MOVE 12 TO gd_salperiod. ENDIF.
  PERFORM z_get_value USING 'PANN_CON' CHANGING gd_buffer.
  CLEAR: w_val.
  CONCATENATE '*' p0016-cttyp INTO w_val.
  FIND w_val IN gd_buffer.
  IF sy-subrc EQ 0. MOVE 12 TO gd_salperiod. ENDIF.
*--------------------------------------------------------------------*
* Header
*.......
*...Get Personnel Subarea Text.......................................*
  CLEAR: w_val, w_val2.
  SELECT SINGLE btext FROM t001p
                      INTO w_val
                     WHERE btrtl EQ p0001-btrtl.
*...Get Name of Employee Group
  SELECT SINGLE ptext FROM t501t
                      INTO w_val2
                     WHERE sprsl EQ gd_emp-sprsl
                       AND persg EQ p0001-persg.
*...F1 -> not used in current config
  CONCATENATE w_val w_val2 INTO w_val SEPARATED BY space.
  PERFORM z_makentry_new USING 'F1' w_val.
*...Add employee name................................................*
  PERFORM z_makentry_new USING 'F2' p0001-ename.
*...Add employee personnel number....................................*
  PERFORM z_makentry_new USING 'F3' gd_emp-pernr.
*...Add Nationality text.............................................*
  CLEAR: w_val.
  SELECT SINGLE natio FROM t005t "Country Names
                      INTO w_val
                     WHERE spras EQ gd_emp-sprsl
                       AND land1 EQ p0002-natio.
  PERFORM z_makentry_new USING 'F4' w_val.
*...Add home city and home station...................................*
  CLEAR: w_val.
  SELECT SINGLE landx FROM t005t "Country Names
                      INTO w_val
                     WHERE spras = gd_emp-sprsl
                       AND land1 = p0351-land1.
  CONCATENATE p0351-ort01 '/' w_val INTO w_val.
  PERFORM z_makentry_new USING 'F5' w_val.
*...Add PAF subject..................................................*
* for a moment there is a limitation to show only three additional
* action. There few if any cases when an employee has more than three
* actions effective at the same date.
  IF gd_emp-sel_type EQ $byact.
    LOOP AT gt_sbj.
      CASE sy-tabix.
        WHEN 1.
          PERFORM z_makentry_new USING 'F6' gt_sbj-sbj.
        WHEN 2.
          PERFORM z_makentry_new USING 'F7' gt_sbj-sbj.
        WHEN 3.
          PERFORM z_makentry_new USING 'F8' gt_sbj-sbj.
      ENDCASE.
    ENDLOOP.
  ELSE.
    PERFORM z_makentry_new USING 'F6' gt_sbj-sbj.
    PERFORM z_makentry_new USING 'F7' $empty.
    PERFORM z_makentry_new USING 'F8' $empty.
  ENDIF.
*...Add effective date...............................................*
  CLEAR: w_val, w_tmp.
  WRITE gd_emp-effdate TO w_tmp RIGHT-JUSTIFIED.
  w_val = w_tmp.
  PERFORM z_makentry_new USING 'F9' w_val.
*...Add position text................................................*
  PERFORM z_proc_txt_f1t_new. " F1T
*...Add contract text................................................*
  CLEAR: w_val.
  SELECT SINGLE cttxt FROM t547s
                        INTO w_val
                       WHERE sprsl EQ gd_emp-sprsl
                         AND cttyp EQ p0016-cttyp.
  PERFORM z_makentry_new USING 'F2T' w_val.
*...Add contract expiry date.....ALWAYS LAST OCCURENCE...............*
  CLEAR: w_tmp.
  IF p0016-ctedt NE $maxdate.
    PERFORM z_get_0016 CHANGING w_tmp.
  ENDIF.
  PERFORM z_makentry_new USING 'CDT' w_tmp.
*...Add grade and step...............................................*
  CLEAR: w_val.
  CONCATENATE p0008-trfgr '/' p0008-trfst INTO w_val.
  PERFORM z_makentry_new USING 'F3T' w_val.
*...Add next increment date......ALWAYS LAST OCCURENCE...............*
  CLEAR: w_tmp, w_txt.
  PERFORM z_get_next_inc_date CHANGING w_tmp.
  IF NOT w_tmp IS INITIAL.
    SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F4L'.
  ENDIF.
  PERFORM z_makentry_new USING 'F4T' w_tmp.
  PERFORM z_makentry_new USING 'F4L' w_txt.
*...Add work schedule %
  CLEAR: w_tmp, w_val, w_txt.
  SELECT SINGLE atext FROM yhr_paftxt
                      INTO w_txt
                     WHERE spras EQ gd_emp-sprsl
                       AND txkey EQ 'WSL'.
  WRITE p0008-bsgrd TO w_tmp RIGHT-JUSTIFIED.
  CONCATENATE w_tmp '%' INTO w_val SEPARATED BY space.
  SHIFT w_val LEFT DELETING LEADING space.
  PERFORM z_makentry_new USING 'WST' w_val.
  PERFORM z_makentry_new USING 'WSL' w_txt.
*...Add net base salary..............................................*
  CLEAR: w_val, w_txt.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NSL'.
* check Pay Scale Group
  IF    p0008-trfgr(1) EQ 'P'  "
    OR  p0008-trfgr(1) EQ 'D'  "
    OR  p0008-trfgr(1) EQ 'A'. " ADG
* add rate (S-rate or D-rate -> with or without family dependants)
* to text line.
    IF  p0016-cttyp NE '03'. " ALD
      PERFORM z_get_rate CHANGING w_txt.
    ENDIF.
  ENDIF.
  PERFORM z_get_wt_fmt2 USING 'BASE' w_txt CHANGING w_val.
  PERFORM z_proc_line_new USING 'F5T' w_val
                            'NSL' w_txt.
*...Add pensionable remuneration.....................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'YNPF' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F6L'.
* if the person is not affiliated to NPO Pension Fund
* do not show 'pensionable remuneration'
  IF    p0961-pfsta EQ space
     OR p0961-pfsta EQ '0'.
    CLEAR: w_txt, w_val.
  ENDIF.
  PERFORM z_makentry_new USING 'F6T' w_val.
  PERFORM z_makentry_new USING 'F6L' w_txt.
*...Add post adjustment..............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'POST' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'F7L'.
* adjust text with number value (like: mult. 60,20)
  PERFORM z_proc_txt_post CHANGING w_txt.
  PERFORM z_proc_line_new USING 'F7T' w_val
                            'F7L' w_txt.
*...Add mobility & hardship allowance................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'MHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'MHL'.
  PERFORM z_proc_line_new USING 'F8T' w_val
                            'MHL' w_txt.
*...Add Additional hardship allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AHA'.
  PERFORM z_proc_line_new USING 'AHT' w_val
                            'AHA' w_txt.
*...Add Non family service allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'NFSA' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NFS'.
  PERFORM z_proc_line_new USING 'NFT' w_val
                            'NFS' w_txt.
*...Add language allowance...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LAAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LAL'.
  PERFORM z_proc_line_new USING 'LAT' w_val
                            'LAL' w_txt.
*...Add secondary dependent allowance................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SDL'.
  PERFORM z_proc_line_new USING 'SDT' w_val
                            'SDL' w_txt.
*...Add remarks......................................................*
* NOT USED
*  clear: W_VAL, W_TXT.
*  perform Z_MAKENTRY using 'R0' W_TXT.
*  perform Z_MAKENTRY using 'R1' W_TXT.
*  perform Z_MAKENTRY using 'R2' W_TXT.
*  perform Z_MAKENTRY using 'R3' W_TXT        .
*  perform Z_MAKENTRY using 'R4' W_TXT.
*  perform Z_MAKENTRY using 'R5' W_TXT.
*...Add current date.................................................*
  CLEAR: w_tmp.
  WRITE sy-datum TO w_tmp RIGHT-JUSTIFIED.
  PERFORM z_makentry_new USING 'FD' w_tmp.
*...Add HR officer full name.........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_proc_txt_fi CHANGING w_txt.
  PERFORM z_makentry_new USING 'FI' w_txt.
  PERFORM z_makentry_new USING 'USR' sy-uname.
*...Add pension number...............................................*
  PERFORM z_makentry_new USING 'PFN' p0961-pfnum.
*...Add gross base salary............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'GBAS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'GSL'.
  PERFORM z_proc_line_new USING 'GST' w_val
                            'GSL' w_txt.
*...Add child allowance..............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CHAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CAL'.
* add number of children to output string
  CONCATENATE w_txt gd_emp-nchild INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line_new USING 'CAT' w_val
                            'CAL' w_txt.
*...Add rental subsidy...............................................*
  CLEAR: w_val, w_txt.
  IF gf_rnts_is_suppressed NE $cross.
* get value and text only if it's not the case of suppression
    PERFORM z_get_wt_fmt USING 'RNTS' CHANGING w_val.
    SELECT SINGLE atext FROM yhr_paftxt
                            INTO w_txt
                           WHERE spras EQ gd_emp-sprsl
                             AND txkey EQ 'RNL'.
  ENDIF.
  PERFORM z_proc_line_new USING 'RNT' w_val
                            'RNL' w_txt.
*...Add spouse allowance.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SPL'.
  PERFORM z_proc_line_new USING 'SPT' w_val
                            'SPL' w_txt.
*...Add spouse differential.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPDI' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SUD'.
  PERFORM z_proc_line_new USING 'SUT' w_val
                            'SUD' w_txt.
*...Add pension contribution.........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'PENC' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PCL'.
  PERFORM z_proc_line_new USING 'PCT' w_val
                            'PCL' w_txt.
*...Add MBF contribution.............................................*
  PERFORM z_proc_txt_mbfc_new.
*...Add other allowances.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'OSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'OSL'.
  PERFORM z_proc_line_new USING 'OST' w_val
                            'OSL' w_txt.
*...Family all. CAF..................................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FSL'.
  PERFORM z_proc_line_new USING 'FST' w_val
                            'FSL' w_txt.
*...Family all. CAF Special...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CSAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CSL'.
  PERFORM z_proc_line_new USING 'CST' w_val
                            'CSL' w_txt.
*...Add final amount of family allowance.............................*
* TO BE CLARIFIED
  CLEAR: w_val, w_txt.
  PERFORM z_makentry_new USING 'ODT' w_val.
  PERFORM z_makentry_new USING 'ODL' w_val.
*...Add non-resident allowance.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'NRAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'NRL'.
  PERFORM z_proc_line_new USING 'NRT' w_val
                            'NRL' w_txt.
*break a_ahounou.
*...Add secondary language allowance.................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SLAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SLL'.
  PERFORM z_proc_line_new USING 'SLT' w_val
                            'SLL' w_txt.
*...Add service allowance............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SEAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SEL'.
  PERFORM z_proc_line_new USING 'SET' w_val
                            'SEL' w_txt.
*...Add family allowance.............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FMAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FML'.
  PERFORM z_proc_line_new USING 'FMT' w_val
                            'FML' w_txt.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FMAT' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FTL'.
  PERFORM z_proc_line_new USING 'FTT' w_val
                            'FTL' w_txt.
*...Add family allowance / Single Parent..............................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'FMAS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'FCL'.
  PERFORM z_proc_line_new USING 'FCT' w_val
                            'FCL' w_txt.
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'RPL'.
  PERFORM z_proc_line_new USING 'RPT' w_val
                            'RPL' w_txt.
*...Add transportation allowance.....................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'TRAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'TRL'.
  PERFORM z_proc_line_new USING 'TRT' w_val
                            'TRL' w_txt.
*...Add spec. pers. non-pensionable allowance........................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SNAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SNL'.
  PERFORM z_proc_line_new USING 'SNT' w_val
                            'SNL' w_txt.
*...Add personal transitional allowance..............................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'PTAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PTL'.
  PERFORM z_proc_line_new USING 'PTT' w_val
                            'PTL' w_txt.
*...Add assignment grant (DSA).......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AGDS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AGL'.
  PERFORM z_proc_line_new USING 'AGT' w_val
                            'AGL' w_txt.
*...Add assignment grant (lump sum)..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AGLS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'ALL'.
  PERFORM z_proc_line_new USING 'ALT' w_val
                            'ALL' w_txt.
*...Add settling in grant (DSA).......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SGDS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SID'.
  PERFORM z_proc_line_new USING 'SIT' w_val
                            'SID' w_txt.
*...Add settling grant (lump sum)..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SGLS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SGL'.
  PERFORM z_proc_line_new USING 'SGT' w_val
                            'SGL' w_txt.
*...Add repatriation grant...........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPGR' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'RGL'.
  PERFORM z_proc_txt_rpgr CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line_new USING 'RGT' w_val
                              'RGL' w_txt.
  ELSE.
    PERFORM z_proc_line_new USING 'RGT' $empty
                              'RGL' $empty.
  ENDIF.
*...Add separation indemnity........................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'TMID' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'TIL'.
  PERFORM z_proc_txt USING 'TMID' CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line_new USING 'TIT' w_val
                              'TIL' w_txt.
  ELSE.
    PERFORM z_proc_line_new USING 'TIT' $empty
                              'TIL' $empty.
  ENDIF.
*...Add death grant..................................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DEGR' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DGL'.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line_new USING 'DGT' w_val
                              'DGL' w_txt.
  ELSE.
    PERFORM z_proc_line_new USING 'DGT' $empty
                              'DGL' $empty.
  ENDIF.
*...Add in lieu of notice............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'ILON' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'ILL'.
  PERFORM z_proc_txt USING 'ILON' CHANGING w_txt.
* If X1, X2 or XA then show values. It means that this type of
* allowance or grant relates only to those three action types.
  IF gf_x1x2xa EQ $cross.
    PERFORM z_proc_line_new USING 'ILT' w_val
                              'ILL' w_txt.
  ELSE.
    PERFORM z_proc_line_new USING 'ILT' $empty
                              'ILL' $empty.
  ENDIF.
*...Add annual leave settlement......................................*
  PERFORM z_proc_txt_anls_new.
*...Add hairdressing indemnity.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'HDID' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'HDL'.
  PERFORM z_proc_line_new USING 'HDT' w_val
                            'HDL' w_txt.
*...Add closing Allowance............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'CLAL' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'CLL'.
  PERFORM z_proc_line_new USING 'CLT' w_val
                            'CLL' w_txt.
*...Add special post allowance.......................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'SPPA' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'PAL'.
  CONCATENATE w_txt
              ' ('
              p0509-trfgr "Pay scale group of the higher duty position
              '/'
              p0509-trfst "Pay scale level of the higher duty position
              ')' INTO w_txt SEPARATED BY space.
  PERFORM z_proc_line_new USING 'PAT' w_val
                            'PAL' w_txt.
*...Separation indemnity (m)............................................* "1311
  PERFORM z_proc_txt_indm_new.
*...Separation indemnity (w)............................................* "1314
  PERFORM z_proc_txt_inds_new.
*...Except. separ. payt. temp..........................................* "1572
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'EXSP' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'EXL'.
  PERFORM z_proc_line_new USING 'EXT' w_val
                            'EXL' w_txt.
*...Add Agency fees............................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'AFEE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'AFE'.
  PERFORM z_proc_line_new USING 'AFT' w_val
                            'AFE' w_txt.
*...Add deduction for housing provided................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DDHP' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DHL'.
  PERFORM z_proc_line_new USING 'DHT' w_val
                            'DHL' w_txt.
*...Add deduction disability benefit..................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DEDB' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'DDB'.
  PERFORM z_proc_line_new USING 'DDT' w_val
                            'DDL' w_txt.
*...Add deduction - social security...................................*
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'DDSS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'SSL'.
  PERFORM z_proc_line_new USING 'SST' w_val
                            'SSL' w_txt.
*...Lloyds Temporary EE...............................................* "1810
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LTEE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LEL'.
  PERFORM z_proc_line_new USING 'LET' w_val
                            'LEL' w_txt.
*...Lloyds Temp Field EE.............................................* "1820
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'LTFE' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'LFL'.
  PERFORM z_proc_line_new USING 'LFT' w_val
                            'LFL' w_txt.
*...Remb Pension SLWOP Staff........................................* "7012
  CLEAR: w_val, w_txt.
  PERFORM z_get_wt_fmt USING 'RPSS' CHANGING w_val.
  SELECT SINGLE atext FROM yhr_paftxt
                        INTO w_txt
                       WHERE spras EQ gd_emp-sprsl
                         AND txkey EQ 'R1L'.
  PERFORM z_proc_line_new USING 'R1T' w_val
                            'R1L' w_txt.
*...Add birth date....................................................*
  CLEAR: w_tmp.
  WRITE p0002-gbdat TO w_tmp RIGHT-JUSTIFIED.
  PERFORM z_makentry_new USING 'BDA' w_tmp.
*...Add internal mailing address......................................*
  CLEAR: w_val.
  CONCATENATE p0006-name2 p0006-stras INTO w_val SEPARATED BY space.
  PERFORM z_makentry_new USING 'IMA' w_val.
*...Add UNESCO and UN entry date......................................*
  PERFORM z_proc_txt_udt_unt_new.
*...Add duty station..................................................*
  PERFORM z_proc_txt_dst_new.
*...Add Administrative Duty Station...................................*
  PERFORM z_proc_txt_adt_new.
*...Add organizational unit...........................................*
  PERFORM z_proc_txt_out_new.
*...Add post number...................................................*
  PERFORM z_proc_txt_pnt_new.
*...Add automatic texts...............................................*
* NOT USED in current config.
  CLEAR: w_txt.
  PERFORM z_makentry_new USING 'AT1' w_txt.
  PERFORM z_makentry_new USING 'AT2' w_txt.
  PERFORM z_makentry_new USING 'AT3' w_txt.
  PERFORM z_makentry_new USING 'AT4' w_txt.
*...create PAF document number or modify revision if one exists.......*
  CLEAR: w_val, w_val2.
  PERFORM z_proc_pafnum CHANGING w_val w_val2.
  PERFORM z_makentry_new USING 'PDN' w_val.
  PERFORM z_makentry_new USING 'PDR' w_val2.
*...Add e-mail address
  CLEAR: w_val.
  w_val = p0105-usrid_long.
  SHIFT w_val LEFT DELETING LEADING space.
  PERFORM z_makentry_new USING 'EMA' w_val.
*...Add marital status
  CLEAR: w_val.
  SELECT SINGLE ftext FROM t502t "Marital Status Designators
                      INTO w_val
                     WHERE sprsl EQ gd_emp-sprsl
                       AND famst EQ p0002-famst.
  PERFORM z_makentry_new USING 'MST' w_val.
* EVO FGU091019
  CLEAR w_val.
  IF p0001-persg = '1'.
    IF gd_emp-sprsl = 'E'.
      CONCATENATE
      'N.B. Please note that due to an ongoing review of the post adjustment system
      'the classification memo of this month is not published yet.'
      'The correct post adjustment will be reflected in your payslip.'
      INTO w_val SEPARATED BY space.
    ELSEIF gd_emp-sprsl = 'F'.
      CONCATENATE
      'N.b. Veuillez noter qu''en raison d''une revue du système de l’ajustement de
      'le memo officiel concernant l’ajustement de poste de ce mois n’a pas été enco
      'L''ajustement de poste officiel et mis à jour sera reflété dans votre bulleti
     INTO w_val SEPARATED BY space.
    ENDIF.
  ENDIF.
  PERFORM z_makentry_new USING 'FOO' w_val.
ENDFORM.                    "z_proc_output_new
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_print_results.
  DATA: w_rline  TYPE zhrpyres,
        w_pu(17) TYPE c,
        w_hl(17) TYPE c,
        w_bt(17) TYPE c.
  DATA: wa_t512t  TYPE t512t.
  WRITE: /5 'Wage Types relevant for current employee'.
  ULINE AT /5(109).
  WRITE:  /5  'ID:     ',
          15  'W.Type  ',
          25  ' Amount per unit',
          42  '          Number',
          59  '          Amount',
          76  ' Curr',
          83  'W.T.text'.
  ULINE AT /5(109).
  LOOP AT gt_results INTO w_rline.
    IF   NOT w_rline-pu EQ 0
      OR NOT w_rline-hl EQ 0
      OR NOT w_rline-bt EQ 0.
      SELECT SINGLE * FROM t512t INTO wa_t512t
                     WHERE sprsl EQ gd_emp-sprsl
                     AND   molga EQ gd_emp-molga
                     AND   lgart EQ w_rline-wt.
      WRITE w_rline-pu TO w_pu.
      WRITE w_rline-hl TO w_hl.
      WRITE w_rline-bt TO w_bt.
      WRITE:  /5  w_rline-id,
              15  w_rline-wt,
              25  w_pu,
              42  w_hl,
              59  w_bt,
              76  w_rline-cu RIGHT-JUSTIFIED,
              83  wa_t512t-lgtxt.
    ENDIF.
  ENDLOOP.
  ULINE AT /5(109).
  SKIP.
ENDFORM.                    "z_print_results
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_print_rt.
  CONSTANTS:
        c_rt(5) TYPE c VALUE 'RT:  '.
  DATA: w_header(85) TYPE c,
        w_pu(17)     TYPE c,
        w_hl(17)     TYPE c,
        w_bt(17)     TYPE c.
  DATA: wa_t512t  TYPE t512t.
  WRITE: /5 'Simulation results'.
  ULINE AT /5(109).
  WRITE:   /5 sy-vline,  6 '       ',
           13 sy-vline, 14 'Emp.Sg.',
           22 sy-vline, 23 'W.Type.',
           30 sy-vline, 31 'W.T.Text',
           51 sy-vline, 52 'Split.N',
           59 sy-vline, 60 ' Amount per Unit',
           77 sy-vline, 78 '          Number',
           95 sy-vline, 96 '          Amount',
          113 sy-vline.
  ULINE AT /5(109).
  LOOP AT rt.
    SELECT SINGLE * FROM t512t INTO wa_t512t
                    WHERE sprsl EQ gd_emp-sprsl
                    AND   molga EQ gd_emp-molga
                    AND   lgart EQ rt-lgart.
    WRITE rt-betpe TO w_pu.
    WRITE rt-anzhl TO w_hl.
    WRITE rt-betrg TO w_bt.
    WRITE: /5 sy-vline, 6  c_rt,
           13 sy-vline, 14 rt-abart,
           22 sy-vline, 23 rt-lgart,
           30 sy-vline, 31 wa_t512t-lgtxt(20),
           51 sy-vline, 52 rt-apznr,
           59 sy-vline, 60 w_pu,
           77 sy-vline, 78 w_hl,
           95 sy-vline, 96 w_bt,
          113 sy-vline.
  ENDLOOP.
  ULINE AT /5(109).
  SKIP.
ENDFORM.                    "z_print_rt
*&---------------------------------------------------------------------*
*&      Form  z_print_emp_data
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
FORM z_print_summary.
  SKIP.
*  write: /5 'Start Date', 70 GD_EMP-BEGDA.
*  write: /5 'End Date', 70 GD_EMP-ENDDA.
*  write: /5 'Reference personnel number', 70 GD_EMP-RFPNR.
*  write: /5 'Company Code', 70 GD_EMP-BUKRS.
*  write: /5 'Personnel Area', 70 GD_EMP-WERKS.
*  write: /5 'Personnel Subarea', 70 GD_EMP-BTRTL.
*  write: /5 'Employee Group', 70 GD_EMP-PERSG.
*  write: /5 'Employee Subgroup', 70 GD_EMP-PERSK.
*  write: /5 'Organizational Unit', 70 GD_EMP-ORGEH.
*  write: /5 'Job', 70 GD_EMP-STELL.
*  write: /5 'Position', 70 GD_EMP-PLANS.
*  write: /5 'Controlling Area of Master Cost Center', 70 GD_EMP-KOKRS.
*  write: /5 'Master Cost Center', 70 GD_EMP-KOSTL.
*  write: /5 'Payroll Area', 70 GD_EMP-ABKRS.
*  write: /5 'Country Grouping', 70 GD_EMP-MOLGA.
*  write: /5 'Pay scale type', 70 GD_EMP-TRFAR.
*  write: /5 'Pay Scale Area', 70 GD_EMP-TRFGB.
*  write: /5 'ES grouping for collective agreement provision', 70 GD_EMP-TRFKZ.
*  write: /5 'Pay Scale Group', 70 GD_EMP-TRFGR.
*  write: /5 'Pay Scale Level', 70 GD_EMP-TRFST.
*  write: /5 'Capacity utilization level', 70 GD_EMP-BSGRD.
*  write: /5 'Annual salary', 70 GD_EMP-ANSAL.
*  write: /5 'Currency key for annual salary', 70 GD_EMP-ANCUR.
*  write: /5 'Employment percentage', 70 GD_EMP-EMPCT.
*  write: /5 'Employment Status', 70 GD_EMP-STAT2.
*  write: /5 'Entry Date', 70 GD_EMP-NCSDATE.
*  write: /5 'Pay Grade Type', 70 GD_EMP-SLTYP.
*  write: /5 'Pay Grade Area', 70 GD_EMP-SLREG.
*  write: /5 'Pay grade', 70 GD_EMP-SLGRP.
*  write: /5 'Pay Grade Level', 70 GD_EMP-SLLEV.
*  write: /5 'Work Contract', 70 GD_EMP-ANSVH.
*  write: /5 'Organizational Key', 70 GD_EMP-VDSK1.
  WRITE: /5 'Personnel Number           ', gd_emp-pernr.
  WRITE: /5 'Employee Name              ', gd_emp-sname.
  WRITE: /5 'A change is detected in IT ', gd_emp-itype.
  ULINE AT /5(109).
  WRITE: /5 'Payroll calculator         ', gd_payroll_name.
  WRITE: /5 'Payroll period             ', gd_emp-period.
  WRITE: /5 'Payroll result seq.number  ', rgdir-seqnr.
  WRITE: /5 'Effective date (adjusted)  ', gd_emp-effdate.
  ULINE AT /5(109).
  SKIP.
ENDFORM.                    "z_print_emp_data
*--------------------------------------------------------------------*
* Display payroll log
*--------------------------------------------------------------------*
FORM z_print_py_log.
  DATA:
    abaplist TYPE TABLE OF abaplist,
    listline TYPE char200,
    listtxt  TYPE TABLE OF char200.
  ULINE AT /5(109).
  CALL FUNCTION 'LIST_FROM_MEMORY'
    TABLES
      listobject = abaplist
    EXCEPTIONS
      not_found  = 1
      OTHERS     = 2.
  IF sy-subrc <> 0.
    WRITE: /5 'Cannot fetch list of payroll run:', sy-subrc.
  ELSE.
    CALL FUNCTION 'LIST_TO_ASCI'
      TABLES
        listasci           = listtxt
        listobject         = abaplist
      EXCEPTIONS
        empty_list         = 1
        list_index_invalid = 2
        OTHERS             = 3.
    IF sy-subrc <> 0.
      WRITE: /5 'Error', sy-subrc, 'converting report!'.
    ELSE.
      LOOP AT listtxt INTO listline.
        WRITE: / listline(120).
      ENDLOOP.
    ENDIF.
  ENDIF.
  ULINE AT /5(109).
ENDFORM.                    "z_print_py_log
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_log USING p_itype TYPE c
                      p_pernr TYPE pernr-pernr
                      p_begda TYPE begda.
  MOVE p_itype TO gd_emp-itype.
  MOVE p_pernr TO gd_emp-pernr.
  MOVE p_begda TO gd_emp-begda.
ENDFORM.                    "Z_proc_log
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_print_error .
  LOOP AT gt_error.
    WRITE: /5 gt_error-msgtext.
  ENDLOOP.
  SKIP.
ENDFORM.                    "z_print_error
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_next_inc_date CHANGING p_tmp TYPE c.
  DATA  l_index TYPE i.
  LOCAL: p0008, p0016.
* derive date if no record exists in infotype
  IF p0008-stvor IS INITIAL.
    CALL FUNCTION 'HR_UN_RECLASS_NEXT_INCR_DATE'
      EXPORTING
        pernr = gd_emp-pernr
        begda = pn-begda
        endda = pn-begda
      IMPORTING
        stvor = p0008-stvor
      TABLES
        p0008 = p0008.
  ENDIF.
  IF NOT p0008-stvor IS INITIAL
     AND p0008-stvor NE $maxdate.
* cast 'next increment' date to character
    WRITE p0008-stvor TO p_tmp RIGHT-JUSTIFIED.
  ENDIF.
* get last contract elements record
  DESCRIBE TABLE p0016 LINES l_index.
  READ TABLE p0016 INDEX l_index.
* define when not to show next increase date
  IF     p0016-cttyp EQ '03'
      OR p0016-cttyp EQ '08'
      OR p0016-cttyp EQ '09'
      OR p0016-cttyp EQ '11'
      OR p0016-cttyp EQ '13'
      OR p0016-cttyp EQ '14'
      OR p0016-cttyp EQ '15'
      OR p0016-cttyp EQ '16'
      OR p0016-cttyp EQ '17'
      OR gd_salperiod NE 12.
    CLEAR p_tmp.
  ENDIF.
ENDFORM.                    "z_get_next_inc_date
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_0016 CHANGING p_tmp TYPE c.
  DATA  l_index TYPE i.
* despite of 'effective date' select 'contract expiry date'
* from the latest IT0016 record
  LOCAL p0016. " preserve global value
  DESCRIBE TABLE p0016 LINES l_index.
  READ TABLE p0016 INDEX l_index.
  WRITE p0016-ctedt TO p_tmp RIGHT-JUSTIFIED.
ENDFORM.                                                    "Z_GET_0016
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_0021 USING p_kdate TYPE d
                      p_subty TYPE string
                      p_subt2 TYPE string.
  DATA: l_index TYPE i VALUE 1,
        l_nbr   TYPE i.
  CLEAR p0021.
* if subtype is empty we search for last record using key date
  IF p_subty EQ $empty.
* sort table to put last record on the top
    SORT p0021 BY begda DESCENDING.
* search for record required
    DO.
      READ TABLE p0021 INDEX l_index.
      IF p0021-begda GT p_kdate.
        ADD 1 TO l_index.
      ELSE.
        EXIT.
      ENDIF.
    ENDDO.
* otherwise calculate number of dependent children
  ELSE.
    LOOP AT p0021 WHERE ( subty EQ p_subty
                     OR subty EQ p_subt2 )
                    AND begda LE p_kdate
                    AND endda GE p_kdate
                    AND kdgbr EQ $cross.
      ADD 1 TO l_nbr.
    ENDLOOP.
    WRITE l_nbr TO gd_emp-nchild LEFT-JUSTIFIED.
  ENDIF.
ENDFORM.                                                    "Z_GET_0021
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_rate CHANGING p_val TYPE string.
  DATA: w_val   TYPE string VALUE 'S-rate',
        w_intky TYPE char1.
  CLEAR p0021.
  LOOP AT p0021 WHERE begda LE gd_emp-effdate
                  AND endda GE gd_emp-effdate
                  AND ( subty EQ '14' OR subty EQ '1' OR subty EQ '2' ).
* KDGBR - Child allowance entitlement
* SPRPS - Lock Indicator for HR Master Data Record
* FAMSA - Type of family record
    IF    p0021-kdgbr EQ 'X'
      AND p0021-sprps IS INITIAL.
* Get internal key for family attribute
      SELECT SINGLE intky FROM t577
                          INTO w_intky
                         WHERE molga EQ gd_emp-molga
                           AND auspr EQ p0021-famsa.
      IF sy-subrc IS INITIAL.
* 0 - spouse working in UNES/UN; 1 - child; 2 - spouse;
        IF w_intky CA '012'. w_val = 'D-rate'. ENDIF.
      ENDIF.
      EXIT.
    ENDIF.
  ENDLOOP.
*AAHOUNOU25012017
  IF pn-begda LE  $changepafdate.
* add rate to output string
    CONCATENATE p_val '(' w_val ')' INTO p_val SEPARATED BY space.
  ENDIF.
*AAHOUNOU25012017
ENDFORM.                    "Z_GET_RATE
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_0509_check CHANGING p_flag.
  DATA: l_index TYPE i.
  DESCRIBE TABLE p0509 LINES l_index.
  LOOP AT p0509 WHERE begda EQ p0509-begda
                  AND endda EQ p0509-endda.
    IF l_index EQ sy-tabix.
      MOVE $cross TO p_flag.
    ENDIF.
  ENDLOOP.
ENDFORM.                    "Z_GET_0509_CHECK
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_0962.
  DATA: l_index TYPE i.
  CLEAR p0962.
  DESCRIBE TABLE p0962 LINES l_index.
  READ TABLE p0962 INDEX l_index.
  IF gd_emp-effdate GT p0962-endda.
* in case of suppression we don't have to display any value for
* rental subsidy althogh results would exist in rt table when
* suppression happens not on the last day of a period
    MOVE $cross TO gf_rnts_is_suppressed.
  ENDIF.
ENDFORM.                                                    "Z_GET_0962
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_get_0960.
  DATA: l_index TYPE i,
        w_q0960 TYPE q0960.
  CLEAR p0960.
  DESCRIBE TABLE p0960 LINES l_index.
  READ TABLE p0960 INDEX l_index.
  w_q0960 = zhr_it0960=>get_q0960( pernr = pernr-pernr
                                   begda = gd_emp-effdate
                                   endda = $maxdate ).
* Mobility Expiration Date
  CHECK NOT w_q0960-moexd IS INITIAL.
  CHECK NOT w_q0960-rered IS INITIAL.
* Check conditions when M&H is suppressed
* 1) mob.exp. date > eff. date
* 2) non-rem. valid to date > eff. date
* 3) hs classification is A or H
  IF    gd_emp-effdate GT w_q0960-moexd
    AND gd_emp-effdate GT w_q0960-rered
    AND w_q0960-rered  CA 'AH'.
* if yes we have a suppression of M&H case
    MOVE $cross TO gf_mhal_is_suppressed.
  ENDIF.
ENDFORM.                                                    "z_get_0960
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM z_proc_inc_period.
  DATA: w_year(4)   TYPE n,
        w_period(2) TYPE n.
  MOVE gd_emp-period(4)   TO w_year.
  MOVE gd_emp-period+4(2) TO w_period.
  IF w_period NE '12'.
    ADD 1 TO w_period.
  ELSE.
    ADD 1 TO w_year.
    MOVE '01' TO w_period.
  ENDIF.
  CONCATENATE w_year w_period INTO gd_emp-period.
ENDFORM.                    "z_proc_inc_period
*--------------------------------------------------------------------*
* another way to remove payroll results is to clear table before you
* preparing output...
*      clear GT_RESULTS.
*      refresh GT_RESULTS.
*--------------------------------------------------------------------*
FORM z_check_x5_condition CHANGING p_lines TYPE table.
  CONSTANTS:
*    c_line1 TYPE string VALUE '*GSL*NSL*F7L*F6L*CAL*SDL*SPL*FML*NRL',
*    c_line2 TYPE string VALUE '*RNL*MHL*LAL*SLL*SEL*RPL*TRL*SNL*PTL',
*    c_line3 TYPE string VALUE '*AGL*ALL*RGL*TIL*DGL*ILL*ANL*HDL*CLL',
*    c_line4 TYPE string VALUE '*PAL*PCL*MFL*DHL*SSL*OSL*NNL*R1L*LEL*LFL',
*    c_line5 TYPE string VALUE '*GST*F5T*F7T*F6T*CAT*SDT*SPT*FMT*NRT',
*    c_line6 TYPE string VALUE '*RNT*F8T*LAT*SLT*SET*RPT*TRT*SNT*PTT*CSL*CST',
*    c_line7 TYPE string VALUE '*AGT*ALT*RGT*TIT*DGT*ILT*ANT*HDT*CLT*FSL*FST',
*    c_line8 TYPE string VALUE '*PAT*PCT*MFT*DHT*SST*OST*NNT*R1T*LET*LFT'.",
**    C_LINE9 type STRING value '*R1T*LET*LFT*'.
    c_line1 TYPE string VALUE '*GSL*NSL*F7L*F6L*CAL*SDL*SPL*FML*NRL',
    c_line2 TYPE string VALUE '*RNL*MHL*LAL*SLL*SEL*RPL*TRL*SNL*PTL', "SLL
    c_line3 TYPE string VALUE '*AGL*ALL*RGL*TIL*DGL*ILL*ANL*HDL*CLL',
    c_line4 TYPE string VALUE '*PAL*PCL*MFL*DHL*SSL*OSL*NNL*R1L*LEL*LFL',
    c_line5 TYPE string VALUE '*GST*F5T*F7T*F6T*CAT*SDT*SPT*FMT*NRT',
    c_line6 TYPE string VALUE '*RNT*F8T*LAT*SLT*SET*RPT*TRT*SNT*PTT*CSL*CST', "SLT
    c_line7 TYPE string VALUE '*AGT*ALT*RGT*TIT*DGT*ILT*ANT*HDT*CLT*FSL*FST',
    c_line8 TYPE string VALUE '*PAT*PCT*MFT*DHT*SST*OST*NNT*R1T*LET*LFT'. ",
  DATA:
    w_tmp        TYPE string,
    w_line       TYPE string,
    w_searchline TYPE string,
    w_index      TYPE i.
  IF NOT gp_byact IS INITIAL
     AND p0000-massn EQ 'X5'. " Leave without pay.
    CHECK p0961-pfsta EQ '0'.
    CHECK p0167-bopti EQ 'OPT7'.
* if condition is true then clear payroll results
    CONCATENATE c_line1 c_line2 c_line3 c_line4
                c_line5 c_line6 c_line7 c_line8 INTO w_searchline.
    LOOP AT p_lines INTO w_line.
      ADD 1 TO w_index.
      SEARCH w_line FOR ';'.
      CHECK sy-subrc IS INITIAL.
      CONCATENATE '*' w_line(sy-fdpos) '*' INTO w_tmp.
      FIND w_tmp IN w_searchline.
      CHECK sy-subrc IS INITIAL.
      CONCATENATE w_tmp+1(3) ';' INTO w_line.
      MODIFY p_lines FROM w_line INDEX w_index.
    ENDLOOP.
  ENDIF.
ENDFORM.                    "z_check_X5_condition