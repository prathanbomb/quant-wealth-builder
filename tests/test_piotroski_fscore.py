"""Unit tests for Piotroski F-Score module."""

import pytest
import pandas as pd

from src.piotroski_fscore import (
    calculate_fscore,
    calculate_fscore_from_dict,
    rank_by_fscore,
    get_top_fscore_picks,
    _score_positive_roa,
    _score_positive_cfo,
    _score_roa_improvement,
    _score_accruals,
    _score_decreased_leverage,
    _score_improved_liquidity,
    _score_no_dilution,
    _score_improved_margin,
    _score_improved_turnover,
)


class TestScorePositiveROA:
    """Tests for _score_positive_roa function."""

    def test_positive_roa_scores_1(self):
        """Positive ROA should score 1."""
        assert _score_positive_roa(100, 1000) == 1  # 10% ROA

    def test_negative_roa_scores_0(self):
        """Negative ROA should score 0."""
        assert _score_positive_roa(-100, 1000) == 0

    def test_zero_roa_scores_0(self):
        """Zero ROA should score 0."""
        assert _score_positive_roa(0, 1000) == 0

    def test_none_net_income_scores_0(self):
        """None net income should score 0."""
        assert _score_positive_roa(None, 1000) == 0

    def test_none_total_assets_scores_0(self):
        """None total assets should score 0."""
        assert _score_positive_roa(100, None) == 0

    def test_zero_total_assets_scores_0(self):
        """Zero total assets should score 0."""
        assert _score_positive_roa(100, 0) == 0


class TestScorePositiveCFO:
    """Tests for _score_positive_cfo function."""

    def test_positive_cfo_scores_1(self):
        """Positive operating cash flow should score 1."""
        assert _score_positive_cfo(100) == 1

    def test_negative_cfo_scores_0(self):
        """Negative operating cash flow should score 0."""
        assert _score_positive_cfo(-100) == 0

    def test_zero_cfo_scores_0(self):
        """Zero operating cash flow should score 0."""
        assert _score_positive_cfo(0) == 0

    def test_none_cfo_scores_0(self):
        """None operating cash flow should score 0."""
        assert _score_positive_cfo(None) == 0


class TestScoreROAImprovement:
    """Tests for _score_roa_improvement function."""

    def test_improved_roa_scores_1(self):
        """Improved ROA should score 1."""
        assert _score_roa_improvement(0.12, 0.10) == 1

    def test_decreased_roa_scores_0(self):
        """Decreased ROA should score 0."""
        assert _score_roa_improvement(0.08, 0.10) == 0

    def test_unchanged_roa_scores_0(self):
        """Unchanged ROA should score 0."""
        assert _score_roa_improvement(0.10, 0.10) == 0

    def test_none_current_roa_scores_0(self):
        """None current ROA should score 0."""
        assert _score_roa_improvement(None, 0.10) == 0

    def test_none_previous_roa_scores_0(self):
        """None previous ROA should score 0."""
        assert _score_roa_improvement(0.10, None) == 0


class TestScoreAccruals:
    """Tests for _score_accruals function."""

    def test_cfo_greater_than_income_scores_1(self):
        """CFO > Net Income should score 1."""
        assert _score_accruals(150, 100) == 1

    def test_cfo_less_than_income_scores_0(self):
        """CFO < Net Income should score 0."""
        assert _score_accruals(80, 100) == 0

    def test_cfo_equal_to_income_scores_0(self):
        """CFO = Net Income should score 0."""
        assert _score_accruals(100, 100) == 0

    def test_none_cfo_scores_0(self):
        """None CFO should score 0."""
        assert _score_accruals(None, 100) == 0

    def test_none_net_income_scores_0(self):
        """None net income should score 0."""
        assert _score_accruals(100, None) == 0


class TestScoreDecreasedLeverage:
    """Tests for _score_decreased_leverage function."""

    def test_decreased_leverage_scores_1(self):
        """Decreased leverage ratio should score 1."""
        # Current: 200/1000 = 20%, Previous: 300/1000 = 30%
        assert _score_decreased_leverage(200, 300, 1000, 1000) == 1

    def test_increased_leverage_scores_0(self):
        """Increased leverage ratio should score 0."""
        # Current: 400/1000 = 40%, Previous: 300/1000 = 30%
        assert _score_decreased_leverage(400, 300, 1000, 1000) == 0

    def test_unchanged_leverage_scores_0(self):
        """Unchanged leverage ratio should score 0."""
        assert _score_decreased_leverage(300, 300, 1000, 1000) == 0

    def test_none_debt_treated_as_zero(self):
        """None debt should be treated as zero debt."""
        # Current: 0/1000 = 0%, Previous: 100/1000 = 10% -> decreased
        assert _score_decreased_leverage(None, 100, 1000, 1000) == 1

    def test_none_total_assets_scores_0(self):
        """None total assets should score 0."""
        assert _score_decreased_leverage(200, 300, None, 1000) == 0

    def test_none_prev_total_assets_scores_0(self):
        """None previous total assets should score 0."""
        assert _score_decreased_leverage(200, 300, 1000, None) == 0

    def test_zero_total_assets_scores_0(self):
        """Zero total assets should score 0."""
        assert _score_decreased_leverage(200, 300, 0, 1000) == 0


class TestScoreImprovedLiquidity:
    """Tests for _score_improved_liquidity function."""

    def test_improved_liquidity_scores_1(self):
        """Improved current ratio should score 1."""
        assert _score_improved_liquidity(2.0, 1.5) == 1

    def test_decreased_liquidity_scores_0(self):
        """Decreased current ratio should score 0."""
        assert _score_improved_liquidity(1.2, 1.5) == 0

    def test_unchanged_liquidity_scores_0(self):
        """Unchanged current ratio should score 0."""
        assert _score_improved_liquidity(1.5, 1.5) == 0

    def test_none_current_ratio_scores_0(self):
        """None current ratio should score 0."""
        assert _score_improved_liquidity(None, 1.5) == 0

    def test_none_prev_current_ratio_scores_0(self):
        """None previous current ratio should score 0."""
        assert _score_improved_liquidity(1.5, None) == 0


class TestScoreNoDilution:
    """Tests for _score_no_dilution function."""

    def test_no_dilution_scores_1(self):
        """No increase in shares should score 1."""
        assert _score_no_dilution(1000, 1000) == 1

    def test_decreased_shares_scores_1(self):
        """Decreased shares (buyback) should score 1."""
        assert _score_no_dilution(900, 1000) == 1

    def test_increased_shares_scores_0(self):
        """Increased shares (dilution) should score 0."""
        assert _score_no_dilution(1100, 1000) == 0

    def test_none_current_shares_scores_0(self):
        """None current shares should score 0."""
        assert _score_no_dilution(None, 1000) == 0

    def test_none_prev_shares_gives_benefit_of_doubt(self):
        """None previous shares should give benefit of doubt (score 1)."""
        assert _score_no_dilution(1000, None) == 1


class TestScoreImprovedMargin:
    """Tests for _score_improved_margin function."""

    def test_improved_margin_scores_1(self):
        """Improved gross margin should score 1."""
        assert _score_improved_margin(0.35, 0.30) == 1

    def test_decreased_margin_scores_0(self):
        """Decreased gross margin should score 0."""
        assert _score_improved_margin(0.25, 0.30) == 0

    def test_unchanged_margin_scores_0(self):
        """Unchanged gross margin should score 0."""
        assert _score_improved_margin(0.30, 0.30) == 0

    def test_none_current_margin_scores_0(self):
        """None current margin should score 0."""
        assert _score_improved_margin(None, 0.30) == 0

    def test_none_prev_margin_scores_0(self):
        """None previous margin should score 0."""
        assert _score_improved_margin(0.30, None) == 0


class TestScoreImprovedTurnover:
    """Tests for _score_improved_turnover function."""

    def test_improved_turnover_scores_1(self):
        """Improved asset turnover should score 1."""
        assert _score_improved_turnover(1.5, 1.2) == 1

    def test_decreased_turnover_scores_0(self):
        """Decreased asset turnover should score 0."""
        assert _score_improved_turnover(1.0, 1.2) == 0

    def test_unchanged_turnover_scores_0(self):
        """Unchanged asset turnover should score 0."""
        assert _score_improved_turnover(1.2, 1.2) == 0

    def test_none_current_turnover_scores_0(self):
        """None current turnover should score 0."""
        assert _score_improved_turnover(None, 1.2) == 0

    def test_none_prev_turnover_scores_0(self):
        """None previous turnover should score 0."""
        assert _score_improved_turnover(1.2, None) == 0


class TestCalculateFScore:
    """Tests for calculate_fscore function."""

    def test_perfect_score_9(self):
        """Company with all positive signals should score 9."""
        score = calculate_fscore(
            net_income=100,
            total_assets=1000,
            operating_cash_flow=150,  # > net_income
            roa=0.12,
            roa_prev=0.10,  # improved
            long_term_debt=200,
            long_term_debt_prev=300,  # decreased
            total_assets_prev=1000,
            current_ratio=2.0,
            current_ratio_prev=1.5,  # improved
            shares_outstanding=1000,
            shares_outstanding_prev=1000,  # no dilution
            gross_margin=0.35,
            gross_margin_prev=0.30,  # improved
            asset_turnover=1.5,
            asset_turnover_prev=1.2,  # improved
        )
        assert score == 9

    def test_zero_score(self):
        """Company with all negative signals should score 0."""
        score = calculate_fscore(
            net_income=-100,  # negative ROA
            total_assets=1000,
            operating_cash_flow=-150,  # negative CFO, and < net_income (accruals fail)
            roa=-0.08,
            roa_prev=-0.05,  # worsened
            long_term_debt=400,
            long_term_debt_prev=300,  # increased
            total_assets_prev=1000,
            current_ratio=1.2,
            current_ratio_prev=1.5,  # decreased
            shares_outstanding=1100,
            shares_outstanding_prev=1000,  # dilution
            gross_margin=0.25,
            gross_margin_prev=0.30,  # decreased
            asset_turnover=1.0,
            asset_turnover_prev=1.2,  # decreased
        )
        assert score == 0

    def test_partial_score(self):
        """Company with mixed signals should score appropriately."""
        score = calculate_fscore(
            net_income=100,  # +1 positive ROA
            total_assets=1000,
            operating_cash_flow=150,  # +1 positive CFO, +1 > net_income
            roa=0.10,
            roa_prev=0.10,  # 0 unchanged
            long_term_debt=300,
            long_term_debt_prev=300,  # 0 unchanged
            total_assets_prev=1000,
            current_ratio=1.5,
            current_ratio_prev=1.5,  # 0 unchanged
            shares_outstanding=1000,
            shares_outstanding_prev=1000,  # +1 no dilution
            gross_margin=0.30,
            gross_margin_prev=0.30,  # 0 unchanged
            asset_turnover=1.2,
            asset_turnover_prev=1.2,  # 0 unchanged
        )
        assert score == 4

    def test_returns_none_when_no_basic_data(self):
        """Should return None when missing basic data."""
        assert calculate_fscore(
            net_income=None,
            total_assets=1000,
            operating_cash_flow=None,
            roa=None,
            roa_prev=None,
            long_term_debt=None,
            long_term_debt_prev=None,
            total_assets_prev=None,
            current_ratio=None,
            current_ratio_prev=None,
            shares_outstanding=None,
            shares_outstanding_prev=None,
            gross_margin=None,
            gross_margin_prev=None,
            asset_turnover=None,
            asset_turnover_prev=None,
        ) is None

    def test_returns_none_when_no_total_assets(self):
        """Should return None when total assets is None."""
        assert calculate_fscore(
            net_income=100,
            total_assets=None,
            operating_cash_flow=100,
            roa=0.10,
            roa_prev=0.08,
            long_term_debt=200,
            long_term_debt_prev=200,
            total_assets_prev=1000,
            current_ratio=1.5,
            current_ratio_prev=1.5,
            shares_outstanding=1000,
            shares_outstanding_prev=1000,
            gross_margin=0.30,
            gross_margin_prev=0.30,
            asset_turnover=1.2,
            asset_turnover_prev=1.2,
        ) is None


class TestCalculateFScoreFromDict:
    """Tests for calculate_fscore_from_dict function."""

    def test_calculates_from_dict(self):
        """Should calculate F-Score from stock data dictionary."""
        data = {
            "net_income": 100,
            "total_assets": 1000,
            "operating_cash_flow": 150,
            "roa": 0.12,
            "roa_prev": 0.10,
            "long_term_debt": 200,
            "long_term_debt_prev": 300,
            "total_assets_prev": 1000,
            "current_ratio": 2.0,
            "current_ratio_prev": 1.5,
            "shares_outstanding": 1000,
            "shares_outstanding_prev": 1000,
            "gross_margin": 0.35,
            "gross_margin_prev": 0.30,
            "asset_turnover": 1.5,
            "asset_turnover_prev": 1.2,
        }
        assert calculate_fscore_from_dict(data) == 9

    def test_handles_missing_keys(self):
        """Should handle missing dictionary keys gracefully."""
        data = {"total_assets": 1000}
        result = calculate_fscore_from_dict(data)
        assert result is None


class TestRankByFScore:
    """Tests for rank_by_fscore function."""

    def test_ranks_stocks_by_fscore(self):
        """Should rank stocks by F-Score descending."""
        df = pd.DataFrame([
            {"symbol": "A", "net_income": 100, "total_assets": 1000,
             "operating_cash_flow": 150, "roa": 0.12, "roa_prev": 0.10,
             "long_term_debt": 200, "long_term_debt_prev": 300, "total_assets_prev": 1000,
             "current_ratio": 2.0, "current_ratio_prev": 1.5, "shares_outstanding": 1000,
             "shares_outstanding_prev": 1000, "gross_margin": 0.35, "gross_margin_prev": 0.30,
             "asset_turnover": 1.5, "asset_turnover_prev": 1.2},  # Score: 9
            {"symbol": "B", "net_income": -100, "total_assets": 1000,
             "operating_cash_flow": -150, "roa": -0.08, "roa_prev": -0.05,
             "long_term_debt": 400, "long_term_debt_prev": 300, "total_assets_prev": 1000,
             "current_ratio": 1.2, "current_ratio_prev": 1.5, "shares_outstanding": 1100,
             "shares_outstanding_prev": 1000, "gross_margin": 0.25, "gross_margin_prev": 0.30,
             "asset_turnover": 1.0, "asset_turnover_prev": 1.2},  # Score: 0
        ])

        result = rank_by_fscore(df)

        assert len(result) == 2
        assert "fscore" in result.columns
        assert "rank_fscore" in result.columns
        assert result.iloc[0]["symbol"] == "A"  # Best stock first
        assert result.iloc[0]["fscore"] == 9
        assert result.iloc[0]["rank_fscore"] == 1
        assert result.iloc[1]["symbol"] == "B"
        assert result.iloc[1]["fscore"] == 0
        assert result.iloc[1]["rank_fscore"] == 2

    def test_excludes_stocks_without_valid_fscore(self):
        """Should exclude stocks with None F-Score."""
        df = pd.DataFrame([
            {"symbol": "A", "net_income": 100, "total_assets": 1000,
             "operating_cash_flow": 150, "roa": 0.10, "roa_prev": 0.08,
             "long_term_debt": None, "long_term_debt_prev": None, "total_assets_prev": 1000,
             "current_ratio": 1.5, "current_ratio_prev": 1.5, "shares_outstanding": None,
             "shares_outstanding_prev": None, "gross_margin": 0.30, "gross_margin_prev": 0.30,
             "asset_turnover": 1.2, "asset_turnover_prev": 1.2},  # Valid
            {"symbol": "B", "net_income": None, "total_assets": None,
             "operating_cash_flow": None, "roa": None, "roa_prev": None,
             "long_term_debt": None, "long_term_debt_prev": None, "total_assets_prev": None,
             "current_ratio": None, "current_ratio_prev": None, "shares_outstanding": None,
             "shares_outstanding_prev": None, "gross_margin": None, "gross_margin_prev": None,
             "asset_turnover": None, "asset_turnover_prev": None},  # Invalid - no data
        ])

        result = rank_by_fscore(df)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_handles_ties_deterministically(self):
        """Should handle ties with method='first' for consistent ordering."""
        df = pd.DataFrame([
            {"symbol": "A", "net_income": 100, "total_assets": 1000,
             "operating_cash_flow": 50, "roa": 0.10, "roa_prev": 0.10,
             "long_term_debt": 200, "long_term_debt_prev": 200, "total_assets_prev": 1000,
             "current_ratio": 1.5, "current_ratio_prev": 1.5, "shares_outstanding": 1000,
             "shares_outstanding_prev": 1000, "gross_margin": 0.30, "gross_margin_prev": 0.30,
             "asset_turnover": 1.2, "asset_turnover_prev": 1.2},  # Score: 2
            {"symbol": "B", "net_income": 100, "total_assets": 1000,
             "operating_cash_flow": 50, "roa": 0.10, "roa_prev": 0.10,
             "long_term_debt": 200, "long_term_debt_prev": 200, "total_assets_prev": 1000,
             "current_ratio": 1.5, "current_ratio_prev": 1.5, "shares_outstanding": 1000,
             "shares_outstanding_prev": 1000, "gross_margin": 0.30, "gross_margin_prev": 0.30,
             "asset_turnover": 1.2, "asset_turnover_prev": 1.2},  # Score: 2
        ])

        result = rank_by_fscore(df)

        assert len(result) == 2
        assert result.iloc[0]["fscore"] == result.iloc[1]["fscore"]
        # Ranks should be different even for ties
        assert result.iloc[0]["rank_fscore"] != result.iloc[1]["rank_fscore"]

    def test_returns_empty_dataframe_when_no_valid_scores(self):
        """Should return empty DataFrame when no valid F-Scores."""
        df = pd.DataFrame([
            {"symbol": "A", "net_income": None, "total_assets": None,
             "operating_cash_flow": None, "roa": None, "roa_prev": None,
             "long_term_debt": None, "long_term_debt_prev": None, "total_assets_prev": None,
             "current_ratio": None, "current_ratio_prev": None, "shares_outstanding": None,
             "shares_outstanding_prev": None, "gross_margin": None, "gross_margin_prev": None,
             "asset_turnover": None, "asset_turnover_prev": None},
        ])

        result = rank_by_fscore(df)

        assert result.empty


class TestGetTopFScorePicks:
    """Tests for get_top_fscore_picks function."""

    def test_returns_top_n_stocks(self):
        """Should return top N stocks."""
        df = pd.DataFrame([
            {"symbol": "A", "fscore": 9, "rank_fscore": 1},
            {"symbol": "B", "fscore": 7, "rank_fscore": 2},
            {"symbol": "C", "fscore": 5, "rank_fscore": 3},
            {"symbol": "D", "fscore": 3, "rank_fscore": 4},
            {"symbol": "E", "fscore": 1, "rank_fscore": 5},
        ])

        result = get_top_fscore_picks(df, n=3)

        assert len(result) == 3
        assert list(result["symbol"]) == ["A", "B", "C"]

    def test_returns_all_when_n_exceeds_length(self):
        """Should return all stocks when n exceeds DataFrame length."""
        df = pd.DataFrame([
            {"symbol": "A", "fscore": 9, "rank_fscore": 1},
            {"symbol": "B", "fscore": 7, "rank_fscore": 2},
        ])

        result = get_top_fscore_picks(df, n=10)

        assert len(result) == 2

    def test_returns_copy(self):
        """Should return a copy, not a view."""
        df = pd.DataFrame([
            {"symbol": "A", "fscore": 9, "rank_fscore": 1},
        ])

        result = get_top_fscore_picks(df, n=1)
        result.loc[0, "symbol"] = "X"

        assert df.iloc[0]["symbol"] == "A"  # Original unchanged

    def test_default_n_is_5(self):
        """Default n should be 5."""
        df = pd.DataFrame([
            {"symbol": f"S{i}", "fscore": 9 - i, "rank_fscore": i + 1}
            for i in range(10)
        ])

        result = get_top_fscore_picks(df)

        assert len(result) == 5
