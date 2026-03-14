from app.engine.inference.types import ModelRequest, ModelResponse

def test_model_request_defaults():
    request = ModelRequest(system_prompt="sys", user_prompt="user", model="gpt")

    assert request.system_prompt == "sys"
    assert request.user_prompt == "user"
    assert request.model == "gpt"
    assert request.temperature == 0.0
    assert request.top_p == 1.0
    assert request.max_tokens is None


def test_model_response_fields():
    response = ModelResponse(raw_text="hello", provider="openai", model="gpt-4")

    assert response.raw_text == "hello"
    assert response.provider == "openai"
    assert response.model == "gpt-4"
