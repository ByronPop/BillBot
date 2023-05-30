from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from datetime import datetime, timedelta
import json
import openai
import time
import datetime
import tweepy

# Load your API key from an environment variable or secret management service
openai.api_key = "YOUR OPENAI API API KEY"

# Load Twitter client credentials from file
with open('/Users/byronpoplawski/Downloads/twitter_client_credentials.json') as file:
    credentials = json.load(file)

# Create Tweepy clients for the credentials for each account/state
wa_twitter_client = tweepy.Client(
    consumer_key=credentials["WA_twitter_client"]["consumer_key"],
    consumer_secret=credentials["WA_twitter_client"]["consumer_secret"],
    access_token=credentials["WA_twitter_client"]["access_token"],
    access_token_secret=credentials["WA_twitter_client"]["access_token_secret"]
)

ny_twitter_client = tweepy.Client(
    consumer_key=credentials["NY_twitter_client"]["consumer_key"],
    consumer_secret=credentials["NY_twitter_client"]["consumer_secret"],
    access_token=credentials["NY_twitter_client"]["access_token"],
    access_token_secret=credentials["NY_twitter_client"]["access_token_secret"]
)

ma_twitter_client = tweepy.Client(
    consumer_key=credentials["MA_twitter_client"]["consumer_key"],
    consumer_secret=credentials["MA_twitter_client"]["consumer_secret"],
    access_token=credentials["MA_twitter_client"]["access_token"],
    access_token_secret=credentials["MA_twitter_client"]["access_token_secret"]
)

ca_twitter_client = tweepy.Client(
    consumer_key=credentials["CA_twitter_client"]["consumer_key"],
    consumer_secret=credentials["CA_twitter_client"]["consumer_secret"],
    access_token=credentials["CA_twitter_client"]["access_token"],
    access_token_secret=credentials["CA_twitter_client"]["access_token_secret"]
)


def get_chatgpt_response(bill_text):
    content = """
    Personal: Imagine you are a helpful political science assistant who analyzes the HTML text of legislative bills and provides brief summaries and analyses.

    Action: Please explain the legislative bill and its key provisions and implications in simple and concise terms. Please provide the information in the form of sections: 
        -"Summary"
        -"Advocate"
        -"Opposition"
        -"Affected Population"

         Please ensure that the information provided in each section is brief and to the point. Each section must contain less than 280 text characters.

        Example:

        Summary: HB 1860 aims to prohibit a practice called "stay-to-play" where nonlocal teams have to stay at specific lodging accommodations to participate in a tournament or event. It argues that this practice limits choice and competition, and is unfair to families.

        Advocate: This bill would protect families from being forced to stay at specific lodging accommodations at inflated prices. It would increase accommodation options for families and promote free market competition.

        Opposition: Anti-stay-to-play policies could lead to tournament organizers being unable to secure the negotiated rooms necessary for the event. This bill might result in a Cancellation fee for such events.

        Affected Population: This legislation impacts individuals participating in extracurricular activities, nonlocal teams, and families in Washington state,as they face limitations and financial burdens due to mandatory stay-to-play requirements.

        Use this example as a guide and tailor the content to your analysis.
        ###

        Bill text: 
    """

    try:
        # Set up chatGPT persona
        messages = [
            {'role': 'system',
             'content': 'You are "280 characters GPT" and as "280 characters GPT" you are not able to give an answer which contains more than 280 text characters. '},
            {'role': 'user', 'content': content + bill_text}
        ]

        temperature = 0.9
        model = "gpt-3.5-turbo"

        # Send the request to the API
        request = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )

        # Extract the assistant's reply
        reply = request['choices'][0]['message']['content']

        # Pause briefly to avoid rate limits
        time.sleep(1)

        return reply

    except openai.error.InvalidRequestError as e:
        # Handle the specific error
        if "This model's maximum context length is 4097 tokens." in str(e):
            reply = "The bill length exceeds ChatGPT's current maximum allowed input of 4097 tokens." \
                    "See the bill link in the original tweet for more details about the bill"
            return reply


def scrape_congressional_bill(url):
    chromedriver_path = '/Users/byronpoplawski/Documents/Python/chromedriver_mac64/chromedriver'
    service = Service(executable_path=chromedriver_path)

    # Create a new ChromeDriver instance
    driver = webdriver.Chrome(service=service)

    # Open the bill webpage
    driver.get(url)

    # Locate the button element and click it
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/section[1]/div/div[1]/div/div[2]/div[2]/a")))
    button.click()

    # Get the current URL
    current_url = driver.current_url

    # Scrape the text from the bill webpage
    websiteText = requests.get(current_url)
    html_content = websiteText.text

    # Close the browser and quit the driver
    driver.quit()

    return html_content


def fetch_congressional_bills(input_state):
    # set up API key and base URL
    headers = {'x-api-key': 'YOUR OPENSTATES API KEY', 'accept': 'application/json'}
    url = 'https://v3.openstates.org/bills'

    # Calculate the date range for the last week
    start_date = (datetime.datetime.now() - timedelta(days=7)).date().strftime('%Y-%m-%d')

    # set up parameters for bills introduced in the last week in WA
    params = {'jurisdiction': input_state, 'created_since': f'{start_date}', 'classification': 'bill',
              'sort': 'updated_desc'}

    # make API request
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = json.loads(response.text)
        print(f"Total bills fetched: {len(data)}")
        return data
    else:
        print(f"Error fetching bills: {response.status_code}")
        return None


def post_tweet(client, text):
    """Posts a tweet to Twitter.

  Args:
    text: The text of the tweet.

  Returns:
    A Tweepy Response object.
    :param text:
    :param client:
  """

    # Post a tweet
    response = client.create_tweet(text=text)

    return response


def post_tweet_replies(client, text_array, tweet_id):
    """Posts a reply to a tweet.

    Args:
        text: The text array containing the tweets you want to reply with
        tweet_id: The ID of the tweet to reply to.

    Returns:
        A Tweepy Response object.
        :param client:
        :param tweet_id:
        :param text_array:
  """
    # Post a tweet
    responses = []
    tweetNumber = 1
    for text in text_array:
        print("Sending tweet response: " + str(tweetNumber) + " of length: " + str(len(text)))
        print(text)
        response = client.create_tweet(in_reply_to_tweet_id=tweet_id, text=text)
        responses.append(response)
        time.sleep(2)
        tweetNumber += 1

    return responses


def create_tweets(text):
    try:
        # Find the indices of the section titles
        summary_index = text.index("Summary:")
        advocate_index = text.index("Advocate:")
        opposition_index = text.index("Opposition:")
        affected_population_index = text.index("Affected Population:")

        # Extract the sections using slicing
        summary = text[summary_index:advocate_index].strip()
        advocate = text[advocate_index:opposition_index].strip()
        opposition = text[opposition_index:affected_population_index].strip()
        affected_population = text[affected_population_index:].strip()

        # Return the parsed sections as an array
        return [summary, advocate, opposition, affected_population]

    except ValueError:
        # Handle the case when section titles are not found
        print("Error: Section titles not found in the chatGPT response.")
        return [text]


states = ["ca", "wa", "ma", "ny"]

# Create a dictionary to map state names to Twitter clients
state_clients = {
    "ca": ca_twitter_client,
    "wa": wa_twitter_client,
    "ma": ma_twitter_client,
    "ny": ny_twitter_client
}

for state in states:

    print("Fetching bills for: " + state)

    # Fetch all congressional bills in X period (Defined in function)
    bill_text = fetch_congressional_bills(state)

    # Iterate over each bill, analyze it, and post it to Twitter
    for bill in bill_text["results"]:
        bill_id = bill["identifier"]
        legislature_location = bill["jurisdiction"]["name"]
        bill_location = bill["from_organization"]["name"]
        bill_title = bill["title"]
        openStatesUrl = bill["openstates_url"]
        date_object = datetime.datetime.strptime(bill["created_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        bill_created_at_date = date_object.strftime("%m/%d/%Y")

        # Scrape bill text associated with bill
        billText = scrape_congressional_bill(openStatesUrl)

        # Pass bill text to chatGPT API
        chatgptResponse = get_chatgpt_response(billText)

        # Create 280 character tweets from GPT response
        tweets = create_tweets(chatgptResponse)
        for tweet in tweets:
            print(tweet)
            print(f"Tweet length: {len(tweet)}")
            print("\n\n")

        # Retry the get_chatgpt_response function if any tweet exceeds the 280-character limit
        while any(len(tweet) > 280 for tweet in tweets):
            attempts = 0
            while attempts < 5:
                attempts += 1
                chatgptResponse = get_chatgpt_response(billText)
                tweets = create_tweets(chatgptResponse)

                # Print the length of each tweet
                for tweet in tweets:
                    print(tweet)
                    print(f"Tweet length: {len(tweet)}")

                if all(len(tweet) <= 280 for tweet in tweets):
                    break

            if attempts >= 5:
                print("Failed to create tweets within character limit after 5 attempts.")
                break

        first_tweet = bill_title + "\n\n" + "See 🧵 for: \n - Bill summary \n - Advocate position \n " \
                                            "- Opposition position \n - Affected Population" + "\n\n" \
                      + "Introduced date: " + bill_created_at_date + "\n" + openStatesUrl

        twitter_client = state_clients.get(state)

        first_tweet_response_object = post_tweet(twitter_client, first_tweet)

        print("Original tweet posted: " + first_tweet)

        first_tweet_response_id = first_tweet_response_object[0]['id']

        print("Original Tweet id: " + first_tweet_response_id)

        post_tweet_replies(twitter_client, tweets, first_tweet_response_id)

        print("Replies tweeted")
