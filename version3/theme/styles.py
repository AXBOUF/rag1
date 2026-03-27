"""
Design system styles and constants for version3 privacy-aware RAG.
Clean minimal dark theme with emerald accent.
"""

# Color Palette
COLORS = {
    # Primary
    "background": "#1f1f23",
    "surface": "#2d2d31",
    "border": "#374151",
    "accent": "#10b981",
    
    # Text
    "text_primary": "#e5e7eb",
    "text_secondary": "#9ca3af",
    "text_disabled": "#6b7280",
    
    # Semantic
    "success": "#34d399",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "info": "#3b82f6",
    
    # Sensitivity Levels
    "public": "#10b981",
    "internal": "#f59e0b",
    "confidential": "#ef4444",
}

# Custom CSS for Streamlit
CUSTOM_CSS = """
<style>
    /* Global variables */
    :root {
        --primary: #10b981;
        --bg: #1f1f23;
        --surface: #2d2d31;
        --border: #374151;
        --text: #e5e7eb;
        --text-secondary: #9ca3af;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Page background */
    .stApp {
        background-color: var(--bg);
    }
    
    /* Chat messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"] {
        background-color: var(--surface);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    
    /* Input fields */
    .stTextInput input, .stTextArea textarea {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--text);
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 1px var(--primary);
    }
    
    /* Buttons */
    .stButton button {
        background-color: var(--primary);
        color: var(--bg);
        border-radius: 6px;
        border: none;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background-color: #059669;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }
    
    /* Select boxes */
    .stSelectbox select {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--text);
    }
    
    /* Cards */
    .card {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
    }
    
    .badge-public {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid #10b981;
    }
    
    .badge-internal {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid #f59e0b;
    }
    
    .badge-confidential {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
    }
    
    /* Status indicators */
    .status-success { color: #34d399; }
    .status-error { color: #ef4444; }
    .status-warning { color: #f59e0b; }
    .status-info { color: #3b82f6; }
    
    /* Code blocks */
    code {
        background-color: var(--surface);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 13px;
    }
    
    /* Dividers */
    hr {
        border-color: var(--border);
        margin: 24px 0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--surface);
        border-radius: 6px;
    }
</style>
"""

def get_sensitivity_color(level: str) -> str:
    """Get color for sensitivity level."""
    return COLORS.get(level.lower(), COLORS["text_secondary"])

def get_sensitivity_badge_html(level: str) -> str:
    """Generate HTML for sensitivity badge."""
    level_lower = level.lower()
    icon = {
        "public": "🟢",
        "internal": "🟡",
        "confidential": "🔒"
    }.get(level_lower, "❓")
    
    return f'<span class="badge badge-{level_lower}">{icon} {level.upper()}</span>'

def get_role_badge_html(role: str) -> str:
    """Generate HTML for role badge."""
    role_lower = role.lower()
    icon = {
        "employee": "👤",
        "manager": "👔",
        "admin": "👑"
    }.get(role_lower, "👤")
    
    return f'{icon} <strong>{role.title()}</strong>'
