/**
 * @fileoverview EPL Match Predictor — Main React App component.
 *
 * Single-component SPA with three views:
 *   - home       : custom team picker (home + away dropdowns)
 *   - prediction : result of POST /api/predict for the chosen matchup
 *   - metrics    : model evaluation data from GET /api/metrics
 */

import React, { useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const API_BASE = 'http://localhost:5001';

/** Combined team pool across training seasons (keeps promoted/relegated clubs selectable). */
const TEAMS = [
  'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
  'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham',
  'Ipswich', 'Leeds', 'Leicester', 'Liverpool', 'Luton',
  'Man City', 'Man United', 'Newcastle', 'Norwich', "Nott'm Forest",
  'Sheffield United', 'Southampton', 'Tottenham', 'Watford', 'West Ham', 'Wolves',
];


/** Root application component. */
function App() {
  const [view, setView] = useState('home');
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam || homeTeam === awayTeam) return;
    setError(null);
    setPredicting(true);
    try {
      const res = await axios.post(`${API_BASE}/api/predict`, {
        home_team: homeTeam,
        away_team: awayTeam,
      });
      setPrediction(res.data);
      setView('prediction');
    } catch (err) {
      setError(err.response?.data?.error || 'Prediction failed. Please try again.');
    } finally {
      setPredicting(false);
    }
  };

  const handleMetrics = async () => {
    setError(null);
    if (!metrics) {
      setMetricsLoading(true);
      try {
        const res = await axios.get(`${API_BASE}/api/metrics`);
        setMetrics(res.data);
      } catch {
        setError('Could not load model metrics.');
        setMetricsLoading(false);
        return;
      }
      setMetricsLoading(false);
    }
    setView('metrics');
  };

  const canPredict = homeTeam && awayTeam && homeTeam !== awayTeam && !predicting;

  const buildChartData = () => ({
    labels: ['Away Win', 'Draw', 'Home Win'],
    datasets: [
      {
        label: 'Precision',
        data: ['A', 'D', 'H'].map((k) =>
          parseFloat((metrics.classification_report[k].precision * 100).toFixed(1))
        ),
        backgroundColor: 'rgba(255, 255, 255, 0.55)',
        borderColor: 'rgba(255, 255, 255, 0.7)',
        borderWidth: 1,
        borderRadius: 0,
      },
      {
        label: 'Recall',
        data: ['A', 'D', 'H'].map((k) =>
          parseFloat((metrics.classification_report[k].recall * 100).toFixed(1))
        ),
        backgroundColor: 'rgba(160, 130, 210, 0.55)',
        borderColor: 'rgba(160, 130, 210, 0.75)',
        borderWidth: 1,
        borderRadius: 0,
      },
      {
        label: 'F1-Score',
        data: ['A', 'D', 'H'].map((k) =>
          parseFloat((metrics.classification_report[k]['f1-score'] * 100).toFixed(1))
        ),
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        borderColor: 'rgba(255, 255, 255, 0.3)',
        borderWidth: 1,
        borderRadius: 0,
      },
    ],
  });

  const chartOptions = {
    responsive: true,
    animation: false,
    plugins: {
      legend: {
        labels: {
          color: 'rgba(255,255,255,0.55)',
          font: { size: 12 },
        },
      },
      tooltip: {
        callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y}%` },
      },
    },
    scales: {
      x: {
        ticks: { color: 'rgba(255,255,255,0.45)', font: { size: 12 } },
        grid: { color: 'rgba(255,255,255,0.06)' },
      },
      y: {
        min: 0,
        max: 100,
        ticks: {
          color: 'rgba(255,255,255,0.45)',
          font: { size: 11 },
          callback: (v) => v + '%',
        },
        grid: { color: 'rgba(255,255,255,0.06)' },
      },
    },
  };

  return (
    <div className="app">
      <nav className="navbar">
        <button className="nav-brand" onClick={() => setView('home')} aria-label="Go to home">
          <img src="/pl-logo.png" alt="" className="brand-logo" />
          <span className="brand-epl">EPL</span>
          <span className="brand-predictor">Predictor</span>
        </button>
        <button
          className="nav-metrics-btn"
          onClick={handleMetrics}
          disabled={metricsLoading}
        >
          {metricsLoading ? '...' : 'Model Performance'}
        </button>
      </nav>

      <main className="main-content">

        {/* HOME VIEW */}
        {view === 'home' && (
          <section className="view home-view">
            <h1 className="hero-title">Match Predictor</h1>

            {error && (
              <div className="error-banner" role="alert">{error}</div>
            )}

            <div className="picker-card">
              <div className="picker-selects">
                <div className="select-group">
                  <label className="select-label" htmlFor="home-select">Home Team</label>
                  <div className="select-wrap">
                    <select
                      id="home-select"
                      className="team-select"
                      value={homeTeam}
                      onChange={(e) => setHomeTeam(e.target.value)}
                    >
                      <option value="">Choose team...</option>
                      {TEAMS.map((t) => (
                        <option key={t} value={t} disabled={t === awayTeam}>{t}</option>
                      ))}
                    </select>
                    <span className="select-arrow" aria-hidden="true">&#9660;</span>
                  </div>
                </div>

                <div className="vs-divider" aria-hidden="true">vs</div>

                <div className="select-group">
                  <label className="select-label" htmlFor="away-select">Away Team</label>
                  <div className="select-wrap">
                    <select
                      id="away-select"
                      className="team-select"
                      value={awayTeam}
                      onChange={(e) => setAwayTeam(e.target.value)}
                    >
                      <option value="">Choose team...</option>
                      {TEAMS.map((t) => (
                        <option key={t} value={t} disabled={t === homeTeam}>{t}</option>
                      ))}
                    </select>
                    <span className="select-arrow" aria-hidden="true">&#9660;</span>
                  </div>
                </div>
              </div>

              <button
                className={`predict-btn ${canPredict ? '' : 'predict-btn--disabled'}`}
                onClick={handlePredict}
                disabled={!canPredict}
              >
                {predicting ? '...' : 'Predict Match \u2192'}
              </button>
            </div>

            <div className="sample-fixtures">
              <h2 className="section-heading">Sample Fixtures</h2>
              <div className="sample-list">
                {[
                  { home: 'Arsenal',     away: 'Chelsea' },
                  { home: 'Man City',    away: 'Liverpool' },
                  { home: 'Tottenham',   away: 'Newcastle' },
                  { home: 'Aston Villa', away: 'West Ham' },
                  { home: 'Brentford',   away: "Nott'm Forest" },
                ].map((f, i) => (
                  <button
                    key={i}
                    className="sample-row"
                    onClick={() => { setHomeTeam(f.home); setAwayTeam(f.away); }}
                  >
                    <span className="sample-team">{f.home}</span>
                    <span className="sample-vs">vs</span>
                    <span className="sample-team">{f.away}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* PREDICTION VIEW */}
        {view === 'prediction' && prediction && (
          <section className="view prediction-view">
            <button className="back-btn" onClick={() => setView('home')}>
              &larr; New Prediction
            </button>

            <div className="pred-match-header">
              <span className="pred-team">{prediction.home_team}</span>
              <span className="pred-vs">vs</span>
              <span className="pred-team">{prediction.away_team}</span>
            </div>

            <div className="pred-card">
              <div>
                <div className="pred-card-label">Predicted Result</div>
                <div className="pred-outcome">
                  {prediction.prediction}
                </div>
              </div>
              <div className="pred-confidence-block">
                <span className="conf-label">Confidence</span>
                <span className="conf-value">{Math.round(prediction.confidence * 100)}%</span>
              </div>
            </div>

            <div className="prob-section">
              <h2 className="section-heading">Outcome Probabilities</h2>
              <div className="prob-list">
                {Object.entries(prediction.probabilities).map(([label, prob]) => (
                  <div key={label} className="prob-row">
                    <span className="prob-label">{label}</span>
                    <div className="prob-track">
                      <div
                        className="prob-fill"
                        style={{ '--fill-width': `${Math.round(prob * 100)}%` }}
                      />
                    </div>
                    <span className="prob-pct">{Math.round(prob * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="features-section">
              <h2 className="section-heading">Key Factors &mdash; Last 5 Matches</h2>
              <div className="features-table-wrap">
                <table className="features-table">
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>{prediction.home_team} (H)</th>
                      <th>{prediction.away_team} (A)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Form Points</td>
                      <td className="stat-cell">{prediction.features.home_form_points}</td>
                      <td className="stat-cell">{prediction.features.away_form_points}</td>
                    </tr>
                    <tr>
                      <td>Avg Goals Scored</td>
                      <td className="stat-cell">{prediction.features.home_form_goals_scored}</td>
                      <td className="stat-cell">{prediction.features.away_form_goals_scored}</td>
                    </tr>
                    <tr>
                      <td>Avg Goals Conceded</td>
                      <td className="stat-cell">{prediction.features.home_form_goals_conceded}</td>
                      <td className="stat-cell">{prediction.features.away_form_goals_conceded}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* METRICS VIEW */}
        {view === 'metrics' && metrics && (
          <section className="view metrics-view">
            <button className="back-btn" onClick={() => setView('home')}>
              &larr; Back to Predictor
            </button>

            <h1 className="hero-title">Model Performance</h1>
            <p className="hero-sub">
              Random Forest classifier trained on EPL 2021&ndash;24, evaluated on 2024&ndash;25.
            </p>

            <div className="accuracy-hero">
              <span className="acc-label">Test Set Accuracy</span>
              <div className="acc-number">
                {Math.round(metrics.accuracy * 100)}
                <span className="acc-pct-sign">%</span>
              </div>
            </div>

            <div className="metrics-panels">
              <div className="panel">
                <h2 className="section-heading">Confusion Matrix</h2>
                <p className="matrix-note">Rows = Actual, Columns = Predicted</p>
                <div className="matrix-wrap">
                  <table className="confusion-matrix">
                    <thead>
                      <tr>
                        <th></th>
                        <th>Away Win</th>
                        <th>Draw</th>
                        <th>Home Win</th>
                      </tr>
                    </thead>
                    <tbody>
                      {['Away Win', 'Draw', 'Home Win'].map((label, i) => (
                        <tr key={label}>
                          <td className="matrix-label">{label}</td>
                          {metrics.confusion_matrix[i].map((val, j) => (
                            <td
                              key={j}
                              className={`matrix-cell${i === j ? ' diag' : ''}`}
                            >
                              {val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="panel">
                <h2 className="section-heading">Precision, Recall &amp; F1</h2>
                <div className="chart-wrap">
                  <Bar data={buildChartData()} options={chartOptions} />
                </div>
              </div>
            </div>
          </section>
        )}

      </main>
    </div>
  );
}

export default App;
