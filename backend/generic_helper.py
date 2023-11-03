import re

def extract_session_id(session_str: str):
    '''
    This function extracts the string from the session ID using regular expressions
    Returns: (str) session id
    '''
    match = re.search(r'/sessions/(.*?)/contexts/', session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string
    
    return ""

def get_str_from_food_dict(food_dict: dict):
    '''
    This function prints a string version of the food dictionary, iterating through each item
    Returns: (str) food items
    '''
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])

if __name__ == "__main__":
    get_str_from_food_dict({'samosa': 2, 'lasagna': 8})

    # print(extract_session_id("projects/mira-chatbot-for-food-del-ejcd/agent/sessions/82edb045-ddd6-7c82-ef6a-161ca23e57fd/contexts/ongoing-order"))