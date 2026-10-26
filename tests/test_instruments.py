"""Tests of the instrument helpers with a fake pyvisa resource (no hardware needed)."""

import numpy as np
import pytest

from pemlab.instruments import (
    FunctionGenerator,
    MeasurementLog,
    Oscilloscope,
    PowerSupply,
    find_instruments,
    measure_current,
    measure_repeated,
    measure_resistance,
    measure_series,
    measure_temperature_pt100,
    measure_voltage,
    pt100_temperature,
)
from pemlab.instruments.discovery import device_type, variable_names


class FakeResource:
    """Records what is written and answers queries from a dictionary."""

    def __init__(self, answers=None, binary=None):
        self.written = []
        self.queried = []
        self.answers = answers or {}
        self.binary = binary or {}
        self.timeout = None
        self.closed = False

    def write(self, command):
        self.written.append(command)

    def query(self, command):
        self.queried.append(command)
        return self.answers[command]

    def query_binary_values(self, command, datatype="B", container=list):
        return container(self.binary[command])

    def close(self):
        self.closed = True


class FakeManager:
    def __init__(self, devices):
        self.devices = devices  # address -> FakeResource or None (cannot be opened)

    def list_resources(self):
        return tuple(self.devices)

    def open_resource(self, address):
        if self.devices[address] is None:
            raise OSError("cannot open")
        return self.devices[address]


IDN_DMM = "RIGOL TECHNOLOGIES,DM3068,DM3O1,00.01"
IDN_SOURCE = "RIGOL TECHNOLOGIES,DP832,DP8C1,00.01"


def test_device_type_and_names():
    assert device_type(IDN_DMM) == "dmm"
    assert device_type(IDN_SOURCE) == "source"
    assert device_type("RIGOL TECHNOLOGIES,DG1062Z,DG1,00.01") == "awg"
    assert device_type("RIGOL TECHNOLOGIES,DS1054Z,DS1,00.01") == "scope"
    assert device_type("ACME,Gizmo,1,2") == "device"
    assert device_type(None) == "device"
    assert variable_names([IDN_DMM, IDN_SOURCE, IDN_DMM]) == ["dmm_1", "source_1", "dmm_2"]


def test_find_instruments_prints_code(capsys):
    manager = FakeManager({
        "TCPIP::141.48.16.191::INSTR": FakeResource({"*IDN?": IDN_DMM + "\n"}),
        "TCPIP::141.48.16.192::INSTR": FakeResource({"*IDN?": IDN_SOURCE}),
        "ASRL1::INSTR": None,
    })
    find_instruments(manager)
    out = capsys.readouterr().out
    assert "dmm_1_add = 'TCPIP::141.48.16.191::INSTR'" in out
    assert "dmm_1 = rm.open_resource(dmm_1_add)" in out
    assert "source_1 = PowerSupply(rm.open_resource(source_1_add))" in out
    assert "from pemlab.instruments import PowerSupply" in out
    assert "no answer" in out  # the port that could not be opened
    assert manager.devices["TCPIP::141.48.16.191::INSTR"].closed


def test_find_instruments_without_devices(capsys):
    find_instruments(FakeManager({}))
    assert "No instruments found" in capsys.readouterr().out


def test_measure_voltage_sends_the_commands_and_returns_a_float():
    dmm = FakeResource({":MEASure:VOLTage:DC?": "1.2345\n"})
    assert measure_voltage(dmm, range=1) == 1.2345
    assert dmm.written == [":MEASure MANU", ":MEASure:VOLTage:DC 1"]


def test_measure_current_resistance_and_ac():
    dmm = FakeResource({
        ":MEASure:CURRent:DC?": "0.001",
        ":MEASure:VOLTage:AC?": "2.0",
        ":MEASure:RESistance?": "100.5",
        ":MEASure:FRESistance?": "99.9",
    })
    assert measure_current(dmm) == 0.001
    assert measure_voltage(dmm, ac=True) == 2.0
    assert measure_resistance(dmm) == 100.5
    assert measure_resistance(dmm, four_wire=True) == 99.9
    assert ":MEASure:CURRent:DC" in dmm.written  # no range: command without argument


def test_pt100_temperature():
    assert pt100_temperature(100.0) == pytest.approx(0.0, abs=1e-9)
    assert pt100_temperature(138.5055) == pytest.approx(100.0, abs=0.01)
    assert pt100_temperature(80.306) == pytest.approx(-50.0, abs=0.01)
    assert pt100_temperature(1385.055, r0=1000) == pytest.approx(100.0, abs=0.01)
    dmm = FakeResource({":MEASure:FRESistance?": "109.73"})
    assert measure_temperature_pt100(dmm) == pytest.approx(25.0, abs=0.05)


def test_power_supply():
    resource = FakeResource()
    source = PowerSupply(resource)
    source.settings(1.1, 0.1)
    source.on()
    source.off()
    source.settings(5, 0.5, channel=2)
    assert resource.written == [
        "APPL CH1,1.1,0.1", "OUTPUT CH1,ON", "OUTPUT CH1,OFF", "APPL CH2,5,0.5",
    ]


def test_power_supply_output_switches_off_after_an_error():
    resource = FakeResource()
    source = PowerSupply(resource)
    with pytest.raises(RuntimeError), source.output():
        raise RuntimeError("boom")
    assert resource.written == ["OUTPUT CH1,ON", "OUTPUT CH1,OFF"]


def test_function_generator():
    resource = FakeResource()
    awg = FunctionGenerator(resource)
    awg.settings("square", frequency=500, amplitude=2, offset=0.5)
    awg.on()
    awg.off(channel=2)
    assert resource.written == [
        ":SOURce1:APPLy:SQUare 500,2,0.5,0", ":OUTPut1 ON", ":OUTPut2 OFF",
    ]
    with pytest.raises(ValueError):
        awg.settings("triangle-ish")


def test_oscilloscope_measure_waveform_and_screenshot(tmp_path):
    preamble = "0,0,3,1,0.5,-1.0,2,0.25,10,128"  # x: 0.5 s steps; y: 0.25 V per step
    resource = FakeResource(
        {":MEASure:ITEM? VPP,CHANnel2": "3.3", ":WAVeform:PREamble?": preamble},
        {":WAVeform:DATA?": [128, 132, 136], ":DISPlay:DATA? ON,OFF,PNG": [137, 80, 78, 71]},
    )
    scope = Oscilloscope(resource)
    assert scope.measure("vpp", channel=2) == 3.3
    time, voltage = scope.read_waveform(channel=1)
    expected_voltage = [(128 - 10 - 128) * 0.25, (132 - 138) * 0.25, (136 - 138) * 0.25]
    expected_time = [(0 - 2) * 0.5 - 1.0, (1 - 2) * 0.5 - 1.0, 0 * 0.5 - 1.0]
    assert voltage.tolist() == pytest.approx(expected_voltage)
    assert time.tolist() == pytest.approx(expected_time)
    path = scope.screenshot(tmp_path / "shots" / "scope.png")
    assert path.read_bytes() == bytes([137, 80, 78, 71])
    with pytest.raises(ValueError):
        scope.measure("nonsense")


def test_measurement_log_saves_csv_in_pemlab_columns(tmp_path):
    log = MeasurementLog("U [V]", "I [A]")
    log.add(1, 0.001)
    log.add(2, 0.002)
    with pytest.raises(ValueError):
        log.add(3)
    path = log.save(tmp_path / "data" / "r.csv")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == ["U [V],I [A]", "1,0.001", "2,0.002"]
    assert len(log) == 2


def test_measurement_log_from_arrays():
    log = MeasurementLog.from_arrays(["t [s]", "U [V]"], np.array([0, 1]), np.array([5, 6]))
    assert log.rows == [(0.0, 5.0), (1.0, 6.0)]


def test_measure_series_and_repeated():
    state = {"u": 0.0}
    log = measure_series(
        [1, 2, 3],
        lambda value: state.update(u=value),
        lambda: (state["u"] / 10, state["u"] / 5),
        ["U [V]", "I [A]", "P [W]"],
        settle=0,
        verbose=False,
    )
    assert log.rows == [(1.0, 0.1, 0.2), (2.0, 0.2, 0.4), (3.0, 0.3, 0.6)]
    counter = iter(range(5))
    assert measure_repeated(lambda: next(counter), n=3) == [0, 1, 2]
