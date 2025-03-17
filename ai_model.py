import os
from openai import OpenAI
import anthropic
import requests

class AIModel:
    def __init__(self, provider: str):
        valid_providers = ['openai', 'anthropic', 'grok', 'perplexity']
        if provider.lower() not in valid_providers:
            raise ValueError(f"Unsupported provider. Must be one of: {valid_providers}")
        self.provider = provider.lower()

    def set_api_key(self, api_key: str) -> None:
        """
        Sets the API key as an environment variable for the specified provider
        
        Args:
            provider: The AI provider (e.g., 'openai', 'anthropic')
            api_key: The API key to set
        """
        if not isinstance(api_key, str):
            raise TypeError("API key must be a string")
        if len(api_key.strip()) == 0:
            raise ValueError("API key cannot be empty or whitespace")
            
        env_var_name = f"{self.provider.upper()}_API_KEY"
        os.environ[env_var_name] = api_key.strip()
        
        print(f"API key for {self.provider} has been set as environment variable {env_var_name}")

    def call(self, prompt: str):
        """
        Makes an API call to the specified AI provider.
        
        Dynamically calls the appropriate method based on the provider name.
        """
        provider_method = f"{self.provider}_api_call"
        method = getattr(self, provider_method, None)
        if method is None:
            return f"Error: Unsupported AI provider '{self.provider}'."
        return method(prompt)
    
    def openai_api_call(self, prompt: str) -> str:
        """
        Makes an API call to OpenAI
        
        Args:
            prompt: The prompt to send
            model: The model to use
            
        Returns:
            The response from the API
        """
        # Get API key from environment variable for security
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        
        if not OPENAI_API_KEY:
            return "Error: OpenAI API key not found in environment variables"
        from openai import OpenAI
        try:
            client = OpenAI()
            completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
            )

            print(completion.choices[0].message) # test
    
            return completion.choices[0].message.content
        except Exception as error:
            print(f"API call failed: {error}")
            return f"Error calling AI service: {str(error)}"

    def anthropic_api_call(self, prompt: str, model: str = "claude-1") -> str:
        """
        Makes an API call to Anthropic's Claude model
        
        Args:
            prompt: The prompt to send
            model: The model to use (default is claude-1)
            
        Returns:
            The response from the API
        """
        # Get API key from environment variable for security
        ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
        
        if not ANTHROPIC_API_KEY:
            return "Error: Anthropic API key not found in environment variables"
        
        try:
            client = anthropic.Client(ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
        except Exception as error:
            print(f"API call failed: {error}")
            return f"Error calling AI service: {str(error)}"

    def grok_api_call(self, prompt: str, model: str = "grok-model") -> str:
        """
        Makes an API call to Grok's model
        
        Args:
            prompt: The prompt to send
            model: The model to use (default is grok-model)
            
        Returns:
            The response from the API
        """
        # Get API key from environment variable for security
        GROK_API_KEY = os.environ.get('GROK_API_KEY')
        
        if not GROK_API_KEY:
            return "Error: Grok API key not found in environment variables"
        
        client = OpenAI(
        api_key=GROK_API_KEY,
        base_url="https://api.x.ai/v1",
        )

        completion = client.chat.completions.create(
        model="grok-2-latest",
        messages=[{"role": "user", "content": prompt}]
        )
        try:
            print(completion.choices[0].message) # test
            return completion.choices[0].message.content
        except requests.exceptions.RequestException as error:
            print(f"API call failed: {error}")
            return f"Error calling AI service: {str(error)}"

    def perplexity_api_call(self, prompt: str, model: str = "perplexity-model") -> str:
        """
        Makes an API call to Perplexity AI
        
        Args:
            prompt: The prompt to send
            model: The model to use (default is perplexity-model)
            
        Returns:
            The response from the API
        """
        # Get API key from environment variable for security
        PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
        
        if not PERPLEXITY_API_KEY:
            return "Error: Perplexity API key not found in environment variables"
        
        url = "https://api.perplexity.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as error:
            print(f"API call failed: {error}")
            return f"Error calling AI service: {str(error)}"
