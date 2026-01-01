from typing import Dict, Any


def format_field_name(field_name: str) -> str:
    """
    Format field name from snake_case to Title Case.
    
    Args:
        field_name: Field name in snake_case
        
    Returns:
        Formatted field name
    """
    return field_name.replace('_', ' ').title()


def format_medical_note(note_data: Dict[str, Any], template_name: str = "") -> str:
    """
    Format medical note data dynamically from JSON structure.
    
    Args:
        note_data: Dictionary containing medical note fields
        template_name: Name of the template used
        
    Returns:
        Formatted string with line breaks
    """
    result = f"Template: {template_name}<br><br>" if template_name else ""
    
    for key, value in note_data.items():
        # Skip internal fields (starting with underscore)
        if key.startswith('_'):
            continue
        
        formatted_key = format_field_name(key)
            
        if isinstance(value, dict):
            result += f"<strong>{formatted_key}:</strong><br>"
            for sub_key, sub_value in value.items():
                formatted_sub_key = format_field_name(sub_key)
                # Handle nested dictionaries recursively
                if isinstance(sub_value, dict):
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>{formatted_sub_key}:</strong><br>"
                    for nested_key, nested_value in sub_value.items():
                        formatted_nested_key = format_field_name(nested_key)
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{formatted_nested_key}: {nested_value}<br>"
                else:
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;{formatted_sub_key}: {sub_value}<br>"
            result += "<br>"
        else:
            result += f"<strong>{formatted_key}:</strong> {value}<br><br>"
    
    return result


def format_template_document(fields: Dict[str, Any], template_name: str = "") -> str:
    """
    Format template structure dynamically from JSON structure.
    
    Args:
        fields: Dictionary containing template field definitions
        template_name: Name of the template
        
    Returns:
        Formatted string with line breaks
    """
    result = f"<strong>Template:</strong> {template_name}<br><br>" if template_name else ""
    
    for key, value in fields.items():
        formatted_key = format_field_name(key)
        
        if isinstance(value, dict):
            description = value.get('description', '')
            field_type = value.get('type', '')
            result += f"<strong>{formatted_key}:</strong><br>"
            if description:
                result += f"&nbsp;&nbsp;&nbsp;&nbsp;Description: {description}<br>"
            if field_type:
                result += f"&nbsp;&nbsp;&nbsp;&nbsp;Type: {field_type}<br>"
            result += "<br>"
        else:
            result += f"<strong>{formatted_key}:</strong> {value}<br><br>"
    
    return result
