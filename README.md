# BillBot
A Twitter bot to help you stay informed with the state legislature. Concise ChatGPT powered summaries and analysis of every bill introduced in every U.S. state.

## Background

Hi everyone, my name is Byron and if you know me you know that I love chatGPT. Like many, I have a casual interest in politics, particularly local politics, as it tends to more directly impact my life. However, staying informed about newly introduced legislation can be challenging. Local news coverage is sparse, and who has time to decipher lengthy legislative bills?

That's where BillBot comes in! BillBot is a Twitter bot I created that helps you stay informed with local legislation.  Each week, BillBot finds the latest bills that have been introduced in your state, passes the bill text to chatGPT, and then posts an analysis of the legislation on Twitter in the form of a succinct thread. The analysis includes:
- A brief summary of the bill
- An advocate opinion
- An opposition opinion
- The affected population

In a few short tweets you can stay up to date on all that’s happening in you.

https://twitter.com/WABillBot

<img src="https://github.com/ByronPop/BillBot/assets/33380363/7b50d559-6a95-49e8-b10f-b61b7e0c194e" width="450"/> <img src="https://github.com/ByronPop/BillBot/assets/33380363/5a75f609-4a7c-4d4a-9bec-e439f21eb2d8" width="450"/> 

## How it Works
I wrote the script for BillBot in Python and leveraged 3 public APIs and a webscraper to pull the legislative bill data, pass it to ChatGPT and then post the analysis to Twitter. The script runs for each state and updates a separate BillBot Twitter account for the specific state (e.g., CABillBot, MABillBot). 

### Legislative Data
Openstates.org (https://openstates.org/) offers a free public API that contains legislative data for every U.S state. To get the bill data, I call the /bills endpoint and retrieve all of the bills introduced in a state during the last week.

```
def fetch_congressional_bills(input_state):
    # set up API key and base URL
    headers = {'x-api-key': 'YOUR API KEY', 'accept': 'application/json'}
    url = 'https://v3.openstates.org/bills'

    # Calculate the date range for the last week
    start_date = (datetime.datetime.now() - timedelta(days=7)).date().strftime('%Y-%m-%d')

    # set up parameters for bills introduced in the last week in the state
    params = {'jurisdiction': input_state, 'created_since': f'{start_date}', 'classification': 'bill', 'sort': 'updated_desc'}

    # make API request
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = json.loads(response.text)
        print(f"Total bills fetched: {len(data)}")
        return data
    else:
        print(f"Error fetching bills: {response.status_code}")
        return None

```
This gives me back a JSON list containing a list of bills and various metadata. Unfortunately, Openstates.org does not include the full bill text in their API. However, they do provide a link to where you can find the complete bill. I iterate over the list of bills and then use a selenium webscraper function to navigate to the link and parse out the bill text. 

```
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

```

### ChatGPT Integration
Once I have the full bill text, I pass it to ChatGPT's API. I spent a lot of time tryng to hone the promp to get ChatGPT to respond with a concise analysis. I discovered that ChatGPT cannot limit the number of characters it returns (e.g., <280 characters) however through clever prompting you can get it to work pretty well (read more here)

```
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

```

### Posting to Twitter
To post to Twitter I use the Tweepy API. Before I can tweet however, I need to clean the data response from ChatGPT. ChatGPT responds with a single block of text containing:
- A brief summary of the bill
- An advocate opinion
- An opposition opinion
- The affected population

In order to post the analysis to Twitter I parse the block into Tweets and store them in an array. 
```
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
```

Each Tweet must be less than 280 characters. Sometimes, ChatGPT fails to respond with an analysis that is <280 characters so I implemented a while loop to check the length of each Tweet and retry the GPT integration until I get an analysis where each section is the appropriate length. 

Once I have an acceptable set of Tweets, I post the initial Tweet:

```
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

```

I then call a separate function to reply to the initial tweet and post chatGPT analysis (the array of Tweets I created earlier)

```
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

```
