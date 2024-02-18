import io

import textfsm


def serialize_textfsm(plain_data: str, template: str) -> list[dict]:
    dict_results = []
    template_file = io.StringIO(template)
    fsm = textfsm.TextFSM(template_file)
    for fsm_result in fsm.ParseText(plain_data):
        dict_results.append({k: v for k, v in zip(fsm.header, fsm_result)})
    return dict_results
