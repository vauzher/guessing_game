import streamlit as st
from dotenv import load_dotenv
import os
import openai
import numpy as np
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Verify the API key is loaded
if not openai.api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

# Set page conf.
st.set_page_config(page_title="Guessing Game", layout="wide")

# Load CSS from a file
# def load_css(file_name):
#     with open(file_name) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# load_css("styles.css")

# pages
def play_page():
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<div class="title">Guessing Game</div>', unsafe_allow_html=True)
    
    # Initialize game state
    if "game_history" not in st.session_state:
        st.session_state.game_history = []
    
    # Chat component for the guessing game
    chat_container = st.container()
    
    with chat_container:
        # Get user guess
        user_guess = st.text_input("Your guess:", "", key="user_guess", help="Type your guess here")
        
        if st.button("Submit Guess", key="submit_guess", help="Click to submit your guess"):
            # Evaluate the guess
            correct_answer = "apple"
            if user_guess.lower() == correct_answer.lower():
                evaluation = "Yes, that's the correct answer!"
            else:
                evaluation = "No, that's not the correct answer. Try again."
            
            # Add the guess and evaluation to the game history
            st.session_state.game_history.append({"guess": user_guess, "evaluation": evaluation})
            
            # Display the guess and evaluation
            st.write(f"You guessed: {user_guess}")
            st.write(f"Evaluation: {evaluation}")
    
    # Display the chat history
    st.markdown('<div class="history">', unsafe_allow_html=True)
    for i, entry in enumerate(st.session_state.game_history):
        st.markdown(f'<div class="history-item">{i+1}. Guess: {entry["guess"]}, Evaluation: {entry["evaluation"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def stats_page():
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<div class="title">Game Statistics</div>', unsafe_allow_html=True)
    
    # Retrieve game history from session state
    game_history = st.session_state.get("game_history", [])
    
    # Calculate statistics
    num_games = len(game_history)
    num_guesses = [1 for entry in game_history]  # Each entry is a single guess
    avg_guesses = np.mean(num_guesses) if num_guesses else 0
    
    # Display statistics
    st.write(f"Number of games played: {num_games}")
    st.write(f"Average number of guesses per game: {avg_guesses:.2f}")
    
    # Plot a bar chart of the number of guesses per game
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(1, num_games+1), num_guesses)
    ax.set_xlabel("Game")
    ax.set_ylabel("Number of Guesses")
    ax.set_title("Number of Guesses per Game")
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

pages = {
    "Play": play_page,
    "Stats": stats_page
}

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Call the selected page function
    pages[selection]()

if __name__ == "__main__":
    main()