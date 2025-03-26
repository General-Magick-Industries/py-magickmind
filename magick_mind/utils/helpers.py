from litellm import embedding


def get_embedding(query: str) -> list[float]:
    """Get embedding for a query using LiteLLM's embedding function"""
    response = embedding(model="text-embedding-3-large", input=[query])
    return response.data[0]["embedding"]
