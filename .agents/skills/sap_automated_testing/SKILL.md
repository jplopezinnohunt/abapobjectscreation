---
name: SAP Automated OData Testing
description: Protocol for mathematically verifying the successful generation and activation of OData services in SAP Gateway.
---

# SAP Automated OData Testing

When the Orchestrator dispatches an Execution Agent (e.g., UI Playwright Agent) to build an SEGW project, generate the runtime artifacts, and activate the service in `/IWFND/MAINT_SERVICE`, the Orchestrator MUST NOT immediately report success to the user based solely on UI clicks or BAPI return codes.

Success must be mathematically proven via real HTTP requests.

## 1. The Validation Script Requirement
As the final step of any OData generation task, the Orchestrator must generate and execute a validation script (e.g., `test_odata_endpoint.js`) inside the `Zagentexecution/tasks/` workspace.

### Core Testing Protocol
1. **Target Identification:** The script must target the host defined in `sap_auth.json` (e.g., `http://<host>:<port>/sap/opu/odata/sap/<SERVICE_NAME>_SRV/$metadata`).
2. **Authentication:** The script must use standard Basic Authentication reading from `sap_auth.json`.
3. **Execution Tool:** The script must utilize industry-standard tools like `axios` or native Node `fetch`.
4. **Validation Criteria:**
   - The HTTP response code MUST be `200 OK`. Any `401`, `403`, `404`, or `500` triggers an immediate localized failure and is reported back to the SME Architects for debugging.
   - The response body (XML) MUST be parsed or checked to ensure the defined `EntitySets` actually exist in the `$metadata` document.

## 2. Example Validation Script Pattern
The generated verification script should resemble the following:

```javascript
const axios = require('axios');
const fs = require('fs');

async function testOData() {
    const auth = JSON.parse(fs.readFileSync('../../config/sap_auth.json', 'utf8'));
    const serviceUrl = `http://${auth.host}:${auth.port}/sap/opu/odata/sap/ZTEST_SRV/$metadata`;
    
    try {
        const response = await axios.get(serviceUrl, {
            auth: {
                username: auth.user,
                password: auth.password
            }
        });
        
        if (response.status === 200 && response.data.includes('EntitySet Name="Materials"')) {
            console.log("SUCCESS: Service is active and EntitySet verified.");
            process.exit(0); // Orchestrator reads success
        } else {
            console.error("FAILURE: MetaData incomplete.");
            process.exit(1);
        }
    } catch (error) {
        console.error(`HTTP ERROR: ${error.response ? error.response.status : error.message}`);
        process.exit(1); // Orchestrator reads failure, triggers Debugging/Healing loop
    }
}
testOData();
```

Only after this script returns a perfect `exit(0)` is the Orchestrator allowed to mark the OData generation task as fully "Verified" and push the code to Git via the CI/CD agent.
