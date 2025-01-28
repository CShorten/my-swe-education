DesinationRule configuration for Istio:

`apiVersion` and `kind` indicate this is an Istio DestinationRule resource, not a standard Kubernetes resource.

DestinationRules are specific to Istio's traffic management features.

`subsets` -- Defines different versions of the service.

Creating "groups" of pods that you can then target with traffic rules. For exapmle, you might want to send 90% of traffic to the Pod with label v1 and 10% of traffic to v2...

-- And route specific users to specific model versions.
