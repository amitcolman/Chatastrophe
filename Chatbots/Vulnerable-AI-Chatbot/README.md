Source: https://github.com/ai-risk-armour/Vulnerable-AI-Chatbot
(Changed the llm from OpenAI to AzureOpenAI, and added output to console)

## Run with Docker:
1. Clone this repository.
2. In the repository's root folder run `docker build --build-arg OPENAI_API_KEY="{YOUR_API_KEY}" -t vuln-bot .`
3. Run `docker run -p 5000:5000 -p 7000:7000 vuln-bot`


After the successful installation, you will have assitant bot at http://127.0.0.1:5000 and website summarizer at http://127.0.0.1:7000
