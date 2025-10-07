
from ursina import *
from wumpus_world import WumpusWorld

class WumpusGame:
    def __init__(self, app_instance):
        self.app = app_instance
        window.title = 'Wumpus World'
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        window.fps_counter.visible = True

        self.grid_size = 4
        self.cell_size = 1.5
        self.game = WumpusWorld(size=self.grid_size, num_pits=2, num_wumpus=1)

        self.board_entities = []
        self.percept_texts = []
        self.hunter_entity = None

        self.create_board()
        self.create_ui()
        self.update_board_visuals()

    def create_board(self):
        for r in range(self.grid_size):
            row_entities = []
            for c in range(self.grid_size):
                btn = Button(
                    parent=scene,
                    model='cube',
                    color=color.white,
                    position=(c * self.cell_size, -r * self.cell_size, 0),
                    scale=self.cell_size * 0.9,
                    texture='brick'
                )
                row_entities.append(btn)
            self.board_entities.append(row_entities)

    def update_board_visuals(self):
        # Clear old percept texts
        for t in self.percept_texts:
            destroy(t)
        self.percept_texts.clear()

        # Update hunter position
        if self.hunter_entity:
            destroy(self.hunter_entity)
        
        hunter_r, hunter_c = self.game.hunter_pos
        self.hunter_entity = Entity(
            parent=scene,
            model='cube',
            color=color.blue,
            position=(hunter_c * self.cell_size, -hunter_r * self.cell_size, -0.5),
            scale=self.cell_size * 0.5,
            texture='circle'
        )

        # Update cell contents and percepts
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                cell_content = self.game.grid[r][c]
                btn = self.board_entities[r][c]
                
                # Reset color
                btn.color = color.white

                # Add percepts as text on the cell
                percepts = []
                if 'S' in cell_content: percepts.append('Stench')
                if 'B' in cell_content: percepts.append('Breeze')
                if 'L' in cell_content: percepts.append('Glitter')

                if (r, c) == self.game.wumpus_pos and self.game.wumpus_pos is not None: percepts.append('Wumpus')
                if (r, c) in self.game.pits_pos: percepts.append('Pit')
                if (r, c) == self.game.gold_pos and not self.game.has_gold: percepts.append('Gold')

                if percepts:
                    text_entity = Text(
                        text='\n'.join(percepts),
                        parent=btn,
                        origin=(0, 0),
                        scale=0.1 / self.cell_size,
                        color=color.black,
                        position=(0, 0, -0.5)
                    )
                    self.percept_texts.append(text_entity)

                # Highlight current hunter position
                if (r, c) == self.game.hunter_pos:
                    btn.color = color.light_gray

        self.update_score_text()
        self.update_game_status_text()

    def create_ui(self):
        # Movement buttons
        button_scale = 0.1
        button_y_offset = -0.5
        button_x_offset = 0.7

        # Up
        Button(text='Up', scale=button_scale, x=button_x_offset, y=0.4 + button_y_offset, on_click=lambda: self.move_hunter(-1, 0))
        # Down
        Button(text='Down', scale=button_scale, x=button_x_offset, y=0.2 + button_y_offset, on_click=lambda: self.move_hunter(1, 0))
        # Left
        Button(text='Left', scale=button_scale, x=button_x_offset - 0.1, y=0.3 + button_y_offset, on_click=lambda: self.move_hunter(0, -1))
        # Right
        Button(text='Right', scale=button_scale, x=button_x_offset + 0.1, y=0.3 + button_y_offset, on_click=lambda: self.move_hunter(0, 1))

        # Action buttons
        Button(text='Grab Gold', scale=button_scale, x=button_x_offset, y=0.0 + button_y_offset, on_click=self.game.grab_gold)
        Button(text='Climb Out', scale=button_scale, x=button_x_offset, y=-0.2 + button_y_offset, on_click=self.game.climb_out)
        Button(text='Shoot Up', scale=button_scale, x=button_x_offset, y=-0.4 + button_y_offset, on_click=lambda: self.shoot_arrow('up'))
        Button(text='Shoot Down', scale=button_scale, x=button_x_offset, y=-0.6 + button_y_offset, on_click=lambda: self.shoot_arrow('down'))
        Button(text='Shoot Left', scale=button_scale, x=button_x_offset - 0.1, y=-0.5 + button_y_offset, on_click=lambda: self.shoot_arrow('left'))
        Button(text='Shoot Right', scale=button_scale, x=button_x_offset + 0.1, y=-0.5 + button_y_offset, on_click=lambda: self.shoot_arrow('right'))

        # Game status text
        self.score_text = Text(text=f'Score: {self.game.score}', origin=(-0.5, 0.5), scale=2, x=-0.8, y=0.45)
        self.status_text = Text(text='Game On!', origin=(-0.5, 0.5), scale=2, x=-0.8, y=0.4)

    def move_hunter(self, dr, dc):
        if not self.game.game_over:
            self.game.move_hunter(dr, dc)
            self.update_board_visuals()
            self.check_game_over()

    def shoot_arrow(self, direction):
        if not self.game.game_over and self.game.has_arrow:
            self.game.shoot_arrow(direction)
            self.update_board_visuals()
            self.check_game_over()

    def update_score_text(self):
        self.score_text.text = f'Score: {self.game.score}'

    def update_game_status_text(self):
        if self.game.game_over:
            if not self.game.is_alive:
                self.status_text.text = 'Game Over! You Died!'
                self.status_text.color = color.red
            elif self.game.has_gold and self.game.hunter_pos == (0,0):
                self.status_text.text = 'Game Over! You Won!'
                self.status_text.color = color.green
            else:
                self.status_text.text = 'Game Over!'
                self.status_text.color = color.orange
        else:
            self.status_text.text = 'Game On!'
            self.status_text.color = color.white

    def check_game_over(self):
        if self.game.game_over:
            print("Game Over!")
            self.update_game_status_text()

if __name__ == '__main__':
    app = Ursina()
    game_instance = WumpusGame(app)
    app.run()

