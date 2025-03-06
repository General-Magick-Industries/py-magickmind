from enum import Enum as PyEnum


class AvailableBrainoids(PyEnum):
    Claude_3_5_Sonnet = "anthropic/claude-3-5-sonnet-20240620"
    Claude_3_7_Sonnet = "anthropic/claude-3-7-sonnet-latest"
    # GPT_4o_Mini = "openai/gpt-4o-mini"
    GPT_4o = "openai/gpt-4o"
    GPT_4 = "openai/gpt-4"
    QWEN_2_5_72B_INSTRUCT_TURBO = "together_ai/Qwen2.5-72B-Instruct-Turbo"
