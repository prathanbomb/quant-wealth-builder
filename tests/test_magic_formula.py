"""Unit tests for Magic Formula calculation module."""

import pytest
import pandas as pd

from src.magic_formula import (
    calculate_earnings_yield,
    calculate_roc,
    rank_stocks,
    get_top_picks,
)


class TestCalculateEarningsYield:
    """Tests for calculate_earnings_yield function."""

    def test_earnings_yield_valid_inputs(self):
        """Should calculate correct earnings yield with valid inputs."""
        # EBIT = 100, EV = 1000 -> EY = 0.10 (10%)
        result = calculate_earnings_yield(ebit=100, enterprise_value=1000)
        assert result == 0.10

    def test_earnings_yield_large_values(self):
        """Should handle large real-world values."""
        # Apple-like: EBIT = 124.5B, EV = 3.4T -> EY ≈ 3.66%
        result = calculate_earnings_yield(
            ebit=124_500_000_000,
            enterprise_value=3_400_000_000_000
        )
        assert result == pytest.approx(0.0366, rel=0.01)

    def test_earnings_yield_negative_ebit(self):
        """Should handle negative EBIT (unprofitable company)."""
        result = calculate_earnings_yield(ebit=-50, enterprise_value=1000)
        assert result == -0.05

    def test_earnings_yield_zero_ev_returns_none(self):
        """Should return None when enterprise value is zero."""
        result = calculate_earnings_yield(ebit=100, enterprise_value=0)
        assert result is None

    def test_earnings_yield_negative_ev_returns_none(self):
        """Should return None when enterprise value is negative."""
        result = calculate_earnings_yield(ebit=100, enterprise_value=-500)
        assert result is None


class TestCalculateROC:
    """Tests for calculate_roc function."""

    def test_roc_valid_inputs(self):
        """Should calculate correct ROC with valid inputs."""
        # EBIT = 100, Total Assets = 1000, Current Liabilities = 200
        # Capital Employed = 800, ROC = 100/800 = 0.125 (12.5%)
        result = calculate_roc(
            ebit=100,
            total_assets=1000,
            current_liabilities=200
        )
        assert result == 0.125

    def test_roc_large_values(self):
        """Should handle large real-world values."""
        # EBIT = 124.5B, Total Assets = 365B, Current Liabilities = 176B
        # Capital Employed = 189B, ROC ≈ 65.9%
        result = calculate_roc(
            ebit=124_500_000_000,
            total_assets=365_000_000_000,
            current_liabilities=176_000_000_000
        )
        assert result == pytest.approx(0.659, rel=0.01)

    def test_roc_negative_ebit(self):
        """Should handle negative EBIT (unprofitable company)."""
        result = calculate_roc(
            ebit=-50,
            total_assets=1000,
            current_liabilities=200
        )
        assert result == pytest.approx(-0.0625, rel=0.01)

    def test_roc_zero_capital_returns_none(self):
        """Should return None when capital employed is zero."""
        # Total Assets = Current Liabilities -> Capital = 0
        result = calculate_roc(
            ebit=100,
            total_assets=500,
            current_liabilities=500
        )
        assert result is None

    def test_roc_negative_capital_returns_none(self):
        """Should return None when capital employed is negative."""
        # Current Liabilities > Total Assets -> negative capital
        result = calculate_roc(
            ebit=100,
            total_assets=500,
            current_liabilities=800
        )
        assert result is None


class TestRankStocks:
    """Tests for rank_stocks function."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "symbol": ["A", "B", "C", "D", "E"],
            "earnings_yield": [0.10, 0.08, 0.12, 0.06, 0.09],
            "roc": [0.25, 0.30, 0.20, 0.35, 0.15],
        })

    def test_rank_stocks_adds_columns(self, sample_df):
        """Should add rank_ey, rank_roc, and magic_score columns."""
        result = rank_stocks(sample_df)

        assert "rank_ey" in result.columns
        assert "rank_roc" in result.columns
        assert "magic_score" in result.columns

    def test_rank_stocks_correct_ey_ranking(self, sample_df):
        """Should rank earnings yield correctly (highest = rank 1)."""
        result = rank_stocks(sample_df)

        # C has highest EY (0.12) -> rank 1
        c_row = result[result["symbol"] == "C"].iloc[0]
        assert c_row["rank_ey"] == 1

        # D has lowest EY (0.06) -> rank 5
        d_row = result[result["symbol"] == "D"].iloc[0]
        assert d_row["rank_ey"] == 5

    def test_rank_stocks_correct_roc_ranking(self, sample_df):
        """Should rank ROC correctly (highest = rank 1)."""
        result = rank_stocks(sample_df)

        # D has highest ROC (0.35) -> rank 1
        d_row = result[result["symbol"] == "D"].iloc[0]
        assert d_row["rank_roc"] == 1

        # E has lowest ROC (0.15) -> rank 5
        e_row = result[result["symbol"] == "E"].iloc[0]
        assert e_row["rank_roc"] == 5

    def test_rank_stocks_correct_magic_score(self, sample_df):
        """Should calculate magic score as sum of ranks."""
        result = rank_stocks(sample_df)

        for _, row in result.iterrows():
            assert row["magic_score"] == row["rank_ey"] + row["rank_roc"]

    def test_rank_stocks_sorted_by_magic_score(self, sample_df):
        """Should sort by magic_score ascending."""
        result = rank_stocks(sample_df)

        magic_scores = result["magic_score"].tolist()
        assert magic_scores == sorted(magic_scores)

    def test_rank_stocks_best_stock_first(self, sample_df):
        """Should have best stock (lowest magic score) first."""
        result = rank_stocks(sample_df)

        # Manual calculation:
        # A: EY=0.10 (rank 2), ROC=0.25 (rank 3) -> score 5
        # B: EY=0.08 (rank 4), ROC=0.30 (rank 2) -> score 6
        # C: EY=0.12 (rank 1), ROC=0.20 (rank 4) -> score 5
        # D: EY=0.06 (rank 5), ROC=0.35 (rank 1) -> score 6
        # E: EY=0.09 (rank 3), ROC=0.15 (rank 5) -> score 8

        # A or C should be first (both have score 5)
        first_symbol = result.iloc[0]["symbol"]
        assert first_symbol in ["A", "C"]

    def test_rank_stocks_handles_ties(self):
        """Should handle ties deterministically with method='first'."""
        df = pd.DataFrame({
            "symbol": ["X", "Y", "Z"],
            "earnings_yield": [0.10, 0.10, 0.08],  # X and Y tied
            "roc": [0.20, 0.20, 0.25],  # X and Y tied
        })

        result = rank_stocks(df)

        # With method='first', ties are broken by row order
        x_row = result[result["symbol"] == "X"].iloc[0]
        y_row = result[result["symbol"] == "Y"].iloc[0]

        # X should get rank 1, Y should get rank 2 (first appearance wins)
        assert x_row["rank_ey"] == 1
        assert y_row["rank_ey"] == 2

    def test_rank_stocks_preserves_original(self, sample_df):
        """Should not modify the original DataFrame."""
        original_columns = sample_df.columns.tolist()
        rank_stocks(sample_df)

        assert sample_df.columns.tolist() == original_columns
        assert "rank_ey" not in sample_df.columns


class TestGetTopPicks:
    """Tests for get_top_picks function."""

    @pytest.fixture
    def ranked_df(self):
        """Create a ranked DataFrame for testing."""
        df = pd.DataFrame({
            "symbol": ["A", "B", "C", "D", "E", "F", "G"],
            "earnings_yield": [0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06],
            "roc": [0.30, 0.28, 0.26, 0.24, 0.22, 0.20, 0.18],
        })
        return rank_stocks(df)

    def test_get_top_picks_default_n(self, ranked_df):
        """Should return 5 stocks by default."""
        result = get_top_picks(ranked_df)
        assert len(result) == 5

    def test_get_top_picks_custom_n(self, ranked_df):
        """Should return specified number of stocks."""
        result = get_top_picks(ranked_df, n=3)
        assert len(result) == 3

    def test_get_top_picks_returns_best_stocks(self, ranked_df):
        """Should return stocks with lowest magic scores."""
        result = get_top_picks(ranked_df, n=3)

        # The top stocks should have the lowest magic scores
        top_scores = result["magic_score"].tolist()
        all_scores = ranked_df["magic_score"].tolist()

        for score in top_scores:
            # Each top score should be among the lowest
            assert score <= sorted(all_scores)[2]  # n=3

    def test_get_top_picks_n_larger_than_df(self, ranked_df):
        """Should return all stocks if n > len(df)."""
        result = get_top_picks(ranked_df, n=100)
        assert len(result) == len(ranked_df)

    def test_get_top_picks_preserves_columns(self, ranked_df):
        """Should preserve all columns from input."""
        result = get_top_picks(ranked_df, n=3)

        for col in ranked_df.columns:
            assert col in result.columns

    def test_get_top_picks_returns_copy(self, ranked_df):
        """Should return a copy, not a view."""
        result = get_top_picks(ranked_df, n=3)
        result["new_col"] = 1

        assert "new_col" not in ranked_df.columns
