"""
UI utilities for the Legal AI Marketing Assistant.

This module provides reusable UI components and helpers for the Streamlit interface,
promoting consistent UI patterns and reducing duplication.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
import pandas as pd
import uuid

# Standard legal practice areas
PRACTICE_AREAS = [
    "Administrative Law",
    "Business & Corporate Law",
    "Civil Law", 
    "Criminal Law",
    "Employment & Labor Law",
    "Estate Law",
    "Family Law",
    "Immigration Law",
    "Intellectual Property Law",
    "Real Estate Law",
    "Tax Law",
    "Other"
]

# Standard content formats
CONTENT_FORMATS = [
    "Article",
    "Blog Post",
    "Video",
    "Podcast",
    "Infographic",
    "Newsletter",
    "Webinar",
    "Case Study",
    "Guide",
    "FAQ",
    "White Paper",
    "Social Media Post",
    "Other"
]


def info_expander(title: str, content: str, expanded: bool = False) -> None:
    """
    Create a standard information expander component.
    
    Args:
        title: Title for the expander
        content: Markdown content to display inside the expander
        expanded: Whether the expander should be initially expanded
    """
    with st.expander(title, expanded=expanded):
        st.markdown(content)


def practice_area_selector(
    label: str = "Practice Area",
    default: List[str] = None,
    key: Optional[str] = None,
    multiple: bool = True
) -> Union[List[str], str]:
    """
    Standardized practice area selection component.
    
    Args:
        label: Label for the selection widget
        default: Default selected values
        key: Unique key for the widget
        multiple: Whether to allow multiple selections
        
    Returns:
        List of selected practice areas (if multiple=True) or a single practice area (if multiple=False)
    """
    if key is None:
        key = f"practice_area_{uuid.uuid4()}"
    
    if multiple:
        return st.multiselect(
            label, 
            PRACTICE_AREAS, 
            default=default or [],
            key=key
        )
    else:
        return st.selectbox(
            label,
            PRACTICE_AREAS,
            index=0 if default is None or not default else PRACTICE_AREAS.index(default[0]),
            key=key
        )


def content_format_selector(
    label: str = "Content Format",
    default: Optional[str] = None,
    key: Optional[str] = None
) -> str:
    """
    Standardized content format selection component.
    
    Args:
        label: Label for the selection widget
        default: Default selected value
        key: Unique key for the widget
        
    Returns:
        Selected content format
    """
    if key is None:
        key = f"content_format_{uuid.uuid4()}"
    
    index = 0
    if default is not None and default in CONTENT_FORMATS:
        index = CONTENT_FORMATS.index(default)
    
    return st.selectbox(
        label,
        CONTENT_FORMATS,
        index=index,
        key=key
    )


def content_form(
    on_submit: Callable[[Dict[str, Any]], None],
    initial_values: Dict[str, Any] = None,
    form_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Standard content input form.
    
    Args:
        on_submit: Callback function to call with form data when submitted
        initial_values: Initial values for form fields
        form_key: Unique key for the form
        
    Returns:
        Form data if submitted, None otherwise
    """
    initial_values = initial_values or {}
    
    if form_key is None:
        form_key = f"content_form_{uuid.uuid4()}"
    
    with st.form(form_key):
        title = st.text_input(
            "Title",
            value=initial_values.get("title", "")
        )
        
        description = st.text_area(
            "Description",
            value=initial_values.get("description", "")
        )
        
        practice_area = practice_area_selector(
            default=initial_values.get("practice_area", []),
            key=f"{form_key}_practice_area"
        )
        
        content_format = content_format_selector(
            default=initial_values.get("content_format"),
            key=f"{form_key}_content_format"
        )
        
        # Optional fields based on presence in initial_values
        fields = {}
        
        if "url" in initial_values:
            fields["url"] = st.text_input(
                "URL",
                value=initial_values.get("url", "")
            )
        
        if "author" in initial_values:
            fields["author"] = st.text_input(
                "Author",
                value=initial_values.get("author", "")
            )
        
        if "publication_date" in initial_values:
            fields["publication_date"] = st.date_input(
                "Publication Date",
                value=initial_values.get("publication_date")
            )
        
        if "tags" in initial_values:
            fields["tags"] = st.text_input(
                "Tags (comma-separated)",
                value=", ".join(initial_values.get("tags", []))
            )
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            result = {
                "title": title,
                "description": description,
                "practice_area": practice_area,
                "content_format": content_format,
                **fields
            }
            
            # Process tags if provided
            if "tags" in fields:
                result["tags"] = [tag.strip() for tag in fields["tags"].split(",") if tag.strip()]
            
            on_submit(result)
            return result
    
    return None


def display_dataframe(
    df: pd.DataFrame,
    title: Optional[str] = None,
    use_container_width: bool = True,
    height: Optional[int] = None,
    column_config: Optional[Dict[str, Dict[str, Any]]] = None
) -> None:
    """
    Display a DataFrame with consistent styling.
    
    Args:
        df: DataFrame to display
        title: Optional title to display above the DataFrame
        use_container_width: Whether to use the full container width
        height: Optional height for the dataframe
        column_config: Optional column configuration
    """
    if title:
        st.subheader(title)
    
    if df is None or df.empty:
        st.info("No data available.")
        return
    
    st.dataframe(
        df,
        use_container_width=use_container_width,
        height=height,
        column_config=column_config
    )


def status_indicator(
    status: str,
    statuses: Dict[str, Tuple[str, str]] = None
) -> None:
    """
    Display a status indicator with consistent color coding.
    
    Args:
        status: Status to display
        statuses: Optional mapping of status values to (color, icon) tuples
    """
    if statuses is None:
        statuses = {
            "success": ("green", "✅"),
            "error": ("red", "❌"),
            "warning": ("orange", "⚠️"),
            "info": ("blue", "ℹ️"),
            "pending": ("gray", "⏳")
        }
    
    color, icon = statuses.get(
        status.lower(),
        ("gray", "•")
    )
    
    st.markdown(
        f"<span style='color: {color};'>{icon} {status}</span>",
        unsafe_allow_html=True
    )


def section_header(title: str, description: Optional[str] = None) -> None:
    """
    Display a consistent section header.
    
    Args:
        title: Section title
        description: Optional section description
    """
    st.markdown(f"## {title}")
    
    if description:
        st.markdown(f"*{description}*")
    
    st.markdown("---")


def action_button(
    label: str,
    key: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None
) -> bool:
    """
    Display a consistently styled action button.
    
    Args:
        label: Button label
        key: Unique key for the button
        help_text: Optional hover help text
        icon: Optional icon name
        
    Returns:
        True if the button was clicked, False otherwise
    """
    if key is None:
        key = f"button_{label.lower().replace(' ', '_')}_{uuid.uuid4()}"
    
    kwargs = {"key": key}
    if help_text:
        kwargs["help"] = help_text
    if icon:
        kwargs["type"] = "primary"
        kwargs["use_container_width"] = False
        return st.button(f":{icon}: {label}", **kwargs)
    else:
        return st.button(label, **kwargs)


def error_message(message: str) -> None:
    """
    Display a consistently styled error message.
    
    Args:
        message: Error message to display
    """
    st.error(message)


def success_message(message: str) -> None:
    """
    Display a consistently styled success message.
    
    Args:
        message: Success message to display
    """
    st.success(message)


def warning_message(message: str) -> None:
    """
    Display a consistently styled warning message.
    
    Args:
        message: Warning message to display
    """
    st.warning(message)


def info_message(message: str) -> None:
    """
    Display a consistently styled info message.
    
    Args:
        message: Info message to display
    """
    st.info(message)


def tabs_container(tabs: Dict[str, Callable[[], None]]) -> None:
    """
    Create a container with tabs.
    
    Args:
        tabs: Dictionary mapping tab names to callback functions
    """
    tab_list = st.tabs(list(tabs.keys()))
    
    for i, (tab_name, callback) in enumerate(tabs.items()):
        with tab_list[i]:
            callback()
