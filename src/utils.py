# utils.py (Modified)
from mem0 import Memory
import os

# Custom instructions (Keep as is)
# ... CUSTOM_INSTRUCTIONS = """...""" ...

def get_mem0_client():
    # Get LLM provider and configuration
    llm_provider = os.getenv('LLM_PROVIDER')
    llm_api_key = os.getenv('LLM_API_KEY') # Generic key, might need specific ones
    llm_model = os.getenv('LLM_CHOICE')

    # Get Embedder provider and configuration (assuming separate control if needed, else defaults to LLM provider)
    # You might want to add a separate EMBEDDER_PROVIDER env var if you want to mix/match
    embedder_provider = os.getenv('EMBEDDER_PROVIDER', llm_provider) # Default to llm_provider if not set
    embedding_model = os.getenv('EMBEDDING_MODEL_CHOICE')

    # Specific API Keys (Recommended over generic LLM_API_KEY)
    openai_api_key = os.getenv('OPENAI_API_KEY', llm_api_key) # Fallback for openai/openrouter
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY', llm_api_key) # Fallback for openrouter
    gemini_api_key = os.getenv('GEMINI_API_KEY') # Key for Gemini LLM
    google_api_key = os.getenv('GOOGLE_API_KEY') # Key for Gemini Embedder (often same as Gemini key)

    # Initialize config dictionary
    config = {}
    embedding_dims = 768 # Default dimension, will be updated based on embedder

    # --- Configure LLM ---
    if llm_provider == 'openai':
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": llm_model or "gpt-4o-mini", # Default OpenAI model
                "temperature": 0.2,
                "max_tokens": 2000,
                "api_key": openai_api_key, # Use specific key
            }
        }
    elif llm_provider == 'openrouter':
         config["llm"] = {
            "provider": "openrouter", # Use 'openrouter' provider if mem0 lib supports it, else might need 'openai' with base_url
            "config": {
                "model": llm_model, # Required
                "temperature": 0.2,
                "max_tokens": 2000,
                "api_key": openrouter_api_key, # Use specific key
                # "base_url": "https://openrouter.ai/api/v1" # May need base_url if using 'openai' provider
            }
        }
    elif llm_provider == 'ollama':
        config["llm"] = {
            "provider": "ollama",
            "config": {
                "model": llm_model, # Required
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
        llm_base_url = os.getenv('LLM_BASE_URL')
        if llm_base_url:
            config["llm"]["config"]["ollama_base_url"] = llm_base_url

    # --- NEW: Add Gemini LLM Configuration ---
    elif llm_provider == 'gemini':
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required for Gemini LLM provider")
        config["llm"] = {
            "provider": "gemini", # Use the provider name from Mem0 docs
            "config": {
                "model": llm_model or "gemini-1.5-flash-latest", # Default Gemini model
                "temperature": 0.2,
                "max_tokens": 2000,
                "api_key": gemini_api_key # Pass the API key
            }
        }
    # --- End of Gemini LLM ---

    else:
        print(f"Warning: Unsupported LLM provider '{llm_provider}'. Mem0 might default to OpenAI.")
        # Optionally raise an error: raise ValueError(f"Unsupported LLM provider: {llm_provider}")


    # --- Configure Embedder ---
    # Using embedder_provider allows mixing (e.g., OpenAI LLM + Gemini Embedder)
    if embedder_provider == 'openai':
        embedding_dims = 1536 # Default for text-embedding-3-small
        config["embedder"] = {
            "provider": "openai",
            "config": {
                "model": embedding_model or "text-embedding-3-small",
                "embedding_dims": embedding_dims,
                "api_key": openai_api_key # Use specific key
            }
        }

    elif embedder_provider == 'ollama':
        embedding_dims = 768 # Default for nomic-embed-text
        config["embedder"] = {
            "provider": "ollama",
            "config": {
                "model": embedding_model or "nomic-embed-text",
                "embedding_dims": embedding_dims
            }
        }
        embedding_base_url = os.getenv('LLM_BASE_URL') # Assuming embedder uses same base URL
        if embedding_base_url:
            config["embedder"]["config"]["ollama_base_url"] = embedding_base_url

    # --- NEW: Add Gemini Embedder Configuration ---
    elif embedder_provider == 'gemini':
        if not google_api_key:
            # Note: Mem0 Gemini Embedder docs use GOOGLE_API_KEY env var name
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini Embedder provider")
        gemini_embed_model = embedding_model or "models/text-embedding-004"
        # Determine dims based on model - needs mapping or assuming default
        embedding_dims = 768 # Default for text-embedding-004
        config["embedder"] = {
            "provider": "gemini", # Use the provider name from Mem0 docs
            "config": {
                "model": gemini_embed_model,
                "embedding_dims": embedding_dims,
                 # Mem0 docs show GOOGLE_API_KEY for embedder
                "api_key": google_api_key
            }
        }
    # --- End of Gemini Embedder ---

    else:
         print(f"Warning: Unsupported Embedder provider '{embedder_provider}'. Mem0 might default to OpenAI.")
         # Set default dims if needed, assuming OpenAI fallback
         embedding_dims = 1536


    # Configure Supabase vector store (or potentially Qdrant if preferred)
    config["vector_store"] = {
        "provider": "supabase", # Or change to "qdrant" if using Qdrant integration
        "config": {
            "connection_string": os.environ.get('DATABASE_URL', ''),
            "collection_name": "mem0_memories",
            # Use the determined embedding_dims based on the chosen embedder
            "embedding_model_dims": embedding_dims
            # If using Qdrant, replace "connection_string" with Qdrant config:
            # "url": os.getenv("QDRANT_URL"),
            # "api_key": os.getenv("QDRANT_API_KEY"),
        }
    }

    # config["custom_fact_extraction_prompt"] = CUSTOM_INSTRUCTIONS

    # Create and return the Memory client
    print(f"Initializing Mem0 with config: {config}") # Add logging
    try:
        return Memory.from_config(config)
    except Exception as e:
        print(f"Error during Mem0 initialization: {e}")
        raise
