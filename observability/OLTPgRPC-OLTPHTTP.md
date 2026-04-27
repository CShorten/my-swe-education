# OTLP/gRPC vs OTLP/HTTP: Choosing a Transport for OpenTelemetry

## Context: What OTLP Is

OTLP (OpenTelemetry Protocol) is the wire format OpenTelemetry uses to ship telemetry — traces, metrics, logs — from instrumented applications to collectors and from collectors to backends like Dash0, Honeycomb, Datadog, Grafana Tempo/Mimir/Loki, and so on. The protocol is defined as a set of Protocol Buffer (protobuf) message schemas in the [opentelemetry-proto](https://github.com/open-telemetry/opentelemetry-proto) repo, with three top-level service definitions: `TraceService`, `MetricsService`, and `LogsService`.

What OTLP doesn't fully prescribe is *how* those protobuf messages get over the wire. The OTel specification defines two officially supported transport variants:

- **OTLP/gRPC** — protobuf over gRPC over HTTP/2.
- **OTLP/HTTP** — protobuf (or JSON) over plain HTTP/1.1 or HTTP/2.

Both carry identical telemetry payloads. The difference is purely in the transport layer, and the choice between them comes down to deployment constraints, performance characteristics, and client/server library support.

## OTLP/gRPC

### What It Is

OTLP/gRPC uses gRPC as the RPC framework. The protobuf service definitions in the spec compile directly into gRPC client and server stubs. A client calls `Export()` on the appropriate service stub (`TraceService.Export`, `MetricsService.Export`, `LogsService.Export`), passing a request that batches multiple records into one call. The server responds with an `ExportResponse` indicating success, partial success (some records rejected), or failure.

The default port is **4317**, and the default URL path scheme is the gRPC convention: `/<service>/<method>` (e.g., `/opentelemetry.proto.collector.trace.v1.TraceService/Export`).

### Wire Characteristics

gRPC sits on HTTP/2, which gives it a few specific properties:

**Binary framing.** Headers and payloads are binary, with HPACK-compressed headers. This is meaningfully smaller than HTTP/1.1's text headers, especially when shipping high volumes of small batches.

**Multiplexing on a single connection.** Multiple in-flight RPC calls share one TCP/TLS connection. For a busy exporter sending traces, metrics, and logs concurrently, this avoids the connection-pool overhead you'd see with HTTP/1.1.

**Built-in compression.** gRPC negotiates per-message compression (typically gzip) at the framing layer, separately from any TLS-level compression.

**Streaming RPC support.** The protocol *can* support streaming, though the OTLP spec uses unary RPCs (request/response) rather than streaming exports. Worth noting because it occasionally comes up as a future direction.

**Strict status semantics.** gRPC has its own status codes (`OK`, `UNAVAILABLE`, `RESOURCE_EXHAUSTED`, etc.) distinct from HTTP status codes, and the OTLP spec maps retry behavior to specific gRPC statuses cleanly.

### When It Works Well

OTLP/gRPC is the default choice when you control both ends of the connection — your application talking to your own collector, or your collector talking to a backend that you've configured. It performs well, the libraries are mature in every supported language, and the connection-reuse properties matter at high telemetry volumes.

### Where It Gets Awkward

The friction with gRPC tends to be operational rather than technical:

**HTTP/2 requirement.** Some load balancers, proxies, and corporate egress points don't handle HTTP/2 cleanly, particularly older AWS ALB configurations, certain WAFs, and ingress controllers that were originally designed for HTTP/1.1 traffic. End-to-end HTTP/2 (including ALPN negotiation) needs to actually work for gRPC to work.

**Browser environments.** Browsers can't speak gRPC directly — they need gRPC-Web with a proxy. This rules out OTLP/gRPC for shipping telemetry from a browser-side OTel SDK, which is one of the main reasons OTLP/HTTP exists.

**Stricter network requirements.** Long-lived HTTP/2 connections need stable network paths; aggressive idle-timeout settings on intermediate proxies can cause connection churn.

**Library size.** The gRPC runtime is non-trivial in some languages (notably JavaScript and Python), which matters for serverless and constrained environments.

## OTLP/HTTP

### What It Is

OTLP/HTTP carries the same protobuf messages over plain HTTP, using a simple POST per export. Each signal has its own URL path:

- `/v1/traces` for spans
- `/v1/metrics` for metric data
- `/v1/logs` for log records

The default port is **4318**. The request body is either binary protobuf (with `Content-Type: application/x-protobuf`) or JSON (`Content-Type: application/json`). The JSON encoding is defined by the protobuf JSON mapping spec, so the same schemas describe both formats.

### Wire Characteristics

OTLP/HTTP is, deliberately, much simpler:

**Plain HTTP semantics.** Status codes are standard HTTP (200 OK, 4xx for client errors, 5xx for server errors with retry semantics defined by `Retry-After`). Any tool that handles HTTP handles this — load balancers, proxies, debuggers, `curl`.

**No HTTP/2 requirement.** It runs over HTTP/1.1 or HTTP/2 transparently, depending on what the client and server negotiate.

**JSON option.** Useful for debugging — you can `curl` an OTLP/HTTP endpoint with hand-written JSON and see what the server does. The binary protobuf is still the production default for size and speed reasons, but the JSON option makes the protocol much more approachable.

**Stateless.** Each POST is independent. Connection reuse via HTTP keep-alive helps, but there's no protocol-level multiplexing.

### When It Works Well

OTLP/HTTP is the right choice when:

**You're shipping telemetry from a browser.** gRPC isn't an option; OTLP/HTTP (often with CORS configured on the receiving collector) is the only path.

**You're behind infrastructure that doesn't speak HTTP/2 cleanly.** Older API gateways, certain corporate proxies, some cloud load balancers in their default configurations.

**You're in a serverless or constrained environment** where adding the gRPC runtime is a meaningful binary-size or cold-start cost.

**You need to debug the wire.** Capturing OTLP/HTTP traffic with standard tools is significantly easier than decoding HTTP/2 framed gRPC.

**Your backend only accepts HTTP.** Some vendors offer OTLP/HTTP ingestion but not OTLP/gRPC, or vice versa. Dash0, Honeycomb, Grafana Cloud, and most modern backends support both, but it's worth checking.

### Where It Gets Awkward

The trade-offs go the other direction:

**Higher per-request overhead.** Text headers, no built-in multiplexing, JSON (if you choose it) is meaningfully larger than protobuf. At very high telemetry volumes, this shows up as more egress bytes and more CPU on both ends.

**Less polished retry semantics.** The spec defines retry behavior, but the mapping is a little less crisp than gRPC's status-code-driven model.

## Practical Comparison

| Dimension | OTLP/gRPC | OTLP/HTTP |
|---|---|---|
| Default port | 4317 | 4318 |
| Transport | gRPC over HTTP/2 | HTTP/1.1 or HTTP/2 |
| Payload format | Protobuf binary | Protobuf binary or JSON |
| URL scheme | One service endpoint per signal type, RPC-style paths | `/v1/traces`, `/v1/metrics`, `/v1/logs` |
| Connection model | Long-lived, multiplexed | Per-request (with keep-alive) |
| Header overhead | Low (HPACK compression) | Higher (text headers) |
| Browser support | No (needs gRPC-Web proxy) | Yes (with CORS) |
| Debugging | Harder (binary HTTP/2 framing) | Easier (`curl`-able, JSON option) |
| Library footprint | Larger (gRPC runtime) | Smaller (just HTTP) |
| Streaming | Supported by gRPC, not used by OTLP | N/A |

## How to Choose

A reasonable default decision tree:

**Inside a backend cluster, app-to-collector or collector-to-collector?** Use OTLP/gRPC. The performance and connection-reuse properties matter, and you control the network path.

**Crossing a corporate egress, third-party load balancer, or unfamiliar network?** Try OTLP/gRPC first; if HTTP/2 turns out to be a fight, fall back to OTLP/HTTP. The performance difference matters less than reliability when you have one shot through a proxy you don't control.

**From a browser?** OTLP/HTTP, no other option.

**From a serverless function with cold-start sensitivity?** OTLP/HTTP, especially in JavaScript/Python where the gRPC runtime has noticeable startup cost.

**Into a SaaS backend like Dash0, Honeycomb, Grafana Cloud?** Either works for most vendors. Check their docs for which they recommend; some have better-tuned ingest paths for one over the other. The vendor-recommended path is usually the right call.

**Mixed environment?** A common production pattern is OTLP/gRPC from apps to a local OpenTelemetry Collector (running as a sidecar or DaemonSet), then OTLP/HTTP from the Collector out to the SaaS backend. The Collector terminates the gRPC connection, batches and processes the data, and re-exports over whatever the backend prefers — getting you the best of both transports.

## A Note on Configuration

The OpenTelemetry SDKs follow standard environment variables for transport selection:

- `OTEL_EXPORTER_OTLP_PROTOCOL` — `grpc`, `http/protobuf`, or `http/json`
- `OTEL_EXPORTER_OTLP_ENDPOINT` — the URL or host:port (interpretation depends on protocol)
- `OTEL_EXPORTER_OTLP_HEADERS` — for auth tokens (commonly `Authorization=Bearer …` or vendor-specific keys)

Per-signal overrides exist as well (`OTEL_EXPORTER_OTLP_TRACES_PROTOCOL`, etc.), which is occasionally useful — you might ship traces over gRPC for performance and logs over HTTP because your log backend only accepts HTTP.

Most SDKs default to OTLP/gRPC if you don't specify, which is the right default for backend services but the wrong one for browser-side or serverless code, where you'll want to override explicitly.

## Where It Fits

Both transports carry identical telemetry — the choice is about how the bytes move, not what they mean. OTLP/gRPC is the high-throughput, infrastructure-controlled default; OTLP/HTTP is the universal-compatibility fallback that also happens to be the only option in browser and some serverless contexts. For most production architectures you'll end up using both: gRPC inside the cluster, HTTP at the edge or out to vendor backends, with a Collector in the middle terminating one and originating the other.

The protocol's deliberate split into two transports is one of OTel's better design choices — it would have been tempting to standardize on gRPC alone, but doing so would have cut out browser telemetry entirely and made adoption much harder in environments where HTTP/2 is operationally awkward. Having both, with identical payload semantics, means you almost never have to argue about which transport — you pick whichever fits the network you're on and move on.
