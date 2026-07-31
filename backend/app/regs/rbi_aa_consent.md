# RBI-AA — Account Aggregator framework: consent and purpose limitation (curated summary)

> Curated prototype summary of the RBI Master Direction on NBFC-Account
> Aggregators and the DEPA consent artefact standard. Not verbatim law.

## §1 Consent artefact
Financial information may be fetched only under a valid, machine-readable
consent artefact specifying the data types, date range, purpose, frequency and
expiry. The consent must exist BEFORE any data is pulled, and the fetch must
reference the consent identifier.

## §2 Purpose limitation
Data obtained under an Account Aggregator consent may be used solely for the
declared purpose (here: working-capital underwriting) and must not be
repurposed or resold. Access must stop when the consent expires or is revoked.

## §3 Auditability
Every fetch against a consent must be logged with the consent reference, so
the data trail from consent to credit decision is reconstructable end to end.
