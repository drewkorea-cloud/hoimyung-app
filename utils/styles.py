def get_css():
    return """
    <style>
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
        font-size: 20px !important;
    }
    .stMarkdown p, .stMarkdown li {
        font-size: 20px !important;
        line-height: 1.6 !important;
        color: #2D3748 !important;
    }
    button[data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #718096 !important;
        background-color: #F7FAFC !important;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px !important; 
        margin-right: 8px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #2E86C1 !important;
        border: none !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 22px !important;
        font-weight: 700 !important;
        padding: 12px 5px !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 30px !important;
        font-weight: 900 !important;
    }
    .stNumberInput label, .stTextInput label, .stSelectbox label, .stSlider label {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #1A202C !important;
        margin-bottom: 10px !important;
    }
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] div {
        font-size: 20px !important;
        font-weight: 600 !important;
        min-height: 45px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 20px !important;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        font-size: 38px !important;
        font-weight: 900 !important;
        color: #2563EB !important;
    }
    h1, h2, h3 {
        font-weight: 800 !important;
        color: #2C3E50 !important;
    }
    h3 { font-size: 26px !important; }
    [data-testid="stDataFrame"] {
        font-size: 18px !important;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 2px solid #E2E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
    }
    </style>
    """