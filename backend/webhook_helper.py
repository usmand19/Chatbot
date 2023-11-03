from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

def webhook_message(message):
    '''
    This function takes an input string and will place it in the Webhook response object
    '''
    return {
                "fulfillmentText": message

                }

    return {
                "fulfillmentText": "Text response",
                "fulfillmentMessages": [    
                                        {
                                            "text": {
                                                        "text": [message]
                                                    }
                                        }
                                        ]   
                }

