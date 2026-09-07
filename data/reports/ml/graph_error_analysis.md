# Phase 2.1: Model Error & Confusion Matrix Analysis

## 1. Confusion Matrix Comparison (Test Set, N = 8,060)

### Tabular XGBoost Confusion Matrix
```text
             Pred Low    Pred Med    Pred High
Actual Low     5536        208         136        
Actual Med     128         1028        334        
Actual High    44          189         457        
```

### Graph-Enhanced XGBoost Confusion Matrix
```text
             Pred Low    Pred Med    Pred High
Actual Low     5539        202         139        
Actual Med     126         1020        344        
Actual High    46          190         454        
```

## 2. High-Risk False Negative Breakdown
- **Total Actual High-Risk Vendors**: `690`
- **Tabular False Negatives**: `233` (Rate: `33.77%`, Pred Low: `44`, Pred Med: `189`)
- **Graph False Negatives**: `236` (Rate: `34.20%`, Pred Low: `46`, Pred Med: `190`)
- **Delta False Negatives**: `+3`

## 3. Discordant Predictions Breakdown
- **Graph Correct while Tabular Incorrect**: `51` instances
- **Tabular Correct while Graph Incorrect**: `59` instances
- **High-Risk Caught by Graph but Missed by Tabular**: `14` instances
- **High-Risk Caught by Tabular but Missed by Graph**: `17` instances
