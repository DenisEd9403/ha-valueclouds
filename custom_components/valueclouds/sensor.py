```python
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ValueCloudsCoordinator


SENSORS = [
    (
        "battery_soc",
        "Batería",
        "bt_battery_capacity",
        PERCENTAGE,
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "battery_voltage",
        "Tensión batería",
        "bt_bms_battery_voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "battery_current",
        "Corriente batería",
        "bt_bms_battery_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "battery_power",
        "Potencia batería",
        "battery_active_discharging_power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "solar_power",
        "Potencia solar",
        "pv_output_power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "solar_voltage",
        "Tensión PV1",
        "pv_voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "load_power",
        "Potencia carga",
        "load_active_power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "grid_power",
        "Potencia red",
        "grid_active_sell_power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    (
        "solar_energy",
        "Energía solar acumulada",
        "energy_total",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    (
        "grid_energy_import",
        "Energía comprada",
        "energy_total_from_grid",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    (
        "grid_energy_export",
        "Energía exportada",
        "energy_total_to_grid",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    (
        "load_energy",
        "Energía consumida",
        "load_energy_total",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    (
        "inverter_voltage",
        "Tensión inversor",
        "bc_phase_a_inverter_voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ValueClouds sensors."""

    coordinator: ValueCloudsCoordinator = hass.data["valueclouds"][
        entry.entry_id
    ]

    async_add_entities(
        ValueCloudsSensor(
            coordinator,
            entry.entry_id,
            sensor_id,
            name,
            parameter,
            unit,
            device_class,
            state_class,
        )
        for (
            sensor_id,
            name,
            parameter,
            unit,
            device_class,
            state_class,
        ) in SENSORS
    )


class ValueCloudsSensor(
    CoordinatorEntity[ValueCloudsCoordinator],
    SensorEntity,
):
    """ValueClouds sensor."""

    def __init__(
        self,
        coordinator: ValueCloudsCoordinator,
        entry_id: str,
        sensor_id: str,
        name: str,
        parameter: str,
        unit: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
    ) -> None:
        super().__init__(coordinator)

        self._parameter = parameter
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{sensor_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self):
        """Return the sensor value."""

        data = self.coordinator.data

        if not data:
            return None

        pars = data.get("data", {}).get("pars", {})

        for group in pars.values():
            if not isinstance(group, list):
                continue

            for item in group:
                if item.get("id") == self._parameter:
                    value = item.get("val")

                    if value is None:
                        return None

                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return value

        return None
```
