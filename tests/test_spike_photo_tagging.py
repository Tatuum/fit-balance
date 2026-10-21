import pytest
from pydantic import ValidationError
from spike_photo_tagging import SpikeResult, build_prompt, parse_response

from fit_balance.scoring import load_effects_table


def test_build_prompt_lists_every_technique_in_effects_table():
    vocabulary = list(load_effects_table())
    prompt = build_prompt(vocabulary)
    for name in vocabulary:
        assert f"- {name}\n" in prompt
    assert "uncertain_note" in prompt


def test_parse_response_valid_json():
    result = parse_response('{"techniques": ["v_neck", "a_line"], "uncertain_note": null}')
    assert result == SpikeResult(techniques=["v_neck", "a_line"], uncertain_note=None)


def test_parse_response_keeps_uncertain_note():
    result = parse_response('{"techniques": [], "uncertain_note": "asymmetric hem"}')
    assert result.techniques == []
    assert result.uncertain_note == "asymmetric hem"


def test_parse_response_strips_code_fence():
    raw = '```json\n{"techniques": ["peplum"]}\n```'
    assert parse_response(raw).techniques == ["peplum"]


def test_parse_response_rejects_malformed_output():
    with pytest.raises(ValidationError):
        parse_response("I think this is a v-neck dress.")


def test_parse_response_rejects_wrong_shape():
    with pytest.raises(ValidationError):
        parse_response('{"techniques": "v_neck"}')
