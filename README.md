# EPL-Match-Predictor

A Premier League match predictor developed as my Computer Science senior capstone project CMPS490. This application uses historical match data and machine learning algorithms to predict match outcomes.

## Project Overview

- **Backend**: Python/Flask REST API with scikit-learn for predictions
- **Frontend**: React single-page application with interactive visualizations
- **Database**: SQLite with EPL match data from 2021-22 through 2023-24
- **ML Model**: Random Forest classifier trained on historical match statistics

## Repository Structure

```
backend/
  etl.py              # Data pipeline: downloads CSVs and creates SQLite database
  requirements.txt    # Python dependencies
  data/               # Raw CSV files from football-data.co.uk
    2021-22.csv
    2022-23.csv
    2023-24.csv
  epl_data.db         # SQLite database
README.md           
```
### Prerequisites
- Python 3.11+
- pip
