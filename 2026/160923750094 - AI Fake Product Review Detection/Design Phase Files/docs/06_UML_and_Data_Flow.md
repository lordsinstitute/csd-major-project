# 6. UML Diagrams and Data Flow

All diagrams are in the `diagrams/` folder. The editable Mermaid sources are in `diagrams/src/`.

## 6.1 Use case diagram
![Use case diagram](../diagrams/01_use_case.png)

## 6.2 Data flow diagram
![Data flow diagram](../diagrams/05_data_flow_diagram.png)

| Process | Input | Output |
|---|---|---|
| 1.0 Accept input | Review text, behaviour numbers or CSV file | Raw review(s) |
| 2.0 Preprocess | Raw review(s) | Cleaned text as TF-IDF numbers |
| 3.0 Predict | TF-IDF numbers, saved model (D2) | Fake probability |
| 4.0 Score | Fake probability, behaviour risk | Trust score, level, user trust, bot status |
| 5.0 Explain | TF-IDF numbers, explainer weights (D2) | Reasons, top words, highlighted text |
| 6.0 Display | Scores and explanations | Gauge, tables, charts, downloads |
| 7.0 Train | Reviews dataset (D1) | Model files saved to D2 |

## 6.3 Class diagram
The code is mostly small functions in modules. They are shown as classes to describe responsibilities. `Analyzer` is the only real class.

![Class diagram](../diagrams/06_class_diagram.png)

## 6.4 Sequence diagrams

### Check one review
![Sequence: check one review](../diagrams/07_sequence_single_review.png)

### Check a CSV file
![Sequence: check a CSV file](../diagrams/08_sequence_csv.png)

### Train the model
![Sequence: train the model](../diagrams/09_sequence_training.png)
