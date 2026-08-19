from researchops_mcp.mock_data import MOCK_PAPERS


def test_mock_papers_have_stable_ids() -> None:
    assert all("paper_id" in paper for paper in MOCK_PAPERS)
    assert len({paper["paper_id"] for paper in MOCK_PAPERS}) == len(MOCK_PAPERS)
