"""
Real-time dashboard for Carbon-Aware FinOps metrics.
"""

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.logging_config import get_logger, LoggerMixin
from src.utils.retry_handler import AWSRetrySession, exponential_backoff, safe_aws_call
from src.config.settings import settings
from src.carbon.carbon_api_client import EC2EnergyCalculator
from src.carbon.carbon_api_client import CarbonIntensityClient


class DataCache:
    """Thread-safe data cache with TTL support."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.ttl = ttl_seconds
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self.lock:
            if key in self.cache:
                if time.time() - self.timestamps[key] < self.ttl:
                    return self.cache[key]
                else:
                    # Remove expired entry
                    del self.cache[key]
                    del self.timestamps[key]
            return None

    def set(self, key: str, value: Any) -> None:
        """Set cached value with current timestamp."""
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached data."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()


class CarbonFinOpsDashboard(LoggerMixin):
    """Real-time dashboard for Carbon-Aware FinOps metrics with performance optimizations."""

    def __init__(self, aws_profile=None):
        self.app = dash.Dash(__name__)
        self.aws_profile = aws_profile or (settings.aws.profile if settings.aws else None)

        # Performance optimizations
        self.cache = DataCache(
            ttl_seconds=(settings.dashboard.refresh_interval if settings.dashboard else 60000) // 1000
        )  # Convert to seconds
        self.executor = ThreadPoolExecutor(max_workers=4)

        try:
            # Use retry session for improved reliability
            self.aws_session = AWSRetrySession(
                self.aws_profile, settings.aws.region if settings.aws else "eu-central-1"
            )
            self.dynamodb = self.aws_session.get_resource("dynamodb")
            self.cloudwatch = self.aws_session.get_client("cloudwatch")
            # Cost Explorer is only available in us-east-1
            self.ce = self.aws_session.session.client("ce", region_name="us-east-1")
            self.ec2 = self.aws_session.get_client("ec2")

            self.logger.info(f"AWS clients initialized successfully with profile: {self.aws_profile}")
            
            # Initialize energy calculator
            self.energy_calculator = EC2EnergyCalculator()
            
        except Exception as e:
            self.logger.warning(f"AWS clients initialization failed with profile '{self.aws_profile}': {e}")
            self.logger.info("Please run: aws sso login --profile carbon-finops-sandbox")
            # Initialize as None to handle offline mode
            self.aws_session = None
            self.dynamodb = None
            self.cloudwatch = None
            self.ce = None
            self.ec2 = None
            self.energy_calculator = EC2EnergyCalculator()

        # Initialize layout
        self.setup_layout()
        self.setup_callbacks()

    def parallel_data_fetch(self, tasks: List[tuple]) -> Dict[str, Any]:
        """
        Fetch data in parallel using ThreadPoolExecutor.

        Args:
            tasks: List of (function, args) tuples to execute

        Returns:
            Dictionary of results keyed by task index
        """
        results = {}
        future_to_index = {}

        for i, (func, args) in enumerate(tasks):
            future = self.executor.submit(func, *args)
            future_to_index[future] = i

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result(timeout=10)  # 10 second timeout
            except Exception as e:
                self.logger.error(f"Task {index} failed: {e}")
                results[index] = None

        # Convert integer keys to strings for consistent return type
        return {str(k): v for k, v in results.items()}

    @exponential_backoff(max_retries=2)
    def get_dynamodb_data_cached(self, table_name: str, cache_key: str) -> Optional[List[Dict]]:
        """Get DynamoDB data with caching."""
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return list(cached_data) if isinstance(cached_data, list) else []

        if not self.dynamodb:
            return None

        try:
            table = self.dynamodb.Table(table_name)
            response = safe_aws_call(table.scan)

            if response:
                data = response.get("Items", [])
                # Cache the result
                self.cache.set(cache_key, data)
                return list(data) if data else []

        except Exception as e:
            self.logger.error(f"Failed to fetch data from {table_name}: {e}")

        return None

    def get_state_data(self) -> List[Dict]:
        """Get instance state data from DynamoDB."""
        return (
            self.get_dynamodb_data_cached(
                settings.aws.state_table if settings.aws else "carbon-finops-state", "state_data"
            )
            or []
        )

    def get_rightsizing_data(self) -> List[Dict]:
        """Get rightsizing recommendations from DynamoDB."""
        return (
            self.get_dynamodb_data_cached(
                settings.aws.rightsizing_table if settings.aws else "carbon-finops-rightsizing", "rightsizing_data"
            )
            or []
        )

    def get_cost_data(self) -> List[Dict]:
        """Get cost data from DynamoDB."""
        return (
            self.get_dynamodb_data_cached(
                settings.aws.costs_table if settings.aws else "carbon-finops-costs", "cost_data"
            )
            or []
        )

    def calculate_kpis_parallel(self) -> Dict[str, Any]:
        """Calculate KPIs using parallel data fetching."""
        cache_key = "dashboard_kpis"
        cached_kpis = self.cache.get(cache_key)
        if cached_kpis:
            return dict(cached_kpis) if isinstance(cached_kpis, dict) else {}

        # Define parallel tasks
        tasks = [(self.get_state_data, ()), (self.get_rightsizing_data, ()), (self.get_cost_data, ())]

        # Fetch data in parallel
        results = self.parallel_data_fetch(tasks)

        state_data = results.get("0", [])
        rightsizing_data = results.get("1", [])
        cost_data = results.get("2", [])

        # Calculate KPIs
        kpis = self._calculate_kpis_from_data(state_data, rightsizing_data, cost_data)

        # Cache results
        self.cache.set(cache_key, kpis)
        return kpis

    def _calculate_kpis_from_data(self, state_data: List, rightsizing_data: List, _cost_data: List) -> Dict[str, Any]:
        """Calculate KPIs from fetched data."""
        try:
            # Calculate cost savings
            total_savings = 0.0
            for item in rightsizing_data:
                if "recommendation" in item:
                    rec = item["recommendation"]
                    if isinstance(rec, dict) and "estimated_monthly_savings" in rec:
                        total_savings += float(rec.get("estimated_monthly_savings", 0))

            # Calculate carbon reduction (simplified)
            carbon_actions = len([item for item in state_data if item.get("action") == "shutdown"])
            carbon_reduction = int(carbon_actions * 2.5)  # Approximate kg CO2 per shutdown

            # Count optimized instances
            optimized_instances = len(
                [item for item in rightsizing_data if item.get("recommendation", {}).get("action") != "no_change"]
            )

            return {
                "cost_savings": f"${total_savings:.2f}",
                "carbon_reduction": f"{carbon_reduction:.1f} kg",
                "optimized_instances": str(optimized_instances),
            }

        except Exception as e:
            self.logger.error(f"Error calculating KPIs: {e}")
            return {"cost_savings": "$0.00", "carbon_reduction": "0.0 kg", "optimized_instances": "0"}

    def create_timeline_chart_cached(self, data: List[Dict], title: str, y_field: str, cache_key: str) -> go.Figure:
        """Create timeline chart with caching."""
        cached_chart = self.cache.get(cache_key)
        if cached_chart:
            return cached_chart

        fig = go.Figure()

        if not data:
            fig.add_trace(
                go.Scatter(x=[datetime.now()], y=[0], mode="markers", name="No Data", text="No data available")
            )
        else:
            # Process data for timeline
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                # Convert timestamp to datetime
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
                df = df.dropna(subset=["datetime"])

                if not df.empty and y_field in df.columns:
                    df = df.sort_values("datetime")

                    # Limit data points for performance
                    max_points = settings.dashboard.max_chart_points if settings.dashboard else 1000
                    if len(df) > max_points:
                        df = df.tail(max_points)

                    fig.add_trace(
                        go.Scatter(
                            x=df["datetime"], y=df[y_field], mode="lines+markers", name=title, line=dict(width=2)
                        )
                    )

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title=title,
            showlegend=False,
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
        )

        # Cache the figure
        self.cache.set(cache_key, fig)
        return fig

    def setup_layout(self):
        """Setup dashboard layout."""

        self.app.layout = html.Div(
            [
                html.Div(
                    [
                        html.H1("Carbon-Aware FinOps Dashboard", style={"textAlign": "center", "color": "#2c3e50"}),
                        html.Hr(),
                    ]
                ),
                # KPI Row (Focused Overview)
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("Cost Savings", style={"color": "#27ae60"}),
                                        html.H2(id="cost-savings", children="$0"),
                                        html.P("Today", style={"color": "#7f8c8d"}),
                                    ],
                                    className="kpi-card",
                                ),
                            ],
                            className="six columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("CO₂ Reduction", style={"color": "#2ecc71"}),
                                        html.H2(id="carbon-reduction", children="0 kg"),
                                        html.P("Today", style={"color": "#7f8c8d"}),
                                    ],
                                    className="kpi-card",
                                ),
                            ],
                            className="six columns",
                        ),
                    ],
                    className="row",
                ),
                # Recommendations Table (Focused)
                html.Div(
                    [html.H3("Active Rightsizing Recommendations"), html.Div(id="recommendations-table")], style={"margin": "20px"}
                ),
                # Baseline vs Scheduling Comparison
                html.Div([
                    html.H3("Baseline vs Scheduling Savings", style={"color": "#2c3e50"}),
                    html.P(
                        "Daily cost and CO₂ comparison of 24/7 baseline vs scheduled instances",
                        style={"color": "#7f8c8d", "font-style": "italic"}
                    ),
                    html.Div([
                        html.Div([
                            dcc.Graph(id="baseline-cost-chart"),
                        ], className="six columns"),
                        html.Div([
                            dcc.Graph(id="baseline-carbon-chart"),
                        ], className="six columns"),
                    ], className="row"),
                    html.Div([
                        html.H4("Daily Comparison Table"),
                        html.Div(id="baseline-comparison-table"),
                    ], style={"marginTop": "10px"}),
                ], style={"margin": "20px"}),
                # Hourly Comparison (Focused)
                html.Div([
                    html.H3("Hourly Comparison", style={"color": "#2c3e50"}),
                    html.P(
                        "Hourly cost and CO₂ based on today's DynamoDB costs and ElectricityMap forecast",
                        style={"color": "#7f8c8d", "fontStyle": "italic"}
                    ),
                    html.Div([
                        html.Div([
                            dcc.Graph(id="hourly-cost-chart"),
                        ], className="six columns"),
                        html.Div([
                            dcc.Graph(id="hourly-carbon-chart"),
                        ], className="six columns"),
                    ], className="row"),
                ], style={"margin": "20px"}),
                # Auto-refresh - Update every hour for real data
                dcc.Interval(id="interval-component", interval=60 * 60 * 1000, n_intervals=0),  # Update every hour
            ]
        )

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        def update_dashboard(_n_intervals):  # Callback function for Dash - n_intervals is required by Dash but unused
            # Get current metrics
            metrics = self.get_current_metrics()

            # Update KPIs
            cost_savings = f"${metrics['cost_savings']:.2f}"
            carbon_reduction = f"{metrics['carbon_reduction']:.1f} kg"

            # Create recommendations table
            recommendations_table = self.create_recommendations_table()

            # Baseline vs Scheduling comparison
            comparison_data = self.get_baseline_comparison_data()
            baseline_cost_chart = self.create_baseline_cost_chart(comparison_data)
            baseline_carbon_chart = self.create_baseline_carbon_chart(comparison_data)
            baseline_comparison_table = self.create_baseline_comparison_table(comparison_data)

            # Hourly charts
            hourly_cost_chart = self.create_hourly_cost_chart()
            hourly_carbon_chart = self.create_hourly_carbon_chart()

            return (
                cost_savings,
                carbon_reduction,
                baseline_cost_chart,
                baseline_carbon_chart,
                baseline_comparison_table,
                recommendations_table,
                hourly_cost_chart,
                hourly_carbon_chart,
            )

        # Register the callback with Dash
        self.app.callback(
            [
                Output("cost-savings", "children"),
                Output("carbon-reduction", "children"),
                Output("baseline-cost-chart", "figure"),
                Output("baseline-carbon-chart", "figure"),
                Output("baseline-comparison-table", "children"),
                Output("recommendations-table", "children"),
                Output("hourly-cost-chart", "figure"),
                Output("hourly-carbon-chart", "figure"),
            ],
            [Input("interval-component", "n_intervals")],
        )(update_dashboard)

    # ---------- Baseline vs Scheduling comparison helpers ----------
    def _instance_groups(self) -> Dict[str, Dict[str, str]]:
        """Define baseline and scheduled instance groups aligned with Terraform tags."""
        return {
            "web-server": {"name": "Web Server", "type": "t3.medium", "schedule": "24/7 Always Running", "color": "#e74c3c"},
            "app-server": {"name": "App Server", "type": "t3.large", "schedule": "Office Hours + Weekend Shutdown", "color": "#e67e22"},
            "db-server": {"name": "DB Server", "type": "t3.small", "schedule": "Extended Development Hours", "color": "#27ae60"},
            "batch-server": {"name": "Batch Server", "type": "t3.micro", "schedule": "Carbon-Aware 24/7", "color": "#2ecc71"},
        }

    def _estimate_daily_runtime_hours(self, schedule_name: str, region: str = "eu-central-1") -> float:
        """Estimate daily runtime hours based on schedule name.
        Uses ElectricityMap forecast for carbon-aware schedule.
        """
        schedule = schedule_name.strip().lower()
        today = datetime.now()
        weekday = today.weekday()  # 0=Mon..6=Sun

        if schedule in ("24/7 always running", "always-on"):
            return 24.0
        if schedule == "office hours + weekend shutdown":
            return 10.0 if weekday < 5 else 0.0  # 08:00-18:00 weekdays
        if schedule == "extended development hours":
            return 13.0 if weekday < 5 else 0.0  # 07:00-20:00 weekdays
        if schedule == "carbon-aware 24/7":
            try:
                threshold = 300.0
                # Prefer configured threshold if available via YAML defaults
                threshold = threshold
                carbon_client = CarbonIntensityClient(provider="electricitymap")
                forecast = carbon_client.get_forecast(region, hours=24)
                below = [v for v in forecast if v < threshold]
                return float(len(below))
            except Exception:
                return 12.0  # Fallback half-day
        return 24.0

    def get_baseline_comparison_data(self) -> List[Dict[str, Any]]:
        """Compute baseline vs scheduled daily cost and CO₂ per instance group."""
        groups = self._instance_groups()
        region = settings.aws.region if settings.aws else "eu-central-1"

        # Use ElectricityMap for carbon intensity
        carbon_client = CarbonIntensityClient(provider="electricitymap")

        try:
            carbon_intensity = float(carbon_client.get_current_intensity(region))
        except Exception:
            carbon_intensity = 400.0

        # Build mapping of group key -> instance_id from EC2
        instance_id_map: Dict[str, str] = {}
        try:
            # Reuse logic from real instance fetch
            response = self.ec2.describe_instances(
                Filters=[
                    {"Name": "tag:Project", "Values": ["carbon-aware-finops"]},
                    {"Name": "tag:InstanceRole", "Values": ["Scheduled"]},
                ]
            )
            for reservation in response.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "")
                    for key in groups.keys():
                        if name_tag.endswith(key):  # matches carbon-aware-finops-<key>
                            instance_id_map[key] = inst.get("InstanceId", "")
        except Exception as e:
            self.logger.warning(f"Could not map instance IDs: {e}")

        # Prefer hourly table for today's cost totals; fallback to daily costs table
        costs_by_instance: Dict[str, float] = {}
        hourly_data = self.get_hourly_metrics_from_dynamodb()
        if hourly_data:
            for series in hourly_data:
                iid = series.get("instance_id")
                if not iid:
                    continue
                total = sum(series.get("hourly_costs", []) or [])
                costs_by_instance[iid] = costs_by_instance.get(iid, 0.0) + float(total)
        else:
            today_str = datetime.now().strftime("%Y-%m-%d")
            try:
                cost_items = self.get_cost_data()  # expects items with 'date', 'instance_id', 'cost'
                for item in cost_items:
                    if str(item.get("date", "")) == today_str:
                        iid = str(item.get("instance_id", ""))
                        try:
                            amt = float(item.get("cost", 0.0))
                        except Exception:
                            amt = 0.0
                        costs_by_instance[iid] = costs_by_instance.get(iid, 0.0) + amt
            except Exception as e:
                self.logger.warning(f"Failed to load daily costs from DynamoDB: {e}")

        rows: List[Dict[str, Any]] = []

        for key, cfg in groups.items():
            instance_type = cfg["type"]
            schedule_name = cfg["schedule"]
            color = cfg["color"]

            # Baseline 24/7
            baseline_hours = 24.0
            scheduled_hours = self._estimate_daily_runtime_hours(schedule_name, region)

            # Energy and carbon via EC2EnergyCalculator
            try:
                power_watts = self.energy_calculator.get_instance_power_consumption(instance_type, cpu_utilization=0.20)
            except Exception:
                power_watts = 100.0

            baseline_kwh = (power_watts * baseline_hours) / 1000.0
            scheduled_kwh = (power_watts * scheduled_hours) / 1000.0

            # Use hourly forecast to better estimate daily CO2 over running hours
            try:
                forecast = carbon_client.get_forecast(region, hours=24)
                # forecast returned as floats
                # Baseline runs all hours
                baseline_co2_kg = sum(((power_watts / 1000.0) * v) / 1000.0 for v in forecast)
                # Scheduled runs only specific hours; derive mask
                mask = [False] * 24
                now_hour = datetime.now().hour
                if schedule_name.lower() == "office hours + weekend shutdown" and datetime.now().weekday() < 5:
                    for h in range(8, 18):
                        mask[h] = True
                elif schedule_name.lower() == "extended development hours" and datetime.now().weekday() < 5:
                    for h in range(7, 20):
                        mask[h] = True
                elif schedule_name.lower() == "carbon-aware 24/7":
                    # Select hours below threshold
                    th = 300.0
                    for idx, v in enumerate(forecast):
                        if v < th:
                            mask[(now_hour + idx) % 24] = True
                else:
                    mask = [True] * 24
                scheduled_co2_kg = sum(((power_watts / 1000.0) * v) / 1000.0 for i, v in enumerate(forecast) if mask[(now_hour + i) % 24])
            except Exception:
                baseline_co2_kg = (baseline_kwh * carbon_intensity) / 1000.0
                scheduled_co2_kg = (scheduled_kwh * carbon_intensity) / 1000.0

            # Cost totals: use hourly table totals (or daily table fallback above)
            iid = instance_id_map.get(key, "")
            scheduled_cost = float(costs_by_instance.get(iid, 0.0))
            # Baseline cost: from baseline instance hourly totals if available; else estimate from scheduled cost per hour
            baseline_iid = instance_id_map.get("web-server", "")
            baseline_cost = float(costs_by_instance.get(baseline_iid, 0.0))
            if baseline_cost == 0.0:
                try:
                    cost_per_hour = scheduled_cost / scheduled_hours if scheduled_hours > 0 else 0.0
                except Exception:
                    cost_per_hour = 0.0
                if cost_per_hour == 0.0:
                    try:
                        from src.config.settings import get_instance_pricing
                        cost_per_hour = float(get_instance_pricing(instance_type))
                    except Exception:
                        cost_per_hour = 0.05
                baseline_cost = 24.0 * cost_per_hour

            rows.append({
                "Instance": cfg["name"],
                "Type": instance_type,
                "Schedule": schedule_name,
                "Baseline Hours": baseline_hours,
                "Scheduled Hours": scheduled_hours,
                "Baseline Cost ($)": round(baseline_cost, 4),
                "Scheduled Cost ($)": round(scheduled_cost, 4),
                "Cost Savings ($)": round(baseline_cost - scheduled_cost, 4),
                "Baseline CO₂ (kg)": round(baseline_co2_kg, 4),
                "Scheduled CO₂ (kg)": round(scheduled_co2_kg, 4),
                "CO₂ Savings (kg)": round(baseline_co2_kg - scheduled_co2_kg, 4),
                "color": color,
            })

        return rows

    def create_baseline_cost_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        fig = go.Figure()
        if not data:
            return fig
        names = [r["Instance"] for r in data]
        baseline = [r["Baseline Cost ($)"] for r in data]
        scheduled = [r["Scheduled Cost ($)"] for r in data]
        colors = [r["color"] for r in data]

        fig.add_trace(go.Bar(x=names, y=baseline, name="Baseline (24/7)", marker_color="#7f8c8d"))
        fig.add_trace(go.Bar(x=names, y=scheduled, name="Scheduled", marker_color=colors))
        fig.update_layout(
            title="Daily Cost Comparison",
            barmode="group",
            yaxis_title="Cost ($ per day)",
            height=380,
        )
        return fig

    def create_baseline_carbon_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        fig = go.Figure()
        if not data:
            return fig
        names = [r["Instance"] for r in data]
        baseline = [r["Baseline CO₂ (kg)"] for r in data]
        scheduled = [r["Scheduled CO₂ (kg)"] for r in data]
        colors = [r["color"] for r in data]

        fig.add_trace(go.Bar(x=names, y=baseline, name="Baseline (24/7)", marker_color="#7f8c8d"))
        fig.add_trace(go.Bar(x=names, y=scheduled, name="Scheduled", marker_color=colors))
        fig.update_layout(
            title="Daily CO₂ Comparison",
            barmode="group",
            yaxis_title="CO₂ (kg per day)",
            height=380,
        )
        return fig

    def create_baseline_comparison_table(self, data: List[Dict[str, Any]]):
        if not data:
            return html.Div([html.P("No comparison data available")])
        display_cols = [
            "Instance", "Type", "Schedule",
            "Baseline Hours", "Scheduled Hours",
            "Baseline Cost ($)", "Scheduled Cost ($)", "Cost Savings ($)",
            "Baseline CO₂ (kg)", "Scheduled CO₂ (kg)", "CO₂ Savings (kg)",
        ]
        table_rows = []
        for r in data:
            table_rows.append({k: r[k] for k in display_cols})
        return dash_table.DataTable(
            data=table_rows,
            columns=[{"name": c, "id": c} for c in display_cols],
            style_cell={"textAlign": "center", "padding": "8px", "fontFamily": "Arial"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
        )

    def get_current_metrics(self):
        """Get current metrics from DynamoDB and CloudWatch."""

        # Default values for offline mode
        default_metrics = {
            "cost_savings": 0,
            "carbon_reduction": 0,
            "energy_savings": 0,
            "optimized_instances": 0,
            "total_shutdowns": 0,
            "total_startups": 0,
        }

        if not self.dynamodb:
            return default_metrics

        try:
            # Get data from DynamoDB
            table = self.dynamodb.Table("carbon-aware-finops-state")

            # Query last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            response = table.scan(
                FilterExpression="#t >= :start",
                ExpressionAttributeNames={"#t": "timestamp"},
                ExpressionAttributeValues={":start": int(start_date.timestamp())},
            )

            # Calculate metrics
            def _to_int(v: Any) -> int:
                try:
                    if v is None:
                        return 0
                    if isinstance(v, Decimal):
                        return int(v)
                    return int(v)
                except Exception:
                    return 0

            def _to_float(v: Any) -> float:
                try:
                    if v is None:
                        return 0.0
                    if isinstance(v, Decimal):
                        return float(v)
                    return float(v)
                except Exception:
                    return 0.0

            total_shutdowns = sum(_to_int(item.get("shutdowns", 0)) for item in response.get("Items", []))
            total_startups = sum(_to_int(item.get("startups", 0)) for item in response.get("Items", []))

            # Estimate savings using energy calculator
            cost_per_hour = 0.05  # Average cost per instance hour
            carbon_per_hour = 0.2  # kg CO2 per instance hour
            
            # Calculate energy savings using average instance power consumption
            avg_instance_power_kw = 0.1  # 100W average for t3.medium instances
            hours_saved = _to_int(total_shutdowns) * 8
            energy_saved_kwh = float(hours_saved) * float(avg_instance_power_kw)

            return {
                "cost_savings": float(hours_saved) * float(cost_per_hour),
                "carbon_reduction": float(hours_saved) * float(carbon_per_hour),
                "energy_savings": float(energy_saved_kwh),
                "optimized_instances": total_shutdowns,
                "total_shutdowns": total_shutdowns,
                "total_startups": total_startups,
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return default_metrics

    def create_cost_timeline(self):
        """Create cost timeline chart."""

        if not self.ce:
            # Return empty chart if no AWS connection
            fig = go.Figure()
            fig.update_layout(
                title="Cost Data - AWS Connection Required",
                xaxis_title="Date",
                yaxis_title="Cost ($)",
                annotations=[
                    dict(
                        text="Please ensure AWS SSO is logged in to view cost data",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=False,
                        font=dict(size=16),
                    )
                ],
            )
            return fig

        # Get cost data from Cost Explorer
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                Filter={"Tags": {"Key": "Project", "Values": ["carbon-aware-finops"]}},
            )

            dates = [r["TimePeriod"]["Start"] for r in response["ResultsByTime"]]
            costs = [float(r["Total"]["UnblendedCost"]["Amount"]) for r in response["ResultsByTime"]]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=dates, y=costs, mode="lines+markers", name="Daily Cost", line=dict(color="#e74c3c", width=2)
                )
            )

            fig.update_layout(
                title="Cost Trend (Last 30 Days)", xaxis_title="Date", yaxis_title="Cost ($)", hovermode="x unified"
            )

            return fig

        except Exception as e:
            self.logger.error(f"Error creating cost timeline: {e}")
            # Return empty figure on error
            return go.Figure()

    def create_carbon_timeline(self):
        """Create carbon emissions timeline chart."""

        if not self.dynamodb:
            # Return empty chart if no AWS connection
            fig = go.Figure()
            fig.update_layout(
                title="Carbon Emissions Data - AWS Connection Required",
                xaxis_title="Date",
                yaxis_title="CO₂ (kg)",
                annotations=[
                    dict(
                        text="Please ensure AWS SSO is logged in to view carbon data",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=False,
                        font=dict(size=16),
                    )
                ],
            )
            return fig

        try:
            # Get real carbon data from DynamoDB
            table = self.dynamodb.Table("carbon-aware-finops-state")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            response = table.scan(
                FilterExpression="#t >= :start",
                ExpressionAttributeNames={"#t": "timestamp"},
                ExpressionAttributeValues={":start": int(start_date.timestamp())},
            )

            if not response.get("Items"):
                # No data available
                fig = go.Figure()
                fig.update_layout(
                    title="Carbon Emissions Data - No Data Available",
                    xaxis_title="Date",
                    yaxis_title="CO₂ (kg)",
                    annotations=[
                        dict(
                            text="No carbon emissions data found. Run carbon-aware scheduling to collect data.",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            xanchor="center",
                            yanchor="middle",
                            showarrow=False,
                            font=dict(size=14),
                        )
                    ],
                )
                return fig

            # Process real data
            carbon_data = []
            for item in response["Items"]:
                if "carbon_intensity" in item:
                    carbon_data.append(
                        {
                            "timestamp": datetime.fromtimestamp(int(item["timestamp"])),
                            "carbon_intensity": float(item.get("carbon_intensity", 0)),
                        }
                    )

            if carbon_data:
                df = pd.DataFrame(carbon_data)
                df = df.sort_values("timestamp")

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df["carbon_intensity"],
                        mode="lines+markers",
                        name="Carbon Intensity",
                        line=dict(color="#27ae60"),
                    )
                )

                fig.update_layout(
                    title="Real Carbon Intensity Data",
                    xaxis_title="Date",
                    yaxis_title="Carbon Intensity (gCO₂/kWh)",
                    hovermode="x unified",
                )
                return fig

        except Exception as e:
            self.logger.error(f"Error getting carbon timeline data: {e}")

            # Fallback empty chart with specific error handling
            fig = go.Figure()
            if "ResourceNotFoundException" in str(e):
                fig.update_layout(
                    title="Carbon Data Setup Required",
                    xaxis_title="Date",
                    yaxis_title="CO₂ (kg)",
                    annotations=[
                        dict(
                            text=(
                                "The carbon data table doesn't exist yet. "
                                "Deploy DynamoDB tables or run carbon-aware scheduling first."
                            ),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            xanchor="center",
                            yanchor="middle",
                            showarrow=False,
                            font=dict(size=14),
                        )
                    ],
                )
            else:
                fig.update_layout(
                    title="Carbon Emissions Data - Error Loading Data",
                    xaxis_title="Date",
                    yaxis_title="CO₂ (kg)",
                    annotations=[
                        dict(
                            text=f"Error loading data: {str(e)[:50]}...",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            xanchor="center",
                            yanchor="middle",
                            showarrow=False,
                            font=dict(size=14),
                        )
                    ],
                )
            return fig

    def create_energy_timeline(self):
        """Create energy consumption timeline chart."""

        if not self.dynamodb:
            # Return empty chart if no AWS connection
            fig = go.Figure()
            fig.update_layout(
                title="Energy Data - AWS Connection Required",
                xaxis_title="Date",
                yaxis_title="Energy (kWh)",
                annotations=[
                    dict(
                        text="Please ensure AWS SSO is logged in to view energy data",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=False,
                        font=dict(size=16),
                    )
                ],
            )
            return fig

        try:
            # Get instance data and calculate energy consumption
            table = self.dynamodb.Table("carbon-aware-finops-state")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            response = table.scan(
                FilterExpression="#t >= :start",
                ExpressionAttributeNames={"#t": "timestamp"},
                ExpressionAttributeValues={":start": int(start_date.timestamp())},
            )

            # Calculate daily energy consumption
            daily_energy = {}
            for item in response.get("Items", []):
                # Convert potential Decimal to int
                try:
                    ts_val = item.get("timestamp", 0)
                    if isinstance(ts_val, Decimal):
                        ts = int(ts_val)
                    else:
                        ts = int(ts_val)
                except Exception:
                    ts = 0
                timestamp = datetime.fromtimestamp(ts)
                date_key = timestamp.strftime("%Y-%m-%d")
                
                shutdowns = item.get("shutdowns", 0)
                startups = item.get("startups", 0)

                # Estimate energy saved from shutdowns (8 hours * 0.1 kW average)
                try:
                    sh = int(shutdowns) if not isinstance(shutdowns, Decimal) else int(shutdowns)
                except Exception:
                    sh = 0
                energy_saved = float(sh) * 8.0 * 0.1  # kWh
                
                if date_key not in daily_energy:
                    daily_energy[date_key] = 0
                daily_energy[date_key] += energy_saved

            # Create timeline data
            dates = sorted(daily_energy.keys())
            energy_values = [daily_energy[date] for date in dates]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=energy_values,
                mode='lines+markers',
                name='Energy Saved',
                line=dict(color='#e67e22', width=3)
            ))

            fig.update_layout(
                title="Energy Consumption Savings Over Time",
                xaxis_title="Date",
                yaxis_title="Energy Saved (kWh)",
                hovermode="x",
                plot_bgcolor="white",
                height=400,
            )

            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")

        except Exception as e:
            self.logger.error(f"Error creating energy timeline: {e}")
            fig = go.Figure()
            fig.update_layout(
                title="Energy Timeline - Error",
                xaxis_title="Date",
                yaxis_title="Energy (kWh)",
                annotations=[
                    dict(
                        text=f"Error loading data: {str(e)[:50]}...",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=False,
                        font=dict(size=14),
                    )
                ],
            )
        return fig

    def create_recommendations_table(self):
        """Create recommendations table from real AWS data."""

        if not self.dynamodb:
            return html.Div(
                [
                    html.H4("Recommendations - AWS Connection Required"),
                    html.P("Please ensure AWS SSO is logged in to view recommendations."),
                ]
            )

        try:
            # Get real recommendations from DynamoDB
            table = self.dynamodb.Table("carbon-aware-finops-rightsizing")

            response = table.scan()

            if not response.get("Items"):
                return html.Div(
                    [
                        html.H4("No Recommendations Available"),
                        html.P(
                            "No rightsizing recommendations found. "
                            "Run the rightsizing Lambda function to generate recommendations."
                        ),
                    ]
                )

            recommendations = []
            for item in response["Items"]:
                if item.get("recommendation", {}).get("action") != "no_change":
                    rec = item.get("recommendation", {})
                    recommendations.append(
                        {
                            "Instance": item.get("instance_id", "N/A"),
                            "Current": item.get("current_type", "N/A"),
                            "Recommended": rec.get("recommended_type", "N/A"),
                            "Savings": f"${rec.get('estimated_monthly_savings', 0):.2f}/month",
                            "Action": rec.get("action", "N/A").title(),
                            "Reason": ", ".join(rec.get("reason", [])),
                        }
                    )

            if not recommendations:
                return html.Div(
                    [
                        html.H4("No Active Recommendations"),
                        html.P("All instances are optimally sized based on current usage patterns."),
                    ]
                )

            df = pd.DataFrame(recommendations)

            # Convert DataFrame to proper types for Dash DataTable
            table_data = []
            for record in df.to_dict("records"):
                # Ensure all keys are strings and values are proper types
                table_record = {}
                for key, value in record.items():
                    table_record[str(key)] = str(value) if value is not None else ""
                table_data.append(table_record)

            # Type ignore for Dash DataTable style properties that aren't properly typed
            return dash_table.DataTable(
                data=table_data,  # type: ignore
                columns=[{"name": str(i), "id": str(i)} for i in df.columns],
                style_cell={"textAlign": "left"},
                style_data_conditional=[  # type: ignore
                    {
                        "if": {"column_id": "Action", "filter_query": '{Action} = "Downsize"'},
                        "backgroundColor": "#3498db",
                        "color": "white",
                    },
                    {
                        "if": {"column_id": "Action", "filter_query": '{Action} = "Upsize"'},
                        "backgroundColor": "#e67e22",
                        "color": "white",
                    },
                    {
                        "if": {"column_id": "Action", "filter_query": '{Action} = "Convert to spot"'},
                        "backgroundColor": "#9b59b6",
                        "color": "white",
                    },
                ]
            )

        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")

            # Handle specific DynamoDB table not found error
            if "ResourceNotFoundException" in str(e):
                return html.Div(
                    [
                        html.H4("Recommendations Setup Required"),
                        html.P("The rightsizing recommendations table doesn't exist yet."),
                        html.P(
                            "Please deploy the DynamoDB tables first or run the rightsizing "
                            "Lambda function to create the table."
                        ),
                    ]
                )
            else:
                return html.Div(
                    [html.H4("Error Loading Recommendations"), html.P(f"Failed to load recommendations: {str(e)}")]
                )

    def create_instance_analysis_table(self):
        """Create detailed instance cost & carbon analysis table for thesis research."""
        
        # Define instance configurations for analysis
        instance_configs = {
            "web-server": {
                "name": "Web Server",
                "type": "t3.medium", 
                "schedule": "24/7 Always Running",
                "rightsizing": "Over-provisioned",
                "color": "#e74c3c"
            },
            "app-server": {
                "name": "App Server", 
                "type": "t3.large",
                "schedule": "Office Hours + Weekend Shutdown",
                "rightsizing": "Over-provisioned", 
                "color": "#e67e22"
            },
            "db-server": {
                "name": "DB Server",
                "type": "t3.small",
                "schedule": "Extended Development Hours", 
                "rightsizing": "Right-sized",
                "color": "#27ae60"
            },
            "batch-server": {
                "name": "Batch Server",
                "type": "t3.micro",
                "schedule": "Carbon-Aware 24/7",
                "rightsizing": "Right-sized",
                "color": "#2ecc71" 
            }
        }

        # Calculate costs and carbon emissions using energy calculator
        analysis_data = []
        
        for instance_id, config in instance_configs.items():
            # Get power consumption and costs using energy calculator
            try:
                if hasattr(self, 'energy_calculator'):
                    instance_analysis = self.energy_calculator.get_complete_instance_analysis(
                        instance_id=f"i-{instance_id}",
                        instance_type=config["type"],
                        runtime_hours=24,  # Daily analysis
                        region="eu-central-1",
                        cpu_utilization=0.20  # Assume 20% average utilization (fraction)
                    )
                    
                    # Calculate daily and monthly values
                    daily_cost = instance_analysis.cost_usd  # This is for 24h
                    monthly_cost = daily_cost * 30
                    daily_carbon_kg = instance_analysis.carbon_emissions_kg  # This is for 24h
                    monthly_carbon_kg = daily_carbon_kg * 30
                    daily_energy_kwh = instance_analysis.energy_consumption_kwh  # This is for 24h
                    
                    analysis_data.append({
                        "Instance": config["name"],
                        "Type": config["type"], 
                        "Schedule": config["schedule"],
                        "Rightsizing": config["rightsizing"],
                        "Power (W)": f"{instance_analysis.power_consumption_watts:.1f}W",
                        "Daily Cost": f"${daily_cost:.2f}",
                        "Monthly Cost": f"${monthly_cost:.2f}",
                        "Daily CO₂": f"{daily_carbon_kg:.2f} kg",
                        "Monthly CO₂": f"{monthly_carbon_kg:.1f} kg",
                        "Energy/Day": f"{daily_energy_kwh:.2f} kWh"
                    })
                else:
                    # Fallback without energy calculator
                    analysis_data.append({
                        "Instance": config["name"],
                        "Type": config["type"],
                        "Schedule": config["schedule"], 
                        "Rightsizing": config["rightsizing"],
                        "Power (W)": "N/A",
                        "Daily Cost": "N/A",
                        "Monthly Cost": "N/A", 
                        "Daily CO₂": "N/A",
                        "Monthly CO₂": "N/A",
                        "Energy/Day": "N/A"
                    })
                    
            except Exception as e:
                self.logger.error(f"Error calculating analysis for {instance_id}: {e}")
                analysis_data.append({
                    "Instance": config["name"],
                    "Type": config["type"],
                    "Schedule": config["schedule"],
                    "Rightsizing": config["rightsizing"], 
                    "Power (W)": "Error",
                    "Daily Cost": "Error",
                    "Monthly Cost": "Error",
                    "Daily CO₂": "Error", 
                    "Monthly CO₂": "Error",
                    "Energy/Day": "Error"
                })

        # Create the table
        if analysis_data:
            return dash_table.DataTable(
                data=analysis_data,
                columns=[
                    {"name": "Instance", "id": "Instance"},
                    {"name": "Instance Type", "id": "Type"},
                    {"name": "Schedule Pattern", "id": "Schedule"}, 
                    {"name": "Rightsizing", "id": "Rightsizing"},
                    {"name": "Power Consumption", "id": "Power (W)"},
                    {"name": "Daily Cost", "id": "Daily Cost"},
                    {"name": "Monthly Cost", "id": "Monthly Cost"},
                    {"name": "Daily CO₂", "id": "Daily CO₂"},
                    {"name": "Monthly CO₂", "id": "Monthly CO₂"},
                    {"name": "Daily Energy", "id": "Energy/Day"}
                ],
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': 'Arial'
                },
                style_data_conditional=[  # type: ignore
                    {
                        'if': {'filter_query': '{Rightsizing} = Over-provisioned'},
                        'backgroundColor': '#fee2e2',
                        'color': '#dc2626'
                    },
                    {
                        'if': {'filter_query': '{Rightsizing} = Right-sized'},
                        'backgroundColor': '#d1fae5', 
                        'color': '#059669'
                    }
                ],
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                }
            )
        else:
            return html.Div([
                html.H4("Instance Analysis"),
                html.P("No instance data available for analysis")
            ])

    def create_hourly_cost_chart(self):
        """Create hourly cost timeline with real AWS instance data and scheduler effects."""
        
        fig = go.Figure()
        
        try:
            # Prefer hourly metrics from DynamoDB if available
            real_instance_data = self.get_hourly_metrics_from_dynamodb()
            if not real_instance_data:
                # Fallback to computed hourly data
                real_instance_data = self.get_real_instance_hourly_data()
            
            if not real_instance_data:
                fig.add_annotation(
                    text="No real instance data available. Check AWS connection.",
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Process each real instance
            for instance_data in real_instance_data:
                instance_name = instance_data["name"]
                instance_type = instance_data["type"] 
                hourly_states = instance_data["hourly_states"]  # List of running/stopped states
                hourly_costs = instance_data["hourly_costs"]    # Real calculated costs
                hours = instance_data["hours"]                  # Time labels
                color = instance_data["color"]
                
                # Add trace for this real instance
                fig.add_trace(go.Scatter(
                    x=hours,
                    y=hourly_costs,
                    mode='lines+markers',
                    name=f"{instance_name} ({instance_type})",
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>{instance_name}</b><br>Time: %{{x}}<br>Cost: $%{{y:.4f}}/hour<br>State: {hourly_states}<extra></extra>'
                ))
            
            fig.update_layout(
                title="Real Instance Costs - Current AWS States & Pricing",
                xaxis_title="Time (Since Launch)",
                yaxis_title="Cost ($/hour)",
                hovermode="x unified",
                plot_bgcolor="white", 
                height=400,
                showlegend=True,
                legend=dict(x=0.02, y=0.98)
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
            
        except Exception as e:
            self.logger.error(f"Error creating real hourly cost chart: {e}")
            fig.add_annotation(
                text=f"Error loading real cost data: {str(e)[:50]}...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            
        return fig

    def create_hourly_carbon_chart(self):
        """Create hourly carbon emissions timeline with real AWS instance data and live carbon intensity."""
        
        fig = go.Figure()
        
        try:
            # Prefer hourly metrics from DynamoDB if available
            real_instance_data = self.get_hourly_metrics_from_dynamodb()
            if not real_instance_data:
                # Fallback to computed hourly data
                real_instance_data = self.get_real_instance_hourly_data()
            
            if not real_instance_data:
                fig.add_annotation(
                    text="No real instance data available. Check AWS connection.",
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Process each real instance
            for instance_data in real_instance_data:
                instance_name = instance_data["name"]
                instance_type = instance_data["type"]
                hourly_states = instance_data["hourly_states"]  # List of running/stopped states
                hourly_carbon = instance_data["hourly_carbon"]  # Real calculated carbon emissions
                hours = instance_data["hours"]                  # Time labels
                color = instance_data["color"]
                
                # Add trace for this real instance
                fig.add_trace(go.Scatter(
                    x=hours,
                    y=hourly_carbon,
                    mode='lines+markers',
                    name=f"{instance_name} ({instance_type})",
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>{instance_name}</b><br>Time: %{{x}}<br>CO₂: %{{y:.4f}} kg/hour<br>State: {hourly_states}<extra></extra>'
                ))
            
            fig.update_layout(
                title="Real Carbon Emissions - Current AWS States & Power Consumption",
                xaxis_title="Time (Since Launch)",
                yaxis_title="CO₂ Emissions (kg/hour)",
                hovermode="x unified",
                plot_bgcolor="white",
                height=400,
                showlegend=True,
                legend=dict(x=0.02, y=0.98)
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
            
        except Exception as e:
            self.logger.error(f"Error creating real hourly carbon chart: {e}")
            fig.add_annotation(
                text=f"Error loading real carbon data: {str(e)[:50]}...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            
        return fig

    def get_hourly_metrics_from_dynamodb(self):
        """Read hourly cost and carbon metrics from DynamoDB if available.

        Expects table items with attributes:
          - instance_id: string
          - timestamp: number (epoch seconds) per hour
          - cost: number (USD for the hour)
          - carbon_kg: number (kg CO₂ for the hour)
        """
        if not self.dynamodb:
            return None

        try:
            from decimal import Decimal
            table_name = settings.aws.hourly_table if settings.aws else "carbon-aware-finops-hourly"
            table = self.dynamodb.Table(table_name)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            resp = table.scan(
                FilterExpression="#t >= :start",
                ExpressionAttributeNames={"#t": "timestamp"},
                ExpressionAttributeValues={":start": int(start_time.timestamp())},
            )
            items = resp.get("Items", [])
            if not items:
                return None

            # Group by instance_id
            by_instance: Dict[str, List[Dict[str, Any]]] = {}
            for it in items:
                iid = str(it.get("instance_id", ""))
                if not iid:
                    continue
                by_instance.setdefault(iid, []).append(it)

            # Resolve instance metadata (names, types, colors)
            meta = self._resolve_instance_meta(list(by_instance.keys()))

            # Build series per instance
            data = []
            for iid, arr in by_instance.items():
                arr = sorted(arr, key=lambda x: int(x.get("timestamp", 0)))
                hours = []
                hourly_costs = []
                hourly_carbon = []
                for it in arr:
                    ts = int(it.get("timestamp", 0))
                    hours.append(datetime.fromtimestamp(ts).strftime("%H:%M"))
                    c = it.get("cost", 0)
                    co2 = it.get("carbon_kg", 0)
                    # Decimal to float
                    if isinstance(c, Decimal):
                        c = float(c)
                    if isinstance(co2, Decimal):
                        co2 = float(co2)
                    try:
                        hourly_costs.append(float(c))
                    except Exception:
                        hourly_costs.append(0.0)
                    try:
                        hourly_carbon.append(float(co2))
                    except Exception:
                        hourly_carbon.append(0.0)

                # Fill metadata
                name = meta.get(iid, {}).get("name", iid)
                inst_type = meta.get(iid, {}).get("type", "?")
                color = meta.get(iid, {}).get("color", "#3498db")
                data.append({
                    "name": name,
                    "type": inst_type,
                    "instance_id": iid,
                    "hours": hours,
                    "hourly_states": ["running" if v > 0 else "stopped" for v in hourly_costs],
                    "hourly_costs": hourly_costs,
                    "hourly_carbon": hourly_carbon,
                    "color": color
                })

            return data

        except Exception as e:
            self.logger.warning(f"Hourly metrics table not available or failed to read: {e}")
            return None

    def _resolve_instance_meta(self, instance_ids: List[str]) -> Dict[str, Dict[str, str]]:
        """Resolve instance names, types, and colors for given instance IDs."""
        meta: Dict[str, Dict[str, str]] = {}
        if not self.ec2 or not instance_ids:
            return meta
        try:
            # Chunk requests if many IDs
            chunk = 50
            for i in range(0, len(instance_ids), chunk):
                ids = instance_ids[i:i+chunk]
                resp = self.ec2.describe_instances(InstanceIds=ids)
                for res in resp.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        iid = inst.get("InstanceId")
                        if not iid:
                            continue
                        name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), iid)
                        inst_type = inst.get("InstanceType", "?")
                        # Color by name pattern
                        color_map = {
                            "web": "#e74c3c",
                            "app": "#e67e22",
                            "db": "#27ae60",
                            "batch": "#2ecc71",
                        }
                        color = "#3498db"
                        for k, v in color_map.items():
                            if k in name_tag.lower():
                                color = v
                                break
                        meta[iid] = {"name": name_tag, "type": inst_type, "color": color}
        except Exception as e:
            self.logger.warning(f"Could not resolve instance metadata: {e}")
        return meta

    def get_real_instance_hourly_data(self):
        """Fetch real AWS instance data for the last 24 hours with costs and carbon calculations."""
        
        if not self.ec2:
            return None
            
        try:
            from datetime import datetime, timedelta
            
            # Define the scheduled instances we want to track
            target_instances = {
                "carbon-aware-finops-web-server": {"name": "Web Server", "type": "t3.medium", "color": "#e74c3c"},
                "carbon-aware-finops-app-server": {"name": "App Server", "type": "t3.large", "color": "#e67e22"},
                "carbon-aware-finops-db-server": {"name": "DB Server", "type": "t3.small", "color": "#27ae60"},
                "carbon-aware-finops-batch-server": {"name": "Batch Server", "type": "t3.micro", "color": "#2ecc71"}
            }
            
            # Get current instance states from AWS
            response = self.ec2.describe_instances(
                Filters=[
                    {"Name": "tag:Project", "Values": ["carbon-aware-finops"]},
                    {"Name": "tag:InstanceRole", "Values": ["Scheduled"]}
                ]
            )
            
            real_instances = {}
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    name_tag = next((tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"), None)
                    if name_tag in target_instances:
                        real_instances[name_tag] = {
                            "instance_id": instance["InstanceId"],
                            "current_state": instance["State"]["Name"],
                            "instance_type": instance["InstanceType"],
                            **target_instances[name_tag]
                        }
            
            # Load today's real daily costs from DynamoDB for these instances
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_costs: Dict[str, float] = {}
            try:
                cost_items = self.get_cost_data()
                for item in cost_items:
                    if str(item.get("date", "")) == today_str:
                        iid = str(item.get("instance_id", ""))
                        try:
                            amt = float(item.get("cost", 0.0))
                        except Exception:
                            amt = 0.0
                        today_costs[iid] = today_costs.get(iid, 0.0) + amt
            except Exception as e:
                self.logger.warning(f"Could not load today's costs: {e}")

            # Generate last 24 hours timeline
            now = datetime.now()
            hours_timeline = []
            for i in range(24):
                hour_time = now - timedelta(hours=23-i)
                hours_timeline.append(hour_time.strftime("%H:%M"))
            
            # Get DynamoDB scheduler history for more accurate state tracking
            scheduler_history = self.get_scheduler_history_last_24h()
            
            # Carbon intensity forecast for next 24h
            try:
                region = settings.aws.region if settings.aws else "eu-central-1"
                fc = CarbonIntensityClient(provider="electricitymap").get_forecast(region, hours=24)
            except Exception:
                fc = [400.0] * 24
            now_hour = now.hour

            instance_data_list = []
            for instance_name, instance_info in real_instances.items():
                instance_type = instance_info["instance_type"]
                current_state = instance_info["current_state"]
                instance_id = instance_info["instance_id"]
                
                # Determine power consumption
                try:
                    power_watts = self.energy_calculator.get_instance_power_consumption(instance_type, cpu_utilization=0.20)
                except Exception:
                    power_watts = 100.0
                
                # Generate hourly states and costs based on current state and scheduler history
                hourly_states = []
                hourly_costs = []
                hourly_carbon = []
                
                # Only show data for actual runtime hours, not fake 24h data
                hours_since_launch = min(24, max(1, len(hours_timeline)))  # At least 1 hour
                
                # Build running mask
                running_mask: List[bool] = []
                for hour_idx in range(hours_since_launch):
                    is_running = current_state == "running"
                    if scheduler_history:
                        try:
                            hour_of_day = int(hours_timeline[hour_idx].split(":")[0])
                        except Exception:
                            hour_of_day = None
                        if hour_of_day is not None and hour_of_day in scheduler_history:
                            shutdowns = scheduler_history[hour_of_day].get("shutdowns", 0)
                            startups = scheduler_history[hour_of_day].get("startups", 0)
                            if shutdowns > 0:
                                is_running = False
                            elif startups > 0:
                                is_running = True
                    running_mask.append(is_running)

                # Allocate daily cost across running hours if we have DynamoDB totals
                daily_cost_total = today_costs.get(instance_id, None)
                running_hours_count = max(1, sum(1 for r in running_mask if r))
                if daily_cost_total is not None:
                    cost_per_running_hour = daily_cost_total / running_hours_count
                else:
                    # fallback to simple on-demand pricing if no cost data
                    pricing = {"t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416, "t3.large": 0.0832}
                    cost_per_running_hour = pricing.get(instance_type, 0.05)

                for hour_idx in range(hours_since_launch):
                    state = "running" if running_mask[hour_idx] else "stopped"
                    cost = cost_per_running_hour if running_mask[hour_idx] else 0.0
                    intensity = fc[hour_idx] if hour_idx < len(fc) else 400.0
                    carbon_kg = ((power_watts / 1000.0) * intensity / 1000.0) if running_mask[hour_idx] else 0.0

                    hourly_states.append(state)
                    hourly_costs.append(cost)
                    hourly_carbon.append(carbon_kg)
                
                # Trim timeline to match actual data
                hours_timeline = hours_timeline[-hours_since_launch:]
                
                instance_data_list.append({
                    "name": instance_info["name"],
                    "type": instance_type,
                    "instance_id": instance_info["instance_id"],
                    "hours": hours_timeline,
                    "hourly_states": hourly_states,
                    "hourly_costs": hourly_costs,
                    "hourly_carbon": hourly_carbon,
                    "color": instance_info["color"]
                })
            
            return instance_data_list
            
        except Exception as e:
            self.logger.error(f"Error fetching real instance hourly data: {e}")
            return None
    
    def get_scheduler_history_last_24h(self):
        """Get scheduler activity from DynamoDB for the last 24 hours."""
        try:
            if not self.dynamodb:
                return None
                
            table = self.dynamodb.Table("carbon-aware-finops-state")
            
            # Query last 24 hours of scheduler activity
            from datetime import datetime, timedelta
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            response = table.scan(
                FilterExpression="attribute_exists(shutdowns) AND #t >= :start",
                ExpressionAttributeNames={"#t": "timestamp"},
                ExpressionAttributeValues={":start": int(start_time.timestamp())}
            )
            
            # Process scheduler history (this is simplified - real implementation would be more complex)
            scheduler_events = {}
            for item in response.get("Items", []):
                if item.get("shutdowns", 0) > 0 or item.get("startups", 0) > 0:
                    timestamp = int(item["timestamp"])
                    hour = datetime.fromtimestamp(timestamp).hour
                    scheduler_events[hour] = {
                        "shutdowns": item.get("shutdowns", 0),
                        "startups": item.get("startups", 0)
                    }
            
            return scheduler_events
            
        except Exception as e:
            self.logger.warning(f"Could not get scheduler history: {e}")
            return None

    def create_instance_status_chart(self):
        """Create instance status pie chart."""

        if not self.ec2:
            # Return empty chart with message
            fig = go.Figure()
            fig.update_layout(
                title="Instance Status - AWS Connection Required",
                annotations=[
                    dict(
                        text="Please ensure AWS SSO is logged in to view instance status",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=False,
                        font=dict(size=16),
                    )
                ],
            )
            return fig
        else:
            try:
                # Get current instance states
                response = self.ec2.describe_instances(
                    Filters=[{"Name": "tag:Project", "Values": ["carbon-aware-finops"]}]
                )

                status_counts = {"running": 0, "stopped": 0, "pending": 0, "stopping": 0}

                for reservation in response["Reservations"]:
                    for instance in reservation["Instances"]:
                        state = instance["State"]["Name"]
                        if state in status_counts:
                            status_counts[state] += 1
            except Exception as e:
                self.logger.error(f"Error getting instance status: {e}")
                status_counts = {"running": 0, "stopped": 0}

        fig = go.Figure(data=[go.Pie(labels=list(status_counts.keys()), values=list(status_counts.values()), hole=0.3)])

        fig.update_layout(
            title="Current Instance Status",
            annotations=[dict(text="Instances", x=0.5, y=0.5, font_size=20, showarrow=False)],
        )

        return fig

    def run(self, debug=True, port=8050, host="127.0.0.1"):
        """Run the dashboard."""
        print(f"🚀 Starting dashboard at http://{host}:{port}")
        print("Press Ctrl+C to stop")
        self.app.run(debug=debug, port=port, host=host)


def main():
    """Main entry point for the dashboard."""
    logger = get_logger("dashboard")
    logger.info("Starting Carbon-Aware FinOps Dashboard")

    dashboard = CarbonFinOpsDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
