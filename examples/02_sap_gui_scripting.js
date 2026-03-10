/**
 * SAP GUI Scripting - Alternativa a WebGUI
 *
 * Este approach usa la API COM de SAP GUI (Desktop)
 * en lugar de browser automation.
 *
 * Ventajas:
 *   - API oficial de SAP
 *   - Más estable que WebGUI automation
 *   - Mejor rendimiento
 *   - Selectores más confiables
 *
 * Desventajas:
 *   - Solo funciona en Windows
 *   - Requiere SAP GUI instalado localmente
 *   - Usuario debe habilitar scripting en SAP GUI
 */

const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class SapGuiScripting {
    /**
     * Conecta a SAP GUI usando COM/ActiveX
     * Usa PowerShell para interactuar con el objeto COM
     */
    async connect() {
        // Verificar si SAP GUI está corriendo usando SapROTWr
        const psScript = `
            try {
                $sapRot = New-Object -ComObject "SapROTWr.SapROTWrapper"
                $application = $sapRot.GetScriptingEngine
                $connection = $application.Children(0)
                $session = $connection.Children(0)
                Write-Output "Connected"
            } catch {
                Write-Output "Error: $_"
            }
        `;

        try {
            const { stdout } = await execPromise(`powershell -Command "${psScript}"`);
            console.log('[SapGuiScripting]', stdout.trim());
            return stdout.includes('Connected');
        } catch (error) {
            console.error('[SapGuiScripting] Failed to connect:', error.message);
            return false;
        }
    }

    /**
     * Ejemplo: Navegar a transacción SEGW
     */
    async navigateToSegw() {
        const psScript = `
            $sapRot = New-Object -ComObject "SapROTWr.SapROTWrapper"
            $application = $sapRot.GetScriptingEngine
            $session = $application.Children(0).Children(0)

            # Navegar a SEGW
            $session.findById("wnd[0]/tbar[0]/okcd").text = "/nSEGW"
            $session.findById("wnd[0]").sendVKey(0)  # Enter

            Write-Output "Navigated to SEGW"
        `;

        try {
            const { stdout } = await execPromise(`powershell -Command "${psScript}"`);
            console.log('[SapGuiScripting]', stdout.trim());
        } catch (error) {
            console.error('[SapGuiScripting] Navigation failed:', error.message);
            throw error;
        }
    }

    /**
     * Ejemplo: Crear entity en SEGW usando GUI Scripting
     */
    async createEntityInSegw(projectName, entityName) {
        const psScript = `
            $sapRot = New-Object -ComObject "SapROTWr.SapROTWrapper"
            $session = $sapRot.GetScriptingEngine.Children(0).Children(0)

            # Seleccionar proyecto en tree
            $tree = $session.findById("wnd[0]/usr/cntlCUSTOM_CONTAINER/shellcont/shell")
            $nodeKey = $tree.GetNodeKeyByPath("${projectName}\\Data Model\\Entity Types")
            $tree.selectedNode = $nodeKey

            # Click en botón Create
            $session.findById("wnd[0]/tbar[1]/btn[0]").press()

            # Llenar popup
            Start-Sleep -Milliseconds 500
            $session.findById("wnd[1]/usr/txtENTITY_NAME").text = "${entityName}"
            $session.findById("wnd[1]/tbar[0]/btn[0]").press()  # OK

            Write-Output "Entity ${entityName} created"
        `;

        try {
            const { stdout } = await execPromise(`powershell -Command "${psScript}"`);
            console.log('[SapGuiScripting]', stdout.trim());
            return true;
        } catch (error) {
            console.error('[SapGuiScripting] Entity creation failed:', error.message);
            return false;
        }
    }

    /**
     * Helper: Obtener IDs de elementos para scripting
     * Útil para debugging - muestra IDs de elementos en la pantalla actual
     */
    async dumpScreenElements() {
        const psScript = `
            $sapRot = New-Object -ComObject "SapROTWr.SapROTWrapper"
            $session = $sapRot.GetScriptingEngine.Children(0).Children(0)

            function Dump-Children {
                param($parent, $indent = 0)

                $spaces = "  " * $indent
                foreach ($child in $parent.Children) {
                    Write-Output "$spaces$($child.Id) - $($child.Type)"
                    if ($child.Children.Count -gt 0) {
                        Dump-Children -parent $child -indent ($indent + 1)
                    }
                }
            }

            Write-Output "Screen Elements:"
            Dump-Children -parent $session.findById("wnd[0]")
        `;

        try {
            const { stdout } = await execPromise(`powershell -Command "${psScript}"`);
            console.log(stdout);
        } catch (error) {
            console.error('[SapGuiScripting] Dump failed:', error.message);
        }
    }
}

// Ejemplo de uso
async function testSapGuiScripting() {
    console.log('========================================');
    console.log('SAP GUI Scripting Test');
    console.log('========================================\n');

    const sapGui = new SapGuiScripting();

    // Paso 1: Conectar
    console.log('1. Connecting to SAP GUI...');
    const connected = await sapGui.connect();

    if (!connected) {
        console.log('❌ SAP GUI no está corriendo o scripting no habilitado');
        console.log('\nPara habilitar scripting:');
        console.log('1. Abrir SAP GUI');
        console.log('2. Click derecho en barra de título');
        console.log('3. Options → Accessibility & Scripting → Scripting');
        console.log('4. Marcar "Enable scripting"');
        return;
    }

    console.log('✅ Connected\n');

    // Paso 2: Navegar a SEGW
    console.log('2. Navigating to SEGW...');
    await sapGui.navigateToSegw();
    console.log('✅ Done\n');

    // Paso 3: Crear entity
    console.log('3. Creating entity...');
    const success = await sapGui.createEntityInSegw('Z_CRP_SRV', 'TestEntity');

    if (success) {
        console.log('\n========================================');
        console.log('✅ SUCCESS!');
        console.log('========================================');
    }
}

// Descomentar para ejecutar
// testSapGuiScripting().catch(console.error);

module.exports = SapGuiScripting;
