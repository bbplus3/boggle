import random
import string
import time
import nltk
from nltk.corpus import words
from htmltools import tags
from itertools import product
from shiny import *
#shiny run shiny_boggle.py --port 8080

# Download word list if not already downloaded
nltk.download("words", quiet=True)
english_words = set(words.words())

#GRID_SIZE = 4  # 4x4 Boggle grid

#def generate_grid():
#    return [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Boggle dice (4x4 board, includes "Qu")
BOGGLE_DICE = [
    ["A", "A", "E", "E", "G", "N"],
    ["E", "L", "R", "T", "T", "Y"],
    ["A", "O", "O", "T", "T", "W"],
    ["A", "B", "B", "J", "O", "O"],
    ["E", "H", "R", "T", "V", "W"],
    ["C", "I", "M", "O", "T", "U"],
    ["D", "I", "S", "T", "T", "Y"],
    ["E", "I", "O", "S", "S", "T"],
    ["D", "E", "L", "R", "V", "Y"],
    ["A", "C", "H", "O", "P", "S"],
    ["H", "I", "M", "N", "Qu", "U"],
    ["E", "E", "I", "N", "S", "U"],
    ["E", "E", "G", "H", "N", "W"],
    ["A", "F", "F", "K", "P", "S"],
    ["H", "L", "N", "N", "R", "Z"],
    ["D", "E", "I", "L", "R", "X"]
]

SCORE_TABLE = {
    3: 1,
    4: 1,
    5: 2,
    6: 3,
    7: 5,
    8: 11
}

# Create board
def generate_grid():
    random.shuffle(BOGGLE_DICE)
    return [[random.choice(die) for die in BOGGLE_DICE[i*4:(i+1)*4]] for i in range(4)]

def in_bounds(x, y):
    return 0 <= x < 4 and 0 <= y < 4

# Recursive DFS search for a word on the board
def is_valid_word(board, word):
    word = word.upper()

    def dfs(x, y, idx, visited):
        if idx == len(word):
            return True
        for dx, dy in product([-1, 0, 1], repeat=2):
            nx, ny = x + dx, y + dy
            if (dx == dy == 0) or not in_bounds(nx, ny) or (nx, ny) in visited:
                continue
            cell = board[nx][ny].upper()
            target = word[idx:idx+len(cell)]
            if target == cell:
                if dfs(nx, ny, idx + len(cell), visited | {(nx, ny)}):
                    return True
        return False

    for x in range(4):
        for y in range(4):
            cell = board[x][y].upper()
            if word.startswith(cell):
                if dfs(x, y, len(cell), {(x, y)}):
                    return True
    return False


def score_word(word):
    length = len(word)
    if length < 3:
        return 0
    elif length <= 4:
        return 1
    elif length == 5:
        return 2
    elif length == 6:
        return 3
    elif length == 7:
        return 5
    else:
        return 11

# UI
app_ui = ui.page_fluid(
    ui.h2("🔤 Boggle Game"),
    ui.a("How to play Boggle", href="https://en.wikipedia.org/wiki/Boggle", target="_blank"),
    ui.output_text("timer"),
    ui.row(
        ui.column(6, ui.output_ui("letter_grid")),
        ui.column(6,
            ui.input_text("word_input", "Enter word:", ""),
            ui.input_action_button("submit_word", "Submit"),
            ui.input_action_button("shuffle", "Shuffle Letters"),
            ui.output_text("feedback"),
            ui.output_text_verbatim("word_list"),
            ui.output_text("score")
        ),
        
    ),
)

def server(input, output, session):
    grid = reactive.value(generate_grid())
    word_history = reactive.value([])
    total_score = reactive.value(0)
    feedback_msg = reactive.value("")
    game_end_time = reactive.value(time.time() + 180)

    def reset_game():
        grid.set(generate_grid())
        word_history.set([])
        total_score.set(0)
        feedback_msg.set("")
        game_end_time.set(time.time() + 180)

    @reactive.Effect
    @reactive.event(input.shuffle)
    def _():
        reset_game()

    @output
    @render.ui
    def letter_grid():
        return tags.div(
            {"style": "display: grid; grid-template-columns: repeat(4, 60px); gap: 10px;"},
            *[
                tags.div(
                    letter,
                    style="border: 1px solid #333; text-align: center; font-size: 24px; padding: 14px; border-radius: 10px; background-color: #f0f0f0;"
                )
                for row in grid() for letter in row
            ]
        )

    @output
    @render.ui
    def timer():
        reactive.invalidate_later(1000)  # Update every 1000 ms = 1 second
        remaining = int(game_end_time() - time.time())
        if remaining >= 0:
            minutes, seconds = divmod(remaining, 60)
            # FEATURE UNDER CONSTRUCTION
            #return f"⏳ Time left: {minutes:02}:{seconds:02}"
        elif remaining <= 0:
            return "⏰ Time is up!"

    @output
    @render.text
    def feedback():
        return feedback_msg()

    @output
    @render.text
    def word_list():
        return "📜 Words found:\n" + "\n".join(word_history())

    @output
    @render.text
    def score():
        return f"🏆 Total Score: {total_score()}"

    @reactive.Effect
    @reactive.event(input.submit_word)
    def process_word():
        word = input.word_input().upper().strip()
        if time.time() > game_end_time():
            feedback_msg.set("⏰ Time is up!")
            return
        if len(word) < 3:
            feedback_msg.set(f"❌ '{word}' is too short.")
        elif word.lower() not in english_words:
            feedback_msg.set(f"❌ '{word}' is not a valid English word.")
        elif word in word_history():
            feedback_msg.set(f"⚠️ You already found '{word}'.")
        else:
            word_history.set(word_history() + [word])
            word_score = score_word(word)
            total_score.set(total_score() + word_score)
            feedback_msg.set(f"✅ '{word}' accepted! (+{word_score} points)")

app = App(app_ui, server)