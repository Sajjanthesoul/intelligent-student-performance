# Explainability roadmap:
# 1. Extract tree-based featureImportances from the fitted RandomForest model.
# 2. Preserve the feature-index mapping from StringIndexer/OneHotEncoder/VectorAssembler.
# 3. For local explanations, use a sampled model-compatible SHAP workflow.
# 4. Document the background sample and computational constraints.
# Feature importance and SHAP values describe model associations, not causation.
