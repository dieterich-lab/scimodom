"""Administration services.

Rules:

- These services only orchestrate: Domain logic stays in the domain services.
- Dependencies: administration services may use domain services, but domain
  services must never import from this package.
- No user interface. Use cases that modify data are split into a validating
  step without side effects, and an `execute` step that returns a result object.
  Failures that leave work partially done are reported with an exception.
"""
