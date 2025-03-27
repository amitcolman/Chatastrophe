# Broken Chatbot

* Go to chatapp folder
* Edit the .env file and add your OpenAI API key
  * OPENAI_API_KEY & OPENAI_MODEL_NAME
* run -> docker compose --env-file .\backend\.env build
* run -> docker compose up
* Wait for Ollama to pull the model before using the chatbot