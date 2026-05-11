# Signal Channels

Signals channels are a Temporal workflow primitive for sending data to a running workflow from the outside.

A Temporal workflow is a long-lied, durable function. Unlike a normal HTTP handler that runs once and returns, this pipeline workflow starts up and then sits in a loop waiting for wrok. Signal channels are how that work gets delivered.

Think of them like Go channels, but durable - they survive process restarts, server crashes, etc. Temopral persists the signasl and replays them.

The signals are sent from Temporal `activities` (normal functions that run outsid the workflow).
