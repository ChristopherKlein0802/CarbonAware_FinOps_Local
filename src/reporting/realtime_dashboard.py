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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.logging_config import get_logger, LoggerMixin
from src.utils.retry_handler import AWSRetrySession, exponential_backoff, safe_aws_call
from src.config.settings import settings


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
            self.ce = self.aws_session.get_client("ce")
            self.ec2 = self.aws_session.get_client("ec2")

            self.logger.info(f"AWS clients initialized successfully with profile: {self.aws_profile}")
        except Exception as e:
            self.logger.warning(f"AWS clients initialization failed with profile '{self.aws_profile}': {e}")
            self.logger.info("Please run: aws sso login --profile carbon-finops-sandbox")
            # Initialize as None to handle offline mode
            self.aws_session = None
            self.dynamodb = None
            self.cloudwatch = None
            self.ce = None
            self.ec2 = None

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
            return cached_data

        if not self.dynamodb:
            return None

        try:
            table = self.dynamodb.Table(table_name)
            response = safe_aws_call(table.scan)

            if response:
                data = response.get("Items", [])
                # Cache the result
                self.cache.set(cache_key, data)
                return data

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
            return cached_kpis

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
                # KPI Cards Row
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("Cost Savings", style={"color": "#27ae60"}),
                                        html.H2(id="cost-savings", children="$0"),
                                        html.P("This Month", style={"color": "#7f8c8d"}),
                                    ],
                                    className="kpi-card",
                                ),
                            ],
                            className="four columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("CO₂ Reduction", style={"color": "#2ecc71"}),
                                        html.H2(id="carbon-reduction", children="0 kg"),
                                        html.P("This Month", style={"color": "#7f8c8d"}),
                                    ],
                                    className="kpi-card",
                                ),
                            ],
                            className="four columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("Optimized Instances", style={"color": "#3498db"}),
                                        html.H2(id="optimized-instances", children="0"),
                                        html.P("Active Now", style={"color": "#7f8c8d"}),
                                    ],
                                    className="kpi-card",
                                ),
                            ],
                            className="four columns",
                        ),
                    ],
                    className="row",
                ),
                # Charts Row
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(id="cost-timeline"),
                            ],
                            className="six columns",
                        ),
                        html.Div(
                            [
                                dcc.Graph(id="carbon-timeline"),
                            ],
                            className="six columns",
                        ),
                    ],
                    className="row",
                ),
                # Recommendations Table
                html.Div(
                    [html.H3("Active Recommendations"), html.Div(id="recommendations-table")], style={"margin": "20px"}
                ),
                # Instance Status
                html.Div([html.H3("Instance Status"), dcc.Graph(id="instance-status-chart")], style={"margin": "20px"}),
                # Auto-refresh
                dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),  # Update every minute
            ]
        )

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [
                Output("cost-savings", "children"),
                Output("carbon-reduction", "children"),
                Output("optimized-instances", "children"),
                Output("cost-timeline", "figure"),
                Output("carbon-timeline", "figure"),
                Output("recommendations-table", "children"),
                Output("instance-status-chart", "figure"),
            ],
            [Input("interval-component", "n_intervals")],
        )
        def update_dashboard(_n_intervals):
            # Get current metrics
            metrics = self.get_current_metrics()

            # Update KPIs
            cost_savings = f"${metrics['cost_savings']:.2f}"
            carbon_reduction = f"{metrics['carbon_reduction']:.1f} kg"
            optimized_count = str(metrics["optimized_instances"])

            # Create timeline charts
            cost_fig = self.create_cost_timeline()
            carbon_fig = self.create_carbon_timeline()

            # Create recommendations table
            recommendations_table = self.create_recommendations_table()

            # Create instance status char
            status_fig = self.create_instance_status_chart()

            return (
                cost_savings,
                carbon_reduction,
                optimized_count,
                cost_fig,
                carbon_fig,
                recommendations_table,
                status_fig,
            )

    def get_current_metrics(self):
        """Get current metrics from DynamoDB and CloudWatch."""

        # Default values for offline mode
        default_metrics = {
            "cost_savings": 0,
            "carbon_reduction": 0,
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
            total_shutdowns = sum(item.get("shutdowns", 0) for item in response.get("Items", []))
            total_startups = sum(item.get("startups", 0) for item in response.get("Items", []))

            # Estimate savings (simplified)
            cost_per_hour = 0.05  # Average cost per instance hour
            carbon_per_hour = 0.2  # kg CO2 per instance hour

            hours_saved = total_shutdowns * 8

            return {
                "cost_savings": hours_saved * cost_per_hour,
                "carbon_reduction": hours_saved * carbon_per_hour,
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

            return dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={"textAlign": "left"},
                style_data_conditional=[
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
                ],
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
