"""Find the connected VISA instruments and print the code to open them."""

import re

_TYPES = {
    "dmm": r"^(DM\d|DMM|34\d\d\d)",
    "source": r"^(DP\d|E36\d|N67\d|N57\d|SPD|2230)",
    "awg": r"^(DG\d|33\d\d\d|AFG|SDG)",
    "scope": r"^(DS\d|DHO|MSO|DSO|TDS|SDS|DPO)",
}
# pemlab classes that wrap the resource (the DMM functions take the plain resource)
_WRAPPERS = {"source": "PowerSupply", "awg": "FunctionGenerator", "scope": "Oscilloscope"}


def device_type(idn: str | None) -> str:
    """Kind of instrument from its *IDN? answer ('manufacturer,model,serial,version')."""
    parts = (idn or "").split(",")
    model = parts[1].strip() if len(parts) > 1 else ""
    for kind, pattern in _TYPES.items():
        if re.match(pattern, model, re.IGNORECASE):
            return kind
    return "device"


def variable_names(idns: list[str | None]) -> list[str]:
    """One variable name per instrument, numbered per kind: dmm_1, dmm_2, source_1, ..."""
    counts: dict[str, int] = {}
    names = []
    for idn in idns:
        kind = device_type(idn)
        counts[kind] = counts.get(kind, 0) + 1
        names.append(f"{kind}_{counts[kind]}")
    return names


def instruments_to_text(found: list[tuple[str, str | None]]) -> str:
    """Overview of (address, *IDN? answer) pairs and the code that opens every instrument."""
    idns = [idn for _, idn in found]
    names = variable_names(idns)
    kinds = [device_type(idn) for idn in idns]

    overview = [f"{address}  {idn or '(no answer to *IDN?)'}" for address, idn in found]
    wrappers = sorted({_WRAPPERS[kind] for kind in kinds if kind in _WRAPPERS})

    code = ["import pyvisa"]
    if wrappers:
        code.append("from pemlab.instruments import " + ", ".join(wrappers))
    code += ["", "rm = pyvisa.ResourceManager()", ""]
    for (address, idn), name, kind in zip(found, names, kinds, strict=True):
        opened = f"rm.open_resource({name}_add)"
        wrapper = _WRAPPERS.get(kind)
        code += [
            f"# {idn or 'no answer to *IDN?'}",
            f"{name}_add = '{address}'",
            f"{name} = {wrapper}({opened})" if wrapper else f"{name} = {opened}",
            "",
        ]
    return "\n".join([*overview, "", "# --- copy into your script ---", *code]).rstrip() + "\n"


def _ask_idn(rm, address: str, timeout_ms: int) -> str | None:
    """The *IDN? answer of an instrument, None if it does not answer."""
    try:
        device = rm.open_resource(address)
    except Exception:  # pyvisa raises its own error types, any failure means "not usable"
        return None
    try:
        device.timeout = timeout_ms
        return device.query("*IDN?").strip()
    except Exception:
        return None
    finally:
        device.close()


def find_instruments(rm=None, timeout_ms: int = 2000) -> None:
    """Print all connected instruments and the code to open them.

    Call it once, copy the printed block into your script and delete the call again.
    `rm` is an optional pyvisa ResourceManager (default: the standard backend).
    """
    if rm is None:
        import pyvisa  # optional dependency: pip install "pemlab[instruments]"

        rm = pyvisa.ResourceManager()
    found = [(address, _ask_idn(rm, address, timeout_ms)) for address in rm.list_resources()]
    print(instruments_to_text(found) if found else "No instruments found.")
