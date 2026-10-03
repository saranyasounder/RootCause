"""
Generate a synthetic equipment error-code reference table for the
Equipment Support Copilot project.

This is ORIGINAL synthetic content, modeled on the general shape of
real hardware diagnostic taxonomies (BIOS/firmware, cooling, power,
storage, expansion bus, peripheral, and security fault categories)
but not copied from any single vendor's documentation. Codes, wording,
equipment IDs, and causes are invented for this project.

Output: data/error_codes.csv
Columns: equipment_id, model, category, error_code, description,
         severity, typical_cause, recommended_action
"""

import csv
import random

random.seed(42)

# ---------------------------------------------------------------------
# Equipment fleet: a small, mixed fleet like a real IT/ops environment
# ---------------------------------------------------------------------
EQUIPMENT = [
    {"equipment_id": "SVR-R740-01", "model": "Rack Server R740", "type": "server"},
    {"equipment_id": "SVR-R740-02", "model": "Rack Server R740", "type": "server"},
    {"equipment_id": "SVR-R650-01", "model": "Rack Server R650", "type": "server"},
    {"equipment_id": "WKS-T5820-01", "model": "Tower Workstation T5820", "type": "workstation"},
    {"equipment_id": "WKS-T5820-02", "model": "Tower Workstation T5820", "type": "workstation"},
    {"equipment_id": "LAP-LAT5540-01", "model": "Laptop Latitude 5540", "type": "laptop"},
    {"equipment_id": "LAP-LAT5540-02", "model": "Laptop Latitude 5540", "type": "laptop"},
    {"equipment_id": "TAPE-LTO9-01", "model": "Tape Library LTO-9", "type": "tape"},
    {"equipment_id": "NAS-ME412-01", "model": "Storage Array ME412", "type": "storage"},
    {"equipment_id": "FAB-ETCH-12", "model": "Etch Tool ET-12", "type": "fab_tool"},
]

TYPE_CATEGORIES = {
    "server": ["bios_firmware", "cooling", "storage_backplane", "expansion_bus", "power"],
    "workstation": ["bios_firmware", "cooling", "expansion_bus", "memory", "video"],
    "laptop": ["battery_power", "video", "audio", "memory", "bios_firmware"],
    "tape": ["tape_media", "storage_backplane"],
    "storage": ["storage_backplane", "power", "expansion_bus"],
    "fab_tool": ["calibration", "sensor", "gas_flow", "robotics"],
}

# ---------------------------------------------------------------------
# Error code catalog, grouped by category.
# Format: (code_suffix, description, severity, typical_cause, action)
# ---------------------------------------------------------------------
CATALOG = {
    "bios_firmware": [
        ("F-1010", "Firmware self-check reported a version mismatch against the signed manifest.",
         "High", "System BIOS/firmware is out of date or was interrupted during a prior update.",
         "Update firmware to the latest qualified version and re-run the boot diagnostic."),
        ("F-1022", "Configuration checksum failure detected in NVRAM.",
         "Medium", "NVRAM settings were corrupted, often after an unclean shutdown or battery depletion.",
         "Reset BIOS/UEFI to defaults, reconfigure boot order, and re-run diagnostics."),
        ("F-1035", "Secure boot policy violation on startup.",
         "High", "An unsigned or altered boot loader component was detected.",
         "Reinstall trusted boot components from a known-good image and re-enable secure boot."),
    ],
    "cooling": [
        ("C-2001", "Fan module reporting RPM below minimum threshold.",
         "Medium", "Fan bearing wear or dust/debris obstruction reducing airflow.",
         "Inspect and clean intake vents; replace fan module if RPM remains below threshold."),
        ("C-2014", "Thermal zone exceeded warning setpoint during load test.",
         "High", "Inadequate airflow, failed fan, or degraded thermal paste on a hot component.",
         "Check fan operation, reseat heatsink, and verify rack/enclosure airflow clearance."),
        ("C-2028", "Redundant fan pair mismatch — one fan idle while its pair is active.",
         "Low", "One fan in a redundant pair has failed or is not receiving control signal.",
         "Reseat fan connector; replace the idle fan unit if it remains unresponsive."),
    ],
    "storage_backplane": [
        ("S-3005", "Backplane reports drive slot status inconsistent with controller view.",
         "High", "Loose drive seating, failing backplane connector, or a degraded drive.",
         "Reseat the drive and cable; swap to a known-good slot to isolate backplane vs. drive."),
        ("S-3019", "Predictive failure signal received from drive self-monitoring.",
         "Critical", "Drive is reporting early indicators of mechanical or media failure.",
         "Back up data immediately and schedule drive replacement before failure occurs."),
        ("S-3033", "RAID controller battery/cache module reporting degraded charge.",
         "Medium", "Cache backup battery is nearing end of life.",
         "Replace the cache backup battery/module at the next maintenance window."),
    ],
    "expansion_bus": [
        ("P-4002", "PCIe link negotiated at a lower width/speed than expected.",
         "Medium", "Poor seating of the adapter card or a marginal slot connection.",
         "Reseat the adapter card fully and verify slot compatibility; retest link training."),
        ("P-4017", "PCIe device present but not responding to bus queries.",
         "High", "Card failure, firmware hang on the device, or power delivery fault to the slot.",
         "Reseat the card; test in an alternate slot; replace card if issue persists."),
    ],
    "memory": [
        ("M-5003", "Memory module failed pattern test during POST diagnostics.",
         "High", "A DIMM has a physical fault or is improperly seated.",
         "Reseat the DIMM; if the fault follows the slot, the module should be replaced."),
        ("M-5011", "SMBIOS memory configuration does not match physically installed DIMMs.",
         "Low", "BIOS cached an outdated memory map, often after a recent memory change.",
         "Reboot to allow BIOS to re-enumerate memory; update firmware if mismatch persists."),
    ],
    "video": [
        ("V-6004", "Display self-test detected pixel-level rendering errors.",
         "Low", "Panel defect or a loose display cable connection.",
         "Reseat the display cable; replace the panel if defects persist after reseating."),
        ("V-6009", "GPU reported a driver timeout during stress test.",
         "Medium", "Overheating GPU, outdated driver, or insufficient power delivery.",
         "Update GPU drivers, verify cooling, and confirm power connector seating."),
    ],
    "audio": [
        ("A-7002", "Internal speaker self-test produced no audible tone.",
         "Low", "Speaker disconnected internally, or external jack is muting internal output.",
         "Unplug external audio devices and reseat the internal speaker connector."),
    ],
    "battery_power": [
        ("B-8001", "System unable to detect connected AC charger.",
         "Medium", "Faulty charger, damaged port, or loose power connection.",
         "Reseat the power cable at both ends; test with a known-good charger."),
        ("B-8013", "Battery health check reports capacity below service threshold.",
         "Medium", "Normal battery wear over charge cycles, or a battery nearing end of life.",
         "Schedule battery replacement; avoid deep discharge cycles in the interim."),
        ("B-8022", "Charger wattage/type could not be identified by the system.",
         "Low", "Non-OEM or damaged charger is being used.",
         "Replace with an OEM-specified charger and retest."),
    ],
    "power": [
        ("W-4501", "Redundant power supply reporting a single-unit failure.",
         "High", "PSU has failed internally or lost input power from its feed.",
         "Verify input power to the failed unit; replace the PSU if it does not recover."),
        ("W-4509", "Power supply input voltage out of qualified range.",
         "Medium", "Unstable upstream power source or a loose input connector.",
         "Verify PDU/outlet voltage and reseat the power input connector."),
    ],
    "tape_media": [
        ("T-9004", "Tape drive reports a media/drive generation mismatch.",
         "Low", "Incompatible tape cartridge generation inserted into the drive.",
         "Insert a cartridge of the correct supported generation for this drive."),
        ("T-9011", "Read-after-write verification failed on tape media.",
         "High", "Degraded or damaged tape media, or a drive head requiring cleaning.",
         "Retry with a different cartridge; run a cleaning cartridge cycle if failures continue."),
    ],
    "calibration": [
        ("K-1101", "Process chamber calibration drift exceeded control limits.",
         "High", "Sensor drift since last calibration cycle, or recent maintenance disturbed alignment.",
         "Run full recalibration sequence and verify against reference standard before resuming production."),
        ("K-1108", "End-point detection sensor reading outside expected calibration curve.",
         "Medium", "Sensor window contamination or aging light source.",
         "Clean sensor optics and inspect light source; recalibrate against reference wafer."),
    ],
    "sensor": [
        ("N-1205", "Pressure sensor reading inconsistent with redundant sensor pair.",
         "High", "One sensor has drifted or failed; possible wiring fault.",
         "Cross-check both sensors against a calibrated reference gauge and replace the outlier."),
    ],
    "gas_flow": [
        ("G-1301", "Mass flow controller reporting flow rate outside setpoint tolerance.",
         "Critical", "MFC calibration drift, partial blockage, or upstream pressure fluctuation.",
         "Verify upstream supply pressure, then recalibrate or replace the MFC."),
    ],
    "robotics": [
        ("R-1402", "Wafer handling robot reported a position deviation fault during transfer.",
         "High", "Encoder drift, mechanical wear, or an obstruction in the transfer path.",
         "Home the robot, inspect the transfer path for obstructions, and re-teach positions if the fault recurs."),
    ],
}


def generate_rows():
    rows = []
    for eq in EQUIPMENT:
        categories = TYPE_CATEGORIES[eq["type"]]
        for cat in categories:
            for suffix, desc, severity, cause, action in CATALOG[cat]:
                # Not every unit has hit every fault — sample realistically
                if random.random() < 0.7:
                    rows.append({
                        "equipment_id": eq["equipment_id"],
                        "model": eq["model"],
                        "category": cat,
                        "error_code": suffix,
                        "description": desc,
                        "severity": severity,
                        "typical_cause": cause,
                        "recommended_action": action,
                    })
    return rows


def main():
    rows = generate_rows()
    out_path = "data/error_codes.csv"
    fieldnames = [
        "equipment_id", "model", "category", "error_code",
        "description", "severity", "typical_cause", "recommended_action",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()