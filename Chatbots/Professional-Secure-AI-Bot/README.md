Source: https://github.com/NSIDE-ATTACK-LOGIC/Professional-Secure-AI-Bot/tree/main
(Changed the llm from OpenAI to AzureOpenAI)

## Run with Docker:
1. Clone this repository.
2. In the repository's root folder run `docker build --build-arg OPENAI_API_KEY="YOUR TOKEN" -t secure-ai-bot .`
3. Run `docker run -p 5000:5000 secure-ai-bot`

## Local Installation:
1. Clone this repository.
2. Go to the cloned directory and run `pip install .`.
3. Export an `OPENAI_API_KEY`environment variable via `export OPENAI_API_KEY="YOUR TOKEN"`.
4. Install the "spacy" model for local vector embeddings: 
   `python -m spacy download en_core_web_sm`
5. Run `secure_ai_bot` in the cloned directory.
   Note: The application is not independent from the working directory.

After the successful installation, you will see the following webpage at http://127.0.0.1:5000
