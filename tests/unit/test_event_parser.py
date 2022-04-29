from pathlib import Path
import json
from anchorpy import EventParser, Idl, Program, Event
from solana.publickey import PublicKey


def test_event_parser() -> None:
    path = Path("tests/idls/events.json")
    with path.open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    program = Program(idl, PublicKey("2dhGsWUzy5YKUsjZdLHLmkNpUDAXkNa9MYWsPc4Ziqzy"))
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
