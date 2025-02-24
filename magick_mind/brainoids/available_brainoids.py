from enum import Enum as PyEnum


class AvailableBrainoids(PyEnum):
    Claude_3_5_Sonnet = "anthropic/claude-3-5-sonnet-20240620"
    # GPT_4o_Mini = "openai/gpt-4o-mini"
    GPT_4o = "openai/gpt-4o"
    GPT_4 = "openai/gpt-4"
