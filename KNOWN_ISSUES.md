# Known Issues & Limitations

## Current Limitations

### AWS Integration
- CloudTrail events have ~15-minute delay in availability
- Cost Explorer data updates daily, not real-time
- Multi-region support limited to eu-central-1 implementation
- SSO token refresh requires manual re-authentication

### Carbon Intensity Data
- ElectricityMaps API has hourly granularity, not minute-level
- Historical data limited to 48 hours
- No fallback for API outages (no-fallback-policy by design)
- Time alignment coverage depends on data availability

### Calculations
- Power model uses simplified linear scaling (30% idle, 70% variable)
- CPU utilization only - doesn't account for memory, disk, network
- Carbon intensity assumes grid average, not marginal emissions
- No embodied emissions in calculations (operational only)

### Dashboard Performance
- Initial load can take 10-15 seconds with cold cache
- Large instance counts (>50) may slow down processing
- Streamlit refresh triggers full re-computation
- No incremental updates or background workers

### Testing
- Integration tests require live AWS credentials
- Some edge cases not covered (API rate limiting, partial data)
- Mock data in tests may not reflect all real-world scenarios
- No load testing performed

## Future Improvements

### Short-term
- Add caching for Boavizta API calls
- Implement progressive loading for dashboard
- Add more granular error messages
- Support for additional AWS regions

### Medium-term
- Multi-region carbon intensity comparison
- Support for other cloud providers (Azure, GCP)
- Embodied emissions calculations
- Historical trend analysis beyond 48h

### Long-term
- Real-time carbon-aware scheduling recommendations
- Integration with FinOps tools (CloudHealth, Vantage)
- Machine learning for cost/carbon predictions
- Multi-cloud dashboard

## Known Bugs
- None currently identified (but likely exist in edge cases)

## Workarounds

### SSO Token Expired
Run `aws sso login --profile your-profile` to refresh credentials

### Missing Cost Data
Ensure IAM permissions include `AWSCostExplorerReadOnlyAccess`

### Slow Dashboard Load
Use `make dashboard` with cache enabled (default behavior)
