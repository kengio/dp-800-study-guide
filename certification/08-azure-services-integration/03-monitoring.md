---
title: Monitoring Azure SQL and Fabric SQL
type: study-material
tags:
  - dp-800
  - azure-monitor
  - application-insights
  - log-analytics
---

# Monitoring Azure SQL and Fabric SQL

## Overview

Azure Monitor is the unified monitoring platform for Azure services. For SQL databases, monitoring covers query performance, resource utilization, errors, and availability. Key components are: **Diagnostic Settings** (send metrics/logs to destinations), **Log Analytics** (query logs with KQL), **Application Insights** (application-level telemetry), and **Query Performance Insight** (query-level analysis).

> [!abstract]
> - Covers Azure Monitor metrics, DMV-based diagnostics, Query Store for plan monitoring, and alerting setup
> - Monitoring combines Azure-level metrics (Azure Monitor) with SQL-level diagnostics (DMVs, Query Store)
> - Key exam topics: which DMV for which scenario, Query Store for regression detection, Azure Monitor alert rules

> [!tip] What the Exam Tests
> - `sys.dm_exec_requests` = currently running queries + blocking info; `sys.dm_os_wait_stats` = cumulative wait statistics
> - Query Store detects **plan regressions** automatically with Automatic Plan Correction (`FORCE_LAST_GOOD_PLAN`)
> - Azure Monitor metrics (CPU, DTU, storage) come from the Azure platform; DMVs come from inside the database engine — both are needed for full visibility

---

## Azure Monitor for SQL

### Diagnostic Settings

Diagnostic settings route Azure SQL metrics and logs to Log Analytics, Event Hub, or Storage:

```text
Azure SQL Database → Monitoring → Diagnostic Settings → Add Diagnostic Setting

Categories to enable:
├── SQLInsights          ← detailed query telemetry (requires Intelligent Insights)
├── AutomaticTuning      ← automatic index/plan changes
├── QueryStoreRuntimeStatistics  ← Query Store data
├── QueryStoreWaitStatistics     ← Query Store waits
├── Errors               ← error log entries
├── DatabaseWaitStatistics       ← wait stats by category
├── Timeouts             ← query timeouts
├── Blocks               ← blocking events
└── Deadlocks            ← deadlock graphs

Destinations:
├── Send to Log Analytics workspace
├── Archive to Storage Account
└── Stream to Event Hub
```

### Key Metrics

Azure SQL exposes these metrics via Azure Monitor (viewable in Metrics blade):

| Metric | Description | Alert Threshold |
| :--- | :--- | :--- |
| `cpu_percent` | DTU/vCore CPU usage | > 80% sustained |
| `dtu_consumption_percent` | DTU utilization (DTU model) | > 80% |
| `storage_percent` | Database size vs max | > 85% |
| `connection_successful` | Successful connections/sec | Monitor for drops |
| `connection_failed` | Failed connections/sec | > 0 is concerning |
| `deadlock` | Deadlocks/sec | ==> 0 requires investigation== |
| `workers_percent` | Worker threads used | > 80% |
| `sessions_percent` | Sessions used vs max | > 80% |

---

## Log Analytics and KQL

### Connecting to Log Analytics

After enabling diagnostic settings to send to a Log Analytics workspace, query using KQL:

```kql
-- Navigate to Log Analytics workspace → Logs
-- Or: Azure SQL → Monitoring → Logs
```

### KQL Queries for SQL Monitoring

```kql
// Top CPU-consuming queries (from QueryStoreRuntimeStatistics)
AzureDiagnostics
| where Category == "QueryStoreRuntimeStatistics"
| where ResourceType == "SERVERS/DATABASES"
| project TimeGenerated, query_id_d, avg_cpu_time_d, count_executions_d,
          avg_duration_d, DatabaseName = Resource
| top 20 by avg_cpu_time_d desc
```

```kql
// Deadlock events in the last 24 hours
AzureDiagnostics
| where Category == "Deadlocks"
| where TimeGenerated >= ago(24h)
| project TimeGenerated, Resource, deadlock_xml_s
| order by TimeGenerated desc
```

```kql
// Failed connections over time
AzureMetrics
| where MetricName == "connection_failed"
| where TimeGenerated >= ago(7d)
| summarize TotalFailures = sum(Total) by bin(TimeGenerated, 1h), Resource
| render timechart
```

```kql
// Database CPU utilization over time
AzureMetrics
| where MetricName == "cpu_percent"
| where TimeGenerated >= ago(24h)
| summarize AvgCPU = avg(Average), MaxCPU = max(Maximum)
    by bin(TimeGenerated, 5m), Resource
| render timechart
```

```kql
// Wait statistics breakdown
AzureDiagnostics
| where Category == "DatabaseWaitStatistics"
| where TimeGenerated >= ago(1h)
| summarize TotalWaitMs = sum(delta_wait_time_ms_d) by wait_type_s
| top 10 by TotalWaitMs desc
| render barchart
```

```kql
// Query timeout events
AzureDiagnostics
| where Category == "Timeouts"
| where TimeGenerated >= ago(24h)
| project TimeGenerated, Resource, error_number_d, query_hash_s
| summarize TimeoutCount = count() by query_hash_s, Resource
| top 20 by TimeoutCount desc
```

```kql
// Blocking events
AzureDiagnostics
| where Category == "Blocks"
| where TimeGenerated >= ago(1h)
| project TimeGenerated, Resource, duration_d, blocked_process_report_s
| order by duration_d desc
```

---

## Application Insights Integration

Application Insights captures application-level telemetry including SQL dependency calls made from application code.

### SQL Dependency Tracking

When using Azure SDK or Entity Framework with Application Insights, SQL queries are tracked as dependencies:

```text
Application Insights → Performance → Dependencies → SQL
Shows:
- Query execution time (per query type)
- Failure rate
- Call volume
- End-to-end request traces including SQL calls
```

### Custom Telemetry from SQL

```sql
-- Log custom events from within SQL using sp_invoke_external_rest_endpoint
-- (Azure SQL Managed Instance or SQL Database)
DECLARE @body NVARCHAR(MAX) = N'{
    "name": "LongRunningQuery",
    "properties": {
        "duration_ms": 5000,
        "query_hash": "abc123",
        "database": "MyDB"
    }
}';

EXEC sp_invoke_external_rest_endpoint
    @url = 'https://dc.services.visualstudio.com/v2/track',
    @method = 'POST',
    @headers = '{"Content-Type":"application/json"}',
    @payload = @body;
```

### KQL in Application Insights

```kql
// Slow SQL dependencies from Application Insights
dependencies
| where type == "SQL"
| where duration > 1000  -- slower than 1 second
| summarize AvgDuration = avg(duration), CallCount = count()
    by name, target
| top 20 by AvgDuration desc
```

```kql
// SQL failure rate
dependencies
| where type == "SQL"
| where timestamp >= ago(1h)
| summarize Total = count(), Failures = countif(success == false)
    by bin(timestamp, 5m)
| extend FailureRate = Failures * 100.0 / Total
| render timechart
```

---

## Query Performance Insight

Query Performance Insight (QPI) in the Azure portal is a visual interface over Query Store data:

```text
Azure SQL Database → Intelligent Performance → Query Performance Insight

Views:
├── Long Running Queries    ← top queries by total duration
├── Top Resource Consumers  ← top by CPU, data I/O, log I/O
└── Custom                  ← configure time range and metric

For each query:
├── View the query text
├── View execution plan
├── See resource trend over time
└── Get index recommendations
```

### Enabling Query Performance Insight

QPI requires Query Store to be enabled:

```sql
-- Ensure Query Store is enabled and in READ_WRITE mode
ALTER DATABASE MyDB SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 1000,
    INTERVAL_LENGTH_MINUTES = 60
);

-- Verify
SELECT name, is_query_store_on FROM sys.databases WHERE name = 'MyDB';
```

---

## Setting Up Alerts

```text
Azure Monitor → Alerts → Create Alert Rule

Signal types for Azure SQL:
├── Metric: cpu_percent > 80% for 5 minutes → Alert
├── Metric: deadlock > 0 → Alert (any occurrence)
├── Log (KQL): Deadlocks category → count > 0 → Alert
└── Log (KQL): Errors category → severity = critical → Alert

Action Groups:
├── Email/SMS notification
├── Logic App trigger
├── Azure Function trigger
└── Webhook
```

### Alert Rule via Azure CLI

```bash
# Create a CPU alert for Azure SQL Database
az monitor metrics alert create \
  --name "HighCPU-Alert" \
  --resource-group myRG \
  --scopes "/subscriptions/{sub}/resourceGroups/myRG/providers/Microsoft.Sql/servers/myserver/databases/MyDB" \
  --condition "avg cpu_percent > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group "/subscriptions/{sub}/resourceGroups/myRG/providers/Microsoft.Insights/actionGroups/DBATeam" \
  --description "Alert when CPU exceeds 80% for 5 minutes"
```

---

## Intelligent Insights

Intelligent Insights uses built-in intelligence to detect performance anomalies:

```text
Azure SQL → Intelligent Performance → Intelligent Insights

Detects:
├── Reaching resource limits (CPU, I/O, log)
├── Increased database parallelism
├── Schema issues (missing indexes, locking)
├── Plan regression
└── Tempdb contention

Output: JSON diagnostic log (send via Diagnostic Settings to Log Analytics)
```

```kql
// Query Intelligent Insights diagnostics
AzureDiagnostics
| where Category == "SQLInsights"
| where status_s == "Active"
| project TimeGenerated, Resource, rootCauseAnalysis_s, impact_s
| order by TimeGenerated desc
```

---

## Use Cases

- **Proactive alerting**: CPU/storage alerts notify DBA team before users experience slowdowns
- **Query Store + QPI**: Identify and investigate top resource-consuming queries in the Azure portal
- **Log Analytics KQL**: Correlate deadlocks, blocks, and timeouts across time windows
- **Application Insights**: Trace end-to-end request latency including database time in application code

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| No data in Log Analytics | Diagnostic settings not enabled | ==Enable diagnostic settings and wait 15 minutes for data to flow== |
| QPI shows no data | Query Store disabled or in READ_ONLY | Enable Query Store: `ALTER DATABASE ... SET QUERY_STORE = ON` |
| KQL returns 0 rows | Wrong category name or time range | Check category spelling; expand time range |
| Metrics blade empty | Data not yet available | Metrics have ~1 minute latency; logs have ~5 minute latency |

---

## Exam Tips

- **Diagnostic Settings** must be configured to route logs to Log Analytics — no data flows without this step
- **Query Performance Insight** requires Query Store to be `ON` in `READ_WRITE` mode
- KQL `AzureDiagnostics` table contains all diagnostic log data — filter by `Category` to find specific log types
- `AzureMetrics` table contains metric data (CPU, DTU, storage) — use for time-series analysis
- **Intelligent Insights** automatically detects anomalies — more automated than manual KQL alerting

---

## Key Takeaways

- Azure Monitor collects metrics and logs; Log Analytics stores them; KQL queries them
- Enable Diagnostic Settings first — without them, no SQL telemetry reaches Log Analytics
- Query Performance Insight is the fastest way to find top resource consumers in Azure SQL
- Application Insights tracks SQL as dependency calls — connects database time to user-facing latency

---

## Related Topics

- [01-Data API Builder](./01-data-api-builder.md)
- [04-Change & Event Handling](./04-change-event-handling.md)
- [03-Query Performance Troubleshooting](../06-performance-optimization/03-query-performance-troubleshooting.md)

---

## Official Documentation

- [Azure SQL Monitoring](https://learn.microsoft.com/en-us/azure/azure-sql/database/monitoring-overview)
- [Log Analytics with Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/metrics-diagnostic-telemetry-logging-streaming-export-configure)
- [Query Performance Insight](https://learn.microsoft.com/en-us/azure/azure-sql/database/query-performance-insight-use)
- [Intelligent Insights](https://learn.microsoft.com/en-us/azure/azure-sql/database/intelligent-insights-overview)

---

**[← Previous](./02-rest-graphql-endpoints.md) | [↑ Back to Section](./README.md) | [Next →](./04-change-event-handling.md)**
