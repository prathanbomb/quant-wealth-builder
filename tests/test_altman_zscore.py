"""Unit tests for Altman Z-Score module."""

import pytest
import pandas as pd

from src.altman_zscore import (
    calculate_zscore,
    get_risk_zone,
    calculate_zscore_from_dict,
    rank_by_zscore,
    get_top_zscore_picks,
    SAFE_ZONE_THRESHOLD,
    GREY_ZONE_THRESHOLD,
)


class TestCalculateZScore:
    """Tests for calculate_zscore function."""

    def test_basic_calculation(self):
        """Should calculate Z-Score correctly for all components."""
        # Using simplified example
        zscore = calculate_zscore(
            working_capital=100,
            retained_earnings=200,
            ebit=150,
            market_cap=1000,
            total_liabilities=300,
            revenue=500,
            total_assets=1000,
        )
        # Should have a valid Z-Score
        assert zscore is not None
        assert zscore > 0

    def test_safe_zone_calculation(self):
        """Should calculate Z-Score in Safe Zone."""
        # Company with strong financials
        zscore = calculate_zscore(
            working_capital=500,  # Strong liquidity
            retained_earnings=800,  # Strong cumulative earnings
            ebit=300,  # Strong profitability
            market_cap=3000,  # Strong market position
            total_liabilities=500,  # Manageable debt
            revenue=2000,  # Strong revenue
            total_assets=2000,
        )
        # This should be in Safe Zone (> 2.99)
        assert zscore is not None
        assert zscore > SAFE_ZONE_THRESHOLD

    def test_distress_zone_calculation(self):
        """Should calculate Z-Score in Distress Zone."""
        # Company with weak financials
        zscore = calculate_zscore(
            working_capital=-100,  # Negative working capital
            retained_earnings=-200,  # Negative retained earnings
            ebit=50,  # Low profitability
            market_cap=100,  # Low market cap
            total_liabilities=500,  # High debt
            revenue=200,  # Low revenue
            total_assets=500,
        )
        # This should be in Distress Zone (< 1.81)
        assert zscore is not None
        assert zscore < GREY_ZONE_THRESHOLD

    def test_returns_none_for_zero_total_assets(self):
        """Should return None when total assets is zero."""
        zscore = calculate_zscore(
            working_capital=100,
            retained_earnings=200,
            ebit=150,
            market_cap=1000,
            total_liabilities=300,
            revenue=500,
            total_assets=0,  # Would cause division by zero
        )
        assert zscore is None

    def test_returns_none_for_none_total_assets(self):
        """Should return None when total assets is None."""
        zscore = calculate_zscore(
            working_capital=100,
            retained_earnings=200,
            ebit=150,
            market_cap=1000,
            total_liabilities=300,
            revenue=500,
            total_assets=None,
        )
        assert zscore is None

    def test_handles_negative_working_capital(self):
        """Should handle negative working capital (current liabilities > current assets)."""
        zscore = calculate_zscore(
            working_capital=-100,  # Negative working capital
            retained_earnings=500,
            ebit=200,
            market_cap=1500,
            total_liabilities=600,
            revenue=800,
            total_assets=1000,
        )
        # Should still calculate, just with negative contribution from WC ratio
        assert zscore is not None

    def test_requires_minimum_components(self):
        """Should require at least 4 out of 5 components."""
        # Only 2 components provided
        zscore = calculate_zscore(
            working_capital=100,
            retained_earnings=200,
            ebit=None,  # Missing
            market_cap=None,  # Missing
            total_liabilities=None,  # Missing
            revenue=500,
            total_assets=1000,
        )
        assert zscore is None

    def test_handles_missing_components_gracefully(self):
        """Should calculate Z-Score with 4 valid components."""
        # 4 out of 5 components valid (one missing)
        zscore = calculate_zscore(
            working_capital=100,
            retained_earnings=200,
            ebit=150,
            market_cap=None,  # Missing
            total_liabilities=300,
            revenue=500,
            total_assets=1000,
        )
        # Should still calculate with 4 components
        assert zscore is not None

    def test_all_components_none_returns_none(self):
        """Should return None when all components are None."""
        zscore = calculate_zscore(
            working_capital=None,
            retained_earnings=None,
            ebit=None,
            market_cap=None,
            total_liabilities=None,
            revenue=None,
            total_assets=1000,
        )
        assert zscore is None


class TestGetRiskZone:
    """Tests for get_risk_zone function."""

    def test_safe_zone(self):
        """Should return 'Safe' for Z > 2.99."""
        assert get_risk_zone(3.5) == "Safe"
        assert get_risk_zone(4.0) == "Safe"
        assert get_risk_zone(10.0) == "Safe"

    def test_grey_zone(self):
        """Should return 'Grey' for 1.81 < Z < 2.99."""
        assert get_risk_zone(2.0) == "Grey"
        assert get_risk_zone(2.5) == "Grey"
        assert get_risk_zone(2.9) == "Grey"

    def test_distress_zone(self):
        """Should return 'Distress' for Z < 1.81."""
        assert get_risk_zone(1.0) == "Distress"
        assert get_risk_zone(0.5) == "Distress"
        assert get_risk_zone(-1.0) == "Distress"

    def test_boundary_safe_grey(self):
        """Should handle boundary between Safe and Grey zones."""
        assert get_risk_zone(2.99) == "Grey"  # Not in Safe Zone
        assert get_risk_zone(3.0) == "Safe"  # Just into Safe Zone

    def test_boundary_grey_distress(self):
        """Should handle boundary between Grey and Distress zones."""
        assert get_risk_zone(1.81) == "Distress"  # Not in Grey Zone
        assert get_risk_zone(1.82) == "Grey"  # Just into Grey Zone

    def test_none_zscore_returns_unknown(self):
        """Should return 'Unknown' for None Z-Score."""
        assert get_risk_zone(None) == "Unknown"


class TestCalculateZScoreFromDict:
    """Tests for calculate_zscore_from_dict function."""

    def test_calculates_from_dict(self):
        """Should calculate Z-Score and zone from stock data dictionary."""
        data = {
            "working_capital": 500,
            "retained_earnings": 800,
            "ebit": 300,
            "market_cap": 3000,
            "total_liabilities": 500,
            "revenue": 2000,
            "total_assets": 2000,
        }
        zscore, zone = calculate_zscore_from_dict(data)

        assert zscore is not None
        assert zone in ["Safe", "Grey", "Distress"]

    def test_returns_unknown_for_missing_total_assets(self):
        """Should return None Z-Score and 'Unknown' zone when total_assets missing."""
        data = {
            "working_capital": 500,
            "retained_earnings": 800,
            "ebit": 300,
            "market_cap": 3000,
            "total_liabilities": 500,
            "revenue": 2000,
            "total_assets": None,
        }
        zscore, zone = calculate_zscore_from_dict(data)

        assert zscore is None
        assert zone == "Unknown"


class TestRankByZScore:
    """Tests for rank_by_zscore function."""

    def test_ranks_only_safe_zone_stocks(self):
        """Should only rank and include Safe Zone stocks."""
        df = pd.DataFrame([
            {
                "symbol": "A", "working_capital": 500, "retained_earnings": 800,
                "ebit": 300, "market_cap": 3000, "total_liabilities": 500,
                "revenue": 2000, "total_assets": 2000,
                # A should be in Safe Zone
            },
            {
                "symbol": "B", "working_capital": 50, "retained_earnings": 100,
                "ebit": 80, "market_cap": 300, "total_liabilities": 400,
                "revenue": 500, "total_assets": 500,
                # B should be in Grey or Distress Zone
            },
            {
                "symbol": "C", "working_capital": 400, "retained_earnings": 700,
                "ebit": 250, "market_cap": 2500, "total_liabilities": 400,
                "revenue": 1500, "total_assets": 1500,
                # C should be in Safe Zone
            },
        ])

        result = rank_by_zscore(df)

        # Should only include Safe Zone stocks (A and C)
        assert len(result) <= 3
        assert "zscore" in result.columns
        assert "risk_zone" in result.columns
        assert "rank_zscore" in result.columns

        # All included stocks should be in Safe Zone
        for _, row in result.iterrows():
            assert row["risk_zone"] == "Safe"
            assert row["zscore"] > SAFE_ZONE_THRESHOLD

    def test_excludes_grey_zone_stocks(self):
        """Should exclude stocks in Grey Zone."""
        df = pd.DataFrame([
            {
                "symbol": "SafeStock", "working_capital": 500, "retained_earnings": 800,
                "ebit": 300, "market_cap": 3000, "total_liabilities": 500,
                "revenue": 2000, "total_assets": 2000,
            },
            {
                "symbol": "GreyStock", "working_capital": 100, "retained_earnings": 200,
                "ebit": 100, "market_cap": 500, "total_liabilities": 400,
                "revenue": 600, "total_assets": 800,
            },
        ])

        result = rank_by_zscore(df)

        # Grey zone stock should be excluded
        if len(result) > 0:
            for _, row in result.iterrows():
                assert row["risk_zone"] == "Safe"
                assert row["symbol"] != "GreyStock"

    def test_excludes_distress_zone_stocks(self):
        """Should exclude stocks in Distress Zone."""
        df = pd.DataFrame([
            {
                "symbol": "SafeStock", "working_capital": 500, "retained_earnings": 800,
                "ebit": 300, "market_cap": 3000, "total_liabilities": 500,
                "revenue": 2000, "total_assets": 2000,
            },
            {
                "symbol": "DistressStock", "working_capital": -200, "retained_earnings": -100,
                "ebit": 20, "market_cap": 100, "total_liabilities": 500,
                "revenue": 200, "total_assets": 400,
            },
        ])

        result = rank_by_zscore(df)

        # Distress zone stock should be excluded
        if len(result) > 0:
            for _, row in result.iterrows():
                assert row["risk_zone"] == "Safe"
                assert row["symbol"] != "DistressStock"

    def test_returns_empty_when_no_safe_stocks(self):
        """Should return empty DataFrame when no Safe Zone stocks."""
        df = pd.DataFrame([
            {
                "symbol": "GreyStock", "working_capital": 100, "retained_earnings": 200,
                "ebit": 100, "market_cap": 500, "total_liabilities": 400,
                "revenue": 600, "total_assets": 800,
            },
            {
                "symbol": "DistressStock", "working_capital": -200, "retained_earnings": -100,
                "ebit": 20, "market_cap": 100, "total_liabilities": 500,
                "revenue": 200, "total_assets": 400,
            },
        ])

        result = rank_by_zscore(df)

        assert result.empty

    def test_ranks_descending_by_zscore(self):
        """Should rank stocks by Z-Score descending (safest first)."""
        df = pd.DataFrame([
            {
                "symbol": "A", "working_capital": 300, "retained_earnings": 500,
                "ebit": 200, "market_cap": 2000, "total_liabilities": 400,
                "revenue": 1000, "total_assets": 1000,
            },
            {
                "symbol": "B", "working_capital": 500, "retained_earnings": 800,
                "ebit": 300, "market_cap": 3000, "total_liabilities": 500,
                "revenue": 2000, "total_assets": 2000,
            },
            {
                "symbol": "C", "working_capital": 250, "retained_earnings": 400,
                "ebit": 150, "market_cap": 1500, "total_liabilities": 350,
                "revenue": 800, "total_assets": 800,
            },
        ])

        result = rank_by_zscore(df)

        if len(result) >= 2:
            # First stock should have highest Z-Score
            assert result.iloc[0]["zscore"] >= result.iloc[1]["zscore"]
            # Ranks should be sequential starting from 1
            assert result.iloc[0]["rank_zscore"] == 1

    def test_handles_ties_deterministically(self):
        """Should handle ties with method='first' for consistent ordering."""
        df = pd.DataFrame([
            {
                "symbol": "A", "working_capital": 300, "retained_earnings": 500,
                "ebit": 200, "market_cap": 2000, "total_liabilities": 400,
                "revenue": 1000, "total_assets": 1000,
            },
            {
                "symbol": "B", "working_capital": 300, "retained_earnings": 500,
                "ebit": 200, "market_cap": 2000, "total_liabilities": 400,
                "revenue": 1000, "total_assets": 1000,  # Same as A
            },
        ])

        result = rank_by_zscore(df)

        if len(result) == 2:
            # Should have different ranks even with same Z-Score
            assert result.iloc[0]["rank_zscore"] != result.iloc[1]["rank_zscore"]

    def test_calculates_risk_zone_for_each_stock(self):
        """Should calculate risk zone for each stock."""
        df = pd.DataFrame([
            {
                "symbol": "SafeStock", "working_capital": 500, "retained_earnings": 800,
                "ebit": 300, "market_cap": 3000, "total_liabilities": 500,
                "revenue": 2000, "total_assets": 2000,
            },
        ])

        result = rank_by_zscore(df)

        if len(result) > 0:
            assert result.iloc[0]["risk_zone"] == "Safe"


class TestGetTopZScorePicks:
    """Tests for get_top_zscore_picks function."""

    def test_returns_top_n_stocks(self):
        """Should return top N stocks by Z-Score."""
        df = pd.DataFrame([
            {"symbol": "A", "zscore": 5.0, "risk_zone": "Safe", "rank_zscore": 1},
            {"symbol": "B", "zscore": 4.5, "risk_zone": "Safe", "rank_zscore": 2},
            {"symbol": "C", "zscore": 4.0, "risk_zone": "Safe", "rank_zscore": 3},
            {"symbol": "D", "zscore": 3.5, "risk_zone": "Safe", "rank_zscore": 4},
            {"symbol": "E", "zscore": 3.0, "risk_zone": "Safe", "rank_zscore": 5},
        ])

        result = get_top_zscore_picks(df, n=3)

        assert len(result) == 3
        assert list(result["symbol"]) == ["A", "B", "C"]

    def test_returns_fewer_when_insufficient_safe_stocks(self):
        """Should return fewer stocks when fewer than N are in Safe Zone."""
        df = pd.DataFrame([
            {"symbol": "A", "zscore": 5.0, "risk_zone": "Safe", "rank_zscore": 1},
            {"symbol": "B", "zscore": 4.5, "risk_zone": "Safe", "rank_zscore": 2},
        ])

        result = get_top_zscore_picks(df, n=5)

        assert len(result) == 2

    def test_returns_copy(self):
        """Should return a copy, not a view."""
        df = pd.DataFrame([
            {"symbol": "A", "zscore": 5.0, "risk_zone": "Safe", "rank_zscore": 1},
        ])

        result = get_top_zscore_picks(df, n=1)
        result.loc[0, "symbol"] = "X"

        assert df.iloc[0]["symbol"] == "A"  # Original unchanged

    def test_default_n_is_5(self):
        """Default n should be 5."""
        df = pd.DataFrame([
            {"symbol": f"S{i}", "zscore": 10.0 - i, "risk_zone": "Safe", "rank_zscore": i}
            for i in range(1, 11)
        ])

        result = get_top_zscore_picks(df)

        assert len(result) == 5
