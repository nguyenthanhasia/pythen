# Legal reasoning tutorial

Learn how to turn a hypothetical legal rule into an executable model, evaluate evidence, handle exceptions, and analyze what would change a conclusion. This tutorial uses **PYTHEN 2 v0.2.0a3**, a pinned alpha release.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nguyenthanhasia/pythen/blob/main/tutorials/legal_reasoning/legal_reasoning.ipynb)

The badge targets the notebook on `main` and becomes usable once the tutorial is merged. Until then, upload `legal_reasoning.ipynb` to [Google Colab](https://colab.research.google.com/) or open it locally.

## Learning path

1. Propositions and evidence
2. Conjunction and disjunction
3. Exceptions and defeasible reasoning
4. Rule graphs and exception scope
5. Case assessment and reasoning tables
6. Counterfactuals, witnesses, and verification
7. Candidate restrictions and search budgets
8. Interactive case lab with Colab checkboxes
9. Exhaustive tests for a small rule graph
10. Structural Leap and an independent contract exercise

## Run locally

```bash
python -m pip install "pythen==0.2.0a3" jupyterlab
jupyter lab tutorials/legal_reasoning/legal_reasoning.ipynb
```

Run the notebook cells in order. The first cell installs the pinned version. The notebook contains executable assertions but the committed notebook is cleared of outputs. All examples are hypothetical; they are not jurisdiction-specific legal advice. A missing proposition is not necessarily false in the real world, and a minimum fact addition is not a probability or a legal proof standard.

See the [release](https://github.com/nguyenthanhasia/pythen/releases/tag/v0.2.0a3) and [framework semantics](https://github.com/nguyenthanhasia/pythen/blob/v0.2.0a3/docs/framework_v2.md).
