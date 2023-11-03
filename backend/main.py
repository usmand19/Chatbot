from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
import webhook_helper

app = FastAPI()
# Dictionary to store orders in prograss by session id (order stored as dictionary)
# When a user submits the order, the records are then put into the database
in_progress_orders = {}
#Track order
@app.get("/")
async def default():
    '''
    This function is the defualt text returned when the connection is established
    '''
    return "Default Text"

    

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON Data from the request
    payload = await request.json()

    #Extract the necessary information from the payload
    # based on the structure of the Webhook request from DialogFlow
    # Extract the intent form the JSON object
    intent = payload['queryResult']['intent']['displayName']
    # Extract the parameters from the JSOn object
    parameters = payload['queryResult']['parameters']
    # Extract the output context from the JSOn object
    output_contexts = payload['queryResult']['outputContexts'] 
    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])


    # Intent Handler dictionary:
    # This dictionary stores the different intents and assigns a function to run
    intent_handler_dictionary = {
        'track.order - context: ongoing-tracking': track_order,
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order
    }
    

    return intent_handler_dictionary[intent](parameters, session_id)       


def add_to_order(parameters: dict, session_id: str):
    '''
    This function gets a dictionary of the parameters for the order.add intent, and adds it to the existing order dictionary
    Returns: JSON response of current order or an error message
    '''
    food_items = parameters['food-item']
    quantities = parameters['number']

    # Check if the length of items is consistent
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry  don't quite understand. Can you splease specify food items and quantities again?"
    else:

        new_food_dict = dict(zip(food_items, quantities))

        if session_id in in_progress_orders:
            current_food_dict = in_progress_orders[session_id]
            current_food_dict.update(new_food_dict)
            in_progress_orders[session_id] = current_food_dict
        else:
            in_progress_orders[session_id] = new_food_dict
        order_string = generic_helper.get_str_from_food_dict(in_progress_orders[session_id])
        fulfillment_text = f"So far you have: {order_string}. Do you need anything else"

    return JSONResponse(webhook_helper.webhook_message(fulfillment_text))

def complete_order(parameters: dict, session_id: str):
    '''
    This function gets the session id for the order.complete intent, and adds it to the order MYSQL database,
    removing the order from the existing orders dictionary
    Returns: JSON response to confirm the order or an error message
    '''
    # Check if the order exists in progress
    print(in_progress_orders)
    if session_id not in in_progress_orders:
        fulfillment_text = "I'm having trouble finding your order. Can you place a new order?"
    else:
        order = in_progress_orders[session_id]
        order_id = save_to_db(order)
        print(order, order_id)
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error."\
                                "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Your order is placed! " \
                               f"Your Order ID is: {order_id}. " \
                               f"Your order total is {order_total}, which you can pay at the time of delivery"

        del in_progress_orders[session_id]

    return JSONResponse(webhook_helper.webhook_message(fulfillment_text))

def save_to_db(order: dict):
    '''
    This functions takes a dictionary of food items from an order, and stores the items into the database with the 
    next order id, determined by the get_next_order_id() stored process
    returns: Next order id for output message
    '''
    # Get the next order # in the database
    next_order_id = db_helper.get_next_order_id()
    # Insert the items into the order items table
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1
    # Insert the order number into order tracking as in progress
    db_helper.insert_order_tracking(next_order_id,'In Progress')
    return next_order_id

def track_order(parameters: dict, session_id: str):

    '''
    This function is for the track.order intent, mapping the status from the order id stored in the db
    Returns: JSON response of order status as store in db or error message
    '''
    # The JSON of the output from dialog flow has a dictionary for parameteers, so you can just call it for the order name
    order_id = parameters['number']
    order_status = db_helper.get_order_status(order_id)

    if order_status == 1:
        fulfillment_text = f"No order found with order id: {order_id}"
    else:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
        
    return JSONResponse(webhook_helper.webhook_message(fulfillment_text))

def remove_from_order(parameters: dict, session_id: str):
    '''
    This function removes food items from the existing order dictionary based on the session id as the key.
    Returns: JSOn object of removed food item(s), a message indicating no items lef tin order, or an error message
    '''
    # Locate the session id
    if session_id not in in_progress_orders:
        fulfillment_text = "I'm having trouble finding your order. Can you place a new order?"
    else:
        # Get the current order for the session
        current_order = in_progress_orders[session_id]
        # Get food items from parameter of post call
        food_items = parameters['food-item']
        # Create a list to store removed items and non-existent items for error handling
        removed_items = []
        no_such_items = []

        for item in food_items:
            if item not in current_order:
                no_such_items.append(item)
            else:
                removed_items.append(item)
                del current_order[item]

        if len(removed_items) > 0:
            fulfillment_text = f"Removed {', '.join(removed_items)} from your order."

        if len(no_such_items) > 0:
            fulfillment_text = f"Your current order does not have {', '.join(no_such_items)}."

        if len(current_order.keys()) == 0:
            fulfillment_text += " Your order is empty!" 
        else:
            fulfillment_text += f" Here is what is left in your order: {generic_helper.get_str_from_food_dict(current_order)}"

    return JSONResponse(webhook_helper.webhook_message(fulfillment_text))   
