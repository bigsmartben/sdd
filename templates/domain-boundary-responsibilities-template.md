# Domain Boundary Responsibilities: [PROJECT]

**Projection Type**: Repository-First Projection  
**Canonical Path**: `.specify/memory/repository-first/domain-boundary-responsibilities.md`  
**Primary Evidence**: Source anchors only (`path::symbol`)

Use this artifact to document domain-boundary responsibilities backed by source anchors.
This artifact MUST stay at domain-boundary granularity and MUST NOT model dependency direction.

## Evidence Rules

- Boundary conclusions MUST be anchored in source-code files/symbols.
- Engineering assembly manifests, planning artifacts, and helper docs are supporting inputs only and MUST NOT replace source anchors.
- Missing source evidence MUST remain explicit as `TODO(REPO_ANCHOR)` and forward-looking.

## Boundary Responsibility Matrix

| Domain Boundary | Responsibilities | Core Entity Anchors (`path::symbol`) | 2nd-Party Collaboration Anchor |
|----------------|------------------|---------------------------------------|--------------------------------|
| [Boundary A] | [Normative responsibility statements using MUST/SHOULD] | [`src/domain/a.py::EntityA`, `src/domain/a_service.py::AService`] | [`src/integration/vendor_client.py::VendorClient`] |
| [Boundary B] | [Normative responsibility statements using MUST/SHOULD] | [`src/domain/b.py::EntityB`] | [`src/integration/external_api.py::ExternalApi`] |

## Boundary Notes

- Do not infer responsibilities from path names alone.
- Do not encode module invocation direction (`allowed`/`forbidden`) here; use `.specify/memory/repository-first/module-invocation-spec.md` for invocation governance.
