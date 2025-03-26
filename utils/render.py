import os
import uuid
import yaml
import logging
import traceback
from pathlib import Path
from .resume_converter import JSONResumeConverter
from rendercv.data import RenderCVDataModel
from rendercv.renderer.renderer import (
    create_a_typst_file_and_copy_theme_files,
    render_a_pdf_from_typst,
    create_a_markdown_file,
    render_an_html_from_markdown
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = os.path.join('utils', 'templates')

def fix_bullet_character(data):
    """
    Specifically fix the bullet character in the YAML data structure.
    Replaces problematic bullet characters with the standard bullet point '•'.
    """
    if isinstance(data, dict):
        # Special handling for the bullet configuration
        if 'design' in data and 'highlights' in data['design'] and 'bullet' in data['design']['highlights']:
            data['design']['highlights']['bullet'] = '•'
        return {k: fix_bullet_character(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [fix_bullet_character(item) for item in data]
    return data

def sanitize_yaml_data(data):
    """
    Recursively sanitize YAML data to ensure compatibility
    """
    if isinstance(data, dict):
        return {k: sanitize_yaml_data(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [sanitize_yaml_data(v) for v in data if v is not None]
    elif data is None:
        return ""
    return data

def read_yaml_template(theme_type='classic'):
    """
    Read and validate the YAML template based on theme type.
    
    Args:
        theme_type (str): Theme type to select (e.g., 'Classic', 'Modern', 'Professional')
    
    Returns:
        dict: Parsed YAML template
    """
    try:
        theme_type = theme_type.lower().capitalize()
        
        
        template_path = os.path.join(TEMPLATE_PATH, f'{theme_type}.yaml')
        
        
        if not template_path:
            logger.error(f"No YAML template found for theme {theme_type}")
            raise FileNotFoundError(f"Could not find YAML template for theme {theme_type}")
        
        logger.info(f"Using YAML template from: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
            
        if 'design' in template and 'highlights' in template['design']:
            template['design']['highlights']['bullet'] = '•'
            
        return template
    except Exception as e:
        logger.error(f"Error reading YAML template for theme {theme_type}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def generate_resume_pdf(json_data,theme_type='classic'):
    """
    Generate a PDF resume from JSON data using rendercv library directly.
    Includes improved error handling, encoding support, and bullet character fixes.
    Returns only the PDF path for backward compatibility.
    """
    try:
        if not json_data or not isinstance(json_data, dict):
            raise ValueError("Invalid JSON data provided")

        converter = JSONResumeConverter(json_data)
        converted_data = converter.convert()
        
        logger.debug(f"Converted Data: {converted_data}")
        
        try:
            base_yaml = read_yaml_template(theme_type)
        except Exception as yaml_load_error:
            logger.error(f"Error loading base YAML: {yaml_load_error}")
            raise

        base_yaml['cv'] = converted_data

        fixed_yaml = fix_bullet_character(sanitize_yaml_data(base_yaml))

        TEMP_DIR = os.path.join(BASE_DIR, 'temp')
        OUTPUT_FOLDER = os.path.join(TEMP_DIR, 'output')
        
        output_dir = Path(OUTPUT_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        input_filename = f"{uuid.uuid4()}_resume"
        yaml_path = output_dir / f"{input_filename}.yaml"
        
        logger.debug(f"Attempting to write YAML to: {yaml_path}")
        
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(fixed_yaml, f, 
                         sort_keys=False, 
                         default_flow_style=False, 
                         allow_unicode=True)
                
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Bullet character in file: {content.find('•') != -1}")
                
        except Exception as yaml_write_error:
            logger.error(f"Error writing YAML file: {yaml_write_error}")
            logger.error(f"Full path attempted: {yaml_path}")
            logger.error(f"Directory exists check: {output_dir.exists()}")
            raise

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            data_model = RenderCVDataModel(**yaml_data)
            
            typst_path = create_a_typst_file_and_copy_theme_files(data_model, output_dir)
            logger.info(f"Typst file generated successfully at {typst_path}")
            
            pdf_path = render_a_pdf_from_typst(typst_path)
            
            pdf_path_str = str(pdf_path)
            
            try:
                os.remove(yaml_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary YAML file: {cleanup_error}")
            
        except Exception as render_error:
            logger.error(f"Error during rendering: {render_error}")
            logger.error(traceback.format_exc())
            raise
    
    except Exception as e:
        logger.error(f"Resume generation failed: {e}")
        logger.error(traceback.format_exc())
        raise

def generate_resume_html(json_data,theme_type='classic'):
    """
    Generate HTML resume from JSON data and return the HTML content directly.
    """
    try:
        if not json_data or not isinstance(json_data, dict):
            raise ValueError("Invalid JSON data provided")

        converter = JSONResumeConverter(json_data)
        converted_data = converter.convert()
        
        logger.debug(f"Converted Data: {converted_data}")
        
        try:
            base_yaml = read_yaml_template(theme_type)
        except Exception as yaml_load_error:
            logger.error(f"Error loading base YAML: {yaml_load_error}")
            raise

        base_yaml['cv'] = converted_data
        
        fixed_yaml = fix_bullet_character(sanitize_yaml_data(base_yaml))
        
        TEMP_DIR = os.path.join(BASE_DIR, 'temp')
        OUTPUT_FOLDER = os.path.join(TEMP_DIR, 'output')
        
        output_dir = Path(OUTPUT_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        input_filename = f"{uuid.uuid4()}_resume"
        yaml_path = output_dir / f"{input_filename}.yaml"
        
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(fixed_yaml, f, 
                         sort_keys=False, 
                         default_flow_style=False, 
                         allow_unicode=True)
        except Exception as yaml_write_error:
            logger.error(f"Error writing YAML file: {yaml_write_error}")
            raise

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            data_model = RenderCVDataModel(**yaml_data)
            
            markdown_path = create_a_markdown_file(data_model, output_dir)
            
            html_path = render_an_html_from_markdown(markdown_path)
            
            with open(html_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
            
            try:
                os.remove(yaml_path)
                os.remove(markdown_path)
                os.remove(html_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary files: {cleanup_error}")
            
            return html_content
            
        except Exception as render_error:
            logger.error(f"Error during rendering: {render_error}")
            logger.error(traceback.format_exc())
            raise
    
    except Exception as e:
        logger.error(f"Resume HTML generation failed: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        template = read_yaml_template()
        logger.info("Successfully loaded and validated YAML template")
        logger.debug(f"Bullet character: {template.get('design', {}).get('highlights', {}).get('bullet', 'not set')}")
    except Exception as e:
        logger.error(f"Template validation failed: {e}")
