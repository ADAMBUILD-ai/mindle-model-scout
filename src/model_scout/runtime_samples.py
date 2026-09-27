from __future__ import annotations

def _embedding_sample_sentences(request: dict) -> list[str]:
    """Choose transparent, deterministic component probes for the requesting product."""
    product = str(request.get("product") or request.get("project") or "").casefold()
    if product == "arcos":
        return [
            "토지 조건과 지적도 문서의 적합성 검색",
            "대상 토지의 도로 접면과 용도지역 조건",
            "위성영상의 도로 건물 수계 정보",
            "일반 영상 자막 편집",
        ]
    if product == "agri":
        return [
            "농산물 공급자와 시장 자료 의미 검색",
            "농산물 거래 자료와 공급자 조건",
            "작물 병해 현장 이미지 분류",
            "건축 도면 OCR",
        ]
    return ["한국어 문서 의미 검색", "다국어 임베딩 모델", "건축 도면 OCR", "financial filing evidence retrieval"]


