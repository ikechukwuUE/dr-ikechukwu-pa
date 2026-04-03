"""
Flask API Gateway — BeeAI Multi-Agent System
=============================================
REST API gateway for Vogue Space multi-agent system.
Provides endpoints for all domain pipelines.

Architecture:
- Flask with sync routes (async workflows wrapped with asyncio.to_thread)
- BeeAI Framework integration
- MCP tool server connectivity
- OpenRouter LLM integration
"""
import asyncio
import base64
import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Helper function for running async workflows with proper cleanup
def run_async_workflow(coro):
    """Run async workflow with proper cleanup of asyncio tasks."""
    loop = None
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the coroutine
        result = loop.run_until_complete(coro)
        
        # Clean up any pending tasks
        pending = asyncio.all_tasks(loop)
        if pending:
            # Cancel all pending tasks
            for task in pending:
                task.cancel()
            # Wait for all tasks to be cancelled
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        # Close the event loop
        loop.close()
        
        return result
    except Exception as e:
        # Ensure the loop is closed even if an error occurs
        try:
            if loop is not None:
                loop.close()
        except:
            pass
        raise e

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

# Image processing utilities for multimodal support
from shared.image_utils import (
    encode_image_bytes_to_base64,
    validate_image_size,
    get_image_format,
    compress_image,
    resize_image,
    create_openrouter_multimodal_message,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "flask": "running",
            "beeai": "available",
            "mcp": "connected"
        }
    })


# ============================================================================
# MEDICINE DOMAIN ENDPOINTS
# ============================================================================

@app.route('/api/medicine/qa', methods=['POST'])
def medicine_qa():
    """
    Medical Q&A endpoint.
    
    Request body:
    {
        "query": "What are the symptoms of diabetes?",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: query"
            }), 400
        
        query = data['query']
        session_id = data.get('session_id', '')
        
        # Import and run medicine workflow
        from domains.medicine.workflows.pipelines import (
            MedicineWorkflowState, MedicineWorkflowExecutor
        )
        
        async def run_workflow():
            executor = MedicineWorkflowExecutor()
            state = MedicineWorkflowState(
                query=query,
                pipeline_type="qa",
                session_id=session_id
            )
            return await executor.execute_workflow(state)
        
        result = run_async_workflow(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": result.session_id,
                "query": result.query,
                "urgency": result.urgency.value if result.urgency else None,
                "specialty": result.specialty,
                "specialist_response": {
                    "assessment": result.specialist_response.assessment if result.specialist_response else None,
                    "recommendations": result.specialist_response.recommendations if result.specialist_response else [],
                    "confidence": result.specialist_response.confidence if result.specialist_response else None
                } if result.specialist_response else None,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Medicine Q&A error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/medicine/research', methods=['POST'])
def medicine_research():
    """
    Medical Research endpoint.
    
    Request body:
    {
        "question": "What is the latest research on Alzheimer's disease?",
        "scope": "broad",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: question"
            }), 400
        
        question = data['question']
        scope = data.get('scope', 'broad')
        session_id = data.get('session_id', '')
        
        # Import and run medicine workflow
        from domains.medicine.workflows.pipelines import (
            MedicineWorkflowState, MedicineWorkflowExecutor
        )
        
        async def run_workflow():
            executor = MedicineWorkflowExecutor()
            state = MedicineWorkflowState(
                query=question,
                pipeline_type="research",
                session_id=session_id
            )
            return await executor.execute_workflow(state)
        
        result = run_async_workflow(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": result.session_id,
                "question": question,
                "research_manuscript": {
                    "title": result.research_manuscript.title if result.research_manuscript else None,
                    "abstract": result.research_manuscript.abstract if result.research_manuscript else None,
                    "sections": result.research_manuscript.sections if result.research_manuscript else {},
                    "references": result.research_manuscript.references if result.research_manuscript else []
                } if result.research_manuscript else None,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Medicine research error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/medicine/clinical', methods=['POST'])
def medicine_clinical():
    """
    Clinical Decision Support endpoint.
    
    Supports both JSON and multipart form data with image upload.
    
    Request body (JSON):
    {
        "patient_info": {
            "history": "Patient history...",
            "examination": "Physical examination...",
            "investigations": {"lab_results": "..."}
        },
        "session_id": "optional-session-id"
    }
    
    Request body (multipart form data):
    - image: Image file (JPEG, PNG, WebP)
    - patient_info: JSON string with patient information
    - session_id: Optional session ID
    """
    try:
        patient_info = None
        image_base64 = None
        session_id = ''
        
        # Handle multipart form data with image
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Get patient_info from form data
            patient_info_str = request.form.get('patient_info')
            if patient_info_str:
                import json
                patient_info = json.loads(patient_info_str)
            else:
                return jsonify({
                    "success": False,
                    "error": "Missing required field: patient_info"
                }), 400
            
            session_id = request.form.get('session_id', '')
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    # Validate file type
                    allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
                    file_ext = os.path.splitext(image_file.filename)[1].lower()
                    if file_ext not in allowed_extensions:
                        return jsonify({
                            "success": False,
                            "error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
                        }), 400
                    
                    # Read image data
                    image_data = image_file.read()
                    
                    # Validate and process using image_utils
                    if not validate_image_size(image_data):
                        return jsonify({
                            "success": False,
                            "error": "Image file too large. Maximum size: 10MB"
                        }), 400
                    
                    # Validate format
                    if not get_image_format(image_data):
                        return jsonify({
                            "success": False,
                            "error": "Invalid image format. Allowed: JPEG, PNG, WebP"
                        }), 400
                    
                    # Resize and compress for API efficiency
                    image_data = resize_image(image_data, max_width=1024, max_height=1024) or image_data
                    image_data = compress_image(image_data, quality=85) or image_data
                    
                    # Encode using image_utils
                    image_base64 = encode_image_bytes_to_base64(image_data)
                    logger.info(f"Received image: {image_file.filename} ({len(image_data)} bytes)")
        else:
            # Handle JSON request
            data = request.get_json()
            
            if not data or 'patient_info' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required field: patient_info"
                }), 400
            
            patient_info = data['patient_info']
            session_id = data.get('session_id', '')
        
        # Import and run medicine workflow
        from domains.medicine.workflows.pipelines import (
            MedicineWorkflowState, MedicineWorkflowExecutor
        )
        
        async def run_workflow():
            executor = MedicineWorkflowExecutor()
            state = MedicineWorkflowState(
                query=patient_info.get('history', ''),
                pipeline_type="cds",
                session_id=session_id,
                image_base64=image_base64
            )
            return await executor.execute_workflow(state)
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": result.session_id,
                "urgency": result.urgency.value if result.urgency else None,
                "specialty": result.specialty,
                "specialist_response": {
                    "assessment": result.specialist_response.assessment if result.specialist_response else None,
                    "recommendations": result.specialist_response.recommendations if result.specialist_response else [],
                    "confidence": result.specialist_response.confidence if result.specialist_response else None
                } if result.specialist_response else None,
                "management_plan": {
                    "evidence_based_guidelines": result.management_plan.evidence_based_guidelines if result.management_plan else [],
                    "personalized_plan": result.management_plan.personalized_plan if result.management_plan else None,
                    "follow_up": result.management_plan.follow_up if result.management_plan else None
                } if result.management_plan else None,
                "human_approved": result.human_approved,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Medicine clinical error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/medicine/clinical/approve', methods=['POST'])
def medicine_clinical_approve():
    """
    Clinical Decision Support approval endpoint.
    
    Request body:
    {
        "session_id": "session-id",
        "approved": true,
        "feedback": "Optional feedback",
        "modifications": ["Optional modifications"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: session_id"
            }), 400
        
        session_id = data['session_id']
        approved = data.get('approved', False)
        feedback = data.get('feedback', '')
        modifications = data.get('modifications', [])
        
        # Import and run medicine workflow
        from domains.medicine.workflows.pipelines import MedicineWorkflowExecutor
        
        async def run_workflow():
            executor = MedicineWorkflowExecutor()
            return await executor.approve_cds(
                session_id=session_id,
                approved=approved,
                feedback=feedback,
                modifications=modifications
            )
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Medicine clinical approve error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/medicine/news', methods=['GET'])
def medicine_news():
    """Medical News endpoint."""
    try:
        # Import and run medicine workflow
        from domains.medicine.workflows.pipelines import (
            MedicineWorkflowState, MedicineWorkflowExecutor
        )
        
        async def run_workflow():
            executor = MedicineWorkflowExecutor()
            state = MedicineWorkflowState(
                query="",
                pipeline_type="news"
            )
            return await executor.execute_workflow(state)
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "final_output": result.final_output,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Medicine news error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# FINANCE DOMAIN ENDPOINTS
# ============================================================================

@app.route('/api/finance/qa', methods=['POST'])
def finance_qa():
    """
    Financial Q&A endpoint.
    
    Request body:
    {
        "query": "What is the best investment strategy for retirement?",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: query"
            }), 400
        
        query = data['query']
        session_id = data.get('session_id', '')
        
        # Import and run finance workflow
        from domains.finance.workflows.pipelines import (
            FinanceWorkflowState, FinanceWorkflowExecutor
        )
        
        async def run_workflow():
            executor = FinanceWorkflowExecutor()
            state = FinanceWorkflowState(
                query=query,
                pipeline_type="qa",
                session_id=session_id
            )
            return await executor.execute_workflow(state)
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": result.session_id,
                "outfit_analysis": result.outfit_analysis.model_dump() if result.outfit_analysis else None,
                "final_output": result.final_output or "",
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Fashion analyze error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/fashion/trends', methods=['GET'])
def fashion_trends():
    """Fashion Trends endpoint."""
    try:
        # Import and run fashion workflow
        from domains.fashion.workflows.pipelines import (
            FashionWorkflowState, FashionWorkflowExecutor
        )
        
        async def run_workflow():
            executor = FashionWorkflowExecutor()
            state = FashionWorkflowState(
                query="current fashion trends"
            )
            return await executor.execute_workflow(state)
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "style_trend": result.style_trend.model_dump() if result.style_trend else None,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Fashion trends error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/fashion/recommend', methods=['POST'])
def fashion_recommend():
    """
    Outfit Recommendation endpoint.
    
    Request body:
    {
        "budget": 200,
        "occasion": "wedding",
        "time": "evening",
        "location": "Lagos",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Missing request body"
            }), 400
        
        budget = data.get('budget', 0)
        occasion = data.get('occasion', '')
        time = data.get('time', '')
        location = data.get('location', '')
        session_id = data.get('session_id', '')
        
        # Import and run fashion workflow
        from domains.fashion.workflows.pipelines import (
            FashionWorkflowState, FashionWorkflowExecutor
        )
        
        async def run_workflow():
            executor = FashionWorkflowExecutor()
            state = FashionWorkflowState(
                budget=budget,
                occasion=occasion,
                time=time,
                location=location,
                session_id=session_id
            )
            return await executor.execute_workflow(state)
        
        result = asyncio.run(run_workflow())
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": result.session_id,
                "outfit_recommendation": result.outfit_recommendation.model_dump() if result.outfit_recommendation else None,
                "completed_steps": result.completed_steps
            }
        })
        
    except Exception as e:
        logger.error(f"Fashion recommend error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Flask API Gateway on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
