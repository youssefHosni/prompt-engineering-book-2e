# Six previous releases

Examples, not templates. They exist so the model can match register without
being told about register in the prompt.

## v4.2.0

### Added
- Exports include the order reference.
- Depot filters accept multiple values.

### Fixed
- Surcharge rounded to the nearest penny rather than truncating.

## v4.1.1

### Fixed
- Delivery estimates no longer skip weekends twice.

## v4.1.0

### Added
- Saved searches on the consignment list.

### Changed
- The consignment list defaults to the last 30 days, not all time.

## v4.0.0

### Breaking
- `GET /orders` returns `ref` instead of `order_id`. Update clients before upgrading.

### Added
- Pagination on every list endpoint.

## v3.9.2

### Fixed
- Timezone handling on collections booked after 23:00.

## v3.9.1

### Needs description
- PR #4412 "fix the thing" — no description, author unavailable.
