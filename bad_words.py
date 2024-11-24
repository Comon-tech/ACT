import requests
import json

# Define the API endpoint
url = "https://vector.profanity.dev"

# List of offensive words
offensive_words = ["fuck","motherfucker","fucker","motherfucker","shit","whore","asshole","bitch","ass","nigga", "Israel", "israel","nazi","jew","coon","dild","dildo","rape","dick","porn","penis","killyourself","whore","slut","twat","x-rated","xrated","18+","gore","cock","cum","cancer", "idiot", "vagina" ]

def check_for_bad_words(message):
    loop_index = 0
    split_messages = []
    temp_words = ""
    loop_index_max = len(message.split(" "))

    for index, wrd in enumerate(message.split(" ")):
        temp_words += wrd + " "
        if loop_index == 9:
            split_messages.append(temp_words)
            loop_index = 0
            temp_words = ""
        elif loop_index_max == index + 1:
            split_messages.append(temp_words)
        else:
            loop_index += 1
    return split_messages

def split_msg_into_array(words):
    # for words in split_messages:
    data = {"message": words}

    # Set the headers
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Handle the response
    if response.status_code == 200:
        # print("Response:", response.json())
        response = response.json()
        if response["isProfanity"] == True:
            return True, response["flaggedFor"]

    return False, "safe"


# words = check_for_bad_words(message)
# for word in words:
#     true_or_false, flagge_word = split_msg_into_array(word)
#     if true_or_false:
#         print(f"Bad word found: {flagge_word}")
#     else:
#         print("No bad words found")