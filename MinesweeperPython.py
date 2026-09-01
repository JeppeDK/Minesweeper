import tkinter as tk
import random
import time
import requests
import os
import sys


# ============================================================
# SUPABASE SETTINGS
# ============================================================

SUPABASE_URL = "https://iyevbpqudzcvrzuqsdzi.supabase.co"

SUPABASE_KEY = "sb_publishable_Rgnfbg6IIxKJhzgoj5e_Fw_i6fJF9j5"

TABLE_NAME = "minesweeper_scores"


# ============================================================
# RESOURCE PATH
# ============================================================

def get_resource_path(filename):

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

    return os.path.join(
        base_path,
        filename
    )


# ============================================================
# SUPABASE FUNCTIONS
# ============================================================

def supabase_headers():

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


def upload_score(name, difficulty, seconds):

    name = name.strip()[:16]

    if not name:
        name = "Anonymous"

    seconds = int(seconds)

    try:

        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

        # ====================================================
        # CHECK EXISTING SCORE
        # ====================================================

        params = {
            "select": "player,difficulty,time_seconds",
            "player": f"eq.{name}",
            "difficulty": f"eq.{difficulty}",
            "limit": "1"
        }

        response = requests.get(
            url,
            headers=supabase_headers(),
            params=params,
            timeout=5
        )

        print()
        print("========================================")
        print("SUPABASE SCORE CHECK")
        print("========================================")
        print("Status:", response.status_code)
        print("Response:", response.text)

        if response.status_code != 200:

            print("ERROR: Could not check existing score.")

            return False

        existing = response.json()

        # ====================================================
        # PLAYER ALREADY HAS A SCORE
        # ====================================================

        if existing:

            old_time = int(
                existing[0]["time_seconds"]
            )

            print(
                f"Existing score: "
                f"{name} | {difficulty} | {old_time}s"
            )

            # ------------------------------------------------
            # New score is NOT better
            # ------------------------------------------------

            if seconds >= old_time:

                print(
                    f"Not updating because "
                    f"{old_time}s is already better."
                )

                return True

            # =================================================
            # UPDATE EXISTING SCORE
            # =================================================

            update_params = {
                "player": f"eq.{name}",
                "difficulty": f"eq.{difficulty}"
            }

            update_data = {
                "time_seconds": seconds
            }

            response = requests.patch(
                url,
                headers=supabase_headers(),
                params=update_params,
                json=update_data,
                timeout=5
            )

            print()
            print("========================================")
            print("SUPABASE UPDATE")
            print("========================================")
            print("Status:", response.status_code)
            print("Response:", response.text)

            if response.status_code not in (200, 204):

                print("ERROR: Supabase update failed.")

                return False

            # =================================================
            # VERIFY UPDATE
            # =================================================

            verify_params = {
                "select": "player,difficulty,time_seconds",
                "player": f"eq.{name}",
                "difficulty": f"eq.{difficulty}",
                "limit": "1"
            }

            verify = requests.get(
                url,
                headers=supabase_headers(),
                params=verify_params,
                timeout=5
            )

            print()
            print("========================================")
            print("SUPABASE UPDATE VERIFICATION")
            print("========================================")
            print("Status:", verify.status_code)
            print("Response:", verify.text)

            if verify.status_code != 200:

                print("ERROR: Could not verify update.")

                return False

            rows = verify.json()

            if not rows:

                print(
                    "ERROR: Supabase returned no row "
                    "after the update."
                )

                return False

            actual_time = int(
                rows[0]["time_seconds"]
            )

            print(
                f"Database currently says: "
                f"{name} | {difficulty} | {actual_time}s"
            )

            if actual_time == seconds:

                print(
                    f"SUCCESS: New best score for "
                    f"{name}: {seconds}s"
                )

                return True

            print(
                f"ERROR: Expected {seconds}s "
                f"but database contains {actual_time}s"
            )

            return False

        # ====================================================
        # NO PREVIOUS SCORE -> INSERT
        # ====================================================

        data = {
            "player": name,
            "difficulty": difficulty,
            "time_seconds": seconds
        }

        response = requests.post(
            url,
            headers=supabase_headers(),
            json=data,
            timeout=5
        )

        print()
        print("========================================")
        print("SUPABASE INSERT")
        print("========================================")
        print("Status:", response.status_code)
        print("Response:", response.text)

        if response.status_code not in (200, 201):

            print("ERROR: Supabase insert failed.")

            return False

        # ====================================================
        # VERIFY INSERT
        # ====================================================

        verify_params = {
            "select": "player,difficulty,time_seconds",
            "player": f"eq.{name}",
            "difficulty": f"eq.{difficulty}",
            "limit": "1"
        }

        verify = requests.get(
            url,
            headers=supabase_headers(),
            params=verify_params,
            timeout=5
        )

        print()
        print("========================================")
        print("SUPABASE INSERT VERIFICATION")
        print("========================================")
        print("Status:", verify.status_code)
        print("Response:", verify.text)

        if verify.status_code != 200:

            print("ERROR: Could not verify inserted score.")

            return False

        rows = verify.json()

        if not rows:

            print(
                "ERROR: Insert reported success, "
                "but no row was found afterwards."
            )

            return False

        actual_time = int(
            rows[0]["time_seconds"]
        )

        print(
            f"Database contains: "
            f"{name} | {difficulty} | {actual_time}s"
        )

        if actual_time == seconds:

            print(
                f"SUCCESS: Score uploaded for "
                f"{name}: {seconds}s"
            )

            return True

        print(
            f"ERROR: Expected {seconds}s "
            f"but database contains {actual_time}s"
        )

        return False

    except requests.RequestException as error:

        print()
        print("========================================")
        print("SUPABASE CONNECTION ERROR")
        print("========================================")
        print(error)

        return False

    except Exception as error:

        print()
        print("========================================")
        print("UNEXPECTED SUPABASE ERROR")
        print("========================================")
        print(error)

        return False


def get_scores(difficulty):

    try:

        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

        params = {
            "select": "player,difficulty,time_seconds",
            "difficulty": f"eq.{difficulty}",
            "order": "time_seconds.asc",
            "limit": "10"
        }

        response = requests.get(
            url,
            headers=supabase_headers(),
            params=params,
            timeout=5
        )

        print()
        print("========================================")
        print("SUPABASE LEADERBOARD")
        print("========================================")
        print("Difficulty:", difficulty)
        print("Status:", response.status_code)
        print("Response:", response.text)

        if response.status_code != 200:

            print("Supabase leaderboard error.")

            return []

        scores = response.json()

        print(
            f"Leaderboard returned {len(scores)} score(s)."
        )

        return scores

    except requests.RequestException as error:

        print("Connection error:", error)

        return []

    except Exception as error:

        print("Leaderboard error:", error)

        return []


# ============================================================
# MINESWEEPER
# ============================================================

class Minesweeper:

    def __init__(self, root):

        self.root = root

        self.root.title("Minesweeper")

        # ====================================================
        # ICON
        # ====================================================

        try:

            icon_path = get_resource_path("icon.ico")

            if os.path.exists(icon_path):

                self.root.iconbitmap(icon_path)

        except Exception as error:

            print("Could not load icon:", error)

        # ====================================================
        # WINDOW
        # ====================================================

        self.root.geometry("500x550")

        self.root.minsize(
            300,
            350
        )

        # ====================================================
        # DIFFICULTIES
        # ====================================================

        self.difficulties = {

            "Easy": (
                8,
                8,
                10
            ),

            "Medium": (
                16,
                16,
                40
            ),

            "Hard": (
                30,
                16,
                99
            ),

            "Impossible": (
                40,
                24,
                200
            )
        }

        self.difficulty = "Easy"

        self.width = 8

        self.height = 8

        self.mine_count = 10

        # ====================================================
        # GAME STATE
        # ====================================================

        self.mines = set()

        self.revealed = set()

        self.flags = set()

        self.board = []

        self.first_click = True

        self.game_over = False

        self.won = False

        self.start_time = None

        self.elapsed = 0

       

        # ====================================================
        # DRAWING
        # ====================================================

        self.cell_size = 20

        self.offset_x = 0

        self.offset_y = 0

        self.hidden_color = "#bdbdbd"

        self.hidden_hover = "#d0d0d0"

        self.revealed_color = "#dedede"

        self.grid_color = "#888888"

        self.number_colors = {

            1: "#0000ff",
            2: "#008000",
            3: "#ff0000",
            4: "#000080",
            5: "#800000",
            6: "#008080",
            7: "#000000",
            8: "#555555"
        }

        # ====================================================
        # UI
        # ====================================================

        self.create_ui()

        self.canvas.bind(
            "<Button-1>",
            self.left_click
        )

        self.canvas.bind(
            "<Button-3>",
            self.right_click
        )

        self.canvas.bind(
            "<Motion>",
            self.mouse_move
        )

        self.canvas.bind(
            "<Leave>",
            self.mouse_leave
        )

        self.root.bind(
            "<Configure>",
            self.on_resize
        )

        self.new_game()

        self.update_timer()

    # ========================================================
    # SECRET KEY
    # ========================================================

    def secret_key(self, event):

        key = event.keysym

        if self.game_over:

            return

        # Only process arrow keys
        if key not in self.secret_code:

            return

        expected = self.secret_code[
            self.secret_progress
        ]

        if key == expected:

            self.secret_progress += 1

            if self.secret_progress == len(
                self.secret_code
            ):

                self.secret_progress = 0

                self.auto_win()

        else:

            self.secret_progress = 0

            if key == self.secret_code[0]:

                self.secret_progress = 1

    # ========================================================
    # AUTO WIN
    # ========================================================

    def auto_win(self):

        if self.game_over:

            return

        # ----------------------------------------------------
        # Create board if this is before first click
        # ----------------------------------------------------

        if self.first_click:

            row = self.height // 2

            col = self.width // 2

            self.generate_mines(
                row,
                col
            )

            self.first_click = False

            self.start_time = time.time()

        # ----------------------------------------------------
        # Make sure timer exists
        # ----------------------------------------------------

        if self.start_time is None:

            self.start_time = time.time()

        # ----------------------------------------------------
        # Reveal every safe square
        # ----------------------------------------------------

        for row in range(self.height):

            for col in range(self.width):

                if (row, col) not in self.mines:

                    self.revealed.add(
                        (row, col)
                    )

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        self.elapsed = max(
            1,
            int(
                time.time()
                - self.start_time
            )
        )

        # ----------------------------------------------------
        # Normal win process
        # ----------------------------------------------------

        self.win_game()

    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):

        top = tk.Frame(
            self.root
        )

        top.pack(
            fill="x",
            padx=8,
            pady=8
        )

        # ====================================================
        # DIFFICULTY
        # ====================================================

        tk.Label(
            top,
            text="Difficulty:"
        ).pack(
            side="left"
        )

        self.difficulty_var = tk.StringVar(
            value="Easy"
        )

        self.difficulty_menu = tk.OptionMenu(
            top,
            self.difficulty_var,
            *self.difficulties.keys(),
            command=self.change_difficulty
        )

        self.difficulty_menu.config(
            font=("Arial", 10)
        )

        self.difficulty_menu.pack(
            side="left",
            padx=5
        )

        # ====================================================
        # NAME
        # ====================================================

        tk.Label(
            top,
            text="Name:"
        ).pack(
            side="left",
            padx=(8, 2)
        )

        self.name_var = tk.StringVar()

        self.name_entry = tk.Entry(
            top,
            textvariable=self.name_var,
            width=14
        )

        self.name_entry.pack(
            side="left",
            padx=3
        )

        # ====================================================
        # NEW GAME
        # ====================================================

        tk.Button(
            top,
            text="New Game",
            command=self.new_game
        ).pack(
            side="left",
            padx=3
        )

        # ====================================================
        # LEADERBOARD
        # ====================================================

        tk.Button(
            top,
            text="🏆 Leaderboard",
            command=self.show_leaderboard
        ).pack(
            side="left",
            padx=3
        )

        # ====================================================
        # STATUS
        # ====================================================

        status = tk.Frame(
            self.root
        )

        status.pack(
            fill="x",
            padx=10
        )

        self.mine_label = tk.Label(
            status,
            text="💣 10",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        self.mine_label.pack(
            side="left"
        )

        self.timer_label = tk.Label(
            status,
            text="⏱ 0",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        self.timer_label.pack(
            side="right"
        )

        # ====================================================
        # BOARD
        # ====================================================

        self.canvas = tk.Canvas(
            self.root,
            bg=self.hidden_color,
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

    # ========================================================
    # NEW GAME
    # ========================================================

    def new_game(self):

        self.mines.clear()

        self.revealed.clear()

        self.flags.clear()

        self.first_click = True

        self.game_over = False

        self.won = False

        self.start_time = None

        self.elapsed = 0

        self.secret_progress = 0

        self.board = [

            [0 for _ in range(self.width)]

            for _ in range(self.height)
        ]

        self.canvas.delete(
            "all"
        )

        self.update_status()

        self.timer_label.config(
            text="⏱ 0"
        )

        self.draw_board()

    # ========================================================
    # DIFFICULTY
    # ========================================================

    def change_difficulty(
        self,
        difficulty
    ):

        self.difficulty = difficulty

        (
            self.width,
            self.height,
            self.mine_count
        ) = self.difficulties[difficulty]

        self.new_game()

    # ========================================================
    # GENERATE MINES
    # ========================================================

    def generate_mines(
        self,
        safe_row,
        safe_col
    ):

        safe = set()

        for dr in (-1, 0, 1):

            for dc in (-1, 0, 1):

                r = safe_row + dr

                c = safe_col + dc

                if (
                    0 <= r < self.height
                    and
                    0 <= c < self.width
                ):

                    safe.add(
                        (r, c)
                    )

        available = [

            (r, c)

            for r in range(self.height)

            for c in range(self.width)

            if (r, c) not in safe
        ]

        if len(available) < self.mine_count:

            available = [

                (r, c)

                for r in range(self.height)

                for c in range(self.width)

                if (r, c) != (
                    safe_row,
                    safe_col
                )
            ]

        self.mines = set(
            random.sample(
                available,
                self.mine_count
            )
        )

        for r in range(self.height):

            for c in range(self.width):

                if (r, c) in self.mines:

                    self.board[r][c] = -1

                    continue

                count = 0

                for nr, nc in self.neighbors(
                    r,
                    c
                ):

                    if (nr, nc) in self.mines:

                        count += 1

                self.board[r][c] = count

    # ========================================================
    # NEIGHBORS
    # ========================================================

    def neighbors(
        self,
        row,
        col
    ):

        for dr in (-1, 0, 1):

            for dc in (-1, 0, 1):

                if dr == 0 and dc == 0:

                    continue

                r = row + dr

                c = col + dc

                if (
                    0 <= r < self.height
                    and
                    0 <= c < self.width
                ):

                    yield r, c

    # ========================================================
    # LEFT CLICK
    # ========================================================

    def left_click(
        self,
        event
    ):

        if self.game_over:

            return

        row, col = self.get_cell(
            event.x,
            event.y
        )

        if row is None:

            return

        if (row, col) in self.flags:

            return

        if self.first_click:

            self.generate_mines(
                row,
                col
            )

            self.first_click = False

            self.start_time = time.time()

        if (row, col) in self.mines:

            self.lose_game(
                row,
                col
            )

            return

        self.reveal(
            row,
            col
        )

        if self.check_win():

            self.win_game()

        self.update_status()

    # ========================================================
    # REVEAL
    # ========================================================

    def reveal(
        self,
        row,
        col
    ):

        stack = [
            (row, col)
        ]

        while stack:

            r, c = stack.pop()

            if (r, c) in self.revealed:

                continue

            if (r, c) in self.flags:

                continue

            if (r, c) in self.mines:

                continue

            self.revealed.add(
                (r, c)
            )

            value = self.board[r][c]

            if value == 0:

                for nr, nc in self.neighbors(
                    r,
                    c
                ):

                    if (
                        (nr, nc) not in self.revealed
                        and
                        (nr, nc) not in self.mines
                        and
                        (nr, nc) not in self.flags
                    ):

                        stack.append(
                            (nr, nc)
                        )

        self.draw_board()

    # ========================================================
    # RIGHT CLICK / FLAG
    # ========================================================

    def right_click(
        self,
        event
    ):

        if self.game_over:

            return

        row, col = self.get_cell(
            event.x,
            event.y
        )

        if row is None:

            return

        if (row, col) in self.revealed:

            return

        if (row, col) in self.flags:

            self.flags.remove(
                (row, col)
            )

        else:

            if len(self.flags) >= self.mine_count:

                return

            self.flags.add(
                (row, col)
            )

        self.draw_board()

        self.update_status()

    # ========================================================
    # WIN CHECK
    # ========================================================

    def check_win(self):

        safe_cells = (
            self.width
            * self.height
            - self.mine_count
        )

        return len(
            self.revealed
        ) >= safe_cells

    # ========================================================
    # WIN
    # ========================================================

    def win_game(self):

        self.game_over = True

        self.won = True

        if (
            self.start_time is not None
            and
            self.elapsed <= 0
        ):

            self.elapsed = max(
                1,
                int(
                    time.time()
                    - self.start_time
                )
            )

        self.flags.update(
            self.mines
        )

        self.draw_board()

        name = self.name_var.get().strip()

        if not name:

            name = "Anonymous"

        name = name[:16]

        success = upload_score(
            name,
            self.difficulty,
            self.elapsed
        )

        if success:

            self.mine_label.config(
                text=f"🏆 {name}: {self.elapsed}s"
            )

        else:

            self.mine_label.config(
                text="🏆 Won - upload failed"
            )

    # ========================================================
    # LOSE
    # ========================================================

    def lose_game(
        self,
        clicked_row,
        clicked_col
    ):

        self.game_over = True

        self.revealed.update(
            self.mines
        )

        self.draw_board()

        self.draw_mine(
            clicked_row,
            clicked_col,
            exploded=True
        )

        self.mine_label.config(
            text="💥 BOOM!"
        )

    # ========================================================
    # LEADERBOARD
    # ========================================================

    def show_leaderboard(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Online Leaderboard"
        )

        window.geometry(
            "430x500"
        )

        window.minsize(
            350,
            400
        )

        try:

            icon_path = get_resource_path(
                "icon.ico"
            )

            if os.path.exists(icon_path):

                window.iconbitmap(
                    icon_path
                )

        except Exception:
            pass

        tk.Label(
            window,
            text="🌎 ONLINE LEADERBOARD",
            font=(
                "Arial",
                17,
                "bold"
            )
        ).pack(
            pady=10
        )

        selected = tk.StringVar(
            value=self.difficulty
        )

        menu = tk.OptionMenu(
            window,
            selected,
            *self.difficulties.keys()
        )

        menu.pack(
            pady=(0, 8)
        )

        status = tk.Label(
            window,
            text="Loading..."
        )

        status.pack()

        frame = tk.Frame(
            window
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        def refresh(*args):

            for widget in frame.winfo_children():

                widget.destroy()

            status.config(
                text="Loading..."
            )

            window.update_idletasks()

            difficulty = selected.get()

            scores = get_scores(
                difficulty
            )

            if not scores:

                status.config(
                    text="No scores found."
                )

                return

            status.config(
                text=f"Top {len(scores)} players"
            )

            # =================================================
            # HEADERS
            # =================================================

            tk.Label(
                frame,
                text="#",
                font=(
                    "Arial",
                    10,
                    "bold"
                ),
                width=5
            ).grid(
                row=0,
                column=0
            )

            tk.Label(
                frame,
                text="Player",
                font=(
                    "Arial",
                    10,
                    "bold"
                ),
                width=18,
                anchor="w"
            ).grid(
                row=0,
                column=1
            )

            tk.Label(
                frame,
                text="Time",
                font=(
                    "Arial",
                    10,
                    "bold"
                ),
                width=10
            ).grid(
                row=0,
                column=2
            )

            # =================================================
            # SCORES
            # =================================================

            for i, score in enumerate(scores):

                if i == 0:

                    rank = "🥇"

                elif i == 1:

                    rank = "🥈"

                elif i == 2:

                    rank = "🥉"

                else:

                    rank = str(i + 1)

                tk.Label(
                    frame,
                    text=rank
                ).grid(
                    row=i + 1,
                    column=0,
                    pady=4
                )

                tk.Label(
                    frame,
                    text=score.get(
                        "player",
                        "Anonymous"
                    ),
                    anchor="w"
                ).grid(
                    row=i + 1,
                    column=1,
                    sticky="w"
                )

                tk.Label(
                    frame,
                    text=f"{score.get('time_seconds', 0)}s"
                ).grid(
                    row=i + 1,
                    column=2
                )

        selected.trace_add(
            "write",
            refresh
        )

        refresh()

        tk.Button(
            window,
            text="Close",
            command=window.destroy
        ).pack(
            pady=10
        )

    # ========================================================
    # DRAW BOARD
    # ========================================================

    def draw_board(self):

        self.canvas.delete(
            "all"
        )

        canvas_width = self.canvas.winfo_width()

        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1:

            canvas_width = 400

        if canvas_height <= 1:

            canvas_height = 400

        self.cell_size = min(
            canvas_width / self.width,
            canvas_height / self.height
        )

        board_width = (
            self.cell_size
            * self.width
        )

        board_height = (
            self.cell_size
            * self.height
        )

        self.offset_x = (
            canvas_width
            - board_width
        ) / 2

        self.offset_y = (
            canvas_height
            - board_height
        ) / 2

        for row in range(self.height):

            for col in range(self.width):

                x1 = (
                    self.offset_x
                    + col * self.cell_size
                )

                y1 = (
                    self.offset_y
                    + row * self.cell_size
                )

                x2 = x1 + self.cell_size

                y2 = y1 + self.cell_size

                # =================================================
                # REVEALED
                # =================================================

                if (row, col) in self.revealed:

                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=self.revealed_color,
                        outline=self.grid_color
                    )

                    if (row, col) in self.mines:

                        self.draw_mine(
                            row,
                            col
                        )

                    else:

                        value = self.board[row][col]

                        if value > 0:

                            font_size = max(
                                8,
                                int(
                                    self.cell_size
                                    * 0.55
                                )
                            )

                            self.canvas.create_text(
                                (x1 + x2) / 2,
                                (y1 + y2) / 2,
                                text=str(value),
                                fill=self.number_colors.get(
                                    value,
                                    "black"
                                ),
                                font=(
                                    "Arial",
                                    font_size,
                                    "bold"
                                )
                            )

                # =================================================
                # HIDDEN
                # =================================================

                else:

                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=self.hidden_color,
                        outline=self.grid_color
                    )

                    if (row, col) in self.flags:

                        font_size = max(
                            8,
                            int(
                                self.cell_size
                                * 0.55
                            )
                        )

                        self.canvas.create_text(
                            (x1 + x2) / 2,
                            (y1 + y2) / 2,
                            text="⚑",
                            fill="red",
                            font=(
                                "Arial",
                                font_size,
                                "bold"
                            )
                        )

    # ========================================================
    # DRAW MINE
    # ========================================================

    def draw_mine(
        self,
        row,
        col,
        exploded=False
    ):

        x1 = (
            self.offset_x
            + col * self.cell_size
        )

        y1 = (
            self.offset_y
            + row * self.cell_size
        )

        x2 = x1 + self.cell_size

        y2 = y1 + self.cell_size

        if exploded:

            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#ff5555",
                outline="black"
            )

        font_size = max(
            8,
            int(
                self.cell_size
                * 0.55
            )
        )

        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text="💣",
            font=(
                "Arial",
                font_size
            )
        )

    # ========================================================
    # GET CELL
    # ========================================================

    def get_cell(
        self,
        x,
        y
    ):

        if self.cell_size <= 0:

            return None, None

        col = int(
            (x - self.offset_x)
            / self.cell_size
        )

        row = int(
            (y - self.offset_y)
            / self.cell_size
        )

        if (
            0 <= row < self.height
            and
            0 <= col < self.width
        ):

            return row, col

        return None, None

    # ========================================================
    # HOVER
    # ========================================================

    def mouse_move(
        self,
        event
    ):

        if self.game_over:

            return

        self.canvas.delete(
            "hover"
        )

        row, col = self.get_cell(
            event.x,
            event.y
        )

        if row is None:

            return

        if (row, col) in self.revealed:

            return

        x1 = (
            self.offset_x
            + col * self.cell_size
        )

        y1 = (
            self.offset_y
            + row * self.cell_size
        )

        x2 = x1 + self.cell_size

        y2 = y1 + self.cell_size

        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=self.hidden_hover,
            outline=self.grid_color,
            tags="hover"
        )

        if (row, col) in self.flags:

            font_size = max(
                8,
                int(
                    self.cell_size
                    * 0.55
                )
            )

            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text="⚑",
                fill="red",
                font=(
                    "Arial",
                    font_size,
                    "bold"
                ),
                tags="hover"
            )

    def mouse_leave(
        self,
        event
    ):

        self.canvas.delete(
            "hover"
        )

    # ========================================================
    # STATUS
    # ========================================================

    def update_status(self):

        if self.game_over:

            return

        remaining = (
            self.mine_count
            - len(self.flags)
        )

        self.mine_label.config(
            text=f"💣 {remaining}"
        )

    # ========================================================
    # TIMER
    # ========================================================

    def update_timer(self):

        if (
            self.start_time is not None
            and
            not self.game_over
        ):

            self.elapsed = int(
                time.time()
                - self.start_time
            )

        self.timer_label.config(
            text=f"⏱ {self.elapsed}"
        )

        self.root.after(
            250,
            self.update_timer
        )

    # ========================================================
    # RESIZE
    # ========================================================

    def on_resize(
        self,
        event
    ):

        if event.widget == self.canvas:

            if (
                event.width > 1
                and
                event.height > 1
            ):

                self.draw_board()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    game = Minesweeper(
        root
    )

    root.mainloop()