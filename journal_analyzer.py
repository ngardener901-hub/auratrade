<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraTrade | AI Trading Assistant for MES/MNQ Futures</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0a0e1a;
            color: #ffffff;
            line-height: 1.6;
            min-height: 100vh;
        }
        .hero {
            text-align: center;
            padding: 60px 20px 40px;
            background: radial-gradient(ellipse at top, rgba(0,212,255,0.08) 0%, transparent 60%);
        }
        .hero h1 {
            font-size: 3.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #00d4ff 0%, #0088ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .hero .subtitle {
            font-size: 1.15rem;
            color: rgba(255,255,255,0.55);
            max-width: 600px;
            margin: 0 auto 30px;
        }
        .badge-row {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        .badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-blue {
            background: rgba(0,212,255,0.12);
            color: #00d4ff;
            border: 1px solid rgba(0,212,255,0.25);
        }
        .badge-red {
            background: rgba(255,51,102,0.12);
            color: #ff3366;
            border: 1px solid rgba(255,51,102,0.25);
        }
        .badge-green {
            background: rgba(0,255,136,0.12);
            color: #00ff88;
            border: 1px solid rgba(0,255,136,0.25);
        }
        .preview-img {
            max-width: 900px;
            width: 90%;
            margin: 0 auto 40px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            display: block;
        }
        .section {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .section h2 {
            font-size: 1.6rem;
            margin-bottom: 20px;
            color: #00d4ff;
        }
        .section p {
            color: rgba(255,255,255,0.65);
            margin-bottom: 16px;
            font-size: 1rem;
        }
        .deploy-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        @media (min-width: 640px) {
            .deploy-grid { grid-template-columns: 1fr 1fr; }
        }
        .deploy-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 24px;
        }
        .deploy-card h3 {
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: #ffffff;
        }
        .deploy-card ol {
            color: rgba(255,255,255,0.55);
            font-size: 0.9rem;
            padding-left: 18px;
        }
        .deploy-card li {
            margin-bottom: 8px;
        }
        .btn {
            display: inline-block;
            padding: 14px 32px;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        .btn-primary {
            background: linear-gradient(135deg, #00d4ff, #0088ff);
            color: #0a0e1a;
            box-shadow: 0 4px 20px rgba(0,212,255,0.25);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,212,255,0.4);
        }
        .btn-secondary {
            background: rgba(255,255,255,0.06);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.15);
            margin-left: 12px;
        }
        .btn-secondary:hover {
            background: rgba(255,255,255,0.1);
        }
        .cta-row {
            text-align: center;
            margin: 30px 0;
        }
        .features {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            margin-top: 20px;
        }
        @media (min-width: 640px) {
            .features { grid-template-columns: 1fr 1fr 1fr; }
        }
        .feature {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .feature-icon {
            font-size: 1.8rem;
            margin-bottom: 10px;
        }
        .feature h4 {
            font-size: 0.95rem;
            margin-bottom: 6px;
            color: #ffffff;
        }
        .feature p {
            font-size: 0.82rem;
            color: rgba(255,255,255,0.5);
            margin: 0;
        }
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255,255,255,0.3);
            font-size: 0.85rem;
            border-top: 1px solid rgba(255,255,255,0.06);
            margin-top: 40px;
        }
        code {
            background: rgba(0,212,255,0.1);
            color: #00d4ff;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.85em;
        }
        .warning {
            background: rgba(255,51,102,0.08);
            border: 1px solid rgba(255,51,102,0.2);
            border-radius: 10px;
            padding: 16px 20px;
            margin: 20px 0;
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
        }
        .warning strong {
            color: #ff3366;
        }
    </style>
</head>
<body>
    <div class="hero">
        <h1>AURA TRADE</h1>
        <p class="subtitle">AI Trading Assistant for MES/MNQ Futures. Regime-aware. Prop-firm safe. Built from 11 sessions of proven edge.</p>
        <div class="badge-row">
            <span class="badge badge-blue">Trend Runner</span>
            <span class="badge badge-red">Trap & Revert</span>
            <span class="badge badge-green">FVG + VWAP Confluence</span>
        </div>
        <img src="dashboard_preview.png" alt="AuraTrade Dashboard Preview" class="preview-img">
        <div class="cta-row">
            <a href="#deploy" class="btn btn-primary">Deploy to Streamlit Cloud (Free)</a>
            <a href="https://github.com/new" target="_blank" class="btn btn-secondary">Create GitHub Repo</a>
        </div>
    </div>

    <div class="section">
        <h2>Three Non-Negotiable Rules</h2>
        <div class="features">
            <div class="feature">
                <div class="feature-icon">1</div>
                <h4>Level Reclaim + FVG Retest</h4>
                <p>Price MUST reclaim London/NYAM level, create an FVG, and retest it. No retest = No trade.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">2</div>
                <h4>VWAP Filter (Blue Days)</h4>
                <p>On Tue/Wed/Thu, ONLY long above VWAP and short below it. Counter-trend entries blocked.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">3</div>
                <h4>Remove Quickly (9-EMA)</h4>
                <p>If price closes on the opposite side of the 9-EMA, the AI kills the trade instantly regardless of stop.</p>
            </div>
        </div>
    </div>

    <div class="section" id="deploy">
        <h2>1-Click Deploy to Streamlit Cloud</h2>
        <p>Streamlit Community Cloud is <strong>free</strong> and lets you run Python apps directly from GitHub. Access AuraTrade from any browser or phone.</p>

        <div class="warning">
            <strong>Before deploying:</strong> This app connects to the Tradovate API for live futures trading. Only deploy with <strong>demo credentials</strong> until you fully test the logic. The $300 daily stop and $2,000 drawdown guardrails are active by default.
        </div>

        <div class="deploy-grid">
            <div class="deploy-card">
                <h3>Option A: Manual Deploy (Recommended)</h3>
                <ol>
                    <li>Create a <strong>public</strong> GitHub repo (e.g., <code>auratrade</code>)</li>
                    <li>Upload all files from the <code>auratrade/</code> folder</li>
                    <li>Go to <a href="https://streamlit.io/cloud" target="_blank" style="color:#00d4ff;">streamlit.io/cloud</a></li>
                    <li>Click "New app" &rarr; select your repo</li>
                    <li>Set <strong>Main file path</strong> to <code>main.py</code></li>
                    <li>Add your Tradovate credentials in <strong>Secrets</strong></li>
                    <li>Click Deploy</li>
                </ol>
            </div>
            <div class="deploy-card">
                <h3>Option B: Deploy from Template</h3>
                <ol>
                    <li>Fork the repo (create your own copy)</li>
                    <li>Connect Streamlit Cloud to your fork</li>
                    <li>Update <code>.streamlit/secrets.toml</code> with your API keys</li>
                    <li>Deploy automatically on every git push</li>
                    <li>Free tier: 1 CPU, 1GB RAM, unlimited public apps</li>
                    <li>App sleeps after 7 days of inactivity (wake on visit)</li>
                </ol>
            </div>
        </div>

        <h2 style="margin-top:40px;">Secrets Setup</h2>
        <p>In Streamlit Cloud, go to your app &rarr; Settings &rarr; Secrets. Paste your Tradovate credentials:</p>
        <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:16px 20px;font-family:'SF Mono',monospace;font-size:0.82rem;color:rgba(255,255,255,0.6);margin:16px 0;overflow-x:auto;">
[tradovate]<br>
TRADOVATE_USERNAME = "your_username"<br>
TRADOVATE_PASSWORD = "your_password"<br>
TRADOVATE_BASE_URL = "https://demo.tradovateapi.com/v1"<br>
TRADOVATE_CID = "your_contract_id"r>
TRADOVATE_ACCOUNT_ID = "your_account_id"
        </div>
    </div>

    <div class="section">
        <h2>System Architecture</h2>
        <div class="features">
            <div class="feature">
                <div class="feature-icon">&#x2699;</div>
                <h4>Regime Classifier</h4>
                <p>BLUE (Tue/Wed/Thu) vs RED (Mon/Fri) with market structure confirmation and cautious sub-regimes.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F4C8;</div>
                <h4>FVG Detector</h4>
                <p>3-candle displacement pattern. Bullish/bearish gap detection with retest validation and age tracking.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F6E1;</div>
                <h4>Risk Guard</h4>
                <p>$300 daily stop. Max 2 trades/session. $2K trailing drawdown. Intraday unrealized PnL monitoring.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F4CB;</div>
                <h4>AI Journal</h4>
                <p>Pattern-matches each trade against your 11-chart training set with human-readable success analysis.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x26A1;</div>
                <h4>OCO Brackets</h4>
                <p>Atomic entry + stop + target orders via Tradovate API. Broker-side protection even if app crashes.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F4F1;</div>
                <h4>Mobile Ready</h4>
                <p>Streamlit apps are responsive. Monitor positions, view signals, and read journal entries from your phone.</p>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>AuraTrade &mdash; Built from 11 proven trading sessions &mdash; Prop Firm Safe by Design</p>
        <p style="margin-top:8px;font-size:0.75rem;">Not financial advice. Futures trading involves substantial risk of loss. Always test in simulation before live deployment.</p>
    </div>
</body>
</html>
