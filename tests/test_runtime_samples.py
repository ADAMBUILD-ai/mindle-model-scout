from src.model_scout.runtime_samples import _embedding_sample_sentences


def test_product_component_probes_are_distinct_and_explicitly_generated():
    arcos = _embedding_sample_sentences({"product": "ARCOS"})
    agri = _embedding_sample_sentences({"product": "AGRI"})
    generic = _embedding_sample_sentences({"product": "OTHER"})
    assert "토지" in arcos[0] and "지적도" in arcos[0]
    assert "농산물" in agri[0]
    assert arcos != agri != generic
    assert len(arcos) == len(agri) == len(generic) == 4
