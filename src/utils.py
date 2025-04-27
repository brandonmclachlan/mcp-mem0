# utils.py (Configured for potential Gemini usage)
from mem0 import Memory
import os

def get_mem0_client():
    # Get LLM provider and configuration
    llm_provider = os.getenv('LLM_PROVIDER') # e.g., 'gemini', 'openai', 'ollama'
    llm_model = os.getenv('LLM_CHOICE') # Optional: e.g., 'gemini-1.5-flash-latest'

    # Get Embedder provider and configuration
    # Defaults to llm_provider if EMBEDDER_PROVIDER is not explicitly set
    embedder_provider = os.getenv('EMBEDDER_PROVIDER', llm_provider) # e.g., 'gemini'
    embedding_model = os.getenv('EMBEDDING_MODEL_CHOICE') # Optional: e.g., 'models/text-embedding-004'

    # Specific API Keys for different providers
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY') # Key for Gemini LLM
    google_api_key = os.getenv('GOOGLE_API_KEY') # Key for Gemini Embedder (might be the same as GEMINI_API_KEY)

    # Initialize config dictionary
    config = {}
    # Default embedding dimension - will be updated based on the chosen embedder
    embedding_dims = 768 # Default suitable for Gemini's text-embedding-004

    # --- Configure LLM ---
    if llm_provider == 'gemini':
        if not gemini_api_key:
            raise ValueError("LLM_PROVIDER is 'gemini' but GEMINI_API_KEY environment variable is not set.")
        config["llm"] = {
            "provider": "gemini",
            "config": {
                "model": llm_model or "gemini-1.5-flash-latest", # Default Gemini model
                "temperature": 0.2,
                "max_tokens": 2000,
                "api_key": gemini_api_key # Pass the API key
            }
        }
        print("Configured LLM provider: Gemini")
    elif llm_provider == 'openai':
        if not openai_api_key:
             raise ValueError("LLM_PROVIDER is 'openai' but OPENAI_API_KEY environment variable is not set.")
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": llm_model or "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 2000,
                "api_key": openai_api_key,
            }
        }
        print("Configured LLM provider: OpenAI")
    # Add other providers like openrouter, ollama as needed...
    # elif llm_provider == 'ollama': ...
    else:
        # Default or raise error if no provider specified or supported
        raise ValueError(f"Unsupported or unspecified LLM_PROVIDER: '{llm_provider}'. Set LLM_PROVIDER environment variable.")

    # --- Configure Embedder ---
    if embedder_provider == 'gemini':
        if not google_api_key:
             # Mem0 Gemini Embedder often uses GOOGLE_API_KEY env var name
            raise ValueError("EMBEDDER_PROVIDER is 'gemini' but GOOGLE_API_KEY environment variable is not set.")
        gemini_embed_model = embedding_model or "models/text-embedding-004" # Default Gemini embedder
        # Determine dims based on model - Assuming 768 for default
        if gemini_embed_model == "models/text-embedding-004":
            embedding_dims = 768
        # Add conditions for other Gemini embed models if needed
        # else: embedding_dims = ???
        config["embedder"] = {
            "provider": "gemini",
            "config": {
                "model": gemini_embed_model,
                "embedding_dims": embedding_dims,
                "api_key": google_api_key # Pass the API key
            }
        }
        print(f"Configured Embedder provider: Gemini (dims: {embedding_dims})")

    elif embedder_provider == 'openai':
        if not openai_api_key:
             raise ValueError("EMBEDDER_PROVIDER is 'openai' but OPENAI_API_KEY environment variable is not set.")
        embedding_dims = 1536 # Default for text-embedding-3-small
        config["embedder"] = {
            "provider": "openai",
            "config": {
                "model": embedding_model or "text-embedding-3-small",
                "embedding_dims": embedding_dims,
                "api_key": openai_api_key
            }
        }
        print(f"Configured Embedder provider: OpenAI (dims: {embedding_dims})")
    # Add other providers like ollama as needed...
    # elif embedder_provider == 'ollama': ...
    else:
        # Default or raise error if no provider specified or supported
        raise ValueError(f"Unsupported or unspecified EMBEDDER_PROVIDER: '{embedder_provider}'. Set EMBEDDER_PROVIDER environment variable.")


    # --- Configure Vector Store ---
    # Ensure DATABASE_URL is set for Supabase
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required for Supabase vector store.")

    config["vector_store"] = {
        "provider": "supabase", # Assumes Supabase
        "config": {
            "connection_string": database_url,
            "collection_name": "mem0_memories",
            # Use the determined embedding_dims based on the chosen embedder
            "embedding_model_dims": embedding_dims # This is crucial
        }
    }
    print(f"Configured Vector Store: Supabase (expecting dims: {embedding_dims})")

    # Optional: Custom instructions
    # config["custom_fact_extraction_prompt"] = CUSTOM_INSTRUCTIONS

    # --- Create and return the Memory client ---
    print(f"Initializing Mem0 with final config...") # Simplified logging
    try:
        return Memory.from_config(config)
    except Exception as e:
        print(f"Error during Mem0 initialization with config {config}: {e}")
        raise
