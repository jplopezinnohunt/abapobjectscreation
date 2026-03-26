  METHOD PREPARE_WORD.

  C_OI_CONTAINER_CONTROL_CREATOR=>GET_CONTAINER_CONTROL(
        IMPORTING
          CONTROL =  MO_CONTROL   " Container Control
          ERROR   =  MO_ERROR   " Error Object
*      retcode =     " Error Code (Obsolete)
      ).

      ME->CHECK_ERROR( ).

    IF IV_CONTAINER IS INITIAL.
      DATA: CONTAINER     TYPE REF TO CL_GUI_CUSTOM_CONTAINER.

      CREATE OBJECT CONTAINER
        EXPORTING
          CONTAINER_NAME = 'CONTAINER'.


      MO_CONTROL->INIT_CONTROL(
        EXPORTING
          INPLACE_ENABLED          = 'X'
*         inplace_resize_documents = ' '
*         inplace_scroll_documents = ' '
*         inplace_show_toolbars    = 'X'
*          no_flush                 = ' '
          R3_APPLICATION_NAME      =  'Document Container' " APPLICATION NAME
*         register_on_close_event  = ' '
*         register_on_custom_event = ' '
*         shell_style              = 1384185856
          PARENT                   =  CONTAINER   " Parent Container
*         name                     =     " Application Name
*         autoalign                = 'x'    " Control Should Fill Container
        IMPORTING
           ERROR   =  MO_ERROR
*         retcode                  =     " Error Value: Obsolete
        EXCEPTIONS
          JAVABEANNOTSUPPORTED     = 1
          OTHERS                   = 2
      ).
      ME->CHECK_ERROR( ).
    ELSE.

      MO_CONTROL->INIT_CONTROL(
      EXPORTING
        INPLACE_ENABLED          = 'X'
*       inplace_resize_documents = ' '
*       inplace_scroll_documents = ' '
*       inplace_show_toolbars    = 'X'
*       no_flush                 = ' '
        R3_APPLICATION_NAME      =  'Document Container' " APPLICATION NAME
*       register_on_close_event  = ' '
*       register_on_custom_event = ' '
*       shell_style              = 1384185856
        PARENT                   =  IV_CONTAINER   " Parent Container
*       name                     =     " Application Name
*       autoalign                = 'x'    " Control Should Fill Container
      IMPORTING
         ERROR   =  MO_ERROR
*       retcode                  =     " Error Value: Obsolete
      EXCEPTIONS
        JAVABEANNOTSUPPORTED     = 1
        OTHERS                   = 2
    ).
      ME->CHECK_ERROR( ).
    ENDIF.
    MO_CONTROL->GET_DOCUMENT_PROXY(
      EXPORTING
*    document_format    = 'NATIVE'
        DOCUMENT_TYPE      = 'Word.Document'
*    no_flush           = ' '
*    register_container = ' '
      IMPORTING
        DOCUMENT_PROXY     = MO_DOCUMENT
        ERROR              = MO_ERROR
*    retcode            =
    ).
    ME->CHECK_ERROR( ).




  ENDMETHOD.