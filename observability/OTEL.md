# OpenTelemetry (OTEL): A Technical Overview

## What It Is

OpenTelemetry (commonly abbreviated **OTel** or **OTEL**) is an open-source observability framework — a collection of APIs, SDKs, and tools used to instrument, generate, collect, and export telemetry data from software systems. It is a Cloud Native Computing Foundation (CNCF) project, formed in 2019 from the merger of two earlier projects: OpenTracing and OpenCensus.

The core problem OTel solves is *vendor lock-in for telemetry*. Before OTel, instrumenting an application for one observability backend (Datadog, New Relic, Jaeger, etc.) typically meant writing code tied to that vendor's SDK. OTel provides a standardized, vendor-neutral way to produce telemetry, which can then be shipped to any compatible backend.

## The Three Signals

OTel is organized around three primary types of telemetry data, often called "signals":

**Traces** capture the path of a request as it flows through a distributed system. A trace is composed of *spans*, where each span represents a unit of work (an HTTP call, a database query, a function execution) with a start time, duration, attributes, and a parent-child relationship to other spans. Traces are essential for debugging latency and understanding service dependencies.

**Metrics** are numerical measurements aggregated over time — counters, gauges, histograms. Examples include request rate, error rate, CPU utilization, queue depth. Metrics are cheap to store and ideal for dashboards and alerting.

**Logs** are timestamped records of discrete events. OTel's logging support arrived later than traces and metrics but is now stable; it focuses on correlating logs with traces and metrics via shared context (trace IDs, span IDs).

A fourth signal, **profiles** (continuous profiling data), is in development but not yet stable across all languages.

## Architecture

The OTel ecosystem has a few key components worth understanding:

The **API** is what application code calls — `tracer.start_span()`, `meter.create_counter()`, etc. It is intentionally minimal and stable, so library authors can instrument their libraries without forcing a specific implementation on downstream users.

The **SDK** is the implementation behind the API. It handles sampling, batching, context propagation, and export. You configure the SDK in your application's startup code.

The **OTLP** (OpenTelemetry Protocol) is the wire format for shipping telemetry. It's a gRPC and HTTP/protobuf protocol that most modern observability vendors now accept natively.

The **Collector** is a standalone agent (written in Go) that sits between your applications and your backend. It receives telemetry (typically over OTLP), processes it (filtering, batching, enrichment, sampling), and exports it to one or more destinations. The Collector is one of the most useful pieces of the ecosystem because it decouples your application from your backend choice — switching from Jaeger to Tempo to Datadog becomes a Collector config change rather than an application redeploy.

## Why It Matters

For someone working on infrastructure or services — especially anything touching memory services, query agents, or multi-component pipelines — OTel is increasingly the default answer for observability. Engram's observability work, for instance, would naturally lean on OTel for tracing memory operations across the extract → buffer → aggregate → transform → commit pipeline you've described, since each stage is a natural span boundary and the trace context can carry tenant/project IDs as attributes.

The practical benefits: instrument once, ship anywhere; correlate traces with metrics and logs through shared context; and avoid rewriting instrumentation when you change vendors or add a second backend.

## Current State (2026)

Traces, metrics, and logs are all stable (GA) across the major language SDKs (Go, Python, Java, JavaScript/Node, .NET, Rust is maturing). OTLP is the de facto standard ingestion protocol. Most observability vendors — Datadog, Grafana, Honeycomb, New Relic, Splunk, etc. — accept OTLP directly, and many have shifted their own SDKs to be OTel-based or OTel-compatible.

The active frontiers are continuous profiling, semantic conventions for AI/LLM workloads (spans for model calls, token counts as attributes, prompt/completion capture), and improvements to the Collector's processing pipeline.

## Further Reading

The canonical entry points are [opentelemetry.io](https://opentelemetry.io) for documentation and the [OpenTelemetry GitHub org](https://github.com/open-telemetry) for source code and specifications. The semantic conventions repo is particularly useful when instrumenting a new domain — it standardizes attribute names so traces from different services remain queryable in a uniform way.
