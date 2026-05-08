FLASK_DEBUG=1
FLASK_CONFIG=application.config.DevelopmentConfig
FLASK_APP=application.wsgi:app
SECRET_KEY=replaceinprod
DATABASE_URL=postgresql://postgres:password@db:5432/sandbox
FLASK_RUN_PORT=5050
# HF_TOKEN=optional_huggingface_token_if_lots_doc_embeddings
