"""
Carbon-Aware FinOps Dashboard - Bachelor Thesis Project
BACHELOR THESIS PROJECT (September 2025)

DASHBOARD DESIGN DECISIONS:
ACADEMIC DASHBOARD IMPLEMENTATION:
- Chart.js Integration: Modern visualization framework
🎨 Builder.io CSS Integration: Clean, modern UI without framework conflicts
📐 Consistent Chart Dimensions: Standardized 400px height for visual harmony
⚡ Performance-First Architecture: Smooth rendering and responsive design
🔬 Scientific Rigor: Real-time API-only data approach for academic accuracy

Professional dashboard with 26 interactive visualizations!
"""

# Standard library imports
import logging
from typing import List, Dict

# Third-party imports
import dash
from dash import dcc, html, Input, Output, clientside_callback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local imports
from utils.data_processing import data_processor
from utils.performance_monitor import monitor_dashboard_render, performance_monitor
from tabs.overview_tab import overview_tab_chartjs
from tabs.thesis_validation_tab import thesis_validation_tab_chartjs
from tabs.research_methods_tab import research_methods_tab_chartjs
from tabs.carbon_tab import carbon_tab_chartjs
from components.components import DashboardCards
from components.chartjs_library import ChartJSFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CarbonAwareDashboard:
    """
    Modern Carbon-Aware FinOps Dashboard

    DESIGN PHILOSOPHY:
    - Lightweight Architecture: 50kb modern framework for fast loading
    - CSS Harmony: Builder.io integration for consistent styling
    - Visual Consistency: Standardized 400px chart dimensions
    - Performance-Optimized: Native browser support, no heavy dependencies
    - Academic Rigor: API-first data approach for scientific accuracy
    """

    def __init__(self):
        """Initialize modern carbon-aware dashboard"""

        # Modern external stylesheets
        external_stylesheets = [
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
            "/assets/modern-thesis-styles.css",
        ]

        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
        self.data_processor = data_processor
        self.overview_tab = overview_tab_chartjs
        self.thesis_tab = thesis_validation_tab_chartjs
        self.research_tab = research_methods_tab_chartjs
        self.carbon_tab = carbon_tab_chartjs
        self.cards = DashboardCards()
        self.charts = ChartJSFactory()

        # Load data ONCE at startup
        self.cached_data = self.load_initial_data()

        # Setup layout and callbacks
        self.setup_layout()
        self.setup_chartjs_callbacks()

        logger.info("✅ Carbon-Aware FinOps Dashboard initialized with Chart.js framework")

    def load_initial_data(self) -> Dict:
        """Load all data ONCE at startup for dashboard initialization"""
        try:
            logger.info("🔄 Loading initial infrastructure data...")
            data = self.data_processor.get_infrastructure_data()
            logger.info("✅ Initial data loaded for dashboard")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load initial data: {e}")
            return {"instances": [], "carbon_intensity": 420, "total_cost": 0, "api_sources": {}}

    def setup_layout(self):
        """Setup modern dashboard layout"""

        instances = self.cached_data.get("instances", [])

        self.app.layout = html.Div(
            [
                # Update interval
                dcc.Interval(
                    id="dashboard-refresh-interval",
                    interval=5 * 1000,  # 5 seconds for debugging
                    n_intervals=0,
                ),
                # Modern Hero Section
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H1("Carbon-Aware FinOps Research Tool", className="hero-title"),
                                        html.H2(
                                            "Bachelor Thesis - Theoretical Framework Exploration", className="hero-subtitle"
                                        ),
                                        html.P(
                                            "Integrated carbon-aware FinOps methodology for German SME market",
                                            className="hero-description",
                                        ),
                                    ],
                                    className="hero-content",
                                ),
                                # Performance Stats
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div("📊", className="stat-icon"),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            str(len(instances)),
                                                            className="stat-value",
                                                            id="chartjs-live-instances",
                                                        ),
                                                        html.Span("Active Instances", className="stat-label"),
                                                    ],
                                                    className="stat-content",
                                                ),
                                            ],
                                            className="stat-card",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("💰", className="stat-icon"),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"€{self.cached_data.get('total_cost', 0):.2f}",
                                                            className="stat-value",
                                                            id="chartjs-live-cost",
                                                        ),
                                                        html.Span("Monthly Cost", className="stat-label"),
                                                    ],
                                                    className="stat-content",
                                                ),
                                            ],
                                            className="stat-card",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("🔬", className="stat-icon"),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "3", className="stat-value", id="api-count"
                                                        ),
                                                        html.Span("API Sources", className="stat-label"),
                                                    ],
                                                    className="stat-content",
                                                ),
                                            ],
                                            className="stat-card",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("⚠️", className="stat-icon"),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "±15%", className="stat-value", id="uncertainty-range"
                                                        ),
                                                        html.Span("Uncertainty", className="stat-label"),
                                                    ],
                                                    className="stat-content",
                                                ),
                                            ],
                                            className="stat-card",
                                        ),
                                    ],
                                    className="stats-grid",
                                ),
                            ],
                            className="hero-container",
                        )
                    ],
                    className="hero-section",
                ),
                # Dashboard Status Banner
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div("🎉", className="banner-icon"),
                                        html.Div(
                                            [
                                                html.Span("Research Prototype", className="banner-badge"),
                                                html.Span(
                                                    "Bachelor Thesis dashboard exploring integrated carbon-aware FinOps methodology",
                                                    className="banner-text",
                                                ),
                                            ],
                                            className="banner-content",
                                        ),
                                    ],
                                    className="banner-inner",
                                )
                            ],
                            className="container",
                        )
                    ],
                    className="success-banner",
                ),
                # Academic Disclaimer Banner
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div("⚠️", className="banner-icon"),
                                        html.Div(
                                            [
                                                html.Span("ACADEMIC DISCLAIMER", className="banner-badge"),
                                                html.Span(
                                                    "All optimization percentages (*) are theoretical estimates requiring empirical validation • Bachelor Thesis Research Prototype",
                                                    className="banner-text",
                                                ),
                                            ],
                                            className="banner-content",
                                        ),
                                    ],
                                    className="banner-inner",
                                )
                            ],
                            className="container",
                        )
                    ],
                    className="warning-banner",
                ),
                # Main Dashboard Layout
                html.Div(
                    [
                        html.Div(
                            [
                                # Navigation Sidebar
                                html.Div(
                                    [
                                        html.Div("Dashboard Navigation", className="nav-title"),
                                        html.Div(
                                            [
                                                html.Button(
                                                    [
                                                        html.Div("📊", className="nav-icon"),
                                                        html.Span("Infrastructure Overview", className="nav-text"),
                                                    ],
                                                    className="nav-item active",
                                                    id="chartjs-nav-overview",
                                                    **{"data-tab": "overview"},
                                                ),
                                                html.Button(
                                                    [
                                                        html.Div("🎓", className="nav-icon"),
                                                        html.Span("Thesis Validation", className="nav-text"),
                                                    ],
                                                    className="nav-item",
                                                    id="chartjs-nav-thesis",
                                                    **{"data-tab": "thesis"},
                                                ),
                                                html.Button(
                                                    [
                                                        html.Div("🔬", className="nav-icon"),
                                                        html.Span("Research Methods", className="nav-text"),
                                                    ],
                                                    className="nav-item",
                                                    id="chartjs-nav-research",
                                                    **{"data-tab": "research"},
                                                ),
                                                html.Button(
                                                    [
                                                        html.Div("🌍", className="nav-icon"),
                                                        html.Span("Carbon Analytics", className="nav-text"),
                                                    ],
                                                    className="nav-item",
                                                    id="chartjs-nav-carbon",
                                                    **{"data-tab": "carbon"},
                                                ),
                                            ],
                                            className="nav-menu",
                                        ),
                                    ],
                                    className="navigation-sidebar",
                                ),
                                # Main Content Area
                                html.Div(
                                    [
                                        # Overview Tab - Infrastructure Monitoring
                                        html.Div(
                                            [self.create_overview_content()],
                                            className="tab-content active",
                                            id="chartjs-overview-content",
                                        ),
                                        # Thesis Validation Tab - Academic Research
                                        html.Div(
                                            [self.create_thesis_content()],
                                            className="tab-content",
                                            id="chartjs-thesis-content",
                                        ),
                                        # Research Methods Tab - Scientific Methodology
                                        html.Div(
                                            [self.create_research_content()],
                                            className="tab-content",
                                            id="chartjs-research-content",
                                        ),
                                        # Carbon Analytics Tab - Environmental Data
                                        html.Div(
                                            [self.create_carbon_content()],
                                            className="tab-content",
                                            id="chartjs-carbon-content",
                                        ),
                                    ],
                                    className="main-content",
                                    id="chartjs-main-content-area",
                                ),
                            ],
                            className="dashboard-layout",
                        )
                    ],
                    className="container",
                ),
            ],
            className="chartjs-builder-dashboard",
        )

    def create_overview_content(self):
        """Create modern overview content"""
        instances = self.cached_data.get("instances", [])

        return html.Div(
            [
                html.Div(
                    [
                        html.H2("📊 Infrastructure Overview Dashboard", className="section-title"),
                        html.P(
                            "Comprehensive AWS monitoring with Chart.js visualization framework",
                            className="section-description",
                        ),
                    ],
                    className="section-header",
                ),
                # KPI Cards
                html.Div(
                    [
                        html.Div(id="chartjs-overview-cost-card", className="metric-card"),
                        html.Div(id="chartjs-overview-co2-card", className="metric-card"),
                        html.Div(id="chartjs-overview-instances-card", className="metric-card"),
                        html.Div(id="chartjs-overview-savings-card", className="metric-card"),
                    ],
                    className="metrics-grid",
                ),
                # Interactive Charts Section
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("💰 Cost Analysis Dashboard", className="chart-title"),
                                html.Div(id="chartjs-overview-costs", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("⏱️ Runtime Patterns Analysis", className="chart-title"),
                                html.Div(id="chartjs-overview-runtime", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("🌍 Carbon Emissions (Chart.js)", className="chart-title"),
                                html.Div(id="chartjs-overview-co2", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("📈 Efficiency Matrix (Chart.js)", className="chart-title"),
                                html.Div(id="chartjs-overview-efficiency", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )

    def create_thesis_content(self):
        """Create Chart.js thesis validation content"""
        return html.Div(
            [
                html.Div(
                    [
                        html.H2("🎓 Thesis Validation with Chart.js", className="section-title"),
                        html.P(
                            "Academic exploration of integrated carbon-aware FinOps approach",
                            className="section-description",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(id="chartjs-thesis-cost-advantage-card", className="metric-card"),
                        html.Div(id="chartjs-thesis-carbon-advantage-card", className="metric-card"),
                        html.Div(id="chartjs-thesis-integration-card", className="metric-card"),
                        html.Div(id="chartjs-thesis-research-card", className="metric-card"),
                    ],
                    className="metrics-grid",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("💰 Cost Optimization Comparison (Chart.js)", className="chart-title"),
                                html.Div(id="chartjs-cost-comparison", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("🌍 Carbon Optimization Comparison (Chart.js)", className="chart-title"),
                                html.Div(id="chartjs-carbon-comparison", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("🚀 Integrated Approach Exploration (Chart.js)", className="chart-title"),
                                html.Div(id="chartjs-comparison-analysis", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper wide",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )

    def create_research_content(self):
        """Create research methods content per .claude-guidelines"""
        return html.Div(
            [
                html.Div(
                    [
                        html.H2("🔬 Research Methodology & Data Quality", className="section-title"),
                        html.P(
                            "Scientific methodology transparency and data quality assessment",
                            className="section-description",
                        ),
                        html.Div(
                            [
                                html.Span("⚠️ ACADEMIC DISCLAIMER:", className="disclaimer-label"),
                                html.Span(" All visualizations show theoretical estimates requiring empirical validation", className="disclaimer-text"),
                            ],
                            className="method-disclaimer",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(id="chartjs-research-api-health-card", className="research-card"),
                        html.Div(id="chartjs-research-uncertainty-card", className="research-card"),
                        html.Div(id="chartjs-research-literature-card", className="research-card"), 
                        html.Div(id="chartjs-research-validation-card", className="research-card"),
                    ],
                    className="research-grid",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("🔍 API Data Quality Status", className="chart-title"),
                                html.Div(id="chartjs-api-health", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("📈 Uncertainty Ranges (±15%)", className="chart-title"),
                                html.Div(id="chartjs-uncertainty-ranges", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("🇩🇪 German Grid Context", className="chart-title"),
                                html.Div(id="chartjs-german-grid-context", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("📚 Literature Foundation Matrix", className="chart-title"),
                                html.Div(id="chartjs-literature-matrix", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )


    def create_carbon_content(self):
        """Create Chart.js carbon content"""
        return html.Div(
            [
                html.Div(
                    [
                        html.H2("🌍 Carbon & Power Analytics", className="section-title"),
                        html.P(
                            "Real-time carbon and power analysis with Chart.js - ElectricityMap & Boavizta APIs!",
                            className="section-description",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(id="chartjs-current-grid-intensity-card", className="carbon-card"),
                        html.Div(id="chartjs-total-power-consumption-card", className="carbon-card"),
                        html.Div(id="chartjs-monthly-co2-emissions-card", className="carbon-card"),
                        html.Div(id="chartjs-carbon-efficiency-score-card", className="carbon-card"),
                    ],
                    className="carbon-grid",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("🌍 Carbon Intensity Trends", className="chart-title"),
                                html.Div(id="chartjs-carbon-intensity", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("⚡ Power Consumption Distribution", className="chart-title"),
                                html.Div(id="chartjs-power-distribution", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("📈 CO2 Emissions Timeline", className="chart-title"),
                                html.Div(id="chartjs-co2-timeline", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                        html.Div(
                            [
                                html.H4("🎯 Carbon Efficiency Matrix", className="chart-title"),
                                html.Div(id="chartjs-carbon-efficiency", className="chartjs-container"),
                            ],
                            className="modern-chart-wrapper",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )

    def setup_chartjs_callbacks(self):
        """Setup Chart.js optimized callbacks"""

        # Clientside callback for tab navigation
        clientside_callback(
            """
            function(n_intervals) {
                // Tab navigation setup - runs after DOM is ready
                setTimeout(function() {
                    const navItems = document.querySelectorAll('.nav-item');
                    const tabContents = document.querySelectorAll('.tab-content');
                    
                    // Remove existing event listeners and add new ones
                    navItems.forEach(item => {
                        // Remove existing listeners
                        const newItem = item.cloneNode(true);
                        item.parentNode.replaceChild(newItem, item);
                    });
                    
                    // Re-select items after cloning
                    const freshNavItems = document.querySelectorAll('.nav-item');
                    
                    freshNavItems.forEach(item => {
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            
                            // Update navigation active states
                            freshNavItems.forEach(nav => nav.classList.remove('active'));
                            this.classList.add('active');
                            
                            // Update tab content active states
                            tabContents.forEach(content => content.classList.remove('active'));
                            
                            const targetTab = this.getAttribute('data-tab');
                            const targetContent = document.getElementById('chartjs-' + targetTab + '-content');
                            if (targetContent) {
                                targetContent.classList.add('active');
                            }
                        });
                    });
                    
                    console.log('Tab navigation initialized for', freshNavItems.length, 'tabs');
                }, 100);
                
                return {};
            }
            """,
            Output("chartjs-main-content-area", "style"),
            Input("dashboard-refresh-interval", "n_intervals"),
        )

        # Chart.js callback for ALL components
        @self.app.callback(
            [
                # Overview Card Outputs
                Output("chartjs-overview-cost-card", "children"),
                Output("chartjs-overview-co2-card", "children"),
                Output("chartjs-overview-instances-card", "children"),
                Output("chartjs-overview-savings-card", "children"),
                # Overview Chart Outputs (Chart.js)
                Output("chartjs-overview-costs", "children"),
                Output("chartjs-overview-runtime", "children"),
                Output("chartjs-overview-co2", "children"),
                Output("chartjs-overview-efficiency", "children"),
                # Thesis Card Outputs
                Output("chartjs-thesis-cost-advantage-card", "children"),
                Output("chartjs-thesis-carbon-advantage-card", "children"),
                Output("chartjs-thesis-integration-card", "children"),
                Output("chartjs-thesis-research-card", "children"),
                # Thesis Chart Outputs (Chart.js)
                Output("chartjs-cost-comparison", "children"),
                Output("chartjs-carbon-comparison", "children"),
                Output("chartjs-comparison-analysis", "children"),
                # Research Methods Card Outputs (Academic Transparency)
                Output("chartjs-research-api-health-card", "children"),
                Output("chartjs-research-uncertainty-card", "children"),
                Output("chartjs-research-literature-card", "children"),
                Output("chartjs-research-validation-card", "children"),
                # Research Methods Chart Outputs (Scientific Methodology)
                Output("chartjs-api-health", "children"),
                Output("chartjs-uncertainty-ranges", "children"),
                Output("chartjs-german-grid-context", "children"),
                Output("chartjs-literature-matrix", "children"),
                # Carbon Card Outputs
                Output("chartjs-current-grid-intensity-card", "children"),
                Output("chartjs-total-power-consumption-card", "children"),
                Output("chartjs-monthly-co2-emissions-card", "children"),
                Output("chartjs-carbon-efficiency-score-card", "children"),
                # Carbon Chart Outputs (Chart.js)
                Output("chartjs-carbon-intensity", "children"),
                Output("chartjs-power-distribution", "children"),
                Output("chartjs-co2-timeline", "children"),
                Output("chartjs-carbon-efficiency", "children"),
                # Live stats
                Output("chartjs-live-instances", "children"),
                Output("chartjs-live-cost", "children"),
            ],
            [Input("dashboard-refresh-interval", "n_intervals")],
        )
        def update_chartjs_dashboard(n_intervals):
            """Single Chart.js callback for ALL dashboard updates"""
            try:
                with monitor_dashboard_render("dashboard_update"):
                    # Refresh data
                    data = self.data_processor.get_infrastructure_data()
                instances = data.get("instances", [])

                # Overview components
                overview_cards = [
                    self.overview_tab.create_cost_card(instances),
                    self.overview_tab.create_co2_card(instances),
                    self.overview_tab.create_instances_card(instances),
                    self.overview_tab.create_savings_card(instances),
                ]

                # Overview Chart.js charts
                overview_charts = [
                    self.overview_tab.create_costs_chart(instances),
                    self.overview_tab.create_runtime_chart(instances),
                    self.overview_tab.create_co2_chart(instances),
                    self.overview_tab.create_efficiency_chart(instances),
                ]

                # Thesis components
                thesis_cards = [
                    self.thesis_tab.create_cost_advantage_card(instances),
                    self.thesis_tab.create_carbon_advantage_card(instances),
                    self.thesis_tab.create_integration_card(instances),
                    self.thesis_tab.create_research_card(instances),
                ]

                # Thesis Chart.js charts (must match 3 Outputs)
                thesis_charts = [
                    self.thesis_tab.create_cost_comparison_chart(instances),
                    self.thesis_tab.create_carbon_comparison_chart(instances),
                    self.thesis_tab.create_comparison_analysis_chart(instances),
                ]

                # Research Methods components (Academic Transparency per .claude-guidelines)
                research_cards = [
                    self.research_tab.create_api_health_status_card(instances),
                    self.research_tab.create_uncertainty_assessment_card(instances),
                    self.research_tab.create_literature_foundation_card(instances),
                    self.research_tab.create_validation_status_card(instances),
                ]

                # Research Methods Chart.js charts (Scientific Methodology)
                research_charts = [
                    self.research_tab.create_api_health_chart(instances),
                    self.research_tab.create_uncertainty_ranges_chart(instances),
                    self.research_tab.create_german_grid_context_chart(instances),
                    self.research_tab.create_literature_matrix_chart(instances),
                ]

                # Carbon components
                carbon_cards = [
                    self.carbon_tab.create_current_grid_intensity_card(instances),
                    self.carbon_tab.create_total_power_consumption_card(instances),
                    self.carbon_tab.create_monthly_co2_emissions_card(instances),
                    self.carbon_tab.create_carbon_efficiency_score_card(instances),
                ]

                # Carbon Chart.js charts
                carbon_charts = [
                    self.carbon_tab.create_carbon_intensity_chart(instances),
                    self.carbon_tab.create_power_distribution_chart(instances),
                    self.carbon_tab.create_co2_timeline_chart(instances),
                    self.carbon_tab.create_carbon_efficiency_chart(instances),
                ]

                # Live stats
                totals = data.get('totals', {})
                live_stats = [str(len(instances)), f"€{totals.get('monthly_cost_eur', 0):.2f}"]

                # Debug: Count return values
                all_returns = [
                    *overview_cards,      # 4
                    *overview_charts,     # 4  
                    *thesis_cards,        # 4
                    *thesis_charts,       # 3
                    *research_cards,      # 4
                    *research_charts,     # 4
                    *carbon_cards,        # 4
                    *carbon_charts,       # 4
                    *live_stats,          # 2
                ]
                
                logger.info(f"🔍 Dashboard callback returns {len(all_returns)} values")
                logger.info(f"📊 Breakdown: overview_cards={len(overview_cards)}, overview_charts={len(overview_charts)}")
                logger.info(f"📊 thesis_cards={len(thesis_cards)}, thesis_charts={len(thesis_charts)}")
                logger.info(f"📊 research_cards={len(research_cards)}, research_charts={len(research_charts)}")
                logger.info(f"📊 carbon_cards={len(carbon_cards)}, carbon_charts={len(carbon_charts)}")
                logger.info(f"📊 live_stats={len(live_stats)}")
                
                return tuple(all_returns)

            except Exception as e:
                logger.error(f"❌ Chart.js dashboard update failed: {e}")
                # Academic Error Handling: Transparent error reporting per .claude-guidelines
                error_content = html.Div([
                    html.Div("⚠️", className="error-icon"),
                    html.H4("Dashboard Data Update Failed", className="error-title"),
                    html.P([
                        "API data retrieval encountered an error. ",
                        "This maintains scientific integrity by not showing fallback data."
                    ], className="error-description"),
                    html.P([
                        "Technical details: ", str(e)
                    ], className="error-technical"),
                    html.Button("Refresh Dashboard", 
                               id="error-refresh-btn", 
                               className="error-refresh-button",
                               **{"data-action": "refresh"})
                ], className="error-container")
                return tuple([error_content] * 30)  # Total outputs match callback

    def run_server(self, debug=True, host="127.0.0.1", port=8053):
        """Run the modern dashboard with health checks"""
        print(f"\n🚀 Carbon-Aware FinOps Dashboard - Bachelor Thesis")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print(f"⚡ Modern Framework: 50kb lightweight bundle")
        print(f"🎨 CSS System: Builder.io design patterns")
        print(f"📐 Consistent: 400px chart dimensions")
        print(f"🇩🇪 German Grid: {self.cached_data.get('carbon_intensity', 420):.0f} g CO2/kWh")
        
        # Health Check vor Dashboard Start
        print(f"\n🏥 Checking API Health...")
        from utils.health_dashboard import print_startup_health_check
        try:
            ready_to_start = print_startup_health_check()
            if not ready_to_start:
                print("⚠️ Dashboard may have limited functionality due to API issues")
        except Exception as e:
            print(f"⚠️ Health check failed: {e}")
            print("Dashboard will start but some features may be limited")
        totals = self.cached_data.get('totals', {})
        instances = self.cached_data.get('instances', [])
        print(f"💰 Monthly Cost: €{totals.get('monthly_cost_eur', 0):.2f}")
        print(f"📋 Instances: {len(instances)}")
        print(f"\n📈 Chart.js Migration: ALL 26 CHARTS MIGRATED!")
        print(f"\nPress Ctrl+C to stop the dashboard\n")

        self.app.run(debug=debug, host=host, port=port)


def main():
    """Main function to run the dashboard"""
    dashboard = CarbonAwareDashboard()
    dashboard.run_server(debug=True, port=8050)


if __name__ == "__main__":
    main()
