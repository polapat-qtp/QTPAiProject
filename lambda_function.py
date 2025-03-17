import os

import json
import requests
from typing import List, Dict, Any, Union
import boto3
from boto3.dynamodb.conditions import Key
import ai_model
from multiprocessing import Process, Pipe, freeze_support

def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes requests from AppScript
    
    Args:
        event: The event dict containing the input parameters
        context: Lambda context
        
    Returns:
        Formatted response for AppScript
    """
    try:
        # Extract parameters from the event
        company_names = event.get('companies', [])
        prompts = event.get('prompts', [])
        provider = event.get('provider', '')
        api_key = event.get('api_key', '')
        number = event.get('number', 10)
        create_list = event.get('create_list', False)
        private_data = event.get('private_data', False)

        model = ai_model.AIModel(provider)

        # When you receive an API key, set it as an environment variable
        model.set_api_key(api_key)

        # Ensure company_names and prompts are lists
        if not isinstance(company_names, list):
            company_names = [company_names] if company_names else []
        
        if not isinstance(prompts, list):
            prompts = [prompts] if prompts else []
        
        # Filter out empty values
        companies = [name for name in company_names if name]
        prompts = [p for p in prompts if p]
        
        if create_list == True:
            companies = generate_companies(companies, number, model)
        result = parallel_ai_call(companies, prompts, private_data, model)
        print("reach after calling ai") #test
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def sheet_ai_call(company: str, prompt: str, private_data,
           model, conn) -> Dict[str, Any]:
    """
    Generates GPT responses for companies based on prompts
    
    Args:
        companies: List of company names
        prompts: List of prompts to send to GPT
        provider: AI provider (default: "openai")
        private_dataL boolean, if true then use data frm dynamoDB
        
    Returns:
        Formatted output data
    """
    try:
        full_prompt = f"""
        Act as a financial analyst for an investment banking company.
        Be concise with your word, and only provide information needed. Evaluate the company {company},
        by answer the following questions: {prompt}.
        If outputs were to be links, names, numerical figures, contact, etc; that do not require textual
        description, ONLY provide that output, nothing else.
        Limit output to less than 80 words, no more than this.
        """
        if private_data:
            private_data_result = read_dynamo(company)
            full_prompt += " Incorporate this data as a reference: " + str(private_data_result)
        result = model.call(full_prompt)
        conn.send([result])
    except Exception as e:
        conn.send([{"error": True, "message": {"content": f"Error processing {company}: {str(e)}"}}])
    finally:
        conn.close()

def parallel_ai_call(companies: List[str], prompts: List[str], private_data, model) -> Dict[str, Any]:
    company_results = {company: [company] for company in companies}

    for prompt in prompts:
        processes = []
        parent_connections = {}
        for company in companies:
            parent_conn, child_conn = Pipe()
            parent_connections[company] = parent_conn
            process = Process(target=sheet_ai_call, args=(company, prompt, private_data, model, child_conn))
            processes.append(process)
            process.start()
 
        for process in processes:
            process.join()

        for company, conn in parent_connections.items():
            result = conn.recv()[0]
            company_results[company].append(result)
    
    results = list(company_results.values())
    return {
        "data": results,
        "metadata": {
            "companies": companies,
            "prompts": prompts,
        }
    }

def generate_companies(company, number, model):
    """
    Generates a list of companies from target company name

    Args:
        company: target company name

    Returns:
        List of companies
    """
    companies = []
    prompt = f"""
        Your task is to conduct deep research to identify {number} companies or investors
        that would be willing to invest in {company}. Follow these steps:
        Search for companies in the gaming industry that have recently engaged in
        gaming companies acquisition, focus on recent transactions. In addition,
        incorporate companies outside of gaming industry, that have traction with the
        gaming industry, or have expanded its business towrds the gaming industry.
        Check these companies recent management presentations, earning call transcripts,
        search company LinkedIn for keywords such as M&A, investment, or deal.
        Output should ONLY be the name of the company, seperated with a comma.
        Do not output anything else. """

    result = model.call(prompt)
    for company in result.split(","):
        companies.append(company.strip())
    return companies
  
def read_dynamo(company): 
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('qtp-ai-dynamo-db')
    response = table.query(KeyConditionExpression=Key("name").eq(company))
    print(response) #test
    if "Items" in response:
        return response["Items"]
    else:
        return {"statusCode": 404, "body": "Customer not found"}

if __name__ == "__main__":
    # Add freeze_support for Windows
    freeze_support()
    
