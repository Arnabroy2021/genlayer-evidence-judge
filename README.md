# GenLayer Evidence Adjudicator

A substantive GenLayer Intelligent Contract that adjudicates a real-world
claim using two independent public web sources and validator consensus.

## What problem it solves

A user submits:

- a natural-language claim;
- Source A URL;
- Source B URL.

The contract:

1. Fetches both sources inside a GenLayer non-deterministic execution.
2. Uses an LLM to classify the claim as `SUPPORTED`, `REFUTED`, or `UNCERTAIN`.
3. Produces a confidence score and evidence-grounded rationale.
4. Has validators independently fetch the same sources and independently
   derive the verdict.
5. Accepts the leader result only when validators agree on the verdict and
   are reasonably close on confidence.
6. Stores the consensus-approved result on-chain.

This is intentionally more than a number-returning demo: the consensus
decision controls whether a substantive evidence judgment is accepted.

## Contract

The complete contract logic is in `contract.py`.

Main write method:

`adjudicate(claim, source_a, source_b)`

Main read method:

`get_result()`

## Example use case

Claim:

`The latest public release of Project X includes feature Y.`

Source A:

`https://example.com/project-release`

Source B:

`https://example.com/project-documentation`

The contract independently evaluates both sources and reaches a consensus
decision.

## Consensus design

The leader and each validator independently:

- retrieve Source A;
- retrieve Source B;
- ask the LLM to make the same structured judgment.

The validator does NOT merely check that the leader returned valid JSON.
It independently recomputes the judgment from the external evidence.

Consensus requires:

- identical `verdict`;
- confidence scores within 20 points.

Rationale text is not required to match word-for-word because natural
language explanations are inherently non-deterministic.

## Why this uses GenLayer meaningfully

The core application decision depends on:

- external web data;
- non-deterministic LLM interpretation;
- independent validator verification;
- an on-chain state update only after consensus.

The design follows GenLayer's recommended pattern for non-deterministic
LLM/web workflows: perform external work inside a non-deterministic block,
independently verify the leader result, and perform storage writes only after
consensus.

## Submission checklist

Before submitting this repository:

1. Keep `contract.py` at repository root.
2. Keep this `README.md` at repository root.
3. Test the contract in GenLayer Studio.
4. Confirm `adjudicate()` executes successfully.
5. Confirm `get_result()` returns the stored verdict.
6. Submit the public GitHub repository URL as the Builder evidence.

## Important

Use stable, reputable public sources when testing. Avoid pages that require
login, personalized sessions, CAPTCHAs, or rapidly changing content.
