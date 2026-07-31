* ==== CLASS POOL ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN ====
CLASS-POOL .
*"* class pool for class ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN

*"* local type definitions
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CCDEF.

*"* class ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN definition
*"* public declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CU.
*"* protected declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CO.
*"* private declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CI.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN definition

*"* macro definitions
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CCMAC.
*"* local class implementation
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CCIMP.

CLASS ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN implementation


* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CI ----
PRIVATE SECTION.

  METHODS _FILL_AVC_AMOUNT_FIELDS
    IMPORTING
      VALUE(IO_LINE_HANDLER) TYPE REF TO CX_HRFPM OPTIONAL
    CHANGING
      !CD_OUTPUT_LINE TYPE DATA .

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM001 ----
METHOD CONSTRUCTOR.
  DATA LD_TYPE TYPE TYS_AGGREG_TYPE_AO.
  DATA LS_ADMISBL_ENH_ID LIKE LINE OF MTR_ADMISSIBLE_ENH_ID.
  SUPER->CONSTRUCTOR( ).
  MO_AGGREG_TYPE ?=  CL_ABAP_TYPEDESCR=>DESCRIBE_BY_DATA( LD_TYPE ).

  MV_SW_USABLE_CHECK =
  BOOLC( CL_HR_T77S0=>READ(  GRPID = 'ZPBC0' SEMID = 'ZENH1' )-GSVAL IS INITIAL ) .

  LS_ADMISBL_ENH_ID-SIGN = 'I'.
  LS_ADMISBL_ENH_ID-OPTION = 'EQ'.
  LS_ADMISBL_ENH_ID-LOW = 'FMAVCMSG'.
  INSERT LS_ADMISBL_ENH_ID INTO TABLE MTR_ADMISSIBLE_ENH_ID.

  CON_VOID_AVAIL_AMOUNT = -1 * 999999999999.
  CON_VOID_MISSING_AMOUNT = 0.

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM002 ----
METHOD DET_AVAILABLE_BUDGET_HIST.
  RV_AVAIL_BUDGET_HIST = IS_AMOUNTS-REQUESTED_AMOUNT - IS_AMOUNTS-MISSING_AMOUNT.
  "this cannot work in general: we need a good method to find out the real availabble nudget
  "at the time the message list is prepared


ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM003 ----
METHOD FIGURE_OUT_MISSING_AMOUNT.
  ASSERT IV_AGGREGATE-NO_AGGREGEE = ABAP_FALSE.
  "historical available budget
  RV_MISSING_AMOUNT = IV_AMOUNTS.

  RV_MISSING_AMOUNT-AVAIL_BDGT_HIST =
    DET_AVAILABLE_BUDGET_HIST( IV_AMOUNTS ).


  RV_MISSING_AMOUNT-MISSING_AMOUNT = IV_AMOUNTS-REQUESTED_AMOUNT.
*  "if that particular aggregate exists already
*  "this however is only applicable under very restricted conditions!
*  "c.f. method check_if_applicable
*  IF iv_aggregate-is_new = abap_true.
*    rv_missing_amount-missing_amount = iv_amounts-missing_amount.
*  ENDIF.


ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM004 ----
METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~BEGIN_OF_GROUP_PROCESSING.
    SUPER->IF_HRFPM_LG_ENHANCEMENT_GRP~BEGIN_OF_GROUP_PROCESSING( ).
    "durign posting trial those global data must not be cleared!!
    IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_FALSE.
      CLEAR:
         MT_RUNID_ADMISSIBLE,
         MT_AO_WITH_AVAIL_AMOUNT.
         "mt_ao_with_mult_usage.
    ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM005 ----
 METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~WORK_OVER_MESSAGE_LIST.
*  Consider a case with four documents are to be posted, with an available budget of 900,- on the budget address
*
*January  February
*#1 100,-   #3 1000,-
*#2 1000,- 	#4 100,-
*
*	The system would do the posting in the sequence #1,#2 #4, #3
*	#1 and #4 could be posted
*	The process would however deliver AVC errors for #2 and #3
*
*Doc  Missing amount from AVC Delta amount
*#2	200,- (because #1 was posted)	1000,-
*#3	300,- (because #4 was posted)	1000,-
*
*The current calculation logic would indicate a total of 1200,- that should be put to the budget address
*That would still not be sufficient though: the correct amount would be 1300,-

   DATA LS_AGGREGATE TYPE TYS_AGGREGATE_RETURN.
   DATA LR_AGGREG TYPE REF TO TYS_AGGREG_TYPE_AO.
   DATA LS_AVC_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS .
   DATA LT_AO_PROCESSED LIKE MT_AO_WITH_AVAIL_AMOUNT.

   FIELD-SYMBOLS <LINE> TYPE ANY.
   FIELD-SYMBOLS <AGGREGATE> LIKE LINE OF MT_AO_WITH_AVAIL_AMOUNT.

   IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_FALSE.
     LOOP AT CT_MESSAGE_LIST ASSIGNING <LINE>.
       TRY .
           LS_AGGREGATE = DET_AGGREGATE_FROM_DATA( <LINE> ).
           IF LS_AGGREGATE-NO_AGGREGEE = ABAP_FALSE.
             MOVE-CORRESPONDING <LINE> TO LS_AVC_AMOUNTS.
             LR_AGGREG ?= LS_AGGREGATE-AGGREGATE->AGGREGATE_ID-AGGREGATE_DATA.

             READ TABLE MT_AO_WITH_AVAIL_AMOUNT ASSIGNING <AGGREGATE>
              WITH KEY CARRIER COMPONENTS CARRIER = LR_AGGREG->CARRIER.

             IF SY-SUBRC <> 0 OR NOT <AGGREGATE>-AVAIL_BDGT_HIST IS BOUND.
               LS_AVC_AMOUNTS-MISSING_AMOUNT = CON_VOID_MISSING_AMOUNT.
               LS_AVC_AMOUNTS-AVAIL_BDGT_HIST = CON_VOID_AVAIL_AMOUNT .
             ELSE.
               LS_AVC_AMOUNTS-AVAIL_BDGT_HIST = <AGGREGATE>-AVAIL_BDGT_HIST->*.

               IF CHECK_IF_USABLE(
                   IS_AGGREGATE = LS_AGGREGATE
                   ID_LINE = <LINE> ) = ABAP_FALSE.
*{   DELETE         D01K9B01MU                                        3
*\                 IF sv_show_technical_columns = abap_false.
*\                   "only show void lines for analysis reasons
*\                   CONTINUE.
*\                 ELSE.
*}   DELETE
                   LS_AVC_AMOUNTS-MISSING_AMOUNT = CON_VOID_MISSING_AMOUNT.
*{   INSERT         D01K9B01O5                                        5
                   LS_AVC_AMOUNTS-ZZ_RESULT_ACCURACY-ZZLATER_RUN_EXISTS = ABAP_TRUE.
*}   INSERT
*{   DELETE         D01K9B01MU                                        4
*\                 ENDIF.
*}   DELETE
               ELSE.
                 "effective available amount to be used for calculation
                 " minimum: determined during step 'fill_avc_amounts'

                 READ TABLE LT_AO_PROCESSED TRANSPORTING NO FIELDS
                    WITH KEY CARRIER COMPONENTS CARRIER = <AGGREGATE>-CARRIER.
                 IF SY-SUBRC <> 0.
                   "first time that the carrier is processed:
                   INSERT <AGGREGATE> INTO TABLE LT_AO_PROCESSED.
                   "in this case the missing amount can be
*{   REPLACE        D01K9B01JE                                        1
*\                   ls_avc_amounts-missing_amount =
*\                     ls_avc_amounts-requested_amount -
*\                       ls_avc_amounts-avail_bdgt_hist.
                     LS_AVC_AMOUNTS-MISSING_AMOUNT =
                        DET_EFFECTIVE_REQUESTED_AMOUNT(
                           IV_AGGREGATE = <AGGREGATE>
                           ID_LINE      = <LINE>
                           IV_AMOUNTS   = LS_AVC_AMOUNTS ) -
                       LS_AVC_AMOUNTS-AVAIL_BDGT_HIST.
*}   REPLACE
                 ELSE.
                   "carrier has alrady been used
                   "the missing amount = requested amount since
                   "'logically' the AVC-gap has been filled when
                   "the carrier was fduon teh first time
*{   REPLACE        D01K9B01JE                                        2
*\                   ls_avc_amounts-missing_amount = ls_avc_amounts-requested_amount.
                   LS_AVC_AMOUNTS-MISSING_AMOUNT =
                           DET_EFFECTIVE_REQUESTED_AMOUNT(
                             IV_AGGREGATE = <AGGREGATE>
                             ID_LINE      = <LINE>
                             IV_AMOUNTS   = LS_AVC_AMOUNTS ).
*}   REPLACE
                 ENDIF.
               ENDIF.
             ENDIF.
             MOVE-CORRESPONDING LS_AVC_AMOUNTS TO <LINE>.
           ENDIF.
         CATCH CX_SY_MOVE_CAST_ERROR ##NO_HANDLER.
       ENDTRY.
     ENDLOOP.
   ENDIF.
 ENDMETHOD.                    "if_hrfpm_lg_enhancement_grp~work_over_message_list

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM006 ----
METHOD ZIF_HRFPM_LG_AVC_AGGREG_HNDL~CHECK_IF_AGGREGEE.
  FIELD-SYMBOLS <AGGREGATE_DATA> TYPE TYS_AGGREG_TYPE_AO.
  RV_IS_AGREGEE = ABAP_FALSE.

  ASSIGN IV_AGGREGATE_KEY TO <AGGREGATE_DATA>.
  IF SY-SUBRC = 0 .
    IF NOT <AGGREGATE_DATA>-ZZAVC_CARRIER IS INITIAL.
      RV_IS_AGREGEE = ABAP_TRUE.
    ENDIF.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM007 ----
METHOD ZIF_HRFPM_LG_AVC_AGGREG_HNDL~CHECK_IF_USABLE.
 "DATA ls_aggregate TYPE tys_aggregate_return.
  DATA LT_RUNID TYPE STANDARD TABLE OF HRFPM_RUNID .
  DATA LV_RUNID_SPACE TYPE HRFPM_RUNID.
  DATA LS_FPM_POS TYPE HRFPM_FPM_POS.
  DATA LS_RUNID_ADMISSIBLE LIKE LINE OF MT_RUNID_ADMISSIBLE.
  DATA LS_FM_POS TYPE HRFPM_FM_POS.

  FIELD-SYMBOLS <AGGREGATE_DATA> TYPE TYS_AGGREG_TYPE_AO.
  FIELD-SYMBOLS <RUNID_ADMISSIBLE> LIKE LINE OF MT_RUNID_ADMISSIBLE.
  FIELD-SYMBOLS <LINE> TYPE ANY.
  FIELD-SYMBOLS <FIELD> TYPE ANY.


  IF IS_AGGREGATE IS INITIAL.
    IS_AGGREGATE = DET_AGGREGATE_FROM_DATA( ID_LINE ).
  ENDIF.

  IF IS_AGGREGATE-NO_AGGREGEE = ABAP_TRUE.
    RV_IS_USABLE = ABAP_FALSE.
  ELSEIF MV_SW_USABLE_CHECK = ABAP_TRUE.
    "adequate 'Missing values' can only be calculated if it can be guaranteed
    " the object is not processed in a later run
    "reject a line from the calculation
    "(A) if there is any later run
    RV_IS_USABLE = ABAP_TRUE.

    ASSIGN:
      IS_AGGREGATE-AGGREGATE->AGGREGATE_ID-AGGREGATE_DATA->* TO <AGGREGATE_DATA>,
      ID_LINE TO <LINE>.

    IF NOT IO_LINE_HANDLER IS BOUND.
      "needed to get hold of all hrobjects affected by the line
      IO_LINE_HANDLER ?= CL_HRFPM_LG_UTILS=>GET_LOG_HANDLER(
           EXTRACT_BAL_MSG_FROM_LINE( ID_LINE ) ).
    ENDIF.

    LOOP AT IO_LINE_HANDLER->HROBJECTS INTO LS_RUNID_ADMISSIBLE-HROBJECT.
      LS_RUNID_ADMISSIBLE-DUE_DATE = <AGGREGATE_DATA>-DUE_DATE.
      READ TABLE MT_RUNID_ADMISSIBLE ASSIGNING <RUNID_ADMISSIBLE>
        WITH KEY ACCESS COMPONENTS
           HROBJECT = LS_RUNID_ADMISSIBLE-HROBJECT
           DUE_DATE = LS_RUNID_ADMISSIBLE-DUE_DATE.

      IF SY-SUBRC <> 0.
        INSERT LS_RUNID_ADMISSIBLE INTO TABLE MT_RUNID_ADMISSIBLE
           ASSIGNING <RUNID_ADMISSIBLE>.
      ENDIF.

      <RUNID_ADMISSIBLE>-RUNID =
         CMAX( VAL1 = <RUNID_ADMISSIBLE>-RUNID
               VAL2 = <AGGREGATE_DATA>-RUNID ).

      RV_IS_USABLE = BOOLC( <AGGREGATE_DATA>-RUNID = <RUNID_ADMISSIBLE>-RUNID ).
      IF RV_IS_USABLE = ABAP_FALSE.
        EXIT.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM008 ----
METHOD ZIF_HRFPM_LG_AVC_AGGREG_HNDL~FILL_AGGREGATE_KEY.

  DATA LS_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS.
  FIELD-SYMBOLS <AGGREGATE_KEY> TYPE TYS_AGGREG_TYPE_AO.

  CREATE DATA RV_AGGREGATE_KEY TYPE HANDLE MO_AGGREG_TYPE.
  ASSIGN RV_AGGREGATE_KEY->* TO <AGGREGATE_KEY>.

  MOVE-CORRESPONDING IV_LINE TO:
      <AGGREGATE_KEY>,
      <AGGREGATE_KEY>-KEY_POS,
      LS_AMOUNTS.

  "concatenate the two message AVC-objects string  into one
  IF NOT <AGGREGATE_KEY>-ZZAVC_CARRIER2 IS INITIAL.
    <AGGREGATE_KEY>-ZZAVC_CARRIER =
      <AGGREGATE_KEY>-ZZAVC_CARRIER && '/' &&
      <AGGREGATE_KEY>-ZZAVC_CARRIER2.
    CLEAR <AGGREGATE_KEY>-ZZAVC_CARRIER2.
  ENDIF.

  "this is a necessary characteristic, because only
  "in the context of a constant available budget we can later calcualte
  "reliable values for the missing budget
  LS_AMOUNTS-AVAIL_BDGT_HIST = DET_AVAILABLE_BUDGET_HIST( LS_AMOUNTS ).
  WRITE LS_AMOUNTS-AVAIL_BDGT_HIST TO <AGGREGATE_KEY>-AVAIL_BDGT_HIST_STRG.
  REPLACE ALL OCCURRENCES OF ',' IN <AGGREGATE_KEY>-AVAIL_BDGT_HIST_STRG WITH ''.
  REPLACE ALL OCCURRENCES OF '.' IN <AGGREGATE_KEY>-AVAIL_BDGT_HIST_STRG WITH ''.

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM009 ----
  METHOD FILL_AVC_AMOUNT_FIELDS.
    "use that method just in order to collect  AVC-related information
    "on the level of a 'aggregate'
    "that will be used later in method 'work_over_message_list'
    "to determine the missing budget
    "(on the level of an individual line this can not be done)
    "example:
*  Consider a case with four documents are to be posted, with an available budget of 900,- on the budget address
*
*January  February
*#1 100,-   #3 1000,-
*#2 1000,- 	#4 100,-
*
*	The system would do the posting in the sequence #1,#2 #4, #3
*	#1 and #4 could be posted
*	The process would however deliver AVC errors for #2 and #3
*
*Doc  Missing amount from AVC Delta amount
*#2	200,- (because #1 was posted)	1000,-
*#3	300,- (because #4 was posted)	1000,-
*
*The current calculation logic would indicate a total of 1200,- that should be put to the budget address
*That would still not be sufficient though: the correct amount would be 1300,-

    DATA LS_AGGREGATE TYPE TYS_AGGREGATE_RETURN.
    DATA LR_AGGREG TYPE REF TO TYS_AGGREG_TYPE_AO.
    DATA LS_AVC_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS .
    DATA LS_AO_WITH_AVAIL_AMOUNT LIKE LINE OF MT_AO_WITH_AVAIL_AMOUNT .
    DATA LV_TABIX TYPE SY-TABIX.

    FIELD-SYMBOLS <AO> LIKE LINE OF MT_AO_WITH_AVAIL_AMOUNT .

    LS_AGGREGATE = DET_AGGREGATE_FROM_DATA( CD_OUTPUT_LINE ).

    IF LS_AGGREGATE-NO_AGGREGEE = ABAP_FALSE.

      "just make sure the buffers are update
      IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_FALSE.
        "only in non-trial mode
        ZIF_HRFPM_LG_AVC_AGGREG_HNDL~CHECK_IF_USABLE(
            ID_LINE         = CD_OUTPUT_LINE
            IO_LINE_HANDLER = IO_LINE_HANDLER
            IS_AGGREGATE    = LS_AGGREGATE  ).
      ENDIF.

      MOVE-CORRESPONDING CD_OUTPUT_LINE TO LS_AVC_AMOUNTS.
      LR_AGGREG ?= LS_AGGREGATE-AGGREGATE->AGGREGATE_ID-AGGREGATE_DATA.

      READ TABLE MT_AO_WITH_AVAIL_AMOUNT ASSIGNING <AO>
           WITH KEY CARRIER COMPONENTS
               CARRIER = LR_AGGREG->CARRIER.

      IF SY-SUBRC <> 0.
        LS_AO_WITH_AVAIL_AMOUNT-CARRIER = LR_AGGREG->CARRIER.
        INSERT LS_AO_WITH_AVAIL_AMOUNT
           INTO TABLE MT_AO_WITH_AVAIL_AMOUNT
            ASSIGNING <AO>.
        LV_TABIX = SY-TABIX.
        "(a)post a fake document in test mode
        "requesting finacing of an amout that big that
        "it will fail, thus forcing a AVC-message
        "(b)that message will be passed to the enhanced log mechanism
        "(message exgtraction in particular)
        "in order to get hold of the missing amount
        "(of course, the better way would be to directly
        "call a function delivering the available budget,
        "but to that end RFC-enabled fucntions woudl have to be provided first)
        IF LCL_AVC_CHECKER=>S_GET_INSTANCE_FOR_TRIAL(
             LR_AGGREG->* )->START_POSTING_TRIAL( ) < 0.
          DELETE MT_AO_WITH_AVAIL_AMOUNT INDEX LV_TABIX.
        ENDIF.
      ENDIF.

      IF <AO> IS ASSIGNED AND NOT <AO>-AVAIL_BDGT_HIST IS BOUND .
        "(c)this will call again 'fill_avc_amount_fields'
        " but now there is already a record in the mt_ao_with_avail_amount
        "table
        "(d) ls_avc_amounts is the filled with the correct values
        "data is filled only in trial mode
        "(reason: in case the trial can not take place becuase of non-AVC-related errors
        "the proper amount cannot be determined!)
        IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_TRUE.
          CREATE DATA <AO>-AVAIL_BDGT_HIST.
          <AO>-AVAIL_BDGT_HIST->* = DET_AVAILABLE_BUDGET_HIST( LS_AVC_AMOUNTS ).
          LCL_AVC_CHECKER=>S_GET_INSTANCE_FOR_TRIAL(
              LR_AGGREG->* )->STOP_POSTING_TRIAL( ).
*      ELSE.
*
*        <ao>-avail_bdgt_hist->* = nmin(
*                        val1 = <ao>-avail_bdgt_hist->*
*                        val2 =  det_available_budget_hist( ls_avc_amounts ) ).
        ENDIF.
      ENDIF.
    ENDIF.
  ENDMETHOD.                    "fill_avc_amount_fields

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00A ----
  METHOD _FILL_AVC_AMOUNT_FIELDS.
    "use that method just in order to collect  AVC-related information
    "on the level of a 'aggregate'
    "that will be used later in method 'work_over_message_list'
    "to determine the missing budget
    "(on the level of an individual line this can not be done)
    "example:
*  Consider a case with four documents are to be posted, with an available budget of 900,- on the budget address
*
*January  February
*#1 100,-   #3 1000,-
*#2 1000,- 	#4 100,-
*
*	The system would do the posting in the sequence #1,#2 #4, #3
*	#1 and #4 could be posted
*	The process would however deliver AVC errors for #2 and #3
*
*Doc  Missing amount from AVC Delta amount
*#2	200,- (because #1 was posted)	1000,-
*#3	300,- (because #4 was posted)	1000,-
*
*The current calculation logic would indicate a total of 1200,- that should be put to the budget address
*That would still not be sufficient though: the correct amount would be 1300,-

    DATA LS_AGGREGATE TYPE TYS_AGGREGATE_RETURN.
    DATA LR_AGGREG TYPE REF TO TYS_AGGREG_TYPE_AO.
    DATA LS_AVC_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS .
    DATA LS_AO_WITH_AVAIL_AMOUNT LIKE LINE OF MT_AO_WITH_AVAIL_AMOUNT .

    FIELD-SYMBOLS <AO> LIKE LINE OF MT_AO_WITH_AVAIL_AMOUNT .

    LS_AGGREGATE = DET_AGGREGATE_FROM_DATA( CD_OUTPUT_LINE ).

    IF LS_AGGREGATE-NO_AGGREGEE = ABAP_FALSE.

*      IF check_if_usable( cd_output_line ) = abap_true.
*        ls_avc_amounts-missing_amount = 0.
*        "serves as indicator that missing amoutn cannot be determined
*        MOVE-CORRESPONDING ls_avc_amounts TO cd_output_line.
*      ELSE.

      MOVE-CORRESPONDING CD_OUTPUT_LINE TO LS_AVC_AMOUNTS.
      LR_AGGREG ?= LS_AGGREGATE-AGGREGATE->AGGREGATE_ID-AGGREGATE_DATA.

      READ TABLE MT_AO_WITH_AVAIL_AMOUNT ASSIGNING <AO>
           WITH KEY CARRIER COMPONENTS
               CARRIER = LR_AGGREG->CARRIER.

      IF SY-SUBRC <> 0.
        LS_AO_WITH_AVAIL_AMOUNT-CARRIER = LR_AGGREG->CARRIER.
        INSERT LS_AO_WITH_AVAIL_AMOUNT INTO TABLE MT_AO_WITH_AVAIL_AMOUNT
            ASSIGNING <AO>.
        CREATE DATA <AO>-AVAIL_BDGT_HIST.
        <AO>-AVAIL_BDGT_HIST->* = DET_AVAILABLE_BUDGET_HIST( LS_AVC_AMOUNTS ).
      ENDIF.

      <AO>-AVAIL_BDGT_HIST->* = NMIN(
                      VAL1 = <AO>-AVAIL_BDGT_HIST->*
                      VAL2 =  DET_AVAILABLE_BUDGET_HIST( LS_AVC_AMOUNTS ) ).
    ENDIF.
  ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00B ----
METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~END_OF_GROUP_PROCESSING.
  "purpose of this method is to complete the
  "internal table mt_runid_admissible (storing the information about)
  "with such runs not processed in the current selection of riun
  "(for example because a later run was successful: in such a situation
  "this has to be taken into account)
  DATA: BEGIN OF LS_RUNID_HROBJECT,
          RUNID TYPE HRFPM_OBJECTS-RUNID.
  INCLUDE TYPE HROBJECT AS HROBJECT.
  DATA: END OF LS_RUNID_HROBJECT.

  DATA LT_RUNID_HROBJECT LIKE STANDARD TABLE OF LS_RUNID_HROBJECT.
  DATA LV_RUNID_MIN TYPE HRFPM_RUNID.

  FIELD-SYMBOLS <RUNID_ADMISSIBLE> LIKE LINE OF MT_RUNID_ADMISSIBLE.
  FIELD-SYMBOLS <RUNID_HROBJECT> LIKE LINE OF LT_RUNID_HROBJECT.

  IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_FALSE.
    "coding is only necessary if not in trial run
    SORT MT_RUNID_ADMISSIBLE ASCENDING BY RUNID.


    IF NOT MT_RUNID_ADMISSIBLE IS INITIAL.
      READ TABLE MT_RUNID_ADMISSIBLE INDEX 1 ASSIGNING <RUNID_ADMISSIBLE>.
      LV_RUNID_MIN = <RUNID_ADMISSIBLE>-RUNID.
      SELECT DISTINCT RUNID PLVAR OTYPE OBJID
          INTO CORRESPONDING FIELDS OF TABLE LT_RUNID_HROBJECT
         FROM HRFPM_OBJECTS
         FOR ALL ENTRIES IN MT_RUNID_ADMISSIBLE WHERE
            PLVAR = MT_RUNID_ADMISSIBLE-HROBJECT-PLVAR AND
            OTYPE = MT_RUNID_ADMISSIBLE-HROBJECT-OTYPE AND
            OBJID = MT_RUNID_ADMISSIBLE-HROBJECT-OBJID AND
            "only later runs are to be considered
            RUNID GT LV_RUNID_MIN AND
            "and only those, where the object reached the commitment update
            NOT ( OBJ_COL = 'E' OR DATA_COL = 'E' ).

      SORT LT_RUNID_HROBJECT BY HROBJECT RUNID DESCENDING .
    ENDIF.


    LOOP AT LT_RUNID_HROBJECT ASSIGNING <RUNID_HROBJECT>.
      IF LS_RUNID_HROBJECT-HROBJECT = <RUNID_HROBJECT>-HROBJECT.
        CONTINUE.
      ELSE.
        LS_RUNID_HROBJECT = <RUNID_HROBJECT>.
        LOOP AT MT_RUNID_ADMISSIBLE ASSIGNING <RUNID_ADMISSIBLE>
         USING KEY ACCESS WHERE
             HROBJECT = <RUNID_HROBJECT>-HROBJECT.
          <RUNID_ADMISSIBLE>-RUNID = CMAX( VAL1 = <RUNID_ADMISSIBLE>-RUNID
                  VAL2 = <RUNID_HROBJECT>-RUNID ).
        ENDLOOP.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00C ----
  METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~CHANGE_FIELD_CAT.
    FIELD-SYMBOLS <FCAT> LIKE LINE OF CT_FIELD_CATALOGUE.
    SUPER->IF_HRFPM_LG_ENHANCEMENT_GRP~CHANGE_FIELD_CAT(
      EXPORTING
        IO_OUTPUT_STRUC_HANDLE = IO_OUTPUT_STRUC_HANDLE
        IV_ENH_GRP_ID          = IV_ENH_GRP_ID
      CHANGING
        CT_FIELD_CATALOGUE     = CT_FIELD_CATALOGUE ).


    IF SV_SHOW_TECHNICAL_COLUMNS = ABAP_FALSE.
      LOOP AT CT_FIELD_CATALOGUE ASSIGNING <FCAT>
        WHERE FIELDNAME = 'ZZAVC_CARRIER2' OR
              FIELDNAME = 'ZZAVC_CARRIER' OR
              "internal GUID for messges
              FIELDNAME = 'LOG_HANDLE'    OR
              FIELDNAME = 'MSGNUMBER'.
        <FCAT>-TECH = 'X'.
      ENDLOOP.
    ENDIF.

    "for split list processing we need this one, since the
    "split list is derived from the message liste that is described
    "by the field catalogue
    MT_SPLIT_LIST_FCAT = CT_FIELD_CATALOGUE .


  ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00D ----
  METHOD CLASS_CONSTRUCTOR.
    GET PARAMETER ID 'HRFPM_ENHLG_SHOWPATH' FIELD SV_SHOW_TECHNICAL_COLUMNS.
  ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00E ----
METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~CALL_TOOL_FOR_LIST.

  CV_RCODE = 4.
  CV_PROCESSED = ABAP_FALSE.

  SUPER->IF_HRFPM_LG_ENHANCEMENT_GRP~CALL_TOOL_FOR_LIST(
     EXPORTING IT_MESSAGE_LIST = IT_MESSAGE_LIST
               IV_TOOL_CODE    = IV_TOOL_CODE
     CHANGING  CV_PROCESSED = CV_PROCESSED
               CV_RCODE     = CV_RCODE ).

  IF CV_PROCESSED = ABAP_FALSE .
    CASE IV_TOOL_CODE.
      WHEN CONST_UCOMM_PREPARE_SPLIT_LIST.
        DO_BUILD_SPLIT_LIST(  IT_MESSAGE_LIST ).
        CV_RCODE = 0.
        CV_PROCESSED = ABAP_TRUE.
    ENDCASE.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00F ----
METHOD DO_BUILD_SPLIT_LIST.
  DATA LS_SPLIT_LIST TYPE TYS_SPLIT_LIST_RET.
  DATA LRT_SPLIT_TAB TYPE REF TO DATA.

  DATA LS_AVC_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS .
  "DATA ls_obj_texts TYPE hrfpm_fpm_pos_obj_text.
  DATA LS_HROBJECT TYPE HROBJECT.
  DATA LS_ACC_CONTENT TYPE HRFPM_DISPLOG_ACC_CONTENT.
  DATA LS_ENH_OBJ_TEXTS TYPE HRFPM_OBJECT_TEXTS.
  DATA LS_AWB_APPLC_OBJECT TYPE HRFPM_AWB_APPLC_OBJECT.
  DATA LV_DO_RECALCULATE TYPE BOOLE_D VALUE ABAP_FALSE.

  FIELD-SYMBOLS <MSG> TYPE ANY.
  FIELD-SYMBOLS <SPLIT> LIKE LINE OF
     LS_SPLIT_LIST-SPLIT_LIST->* .
  FIELD-SYMBOLS <SPLIT_INFO> LIKE LINE OF <SPLIT>-SPLIT_INFO_TAB.
  FIELD-SYMBOLS <FPM> LIKE LINE OF <SPLIT>-FPM_POS_TAB.
  FIELD-SYMBOLS <SPLIT_TAB> TYPE TABLE.
  FIELD-SYMBOLS <SPLIT_TAB_LINE> TYPE ANY.

  "provision those FPM_pos records that are affected by
  "the line
  "BREAK-POINT.
  LS_SPLIT_LIST = SPLIT_LIST_PREPARE( IT_MESSAGE_LIST ).

  LOOP AT LS_SPLIT_LIST-SPLIT_LIST->* ASSIGNING <SPLIT> .
    AT FIRST.
      CREATE DATA LRT_SPLIT_TAB LIKE IT_MESSAGE_LIST.
      ASSIGN LRT_SPLIT_TAB->* TO <SPLIT_TAB>.
    ENDAT.

    READ TABLE IT_MESSAGE_LIST ASSIGNING <MSG> INDEX <SPLIT>-MESSAGE_LINE.

*    IF lines( <split>-fpm_pos_tab ) = 1.
*      "take the original line, as a split is not necessary: the oriigianl list
*      "does also carry all the relevatn infoprmation
*      INSERT INITIAL LINE INTO TABLE <split_tab> ASSIGNING <split_tab_line>.
*      <split_tab_line> = <msg>.
*      "just for demo output
*      MOVE-CORRESPONDING <split_tab_line> TO ls_acc_content.
*      CLEAR: ls_acc_content-acc_values-betrg,
*             ls_acc_content-acc_values-delta_amount.
*      MOVE-CORRESPONDING ls_acc_content TO <split_tab_line>.
*    ELSE.
    LOOP AT <SPLIT>-FPM_POS_TAB ASSIGNING <FPM>.
      LV_DO_RECALCULATE = ABAP_TRUE.
      INSERT INITIAL LINE INTO TABLE <SPLIT_TAB> ASSIGNING <SPLIT_TAB_LINE>.
      <SPLIT_TAB_LINE> = <MSG>.

      CLEAR:
        "ls_obj_texts,
        LS_AVC_AMOUNTS,
        LS_HROBJECT,
        LS_ACC_CONTENT,
        LS_ENH_OBJ_TEXTS.

      MOVE-CORRESPONDING:
       <MSG> TO LS_ACC_CONTENT,
       LS_ENH_OBJ_TEXTS TO <SPLIT_TAB_LINE>,
       LS_AVC_AMOUNTS TO <SPLIT_TAB_LINE>,
       LS_HROBJECT TO <SPLIT_TAB_LINE>.

      "(1) amounts
      "(a) clear amounts (they will be restored in a second step)
      LS_AVC_AMOUNTS-REQUESTED_AMOUNT = <FPM>-DELTA-DELTA_AMOUNT.
      "ls_acc_content-delta_amount     = <fpm>-delta_amount.

      "(2) objects + texts
      IF <FPM>-DEP_FPM_DOC-KEY_HEADER-HROBJECT IS INITIAL
        OR <FPM>-KEY_POS-KEY_HEADER-HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_P.
        LS_HROBJECT = <FPM>-KEY_POS-KEY_HEADER-HROBJECT.
      ELSE.
        LS_HROBJECT = <FPM>-DEP_FPM_DOC-KEY_HEADER-HROBJECT.
      ENDIF.

      MOVE-CORRESPONDING LS_HROBJECT TO LS_AWB_APPLC_OBJECT.

      CALL FUNCTION 'HRFPM_COMPLETE_INFTYP_PS'
        CHANGING
          CS_AWB_APPLC_OBJECT = LS_AWB_APPLC_OBJECT.

      "write everything to the result
      MOVE-CORRESPONDING:
        LS_AWB_APPLC_OBJECT TO LS_ENH_OBJ_TEXTS,
         LS_ENH_OBJ_TEXTS   TO <SPLIT_TAB_LINE>,
         LS_HROBJECT    TO <SPLIT_TAB_LINE>,
         LS_AVC_AMOUNTS TO <SPLIT_TAB_LINE>,
         LS_ACC_CONTENT TO <SPLIT_TAB_LINE>.
    ENDLOOP.
*    ENDIF.
  ENDLOOP.

  TRY.
      IF LV_DO_RECALCULATE = ABAP_TRUE.
        "BREAK-POINT.
        "(3) calculation of mising amount, available budget etc.
        " reuse the method used for the message list
        "this is the only way of using all the information collected
        "during the message processing
        "(the split list is basically nothing else than
        " 'subset' of the over all message list multiplied by the objects
        " but leaving intact alls the importan information lie AVC-Ojects
        IF_HRFPM_LG_ENHANCEMENT_GRP~WORK_OVER_MESSAGE_LIST(
           CHANGING CT_MESSAGE_LIST = <SPLIT_TAB> ).
      ENDIF.
      "(4) display as ALV-List
      SPLIT_LIST_DISPLAY( CHANGING IT_SPLIT_LIST = <SPLIT_TAB> ).
    CATCH CX_HRFPM_LGENHNC .
      "BREAK-POINT.
  ENDTRY.


ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00G ----
METHOD SPLIT_LIST_COLLECT_SPLIT_INFO.
  DATA LRS_BAL_MSG TYPE REF TO BAL_S_MSG.
  DATA LS_SPLIT_INFO LIKE LINE OF MT_SPLIT_INFO.

  IF LCL_AVC_CHECKER=>S_CHK_IF_IN_TRIAL( ) = ABAP_FALSE
    AND DET_AGGREGATE_FROM_DATA( IS_OUTPUT_LINE )-NO_AGGREGEE = ABAP_FALSE.

    MOVE-CORRESPONDING IS_OUTPUT_LINE TO LS_SPLIT_INFO.

    IF NOT LS_SPLIT_INFO-RUNID IS INITIAL AND NOT
         LS_SPLIT_INFO-DEP_FM_DOC IS INITIAL.

      LS_SPLIT_INFO-GLOBAL_MSG_LINE = IV_LINE_INDEX.

      IF NOT IO_LINE_HANDLER IS BOUND.
        LRS_BAL_MSG = EXTRACT_BAL_MSG_FROM_LINE( IS_OUTPUT_LINE ).
        IO_LINE_HANDLER ?= CL_HRFPM_LG_UTILS=>GET_LOG_HANDLER(
            IS_BAL_MSG = LRS_BAL_MSG->* ).
      ENDIF.

      LOOP AT IO_LINE_HANDLER->HROBJECTS INTO LS_SPLIT_INFO-HROBJECT.
*{   REPLACE        D01K9B01OP                                        1
*\        INSERT ls_split_info INTO TABLE mt_split_info.
        READ TABLE MT_SPLIT_INFO TRANSPORTING NO FIELDS
          WITH KEY KEY1 COMPONENTS
               RUNID      = LS_SPLIT_INFO-RUNID
               DEP_FM_DOC = LS_SPLIT_INFO-DEP_FM_DOC
               HROBJECT   = LS_SPLIT_INFO-HROBJECT.

        IF SY-SUBRC <> 0.
          READ TABLE MT_SPLIT_INFO TRANSPORTING NO FIELDS
            WITH KEY MSG_REF COMPONENTS
                      MSG_HNDL   = LS_SPLIT_INFO-MSG_HNDL.
          IF SY-SUBRC <> 0.
           INSERT LS_SPLIT_INFO INTO TABLE MT_SPLIT_INFO.
          ENDIF.
       ENDIF.
*}   REPLACE
      ENDLOOP.
    ENDIF.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00H ----
METHOD SPLIT_LIST_DISPLAY.
  DATA LS_LAYOUT TYPE SLIS_LAYOUT_ALV.
  DATA LS_VARIANT TYPE DISVARIANT .
  "BREAK-POINT.
  "cl_demo_output=>display_data( <split_tab> ).

  "mt_split_list_fcat.

  LS_VARIANT-REPORT = SY-CPROG.
  LS_VARIANT-USERNAME = SY-UNAME.
  LS_VARIANT-HANDLE   = 'SPLT'.

  LS_LAYOUT-ZEBRA = ABAP_TRUE.
  LS_LAYOUT-COLWIDTH_OPTIMIZE = ABAP_TRUE.

  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
    EXPORTING        "i_structure_name      = 'ZHRFPM_S_HROBJECT_DEP_ALV'
      I_GRID_TITLE          = TEXT-SOB
*     I_GRID_SETTINGS       = I_GRID_SETTINGS
      IS_LAYOUT             = LS_LAYOUT
      IT_FIELDCAT           = MT_SPLIT_LIST_FCAT
*     lt_excluding          = it_excluding
*     IT_SPECIAL_GROUPS     = IT_SPECIAL_GROUPS
*     IT_SORT               = IT_SORT
*     IT_FILTER             = IT_FILTER
*     IS_SEL_HIDE           = IS_SEL_HIDE                                                                       "          not supported when dispaly is as popup
      IS_VARIANT            = LS_VARIANT
      I_DEFAULT             = 'X'
      I_SAVE                = 'A'
*     i_screen_start_column = ls_screen_sizing-start_col
*     i_screen_start_line   = ls_screen_sizing-start_line
*     i_screen_end_column   = ls_screen_sizing-end_col
*     i_screen_end_line     = ls_screen_sizing-end_line
    TABLES
      T_OUTTAB              = IT_SPLIT_LIST
    EXCEPTIONS
      PROGRAM_ERROR         = 1
      OTHERS                = 2.
  IF SY-SUBRC <> 0.
* Implement suitable error handling here
  ENDIF.


ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00I ----
METHOD SPLIT_LIST_PREPARE.

  DATA LS_SPLIT_INFO LIKE LINE OF MT_SPLIT_INFO.
  DATA LV_TABIX TYPE SYTABIX.
  DATA LT_SPLIT_INFO LIKE MT_SPLIT_INFO.
  FIELD-SYMBOLS <SPLIT_INFO> LIKE LINE OF MT_SPLIT_INFO.
  FIELD-SYMBOLS <MSG> TYPE ANY.
  FIELD-SYMBOLS <FPM_POS> LIKE LINE OF MRT_SPLIT_LIST_FPM_POS_BFR->*.
  FIELD-SYMBOLS <SPLIT_LIST> LIKE LINE OF RS_SPLIT_LIST-SPLIT_LIST->*.



  IF NOT MRT_SPLIT_LIST_FPM_POS_BFR IS BOUND.
    LT_SPLIT_INFO = MT_SPLIT_INFO.
    LOOP AT LT_SPLIT_INFO ASSIGNING <SPLIT_INFO>.
      <SPLIT_INFO>-DEP_FM_DOC =
         LCL_AVC_CHECKER=>SO_DUMMY_UPD_LOGIC->REGISTRATOR->GET_PERS_ID(
           <SPLIT_INFO>-DEP_FM_DOC ).
    ENDLOOP.

    CREATE DATA MRT_SPLIT_LIST_FPM_POS_BFR.
    IF NOT MT_SPLIT_INFO IS INITIAL.
      SELECT * FROM HRFPM_FPM_POS INTO TABLE
          MRT_SPLIT_LIST_FPM_POS_BFR->*
      FOR ALL ENTRIES IN LT_SPLIT_INFO
        WHERE ENC_TYPE_MP = LT_SPLIT_INFO-DEP_FM_DOC-ENC_TYPE AND
          BELNR_MP = LT_SPLIT_INFO-DEP_FM_DOC-BELNR AND
          PLVAR = LT_SPLIT_INFO-HROBJECT-PLVAR AND
          OTYPE = LT_SPLIT_INFO-HROBJECT-OTYPE AND
          OBJID = LT_SPLIT_INFO-HROBJECT-OBJID .
    ENDIF.
  ENDIF.

  CREATE DATA RS_SPLIT_LIST-SPLIT_LIST.

  LOOP AT IT_MESSAGE_LIST ASSIGNING <MSG>.
    LV_TABIX = SY-TABIX.
    INSERT INITIAL LINE INTO TABLE RS_SPLIT_LIST-SPLIT_LIST->*
     ASSIGNING <SPLIT_LIST>.
    <SPLIT_LIST>-MESSAGE_LINE = LV_TABIX.

    MOVE-CORRESPONDING <MSG> TO LS_SPLIT_INFO.
    LOOP AT MT_SPLIT_INFO ASSIGNING <SPLIT_INFO> USING KEY MSG_REF
      WHERE MSG_HNDL = LS_SPLIT_INFO-MSG_HNDL.

      INSERT <SPLIT_INFO> INTO TABLE <SPLIT_LIST>-SPLIT_INFO_TAB.

      <SPLIT_INFO>-DEP_FM_DOC =
       LCL_AVC_CHECKER=>SO_DUMMY_UPD_LOGIC->REGISTRATOR->GET_PERS_ID(
           <SPLIT_INFO>-DEP_FM_DOC ).

      LOOP AT MRT_SPLIT_LIST_FPM_POS_BFR->* ASSIGNING <FPM_POS>
        USING KEY KEY WHERE
            DEP_FM_DOC = <SPLIT_INFO>-DEP_FM_DOC AND
            HROBJECT   = <SPLIT_INFO>-HROBJECT.
        INSERT <FPM_POS> INTO TABLE <SPLIT_LIST>-FPM_POS_TAB.
      ENDLOOP.
    ENDLOOP.
  ENDLOOP.

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00J ----
METHOD DO_AFTER_CHANGE_LINE.

   SPLIT_LIST_COLLECT_SPLIT_INFO(
      IV_LINE_INDEX   = IV_LINE_INDEX
      IS_OUTPUT_LINE  = IS_OUTPUT_LINE
      IO_LINE_HANDLER = IO_LINE_HANDLER  ).

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00K ----
  METHOD IF_HRFPM_LG_ENHANCEMENT_GRP~GET_APPLICABLE_TOOLS_FOR_LIST.
    DATA LS_UCOMM LIKE LINE OF CT_TOOLS_CODE .

    SUPER->IF_HRFPM_LG_ENHANCEMENT_GRP~GET_APPLICABLE_TOOLS_FOR_LIST(
        EXPORTING IT_MESSAGE_LIST = IT_MESSAGE_LIST
                  IV_SPECIFIC     = IV_SPECIFIC
                  IV_GENERIC      = IV_GENERIC
        CHANGING  CT_TOOLS_CODE   = CT_TOOLS_CODE ) .


    CHECK IV_SPECIFIC = ABAP_TRUE.

    LS_UCOMM-UCOMM = CONST_UCOMM_PREPARE_SPLIT_LIST.
    LS_UCOMM-TEXT  = TEXT-PSL.

    INSERT LS_UCOMM INTO TABLE CT_TOOLS_CODE.
  ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CM00L ----
  METHOD DET_EFFECTIVE_REQUESTED_AMOUNT.
*{   INSERT         D01K9B01JE                                        1
  DATA LS_AWOBJECT   TYPE PMAWOBJECT.
  DATA LV_DEST TYPE RFCDEST.
  DATA LS_FM_POS TYPE HRFPM_FM_POS.
  DATA LV_SUBRC TYPE SY-SUBRC.
  DATA LV_AMNT TYPE FM_TRBTR.

  TRY.
      MOVE-CORRESPONDING ID_LINE TO LS_FM_POS-KEY_POS.
*{   INSERT         D01K9B01NU                                        6
      RV_REQ_AMOUNT = LV_AMNT = IV_AMOUNTS-REQUESTED_AMOUNT.
*}   INSERT

      LS_AWOBJECT =
         CL_HRFPM_ACCOUNTING_INTERFACE=>KEY_POS_TO_AWOBJECT(
           LS_FM_POS-KEY_POS ).

      CL_HRFPM_DB_INTERFACE=>GET_SINGLE_FM_DOC(
        EXPORTING
          IS_FM_DOC_KEY_POS        = LS_FM_POS-KEY_POS
        IMPORTING
          ES_FM_DOC_POS            = LS_FM_POS ).

      CL_HRFPM_ACCOUNTING_INTERFACE=>GET_ACCOUNTING_DESTINATION(
        EXPORTING IP_COMP_CODE   = LS_FM_POS-BUKRS
        IMPORTING EP_DESTINATION = LV_DEST
        CHANGING  CP_SUBRC       = LV_SUBRC ).

      IF LV_SUBRC = 0.
*{   DELETE         D01K9B01NU                                        7
*\        lv_amnt = rv_req_amount.
*}   DELETE
        IF LV_DEST = 'NONE' .
          CALL FUNCTION 'Z_PBC_EFDOC_DET_AVC_DELTA_RFC'
            "DESTINATION lv_dest
            EXPORTING
              IV_AWREF              = LS_AWOBJECT
            CHANGING
              CV_AMNT_TR            = LV_AMNT
*{   REPLACE        D01K9B01NU                                        4
*\            EXCEPTIONS
*\               nothing_found = 1
*\               OTHERS        = 2  .
                .
*}   REPLACE
        ELSE.
          CALL FUNCTION 'Z_PBC_EFDOC_DET_AVC_DELTA_RFC'
            DESTINATION LV_DEST
            EXPORTING
              IV_AWREF              = LS_AWOBJECT
            CHANGING
              CV_AMNT_TR            = LV_AMNT
            EXCEPTIONS
              SYSTEM_FAILURE        = 1
              COMMUNICATION_FAILURE = 2
*{   REPLACE        D01K9B01NU                                        5
*\              nothing_found         = 3 .
              .
*}   REPLACE
        ENDIF.
        LV_SUBRC = SY-SUBRC.
      ENDIF.
      "ENDIF.

      IF LV_SUBRC = 0 .
        RV_REQ_AMOUNT = LV_AMNT.
      ENDIF.
*{   REPLACE        D01K9B01NU                                        9
*\    CATCH cx_hrfpm.
    CATCH CX_HRFPM ##NO_HANDLER.
*}   REPLACE
*{   DELETE         D01K9B01NU                                        8
*\      rv_req_amount = iv_amounts-requested_amount.
*}   DELETE
  ENDTRY.



*}   INSERT
  ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CO ----
PROTECTED SECTION.

  TYPES:
*"* protected components of class ZZCL_IM_HRFPM_ENHLG_GRP_AVC_UN
*"* do not include other source files here!!!
    BEGIN OF TYS_AGGREG_TYPE_AO.
  INCLUDE TYPE ZHRFPM_S_APPL_LOG_AVC_CARRIER AS CARRIER.
  TYPES:
    AVAIL_BDGT_HIST_STRG TYPE CHAR20,
    RUNID                TYPE HRFPM_RUNID,
    KEY_POS              TYPE HRFPM_FM_POS-KEY_POS,
    "this defines the context for the calculation of
    "the missing amount
*      "UNESCO uses posting periods => so the posting date
*      "has to be part of the context
    DUE_DATE             TYPE HRFPM_FM_POS-DUE_DATE,
    END OF TYS_AGGREG_TYPE_AO .
  TYPES:
    BEGIN OF TYS_AO_WITH_AVAIL_AMOUNT,
      CARRIER         TYPE  ZHRFPM_S_APPL_LOG_AVC_CARRIER,
      AVAIL_BDGT_HIST TYPE REF TO HRFPM_APPL_LOG_AVC_AMOUNTS-AVAIL_BDGT_HIST,
    END OF TYS_AO_WITH_AVAIL_AMOUNT .
  TYPES:
    BEGIN OF TYS_RUN_ADMISSIBLE,
      HROBJECT   TYPE HROBJECT,
      DUE_DATE   TYPE DATUM,
      RUNID      TYPE HRFPM_RUNID,
      "fpm_pos    TYPE hrfpm_fpm_pos,
      ADMISSIBLE TYPE BOOLE_D,
    END OF TYS_RUN_ADMISSIBLE .
  TYPES:
    BEGIN OF TYS_SPLIT_INFO,
      GLOBAL_MSG_LINE TYPE SYTABIX,
      RUNID           TYPE HRFPM_RUNID.
  INCLUDE TYPE BALMSGHNDL AS MSG_HNDL.
  INCLUDE TYPE HRFPM_FM_POS-KEY_POS AS DEP_FM_DOC .
  INCLUDE TYPE HROBJECT AS HROBJECT.
  INCLUDE TYPE HROBJECT AS HROBJECT_DP RENAMING WITH SUFFIX _DP.
  TYPES END OF TYS_SPLIT_INFO .
  TYPES:
    TYT_SPLIT_INFO TYPE STANDARD TABLE OF TYS_SPLIT_INFO WITH
       DEFAULT KEY
       WITH NON-UNIQUE SORTED KEY KEY1 COMPONENTS
           RUNID
           DEP_FM_DOC
           HROBJECT
       WITH NON-UNIQUE SORTED KEY MSG_REF COMPONENTS MSG_HNDL .
  TYPES:
    TYT_FPM_POS_BFR TYPE STANDARD TABLE OF HRFPM_FPM_POS WITH DEFAULT KEY
       WITH NON-UNIQUE SORTED KEY KEY COMPONENTS
            DEP_FM_DOC
            HROBJECT .
  TYPES:
    BEGIN OF TYS_SPLIT_LIST,
      MESSAGE_LINE   TYPE SYTABIX,
      SPLIT_INFO_TAB TYPE TYT_SPLIT_INFO,
      FPM_POS_TAB    TYPE HRFPM_FPM_POS_IT,
    END OF TYS_SPLIT_LIST .
  TYPES:
    TYT_SPLIT_LIST TYPE STANDARD TABLE OF TYS_SPLIT_LIST WITH
        DEFAULT KEY .
  TYPES:
    BEGIN OF TYS_SPLIT_LIST_RET,
      SPLIT_LIST TYPE REF TO TYT_SPLIT_LIST,
    END OF TYS_SPLIT_LIST_RET .

  DATA MRT_SPLIT_LIST_FPM_POS_BFR TYPE REF TO TYT_FPM_POS_BFR .
  DATA:
    MT_AO_WITH_AVAIL_AMOUNT TYPE STANDARD TABLE OF TYS_AO_WITH_AVAIL_AMOUNT
       WITH UNIQUE SORTED KEY CARRIER COMPONENTS CARRIER .
  DATA:
    MT_RUNID_ADMISSIBLE TYPE STANDARD TABLE OF TYS_RUN_ADMISSIBLE WITH DEFAULT KEY
      WITH UNIQUE SORTED KEY ACCESS COMPONENTS HROBJECT DUE_DATE .
  DATA MT_SPLIT_INFO TYPE TYT_SPLIT_INFO .
  DATA MT_SPLIT_LIST_FCAT TYPE SLIS_T_FIELDCAT_ALV .
  DATA MV_SW_USABLE_CHECK TYPE BOOLE_D .

  METHODS SPLIT_LIST_DISPLAY
    CHANGING
      !IT_SPLIT_LIST TYPE TABLE .
  METHODS SPLIT_LIST_PREPARE
    IMPORTING
      !IT_MESSAGE_LIST TYPE TABLE
    RETURNING
      VALUE(RS_SPLIT_LIST) TYPE TYS_SPLIT_LIST_RET .
  METHODS SPLIT_LIST_COLLECT_SPLIT_INFO
    IMPORTING
      !IS_OUTPUT_LINE TYPE DATA
      VALUE(IO_LINE_HANDLER) TYPE REF TO CX_HRFPM OPTIONAL
      !IV_LINE_INDEX TYPE SYTABIX .
  METHODS DET_AVAILABLE_BUDGET_HIST
    IMPORTING
      !IS_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS
    RETURNING
      VALUE(RV_AVAIL_BUDGET_HIST) TYPE HRFPM_APPL_LOG_AVC_AMOUNTS-AVAIL_BDGT_HIST .
  METHODS DO_BUILD_SPLIT_LIST
    IMPORTING
      !IT_MESSAGE_LIST TYPE TABLE .
  METHODS DET_EFFECTIVE_REQUESTED_AMOUNT
    IMPORTING
      !IV_AGGREGATE TYPE TYS_AO_WITH_AVAIL_AMOUNT
      !IV_AMOUNTS TYPE HRFPM_APPL_LOG_AVC_AMOUNTS
      !ID_LINE TYPE DATA
    RETURNING
      VALUE(RV_REQ_AMOUNT) TYPE HRFPM_REQ_AMOUNT_HIST .

  METHODS DO_AFTER_CHANGE_LINE
    REDEFINITION .
  METHODS FIGURE_OUT_MISSING_AMOUNT
    REDEFINITION .
  METHODS FILL_AVC_AMOUNT_FIELDS
    REDEFINITION .

* ---- ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN=CU ----
CLASS ZCL_IM_HRFPM_ENHLG_GRP_AVC_UN DEFINITION
  PUBLIC
  INHERITING FROM ZCL_IM_HRFPM_ENHLG_GRP_AVC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
  TYPE-POOLS SLIS .

  CONSTANTS CONST_UCOMM_PREPARE_SPLIT_LIST TYPE SYUCOMM VALUE 'SPLIT_LIST'. "#EC NOTEXT
  CLASS-DATA CON_VOID_AVAIL_AMOUNT TYPE HRFPM_APPL_LOG_AVC_AMOUNTS-AVAIL_BDGT_HIST READ-ONLY .
  CLASS-DATA CON_VOID_MISSING_AMOUNT TYPE HRFPM_APPL_LOG_AVC_AMOUNTS-MISSING_AMOUNT READ-ONLY .
  TYPE-POOLS ABAP .
  CLASS-DATA SV_SHOW_TECHNICAL_COLUMNS TYPE BOOLE_D READ-ONLY VALUE ABAP_FALSE. "#EC NOTEXT

  METHODS CONSTRUCTOR .
  CLASS-METHODS CLASS_CONSTRUCTOR .

  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~BEGIN_OF_GROUP_PROCESSING
    REDEFINITION .
  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~CALL_TOOL_FOR_LIST
    REDEFINITION .
  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~CHANGE_FIELD_CAT
    REDEFINITION .
  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~END_OF_GROUP_PROCESSING
    REDEFINITION .
  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~WORK_OVER_MESSAGE_LIST
    REDEFINITION .
  METHODS ZIF_HRFPM_LG_AVC_AGGREG_HNDL~CHECK_IF_AGGREGEE
    REDEFINITION .
  METHODS ZIF_HRFPM_LG_AVC_AGGREG_HNDL~CHECK_IF_USABLE
    REDEFINITION .
  METHODS ZIF_HRFPM_LG_AVC_AGGREG_HNDL~FILL_AGGREGATE_KEY
    REDEFINITION .
  METHODS IF_HRFPM_LG_ENHANCEMENT_GRP~GET_APPLICABLE_TOOLS_FOR_LIST
    REDEFINITION .