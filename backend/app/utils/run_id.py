from datetime import datetime

def generate_run_id(scenario: str, run_number: int, payload_bytes: int) -> str:
    """
    Generates a run_id in the format:
    scenario_runXX_payloadN_YYYYMMDD_HHMMSS
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_part = f"run{run_number:02d}"
    payload_part = f"{payload_bytes}B"

    return f"{scenario}_{run_part}_{payload_part}_{timestamp}"
