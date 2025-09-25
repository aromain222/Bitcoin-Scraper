#!/usr/bin/env python3
"""
Data Quality Dashboard for Financial Models
Provides comprehensive insights into data quality, reliability, and sources.

Features:
- Data quality scoring across all models
- Source reliability analysis
- Cross-validation metrics
- Performance tracking
- Risk assessment
- Visual reports and recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from financial_data_manager import FinancialDataManager
from data_models import ValuationMethod, ModelOutputs


class DataQualityDashboard:
    """Comprehensive dashboard for monitoring data quality across financial models."""

    def __init__(self):
        self.data_manager = FinancialDataManager()
        self.quality_history = []
        self.model_performance = {}
        self.source_reliability = {}

    def analyze_company_data_quality(self, ticker: str) -> Dict[str, Any]:
        """
        Perform comprehensive data quality analysis for a company.

        Args:
            ticker: Company ticker symbol

        Returns:
            Detailed quality analysis report
        """
        print(f"🔍 Analyzing data quality for {ticker}...")

        # Get company data
        company_data = self.data_manager.get_company_financials(ticker, years=5)

        if not company_data.company_name:
            return {'error': f'No data available for {ticker}'}

        # Analyze data completeness
        completeness_score = self._calculate_completeness_score(company_data)

        # Analyze data consistency
        consistency_score = self._calculate_consistency_score(company_data)

        # Analyze source quality
        source_analysis = self._analyze_source_quality(company_data)

        # Overall quality assessment
        overall_score = self._calculate_overall_quality_score(
            completeness_score, consistency_score, source_analysis
        )

        # Generate recommendations
        recommendations = self._generate_quality_recommendations(
            completeness_score, consistency_score, source_analysis
        )

        report = {
            'ticker': ticker,
            'company_name': company_data.company_name,
            'analysis_date': datetime.now(),
            'overall_quality_score': overall_score,
            'completeness_score': completeness_score,
            'consistency_score': consistency_score,
            'source_analysis': source_analysis,
            'recommendations': recommendations,
            'data_freshness_hours': company_data.data_quality.data_freshness_hours,
            'confidence_level': company_data.data_quality.confidence_level,
            'data_sources_used': company_data.data_quality.sources_used,
            'cross_validation_score': company_data.data_quality.cross_validation_score
        }

        # Store in history
        self.quality_history.append(report)

        return report

    def _calculate_completeness_score(self, company_data) -> float:
        """Calculate data completeness score (0-100)."""
        metrics_to_check = [
            ('revenue', company_data.revenue),
            ('ebitda', company_data.ebitda),
            ('net_income', company_data.net_income),
            ('total_assets', company_data.total_assets),
            ('total_debt', company_data.total_debt),
            ('operating_cash_flow', company_data.operating_cash_flow),
            ('market_cap', company_data.market_cap),
            ('beta', company_data.beta),
            ('pe_ratio', company_data.pe_ratio)
        ]

        available_metrics = 0
        total_metrics = len(metrics_to_check)

        for metric_name, metric_value in metrics_to_check:
            if metric_value is not None:
                if isinstance(metric_value, list):
                    if metric_value and any(v is not None and v != 0 for v in metric_value):
                        available_metrics += 1
                elif metric_value != 0:
                    available_metrics += 1

        completeness = (available_metrics / total_metrics) * 100

        # Bonus for having historical data (more than 1 year)
        historical_bonus = 0
        if company_data.revenue and len(company_data.revenue) > 1:
            historical_bonus += 10
        if company_data.ebitda and len(company_data.ebitda) > 1:
            historical_bonus += 10

        return min(100, completeness + historical_bonus)

    def _calculate_consistency_score(self, company_data) -> float:
        """Calculate data consistency score (0-100)."""
        consistency_checks = []

        # Check revenue vs EBITDA relationship
        if (company_data.revenue and company_data.ebitda and
            len(company_data.revenue) > 0 and len(company_data.ebitda) > 0):

            revenue = company_data.revenue[0]
            ebitda = company_data.ebitda[0]

            if revenue > 0:
                ebitda_margin = ebitda / revenue
                # EBITDA margin should typically be between -50% and 50%
                if -0.5 <= ebitda_margin <= 0.5:
                    consistency_checks.append(1)
                else:
                    consistency_checks.append(0.5)  # Partial credit for extreme but possible cases

        # Check debt vs equity relationship
        if (company_data.total_debt and company_data.total_assets and
            len(company_data.total_debt) > 0 and len(company_data.total_assets) > 0):

            debt = company_data.total_debt[0]
            assets = company_data.total_assets[0]

            if assets > 0:
                debt_ratio = debt / assets
                # Debt ratio should typically be between 0% and 90%
                if 0 <= debt_ratio <= 0.9:
                    consistency_checks.append(1)
                else:
                    consistency_checks.append(0.7)  # Some flexibility

        # Check ROE calculation
        if (company_data.net_income and company_data.roe and
            len(company_data.net_income) > 0):

            net_income = company_data.net_income[0]
            # Rough equity estimate
            equity_estimate = company_data.market_cap * 0.6 if company_data.market_cap else 0

            if equity_estimate > 0:
                calculated_roe = net_income / equity_estimate
                reported_roe = company_data.roe / 100  # Convert from percentage

                # Allow 20% tolerance
                if abs(calculated_roe - reported_roe) / abs(reported_roe) < 0.2:
                    consistency_checks.append(1)
                else:
                    consistency_checks.append(0.8)

        if not consistency_checks:
            return 50.0  # Neutral score if no checks possible

        return (sum(consistency_checks) / len(consistency_checks)) * 100

    def _analyze_source_quality(self, company_data) -> Dict[str, Any]:
        """Analyze quality of data sources used."""
        sources = company_data.data_quality.sources_used
        source_scores = {
            'alpha_vantage': 95,
            'finnhub': 90,
            'yahoo_finance': 80,
            'sec_edgar': 98
        }

        if not sources:
            return {
                'sources_used': [],
                'average_source_score': 0,
                'best_source': None,
                'source_diversity_score': 0
            }

        # Calculate average source quality
        source_qualities = [source_scores.get(source.lower().replace(' ', '_'), 70) for source in sources]
        avg_source_score = sum(source_qualities) / len(source_qualities)

        # Find best source
        best_source = sources[source_qualities.index(max(source_qualities))]

        # Source diversity bonus
        diversity_score = min(20, len(sources) * 5)  # Max 20 points for using 4+ sources

        return {
            'sources_used': sources,
            'average_source_score': avg_source_score,
            'best_source': best_source,
            'source_diversity_score': diversity_score,
            'total_sources': len(sources)
        }

    def _calculate_overall_quality_score(self, completeness: float,
                                       consistency: float,
                                       source_analysis: Dict) -> float:
        """Calculate overall quality score using weighted components."""
        weights = {
            'completeness': 0.4,
            'consistency': 0.3,
            'source_quality': 0.2,
            'source_diversity': 0.1
        }

        source_quality = source_analysis.get('average_source_score', 0)
        source_diversity = source_analysis.get('source_diversity_score', 0)

        overall_score = (
            completeness * weights['completeness'] +
            consistency * weights['consistency'] +
            source_quality * weights['source_quality'] +
            source_diversity * weights['source_diversity']
        )

        return round(overall_score, 1)

    def _generate_quality_recommendations(self, completeness: float,
                                        consistency: float,
                                        source_analysis: Dict) -> List[str]:
        """Generate actionable recommendations for improving data quality."""
        recommendations = []

        # Completeness recommendations
        if completeness < 70:
            recommendations.append("Consider using additional data sources to fill gaps")
            if len(source_analysis.get('sources_used', [])) < 2:
                recommendations.append("Add more data sources for better completeness")

        # Consistency recommendations
        if consistency < 80:
            recommendations.append("Review financial relationships for potential data inconsistencies")
            recommendations.append("Cross-validate key ratios with industry benchmarks")

        # Source recommendations
        sources_used = source_analysis.get('sources_used', [])
        if 'alpha_vantage' not in [s.lower().replace(' ', '_') for s in sources_used]:
            recommendations.append("Consider adding Alpha Vantage for higher quality data")

        if len(sources_used) < 2:
            recommendations.append("Use multiple data sources for better validation")

        # General recommendations
        if completeness > 90 and consistency > 90:
            recommendations.append("Excellent data quality - proceed with confidence")

        return recommendations

    def generate_quality_report(self, tickers: List[str]) -> str:
        """Generate a comprehensive quality report for multiple companies."""
        print(f"📊 Generating quality report for {len(tickers)} companies...")

        reports = []
        for ticker in tickers:
            try:
                report = self.analyze_company_data_quality(ticker)
                if 'error' not in report:
                    reports.append(report)
            except Exception as e:
                print(f"   ⚠️ Error analyzing {ticker}: {e}")

        if not reports:
            return "No valid reports generated"

        # Create summary statistics
        avg_quality = sum(r['overall_quality_score'] for r in reports) / len(reports)
        avg_completeness = sum(r['completeness_score'] for r in reports) / len(reports)
        avg_consistency = sum(r['consistency_score'] for r in reports) / len(reports)

        # Find best and worst performers
        best_company = max(reports, key=lambda x: x['overall_quality_score'])
        worst_company = min(reports, key=lambda x: x['overall_quality_score'])

        report_text = f"""
DATA QUALITY DASHBOARD REPORT
{'='*50}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Companies Analyzed: {len(reports)}

OVERALL STATISTICS:
  Average Quality Score: {avg_quality:.1f}/100
  Average Completeness: {avg_completeness:.1f}/100
  Average Consistency: {avg_consistency:.1f}/100

BEST PERFORMER:
  {best_company['company_name']} ({best_company['ticker']})
  Quality Score: {best_company['overall_quality_score']}/100
  Sources: {', '.join(best_company['data_sources_used'])}

WORST PERFORMER:
  {worst_company['company_name']} ({worst_company['ticker']})
  Quality Score: {worst_company['overall_quality_score']}/100
  Sources: {', '.join(worst_company['data_sources_used'])}

COMPANY DETAILS:
"""

        for report in sorted(reports, key=lambda x: x['overall_quality_score'], reverse=True):
            report_text += ".1f"".1f"".1f"".1f"f"""
{best_company['company_name']} ({best_company['ticker']}): {best_company['overall_quality_score']}/100
  Completeness: {best_company['completeness_score']:.1f}%
  Consistency: {best_company['consistency_score']:.1f}%
  Sources: {', '.join(best_company['data_sources_used'])}
  Freshness: {best_company['data_freshness_hours']:.1f} hours
  Confidence: {best_company['confidence_level']}
  Key Issues:
"""

            for rec in report['recommendations'][:2]:  # Show top 2 recommendations
                report_text += f"    • {rec}\n"

        return report_text

    def create_quality_visualization(self, tickers: List[str], save_path: str = None):
        """Create visual representation of data quality metrics."""
        print("📊 Creating quality visualization...")

        # Collect data
        quality_data = []
        for ticker in tickers:
            try:
                report = self.analyze_company_data_quality(ticker)
                if 'error' not in report:
                    quality_data.append({
                        'ticker': ticker,
                        'company': report['company_name'][:15],  # Truncate long names
                        'quality_score': report['overall_quality_score'],
                        'completeness': report['completeness_score'],
                        'consistency': report['consistency_score'],
                        'sources': len(report['data_sources_used'])
                    })
            except:
                continue

        if not quality_data:
            print("❌ No data available for visualization")
            return

        df = pd.DataFrame(quality_data)

        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Financial Data Quality Dashboard', fontsize=16, fontweight='bold')

        # Quality Score Distribution
        axes[0, 0].bar(df['company'], df['quality_score'], color='skyblue')
        axes[0, 0].set_title('Overall Quality Score by Company')
        axes[0, 0].set_ylabel('Score (0-100)')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Completeness vs Consistency
        scatter = axes[0, 1].scatter(df['completeness'], df['consistency'],
                                   s=df['quality_score']*2, c=df['sources'],
                                   cmap='viridis', alpha=0.7)
        axes[0, 1].set_xlabel('Completeness Score (%)')
        axes[0, 1].set_ylabel('Consistency Score (%)')
        axes[0, 1].set_title('Completeness vs Consistency')
        axes[0, 1].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[0, 1], label='Number of Sources')

        # Quality Components Breakdown
        components = ['quality_score', 'completeness', 'consistency']
        component_names = ['Overall', 'Completeness', 'Consistency']
        x = np.arange(len(df))
        width = 0.25

        for i, (component, name) in enumerate(zip(components, component_names)):
            axes[1, 0].bar(x + i*width, df[component], width,
                          label=name, alpha=0.8)

        axes[1, 0].set_xlabel('Company')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Quality Components Comparison')
        axes[1, 0].set_xticks(x + width)
        axes[1, 0].set_xticklabels(df['company'], rotation=45)
        axes[1, 0].legend()

        # Sources Used
        axes[1, 1].bar(df['company'], df['sources'], color='lightgreen')
        axes[1, 1].set_title('Data Sources Used by Company')
        axes[1, 1].set_ylabel('Number of Sources')
        axes[1, 1].tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   ✅ Visualization saved to {save_path}")
        else:
            plt.show()

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get summary of model performance based on data quality."""
        if not self.quality_history:
            return {'error': 'No quality data available'}

        # Analyze quality trends
        quality_scores = [r['overall_quality_score'] for r in self.quality_history]
        completeness_scores = [r['completeness_score'] for r in self.quality_history]

        return {
            'total_companies_analyzed': len(self.quality_history),
            'average_quality_score': sum(quality_scores) / len(quality_scores),
            'average_completeness': sum(completeness_scores) / len(completeness_scores),
            'quality_distribution': {
                'excellent': len([s for s in quality_scores if s >= 90]),
                'good': len([s for s in quality_scores if 80 <= s < 90]),
                'fair': len([s for s in quality_scores if 70 <= s < 80]),
                'poor': len([s for s in quality_scores if s < 70])
            },
            'most_common_sources': self._get_most_common_sources(),
            'data_freshness_avg': sum(r['data_freshness_hours'] for r in self.quality_history) / len(self.quality_history)
        }

    def _get_most_common_sources(self) -> List[str]:
        """Get most commonly used data sources."""
        all_sources = []
        for report in self.quality_history:
            all_sources.extend(report['data_sources_used'])

        if not all_sources:
            return []

        source_counts = {}
        for source in all_sources:
            source_counts[source] = source_counts.get(source, 0) + 1

        return sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]


def main():
    """Demonstrate the data quality dashboard."""
    print("📊 Data Quality Dashboard Demo")
    print("=" * 40)

    dashboard = DataQualityDashboard()

    # Example companies to analyze
    companies = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Generate quality report
    print("\n📋 Generating Quality Report...")
    report = dashboard.generate_quality_report(companies)
    print(report)

    # Create visualization
    print("\n📊 Creating Quality Visualization...")
    try:
        dashboard.create_quality_visualization(companies, 'data_quality_dashboard.png')
    except ImportError:
        print("   ⚠️ Matplotlib not available for visualization")
    except Exception as e:
        print(f"   ⚠️ Visualization error: {e}")

    # Show performance summary
    print("\n📈 Performance Summary:")
    summary = dashboard.get_model_performance_summary()
    if 'error' not in summary:
        print(f"   Companies Analyzed: {summary['total_companies_analyzed']}")
        print(".1f")
        print(".1f")
        print(f"   Data Freshness: {summary['data_freshness_avg']:.1f} hours average")
        print(f"   Quality Distribution: {summary['quality_distribution']}")
        print(f"   Most Common Sources: {[s[0] for s in summary['most_common_sources']]}")

    print("\n✅ Dashboard demo complete!")
    print("\n💡 Use Cases:")
    print("   • Monitor data quality across your portfolio")
    print("   • Identify companies with poor data quality")
    print("   • Compare data sources effectiveness")
    print("   • Generate reports for stakeholders")


if __name__ == "__main__":
    main()
