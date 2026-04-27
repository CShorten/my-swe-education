## Temporal Interceptors and OpenTelemetry: Preserving Trace Context Across Workflow Boundaries

### The Core Problem: Why Traces Break at Temporal

To understand why interceptors matter, it helps to first see why the trace breaks without them.
OpenTelemetry trace context propagation works by passing a small piece of metadata — typically a traceparent header (W3C Trace Context) containing the trace ID, parent span ID, and flags — alongside the work being done. When an HTTP server receives a request, the otelhttp instrumentation reads traceparent from the incoming headers and uses it as the parent for any spans the server creates. That's how the trace stays connected across a network call.
Temporal, however, isn't HTTP. When your API handler calls client.ExecuteWorkflow(...), the SDK serializes the workflow invocation and pushes it onto the Temporal server (the cluster), where it's persisted as a task in a queue. Some time later — could be milliseconds, could be hours — a worker process polls that task queue, picks up the task, and runs the workflow. There is no synchronous network call from your API to the worker. The two processes are decoupled in both space and time.

By default, Temporal has no idea that an OTel trace context exists in your API's memory. It serializes the workflow inputs you gave it, stores them, and hands them to a worker later. The worker, when it starts executing the workflow, has no parent span to point at — so the OTel SDK does what it's designed to do in that situation: it creates a fresh root span. You end up with two disconnected traces:

```
Trace A (API):
HTTP /v1/memories
  └─ StartWorkflow:PipelineWorkflow   [ends here]

Trace B (Worker, orphaned):
RunWorkflow:PipelineWorkflow          [new root span]
  ├─ RunActivity:ExtractStep
  ├─ RunActivity:TransformStep
  └─ RunActivity:CommitStep
```
