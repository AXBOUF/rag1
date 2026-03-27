"""
Design system styles and constants for version3 privacy-aware RAG.
Apple-inspired dark theme with clean, minimal aesthetics.
"""

# Apple Dark Mode Color Palette
COLORS = {
    # Primary backgrounds
    "background": "#000000",           # Pure black (Apple dark bg)
    "surface": "#1c1c1e",              # Elevated surface
    "surface_elevated": "#2c2c2e",     # Cards, modals
    "border": "#38383a",               # Subtle borders
    
    # Accent (Apple Blue)
    "accent": "#0a84ff",               # Apple blue
    "accent_hover": "#409cff",         # Lighter on hover
    
    # Text
    "text_primary": "#f5f5f7",         # Primary text (Apple off-white)
    "text_secondary": "#86868b",       # Secondary text
    "text_tertiary": "#48484a",        # Disabled/muted
    
    # Semantic
    "success": "#30d158",              # Apple green
    "error": "#ff453a",                # Apple red
    "warning": "#ffd60a",              # Apple yellow
    "info": "#0a84ff",                 # Apple blue
    
    # Sensitivity Levels (Apple-style)
    "public": "#30d158",               # Apple green
    "internal": "#ff9f0a",             # Apple orange
    "confidential": "#ff453a",         # Apple red
}

# Custom CSS for Streamlit - Apple Dark Theme
CUSTOM_CSS = """
<style>
    /* Apple Dark Mode Variables */
    :root {
        --apple-black: #000000;
        --apple-surface: #1c1c1e;
        --apple-surface-elevated: #2c2c2e;
        --apple-border: #38383a;
        --apple-blue: #0a84ff;
        --apple-blue-hover: #409cff;
        --apple-text: #f5f5f7;
        --apple-text-secondary: #86868b;
        --apple-green: #30d158;
        --apple-red: #ff453a;
        --apple-orange: #ff9f0a;
        --apple-yellow: #ffd60a;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer {
        visibility: hidden;
    }
    
    /* Keep header visible for sidebar toggle */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Sidebar toggle button - ensure visible */
    button[kind="header"] {
        color: var(--apple-text) !important;
    }
    
    /* Global background */
    .stApp {
        background-color: var(--apple-black);
    }
    
    /* Main content area */
    .main .block-container {
        background-color: var(--apple-black);
        padding-top: 2rem;
    }
    
    /* Login/Register card container */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        padding: 2rem;
    }
    
    .login-card {
        background: var(--apple-surface);
        border: 1px solid var(--apple-border);
        border-radius: 16px;
        padding: 2.5rem;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-logo {
        width: 64px;
        height: 64px;
        margin: 0 auto 1rem;
        background: linear-gradient(135deg, var(--apple-blue), #5856d6);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
    }
    
    .login-title {
        color: var(--apple-text);
        font-size: 24px;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .login-subtitle {
        color: var(--apple-text-secondary);
        font-size: 14px;
        margin-top: 8px;
    }
    
    .login-divider {
        border: none;
        border-top: 1px solid var(--apple-border);
        margin: 1.5rem 0;
    }
    
    .login-footer {
        text-align: center;
        color: var(--apple-text-secondary);
        font-size: 13px;
    }
    
    .login-footer a {
        color: var(--apple-blue);
        text-decoration: none;
    }
    
    /* Sidebar - Apple style */
    [data-testid="stSidebar"] {
        background-color: var(--apple-surface) !important;
        border-right: 1px solid var(--apple-border);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: var(--apple-surface);
    }
    
    /* Sidebar header */
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--apple-text);
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* All text */
    .stMarkdown, .stText, p, span, label {
        color: var(--apple-text);
    }
    
    /* Secondary text */
    .stCaption, caption, small {
        color: var(--apple-text-secondary) !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: var(--apple-surface);
        border-radius: 18px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: none;
    }
    
    [data-testid="stChatMessageContent"] {
        background-color: transparent;
    }
    
    /* User message */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: var(--apple-blue);
    }
    
    /* Chat input */
    .stChatInputContainer {
        background-color: var(--apple-surface) !important;
        border: 1px solid var(--apple-border);
        border-radius: 22px;
    }
    
    .stChatInputContainer textarea {
        background-color: transparent !important;
        color: var(--apple-text) !important;
        border: none !important;
    }
    
    /* Input fields */
    .stTextInput input, 
    .stTextArea textarea,
    .stNumberInput input {
        background-color: var(--apple-surface-elevated) !important;
        border: 1px solid var(--apple-border) !important;
        border-radius: 10px !important;
        color: var(--apple-text) !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput input:focus, 
    .stTextArea textarea:focus {
        border-color: var(--apple-blue) !important;
        box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.3) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: var(--apple-surface-elevated) !important;
        border: 1px solid var(--apple-border) !important;
        border-radius: 10px !important;
        color: var(--apple-text) !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background-color: var(--apple-surface-elevated);
    }
    
    /* Buttons - Apple style pill buttons */
    .stButton button {
        background-color: var(--apple-blue) !important;
        color: white !important;
        border-radius: 980px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
        letter-spacing: -0.01em;
    }
    
    .stButton button:hover {
        background-color: var(--apple-blue-hover) !important;
        transform: scale(1.02);
    }
    
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: var(--apple-surface-elevated);
        border: 2px dashed var(--apple-border);
        border-radius: 12px;
        padding: 20px;
    }
    
    .stFileUploader:hover {
        border-color: var(--apple-blue);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--apple-blue) !important;
        border-radius: 4px;
    }
    
    /* Dividers */
    hr, .stDivider {
        border-color: var(--apple-border) !important;
        opacity: 0.5;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--apple-surface-elevated) !important;
        border-radius: 10px !important;
        color: var(--apple-text) !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--apple-surface) !important;
        border: 1px solid var(--apple-border);
        border-radius: 0 0 10px 10px;
    }
    
    /* Alerts/Info boxes */
    .stAlert {
        background-color: var(--apple-surface-elevated) !important;
        border: 1px solid var(--apple-border) !important;
        border-radius: 12px !important;
        color: var(--apple-text) !important;
    }
    
    /* Success message */
    .stSuccess {
        background-color: rgba(48, 209, 88, 0.1) !important;
        border-color: var(--apple-green) !important;
    }
    
    /* Error message */
    .stError {
        background-color: rgba(255, 69, 58, 0.1) !important;
        border-color: var(--apple-red) !important;
    }
    
    /* Warning message */
    .stWarning {
        background-color: rgba(255, 214, 10, 0.1) !important;
        border-color: var(--apple-yellow) !important;
    }
    
    /* Info message */
    .stInfo {
        background-color: rgba(10, 132, 255, 0.1) !important;
        border-color: var(--apple-blue) !important;
    }
    
    /* Checkbox */
    .stCheckbox label span {
        color: var(--apple-text) !important;
    }
    
    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 980px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
        letter-spacing: -0.01em;
    }
    
    .badge-public {
        background-color: rgba(48, 209, 88, 0.15);
        color: #30d158;
        border: 1px solid rgba(48, 209, 88, 0.3);
    }
    
    .badge-internal {
        background-color: rgba(255, 159, 10, 0.15);
        color: #ff9f0a;
        border: 1px solid rgba(255, 159, 10, 0.3);
    }
    
    .badge-confidential {
        background-color: rgba(255, 69, 58, 0.15);
        color: #ff453a;
        border: 1px solid rgba(255, 69, 58, 0.3);
    }
    
    /* Code blocks */
    code {
        background-color: var(--apple-surface-elevated);
        padding: 3px 8px;
        border-radius: 6px;
        font-family: 'SF Mono', 'Menlo', monospace;
        font-size: 13px;
        color: var(--apple-text);
    }
    
    /* Scrollbar - Apple style thin */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--apple-black);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--apple-border);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--apple-text-secondary);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--apple-blue) transparent transparent transparent !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--apple-text) !important;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--apple-text-secondary) !important;
    }
</style>
"""

def get_sensitivity_color(level: str) -> str:
    """Get color for sensitivity level."""
    return COLORS.get(level.lower(), COLORS["text_secondary"])

def get_sensitivity_badge_html(level: str) -> str:
    """Generate HTML for sensitivity badge."""
    level_lower = level.lower()
    return f'<span class="badge badge-{level_lower}">{level.upper()}</span>'

def get_role_badge_html(role: str) -> str:
    """Generate HTML for role badge."""
    return f'<strong>{role.upper()}</strong>'
