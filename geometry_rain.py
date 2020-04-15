import arcade
import random
import time

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1200
SCREEN_TITLE = "Geometry Rain"
#SCALING = 1.0

class GeometryRain(arcade.Window):

    def __init__(self, width, height, title):
        """Initialize the game
        """
        super().__init__(width, height, title)

        # Set up the empty sprite lists
        self.enemies_list = arcade.SpriteList()
        self.bonuses_list = arcade.SpriteList()
        self.traps_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()

        self.enemy_schedule = None

        self.paused = False

        # Init score for scoreboard
        self.score = 0
        self.bonus_count = 0
        self.level = 1

        self.BONUS_AVAILABLE = False
        self.BONUS_ACTIVE = False
        self.bonus_start_time = 0
        self.bonus_text = ""

        self.enemy_spawn_time = 0.25
        self.bonus_spawn_time = 8.0
        self.trap_spawn_time = 5.0
        self.point_increase_time = 0.5
        self.level_increase_time = 45.0

        self.TRAP_HIT = False

        # Velocities so you can edit them
        self.enemy_pre_change_velocity = 0
        self.enemy_velocity = (0, random.randint(-10, -3))
        self.player_velocity = 15
        self.bonus_velocity_change = (0, -2)
        

        self.HARDMODE_ACTIVE = False
        self.hardmode_start_time = 0

    def setup(self):
        """Get the game ready to play
        """

        # Set the background color
        arcade.set_background_color(arcade.color.SKY_BLUE)

        # Set up the player
        self.player = arcade.Sprite("images/player_sprite.png", 0.25)
        self.player.center_y = 40
        self.player.left = self.width / 2
        self.all_sprites.append(self.player)

        # Spawn a new enemy every 0.25 seconds
        self.enemy_schedule = arcade.schedule(self.add_enemy, self.enemy_spawn_time)

        # Spawn a new bonus every 8 seconds
        arcade.schedule(self.add_bonus, self.bonus_spawn_time)

        # Spawn a trap every 5 seconds
        arcade.schedule(self.add_trap, self.trap_spawn_time)

        # Give points every half a second the player is alive
        arcade.schedule(self.givePoints, self.point_increase_time)

        # Increase level and difficulty every 45 seconds
        arcade.schedule(self.increaseLevel, self.level_increase_time)

    def on_update(self, delta_time: float):
        """Update the positions and statuses of all game objects
        If paused, do nothing

        Arguments:
            delta_time {float} -- Time since the last update
        """

        # If paused, don't update anything
        if self.paused:
            return

        # If hardmode is active, check if it has reached its duration, then end it and reset values to normal
        if self.HARDMODE_ACTIVE:
            if (time.time() - self.hardmode_start_time) >= 13:
                self.HARDMODE_ACTIVE = False
                arcade.set_background_color(arcade.color.SKY_BLUE)
                self.enemy_spawn_time += 0.15
                self.enemy_schedule = arcade.schedule(self.add_enemy, self.enemy_spawn_time)
                self.hardmode_start_time = 0
                # enemy_velocity will be set back to normal automatically -- see velocity in add_enemy(), it checks for hardmode

        # Did you hit an enemy or bonus?
        if self.player.collides_with_list(self.enemies_list):
            arcade.close_window()

        # Check if bonus streak if 5 to award bonus ability
        if self.bonus_count == 5:
            # GIVE ABILITY POPUP and clear streak count, and start timer for duration
            self.BONUS_AVAILABLE = True
            self.bonus_text = "BONUS READY - PRESS 'Spacebar'"
        
        # Check if duration ran out and end bonus if so, resetting values
        if self.BONUS_ACTIVE:
            if (time.time() - self.bonus_start_time) >= 10:
                print("Bonus ran out of time -- ending bonus ability.")
                self.BONUS_ACTIVE = False
                self.bonus_start_time = 0
                self.enemy_spawn_time = 0.2
                self.enemy_velocity = self.enemy_pre_change_velocity
                for enemy in self.enemies_list:
                    enemy.velocity = self.enemy_pre_change_velocity

        # Update everything
        self.all_sprites.update()

        # Keep the player on screen
        if self.player.top > self.height:
            self.player.top = self.height
        if self.player.right > self.width:
            self.player.right = self.width
        if self.player.bottom < 0:
            self.player.bottom = 0
        if self.player.left < 0:
            self.player.left = 0

    def on_draw(self):
        """Draw all game objects
        """
        # Begin rendering (will end automatically after method ends)
        arcade.start_render()

        # Draw scoreboard text
        arcade.draw_text("SCORE: {}".format(str(self.score)), self.width/2 - 75, self.height - 35, arcade.color.BLACK, 18)
        arcade.draw_text("Bonus Streak: {}/5".format(str(self.bonus_count)), self.width/2 - 75, self.height - 65, arcade.color.BLACK, 18)
        arcade.draw_text("Level: {}".format(str(self.level)), self.width/2 - 75, self.height - 95, arcade.color.BLACK, 18)
        
        # Draw placeholder text for bonus notification
        if self.BONUS_AVAILABLE:
            arcade.draw_text(self.bonus_text, self.width/2 - 75, self.height*0.05, arcade.color.BLACK, 18)

        self.all_sprites.draw()

    def givePoints(self, delta_time: float):
        self.score += 50

    def increaseLevel(self, delta_time: float):
        self.level += 1

        # Increase enemy movement speed slightly
        new_velocity = (0, list(self.enemy_velocity)[1] - 0.7)
        self.enemy_pre_change_velocity = new_velocity
        self.enemy_velocity = new_velocity

        """ I removed this because hardmode increases spawn time pretty rapidly, so that combined with this would be way too much """
        # if self.level < 3:
        #     # Increase enemy spawn rate slightly, but only until level 3. Dont want to get too crazy with it, as hard mode will be rough already
        #     self.enemy_spawn_time -= 0.05

        # HARD MODE LEVELS
        if self.level == 4:
            # Stop all spawning for 5 seconds, give it some suspense, change background color to black, then start hard mode dropping
            self.hardMode()
        elif self.level == 7:
            self.hardMode()

    def hardMode(self):
        self.HARDMODE_ACTIVE = True

        # Change background color
        arcade.set_background_color(arcade.color.BLACK)

        self.hardmode_start_time = time.time()

        # Increase spawn rate
        self.enemy_spawn_time -= 0.15
        self.enemy_schedule = arcade.schedule(self.add_enemy, self.enemy_spawn_time)

        # Now that HARDMODE_ACTIVE is true, in add_enemy(), the spawn rate will change until set to False

    def add_enemy(self, delta_time: float):
        """Adds a new enemy to the screen

        Arguments:
            delta_time {float} -- How much time has passed since the last call
        """
        if self.paused:
            return

        # Check if hardmode is on and how long it has been on for
        if self.HARDMODE_ACTIVE:
            # If hardmode has been on for less than 5 seconds, don't spawn anything.
            if (time.time() - self.hardmode_start_time) < 5:
                return

        if not self.BONUS_ACTIVE:
            if not self.HARDMODE_ACTIVE:
                # Everything is normal play - set velocity to new random
                self.enemy_velocity = (0, random.randint(-10, -3))

        # First, create the new enemy sprite
        enemy = EnemySprite("images/enemy_sprite.png", 0.2)

        # Set its position to a random x position and off-screen at the top
        enemy.top = random.randint(self.height, self.height + 80)
        enemy.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        if self.HARDMODE_ACTIVE:
            enemy.velocity = (0, random.randint(-18, -15))
        else:
            enemy.velocity = self.enemy_velocity

        # Add it to the enemies list and all_sprites list
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def add_bonus(self, delta_time: float):
        if self.paused:
            return

        if self.BONUS_ACTIVE:
            return

        bonus = BonusSprite("images/bonus_sprite.png", 0.3)

        # Set its position to a random x position and off-screen at the top
        bonus.top = random.randint(self.height, self.height + 80)
        bonus.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        bonus.velocity = (0, -5) # x doesn't do anything, but y decreases by amount

        # Add it to the enemies list and all_sprites list
        self.bonuses_list.append(bonus)
        self.all_sprites.append(bonus)

    def add_trap(self, delta_time: float):
        if self.paused:
            return

        trap = TrapSprite("images/trap_sprite.png", 0.3)

        # Set its position to a random x position and off-screen at the top
        trap.top = random.randint(self.height, self.height + 80)
        trap.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        trap.velocity = (0, -5) # x doesn't do anything, but y decreases by amount

        # Add it to the enemies list and all_sprites list
        self.traps_list.append(trap)
        self.all_sprites.append(trap)

    def on_key_press(self, key, modifiers):
        """Handle user keyboard input
        Q: Quit the game
        P: Pause/Unpause the game
        I/J/K/L: Move Up, Left, Down, Right
        Arrows: Move Up, Left, Down, Right

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if key == arcade.key.Q:
            # Quit immediately
            arcade.close_window()

        if key == arcade.key.P:
            self.paused = not self.paused

        if key == arcade.key.SPACE:
            if self.BONUS_AVAILABLE:
                self.bonus_text = ""
                self.BONUS_ACTIVE = True
                self.BONUS_AVAILABLE = False
                self.bonus_count = 0
                self.bonus_start_time = time.time()

                # Ability effect
                self.enemy_spawn_time = 1.0
                self.enemy_velocity = self.bonus_velocity
                for enemy in self.enemies_list:
                    enemy.velocity = self.bonus_velocity


        #if symbol == arcade.key.W or symbol == arcade.key.UP:
        #    self.player.change_y = 15

        #if symbol == arcade.key.S or symbol == arcade.key.DOWN:
        #    self.player.change_y = -15

        if key == arcade.key.A or key == arcade.key.LEFT:
            self.player.change_x = -self.player_velocity
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.player.change_x = self.player_velocity

    def on_key_release(self, key: int, modifiers: int):
        """Undo movement vectors when movement keys are released

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if (
            key == arcade.key.W
            or key == arcade.key.S
            or key == arcade.key.UP
            or key == arcade.key.DOWN
        ):
            self.player.change_y = 0

        if (
            key == arcade.key.A
            or key == arcade.key.D
            or key == arcade.key.LEFT
            or key == arcade.key.RIGHT
        ):
            self.player.change_x = 0

class EnemySprite(arcade.Sprite):
    def update(self):
        """Update the position of the sprite"""

        # Move the sprite
        super().update()

        # Remove if off the screen and increase score
        if self.bottom <= 5:
            self.remove_from_sprite_lists()
            #app.score += self.getPointValue()


class BonusSprite(arcade.Sprite):
    def update(self):
        super().update()

        if self.bottom <= 5:
            self.remove_from_sprite_lists()
            app.bonus_count = 0

        if self.collides_with_sprite(app.player):
            self.remove_from_sprite_lists()
            app.score += self.getPointValue()
            if not app.BONUS_AVAILABLE:
                app.bonus_count += 1
            
            if app.TRAP_HIT:
                app.player_velocity = 15
                app.TRAP_HIT = False
    
    def getPointValue(self):
        point_value = 500
        return point_value

class TrapSprite(arcade.Sprite):
    def update(self):
        super().update()

        if self.bottom <= 5:
            self.remove_from_sprite_lists()

        if self.collides_with_sprite(app.player):
            app.TRAP_HIT = True
            self.remove_from_sprite_lists()
            app.score += self.getPointValue()
            app.bonus_count = 0 # reset bonus streak
            app.player_velocity = 3
    
    def getPointValue(self):
        point_value = -500 # WILL LOSE 500
        return point_value

# Main code entry point
if __name__ == "__main__":
    app = GeometryRain(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    app.setup()
    arcade.run()