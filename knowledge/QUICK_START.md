# Quick Start Guide

## 5 minutos para crear entities en SEGW

### 1️⃣ Preparar JSON (1 min)

Editá `entity_config_example.json` o creá uno nuevo:

```json
{
  "service_name": "Z_CRP_SRV",
  "entities": [
    {
      "name": "MiEntity",
      "properties": [
        {
          "name": "ID",
          "type": "Edm.String",
          "is_key": true,
          "max_length": 10
        },
        {
          "name": "Nombre",
          "type": "Edm.String",
          "max_length": 100
        }
      ]
    }
  ]
}
```

Guardá el file en: `C:\temp\entity_config.json`

### 2️⃣ Crear ABAP Program (2 min)

1. SAP → SE38
2. Crear: `Z_GATEWAY_ENTITY_IMPORTER`
3. Copiar código de `Z_GATEWAY_ENTITY_IMPORTER.abap`
4. Activar (Ctrl+F3)

### 3️⃣ Ejecutar Program (1 min)

1. F8 para ejecutar
2. Ingresar path: `C:\temp\entity_config.json`
3. Ver el código generado en output

### 4️⃣ Copiar a MPC_EXT (1 min)

1. SEGW → Tu proyecto
2. Service Implementation → MPC_EXT → DEFINE method
3. Ctrl+A (seleccionar todo)
4. Pegar código generado
5. Activar
6. SEGW → Generate

### 5️⃣ Verificar

SEGW → Data Model → Entity Types → Ver tus entities ✅

---

## Ejemplo Completo

**JSON Input:**
```json
{
  "service_name": "Z_TEST_SRV",
  "entities": [
    {
      "name": "Product",
      "properties": [
        {"name": "ProductID", "type": "Edm.String", "is_key": true, "max_length": 10},
        {"name": "Name", "type": "Edm.String", "max_length": 100},
        {"name": "Price", "type": "Edm.Decimal", "precision": 10, "scale": 2}
      ]
    }
  ]
}
```

**Generated ABAP Code:**
```abap
METHOD define.
  CALL METHOD super->define.

  DATA: lo_entity TYPE REF TO /iwbep/if_mgw_odata_entity_typ,
        lo_property TYPE REF TO /iwbep/if_mgw_odata_property.

  lo_entity = model->create_entity_type( iv_entity_type_name = 'Product' ).

  lo_property = lo_entity->create_property( iv_property_name = 'ProductID' ).
  lo_property->set_is_key( ).
  lo_property->set_max_length( 10 ).

  lo_property = lo_entity->create_property( iv_property_name = 'Name' ).
  lo_property->set_max_length( 100 ).

  lo_property = lo_entity->create_property( iv_property_name = 'Price' ).
  lo_property->set_precision( 10 ).
  lo_property->set_scale( 2 ).

  model->create_entity_set(
    iv_entity_set_name = 'ProductSet'
    iv_entity_type_name = 'Product' ).

ENDMETHOD.
```

**Result:**
Entity `Product` con `ProductSet` creado en SEGW ✅

---

## Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| File not found | Verificar path completo (ej: `C:\temp\file.json`) |
| JSON parse error | Verificar sintaxis en jsonlint.com |
| Code syntax error | Verificar que service_name y entity names sean válidos |
| No aparece en SEGW | Regenerar service (SEGW → Generate) |

---

## Pro Tips

💡 **Multiple entities**: Poné todas en un JSON, se crean todas de una
💡 **Templates**: Guardá JSONs base para reutilizar
💡 **Git**: Versioná los JSONs junto con tu código
💡 **Backup**: Antes de regenerar, exportá el service por las dudas

---

Listo! Ahora tenés entities en 5 minutos sin clickear en SEGW 🎉
