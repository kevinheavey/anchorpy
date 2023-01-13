from pathlib import Path

from anchorpy import Event, EventParser, Idl, Program
from solders.pubkey import Pubkey


def test_event_parser() -> None:
    path = Path("tests/idls/events.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    program = Program(
        idl, Pubkey.from_string("2dhGsWUzy5YKUsjZdLHLmkNpUDAXkNa9MYWsPc4Ziqzy")
    )
    logs = [
        "Program 2dhGsWUzy5YKUsjZdLHLmkNpUDAXkNa9MYWsPc4Ziqzy invoke [1]",
        "Program log: Instruction: Initialize",
        "Program data: YLjF84sCWpQFAAAAAAAAAAUAAABoZWxsbw==",
        "Program 2dhGsWUzy5YKUsjZdLHLmkNpUDAXkNa9MYWsPc4Ziqzy consumed 1019 of 1400000 compute units",
        "Program 2dhGsWUzy5YKUsjZdLHLmkNpUDAXkNa9MYWsPc4Ziqzy success",
    ]
    parser = EventParser(program.program_id, program.coder)
    evts = []
    parser.parse_logs(logs, lambda evt: evts.append(evt))
    assert len(evts) == 1
    events_coder = program.coder.events
    event_cls = events_coder.layouts["MyEvent"].datacls  # type: ignore
    expected_data = event_cls(
        data=5,
        label="hello",
    )
    expected_event = Event(name="MyEvent", data=expected_data)
    assert evts[0] == expected_event
