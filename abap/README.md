# SAP Gateway Entity Importer

Configuration-driven approach para crear entities en SAP Gateway Service Builder (SEGW) via código ABAP.

## 📋 Overview

En vez de automation de UI, este approach usa:
1. **JSON file** con definición de entities y properties
2. **ABAP program** que lee el JSON y genera código MPC_EXT
3. **Copy/paste** el código generado en tu MPC_EXT class

## 🎯 Ventajas

✅ **Confiable**: No depende de UI automation
✅ **Versionable**: JSON files en Git
✅ **Repetible**: Mismo JSON = mismo resultado
✅ **Rápido**: Genera código para múltiples entities a la vez
✅ **Mantenible**: Editar JSON es más fácil que UI clicks

## 📁 Files

```
abap/
├── Z_GATEWAY_ENTITY_IMPORTER.abap    # ABAP program principal
├── README.md                          # Este file
../
├── entity_config_schema.json          # JSON schema (documentación)
└── entity_config_example.json         # Ejemplo de configuración
```

## 🚀 Uso

### Paso 1: Crear JSON Configuration

Creá un file JSON que defina tus entities. Ejemplo:

```json
{
  "service_name": "Z_CRP_SRV",
  "entities": [
    {
      "name": "Certificate",
      "label": "Certificate",
      "entity_set_name": "CertificateSet",
      "properties": [
        {
          "name": "ID",
          "type": "Edm.String",
          "is_key": true,
          "nullable": false,
          "max_length": 10,
          "label": "Certificate ID"
        },
        {
          "name": "Title",
          "type": "Edm.String",
          "nullable": false,
          "max_length": 100,
          "label": "Certificate Title"
        }
      ]
    }
  ]
}
```

Ver `entity_config_example.json` para un ejemplo completo.

### Paso 2: Crear ABAP Program en SAP

1. Abrí transacción **SE38**
2. Creá nuevo program: **Z_GATEWAY_ENTITY_IMPORTER**
3. Copiá el contenido de `Z_GATEWAY_ENTITY_IMPORTER.abap`
4. Activá el program

### Paso 3: Ejecutar el Program

1. Ejecutá **Z_GATEWAY_ENTITY_IMPORTER** (F8)
2. En el selection screen, ingresá el path a tu JSON file:
   - Ejemplo: `C:\temp\entity_config.json`
   - Podés usar F4 para buscar el file
3. Ejecutá
4. El program va a:
   - Leer el JSON file
   - Validar la estructura
   - Mostrar las entities a crear
   - **Generar código MPC_EXT**

### Paso 4: Copiar Código a MPC_EXT

El program genera código ABAP. Copiá y pegá este código en tu MPC_EXT class:

1. Abrí **SEGW** transaction
2. Abrí tu proyecto (ej: Z_CRP_SRV)
3. Navegá a: **Service Implementation → MPC_EXT**
4. Hacé doble click en el method **DEFINE**
5. **Reemplazá** el contenido del method con el código generado
6. Activá la class
7. Regenerá el service (SEGW → Generate)

### Paso 5: Verificar

1. En SEGW, expandí **Data Model → Entity Types**
2. Deberías ver las entities creadas
3. Verificá properties y entity sets

## 📝 JSON Configuration Reference

### Tipos EDM Soportados

```
Edm.String       - String/text
Edm.Int32        - Integer (32-bit)
Edm.Int64        - Integer (64-bit)
Edm.Decimal      - Decimal con precision/scale
Edm.Boolean      - Boolean (true/false)
Edm.DateTime     - Date and time
Edm.Time         - Time only
Edm.DateTimeOffset - Date/time with timezone
Edm.Guid         - GUID/UUID
Edm.Binary       - Binary data
```

### Property Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ✅ | Property name |
| `type` | string | ✅ | EDM type (ver arriba) |
| `is_key` | boolean | ❌ | Es key field? (default: false) |
| `nullable` | boolean | ❌ | Puede ser null? (default: true) |
| `max_length` | integer | ❌ | Max length para Edm.String |
| `precision` | integer | ❌ | Precision para Edm.Decimal |
| `scale` | integer | ❌ | Scale para Edm.Decimal |
| `label` | string | ❌ | Human-readable label |
| `abap_fieldname` | string | ❌ | ABAP field name correspondiente |

### Entity Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ✅ | Entity Type name |
| `label` | string | ❌ | Human-readable label |
| `entity_set_name` | string | ❌ | Entity Set name (default: {name}Set) |
| `properties` | array | ✅ | List of properties |
| `navigations` | array | ❌ | Navigation properties (TODO) |

## 🔧 Troubleshooting

### Error: "File read error"
- Verificá que el path al JSON file sea correcto
- Verificá que tenés permisos de lectura
- Usá forward slashes o backslashes escapados en el path

### Error: "Invalid JSON"
- Verificá la sintaxis JSON (usa un validator online)
- Verificá que todos los campos required estén presentes
- Verificá que los tipos EDM sean válidos

### Error al activar MPC_EXT
- Verificá que el service name sea correcto
- Verificá que no haya properties duplicadas
- Verificá que al menos una property sea key

### Entities no aparecen en SEGW UI
- Después de pegar el código, **regenerá el service**
- SEGW → Generate Runtime Objects
- Refrescá la vista (F5)

## 📚 Next Steps

Una vez que el código está funcionando:

1. **Version Control**: Commitear los JSON files a Git
2. **CI/CD**: Automatizar la creación en pipelines
3. **Templates**: Crear JSON templates para patterns comunes
4. **Validation**: Agregar validación adicional si es necesario

## 🤝 Workflow Recomendado

```
Developer → Edita JSON → Ejecuta Z_GATEWAY_ENTITY_IMPORTER →
   Copia código → Pega en MPC_EXT → Activa → Regenera → ✅ Done
```

Total time: **~2 minutos** (vs 15-30 minutos manual en SEGW)

## 💡 Tips

- **Multiple entities**: Podés definir múltiples entities en un solo JSON
- **Incremental**: Podés agregar entities nuevas sin afectar las existentes (agregar al method DEFINE)
- **Backup**: Siempre guardá una copia del JSON antes de cambios grandes
- **Documentation**: El JSON file sirve como documentación del modelo

## 🐛 Known Limitations

- **Navigation properties**: Implementación básica (TODO: mejorar)
- **Associations**: Por ahora hay que crear manualmente
- **Function Imports**: No soportado (crear manualmente)
- **Annotations**: No soportado en JSON (agregar en código si es necesario)

## 📞 Support

Para issues o questions:
- Revisar los examples en `entity_config_example.json`
- Revisar el schema en `entity_config_schema.json`
- Verificar logs del program ABAP

---

**Created**: 2026-03-04
**Approach**: Configuration-driven ABAP entity creation
**Alternative to**: WebGUI automation, SAP GUI Scripting
