from flask import Flask, request, jsonify, render_template
import json
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from cachetools import cached, TTLCache
from datetime import datetime
from textblob import TextBlob

app = Flask(__name__)

# Cache for dynamic data (TTL: 3600 seconds = 1 hour)
cache = TTLCache(maxsize=100, ttl=3600)

# Load college data from JSON file
def load_college_data():
    try:
        with open('college_data.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "college_data.json file not found."}
    except json.JSONDecodeError:
        return {"error": "Error decoding college_data.json."}

# Web scraping function to get dynamic data (e.g., latest news and location)
@cached(cache)
def scrape_dynamic_data():
    try:
        url = "https://svce.edu.in/"  # Replace with the actual college URL
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Scrape latest news or announcements
        latest_news = [news_item.get_text(strip=True) for news_item in soup.select('.news-item')]
        
        # Scrape college location
        location_tag = soup.find('div', class_='college-location')  # Adjust selector as needed
        location = location_tag.get_text(strip=True) if location_tag else "Location information not available."
        
        return {"latest_news": latest_news, "location": location}
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except AttributeError:
        return {"error": "Error parsing HTML for dynamic data."}

# Serve the HTML page
@app.route('/')
def home():
    return render_template('index.html')

# Define known greetings and responses
greetings = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! What can I do for you?",
    "good morning": "Good morning! How can I help you?",
    "good evening": "Good evening! What do you need assistance with?",
    "hey": "Hey! How can I help you today?",
    "how are you": "I'm just a bot, but I'm here to help you!",
    "what's up": "Not much! How can I assist you?",
}

# Synonyms for known queries
query_synonyms = {
    "faculty": ["teachers", "professors", "staff"],
    "courses": ["subjects", "classes", "curriculum"],
    "fee structure": ["cost", "tuition", "fees"],
    "placements": ["jobs", "careers", "recruitment"],
    "address": ["location", "where"]
}

# List of known queries
known_queries = list(greetings.keys()) + list(query_synonyms.keys())

# Chatbot response function
@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_query = request.json.get('query', '').lower()
    college_data = load_college_data()
    
    if "error" in college_data:
        return jsonify({"response": college_data["error"]})

    # Use fuzzy matching to find the closest match for greetings
    best_match, score = process.extractOne(user_query, known_queries)
    threshold = 70  # Define a threshold score for a valid match

    # Determine greeting based on time of day
    current_hour = datetime.now().hour
    time_based_greeting = "Hi there!"

    if 5 <= current_hour < 12:
        time_based_greeting = "Good morning!"
    elif 12 <= current_hour < 18:
        time_based_greeting = "Good afternoon!"
    elif 18 <= current_hour < 22:
        time_based_greeting = "Good evening!"

    if score >= threshold:
        if best_match in greetings:
            response = greetings[best_match]
        else:
            # Check for query synonyms
            for key, synonyms in query_synonyms.items():
                if best_match == key or any(synonym in user_query for synonym in synonyms):
                    if key == "faculty":
                        name = user_query.split("about")[-1].strip()
                        response = get_faculty_info(name, college_data['faculty'])
                    elif key == "courses":
                        courses = [course['name'] for course in college_data['courses']]
                        response = "Courses offered: " + ", ".join(courses)
                    elif key == "fee structure":
                        response = (f"B.Tech Tuition Fee: {college_data['fee_structure']['B.Tech']['tuition_fee']}, "
                                    f"Hostel Fee: {college_data['fee_structure']['B.Tech']['hostel_fee']}, "
                                    f"Other Charges: {college_data['fee_structure']['B.Tech']['other_charges']}")
                    elif key == "placements":
                        response = (f"2023 Placement Rate: {college_data['placements']['2023']['placement_rate']}\n"
                                    f"Average Package: {college_data['placements']['2023']['average_package']}\n"
                                    f"Highest Package: {college_data['placements']['2023']['highest_package']}\n"
                                    f"Notable Recruiters: {', '.join(college_data['placements']['2023']['notable_recruiters'])}")
                    elif key == "address":
                        dynamic_data = scrape_dynamic_data()
                        response = dynamic_data.get("location", "Location data not available.")
                    else:
                        response = f"For more detailed information about {key}, please visit the college website or contact the college directly."
                    break
            else:
                response = "I'm not sure how to respond to that."
    else:
        # Fallback response if no valid match found
        response = (f"{time_based_greeting} I'm not sure how to respond to that. "
                    "Can you please provide more details or try asking something else?")

    # Analyze user sentiment
    sentiment = TextBlob(user_query).sentiment
    if sentiment.polarity < 0:
        response += " If you're having a tough time, I'm here to help."

    return jsonify({"response": response})

# Function to get faculty info
def get_faculty_info(name, faculty_data):
    for faculty in faculty_data:
        if faculty['name'].lower() == name.lower():
            return (f"Name: {faculty['name']}\nDepartment: {faculty['department']}\n"
                    f"Qualification: {faculty['qualification']}\n"
                    f"Research Interests: {faculty['research_interests']}\n"
                    f"Contact: {faculty['contact']}")
    return "Faculty member not found."

if __name__ == '__main__':
    app.run(debug=True)
