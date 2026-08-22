from app.rag import chunks, embed, generate
def test_embedding_is_deterministic(): assert embed("spedizione danneggiata") == embed("spedizione danneggiata")
def test_chunk_overlap(): assert len(chunks("x "*1000)) > 1
def test_guardrail_without_context(): assert generate("test",[]).grounded is False


