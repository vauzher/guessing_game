import streamlit as st
import openai
import os
from dotenv import load_dotenv
import random
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure OpenAI with explicit API key
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="Guessing Game", layout="wide")

def initialize_game_modes():
    if "game_mode" not in st.session_state:
        st.session_state.game_mode = "fruits"
    if "current_answer" not in st.session_state:
        st.session_state.current_answer = ""
    if "game_history" not in st.session_state:
        st.session_state.game_history = []

def get_answer_for_mode(mode):
    answers = {
        "fruits": ["apple", "banana", "orange", "mango", "strawberry"],
        "animals": ["elephant", "giraffe", "penguin", "lion", "dolphin"],
        "countries": ["france", "japan", "brazil", "egypt", "canada"]
    }
    return random.choice(answers[mode])

def initialize_stats():
    if "game_stats" not in st.session_state:
        st.session_state.game_stats = {
            "games_played": 0,
            "correct_guesses": 0,
            "total_guesses": 0,
            "mode_stats": {
                "fruits": {
                    "played": 0,
                    "wins": 0,
                    "avg_guesses": 0,
                    "total_guesses": 0
                },
                "animals": {
                    "played": 0,
                    "wins": 0,
                    "avg_guesses": 0,
                    "total_guesses": 0
                },
                "countries": {
                    "played": 0,
                    "wins": 0,
                    "avg_guesses": 0,
                    "total_guesses": 0
                }
            },
            "history": []
        }

def update_stats(mode, num_guesses, won=False):
    # Initialize stats if they don't exist
    initialize_stats()
    
    stats = st.session_state.game_stats
    stats["games_played"] += 1
    stats["total_guesses"] += num_guesses
    if won:
        stats["correct_guesses"] += 1
    
    # Update mode-specific stats
    mode_stats = stats["mode_stats"][mode]
    mode_stats["played"] += 1
    if won:
        mode_stats["wins"] += 1
    
    # Calculate average guesses for the mode
    total_mode_guesses = mode_stats.get("total_guesses", 0) + num_guesses
    mode_stats["total_guesses"] = total_mode_guesses
    mode_stats["avg_guesses"] = total_mode_guesses / max(1, mode_stats["played"])
    
    # Add to history with timestamp
    stats["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "mode": mode,
        "guesses": num_guesses,
        "won": won
    })
    
    # Debug print (optional - remove in production)
    print(f"Updated stats: Games played: {stats['games_played']}, Correct: {stats['correct_guesses']}")

def play_page():
    st.markdown("<h1 style='text-align: center;'>Guessing Game</h1>", unsafe_allow_html=True)
    
    # Initialize game states and stats
    initialize_game_modes()
    initialize_stats()  # Make sure stats are initialized
    
    # Game mode selector in sidebar
    new_mode = st.sidebar.selectbox(
        "Select Game Mode",
        ["fruits", "animals", "countries"],
        index=["fruits", "animals", "countries"].index(st.session_state.game_mode)
    )
    
    # Reset game if mode changes
    if new_mode != st.session_state.game_mode:
        st.session_state.game_mode = new_mode
        st.session_state.game_history = []
        st.session_state.current_answer = get_answer_for_mode(new_mode)
        st.rerun()
    
    # Initialize answer if not set
    if not st.session_state.current_answer:
        st.session_state.current_answer = get_answer_for_mode(st.session_state.game_mode)
    
    # Show initial hint and game information
    if not st.session_state.game_history:
        hints = {
            "fruits": "I'm thinking of a fruit...",
            "animals": "I'm thinking of an animal...",
            "countries": "I'm thinking of a country..."
        }
        
        st.info(f"""
        🎮 Welcome to the Guessing Game! 
        
        Current Mode: {st.session_state.game_mode.title()}
        
        Rules:
        - {hints[st.session_state.game_mode]}
        - Try to guess what it is!
        
        Type your guess below and I'll let you know if you're getting closer!
        """)
        
        # Get initial hint from OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are running a guessing game where the answer is '{st.session_state.current_answer}'. Provide an initial cryptic hint that makes the game fun but doesn't give away the answer too easily. Make it playful and engaging."},
                    {"role": "user", "content": "Give me the first hint but it should not be easy hint."}
                ]
            )
            initial_hint = response.choices[0].message.content
            st.session_state.game_history.append({"user": "Game Start", "bot": initial_hint})
        except Exception as e:
            st.error(f"Error communicating with OpenAI: {str(e)}")
    
    # Display chat history
    for i, chat in enumerate(st.session_state.game_history):
        with st.chat_message("user"):
            st.write(chat["user"])
        with st.chat_message("assistant"):
            st.write(chat["bot"])
    
    # User input
    user_input = st.chat_input("Type your guess here...")
    
    if user_input:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are running a guessing game where the answer is '{st.session_state.current_answer}'. Evaluate the user's guess and respond with whether they are correct or not. If they're wrong, provide a new hint that helps them get closer without making it too obvious."},
                    {"role": "user", "content": user_input}
                ]
            )
            evaluation = response.choices[0].message.content
            st.session_state.game_history.append({"user": user_input, "bot": evaluation})
            
            # Check if user guessed correctly and update stats
            if user_input.lower() == st.session_state.current_answer.lower():
                # Update stats before resetting the game
                num_guesses = len([msg for msg in st.session_state.game_history 
                                 if msg["user"] != "Game Start"])
                update_stats(
                    mode=st.session_state.game_mode,
                    num_guesses=num_guesses,
                    won=True
                )
                
                st.balloons()
                # Reset for next game
                st.session_state.current_answer = get_answer_for_mode(st.session_state.game_mode)
                st.session_state.game_history = []
            
            st.rerun()
        except Exception as e:
            st.error(f"Error communicating with OpenAI: {str(e)}")

def stats_page():
    st.markdown("<h1 style='text-align: center;'>Game Statistics</h1>", unsafe_allow_html=True)
    
    # Initialize stats if needed
    initialize_stats()
    stats = st.session_state.game_stats
    
    # Overall Statistics
    st.subheader("📊 Overall Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Games", stats["games_played"])
    with col2:
        win_rate = (stats["correct_guesses"] / max(1, stats["games_played"])) * 100
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        avg_guesses = stats["total_guesses"] / max(1, stats["games_played"])
        st.metric("Avg Guesses", f"{avg_guesses:.1f}")
    with col4:
        st.metric("Total Correct", stats["correct_guesses"])
    
    # Mode Performance
    st.subheader("🎮 Performance by Mode")
    mode_data = []
    for mode, mode_stats in stats["mode_stats"].items():
        win_rate = (mode_stats["wins"] / max(1, mode_stats["played"])) * 100
        mode_data.append({
            "Mode": mode.title(),
            "Games Played": mode_stats["played"],
            "Win Rate": win_rate,
            "Avg Guesses": mode_stats["avg_guesses"]
        })
    
    df_modes = pd.DataFrame(mode_data)
    fig_modes = go.Figure(data=[
        go.Bar(name="Games Played", x=df_modes["Mode"], y=df_modes["Games Played"]),
        go.Bar(name="Win Rate %", x=df_modes["Mode"], y=df_modes["Win Rate"])
    ])
    fig_modes.update_layout(barmode='group', title="Mode Statistics")
    st.plotly_chart(fig_modes)
    
    # Recent Games History
    st.subheader("📜 Recent Games History")
    if stats["history"]:
        df_history = pd.DataFrame(stats["history"][-10:])  # Last 10 games
        fig_history = px.line(df_history, 
                            x="date", 
                            y="guesses",
                            color="mode",
                            markers=True,
                            title="Number of Guesses Over Time")
        st.plotly_chart(fig_history)
        
        # Recent games table
        st.dataframe(
            df_history.style.apply(lambda x: ['background-color: #90EE90' if v else '' 
                                            for v in x == True], 
                                 subset=['won'])
        )
    else:
        st.info("No games played yet!")
    
    # Achievement Section
    st.subheader("🏆 Achievements")
    achievements = {
        "Quick Thinker": {"desc": "Guess correctly in 3 or fewer attempts", "achieved": avg_guesses <= 3},
        "Master Guesser": {"desc": "Win 5 games in a row", "achieved": stats["correct_guesses"] >= 5},
        "Mode Expert": {"desc": "Win in all game modes", "achieved": all(m["wins"] > 0 for m in stats["mode_stats"].values())}
    }
    
    col1, col2 = st.columns(2)
    for i, (name, ach) in enumerate(achievements.items()):
        with col1 if i % 2 == 0 else col2:
            if ach["achieved"]:
                st.success(f"🌟 {name}: {ach['desc']}")
            else:
                st.info(f"🔒 {name}: {ach['desc']}")

pages = {
    "Play": play_page,
    "Stats": stats_page
}

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    pages[selection]()

if __name__ == "__main__":
    main()




