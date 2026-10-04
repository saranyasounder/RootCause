# RootCause
## Known Limitations

- **Equipment ID extraction uses substring matching against known IDs, not NLP.**
  It does not parse negation — e.g., "My error is on a different unit, not SVR-R740-01"
  will incorrectly match SVR-R740-01. This is a deliberate simplicity tradeoff: the
  router's structured path is designed to avoid LLM calls entirely for speed/cost,
  which rules out true intent parsing. Caught via adversarial test case during
  development (see `test_router.py`).