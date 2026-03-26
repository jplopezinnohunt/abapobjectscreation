# Technical Autopsy: Travel Management Enhancements

## Overview
UNESCO uses custom logic in Travel Management (TV) to enforce strict account assignment rules and validate travel periods against organizational policy.

## 1. Period & Dependant Validation
*   **Include**: [`ZXTRVU03`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXTRVU03_RPY.abap)
*   **Trigger**: Travel Header save/check.
*   **Key Logic**:
    1.  **Travel Privileges**: Reads Infotype `0017` for the employee.
    2.  **Feature `ZTVCK`**: Calls `CL_HRPA_FEATURE=>GET_VALUE` to determine if specific validation rules apply based on the employee's travel configuration.
    3.  **Dependant Verification**: Uses `ZCL_TRIP=>IS_DEPENDANTS_MANDATORY`. If mandatory and no dependants are listed, results in error `ZFITV:003`.
    4.  **Overlapping Checks**: Calls `ZCL_TRIP=>IS_OVERLAPPING_ALLOWED` to prevent the same traveler (or dependants) from having concurrent travel requests.

## 2. Account Assignment & Allotment Controls
*   **Include**: [`ZXTRVU05`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXTRVU05_RPY.abap)
*   **Trigger**: Financial settlement / posting simulation.
*   **Key Logic**:
    1.  **Dual Assignment Block**:
        ```abap
        IF <KONTI>-POSNR <> SPACE AND <KONTI>-KOSTL <> SPACE.
           MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
           WITH 'Please specify either Cost Center or WBS-element, not both!'.
        ENDIF.
        ```
        This ensures that travel is charged either to a Department (Cost Center) or a Project (WBS), maintaining a clean separation of funding.
    2.  **Fund Consistency**: Calls `PERFORM COMPARE_FUND_WBS` to ensure that the WBS Element's budget type matches the Fund.
    3.  **Allotment Check**: Calls `PERFORM FUND_BA_WBS_CC` which likely checks table `YFMXCHKP` for active posting windows.

## Related Objects
*   Class `ZCL_TRIP`: Central travel manager.
*   Table `YFMXCHKP`: Posting check parameters.
*   Message Class `ZFITV`: Travel specific error messages.
